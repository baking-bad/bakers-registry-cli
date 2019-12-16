# Bakers Registry client

[![PyPI version](https://badge.fury.io/py/bakers-registry.svg?)](https://badge.fury.io/py/bakers-registry)
[![made_with pytezos](https://img.shields.io/badge/made_with-pytezos-blue.svg)](https://github.com/baking-bad/pytezos)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Console client for the [Tezos Bakers Registry](https://tezit.github.io/baker-registry)

#### Decentralized approach
* Does not depend on a particular indexer: you can choose from several options, or add new one with little efforts
* Most data is retrieved from a pool of public RPC nodes

## Installation

```bash
pip install bakers-registry
```

#### Requirements
* python 3.6+
* pip

## Usage

### `bakers get` Get a particular baker

```bash
NAME
    bakers get - Get the current baker config

SYNOPSIS
    bakers get BAKER_ADDRESS <flags>

DESCRIPTION
    Get the current baker config

POSITIONAL ARGUMENTS
    BAKER_ADDRESS
        tz-address

FLAGS
    --output_file=OUTPUT_FILE
        path to the file to store the data (optional)
    --raw=RAW
        keep intermediate data representation (default is False)
    --network=NETWORK
        Tezos network (default is mainnet)
    --registry_address=REGISTRY_ADDRESS
        address of the registry contract (predefined)
```

##### Sample output
```json
{
  "bakerName": "Bake'n'Rolls",
  "openForDelegation": true,
  "bakerOffchainRegistryUrl": "https://bakenrolls.com/registry.json",
  "fee": "0.09",
  "bakerPaysFromAccounts": [
    "tz1Zrqm4TkJwqTxm5TiyVFh6taXG4Wrq7tko"
  ],
  "minDelegation": "10",
  "subtractPayoutsLessThanMin": true,
  "payoutDelay": 6,
  "payoutFrequency": 1,
  "minPayout": "0",
  "bakerChargesTransactionFee": true,
  "paymentConfig": {
    "payForOwnBlocks": true,
    "payForStolenBlocks": true,
    "compensateMissedBlocks": false,
    "payForEndorsements": true,
    "compensateLowPriorityEndorsementLoss": false,
    "compensateMissedEndorsements": false,
    "payGainedFees": true,
    "payForAccusationGains": true,
    "subtractLostDepositsWhenAccused": true,
    "subtractLostRewardsWhenAccused": true,
    "subtractLostFeesWhenAccused": true,
    "payForRevelation": true,
    "subtractLostRewardsWhenMissRevelation": true,
    "subtractLostFeesWhenMissRevelation": true
  },
  "overDelegationThreshold": 100,
  "subtractRewardsFromUninvitedDelegation": true
}
```

##### Raw format
```json
{
  "bakerName": "42616b65276e27526f6c6c73",
  "openForDelegation": true,
  "bakerOffchainRegistryUrl": "68747470733a2f2f62616b656e726f6c6c732e636f6d2f72656769737472792e6a736f6e",
  "split": 9100,
  "bakerPaysFromAccounts": [
    "tz1Zrqm4TkJwqTxm5TiyVFh6taXG4Wrq7tko"
  ],
  "minDelegation": 100000,
  "subtractPayoutsLessThanMin": true,
  "payoutDelay": 6,
  "payoutFrequency": 1,
  "minPayout": 0,
  "bakerChargesTransactionFee": true,
  "paymentConfigMask": 16383,
  "overDelegationThreshold": 100,
  "subtractRewardsFromUninvitedDelegation": true,
  "reporterAccount": "tz1Zrqm4TkJwqTxm5TiyVFh6taXG4Wrq7tko"
}

```

### `bakers set` Generate cmdline for `tezos-client`
```bash
NAME
    bakers set - Generate tezos-client command from the config file

SYNOPSIS
    bakers set BAKER_ADDRESS INPUT_FILE <flags>

DESCRIPTION
    Generate tezos-client command from the config file

POSITIONAL ARGUMENTS
    BAKER_ADDRESS
        tz-address
    INPUT_FILE
        path to the file with configuration (can contain any-level representation)

FLAGS
    --preview=PREVIEW
        print resulting config instead of command line (default is False)
    --network=NETWORK
        Tezos network (default is mainnet)
    --registry_address=REGISTRY_ADDRESS
        address of the registry contract (predefined)
```

##### Sample output

```bash
transfer 0 from tz1NortRftucvAkD1J58L32EhSVrQEWJCEnB to KT1ChNsEFxwyCbJyWGSL3KdjeXE28AY1Kaog --entrypoint 'set_data' --arg 'Pair "tz1NortRftucvAkD1J58L32EhSVrQEWJCEnB" (Pair (Some (Pair (Pair (Pair 0x42616b65276e27526f6c6c73 True) 0x68747470733a2f2f62616b656e726f6c6c732e636f6d2f72656769737472792e6a736f6e) (Pair (Pair 9100 { "tz1Zrqm4TkJwqTxm5TiyVFh6taXG4Wrq7tko" }) (Pair (Pair (Pair 100000 True) (Pair 6 (Pair 1 0))) (Pair (Pair True 16383) (Pair 100 True)))))) None)'
```

### `bakers new` Create default config

```bash
NAME
    bakers new - Generates template config for a new baker

SYNOPSIS
    bakers new <flags>

DESCRIPTION
    Generates template config for a new baker

FLAGS
    --output_file=OUTPUT_FILE
        path to the file to store the data (optional)
```

### `bakers all` Get all bakers

```bash
NAME
    bakers all - Get all bakers

SYNOPSIS
    bakers all OUTPUT_FILE <flags>

DESCRIPTION
    Get all bakers

POSITIONAL ARGUMENTS
    OUTPUT_FILE
        path to the file

FLAGS
    --raw=RAW
        keep intermediate data representation (default is False)
    --indexer=INDEXER
        which indexer to use to retrieve operation levels [tzkt, tzstats, conseil]
    --network=NETWORK
        Tezos network (default is mainnet)
    --registry_address=REGISTRY_ADDRESS
        address of the registry contract (predefined)
```

### `bakers log` Get recent changes

```bash
NAME
    bakers log - Show registry changes, line by line

SYNOPSIS
    bakers log <flags>

DESCRIPTION
    Show registry changes, line by line

FLAGS
    --output_file=OUTPUT_FILE
        path to the file
    --since=SINCE
        set lower bound, can be level (int) or string "level:700000" "cycle:170"
    --raw=RAW
        keep intermediate data representation (default is False)
    --indexer=INDEXER
        which indexer to use to retrieve operation levels [tzkt, tzstats, conseil]
    --network=NETWORK
        Tezos network (default is mainnet)
    --registry_address=REGISTRY_ADDRESS
        address of the registry contract (predefined)
```

##### Sample output

```bash
738542  Airfoil              subtractLostFeesWhenMissRevelation: true => false
738542  Airfoil              subtractLostRewardsWhenMissRevelation: true => false
738542  Airfoil              payForRevelation: true => false
738542  Airfoil              bakerPaysFromAccounts: [] => ["tz1QH3G2btaWc1vRLNsEfx2gHM7Ad81TeRit"]
738542  Airfoil              bakerOffchainRegistryUrl: "" => "https://airfoil.services/airfoil.json"
738542  Airfoil              openForDelegation: false => true
736381  Crypto Delegate LLC  subtractRewardsFromUninvitedDelegation: true => false
736381  Crypto Delegate LLC  subtractLostFeesWhenMissRevelation: true => false
736381  Crypto Delegate LLC  subtractLostRewardsWhenMissRevelation: true => false
736381  Crypto Delegate LLC  subtractLostFeesWhenAccused: true => false
736381  Crypto Delegate LLC  subtractLostRewardsWhenAccused: true => false
736381  Crypto Delegate LLC  subtractLostDepositsWhenAccused: true => false
736381  Crypto Delegate LLC  compensateMissedEndorsements: false => true
736381  Crypto Delegate LLC  compensateMissedBlocks: false => true
736381  Crypto Delegate LLC  payoutDelay: 6 => 0
736381  Crypto Delegate LLC  subtractPayoutsLessThanMin: true => false
736381  Crypto Delegate LLC  bakerPaysFromAccounts: [] => ["tz1MyXTZmeMCM4yFnrER9LNYDZ9t2rHYDvcH"]
736381  Crypto Delegate LLC  fee: "0.25" => "-80"
736381  Crypto Delegate LLC  bakerOffchainRegistryUrl: "" => "https://www.cryptodelegate.com/files/theme/CDReg.json"
736381  Crypto Delegate LLC  bakerName: "Crypto Delegate" => "Crypto Delegate LLC"
732641  YieldWallet.io       New Baker: tz1Q8QkSBS63ZQnH3fBTiAMPes9R666Rn6Sc
730509  Bake'n'Rolls         minDelegation: "0" => "10"
730226  TezoSteam            minDelegation: "0" => "100"
730226  TezoSteam            bakerPaysFromAccounts: [] => ["tz1YrmJw6Lje27gWqZ94gU9mNavEjkHu1xGc"]
730226  TezoSteam            bakerOffchainRegistryUrl: "" => "https://raw.githubusercontent.com/StakingTeam/TezoSteam/master/info/reg.json"
730151  tezzz                fee: "0.03" => "0.045"
```