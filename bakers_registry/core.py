import requests
from pytezos import pytezos, RpcError
from conseil import conseil
from concurrent.futures import ThreadPoolExecutor
from functools import reduce


def get_update_levels_tzkt(address):
    res = requests.get(f'https://api.tzkt.io/v1/Accounts/{address}/operations',
                       params=dict(limit=1000)).json()  # TODO: limit
    return set(map(lambda x: x['level'], res))


def get_update_levels_tzstats(address):
    res = requests.get(f'https://api.tzstats.com/tables/op',
                       params=dict(receiver=address,
                                   columns='height',
                                   status='applied')).json()
    return set(map(lambda x: x[0], res))


def get_update_levels_conseil(address):
    Operation = conseil.using('prod').tezos.mainnet.operations

    tx_levels = Operation.query(Operation.block_level) \
        .filter(Operation.destination == address,
                Operation.status == 'applied') \
        .limit(1000) \
        .vector()  # TODO: limit

    orig_level = Operation.query(Operation.block_level) \
        .filter(Operation.originated_contracts == address,
                Operation.status == 'applied') \
        .scalar()

    return set([orig_level] + tx_levels)


def get_update_levels(address, since=None):
    getters = [
        get_update_levels_tzkt,
        get_update_levels_tzstats,
        get_update_levels_conseil]

    with ThreadPoolExecutor(max_workers=3) as executor:
        levels = list(executor.map(lambda x: x(address), getters))

    assert all(map(lambda x: x == levels[0], levels))

    if since:
        if isinstance(since, str):
            kind, value = since.split(':', maxsplit=2)
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
        levels = list(filter(lambda x: x > since, levels))

    return list(sorted(levels[0], reverse=True))


def get_updates(registry_address, since=None):
    print(f'Querying updates since {since or "origination"}...')
    update_levels = get_update_levels(registry_address, since)
    baker_registry = pytezos.using('mainnet-pool').contract(registry_address)

    def parse_updates(level):
        big_map_diff = dict()
        opg_list = baker_registry.shell.blocks[level].operations.managers()
        for opg in opg_list:
            try:
                result = baker_registry.operation_result(opg)
                if result:
                    big_map_diff.update(**result.big_map_diff)
            except RpcError:
                pass
        print(f'Got {len(big_map_diff)} updates at level {level}')
        return big_map_diff

    def merge_updates(a: dict, b: dict):
        keys = set(a.keys()).union(set(b.keys()))
        res = dict()
        for key in keys:
            if key in a and key not in b:
                res[key] = a[key]
            elif key in b and key not in a:
                res[key] = b[key]
            elif a[key]['last_update'] > b[key]['last_update']:
                res[key] = a[key]
            else:
                res[key] = b[key]
        return res

    with ThreadPoolExecutor(max_workers=8) as executor:
        updates = list(executor.map(parse_updates, update_levels))

    return reduce(merge_updates, updates)
