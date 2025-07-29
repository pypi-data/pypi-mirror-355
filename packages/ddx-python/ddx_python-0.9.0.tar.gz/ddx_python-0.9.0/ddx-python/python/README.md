# DerivaDEX Python Packages

This package contains all of the Pythonic tooling used in the DerivaDEX
ecosystem.

## Installation

-   Using a conda environment with Python 3.10
-   Using Black opinionated code formatter

## Tests

In general, some things we want to test are:
- data correctness
- invalid input rejection
- overflows/underflow errors
- rounding errors
- breaching of limits
- etc.

### Posting order invariants

1. Users can only post orders on assets that are whitelisted on the exchange
2. Users cannot post orders if they have insufficient available collateral
3. Users can post orders with quantities up to X precision
4. Users can post orders with prices up to X precision
5. Users can post limit orders with quantities between (0, X]
6. Users can post limit orders with prices between (0, X]
7. Users cannot post orders at a price > 2% of the mark price / best level through the other side of the book
8. Users cannot post orders when the mark price is > 10% away from the avg mark price over the past 5 minutes
9. Users cannot increase position if OMF < IMF after order would be placed
10. Users cannot post orders when account MF < MMR
11. Users cannot post orders breaching the maximum notional value

### Matching order invariants

1. Two orders can match only if they are for the same symbol
2. Two orders can match only if they are opposing sides
3. Two orders can match only if they are from different traders (i.e. no self-match)
4. Two orders can match only if prices cross

### Price feed invariants

1. Index price is computed with the specified centralized exchange / ground-truth weighted distribution / composition
2. Index price updates every second iff there is a 1bp difference from the last registered value
3. Mark price is properly computed (using index price, fair price, and premium ema)

### Liquidation invariants

1. Users' accounts are liquidated in full only when MF < MMR
2. If the -liquidation_spread > insurance_fund_cap, results in ADL
3. If there are no maker orders to liquidate against, results in ADL
4. Liquidation spread debit/credit properly applied to insurance fund balance
5. Accounts are sorted in the correct priority for ADL

### Funding rate invariants
TBD

