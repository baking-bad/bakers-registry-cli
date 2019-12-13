import re
from decimal import Decimal


def decode_mutez(value):
    return Decimal(value) / 10000


def decode_info(data):
    return {
        'bakerName': bytes.fromhex(data['bakerName']).decode(),
        'openForDelegation': data['openForDelegation'],
        'bakerOffchainRegistryUrl': bytes.fromhex(data['bakerOffchainRegistryUrl']).decode(),
        'fee': str(1 - decode_mutez(data['split'])),
        'bakerPaysFromAccounts': data['bakerPaysFromAccounts'],
        'minDelegation': str(decode_mutez(data['minDelegation'])),
        'subtractPayoutsLessThanMin': data['subtractPayoutsLessThanMin'],
        'payoutDelay': data['payoutDelay'],
        'payoutFrequency': data['payoutFrequency'],
        'minPayout': str(decode_mutez(data['minPayout'])),
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


def encode_mutez(value):
    if isinstance(value, str):
        return int(Decimal(value) * 10000)
    if isinstance(value, int):
        return value
    assert False, value


def encode_split(data):
    if data.get('split'):
        return int(data['split'])
    if data.get('fee'):
        return 10000 - encode_mutez(data['fee'])
    return 10000


def encode_info(data):
    return {
        'bakerName': try_hex_encode(data.get('bakerName', '')),
        'openForDelegation': data.get('openForDelegation', True),
        'bakerOffchainRegistryUrl': try_hex_encode(data.get('bakerOffchainRegistryUrl', '')),
        'split': encode_split(data),
        'bakerPaysFromAccounts': data.get('bakerPaysFromAccounts', []),
        'minDelegation': encode_mutez(data.get('minDelegation', 0)),
        'subtractPayoutsLessThanMin': data.get('subtractPayoutsLessThanMin', True),
        'payoutDelay': data.get('payoutDelay', 0),
        'payoutFrequency': data.get('payoutFrequency', 1),
        'minPayout': encode_mutez(data.get('minPayout', 0)),
        'bakerChargesTransactionFee': data.get('bakerChargesTransactionFee', False),
        'paymentConfigMask': encode_config_mask(data, 16383),
        'overDelegationThreshold': data.get('overDelegationThreshold', 100),
        'subtractRewardsFromUninvitedDelegation': data.get('subtractRewardsFromUninvitedDelegation', True)
    }


def decode_snapshot(snapshot: dict):
    return dict(map(lambda x: (x[0], decode_info(x[1])), snapshot.items()))
