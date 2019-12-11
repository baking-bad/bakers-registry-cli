import re
import sys
import fire
import simplejson as json
from decimal import Decimal
from bakers_registry.colored import PrinterJSON
from pprint import pformat, pprint
from pytezos import pytezos, RpcError
from pytezos.michelson.converter import MichelineSchemaError


def fail(data):
    print(f'\033[91m{pformat(data)}\033[0m', file=sys.stderr)
    exit(-1)


def info(data):
    PrinterJSON().print_data(data)
    sys.stdout.write('\n')


def decode_info(data):
    return {
        'bakerName': bytes.fromhex(data['bakerName']).decode(),
        'openForDelegation': data['openForDelegation'],
        'bakerOffchainRegistryUrl': bytes.fromhex(data['bakerOffchainRegistryUrl']).decode(),
        'fee': str(1 - Decimal(data['split']) / 10000),
        'bakerPaysFromAccounts': data['bakerPaysFromAccounts'],
        'minDelegation': str(Decimal(data['minDelegation']) / 10000),
        'subtractPayoutsLessThanMin': data['subtractPayoutsLessThanMin'],
        'payoutDelay': data['payoutDelay'],
        'payoutFrequency': data['payoutFrequency'],
        'minPayout': data['minPayout'],
        'bakerChargesTransactionFee': data['bakerChargesTransactionFee'],
        'paymentConfig': {
            'payForOwnBlocks': data['paymentConfigMask'] & 1 > 0,
            'payForStolenBlocks': data['paymentConfigMask'] & 2048 > 0,
            'compensateMissedBlocks': data['paymentConfigMask'] & 1024 == 0,
            'payForEndorsements': data['paymentConfigMask'] & 2 > 0,
            'compensateLowPriorityEndorsementLoss': data['paymentConfigMask'] & 8192 == 0,
            'compensateMissedEndorsements': data['paymentConfigMask'] & 4096 == 0,
            'payGainedFees': data['paymentConfigMask'] & 4 > 0,
            'payForAccusationGains': data['paymentConfigMask'] & 8 > 0,
            'subtractLostDepositsWhenAccused': data['paymentConfigMask'] & 16 > 0,
            'subtractLostRewardsWhenAccused': data['paymentConfigMask'] & 32 > 0,
            'subtractLostFeesWhenAccused': data['paymentConfigMask'] & 64 > 0,
            'payForRevelation': data['paymentConfigMask'] & 128 > 0,
            'subtractLostRewardsWhenMissRevelation': data['paymentConfigMask'] & 256 > 0,
            'subtractLostFeesWhenMissRevelation': data['paymentConfigMask'] & 512 > 0
        },
        'overDelegationThreshold': data['overDelegationThreshold'],
        'subtractRewardsFromUninvitedDelegation': data['subtractRewardsFromUninvitedDelegation']
    }


def try_hex_encode(data):
    if re.match('^[0-9a-f]$', data) and len(data) % 2 == 0:
        return data
    else:
        return data.encode().hex()


def encode_config_mask(data, default):
    if data.get('paymentConfigMask'):
        return int(data['paymentConfigMask'])
    if data.get('paymentConfig'):
        mask = 0
        config = data['paymentConfig']
        if config.get('payForOwnBlocks'):
            mask |= 1
        if config.get('payForStolenBlocks'):
            mask |= 2048
        if not config.get('compensateMissedBlocks'):
            mask |= 1024
        if config.get('payForEndorsements'):
            mask |= 2
        if not config.get('compensateLowPriorityEndorsementLoss'):
            mask |= 8192
        if not config.get('compensateMissedEndorsements'):
            mask |= 4096
        if config.get('payGainedFees'):
            mask |= 4
        if config.get('payForAccusationGains'):
            mask |= 8
        if config.get('subtractLostDepositsWhenAccused'):
            mask |= 16
        if config.get('subtractLostRewardsWhenAccused'):
            mask |= 32
        if config.get('subtractLostFeesWhenAccused'):
            mask |= 64
        if config.get('payForRevelation'):
            mask |= 128
        if config.get('subtractLostRewardsWhenMissRevelation'):
            mask |= 256
        if config.get('subtractLostFeesWhenMissRevelation'):
            mask |= 512
    return default


def encode_split(data, default):
    if data.get('split'):
        return int(data['split'])
    if data.get('fee'):
        return int((1 - Decimal(data['fee'])) * 10000)
    return default


def encode_min_delegation(value):
    if isinstance(value, str):
        return int(Decimal(value) / 10000)
    if isinstance(value, int):
        return value
    assert False, value


def encode_info(data):
    return {
        'bakerName': try_hex_encode(data.get('bakerName', '')),
        'openForDelegation': data.get('openForDelegation', True),
        'bakerOffchainRegistryUrl': try_hex_encode(data.get('bakerOffchainRegistryUrl', '')),
        'split': encode_split(data, 10000),
        'bakerPaysFromAccounts': data.get('bakerPaysFromAccounts', []),
        'minDelegation': encode_min_delegation(data.get('minDelegation', 0)),
        'subtractPayoutsLessThanMin': data.get('subtractPayoutsLessThanMin', True),
        'payoutDelay': data.get('payoutDelay', 0),
        'payoutFrequency': data.get('payoutFrequency', 1),
        'minPayout': data.get('minPayout', 0),
        'bakerChargesTransactionFee': data.get('bakerChargesTransactionFee', False),
        'paymentConfigMask': encode_config_mask(data, 16383),
        'overDelegationThreshold': data.get('overDelegationThreshold', 100),
        'subtractRewardsFromUninvitedDelegation': data.get('subtractRewardsFromUninvitedDelegation', True)
    }


class BakersRegistryCli:

    def get(self, baker_address, output_file=None, raw_format=False,
            network='mainnet', registry_address='KT1ChNsEFxwyCbJyWGSL3KdjeXE28AY1Kaog'):
        registry = pytezos.using(network).contract(registry_address)
        try:
            data = registry.big_map_get(baker_address)
        except RpcError as e:
            fail(next(iter(e.args)))
        else:
            if not raw_format:
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
        registry = pytezos.using(network).contract(registry_address)
        try:
            cmd = registry.set_data(delegate=baker_address, **data).cmdline()
        except MichelineSchemaError:
            exit(-1)
        else:
            if preview:
                pprint(data)
            else:
                print(cmd)

    def new(self, output_file=None):
        data = decode_info(encode_info({}))
        if output_file:
            with open(output_file, 'w+') as f:
                f.write(json.dumps(data))
        else:
            info(data)


def main():
    return fire.Fire(BakersRegistryCli)


if __name__ == '__main__':
    main()
