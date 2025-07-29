# Mock Services

Lightweight Flask mocks for DDX price feeds and KYC endpoints. Used for integration testing.

## Installation

First, ensure that the `ddx-python` dependency is correctly configured.

From the `mocks/` folder:

```bash
python3 -m pip install .
```

## Price Feed Fuzzer

1. Copy the template and edit your config:
   ```bash
   cp price_feed_fuzzer.conf.json.template \
      $CONFIG_DIR/price_feed_fuzzer.conf.json
   ```
2. Set environment variables:
   - `CONFIG_DIR`: path to your JSON config file
   - `CERTS_DIR`: path to `pricefeedfuzzer.crt` and `.key`

### Run

```bash
# direct
python3 -m price_feed_fuzzer

# or with Gunicorn
gunicorn price_feed_fuzzer:gunicorn_app
```

### Endpoints

- `GET /price/<symbol>`  
  → `{ "price": <Decimal>, "symbol": "<symbol>" }`
- `GET /time`  
  → `{ "time": <unix_timestamp> }`

## Mock KYC Service

No config required.

### Run

```bash
# direct
python3 -m mock_kyc

# or with Gunicorn
gunicorn mock_kyc:gunicorn_app
```

### Endpoints

- `GET /api/v3/brokerage/payment_methods/<id>`  
  Stubbed payment‐method JSON.
- `GET /kyc/1.0/connect/beta_derivadex_b7fc6/recordId/<id>`  
  Stubbed KYC status JSON.
