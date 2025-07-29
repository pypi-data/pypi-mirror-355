#[cfg(feature = "fixed_expiry_future")]
use crate::{
    constants::TX_FUTURES_EXPIRY, specs::quarterly_expiry_future::Quarter,
    types::identifiers::PositionKey,
};
use crate::{
    constants::{
        TX_CANCEL, TX_CANCEL_ALL, TX_COMPLETE_FILL, TX_DISASTER_RECOVERY, TX_EPOCH_MARKER,
        TX_FEE_DISTRIBUTION, TX_FUNDING, TX_INSURANCE_FUND_UPDATE, TX_INSURANCE_FUND_WITHDRAW,
        TX_LIQUIDATION, TX_PARTIAL_FILL, TX_PNL_REALIZATION, TX_POST, TX_PRICE_CHECKPOINT,
        TX_SIGNER_REGISTERED, TX_SPECS_UPDATE, TX_STRATEGY_UPDATE, TX_TRADABLE_PRODUCT_UPDATE,
        TX_TRADE_MINING, TX_TRADER_UPDATE, TX_WITHDRAW, TX_WITHDRAW_DDX,
    },
    specs::types::SpecsUpdate,
    types::{
        accounting::{
            MarkPriceMetadata, PositionSide, Price, PriceDirection, PriceMetadata, TradeSide,
        },
        checkpoint::SignedCheckpoint,
        identifiers::{
            InsuranceFundContributorAddress, SignerAddress, StrategyIdHash, StrategyKey,
        },
        primitives::{IndexPriceHash, OrderHash, ProductSymbol},
        request::{
            MatchableIntent as MatchableIntentTrait, ModifyOrderIntent, OrderIntent, OrderType,
            RequestIndex,
        },
        state::{BookOrder, Epoch, Stats, TradableProductKey},
    },
};
use core_common::{
    Error, Result, bail,
    types::{
        accounting::StrategyId,
        global::TokenAddress,
        identifiers::ReleaseHash,
        primitives::{
            CustodianAddress, Hash, OrderSide, RecordedAmount, RecordedFee, StampedTimeValue,
            TimeValue, TokenSymbol, TraderAddress, UnscaledI128,
        },
        transaction::{EpochId, Tx},
    },
};
#[cfg(feature = "python")]
use pyo3::prelude::*;
use rust_decimal::{Decimal, prelude::Zero};
use serde::{Deserialize, Serialize};
#[cfg(feature = "test_harness")]
use serde::{Deserializer, Serializer, ser::SerializeSeq};
use std::{
    collections::{BTreeMap, HashMap},
    convert::TryFrom,
    ops::{Deref, DerefMut},
};
use strum_macros::{EnumDiscriminants, EnumString};

/// Represents different types of log messages related to transaction processing.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "t", content = "c")]
pub enum TxLogMessage {
    #[serde(rename_all = "camelCase")]
    /// A log entry for a snapshot of the state at a given epoch.
    Snapshot {
        epoch_id: u64,
        leaves: HashMap<Hash, String>,
        offset: u64,
    },
    /// Transaction series send when catching up with the transaction log.
    ///
    /// Messages of this type deliver transactions from the beginning of the
    /// active epoch for each new client on connection.
    Head(Tx<Event>),
    /// Transaction series at the end of the transaction log.
    ///
    /// Messages of this type stream the transaction log in real time to caught-up clients.
    Tail(Tx<Event>),
}

/// Group of attributes that uniquely identify a blockchain transaction.
#[derive(Debug, Default, Clone, Copy, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct BlockTxStamp {
    pub block_number: u64,
    pub tx_hash: Hash,
}

#[derive(Debug, Default, Clone, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PnlEntry {
    /// Revised average entry price post-settlement.
    pub new_avg_entry_price: RecordedAmount,
    /// Raw profit or loss amount for this position.
    pub pnl_amount: Decimal,
}

/// Realized profit and losses data of a trade.
///
/// Holds all data necessary data to apply to a strategy and verify the resulting balance.
///
/// These fields and numeric types allow us to verify without rounding errors that:
/// `new_balance_rounded == old_balance_rounded.apply(pnl.amount).apply(-pnl.fee)`
#[derive(Debug, Default, Clone, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RealizedPnl {
    /// Raw profit or loss amount.
    pub pnl_amount: Decimal,
    /// Unrounded calculated fee, converted and discounted if paid in DDX.
    pub discounted_fee: Decimal,
    /// Updated collateral balance post-trade.
    pub new_balance: RecordedAmount,
    /// Raw profit or loss amounts for each individual position with new average entry prices.
    /// TODO 3591: In the meta variation, this should be replaced by a `PositionUpdate` value which allows to verify the impact on the updated db position record.
    pub individual_pnls: HashMap<ProductSymbol, PnlEntry>,
    /// Actual net amount including discounts applied to the balance.
    ///
    /// The option indicates the finality of the realized PNL lifecycle.
    pub amount: Option<RecordedAmount>,
    /// Indicates the collateral asset used for the funding payment.
    pub collateral_address: TokenAddress,
}

impl RealizedPnl {
    pub fn net_amount(&self) -> RecordedAmount {
        debug_assert!(self.amount.is_some(), "Realized PNL not finalized");
        self.amount.unwrap()
    }
}

/// Record of a strategy's position update.
#[derive(Debug, Default, Clone, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct PositionUpdate {
    /// Amount of the position update.
    pub amount: RecordedAmount,
    /// Updated position reflecting the impact of the position update.
    pub balance: Decimal,
    pub side: PositionSide,
    pub avg_entry_price: Decimal,
}

/// Record of balance update.
///
/// This generic structure applies to strategy margin, position, and other kinds of balances.
/// The available and locked amounts are calculated after the transaction is applied.
#[derive(Debug, Default, PartialEq, Clone, Deserialize, Serialize)]
pub struct BalanceUpdate {
    /// Original user-specified amount.
    pub amount: RecordedAmount,
    /// Balance available after applying the amount.
    pub available: RecordedAmount,
}

impl BalanceUpdate {
    pub fn new(amount: RecordedAmount, balance: RecordedAmount) -> Self {
        BalanceUpdate {
            amount,
            available: balance,
        }
    }
}

impl From<BalanceUpdate> for LiquidBalanceUpdate {
    fn from(value: BalanceUpdate) -> Self {
        LiquidBalanceUpdate {
            amount: value.amount,
            available: value.available,
            locked: None,
            kickback: None,
        }
    }
}

/// Record of balance update that includes a locked amount (can be withdrawn on-chain).
#[derive(Debug, Default, PartialEq, Clone, Deserialize, Serialize)]
pub struct LiquidBalanceUpdate {
    /// Original user-specified amount.
    pub amount: RecordedAmount,
    /// Net available balance after applying the amount and returning the kickback if any.
    pub available: RecordedAmount,
    /// Updated locked collateral balance.
    ///
    /// Optional, as not all balance updates affect locked collateral.
    /// Included for transactions impacting locked collateral.
    pub locked: Option<RecordedAmount>,
    /// Portion of the amount applied to the locked balance.
    ///
    /// For example, suppose deposits have limits, which can't be enforced in the smart contract because state freshness.
    /// Instead, the contract allows deposits to exceed the limit, but the excess is returned (kicked back) to the locked balance.
    /// This allows the trader to claim the funds on-chain just like a regular withdrawal.
    pub kickback: Option<RecordedAmount>,
}

impl LiquidBalanceUpdate {
    /// Create an available balance update, ensuring that a locked balance is only given in context of a kickback.
    ///
    /// The optional `kickback` tuple contains the recorded kickback amount and consequent locked balance.
    pub fn available(
        amount: RecordedAmount,
        balance: RecordedAmount,
        kickback: Option<(RecordedAmount, RecordedAmount)>,
    ) -> Self {
        LiquidBalanceUpdate {
            amount,
            available: balance,
            locked: kickback.map(|k| k.1),
            kickback: kickback.map(|k| k.0),
        }
    }

    pub fn locked(
        amount: RecordedAmount,
        balance: RecordedAmount,
        available: RecordedAmount,
    ) -> Self {
        LiquidBalanceUpdate {
            amount,
            available,
            locked: Some(balance),
            kickback: None,
        }
    }

    /// Returns the net amount after subtracting the kickback if any.
    pub fn net_amount(&self) -> Decimal {
        *self.amount - *self.kickback.unwrap_or_default()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize, EnumDiscriminants)]
#[strum_discriminants(derive(EnumString))]
pub enum IntentRejection {
    Order(OrderRejection),
    Withdraw(WithdrawRejection),
    Cancel(CancelRejection),
    ProfileUpdate(ProfileUpdateRejection),
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize, Copy, EnumString)]
pub enum OrderRejectionReason {
    SelfMatch,
    SolvencyGuard,
    MaxTakerPriceDeviation,
    NoLiquidity,
    InvalidStrategy,
    PostOnlyViolation,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize)]
pub struct OrderRejection {
    pub order_hash: OrderHash,
    pub trader_address: TraderAddress,
    pub strategy_id_hash: StrategyIdHash,
    pub amount: RecordedAmount,
    pub symbol: ProductSymbol,
    pub reason: OrderRejectionReason,
}

impl std::fmt::Display for OrderRejection {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "Order Hash: {:?}, Reason: {:?}",
            self.order_hash, self.reason
        )
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize, Copy, EnumString)]
pub enum WithdrawRejectionReason {
    InvalidStrategy,
    InvalidTrader,
    InvalidInsuranceFundContribution,
    MaxWithdrawalAmount,
    InsufficientDDXBalance,
    InsufficientInsuranceFundContribution,
    InsufficientRemainingInsuranceFund,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize)]
pub struct WithdrawRejection {
    pub currency: TokenSymbol,
    pub trader_address: TraderAddress,
    pub strategy_id_hash: Option<StrategyIdHash>,
    pub amount: RecordedAmount,
    pub insurance_fund: bool,
    pub reason: WithdrawRejectionReason,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize, Copy, EnumString)]
pub enum CancelRejectionReason {
    InvalidOrder,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize)]
pub struct CancelRejection {
    pub order_hash: OrderHash,
    pub trader_address: TraderAddress,
    pub symbol: ProductSymbol,
    pub reason: CancelRejectionReason,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize, Copy, EnumString)]
pub enum ProfileUpdateRejectionReason {
    InvalidTrader,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize)]
pub struct ProfileUpdateRejection {
    pub trader_address: TraderAddress,
    pub reason: ProfileUpdateRejectionReason,
}

pub type Ordinal = u64;

/// One (of potentially many) operations that result from executing a request.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ExecutionOps {
    /// Created a transaction meaning the state transitioned
    StateTransitioning(Vec<Tx<EventMeta>>),
    /// Did not create any transaction during execution meaning the state did not transition
    NonStateTransitioning(Vec<NoTx>),
}

/// A trait for providing descriptive information about transaction event instances.
pub trait EventDescriptor: std::fmt::Debug {
    fn discriminant(&self) -> u8;
    fn kind(&self) -> String {
        let event_repr = format!("{:?}", self);
        // TODO 3503: Is this a safe and intuitive way to get the name of an enum variant?
        match event_repr.split_once(['(', '{']) {
            Some(name) => name.0.trim().to_string(),
            None => event_repr,
        }
    }
}

/// Core transaction event data
///
/// This enum represents the core data for various types of transactions. Each variant
/// encapsulates the essential data needed for the transaction type, conforming to the
/// requirements for auditing and transaction integrity verification.
#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
#[serde(tag = "t", content = "c")]
#[non_exhaustive]
pub enum Event {
    // FIXME 3503: Ensure compatibility with txlog clients.
    PartialFill(OrderMatchOutcome<TradeOutcome>),
    CompleteFill(OrderMatchOutcome<TradeOutcome>),
    // TODO 3591: Data does not include the symbol? Is it not a problem for verification?
    Post(OrderMatchOutcome<TradeOutcome>),
    Cancel(Cancel),
    CancelAll(CancelAll),
    Liquidation(Liquidations<TradeOutcome, AdlOutcome, RecordedAmount>),
    StrategyUpdate(StrategyUpdate<RecordedAmount>),
    TraderUpdate(TraderUpdate<RecordedAmount>),
    Withdraw(Withdraw<RecordedAmount, StrategyIdHash>),
    WithdrawDDX(WithdrawDDX<RecordedAmount>),
    InsuranceFundWithdraw(InsuranceFundWithdraw<RecordedAmount>),
    PriceCheckpoint(HashMap<ProductSymbol, PriceDetail>),
    PnlRealization(PnlRealization),
    Funding(Funding),
    TradeMining(TradeMining<RecordedAmount>),
    #[cfg(feature = "fixed_expiry_future")]
    FuturesExpiry(FuturesExpiry),
    EpochMarker(EpochMarker),
    SignerRegistered(Identity),
    SpecsUpdate(SpecsUpdate),
    TradableProductUpdate(TradableProductUpdate),
    InsuranceFundUpdate(InsuranceFundUpdate<RecordedAmount>),
    FeeDistribution(FeeDistribution),
    DisasterRecovery,
}

impl EventDescriptor for Event {
    fn discriminant(&self) -> u8 {
        let d = match self {
            Event::PartialFill(..) => TX_PARTIAL_FILL,
            Event::CompleteFill(..) => TX_COMPLETE_FILL,
            Event::Post(..) => TX_POST,
            Event::Cancel(..) => TX_CANCEL,
            Event::CancelAll(..) => TX_CANCEL_ALL,
            Event::Liquidation(..) => TX_LIQUIDATION,
            Event::StrategyUpdate(..) => TX_STRATEGY_UPDATE,
            Event::TraderUpdate(..) => TX_TRADER_UPDATE,
            Event::Withdraw(..) => TX_WITHDRAW,
            Event::WithdrawDDX(..) => TX_WITHDRAW_DDX,
            Event::PriceCheckpoint(..) => TX_PRICE_CHECKPOINT,
            Event::PnlRealization(..) => TX_PNL_REALIZATION,
            Event::Funding(..) => TX_FUNDING,
            #[cfg(feature = "fixed_expiry_future")]
            Event::FuturesExpiry(..) => TX_FUTURES_EXPIRY,
            Event::TradeMining(..) => TX_TRADE_MINING,
            Event::SpecsUpdate(..) => TX_SPECS_UPDATE,
            Event::TradableProductUpdate(..) => TX_TRADABLE_PRODUCT_UPDATE,
            Event::EpochMarker(..) => TX_EPOCH_MARKER,
            Event::SignerRegistered { .. } => TX_SIGNER_REGISTERED,
            Event::InsuranceFundUpdate(..) => TX_INSURANCE_FUND_UPDATE,
            Event::InsuranceFundWithdraw(..) => TX_INSURANCE_FUND_WITHDRAW,
            Event::FeeDistribution(..) => TX_FEE_DISTRIBUTION,
            Event::DisasterRecovery => TX_DISASTER_RECOVERY,
        };
        d as u8
    }
}

pub type PriceCheckpointsMap = HashMap<ProductSymbol, PriceDetailMeta>;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PriceCheckpointsMeta {
    pub checkpoints: PriceCheckpointsMap,
    pub order_rejection: Option<OrderRejection>,
}

impl PriceCheckpointsMeta {
    pub fn new(
        checkpoints: PriceCheckpointsMap,
        maybe_order_rejection: Option<OrderRejection>,
    ) -> Self {
        PriceCheckpointsMeta {
            checkpoints,
            order_rejection: maybe_order_rejection,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "t", content = "c")]
pub enum MatchableIntent {
    OrderIntent(OrderIntent),
    ModifyOrderIntent(ModifyOrderIntent),
}

impl MatchableIntentTrait for MatchableIntent {
    fn symbol(&self) -> ProductSymbol {
        match self {
            Self::OrderIntent(intent) => intent.symbol(),
            Self::ModifyOrderIntent(intent) => intent.symbol(),
        }
    }

    fn side(&self) -> OrderSide {
        match self {
            Self::OrderIntent(intent) => intent.side(),
            Self::ModifyOrderIntent(intent) => intent.side(),
        }
    }

    fn strategy(&self) -> StrategyId {
        match self {
            Self::OrderIntent(intent) => intent.strategy(),
            Self::ModifyOrderIntent(intent) => intent.strategy(),
        }
    }

    fn price(&self) -> UnscaledI128 {
        match self {
            Self::OrderIntent(intent) => intent.price(),
            Self::ModifyOrderIntent(intent) => intent.price(),
        }
    }

    fn amount(&self) -> UnscaledI128 {
        match self {
            Self::OrderIntent(intent) => intent.amount(),
            Self::ModifyOrderIntent(intent) => intent.amount(),
        }
    }

    fn stop_price(&self) -> UnscaledI128 {
        match self {
            Self::OrderIntent(intent) => intent.stop_price(),
            Self::ModifyOrderIntent(intent) => intent.stop_price(),
        }
    }

    fn order_type(&self) -> OrderType {
        match self {
            Self::OrderIntent(intent) => intent.order_type(),
            Self::ModifyOrderIntent(intent) => intent.order_type(),
        }
    }

    fn book_order(&self, book_ordinal: Ordinal, time_value: TimeValue) -> Result<BookOrder> {
        match self {
            Self::OrderIntent(intent) => intent.book_order(book_ordinal, time_value),
            Self::ModifyOrderIntent(intent) => intent.book_order(book_ordinal, time_value),
        }
    }
}

/// Extended transaction event with metadata
///
/// The `EventMeta` enum parallels the `Event` enum but encompasses additional metadata,
/// enriching each event with supplementary information. This metadata, while not part of the
/// core transaction record required for auditing, is required for populating user tables.
///
/// This additional metadata serves the singular purpose of message passing from trusted to untrusted areas.
/// This eliminates the need for re-executing business logic or performing redundant database queries in
/// the untrusted area. For this reason, we the meta variations are strictly internal structures.
///
/// This polymorphic approach contrasts with using separate metadata structures, offering a more streamlined data model.
/// It ensures a type-safe association of metadata with each event and simplifies the overall data model by keeping
/// related data cohesively organized. This design reduces the complexity inherent in intermediary wrappers and
/// lookup logic, aiming at code readability, minimizing runtime bugs and maintainability.
// TODO 3503: Consider refactoring the remaining tuples to merge the two enums: `enum Event<O, P, A, ...>` using two type aliases to preserve usage.
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(tag = "t", content = "c")]
#[non_exhaustive]
pub enum EventMeta {
    // TODO 3503: De-duplicate fields between book order and order intent.
    PartialFill(MatchableIntent, OrderMatchOutcome<TradeOutcomeMeta>),
    CompleteFill(MatchableIntent, OrderMatchOutcome<TradeOutcomeMeta>),
    // Here's an example of why this is less contrived that the type-object approach, we don't need void side-effects placeholders.
    Post(MatchableIntent, OrderMatchOutcome<TradeOutcomeMeta>),
    Cancel(Cancel, StrategyKey),
    CancelAll(CancelAll, Vec<Cancel>),
    // This is another example, we can associate a side-effect with its item instead of having to combine two collections.
    Liquidation(LiquidationsMeta),

    // Includes deposits, withdrawal claims and settings updates.
    StrategyUpdate(StrategyUpdate<LiquidBalanceUpdate>),
    TraderUpdate(TraderUpdate<LiquidBalanceUpdate>),
    // TODO 3591: These are the withdrawal intentions, no the claims as indicated above. I can't find a way to justify this model especially given that update events still don't have uniform common attributes (block tx stamps that could justify this are optional). It seems clear than categories should be functional.
    Withdraw(Withdraw<LiquidBalanceUpdate, StrategyId>),
    WithdrawDDX(WithdrawDDX<LiquidBalanceUpdate>),

    InsuranceFundWithdraw(InsuranceFundWithdraw<LiquidBalanceUpdate>),
    PriceCheckpoint(PriceCheckpointsMeta),
    PnlRealization(PnlRealizationMeta),

    Funding(FundingMeta),
    TradeMining(TradeMining<TraderPayments>),
    #[cfg(feature = "fixed_expiry_future")]
    FuturesExpiry(FuturesExpiryMeta),
    EpochMarker(EpochMarkerMeta),
    SignerRegistered(Identity),
    SpecsUpdate(SpecsUpdate),
    TradableProductUpdate(TradableProductUpdate),
    InsuranceFundUpdate(InsuranceFundUpdate<BalanceUpdate>),
    FeeDistribution(FeeDistributionMeta),
    DisasterRecovery(Vec<AccountClosure>),
}

impl EventDescriptor for EventMeta {
    fn discriminant(&self) -> u8 {
        let d = match self {
            EventMeta::PartialFill(..) => TX_PARTIAL_FILL,
            EventMeta::CompleteFill(..) => TX_COMPLETE_FILL,
            EventMeta::Post(..) => TX_POST,
            EventMeta::Cancel(..) => TX_CANCEL,
            EventMeta::CancelAll(..) => TX_CANCEL_ALL,
            EventMeta::Liquidation(..) => TX_LIQUIDATION,
            EventMeta::StrategyUpdate(..) => TX_STRATEGY_UPDATE,
            EventMeta::TraderUpdate(..) => TX_TRADER_UPDATE,
            EventMeta::Withdraw(..) => TX_WITHDRAW,
            EventMeta::WithdrawDDX(..) => TX_WITHDRAW_DDX,
            EventMeta::PriceCheckpoint(..) => TX_PRICE_CHECKPOINT,
            EventMeta::PnlRealization(..) => TX_PNL_REALIZATION,
            EventMeta::Funding(..) => TX_FUNDING,
            #[cfg(feature = "fixed_expiry_future")]
            EventMeta::FuturesExpiry(..) => TX_FUTURES_EXPIRY,
            EventMeta::TradeMining(..) => TX_TRADE_MINING,
            EventMeta::SpecsUpdate(..) => TX_SPECS_UPDATE,
            EventMeta::TradableProductUpdate(..) => TX_TRADABLE_PRODUCT_UPDATE,
            EventMeta::EpochMarker(..) => TX_EPOCH_MARKER,
            EventMeta::SignerRegistered { .. } => TX_SIGNER_REGISTERED,
            EventMeta::InsuranceFundUpdate(..) => TX_INSURANCE_FUND_UPDATE,
            EventMeta::InsuranceFundWithdraw(..) => TX_INSURANCE_FUND_WITHDRAW,
            EventMeta::FeeDistribution(..) => TX_FEE_DISTRIBUTION,
            EventMeta::DisasterRecovery(..) => TX_DISASTER_RECOVERY,
        };
        d as u8
    }
}

#[cfg(feature = "test_harness")]
#[derive(Debug, Clone)]
pub enum EventWithCheckpoint {
    AdvanceEpoch(EpochMarker, (EpochId, SignedCheckpoint)),
    Other(Event),
}

/// Records the result of an order matching execution.
///
/// The order may be partially or completely filled or self-canceled, but not posted to the order book.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct OrderMatchOutcome<T> {
    /// Product symbol of the incoming order.
    pub symbol: ProductSymbol,
    /// Hash of the incoming order.
    pub order_hash: OrderHash,
    #[serde(flatten, skip_serializing_if = "Option::is_none")]
    pub post: Option<BookOrder>,
    /// Outcomes of the trade executions for this order.
    #[serde(bound = "T: Serialize + serde::de::DeserializeOwned")]
    pub trade_outcomes: Vec<T>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub order_rejection: Option<OrderRejection>,
}

impl From<&OrderMatchOutcome<TradeOutcomeMeta>> for OrderMatchOutcome<TradeOutcome> {
    fn from(value: &OrderMatchOutcome<TradeOutcomeMeta>) -> Self {
        OrderMatchOutcome {
            symbol: value.symbol,
            post: value.post.clone(),
            order_hash: value.order_hash,
            trade_outcomes: value.trade_outcomes.iter().map(|o| o.into()).collect(),
            order_rejection: value.order_rejection.clone(),
        }
    }
}

/// Contains the state transition data associated with market liquidations.
#[derive(Debug, Default, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct Liquidations<T, ADL, A> {
    #[serde(
        bound = "T: Serialize + serde::de::DeserializeOwned, ADL: Serialize + serde::de::DeserializeOwned, A: Serialize + serde::de::DeserializeOwned"
    )]
    strategies: Vec<StrategyLiquidated<T, ADL, A>>,
}

#[derive(Debug, Default, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct LiquidationsMeta {
    pub symbol: ProductSymbol,
    pub mark_price: Decimal,
    pub funding_rate: Option<Decimal>,
    pub strategies: Vec<StrategyLiquidatedMeta>,
}

impl From<&LiquidationsMeta> for Liquidations<TradeOutcome, AdlOutcome, RecordedAmount> {
    fn from(value: &LiquidationsMeta) -> Self {
        Liquidations {
            strategies: value.strategies.iter().map(|s| s.into()).collect(),
        }
    }
}

/// Type alias for mapping trader addresses to their corresponding payment details.
pub type TraderPayments = HashMap<TraderAddress, BalanceUpdate>;

/// Core profit and loss (P&L) settlements data.
#[derive(Debug, Default, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct PnlRealization {
    settlement_epoch_id: EpochId,
}

/// Extends PnlRealization with additional metadata including realized P&L amounts for individual strategies.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PnlRealizationMeta {
    pub settlement_epoch_id: EpochId,
    /// Contains detailed information about realized profit and loss amounts for each strategy.
    pub realized_pnl: Vec<(StrategyKey, RealizedPnl)>,
}

impl From<&PnlRealizationMeta> for PnlRealization {
    fn from(value: &PnlRealizationMeta) -> Self {
        PnlRealization {
            settlement_epoch_id: value.settlement_epoch_id,
        }
    }
}

/// Core funding data including strategies impacted by negative funding rates.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct Funding {
    settlement_epoch_id: EpochId,
    /// Identifies strategies affected by negative funding rates.
    ///
    /// The price checkpoint list covers all products, so not repeated for liquidations.
    liquidations: Vec<StrategyLiquidated<TradeOutcome, AdlOutcome, RecordedAmount>>,
}

/// Detailed structure for funding payments, breaking down individual amounts by symbol
/// and reflecting the overall impact on trader balances.
#[derive(Debug, Default, Clone, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct FundingPayment {
    /// Detailed breakdown of payments, itemized by each position symbol.
    // TODO 3503: Amounts here will be inserted into the db. I believe that should add up to the total, which they won't because they are not adjusted. Check with Adi.
    pub itemized_amount: BTreeMap<ProductSymbol, Decimal>,
    /// Total funding payment amount for validation of itemized amounts.
    pub total: RecordedAmount,
    /// New collateral balance after the total funding payment.
    pub new_balance: RecordedAmount,
    /// Indicates the collateral asset used for the funding payment.
    pub collateral_address: TokenAddress,
}

/// Enhanced funding data with additional metadata, providing a comprehensive view
/// of funding-related activities, including market prices, liquidations, and strategy payments.
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct FundingMeta {
    pub settlement_epoch_id: EpochId,
    pub funding_rates_with_mark_prices: HashMap<ProductSymbol, (Decimal, Decimal)>,
    pub liquidations: Vec<StrategyLiquidatedMeta>,
    /// Detailed breakdown of payments per strategy.
    pub payments: Vec<(StrategyKey, FundingPayment)>,
}

impl From<&FundingMeta> for Funding {
    fn from(value: &FundingMeta) -> Self {
        Funding {
            settlement_epoch_id: value.settlement_epoch_id,
            liquidations: value.liquidations.iter().map(|l| l.into()).collect(),
        }
    }
}

#[cfg(feature = "fixed_expiry_future")]
#[derive(Debug, Clone, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct FuturesExpiry {
    settlement_epoch_id: EpochId,
    quarter: Quarter,
}

#[cfg(feature = "fixed_expiry_future")]
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct FuturesExpiryMeta {
    pub settlement_epoch_id: EpochId,
    pub quarter: Quarter,
    pub cancels: Vec<(StrategyKey, Cancel)>,
    pub expired_positions: Vec<(PositionKey, PositionUpdate)>,
}

#[cfg(feature = "fixed_expiry_future")]
impl From<&FuturesExpiryMeta> for FuturesExpiry {
    fn from(value: &FuturesExpiryMeta) -> Self {
        FuturesExpiry {
            settlement_epoch_id: value.settlement_epoch_id,
            quarter: value.quarter,
        }
    }
}

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Identity {
    pub release_hash: ReleaseHash,
    pub signer_address: SignerAddress,
}

/// Metadata for non-state transitioning operations.
/// All operations include a timestamp and are written to time series tables.

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NoTx {
    /// The epoch id.
    pub epoch_id: EpochId,
    /// Index of the associated request.
    pub request_index: RequestIndex,
    /// Timestamp for the operation.
    pub time: StampedTimeValue,
    /// The event for the non-state transitioning operation.
    pub event: NoTxEvent,
}

/// Represents the payload for non-state transitioning events.
#[allow(clippy::large_enum_variant)]
#[derive(Debug, Clone, PartialEq, Deserialize, Serialize)]
pub enum NoTxEvent {
    #[cfg(feature = "eth-base")]
    AdvanceBlock(super::ethereum::ConfirmedBlock),
    Tick,
    IntentRejection(IntentRejection),
    MarkPrice {
        symbol: ProductSymbol,
        mark_price: Decimal,
        funding_rate: Option<Decimal>,
    },
}

pub trait ToEvent {
    fn to_event(&self) -> Tx<Event>;
}

impl ToEvent for Tx<EventMeta> {
    /// Creates a new event without the metadata using references to inner types.
    ///
    /// We convert from a reference because usage requires to keep the meta event so this
    /// approach copies less data than if we were required to clone the meta event.
    fn to_event(&self) -> Tx<Event> {
        Tx {
            epoch_id: self.epoch_id,
            ordinal: self.ordinal,
            state_root_hash: self.state_root_hash,
            request_index: self.request_index,
            batch_id: self.batch_id,
            time: self.time,
            event: match &self.event {
                EventMeta::PartialFill(_, m) => Event::PartialFill(m.into()),
                EventMeta::CompleteFill(_, m) => Event::CompleteFill(m.into()),
                EventMeta::Post(_, m) => Event::Post(m.into()),
                EventMeta::Cancel(c, _) => Event::Cancel(c.clone()),
                EventMeta::CancelAll(c, _) => Event::CancelAll(c.clone()),
                EventMeta::Liquidation(l) => Event::Liquidation(l.into()),
                EventMeta::StrategyUpdate(s) => Event::StrategyUpdate(s.into()),
                EventMeta::TraderUpdate(t) => Event::TraderUpdate(t.into()),
                EventMeta::Withdraw(w) => Event::Withdraw(w.into()),
                EventMeta::WithdrawDDX(w) => Event::WithdrawDDX(w.into()),
                EventMeta::InsuranceFundWithdraw(w) => Event::InsuranceFundWithdraw(w.into()),
                EventMeta::PriceCheckpoint(p) => Event::PriceCheckpoint(
                    p.checkpoints.iter().map(|(k, v)| (*k, v.into())).collect(),
                ),
                EventMeta::PnlRealization(s) => Event::PnlRealization(s.into()),
                EventMeta::Funding(f) => Event::Funding(f.into()),
                EventMeta::TradeMining(t) => Event::TradeMining(t.into()),
                #[cfg(feature = "fixed_expiry_future")]
                EventMeta::FuturesExpiry(f) => Event::FuturesExpiry(f.into()),
                EventMeta::EpochMarker(e) => Event::EpochMarker(e.into()),
                EventMeta::SignerRegistered(s) => Event::SignerRegistered(s.clone()),
                EventMeta::SpecsUpdate(s) => Event::SpecsUpdate(s.clone()),
                EventMeta::TradableProductUpdate(t) => Event::TradableProductUpdate(t.clone()),
                EventMeta::InsuranceFundUpdate(i) => Event::InsuranceFundUpdate(i.into()),
                EventMeta::FeeDistribution(f) => Event::FeeDistribution(f.into()),
                EventMeta::DisasterRecovery(_) => Event::DisasterRecovery,
            },
        }
    }
}

/// Maintains a sequence of transaction log entries.
// TODO: Rename TxSeries?
#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct OrderedTxs(pub Vec<Tx<Event>>);

impl Deref for OrderedTxs {
    type Target = Vec<Tx<Event>>;

    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

impl DerefMut for OrderedTxs {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.0
    }
}

#[cfg(feature = "test_harness")]
#[derive(Debug, Clone)]
pub struct TxWithCheckpoint {
    pub tx: Tx<Event>,
    pub checkpoint: Option<(EpochId, SignedCheckpoint)>,
}

#[cfg(feature = "test_harness")]
impl TxWithCheckpoint {
    pub fn with_checkpoint(
        tx: Tx<Event>,
        checkpoint: &Option<(EpochId, SignedCheckpoint)>,
    ) -> Self {
        if matches!(
            tx.event,
            Event::EpochMarker(EpochMarker::AdvanceEpoch { .. })
        ) {
            TxWithCheckpoint {
                tx,
                checkpoint: *checkpoint,
            }
        } else {
            TxWithCheckpoint {
                tx,
                checkpoint: None,
            }
        }
    }
}

#[cfg(feature = "test_harness")]
impl From<TxWithCheckpoint> for Tx<Event> {
    fn from(value: TxWithCheckpoint) -> Self {
        value.tx
    }
}

#[cfg(feature = "test_harness")]
#[derive(Debug, Default, Clone)]
pub struct OrderedTxsWithCheckpoint(pub Vec<TxWithCheckpoint>);

#[cfg(feature = "test_harness")]
impl Deref for OrderedTxsWithCheckpoint {
    type Target = Vec<TxWithCheckpoint>;
    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

#[cfg(feature = "test_harness")]
impl Serialize for OrderedTxsWithCheckpoint {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        let mut seq = serializer.serialize_seq(Some(self.0.len()))?;
        for tx in &self.0 {
            seq.serialize_element(&(tx.tx.clone(), tx.checkpoint))?;
        }
        seq.end()
    }
}

#[cfg(feature = "test_harness")]
impl<'de> Deserialize<'de> for OrderedTxsWithCheckpoint {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        let txs: Vec<(Tx<Event>, Option<(EpochId, SignedCheckpoint)>)> =
            Vec::deserialize(deserializer)?;
        let mut txs_with_checkpoint = Vec::with_capacity(txs.len());
        for (tx, maybe_checkpoint) in txs {
            txs_with_checkpoint.push(TxWithCheckpoint {
                tx,
                checkpoint: maybe_checkpoint,
            });
        }
        Ok(Self(txs_with_checkpoint))
    }
}

/// Represents a snapshot of price-related data for a product at a specific point in time.
///
/// The included details represent the context of a transaction.
#[derive(Debug, Default, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct PriceDetail {
    pub index_price_hash: IndexPriceHash,
    /// The price itself as emitted by the price feed.
    pub index_price: RecordedAmount,
    pub mark_price_metadata: MarkPriceMetadata,
    /// Ordinal position relative to other price checkpoints.
    pub ordinal: Ordinal,
    pub time_value: TimeValue,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PriceDetailMeta {
    pub inner: PriceDetail,
    /// Metadata apply to more parameterized instruments like index perpetuals.
    pub metadata: PriceMetadata,
    /// Pre-calculated mark price for the product.
    pub mark_price: Decimal,
    pub direction: PriceDirection,
}

impl PriceDetailMeta {
    pub fn new(
        hash: IndexPriceHash,
        price: Price,
        metadata: PriceMetadata,
        direction: PriceDirection,
    ) -> Self {
        PriceDetailMeta {
            inner: PriceDetail {
                index_price: price.index_price,
                mark_price_metadata: price.mark_price_metadata,
                ordinal: price.ordinal,
                time_value: price.time_value,
                index_price_hash: hash,
            },
            metadata,
            mark_price: price.mark_price(),
            direction,
        }
    }

    pub fn void() -> Self {
        PriceDetailMeta {
            inner: PriceDetail::default(),
            metadata: PriceMetadata::Empty,
            mark_price: Decimal::zero(),
            direction: PriceDirection::Unknown,
        }
    }

    pub fn is_void(&self) -> bool {
        debug_assert!(
            (self.inner.index_price.is_zero()
                && self.inner.time_value.is_zero()
                && self.inner.index_price_hash == Default::default()
                && self.inner.mark_price_metadata == Default::default()
                && self.inner.ordinal.is_zero())
                || !self.inner.index_price.is_zero(),
            "Expected a price of zero within a default instance only; got {:?}",
            self
        );
        self.inner.index_price.is_zero() && self.inner.index_price_hash == Default::default()
    }
}

impl From<&PriceDetailMeta> for PriceDetail {
    fn from(value: &PriceDetailMeta) -> Self {
        value.inner.clone()
    }
}

impl From<PriceDetailMeta> for Price {
    fn from(price: PriceDetailMeta) -> Self {
        Price {
            index_price: price.inner.index_price,
            mark_price_metadata: price.inner.mark_price_metadata,
            ordinal: price.inner.ordinal,
            time_value: price.inner.time_value,
        }
    }
}

/// Records the closure of a trading account, encapsulating its final state.
#[derive(Debug, PartialEq, Clone, Serialize, Deserialize)]
pub struct AccountClosure {
    // TODO 3591: Why this instead of the trader address and strategy id as separate attributes like everywhere else?
    pub strategy_key: StrategyKey,
    /// The products associated with the closed account.
    pub symbols: Vec<ProductSymbol>,
    /// The total profit or loss of the account at closure.
    // TODO 3591: Changed from `Balance` because it seem inconsistent with other equivalent operations (including Cancel in this same structure).
    pub total_pnl: RecordedAmount,
    /// Details of any canceled orders upon account closure.
    pub cancels: Vec<Cancel>,
}

/// Represents the outcome of a trade operation.
///
/// `Fill` indicates a successful trade match, while `Cancel` denotes a trade cancellation.
///
/// We chose the cancel, fill with sub-variations based on the common characteristics between these outcomes.
// TODO: Consider actually splitting these into separate types, because it leads to ambiguity. For example, `CompleteFill` holds an array of this type, but must have at least one `Fill` to be semantically correct. I think `PartialFill { fills: Vec<Fill>, cancels: Vec<Cancel> }` is a better idea.
#[allow(clippy::large_enum_variant)]
#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
pub enum TradeOutcome {
    Fill(Fill<FillOutcome>),
    Cancel(Cancel),
}

/// Extended version of `TradeOutcome` with additional metadata.
///
/// `Fill` variant details the impact of the filled order on the strategies involved,
/// whereas `Cancel` details the impact of an order cancellation.
#[allow(clippy::large_enum_variant)]
#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
pub enum TradeOutcomeMeta {
    Fill(TradeOutcomeFillMeta),
    Cancel(TradeOutcomeCancelMeta),
}

impl TradeOutcomeMeta {
    pub fn is_fill(&self) -> bool {
        matches!(self, TradeOutcomeMeta::Fill(_))
    }
}

impl From<&TradeOutcomeMeta> for TradeOutcome {
    fn from(value: &TradeOutcomeMeta) -> Self {
        match value {
            TradeOutcomeMeta::Fill(f) => TradeOutcome::Fill(Fill::from(&f.fill)),
            TradeOutcomeMeta::Cancel(c) => TradeOutcome::Cancel(c.cancel.clone()),
        }
    }
}

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
pub struct TradeOutcomeFillMeta {
    pub fill: Fill<FillOutcomeMeta>,
    /// Metadata updates applicable to the insurance fund and ddx pool, associated with the trade.
    pub insurance_fund_update: Option<BalanceUpdate>,
    pub ddx_pool_update: Option<BalanceUpdate>,
}

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
pub struct TradeOutcomeCancelMeta {
    pub cancel: Cancel,
    /// Identifies the strategy affected by the cancellation.
    pub strategy_key: StrategyKey,
    /// Identifies the taker from which an order match caused a cancellation.
    pub taker: Option<(StrategyKey, OrderHash)>,
    /// Optional field with the strategy of liquidated trader
    pub liquidated_strategy_key: Option<StrategyKey>,
}

/// Details of a trade fill, including trader information, strategy, and fees.
///
/// Captures the all effects of the trade on the given party (maker or taker) strategy.
#[cfg_attr(feature = "test_harness", derive(Default))]
#[derive(Debug, Clone, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct FillOutcome {
    /// Identifies the trader involved in the fill.
    // FIXME 3591: Reconcile these identifiers. We use `trader_address` elsewhere (e.g. AdlOutcome) so there's no justification possible. Limiting changes for the time being.
    trader: TraderAddress,
    /// Strategy ID hash associated with the trade.
    strategy_id_hash: StrategyIdHash,
}

impl From<&FillOutcomeMeta> for FillOutcome {
    fn from(value: &FillOutcomeMeta) -> Self {
        FillOutcome {
            trader: value.trader_address,
            strategy_id_hash: value.strategy_id_hash,
        }
    }
}

/// Fee with associated trader margin update to verify DDX fee payments.
#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
pub enum FeeMeta {
    DefaultCurrency(RecordedFee),
    DDX(BalanceUpdate),
}

impl Default for FeeMeta {
    fn default() -> Self {
        FeeMeta::DefaultCurrency(Default::default())
    }
}

impl FeeMeta {
    pub(crate) fn is_ddx(&self) -> bool {
        matches!(self, FeeMeta::DDX(_))
    }

    #[cfg(test)]
    pub(crate) fn ddx(&self) -> Option<RecordedFee> {
        if let FeeMeta::DDX(fee) = self {
            Some(fee.amount)
        } else {
            None
        }
    }

    pub fn default_currency(&self) -> Option<RecordedFee> {
        if let FeeMeta::DefaultCurrency(fee) = self {
            Some(*fee)
        } else {
            None
        }
    }
}

/// Extended version of `FillOutcome` with additional metadata.

#[cfg_attr(feature = "test_harness", derive(Default))]
#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct FillOutcomeMeta {
    pub trader_address: TraderAddress,
    pub strategy_id_hash: StrategyIdHash,
    /// Calculated fee amount denominated in the default currency.
    pub base_fee: Decimal,
    /// Recorded fee paid in the chosen currency.
    ///
    /// The `fee` is calculated from `base_fee` by applying a discount and converting the currency when applicable.
    pub fee: FeeMeta,
    /// Realized P&L information for this trade party.
    pub realized_pnl: RealizedPnl,
    /// Position update information for this trade party.
    pub position_update: PositionUpdate,
}

impl FillOutcomeMeta {
    /// Creates an initial fill outcome instance.
    ///
    /// The intention is to finalize this instance by accumulating values as the transaction is processed.
    pub fn new_template_to_fill() -> Self {
        FillOutcomeMeta {
            trader_address: Default::default(),
            strategy_id_hash: StrategyIdHash::default(),
            base_fee: Default::default(),
            fee: Default::default(),
            realized_pnl: Default::default(),
            position_update: Default::default(),
        }
    }

    #[cfg(feature = "test_harness")]
    pub fn new_with_strategy<A, D>(trader_address: A, strategy_id: StrategyId, base_fee: D) -> Self
    where
        A: Into<TraderAddress>,
        D: Into<Decimal>,
    {
        let mut meta = FillOutcomeMeta::new_template_to_fill();
        meta.strategy_id_hash = strategy_id.into();
        meta.trader_address = trader_address.into();
        meta.base_fee = base_fee.into();
        meta
    }

    pub fn get_fee_options(&self) -> (Option<RecordedFee>, Option<RecordedFee>) {
        match &self.fee {
            FeeMeta::DefaultCurrency(fee) => (Some(*fee), None),
            FeeMeta::DDX(fee) => (None, Some(fee.amount)),
        }
    }
}

/// Information about a specific trade fill or liquidation event.
///
/// `Trade` represents a standard trade fill, while `Liquidation` covers forced trade fills due to liquidation.
#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
#[serde(tag = "reason", rename_all_fields = "camelCase")]
pub enum Fill<F> {
    Trade {
        /// Details of the market maker's outcome in the trade.
        #[serde(bound = "F: Serialize + serde::de::DeserializeOwned")]
        maker_outcome: F,
        /// Details of the market taker's outcome in the trade.
        #[serde(bound = "F: Serialize + serde::de::DeserializeOwned")]
        taker_outcome: F,
        /// Trading symbol for the product involved in the trade.
        // TODO 3591: Isn't symbol always available in context? As a rule, we should avoid redundant information.
        symbol: ProductSymbol,
        /// Hash of the maker's order.
        maker_order_hash: OrderHash,
        /// Remaining amount in the maker's order post-fill.
        maker_order_remaining_amount: RecordedAmount,
        // TODO 3591: Isn't this always in context as the incoming order or nothing for liquidations? Wouldn't dropping this allow us to collapse the two variants into one?
        /// Hash of the taker's order.
        taker_order_hash: OrderHash,
        /// Amount involved in the trade.
        amount: RecordedAmount,
        /// Price at which the trade was executed.
        price: RecordedAmount,
        /// Indicates the taker's side in the trade.
        taker_side: OrderSide,
    },
    Liquidation {
        /// Details of the maker's outcome in the liquidation trade.
        #[serde(bound = "F: Serialize + serde::de::DeserializeOwned")]
        maker_outcome: F,
        /// Trading symbol for the product involved in the liquidation.
        symbol: ProductSymbol,
        /// Hash of the maker's order involved in the liquidation.
        maker_order_hash: OrderHash,
        /// Remaining amount in the maker's order post-liquidation.
        maker_order_remaining_amount: RecordedAmount,
        /// Hash of the index price relevant to the liquidation.
        index_price_hash: IndexPriceHash,
        /// Amount involved in the liquidation.
        amount: RecordedAmount,
        /// Price at which the liquidation occurred.
        price: RecordedAmount,
        /// Indicates the liquidation engine's side in the trade.
        taker_side: OrderSide,
    },
}

impl Fill<FillOutcomeMeta> {
    #[cfg(test)]
    pub(crate) fn fees(&self) -> (Option<FeeMeta>, Option<FeeMeta>) {
        match self {
            Fill::Trade {
                maker_outcome,
                taker_outcome,
                ..
            } => (
                Some(maker_outcome.fee.clone()),
                Some(taker_outcome.fee.clone()),
            ),
            Fill::Liquidation { maker_outcome, .. } => (Some(maker_outcome.fee.clone()), None),
        }
    }

    pub fn outcome(&self, trade_side: &TradeSide) -> Result<&FillOutcomeMeta> {
        match self {
            Fill::Trade {
                maker_outcome,
                taker_outcome,
                ..
            } => match trade_side {
                TradeSide::Maker => Ok(maker_outcome),
                TradeSide::Taker => Ok(taker_outcome),
            },
            Fill::Liquidation { maker_outcome, .. } => match trade_side {
                TradeSide::Maker => Ok(maker_outcome),
                TradeSide::Taker => Err(Error::Other(
                    "Liquidation fills do not have a taker".to_string(),
                )),
            },
        }
    }

    pub fn outcome_mut(&mut self, trade_side: &TradeSide) -> Result<&mut FillOutcomeMeta> {
        match self {
            Fill::Trade {
                maker_outcome,
                taker_outcome,
                ..
            } => match trade_side {
                TradeSide::Maker => Ok(maker_outcome),
                TradeSide::Taker => Ok(taker_outcome),
            },
            Fill::Liquidation { maker_outcome, .. } => match trade_side {
                TradeSide::Maker => Ok(maker_outcome),
                TradeSide::Taker => Err(Error::Other(
                    "Liquidation fills do not have a taker".to_string(),
                )),
            },
        }
    }

    pub fn amount(&self) -> RecordedAmount {
        match self {
            Fill::Trade { amount, .. } => *amount,
            Fill::Liquidation { amount, .. } => *amount,
        }
    }

    pub fn price(&self) -> RecordedAmount {
        match self {
            Fill::Trade { price, .. } => *price,
            Fill::Liquidation { price, .. } => *price,
        }
    }

    /// Returns the total fees paid by all parties for this fill, in the default currency and DDX respectively.
    pub fn total_fees(&self) -> (Decimal, Decimal) {
        let mut acc = (Decimal::zero(), Decimal::zero());
        match self {
            Fill::Trade {
                maker_outcome,
                taker_outcome,
                ..
            } => {
                match &maker_outcome.fee {
                    FeeMeta::DefaultCurrency(fee) => acc.0 += **fee,
                    FeeMeta::DDX(fee) => acc.1 += *fee.amount,
                }
                match &taker_outcome.fee {
                    FeeMeta::DefaultCurrency(fee) => acc.0 += **fee,
                    FeeMeta::DDX(fee) => acc.1 += *fee.amount,
                }
            }
            Fill::Liquidation { maker_outcome, .. } => match &maker_outcome.fee {
                FeeMeta::DefaultCurrency(fee) => acc.0 += **fee,
                FeeMeta::DDX(fee) => acc.1 += *fee.amount,
            },
        }
        acc
    }
}

impl From<&Fill<FillOutcomeMeta>> for Fill<FillOutcome> {
    fn from(value: &Fill<FillOutcomeMeta>) -> Self {
        match value {
            Fill::Trade {
                maker_outcome,
                taker_outcome,
                symbol,
                maker_order_hash,
                maker_order_remaining_amount,
                taker_order_hash,
                amount,
                price,
                taker_side,
            } => Fill::Trade {
                maker_outcome: maker_outcome.into(),
                taker_outcome: taker_outcome.into(),
                symbol: *symbol,
                maker_order_hash: *maker_order_hash,
                maker_order_remaining_amount: *maker_order_remaining_amount,
                taker_order_hash: *taker_order_hash,
                amount: *amount,
                price: *price,
                taker_side: *taker_side,
            },
            Fill::Liquidation {
                maker_outcome,
                symbol,
                maker_order_hash,
                maker_order_remaining_amount,
                index_price_hash,
                amount,
                price,
                taker_side,
            } => Fill::Liquidation {
                maker_outcome: maker_outcome.into(),
                symbol: *symbol,
                maker_order_hash: *maker_order_hash,
                maker_order_remaining_amount: *maker_order_remaining_amount,
                index_price_hash: *index_price_hash,
                amount: *amount,
                price: *price,
                taker_side: *taker_side,
            },
        }
    }
}

/// Order canceled and removed from the book but did not take
#[derive(Debug, Clone, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Cancel {
    pub symbol: ProductSymbol,
    /// EIP-712 hash of the order intent and unique identifier
    pub order_hash: OrderHash,
    pub amount: RecordedAmount,
}

/// Order canceled and removed from the book but did not take
#[derive(Debug, Clone, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CancelAll {
    pub symbol: ProductSymbol,
    pub strategy_key: StrategyKey,
}

#[derive(Debug, Clone, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct AdlOutcome {
    trader_address: TraderAddress,
    strategy_id_hash: StrategyIdHash,
}

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct AdlOutcomeMeta {
    pub trader_address: TraderAddress,
    pub strategy_id_hash: StrategyIdHash,
    pub realized_pnl: RealizedPnl,
    pub position_update: PositionUpdate,
}

impl From<&AdlOutcomeMeta> for AdlOutcome {
    fn from(value: &AdlOutcomeMeta) -> Self {
        AdlOutcome {
            trader_address: value.trader_address,
            strategy_id_hash: value.strategy_id_hash,
        }
    }
}

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
struct PositionLiquidated<O, ADL, A> {
    // Liquidated amount
    amount: RecordedAmount,
    /// Trade outcomes that resulted from liquidation the position
    #[serde(bound = "O: Serialize + serde::de::DeserializeOwned")]
    trade_outcomes: Vec<O>,
    /// A list of strategies to deleverage in case insolvency
    #[serde(bound = "ADL: Serialize + serde::de::DeserializeOwned")]
    adl_outcomes: Vec<ADL>,
    /// Impact of the liquidation sale on the insurance fund.
    #[serde(
        bound = "A: Serialize + serde::de::DeserializeOwned",
        rename = "newInsuranceFundCap"
    )]
    insurance_fund_update: A,
}

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct PositionLiquidatedMeta {
    pub amount: RecordedAmount,
    pub trade_outcomes: Vec<TradeOutcomeMeta>,
    pub adl_outcomes: Vec<AdlOutcomeMeta>,
    #[serde(rename = "newInsuranceFundCap")]
    pub insurance_fund_update: BalanceUpdate,
    pub price: PriceDetailMeta,
}

impl From<&PositionLiquidatedMeta>
    for PositionLiquidated<TradeOutcome, AdlOutcome, RecordedAmount>
{
    fn from(value: &PositionLiquidatedMeta) -> Self {
        PositionLiquidated {
            amount: value.amount,
            trade_outcomes: value.trade_outcomes.iter().map(|o| o.into()).collect(),
            adl_outcomes: value.adl_outcomes.iter().map(|o| o.into()).collect(),
            insurance_fund_update: value.insurance_fund_update.available,
        }
    }
}

/// Trader account being liquidated (we use cross-margin)
#[cfg_attr(feature = "test_harness", derive(Default))]
#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
struct StrategyLiquidated<O, ADL, A> {
    trader_address: TraderAddress,
    strategy_id_hash: StrategyIdHash,
    canceled_orders: Vec<Cancel>,
    /// Collateral amount that was liquidated, equal to the balance before liquidation.
    // TODO 3591: Rename and take out of the core Tx. I don't see the auditor using this and it does not need it as the strategy balance before is in the state.
    collateral_amount: RecordedAmount,
    #[serde(
        bound = "O: Serialize + serde::de::DeserializeOwned, ADL: Serialize + serde::de::DeserializeOwned, A: Serialize + serde::de::DeserializeOwned"
    )]
    positions: Vec<(ProductSymbol, PositionLiquidated<O, ADL, A>)>,
}

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct StrategyLiquidatedMeta {
    pub trader_address: TraderAddress,
    pub strategy_id_hash: StrategyIdHash,
    pub canceled_orders: Vec<Cancel>,
    pub collateral_amount: RecordedAmount,
    pub positions: Vec<(ProductSymbol, PositionLiquidatedMeta)>,
}

impl From<&StrategyLiquidatedMeta>
    for StrategyLiquidated<TradeOutcome, AdlOutcome, RecordedAmount>
{
    fn from(value: &StrategyLiquidatedMeta) -> Self {
        StrategyLiquidated {
            trader_address: value.trader_address,
            strategy_id_hash: value.strategy_id_hash,
            canceled_orders: value.canceled_orders.clone(),
            collateral_amount: value.collateral_amount,
            positions: value
                .positions
                .iter()
                .map(|(k, v)| (*k, v.into()))
                .collect(),
        }
    }
}

/// Differentiates various types of strategy updates.
///
/// Enumerates different scenarios like deposits, withdrawals, and other events
/// that impact a trader's strategy, enabling appropriate response and adjustment in the strategy.
#[cfg_eval]
#[cfg_attr(feature = "python", pyclass(frozen))]
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize, Default, EnumString)]
pub enum StrategyUpdateKind {
    /// Used as placeholder in default events.
    #[default]
    Unassigned,
    /// Reacts to contract deposit event.
    Deposit,
    /// Reacts to contract withdraw event, decreasing the (claimed) locked collateral.
    Withdraw,
    /// A client request to withdraw funds, which moves funds from available collateral to locked collateral.
    WithdrawIntent,
    FundingPayment,
    RealizedPnl,
}

impl StrategyUpdateKind {
    pub fn discriminant(&self) -> u8 {
        match self {
            StrategyUpdateKind::Deposit => 0,
            StrategyUpdateKind::Withdraw => 1,
            StrategyUpdateKind::WithdrawIntent => 2,
            StrategyUpdateKind::FundingPayment => 3,
            StrategyUpdateKind::RealizedPnl => 4,
            _ => panic!("Variant not assigned"),
        }
    }
}

impl TryFrom<u8> for StrategyUpdateKind {
    type Error = Error;

    fn try_from(value: u8) -> Result<Self, Self::Error> {
        let result = match value {
            0 => Self::Deposit,
            1 => Self::Withdraw,
            2 => Self::WithdrawIntent,
            3 => Self::FundingPayment,
            4 => Self::RealizedPnl,
            _ => bail!("Invalid StrategyUpdateKind value {:?}", value),
        };
        Ok(result)
    }
}

/// Record of strategy updates.
///
/// Encapsulates all the information common to all strategy update kinds.
#[derive(Debug, Clone, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct StrategyUpdate<A> {
    pub trader: TraderAddress,
    pub strategy_id_hash: StrategyIdHash,
    pub strategy_id: Option<StrategyId>,
    pub collateral_address: TokenAddress,
    // TODO 3591: Hold variant specific values here. By flattening the enum, we'd minimize changes. We should rule out breaking up thise "update" structures first.
    pub update_kind: StrategyUpdateKind,
    pub amount: A,
    #[serde(flatten)]
    pub tx_stamp: Option<BlockTxStamp>,
}

// NOTE 3768: Refactored to implemented Default for consistency only.

impl Default for StrategyUpdate<RecordedAmount> {
    fn default() -> Self {
        StrategyUpdate {
            trader: Default::default(),
            strategy_id_hash: Default::default(),
            strategy_id: Default::default(),
            collateral_address: core_common::types::primitives::TokenSymbol::USDC.into(),
            update_kind: Default::default(),
            amount: Default::default(),
            tx_stamp: Default::default(),
        }
    }
}

impl From<&StrategyUpdate<LiquidBalanceUpdate>> for StrategyUpdate<RecordedAmount> {
    fn from(value: &StrategyUpdate<LiquidBalanceUpdate>) -> Self {
        // TODO 3591: These kinds of rules should be enforced by the type system. This signals a data modeling flaw.
        debug_assert!(
            value.amount.kickback.is_none()
                || (value.update_kind == StrategyUpdateKind::Deposit
                    && value.amount.locked.is_some()),
            "Kickback apply to deposits and require a locked balance"
        );
        debug_assert!(
            value.tx_stamp.is_none()
                || (value.update_kind == StrategyUpdateKind::Deposit
                    || value.update_kind == StrategyUpdateKind::Withdraw)
        );
        StrategyUpdate {
            trader: value.trader,
            strategy_id_hash: value.strategy_id_hash,
            strategy_id: value.strategy_id,
            collateral_address: value.collateral_address,
            update_kind: value.update_kind,
            amount: value.amount.amount,
            tx_stamp: value.tx_stamp,
        }
    }
}

/// Represents a state checkpoint confirmed on Ethereum.
#[derive(Debug, Clone, Default, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct CheckpointConfirmed {
    pub state_root: Hash,
    pub tx_root: Hash,
    pub epoch_id: EpochId,
    pub custodians: Vec<TraderAddress>,
    pub bonds: Vec<RecordedAmount>,
    pub submitter: TraderAddress,
    #[serde(flatten)]
    pub tx_stamp: Option<BlockTxStamp>,
}

/// Differentiates various types of trader updates.
#[cfg_attr(feature = "python", pyclass(frozen))]
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize, Default, EnumString)]
pub enum TraderUpdateKind {
    /// Used as placeholder in default events.
    #[default]
    Unassigned,
    /// Reacts to contract DDX deposit event.
    DepositDDX,
    /// Reacts to contract DDX withdraw event, decreasing the (claimed) locked collateral.
    WithdrawDDX,
    WithdrawDDXIntent,
    TradeMiningReward,
    /// Trader profile parameter updates sent via a client intention.
    Profile,
    /// Fee distribution event.
    FeeDistribution,
    /// Denial of access to the platform due to KYC blacklist, expiration, or other reasons.
    Denial,
    /// Admission to the platform due to KYC re-approval, unbanned, or other reasons.
    Admission,
}

impl TraderUpdateKind {
    pub fn discriminant(&self) -> u8 {
        match self {
            TraderUpdateKind::Unassigned => panic!("Variant not assigned"),
            TraderUpdateKind::DepositDDX => 0,
            TraderUpdateKind::WithdrawDDX => 1,
            TraderUpdateKind::WithdrawDDXIntent => 2,
            TraderUpdateKind::TradeMiningReward => 3,
            TraderUpdateKind::Profile => 4,
            TraderUpdateKind::FeeDistribution => 5,
            TraderUpdateKind::Denial => 6,
            TraderUpdateKind::Admission => 7,
        }
    }
}

impl TryFrom<u8> for TraderUpdateKind {
    type Error = Error;

    fn try_from(value: u8) -> Result<Self, Self::Error> {
        let result = match value {
            0 => Self::DepositDDX,
            1 => Self::WithdrawDDX,
            2 => Self::WithdrawDDXIntent,
            3 => Self::TradeMiningReward,
            4 => Self::Profile,
            5 => Self::FeeDistribution,
            6 => Self::Denial,
            7 => Self::Admission,
            _ => bail!("Invalid TraderUpdateKind value {:?}", value),
        };
        Ok(result)
    }
}

/// Record of an to the trader's data.
#[derive(Debug, Default, Clone, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct TraderUpdate<A> {
    pub trader: TraderAddress,
    pub update_kind: TraderUpdateKind,
    // FIXME 3591: I made these fields optional because they are, this at least avoids overwriting good values with default values. Consider holding in the appropriate variant of the TraderUpdateKind enum.
    #[serde(bound = "A: Serialize + serde::de::DeserializeOwned")]
    pub amount: Option<A>,
    pub pay_fees_in_ddx: Option<bool>,
    #[serde(flatten)]
    pub tx_stamp: Option<BlockTxStamp>,
}

impl From<&TraderUpdate<LiquidBalanceUpdate>> for TraderUpdate<RecordedAmount> {
    fn from(value: &TraderUpdate<LiquidBalanceUpdate>) -> Self {
        debug_assert!(
            value.amount.is_none() || value.amount.as_ref().unwrap().kickback.is_none(),
            "Kickback is not applicable to trader balance"
        );
        debug_assert!(
            value.tx_stamp.is_none()
                || (value.update_kind == TraderUpdateKind::DepositDDX
                    || value.update_kind == TraderUpdateKind::WithdrawDDX)
        );
        TraderUpdate {
            trader: value.trader,
            update_kind: value.update_kind,
            amount: value.amount.as_ref().map(|a| a.amount),
            pay_fees_in_ddx: value.pay_fees_in_ddx,
            tx_stamp: value.tx_stamp,
        }
    }
}

/// Record of a withdrawal transaction.
#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct Withdraw<A, S> {
    pub recipient_address: TraderAddress,
    pub strategy: S,
    pub currency: TokenAddress,
    #[serde(bound = "A: Serialize + serde::de::DeserializeOwned")]
    pub amount: A,
}

impl From<&Withdraw<LiquidBalanceUpdate, StrategyId>> for Withdraw<RecordedAmount, StrategyIdHash> {
    fn from(value: &Withdraw<LiquidBalanceUpdate, StrategyId>) -> Self {
        debug_assert!(value.amount.kickback.is_none() && value.amount.locked.is_some());
        Self {
            recipient_address: value.recipient_address,
            strategy: value.strategy.into(),
            currency: value.currency,
            amount: value.amount.amount,
        }
    }
}

/// Record of a DDX withdrawal transaction.
#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct WithdrawDDX<A> {
    pub recipient_address: TraderAddress,
    #[serde(bound = "A: Serialize + serde::de::DeserializeOwned")]
    pub amount: A,
}

impl From<&WithdrawDDX<LiquidBalanceUpdate>> for WithdrawDDX<RecordedAmount> {
    fn from(value: &WithdrawDDX<LiquidBalanceUpdate>) -> Self {
        debug_assert!(value.amount.kickback.is_none() && value.amount.locked.is_some());
        Self {
            recipient_address: value.recipient_address,
            amount: value.amount.amount,
        }
    }
}

/// Record of an insurance fund withdrawal transaction.
#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct InsuranceFundWithdraw<A> {
    pub recipient_address: TraderAddress,
    pub currency: TokenAddress,
    #[serde(bound = "A: Serialize + serde::de::DeserializeOwned")]
    pub amount: A,
}

impl From<&InsuranceFundWithdraw<LiquidBalanceUpdate>> for InsuranceFundWithdraw<RecordedAmount> {
    fn from(value: &InsuranceFundWithdraw<LiquidBalanceUpdate>) -> Self {
        Self {
            recipient_address: value.recipient_address,
            currency: value.currency,
            amount: value.amount.amount,
        }
    }
}

/// Record of DDX fees distributed following a state checkpoint confirmation on-chain.
#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct FeeDistribution {
    /// Epoch associated with the state checkpoint.
    pub epoch_id: EpochId,
    /// Custodians (not submitter) who have signed the state checkpoint.
    pub custodians: Vec<CustodianAddress>,
    /// Sender of the price checkpoint transaction.
    pub submitter: CustodianAddress,
    // TODO 3591: This is this maps back to custodians. Why is it not a map?
    /// Bonds associated with the custodians, which factors into the fee distribution.
    pub bonds: Vec<RecordedAmount>,
    #[serde(flatten)]
    pub tx_stamp: Option<BlockTxStamp>,
}

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct FeeDistributionMeta {
    pub inner: FeeDistribution,
    /// All fee distribution paid including to custodians and the submitter.
    pub payments: HashMap<CustodianAddress, BalanceUpdate>,
}

impl From<&FeeDistributionMeta> for FeeDistribution {
    fn from(value: &FeeDistributionMeta) -> Self {
        value.inner.clone()
    }
}

#[derive(Debug, Clone, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct TradableProductUpdate {
    pub additions: Vec<TradableProductKey>,
    pub removals: Vec<TradableProductKey>,
}

#[derive(Debug, Clone, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct InsuranceFundUpdate<A> {
    pub address: InsuranceFundContributorAddress,
    pub collateral_address: TokenAddress,
    #[serde(bound = "A: Serialize + serde::de::DeserializeOwned")]
    pub amount: A,
    pub update_kind: InsuranceFundUpdateKind,
    pub tx_hash: Hash,
}

impl Default for InsuranceFundUpdate<RecordedAmount> {
    fn default() -> Self {
        Self {
            address: Default::default(),
            collateral_address: core_common::types::primitives::TokenSymbol::USDC.into(),
            amount: Default::default(),
            update_kind: Default::default(),
            tx_hash: Default::default(),
        }
    }
}

impl From<&InsuranceFundUpdate<BalanceUpdate>> for InsuranceFundUpdate<RecordedAmount> {
    fn from(value: &InsuranceFundUpdate<BalanceUpdate>) -> Self {
        Self {
            address: value.address,
            collateral_address: value.collateral_address,
            amount: value.amount.amount,
            update_kind: value.update_kind,
            tx_hash: value.tx_hash,
        }
    }
}

#[cfg_attr(feature = "python", pyclass(frozen))]
#[derive(Debug, Clone, Copy, PartialEq, Deserialize, Serialize, Default, EnumString)]
pub enum InsuranceFundUpdateKind {
    #[default]
    Unassigned,
    Deposit,
    // FIXME 3591: What is this event? A claim or an intention to withdraw?
    Withdraw,
}

impl From<InsuranceFundUpdateKind> for u8 {
    fn from(value: InsuranceFundUpdateKind) -> Self {
        value as Self
    }
}

impl TryFrom<u8> for InsuranceFundUpdateKind {
    type Error = Error;

    fn try_from(value: u8) -> Result<Self, Self::Error> {
        let result = match value {
            0 => Self::Deposit,
            1 => Self::Withdraw,
            _ => bail!("Invalid InsuranceFundUpdateKind value {:?}", value),
        };
        Ok(result)
    }
}

impl From<InsuranceFundUpdateKind> for i32 {
    fn from(value: InsuranceFundUpdateKind) -> i32 {
        value as i32
    }
}

#[derive(Debug, Clone, PartialEq, Deserialize, Serialize)]
#[serde(tag = "kind", rename_all_fields = "camelCase")]
pub enum EpochMarker {
    Genesis {
        state_root_hash: Hash,
    },
    AdvanceEpoch {
        next_book_ordinals: HashMap<ProductSymbol, Ordinal>,
        new_epoch_id: EpochId,
    },
    AdvanceSettlementEpoch,
}

#[derive(Debug, Clone, PartialEq, Deserialize, Serialize)]
#[serde(tag = "kind", rename_all_fields = "camelCase")]
pub enum EpochMarkerMeta {
    Genesis {
        state_root_hash: Hash,
        genesis_tradable_products: Vec<TradableProductKey>,
    },
    AdvanceEpoch {
        old_epoch: Epoch,
        new_epoch: Epoch,
        next_book_ordinals: HashMap<ProductSymbol, Ordinal>,
        checkpoint: Option<Box<SignedCheckpoint>>,
    },
    AdvanceSettlementEpoch {
        old_epoch: Epoch,
        new_epoch: Epoch,
    },
}

impl From<&EpochMarkerMeta> for EpochMarker {
    fn from(value: &EpochMarkerMeta) -> Self {
        match value {
            EpochMarkerMeta::Genesis {
                state_root_hash, ..
            } => EpochMarker::Genesis {
                state_root_hash: *state_root_hash,
            },
            EpochMarkerMeta::AdvanceEpoch {
                next_book_ordinals,
                new_epoch,
                ..
            } => EpochMarker::AdvanceEpoch {
                next_book_ordinals: next_book_ordinals.clone(),
                new_epoch_id: new_epoch.epoch_id,
            },
            EpochMarkerMeta::AdvanceSettlementEpoch { .. } => EpochMarker::AdvanceSettlementEpoch,
        }
    }
}

#[derive(Debug, Clone, Default, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct TradeMining<A> {
    pub settlement_epoch_id: u64,
    pub total_volume: Stats,
    #[serde(bound = "A: Serialize + serde::de::DeserializeOwned")]
    pub ddx_distributed: A,
}

impl From<&TradeMining<TraderPayments>> for TradeMining<RecordedAmount> {
    fn from(value: &TradeMining<TraderPayments>) -> Self {
        Self {
            settlement_epoch_id: value.settlement_epoch_id,
            total_volume: value.total_volume.clone(),
            // This should equal calculated overall distribution because amounts are not being rounded.
            ddx_distributed: value
                .ddx_distributed
                .values()
                .map(|r| *r.amount)
                .sum::<Decimal>()
                .into(),
        }
    }
}
