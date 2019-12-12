import sys
import fire
import simplejson as json
from pprint import pformat
from pytezos import pytezos, RpcError
from pytezos.michelson.converter import MichelineSchemaError

from bakers_registry.encoding import decode_info, encode_info
from bakers_registry.colored import PrinterJSON
from bakers_registry.core import get_updates


def fail(data):
    print(f'\033[91m{pformat(data)}\033[0m', file=sys.stderr)
    exit(-1)


def info(data):
    PrinterJSON().print_data(data)
    sys.stdout.write('\n')


class BakersRegistryCli:

    def get(self, baker_address, output_file=None, raw=False,
            network='mainnet', registry_address='KT1ChNsEFxwyCbJyWGSL3KdjeXE28AY1Kaog'):
        registry = pytezos.using(network).contract(registry_address)
        try:
            data = registry.big_map_get(baker_address)
        except RpcError as e:
            fail(next(iter(e.args)))
        else:
            if not raw:
                data = decode_info(data)

            if output_file:
                with open(output_file, 'w+') as f:
                    f.write(json.dumps(data, indent=4))
            else:
                info(data)

    def set(self, baker_address, input_file, preview=False,
            network='mainnet', registry_address='KT1ChNsEFxwyCbJyWGSL3KdjeXE28AY1Kaog'):
        with open(input_file, 'r') as f:
            data = json.loads(f.read(), use_decimal=True)

        data = encode_info(data)
        registry = pytezos.using(shell=network, key=baker_address).contract(registry_address)
        try:
            cmd = registry.set_data(delegate=baker_address, **data).cmdline()
        except MichelineSchemaError:
            exit(-1)
        else:
            if preview:
                info(data)
            else:
                print(cmd)

    def new(self, output_file=None):
        data = decode_info(encode_info({}))
        if output_file:
            with open(output_file, 'w+') as f:
                f.write(json.dumps(data, indent=4))
        else:
            info(data)

    def all(self, output_file, since=None, raw=False,
            network='mainnet', registry_address='KT1ChNsEFxwyCbJyWGSL3KdjeXE28AY1Kaog'):
        if network != 'mainnet':
            fail('Only mainnet is supported at the moment')

        data = get_updates(registry_address, since)
        if not raw:
            data = dict(map(lambda x: (x[0], decode_info(x[1])), data.items()))

        with open(output_file, 'w+') as f:
            f.write(json.dumps(data, indent=4))


def main():
    return fire.Fire(BakersRegistryCli)


if __name__ == '__main__':
    main()
