use crate::{
    execution::validation::Valuation,
    types::{
        accounting::{
            DEFAULT_MAX_LEVERAGE, Position, PositionSide, Price, PriceDirection, PriceMetadata,
            Strategy, TradeSide,
        },
        ethereum::sign_message_with_blockchain_sender,
        primitives::ProductSymbol,
        request::{
            CancelOrderIntent, ModifyOrderIntent, OrderIntent, OrderType, ProfileUpdate,
            WithdrawDDXIntent, WithdrawIntent,
        },
        state::BookOrder,
        transaction::{Cancel, Fill, FillOutcomeMeta, PriceDetailMeta, TradeOutcomeMeta},
    },
};
use core_common::{
    Address, B256, B520, Result,
    types::{
        accounting::MAIN_STRAT,
        primitives::{
            Bytes32, Hash, OrderSide, TimeValue, TokenSymbol, TraderAddress, UnscaledI128,
            as_scaled_fraction,
        },
        state::BlockchainSender,
    },
};
#[cfg(feature = "test_account")]
use core_crypto::test_accounts::*;
use core_crypto::{eip712::HashEIP712, hash_with_eth_prefix, parse_secret_key, sign_message};
use rust_decimal::{
    Decimal,
    prelude::{FromPrimitive, Zero},
};
use serde::Deserialize;
use std::{
    collections::{BTreeMap, HashMap},
    convert::TryInto,
    time::{SystemTime, UNIX_EPOCH},
};

use super::validation::{AccountMetrics, ProductStore};

// Symbol for test underlying markets
pub const ETH: &str = "ETH";
pub const BTC: &str = "BTC";
pub const DOGE: &str = "DOGE";
pub const DDX: &str = "DDX";

// Symbols for test products
pub const BTCP: &str = "BTCP";
pub const DOGEP: &str = "DOGEP";
pub const ETHP: &str = "ETHP";
pub const FUNDP: &str = "FUNDP";
#[cfg(feature = "fixed_expiry_future")]
pub const ETHFH: &str = "ETHFH";
#[cfg(feature = "fixed_expiry_future")]
pub const ETHFM: &str = "ETHFM";
#[cfg(feature = "fixed_expiry_future")]
pub const ETHFU: &str = "ETHFU";
#[cfg(feature = "fixed_expiry_future")]
pub const ETHFZ: &str = "ETHFZ";
pub const ALT_STRAT: &str = "alternate";

pub const DEFAULT_COLLATERAL_AMOUNT: u32 = 100_000;

pub const ETHP_MARKET_SPECS: &str = r#"
(SingleNamePerpetual :name "ETHP"
    :underlying "ETH"
    :tick-size 0.1
    :max-order-notional 1000000
    :max-taker-price-deviation 0.02
    :min-order-size 0.0001
)"#;
pub const BTCP_MARKET_SPECS: &str = r#"
(SingleNamePerpetual :name "BTCP"
    :underlying "BTC"
    :tick-size 1
    :max-order-notional 1000000
    :max-taker-price-deviation 0.02
    :min-order-size 0.00001
)"#;
pub const DOGEP_MARKET_SPECS: &str = r#"
(SingleNamePerpetual :name "DOGEP"
    :underlying "DOGE"
    :tick-size 0.000001
    :max-order-notional 100000
    :max-taker-price-deviation 0.1
    :min-order-size 1
)"#;
pub const INDEX_FUND_MARKET_SPECS: &str = r#"
(IndexFundPerpetual :name "FUNDP"
    :underlying '("ETH" "BTC")
    :weights '(0.5 0.5)
    :rebalance-interval 604800
    :initial-index-price 1000 
    :tick-size 0.1
    :max-order-notional 1000000
    :max-taker-price-deviation 0.02
    :min-order-size 0.0001
)"#;
#[cfg(feature = "fixed_expiry_future")]
pub const ETHFH_MARKET_SPECS: &str = r#"
(QuarterlyExpiryFuture :class-name "ETHF"
    :underlying "ETH"
    :tick-size 0.1
    :max-order-notional 1000000
    :max-taker-price-deviation 0.02
    :min-order-size 0.0001
)"#;

pub const LOCAL_HOSTNAME: &str = "localhost";
pub const LOCAL_MARKET_GATEWAY: &str = r#"
(MarketGateway :hostname "localhost"
    :port 33243
    :symbols '("ETH" "BTC")
    :get-time (Get
        :query (format "/t")
        :reader (jq "[dt]")
    )
    :get-spot-price (Get
        :query (format "/p/{}")
        :reader (jq "[symbol,price]")
    )
    :tr-symbol (sed "s/(?P<base>[A-Z]+)/${base}USDC/;")
)"#;

pub const GEMINI_HOSTNAME: &str = "api.gemini.com";
pub const GEMINI_MARKET_GATEWAY: &str = r#"
(MarketGateway :hostname "api.gemini.com"
    :port 443
    :symbols '("ETH" "BTC")
    :get-time (Get
        :query "/v1/heartbeat"
        :reader (jq "result")
    )
    :get-spot-price (Get
        :query (format "/v2/ticker/{}")
        :reader (jq "[symbol,close]")
    )
    :tr-symbol (sed "s/(?P<base>[A-Z]+)/${base}USD/;")
)"#;

pub const BINANCE_HOSTNAME: &str = "api.binance.com";
pub const BINANCE_MARKET_GATEWAY: &str = r#"
(MarketGateway :hostname "api.binance.com"
    :port 443
    :symbols '("ETH" "BTC")
    :get-time (Get
        :query "/api/v3/time"
        :reader (jq "serverTime")
    )
    :get-spot-price (Get
        :query (format "/api/v3/ticker/price?symbol={}")
        :reader (jq "[symbol,price]")
    )
    :tr-symbol (sed "s/(?P<base>[A-Z]+)/${base}USDC/;")
)"#;

pub fn int_to_address(i: usize) -> Result<TraderAddress> {
    let address: Address = serde_json::from_str(&format!(r#""0x{:040x}""#, i))?;
    Ok(address.into())
}

pub fn indexed_hash_with_eth_prefix(prefix: u8, i: usize) -> Result<Hash> {
    let hash: B256 = serde_json::from_str(&format!(r#""0x{:02x}{:062x}""#, prefix, i))?;
    Ok(hash.into())
}

pub fn indexed_order_hash(side: u8, i: usize, nonce: u32) -> Result<Hash> {
    let hash: B256 = serde_json::from_str(&format!(r#""0x{:02x}{:040x}{:022x}""#, side, i, nonce))?;
    Ok(hash.into())
}

#[derive(Deserialize, Debug, Clone, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct FakeAccount {
    pub max_leverage: u64,
    #[serde(with = "as_scaled_fraction")]
    pub collateral: UnscaledI128,
    #[serde(default)]
    pub positions: HashMap<ProductSymbol, Position>,
}

impl Default for FakeAccount {
    fn default() -> Self {
        FakeAccount {
            max_leverage: DEFAULT_MAX_LEVERAGE,
            collateral: Decimal::from(DEFAULT_COLLATERAL_AMOUNT).into(),
            positions: Default::default(),
        }
    }
}

impl FakeAccount {
    pub fn with_collateral(collateral: Decimal) -> Self {
        FakeAccount {
            max_leverage: DEFAULT_MAX_LEVERAGE,
            collateral: collateral.into(),
            positions: Default::default(),
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
pub struct MarkPriceMap(pub HashMap<ProductSymbol, (Decimal, PriceDirection)>);

impl ProductStore for MarkPriceMap {
    fn mark_price(&self, symbol: &ProductSymbol) -> Decimal {
        self.mark_price_detail(symbol).0
    }

    fn direction(&self, symbol: &ProductSymbol) -> PriceDirection {
        self.mark_price_detail(symbol).1
    }

    fn mark_price_detail(&self, symbol: &ProductSymbol) -> (Decimal, PriceDirection) {
        *self.0.get(symbol).unwrap()
    }

    fn listed_symbols(&self) -> Vec<ProductSymbol> {
        self.0.keys().cloned().collect()
    }

    fn tradable_symbols(&self) -> Vec<ProductSymbol> {
        self.listed_symbols()
    }
}

#[derive(Deserialize, Debug, Clone, Default, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ExpectedAccount {
    #[serde(with = "as_scaled_fraction")]
    pub collateral: UnscaledI128,
    pub max_leverage: u64, // TODO: Remove
    #[serde(default)]
    pub positions: HashMap<ProductSymbol, ExpectedPosition>,
    pub total_value: Decimal,
    pub notional_value: Decimal,
}

impl ExpectedAccount {
    pub fn with_single_position(
        strategy: &Strategy,
        symbol: &str,
        realized_pnl: Decimal,
        total_value: Decimal,
        notional_value: Decimal,
        balance: Decimal,
        entry_price: Decimal,
    ) -> Self {
        let mut positions: HashMap<ProductSymbol, ExpectedPosition> = HashMap::new();
        if balance != Decimal::zero() {
            let expected_position = ExpectedPosition {
                side: if balance.is_sign_negative() {
                    PositionSide::Short
                } else {
                    PositionSide::Long
                },
                balance: balance.abs().into(),
                avg_entry_price: entry_price.into(),
            };
            positions.insert(symbol.into(), expected_position);
        }
        let collateral = *strategy.avail_collateral[TokenSymbol::USDC] + realized_pnl;
        // We don't insert any position because it will get populated by our test logic
        ExpectedAccount {
            collateral: collateral.into(),
            max_leverage: strategy.max_leverage,
            positions,
            total_value,
            notional_value,
        }
    }

    pub fn entry_price(&self) -> Decimal {
        self.positions
            .values()
            .map(|p| *p.avg_entry_price)
            .sum::<Decimal>()
            / Decimal::from(self.positions.len())
    }

    pub fn fees_as_maker(&self) -> Decimal {
        self.positions
            .values()
            .map(|p| TradeSide::Maker.trading_fee(*p.balance, *p.avg_entry_price))
            .sum()
    }

    pub fn fees_as_taker(&self) -> Decimal {
        self.positions
            .values()
            .map(|p| TradeSide::Taker.trading_fee(*p.balance, *p.avg_entry_price))
            .sum()
    }

    pub fn first_position(&self) -> ExpectedPosition {
        let (_, position) = self.positions.iter().next().unwrap();
        position.clone()
    }

    pub fn assert_eq(&self, account: &AccountMetrics) {
        tracing::debug!(
            "Comparing account / expected: {:#?} / {:#?}",
            account.strategy,
            self
        );
        assert_eq!(
            self.positions.len(),
            account.strategy.positions.len(),
            "expected positions == nb positions"
        );
        for (symbol, position) in account.strategy.positions.iter() {
            let expected_position = self.positions.get(symbol);
            assert!(
                expected_position.is_some(),
                "Position {:?} not in expected account",
                symbol
            );
            assert_eq!(
                *position.balance,
                *expected_position.unwrap().balance,
                "balance == expected_balance"
            );
            assert_eq!(
                *position.avg_entry_price,
                *expected_position.unwrap().avg_entry_price,
                "avg_entry_price == expected_avg_entry_price"
            );
            assert_eq!(
                position.side,
                expected_position.unwrap().side,
                "side == expected_side"
            );
        }
        assert_eq!(
            account.margin_value(),
            *self.collateral,
            "collateral == expected_collateral"
        );
        assert_eq!(
            account.notional_value(),
            self.notional_value,
            "notional == expected_notional"
        );
        assert_eq!(
            account.total_value(),
            self.total_value,
            "total == expected_total"
        );
    }
}

#[derive(Debug, Clone, Default, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ExpectedPosition {
    /// The position side: Long = 0, Short = 1
    pub side: PositionSide,
    /// The position size denominated in the same unit as the underlying
    #[serde(with = "as_scaled_fraction")]
    pub balance: UnscaledI128,
    /// The average entry price (updated when adding to the position)
    #[serde(with = "as_scaled_fraction")]
    pub avg_entry_price: UnscaledI128,
}

impl From<ExpectedPosition> for Position {
    fn from(value: ExpectedPosition) -> Self {
        Position {
            side: value.side,
            balance: value.balance,
            avg_entry_price: value.avg_entry_price,
        }
    }
}

#[derive(Debug, Clone, Default, Deserialize)]
pub struct ExpectedOrderBook {
    pub bids: BTreeMap<Decimal, BookOrder>,
    pub asks: BTreeMap<Decimal, BookOrder>,
}

impl ExpectedOrderBook {
    pub fn assert_eq(&self, bids: &[BookOrder], asks: &[BookOrder]) {
        assert_eq!(self.bids.len(), bids.len(), "bids length");
        assert_eq!(self.asks.len(), asks.len(), "asks length");
        for bid in bids.iter() {
            let price = *bid.price;
            assert_eq!(self.bids.get(&price).unwrap(), bid, "bid == expected bid");
        }
        for ask in asks.iter() {
            let price = *ask.price;
            assert_eq!(self.asks.get(&price).unwrap(), ask, "ask == expected ask");
        }
    }
}

pub fn fake_order<T, P, F>(
    trader: T,
    symbol: P,
    strategy: &str,
    side: OrderSide,
    amount: F,
    price: F,
    post_only: bool,
) -> OrderIntent
where
    T: Into<TraderAddress> + Copy,
    P: Into<ProductSymbol>,
    F: Into<f64>,
{
    let mut order = OrderIntent {
        symbol: symbol.into(),
        strategy: strategy.into(),
        side,
        order_type: OrderType::Limit { post_only },
        nonce: nonce(),
        amount: Decimal::from_f64(amount.into()).unwrap().into(),
        price: Decimal::from_f64(price.into()).unwrap().into(),
        stop_price: Default::default(),
        session_key_signature: Default::default(),
        signature: Default::default(),
    };
    sign_order_as(&mut order, trader);
    order
}

pub fn fake_order_with_key<P, F>(
    key: &str,
    symbol: P,
    strategy: &str,
    side: OrderSide,
    amount: F,
    price: F,
) -> OrderIntent
where
    P: Into<ProductSymbol>,
    F: Into<f64>,
{
    let mut order = OrderIntent {
        symbol: symbol.into(),
        strategy: strategy.into(),
        side,
        order_type: OrderType::Limit { post_only: false },
        nonce: nonce(),
        amount: Decimal::from_f64(amount.into()).unwrap().into(),
        price: Decimal::from_f64(price.into()).unwrap().into(),
        stop_price: Default::default(),
        session_key_signature: Default::default(),
        signature: Default::default(),
    };
    let order_hash = order.hash_eip712();
    let secret_key = parse_secret_key(key).unwrap();
    let signature = sign_message(&secret_key, order_hash.into()).unwrap();
    order.signature = signature.into();
    order
}

pub fn fake_market_order<T, P, F>(
    trader: T,
    symbol: P,
    strategy: &str,
    side: OrderSide,
    amount: F,
) -> OrderIntent
where
    T: Into<TraderAddress> + Copy,
    P: Into<ProductSymbol>,
    F: Into<f64>,
{
    let mut order = OrderIntent {
        symbol: symbol.into(),
        strategy: strategy.into(),
        side,
        order_type: OrderType::Market,
        nonce: nonce(),
        amount: Decimal::from_f64(amount.into()).unwrap().into(),
        price: Default::default(),
        stop_price: Default::default(),
        session_key_signature: Default::default(),
        signature: Default::default(),
    };
    sign_order_as(&mut order, trader);
    order
}

// TODO: Improve as more convenient test scenario setup.
pub enum FakeOrderSet {
    A,
}

pub fn fake_orders(fake_set: FakeOrderSet) -> Vec<OrderIntent> {
    let mut orders = vec![];
    let alice: TraderAddress = ALICE.into();
    let bob: TraderAddress = BOB.into();
    match fake_set {
        FakeOrderSet::A => {
            orders.push(fake_order(
                alice,
                ETHP,
                MAIN_STRAT,
                OrderSide::Ask,
                20,
                235,
                false,
            ));
            orders.push(fake_order(
                alice,
                ETHP,
                MAIN_STRAT,
                OrderSide::Ask,
                20,
                241,
                false,
            ));
            orders.push(fake_order(
                alice,
                ETHP,
                MAIN_STRAT,
                OrderSide::Ask,
                20,
                247,
                false,
            ));
            orders.push(fake_order(
                bob,
                ETHP,
                MAIN_STRAT,
                OrderSide::Bid,
                20,
                250,
                false,
            ));
            orders.push(fake_order(
                bob,
                ETHP,
                MAIN_STRAT,
                OrderSide::Bid,
                20,
                250,
                false,
            ));
            orders.push(fake_order(
                bob,
                ETHP,
                MAIN_STRAT,
                OrderSide::Bid,
                100,
                250,
                false,
            ));
            orders.push(fake_order(
                alice,
                ETHP,
                MAIN_STRAT,
                OrderSide::Ask,
                20,
                225,
                false,
            ));
            orders.push(fake_order(
                alice,
                ETHP,
                MAIN_STRAT,
                OrderSide::Ask,
                20,
                230,
                false,
            ));
            orders.push(fake_order(
                alice,
                ETHP,
                MAIN_STRAT,
                OrderSide::Ask,
                20,
                245,
                false,
            ));
        }
    }
    orders
}

#[derive(Default)]
pub struct FakeClock {
    time_value: TimeValue,
}

impl FakeClock {
    pub fn now(&self) -> TimeValue {
        self.time_value
    }

    pub fn advance_by(&mut self, duration_in_secs: u64) -> TimeValue {
        self.time_value += duration_in_secs;
        self.now()
    }

    pub fn tick(&mut self) -> TimeValue {
        self.time_value += 1;
        self.now()
    }
}

pub fn current_time() -> TimeValue {
    FakeClock::default().now()
}

// TODO: Review whether using this for unit tests is appropriate vs a counter
/// A timestamp based nonce for unit testing
pub fn nonce() -> Hash {
    as_nonce(micros_timestamp())
}

fn micros_timestamp() -> u64 {
    // Assuming this century's micros timestamp fits 64 bits
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_millis()
        .try_into()
        .unwrap()
}

pub fn as_nonce(value: u64) -> Hash {
    // Smallest at the end to preserve ordering
    // For example, number 0x61626364 would be stored: 0x0000000000000000000000000000000000000000000000000000000061626364
    Bytes32::from(value).into()
}

pub fn price_with_single_name_perp_defaults(
    index_price: UnscaledI128,
    ordinal: u64,
) -> PriceDetailMeta {
    PriceDetailMeta::new(
        Default::default(),
        Price::from_price_value(index_price, ordinal, Default::default()),
        PriceMetadata::SingleNamePerpetual,
        PriceDirection::Up,
    )
}

pub fn sign_nonce_with_blockchain_sender<'a, T: Into<&'a BlockchainSender>>(
    nonce: Hash,
    signer: T,
) -> B520 {
    let message_hash = hash_with_eth_prefix(nonce.into());
    sign_message_with_blockchain_sender(signer.into(), message_hash).unwrap()
}

pub fn sign_cancel_order_with_blockchain_sender<'a, T: Into<&'a BlockchainSender>>(
    intent: &mut CancelOrderIntent,
    signer: T,
) {
    intent.nonce = nonce(); // TODO: Why is this here?
    let hash = intent.hash_eip712();
    let signature = sign_message_with_blockchain_sender(signer.into(), hash.into()).unwrap();
    intent.signature = signature.into();
}

pub fn sign_order_with_blockchain_sender<'a, T: Into<&'a BlockchainSender>>(
    order: &mut OrderIntent,
    signer: T,
) {
    order.nonce = nonce(); // TODO: Why is this here?
    let order_hash = order.hash_eip712();
    let signature = sign_message_with_blockchain_sender(signer.into(), order_hash.into()).unwrap();
    order.signature = signature.into();
}

pub fn sign_withdraw_with_blockchain_sender<'a, T: Into<&'a BlockchainSender>>(
    intent: &mut WithdrawIntent,
    signer: T,
) {
    intent.nonce = nonce(); // TODO: Why is this here?
    let hash = intent.hash_eip712();
    let signature = sign_message_with_blockchain_sender(signer.into(), hash.into()).unwrap();
    intent.signature = signature.into();
}

pub fn sign_withdraw_ddx_with_blockchain_sender<'a, T: Into<&'a BlockchainSender>>(
    intent: &mut WithdrawDDXIntent,
    signer: T,
) {
    intent.nonce = nonce();
    let hash = intent.hash_eip712();
    let signature = sign_message_with_blockchain_sender(signer.into(), hash.into()).unwrap();
    intent.signature = signature.into();
}

/// Register an API client for the trader
pub fn sign_nonce_as(nonce: Hash, signer: TraderAddress) -> B520 {
    let secret_key = get_secret_key(&signer).unwrap();
    let message_hash = hash_with_eth_prefix(nonce.into());
    sign_message(&secret_key, message_hash).unwrap()
}

pub fn sign_cancel_order_as(intent: &mut CancelOrderIntent, signer: TraderAddress) {
    intent.nonce = nonce(); // TODO: Why is this here?
    let hash = intent.hash_eip712();
    let secret_key = get_secret_key(&signer).unwrap();
    let signature = sign_message(&secret_key, hash.into()).unwrap();
    intent.signature = signature.into();
}

pub fn sign_order_as<T: Into<TraderAddress>>(order: &mut OrderIntent, signer: T) {
    order.nonce = nonce(); // TODO: Why is this here?
    let order_hash = order.hash_eip712();
    let secret_key = get_secret_key(&signer.into()).unwrap();
    let signature = sign_message(&secret_key, order_hash.into()).unwrap();
    order.signature = signature.into();
}

pub fn sign_modify_as<T: Into<TraderAddress>>(order: &mut ModifyOrderIntent, signer: T) {
    order.nonce = nonce(); // TODO: Why is this here?
    let order_hash = order.hash_eip712();
    let secret_key = get_secret_key(&signer.into()).unwrap();
    let signature = sign_message(&secret_key, order_hash.into()).unwrap();
    order.signature = signature.into();
}

pub fn sign_profile_update_as<T: Into<TraderAddress>>(update: &mut ProfileUpdate, signer: T) {
    let update_hash = update.hash_eip712();
    let secret_key = get_secret_key(&signer.into()).unwrap();
    let signature = sign_message(&secret_key, update_hash.into()).unwrap();
    update.signature = signature.into();
}

pub fn sign_withdraw_as<T: Into<TraderAddress>>(intent: &mut WithdrawIntent, signer: T) {
    intent.nonce = nonce(); // TODO: Why is this here?
    let hash = intent.hash_eip712();
    let secret_key = get_secret_key(&signer.into()).unwrap();
    let signature = sign_message(&secret_key, hash.into()).unwrap();
    intent.signature = signature.into();
}

pub fn sign_withdraw_ddx_as(intent: &mut WithdrawDDXIntent, signer: TraderAddress) {
    intent.nonce = nonce();
    let hash = intent.hash_eip712();
    let secret_key = get_secret_key(&signer).unwrap();
    let signature = sign_message(&secret_key, hash.into()).unwrap();
    intent.signature = signature.into();
}

pub fn get_cancels(trade_outcomes: &[TradeOutcomeMeta]) -> Vec<Cancel> {
    trade_outcomes
        .iter()
        .filter_map(|o| {
            if let TradeOutcomeMeta::Cancel(c) = o {
                Some(c.cancel.clone())
            } else {
                None
            }
        })
        .collect()
}

pub fn get_fills(trade_outcomes: &[TradeOutcomeMeta]) -> Vec<Fill<FillOutcomeMeta>> {
    trade_outcomes
        .iter()
        .filter_map(|o| {
            if let TradeOutcomeMeta::Fill(f) = o {
                Some(f.fill.clone())
            } else {
                None
            }
        })
        .collect()
}

pub fn total_fees(trade_outcomes: &[TradeOutcomeMeta]) -> (Decimal, Decimal) {
    get_fills(trade_outcomes)
        .iter()
        .fold((Decimal::zero(), Decimal::zero()), |acc, fill| {
            let (fees_default, fees_ddx) = fill.total_fees();
            (acc.0 + fees_default, acc.1 + fees_ddx)
        })
}
