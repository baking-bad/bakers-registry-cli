import requests
from decimal import Decimal
from typing import List, Tuple
from pytezos import pytezos, RpcError
from pytezos.michelson.converter import MichelineSchemaError
from conseil import conseil
from concurrent.futures import ThreadPoolExecutor
from functools import reduce
from jsondiff import diff
from jsondiff.symbols import insert, delete
from yaspin import yaspin

from bakers_registry.encoding import decode_info, decode_snapshot, encode_info, decode_hex

LIMIT = 1000  # TODO: change me
CREATE_FEE = Decimal('1.5')
UPDATE_FEE = Decimal('0.5')


def get_update_levels_tzkt(address):
    res = requests.get(f'https://api.tzkt.io/v1/Accounts/{address}/operations',
                       params=dict(limit=LIMIT)).json()
    return set(map(lambda x: x['level'], res))


def get_update_levels_tzstats(address):
    res = requests.get(f'https://api.tzstats.com/tables/op',
                       params=dict(receiver=address,
                                   limit=LIMIT,
                                   columns='height',
                                   status='applied')).json()
    return set(map(lambda x: x[0], res))


def get_update_levels_conseil(address):
    Operation = conseil.using('prod').tezos.mainnet.operations

    tx_levels = Operation.query(Operation.block_level) \
        .filter(Operation.destination == address,
                Operation.status == 'applied') \
        .limit(LIMIT) \
        .vector()

    orig_level = Operation.query(Operation.block_level) \
        .filter(Operation.originated_contracts == address,
                Operation.status == 'applied') \
        .scalar()

    return set([orig_level] + tx_levels)


def get_update_levels(address, indexer, since=None) -> List[int]:
    indexers = {
        'tzkt': get_update_levels_tzkt,
        'tzstats': get_update_levels_tzstats,
        'conseil': get_update_levels_conseil
    }

    with yaspin(text=f"Retrieving operation levels from {indexer}..."):
        update_levels = indexers[indexer](address)
        update_levels = list(sorted(update_levels, reverse=True))
        if since:
            if isinstance(since, str):
                kind, value = since.split(':')
                if kind == 'level':
                    since = int(value)
                elif kind == 'cycle':
                    since = int(value) * 4096
                # elif kind == 'time': TODO
                # elif kind == 'date':
                else:
                    assert False, kind
            else:
                assert isinstance(since, int), since
            update_levels = list(filter(lambda x: x > since, update_levels))

    return update_levels


def get_updates(registry_address, indexer, since=None) -> List[Tuple[int, dict]]:
    update_levels = get_update_levels(registry_address, indexer=indexer, since=since)

    with yaspin(text=f"Retrieving big map diffs since {since or 'origination'}..."):
        baker_registry = pytezos.using('mainnet-pool').contract(registry_address)

        def parse_updates(level):
            big_map_diff = dict()
            opg_list = baker_registry.shell.blocks[level].operations.managers()
            for opg in opg_list:
                try:
                    results = baker_registry.operation_result(opg)
                    for result in results:
                        if hasattr(result, 'big_map_diff'):
                            big_map_diff.update(**result.big_map_diff)
                        else:
                            big_map_diff.update(**result.storage[0])
                except RpcError:
                    pass
            return level, big_map_diff

        with ThreadPoolExecutor(max_workers=10) as executor:
            updates = list(executor.map(parse_updates, update_levels))

    return updates


def get_snapshot(registry_address, bakers_addresses: list, raw=False, level=None, network='mainnet') -> dict:
    with yaspin(text=f'Retrieving big map snapshot at {level or "head"}...'):
        registry = pytezos.using(network).contract(registry_address)

        def big_map_get(address):
            try:
                data = registry.big_map_get(address, level or 'head')
            except AssertionError:
                data = None
            else:
                if raw:
                    for key in ['last_update', 'reporterAccount']:
                        if key in data:
                            del data[key]
                else:
                    data = decode_info(data)

            return address, data

        with ThreadPoolExecutor(max_workers=10) as executor:
            snapshot = dict(executor.map(big_map_get, bakers_addresses))

    return {k: v for k, v in snapshot.items() if v is not None}


def get_all_bakers(registry_address, indexer='tzkt', raw=False) -> dict:
    updates = get_updates(registry_address, indexer=indexer)

    def merge_updates(a: tuple, b: tuple):
        keys = set(a[1].keys()).union(set(b[1].keys()))
        res = dict()
        for key in keys:
            if key in a[1] and key not in b[1]:
                res[key] = a[1][key]
            elif key in b[1] and key not in a[1]:
                res[key] = b[1][key]
            elif a[0] > b[0]:
                res[key] = a[1][key]
            else:
                res[key] = b[1][key]
        return max(a[0], b[0]), res

    with yaspin(text='Merging updates...'):
        _, data = reduce(merge_updates, updates)
        if not raw:
            data = decode_snapshot(data)

    return data


def iter_diff(node, root_key=''):
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(key, str):
                yield from iter_diff(value, key)
            elif key in [insert, delete]:
                if isinstance(value, list):
                    for key_index, item in value:
                        yield (root_key,
                               None if key == insert else item,
                               item if key == insert else None)
                elif isinstance(value, dict):
                    for sub_key, item in value.items():
                        yield (sub_key,
                               None if key == insert else item,
                               item if key == insert else None)
                else:
                    assert False, value
            else:
                assert False, key
    elif isinstance(node, list):
        assert len(node) == 2, node
        yield root_key, node[0], node[1]
    else:
        assert False, node


def format_entry(entry, level=0, baker=''):
    assert isinstance(entry, tuple)
    assert len(entry) == 3

    if entry[1] is None:
        kind = 'insert'
    elif entry[2] is None:
        kind = 'remove'
    else:
        kind = 'replace'

    return dict(
        level=level,
        baker=baker,
        kind=kind,
        key=entry[0],
        before=entry[1],
        after=entry[2]
    )


def flat_list(list_of_lists):
    return [item for sublist in list_of_lists for item in sublist]


def get_unify_diff(registry_address, indexer='tzkt', since=None, raw=False) -> list:
    if since is None:
        with yaspin(text=f"Getting current cycle..."):
            since = f'cycle:{pytezos.using("mainnet").shell.head.cycle() - 2}'

    updates = get_updates(registry_address, indexer=indexer, since=since)
    if not updates:
        return []

    updates = list(sorted(updates, key=lambda x: x[0]))
    altered_addresses = list()
    for _, update in updates:
        altered_addresses.extend(list(update.keys()))

    if since:
        snapshot = get_snapshot(
            registry_address=registry_address,
            bakers_addresses=list(set(altered_addresses)),
            raw=raw,
            level=updates[0][0] - 1
        )
    else:
        snapshot = decode_snapshot(updates[0][1])
        updates = updates[1:]

    with yaspin(text='Calculating json diffs...'):
        log = list()
        for level, update in updates:
            for address, info in update.items():
                if raw:
                    info.pop('last_update')
                    baker = decode_hex(info['bakerName'])
                else:
                    info = decode_info(info)
                    baker = info['bakerName']

                if address in snapshot:
                    changes = diff(snapshot[address], info, syntax='symmetric')
                    log.extend(map(lambda x: format_entry(x, level, baker),
                                   list(iter_diff(changes))))
                else:
                    log.append(dict(
                        level=level,
                        baker=baker,
                        kind='create',
                        address=address
                    ))

                snapshot.update(address=info)

    return list(reversed(log))


def get_baker(registry_address, baker_address, raw=False, network='mainnet'):
    data = get_snapshot(
        registry_address=registry_address,
        bakers_addresses=[baker_address],
        raw=raw,
        network=network
    )
    if isinstance(data, dict) and set(data.keys()) == {baker_address}:
        return data[baker_address]


def upsert_baker(registry_address, baker_address, data, dry_run=False, network='mainnet'):
    data = encode_info(data)
    current_state = get_baker(
        registry_address=registry_address,
        baker_address=baker_address,
        network=network,
        raw=True
    )

    if current_state:
        changes = diff(current_state, data, syntax='symmetric')
        log = list(map(format_entry, list(iter_diff(changes))))
        fee = UPDATE_FEE
    else:
        log = [dict(kind='create', address=baker_address)]
        fee = CREATE_FEE

    with yaspin(text='Generating command line...'):
        registry = pytezos.using(shell=network, key=baker_address).contract(registry_address)
        try:
            call = registry.set_data(delegate=baker_address, **data).with_amount(fee)
            cmdline = call.cmdline()
        except MichelineSchemaError:
            exit(-1)

    if dry_run:
        with yaspin(text='Simulating operation...'):
            call.result()

    return cmdline, log
