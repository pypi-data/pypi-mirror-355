[![PyPI - Version](https://img.shields.io/pypi/v/symbiosis-api-client.svg)](https://pypi.org/project/symbiosis-api-client) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/symbiosis-api-client.svg)](https://pypi.org/project/symbiosis-api-client)


# Symbiosis API Client

### Installation

```console
pip install symbiosis-api-client
```

## Some Info

- Python syncronous client for [Symbiosis Finance](https://symbiosis.finance/) REST API
- Client relies on [JS SDK ](https://github.com/symbiosis-finance/js-sdk) in part of  [configuration file](https://github.com/symbiosis-finance/js-sdk/blob/main/src/crosschain/config/mainnet.ts). If there is a new commit, Client will raise `InvalidCommit`
- Partial [Symbiosis Swagger](https://api.symbiosis.finance/crosschain/docs/), not much info
- [Symbiosis API Docs](https://docs.symbiosis.finance/developer-tools/symbiosis-api), what and why


## ToDo Plan:

- [ ] Cover routes:
  - [X] Eth USDT -> Tron USDT
  - [X] Eth USDT -> TON USDT
  - [ ] BSC DAI -> Tron TRX
  - [ ] TON TON -> BSC BNB
- [ ] Make BaseSwap full logic replica
- [X] Main functionality
- [X] Rate limit + Singleton
- [X] Exception Codes
- [X] tox for Python versions
- [X] Pydantic models
- [ ] Test Stuck transactions functionality, [docs here](https://docs.symbiosis.finance/crosschain-liquidity-engine/symbiosis-and-emergencies)
- [ ] Testnet – when there are tokens available on Symbiosis
- [ ] Async client maybe?


-----

## Table of Contents

- [Symbiosis API Client](#symbiosis-api-client)
    - [Installation](#installation)
  - [Some Info](#some-info)
  - [ToDo Plan:](#todo-plan)
  - [Table of Contents](#table-of-contents)
  - [License](#license)


## License

`symbiosis-api-client` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
