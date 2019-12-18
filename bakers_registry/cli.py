import sys
import fire
import simplejson as json
from pprint import pformat
from pytezos import RpcError

from bakers_registry.encoding import decode_info, encode_info
from bakers_registry.colored import PrinterJSON, PrinterLog
from bakers_registry.core import get_all_bakers, upsert_baker, get_unify_diff, get_baker


def fail(data):
    print(f'\033[91m{pformat(data)}\033[0m', file=sys.stderr)
    exit(-1)


def info(data):
    PrinterJSON().print_data(data)
    sys.stdout.write('\n')


class BakersRegistryCli:
    """
    Tezos Bakers Registry CLI

    Welcome!
    * Smart contract: https://better-call.dev/main/KT1ChNsEFxwyCbJyWGSL3KdjeXE28AY1Kaog
    * Registry UI: https://tezit.github.io/baker-registry
    * Registry FAQ: https://hackmd.io/DZyJU5HSThmGX8ER7tprXg
    """

    def get(self, baker_address, output_file=None, raw=False,
            network='mainnet', registry_address='KT1ChNsEFxwyCbJyWGSL3KdjeXE28AY1Kaog'):
        """
        Get the current baker config
        :param baker_address: tz-address
        :param output_file: path to the file to store the data (optional)
        :param raw: keep intermediate data representation (default is False)
        :param network: Tezos network (default is mainnet)
        :param registry_address: address of the registry contract (predefined)
        """
        try:
            data = get_baker(
                registry_address=registry_address,
                baker_address=baker_address,
                raw=raw,
                network=network)
        except RpcError as e:
            fail(next(iter(e.args)))
        else:
            if not data:
                fail('Not found')

            if output_file:
                with open(output_file, 'w+') as f:
                    f.write(json.dumps(data, indent=4))
            else:
                info(data)

    def set(self, baker_address, input_file, preview=False,
            network='mainnet', registry_address='KT1ChNsEFxwyCbJyWGSL3KdjeXE28AY1Kaog'):
        """
        Generate tezos-client command from the config file
        :param baker_address: tz-address
        :param input_file: path to the file with configuration (can contain any-level representation)
        :param preview: print resulting diff and simulate operation instead of command line (default is False)
        :param network: Tezos network (default is mainnet)
        :param registry_address: address of the registry contract (predefined)
        """
        with open(input_file, 'r') as f:
            data = json.loads(f.read(), use_decimal=True)

        try:
            cmdline, log = upsert_baker(
                registry_address=registry_address,
                baker_address=baker_address,
                data=data,
                dry_run=preview,
                network=network
            )
        except RpcError as e:
            fail(next(iter(e.args)))
        else:
            if preview:
                PrinterLog().print_log(log)
            else:
                print(cmdline)

    def new(self, output_file=None):
        """
        Generates template config for a new baker
        :param output_file: path to the file to store the data (optional)
        """
        data = decode_info(encode_info({}))
        if output_file:
            with open(output_file, 'w+') as f:
                f.write(json.dumps(data, indent=4))
        else:
            info(data)

    def all(self, output_file, raw=False,
            indexer='tzkt', network='mainnet', registry_address='KT1ChNsEFxwyCbJyWGSL3KdjeXE28AY1Kaog'):
        """
        Get all bakers
        :param output_file: path to the file
        :param raw: keep intermediate data representation (default is False)
        :param indexer: which indexer to use to retrieve operation levels [tzkt, tzstats, conseil]
        :param network: Tezos network (default is mainnet)
        :param registry_address: address of the registry contract (predefined)
        """
        if network != 'mainnet':
            fail('Only mainnet is supported at the moment')

        data = get_all_bakers(registry_address, indexer=indexer, raw=raw)
        with open(output_file, 'w+') as f:
            f.write(json.dumps(data, indent=4))

    def log(self, output_file=None, since=None, raw=False,
            indexer='tzkt', network='mainnet', registry_address='KT1ChNsEFxwyCbJyWGSL3KdjeXE28AY1Kaog'):
        """
        Show registry changes, line by line
        :param output_file: path to the file
        :param since: set lower bound, can be level (int) or string "level:700000" "cycle:170".
            Default is "cycle:{current_cycle - 2}".
        :param raw: keep intermediate data representation (default is False)
        :param indexer: which indexer to use to retrieve operation levels [tzkt, tzstats, conseil]
        :param network: Tezos network (default is mainnet)
        :param registry_address: address of the registry contract (predefined)
        """
        if network != 'mainnet':
            fail('Only mainnet is supported at the moment')

        log = get_unify_diff(
            registry_address=registry_address,
            indexer=indexer,
            since=since,
            raw=raw)
        if output_file:
            with open(output_file, 'w+') as f:
                f.write(json.dumps(log, indent=4))
        else:
            PrinterLog().print_log(log)


def main():
    return fire.Fire(BakersRegistryCli)


if __name__ == '__main__':
    main()
