# Sample Market-Maker Bot

## What it is
A reference client that:
- Connects to the DerivaDEX Trader API  
- Posts multi-level order ladders around a reference price  
- Automatically replaces orders when deviation thresholds are hit  
- Adheres to trade-mining rules and collateral tranches  

## Configuration
Provide a `.env` file or override via CLI:
```ini
[ddx-specs]
ref-px-deviation-to-replace-orders=0.0001
price-offset=0.001
levels-to-quote=10
quantity-per-level=10
deposit-minimum=100000
sleep-rate=5

[deployment-environment-specs]
rpc-url="https://pre.derivadex.io/ganache"
staging-env=pre
collateral-address=0xb69e673309512a9d726f87304c6984054f87a93b
chain-id=1337
verifying-contract=0x1d7022f5b17d2f8b695918fb48fa1089c9f85401
# Provide either one:
private-key=<your_private_key>
mnemonic=<your_mnemonic>
```

## Usage
```bash
python sample_mm_auditor_bot.py --config path/to/.env
```
The bot will begin quoting once on-chain deposits ≥ `deposit-minimum`.
