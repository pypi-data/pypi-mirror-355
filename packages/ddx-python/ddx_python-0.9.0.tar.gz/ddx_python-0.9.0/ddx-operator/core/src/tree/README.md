# SMT Migration Overview
This document provides an overview of the key / item combinations in the SMT, so that we are aware of the potential side effects in the SMT after changing data structures.

## Item types
1. Empty
2. Trader(Trader)
    * key: **TraderAddress**
    
    * value:
    ```rust 
        pub struct Trader {
            pub avail_ddx_balance: UnscaledI128,
            pub locked_ddx_balance: UnscaledI128,
            pub referral_address: Address,
            pub pay_fees_in_ddx: bool,
            pub access_denied: bool,
        } 
    ```
3. Strategy(Strategy)
    * key: 
        ```rust
        pub struct StrategyKey {
            pub trader_address: TraderAddress,
            pub strategy_id_hash: StrategyIdHash,
        } 
        ```
                
    * value: 
    ```rust
        pub struct Strategy {
            pub strategy_id: StrategyId,
            pub avail_collateral: Balance,
            pub locked_collateral: Balance,
            pub max_leverage: U64,
            pub frozen: bool,
        }
     ```
4. Position(Position)
    * key:
    ```rust
    pub struct PositionKey {
        pub trader_address: TraderAddress,
        pub strategy_id_hash: StrategyIdHash,
        pub symbol: ProductSymbol,
    }
    ```
    
    * value: 
    ```rust
        pub struct Position {
            pub side: PositionSide,
            pub balance: UnscaledI128,
            pub avg_entry_price: UnscaledI128,
        }
    ```
5. BookOrder(BookOrder)
    * key:
    ```rust
    pub struct BookOrderKey {
        pub symbol: ProductSymbol,
        pub order_hash: OrderHash,
    }

    // OrderIntent hashes into OrderHash
    pub struct OrderIntent {
        pub symbol: ProductSymbol,
        pub strategy: StrategyId,
        pub side: OrderSide,
        pub order_type: OrderType,
        pub nonce: Nonce,
        pub amount: UnscaledI128,
        pub price: UnscaledI128,
        pub stop_price: UnscaledI128,
        pub signature: Signature,
    }
    ```
    
    * value: 
    ```rust
        pub struct BookOrder {
            pub side: OrderSide,
            pub amount: UnscaledI128,
            pub price: UnscaledI128,
            pub trader_address: TraderAddress,
            pub strategy_id_hash: StrategyIdHash,
            pub book_ordinal: u64,
            pub time_value: TimeValue,
        }
    ```
6. Price(Price)
    * key:
    ```rust
    pub struct PriceKey {
        pub symbol: ProductSymbol,
        pub index_price_hash: IndexPriceHash,
    }

    // Hashes into IndexPriceHash
    pub struct IndexPrice {
        pub symbol: ProductSymbol,
        pub price: UnscaledI128,
        pub prev_price: UnscaledI128,
        pub timestamp: U64,
    }

    ```

    * value:
    ```rust
    pub struct Price {
        pub index_price: UnscaledI128,
        pub ema: UnscaledI128,
        pub ordinal: u64,
    }
    ```
7. InsuranceFund(Balance)
    * key:
    ```rust
    pub struct InsuranceFundKey([u8; 31]);
    ```
    * value:
    ```rust
    pub struct Balance([Collateral; MAX_COLLATERAL_TYPES]);
    ```
8. Stats(Stats)
    * key:
    ```rust
    pub struct StatsKey {
        pub trader: TraderAddress,
    }
    ```
    * value:
    ```rust
    pub struct Stats {
        pub maker_volume: UnscaledI128,
        pub taker_volume: UnscaledI128,
    }
    ```
9. Signer { ReleaseHash }
    * key: SignerAddress
    * value: Hash
10. Specs(SpecsExpr)
    * key:
    ```rust
    pub struct SpecsKey {
        pub kind: SpecsKind,
        pub name: String,
    }
    ```
    * value: SpecsExpr (String)
11. InsuranceFundContribution(InsuranceFundContribution)
    * key: See InsuranceFund item
    * value:
    ```rust
    pub struct InsuranceFundContribution {
        pub avail_balance: Balance,
        pub locked_balance: Balance,
    }
    ```
12. FeePool(Balance)
    * key:
    ```rust
    pub struct FeePoolKey([u8; 31]);
    ```
    * value: Same as InsuranceFund
13. EpochMetadata(EpochMetadata)
* key:
```rust
pub struct EpochMetadataKey {
    pub epoch_id: u64,
}
```
* value: 
```rust
pub struct EpochMetadata {
    pub next_book_ordinals: HashMap<ProductSymbol, u64>,
}


```
