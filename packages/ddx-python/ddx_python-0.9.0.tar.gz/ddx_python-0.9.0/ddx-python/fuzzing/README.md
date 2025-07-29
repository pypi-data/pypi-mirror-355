# ddx-python-fuzzing

Whitebox fuzzing suite for DerivaDEX components (market-maker, market-taker, auditor, chaos bots…).

## Installation

First, ensure that the `ddx-python` dependency is correctly configured.

From this `fuzzing/` folder:

```bash
python3 -m pip install .
```

## Configuration

Copy and customize any `.conf.json.template`:

```bash
cp whitebox_fuzzing/strategy.conf.json.template ./strategy.conf.json
# edit RPC URL, initial balances, etc.
```
