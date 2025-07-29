#[cfg(all(feature = "test_harness", feature = "fixed_expiry_future"))]
use crate::constants::DEFAULT_EXPIRY_PRICE_LEAVES_DURATION;
#[cfg(feature = "test_harness")]
use crate::constants::{
    DEFAULT_FUNDING_PERIOD_LEN, DEFAULT_PNL_REALIZATION_PERIOD_LEN, DEFAULT_TRADE_MINING_PERIOD_LEN,
};
#[cfg(all(feature = "fixed_expiry_future", not(target_family = "wasm")))]
use crate::util::env::EXPIRY_PRICE_LEAVES_DURATION;
#[cfg(feature = "test_harness")]
use crate::{
    constants::{
        DEFAULT_EMA_PERIODS, DEFAULT_NB_CONFIRMATIONS, DEFAULT_PRICE_CHECKPOINT_INTERVAL,
        DEFAULT_TEST_CLOCK_TICK_MS, DEFAULT_TRADE_MINING_DURATION_IN_SETTLEMENT_EPOCHS,
    },
    util::{
        default_trade_mining_maker_reward_percentage, default_trade_mining_reward_per_epoch,
        default_trade_mining_taker_reward_percentage,
    },
};
use crate::{
    constants::{
        DEFAULT_EPOCH_LEN, DEFAULT_SETTLEMENT_EPOCH_LEN, NB_INIT_CMDS, SUBMIT_WITHDRAWAL_THRESHOLD,
    },
    specs::types::{SpecsExpr, SpecsKey},
    types::{
        accounting::{Balance, Position, Price, Strategy},
        identifiers::StrategyIdHash,
        primitives::ProductSymbol,
        request::{
            AdvanceEpoch, AdvanceSettlementEpoch, Block, Cmd, IndexPrice, MintPriceCheckpoint,
            SettlementAction, UpdateProductListings,
        },
        transaction::Ordinal,
    },
    util::{
        env::{
            EMA_PERIODS, EPOCH_SIZE, FUNDING_SETTLEMENT_MULTIPLIER, NB_CONFIRMATION,
            PNL_REALIZATION_SETTLEMENT_MULTIPLIER, PRICE_CHECKPOINT_SIZE,
            SETTLEMENT_EPOCH_MULTIPLIER, TRADE_MINING_LENGTH, TRADE_MINING_MAKER_REWARD_PERCENTAGE,
            TRADE_MINING_REWARD_PER_EPOCH, TRADE_MINING_SETTLEMENT_MULTIPLIER,
            TRADE_MINING_TAKER_REWARD_PERCENTAGE,
        },
        serde::as_specs,
    },
};
use clap::{ArgMatches, Args, Command, FromArgMatches, arg, value_parser};
use core_common::{
    B256, Error, Result, U256, bail,
    constants::RUNTIME_MAX_WORKER_THREADS,
    ensure,
    types::{
        identifiers::ReleaseHash,
        node::{BackoffConfig, BootstrapNodeUrls, NodeContext},
        primitives::{
            Bytes32, Keccak256, OrderSide, StampedTimeValue, TimeValue, TraderAddress, UnscaledI128,
        },
        state::ConfigurableFromEnv,
        transaction::EpochId,
    },
    util::tokenize::Tokenizable,
};
use core_macros::AbiToken;
use derive_builder::Builder;
#[cfg(feature = "database")]
use postgres_types::{FromSql, IsNull, ToSql, Type, to_sql_checked};
#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "arbitrary")]
use quickcheck::Arbitrary;
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};
use std::{
    collections::{BTreeMap, HashMap},
    convert::TryFrom,
    fmt::{self, Debug},
    str::FromStr,
};

#[cfg(feature = "python")]
pub mod exported;
mod tradable_product;
mod trader;

pub use sparse_merkle_tree::H256 as StoreHash;
pub use tradable_product::{TradableProduct, TradableProductKey, TradableProductParameters};
pub use trader::Trader;

pub type LeafMapHex =
    HashMap<core_common::types::primitives::Hash, (core_common::types::primitives::Hash, String)>;

/// An SMT item that can be voided, i.e. removed when determined void
pub trait VoidableItem {
    /// Check if the item is void
    fn is_void(&self) -> bool;
}

impl VoidableItem for ReleaseHash {
    fn is_void(&self) -> bool {
        false
    }
}

// TODO: Does this represent order_book or order_intent ?
/// A Bid or Ask in the orderbook (maker order)
#[cfg_attr(feature = "python", pyclass(get_all, set_all))]
#[derive(Debug, Clone, PartialEq, Deserialize, Serialize, AbiToken, Eq, Default)]
#[serde(rename_all = "camelCase")]
#[repr(C)]
pub struct BookOrder {
    /// Bid = 0, Ask = 1
    pub side: OrderSide,
    /// Order amount
    pub amount: UnscaledI128,
    /// Price offered to takers
    pub price: UnscaledI128,
    /// Maker address
    pub trader_address: TraderAddress,
    /// Maker strategy identifier
    pub strategy_id_hash: StrategyIdHash,
    /// Per market ordinal sequencing inclusion in the order book
    pub book_ordinal: Ordinal,
    /// Time stamp of the post order transaction
    pub time_value: TimeValue,
}

impl VoidableItem for BookOrder {
    fn is_void(&self) -> bool {
        self.amount.is_zero()
    }
}

#[cfg(feature = "python")]
#[pymethods]
impl BookOrder {
    #[new]
    fn new_py(
        side: OrderSide,
        amount: UnscaledI128,
        price: UnscaledI128,
        trader_address: TraderAddress,
        strategy_id_hash: StrategyIdHash,
        book_ordinal: Ordinal,
        time_value: TimeValue,
    ) -> Self {
        Self {
            side,
            amount,
            price,
            trader_address,
            strategy_id_hash,
            book_ordinal,
            time_value,
        }
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for BookOrder {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        BookOrder {
            side: OrderSide::arbitrary(g),
            amount: UnscaledI128::arbitrary(g),
            price: UnscaledI128::arbitrary(g),
            trader_address: TraderAddress::arbitrary(g),
            strategy_id_hash: StrategyIdHash::arbitrary(g),
            book_ordinal: u64::arbitrary(g),
            time_value: u64::arbitrary(g),
        }
    }
}

/// A trader statistics value. This is used to store verified data like trade
/// volume data for trade mining.
#[cfg_attr(feature = "python", pyclass(get_all, set_all))]
#[derive(Debug, Default, Clone, PartialEq, Deserialize, Serialize, AbiToken, Eq)]
#[serde(rename_all = "camelCase")]
#[repr(C)]
pub struct Stats {
    /// The maker volume of the trader during this trade mining period
    pub maker_volume: UnscaledI128,
    /// The taker volume of the trader during this trade mining period
    pub taker_volume: UnscaledI128,
}

impl VoidableItem for Stats {
    fn is_void(&self) -> bool {
        self.maker_volume.is_zero() && self.taker_volume.is_zero()
    }
}

#[cfg(feature = "python")]
#[pymethods]
impl Stats {
    #[new]
    fn new_py(maker_volume: UnscaledI128, taker_volume: UnscaledI128) -> Self {
        Self {
            maker_volume,
            taker_volume,
        }
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for Stats {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Self {
            maker_volume: UnscaledI128::arbitrary(g),
            taker_volume: UnscaledI128::arbitrary(g),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Deserialize, Serialize, Copy)]
pub enum EpochKind {
    Regular,
    Settlement,
}

/// This epoch marker is used to track the current epochs in the state.
///
/// It can only be initialized at zero or created from an epoch command (not given arbitrary values).
#[derive(Debug, Clone, PartialEq, Deserialize, Serialize, Copy)]
#[serde(rename_all = "camelCase")]
pub struct Epoch {
    pub kind: EpochKind,
    pub epoch_id: EpochId,
    pub time: StampedTimeValue,
    pub length: u64,
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for Epoch {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Self {
            kind: EpochKind::Regular,
            epoch_id: u64::arbitrary(g),
            time: StampedTimeValue::arbitrary(g),
            length: u64::arbitrary(g),
        }
    }
}

impl Epoch {
    pub(super) fn new(
        kind: EpochKind,
        epoch_id: EpochId,
        time: StampedTimeValue,
        length: u64,
    ) -> Self {
        debug_assert!(time.value > 0 || (epoch_id <= 1 && time.value == 0));
        Epoch {
            kind,
            epoch_id,
            time,
            length,
        }
    }

    pub fn initial_regular(length: Option<u64>) -> Self {
        Epoch::new(
            EpochKind::Regular,
            0,
            Default::default(),
            length.unwrap_or(DEFAULT_EPOCH_LEN),
        )
    }

    pub fn initial_settlement(length: Option<u64>) -> Self {
        Epoch::new(
            EpochKind::Settlement,
            0,
            Default::default(),
            length.unwrap_or(DEFAULT_SETTLEMENT_EPOCH_LEN),
        )
    }
}

/// A leaf value in the Sparse Merkle Tree
///
/// We use a global tree to store the state. This means that all of our entity types become
/// leaves. We wrap them in this enum to mark their type.
///
/// ### Notes
///
/// The position that each entry has in this list defines the discriminant
/// that will be used when it is encoded and hashed via the AbiToken. Take
/// care to ensure that this order is identical to the order laid out in
/// the `ITEM_*` constants.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, AbiToken, Eq)]
pub enum Item {
    Empty,
    Trader(Trader),
    Strategy(Strategy),
    Position(Position),
    BookOrder(BookOrder),
    Price(Price),
    /// Pool of collateral populated from profitable liquidation spread.
    InsuranceFund(Balance),
    Stats(Stats),
    Signer(ReleaseHash),
    Specs(SpecsExpr),
    InsuranceFundContribution(InsuranceFundContribution),
    EpochMetadata(EpochMetadata),
    TradableProduct(TradableProduct),
}

core_common::impl_contiguous_marker_for!(
    Trader
    Strategy
    Position
    BookOrder
    Price
    Balance
    Stats
    InsuranceFundContribution
    TradableProduct
);

core_common::impl_unsafe_byte_slice_for!(
    Trader
    Strategy
    Position
    BookOrder
    Price
    Balance
    Stats
    InsuranceFundContribution
    TradableProduct
);

#[cfg(all(feature = "arbitrary", feature = "test_harness"))]
impl Arbitrary for Item {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        let discriminator = *g
            .choose(&[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
            .unwrap();
        match discriminator {
            0 => Self::Empty,
            1 => Self::Trader(Arbitrary::arbitrary(g)),
            2 => Self::Strategy(Arbitrary::arbitrary(g)),
            3 => Self::Position(Arbitrary::arbitrary(g)),
            4 => Self::BookOrder(Arbitrary::arbitrary(g)),
            5 => Self::Price(Arbitrary::arbitrary(g)),
            6 => Self::InsuranceFund(Arbitrary::arbitrary(g)),
            7 => Self::Stats(Arbitrary::arbitrary(g)),
            8 => Self::Signer(Arbitrary::arbitrary(g)),
            9 => Self::Specs(Arbitrary::arbitrary(g)),
            10 => Self::InsuranceFundContribution(Arbitrary::arbitrary(g)),
            11 => Self::EpochMetadata(Arbitrary::arbitrary(g)),
            12 => Self::TradableProduct(Arbitrary::arbitrary(g)),
            _ => panic!("Invalid discriminator"),
        }
    }
}

pub const ITEM_EMPTY: u8 = 0;
pub const ITEM_TRADER: u8 = 1;
pub const ITEM_STRATEGY: u8 = 2;
pub const ITEM_POSITION: u8 = 3;
pub const ITEM_BOOK_ORDER: u8 = 4;
pub const ITEM_PRICE: u8 = 5;
pub const ITEM_INSURANCE_FUND: u8 = 6;
pub const ITEM_STATS: u8 = 7;
pub const ITEM_SIGNER: u8 = 8;
pub const ITEM_SPECS: u8 = 9;
pub const ITEM_INSURANCE_FUND_CONTRIBUTION: u8 = 10;
pub const ITEM_EPOCH_METADATA: u8 = 11;
pub const ITEM_TRADABLE_PRODUCT: u8 = 12;

impl Item {
    pub fn discriminant(&self) -> u8 {
        match self {
            Item::Empty => ITEM_EMPTY,
            Item::Trader(_) => ITEM_TRADER,
            Item::Strategy(_) => ITEM_STRATEGY,
            Item::Position(_) => ITEM_POSITION,
            Item::BookOrder(_) => ITEM_BOOK_ORDER,
            Item::Price(_) => ITEM_PRICE,
            Item::InsuranceFund(_) => ITEM_INSURANCE_FUND,
            Item::Stats(_) => ITEM_STATS,
            Item::Signer { .. } => ITEM_SIGNER,
            Item::Specs(_) => ITEM_SPECS,
            Item::InsuranceFundContribution(_) => ITEM_INSURANCE_FUND_CONTRIBUTION,
            Item::EpochMetadata(_) => ITEM_EPOCH_METADATA,
            Item::TradableProduct(_) => ITEM_TRADABLE_PRODUCT,
        }
    }
}

impl Default for Item {
    fn default() -> Self {
        Self::Empty
    }
}

impl sparse_merkle_tree::traits::Value for Item {
    fn to_h256(&self) -> sparse_merkle_tree::H256 {
        let message: Vec<u8> = if self.discriminant() == ITEM_EMPTY {
            return sparse_merkle_tree::H256::zero();
        } else {
            let token = self.clone().into_token();
            token.abi_encode()
        };
        message.keccak256().into()
    }

    fn zero() -> Self {
        Default::default()
    }
}

/// Inserts initial data in the verified state tree and db then returns the state root hash.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub enum BootstrapState {
    /// Runs the genesis ceremony with the unverified values.
    /// We expect these values to be published ahead of time so anyone can verify the
    /// genesis state before joining the cluster.
    #[serde(rename_all = "camelCase")]
    Genesis {
        #[serde(with = "as_specs")]
        specs: HashMap<SpecsKey, SpecsExpr>,
        #[serde(default)]
        insurance_fund_cap: Balance,
        #[serde(default)]
        ddx_fee_pool: UnscaledI128,
        #[serde(default)]
        release_hash: Bytes32,
    },
    /// Starts a cluster from an existing state.
    /// This expects the forked distributed state to be available in the local cluster.
    Resume {
        #[serde(rename = "snapshotEpochId")]
        snapshot_epoch_id: Option<EpochId>,
        #[serde(rename = "includeReleaseSigners")]
        include_release_signers: Option<ReleaseHash>,
    },
}

impl BootstrapState {
    pub fn is_genesis(&self) -> bool {
        matches!(self, BootstrapState::Genesis { .. })
    }

    pub fn from_env_genesis() -> Self {
        let text = std::env::var("GENESIS_PARAMS").expect("GENESIS_PARAMS must be set");
        let bootstrap_state =
            serde_json::from_str::<Self>(&text).expect("Cannot deserialize GENESIS_PARAMS");
        assert!(
            bootstrap_state.is_genesis(),
            "Expected GENESIS_PARAMS to be the genesis variant"
        );
        bootstrap_state
    }
}

#[derive(Debug, Clone, Builder)]
pub struct EnvironmentContext {
    /// Connection string for the PostgreSQL database cluster.
    pub db_connstr: String,
    /// The number of worker threads.
    pub core_threads: usize,
    /// Initial set of peer URLs for network discovery.
    pub bootstrap_nodes: BootstrapNodeUrls,
    /// The name of the deployment we are using, ie. devnet.
    pub contract_deployment: String,
    /// URL for the Contract Server that provides blockchain deployment specifications.
    pub contract_server_url: String,
    /// System backoff parameters
    pub backoff: BackoffConfig,
}

impl EnvironmentContextBuilder {
    pub fn from_env() -> Self {
        let mut builder = Self::default();
        if let (Ok(db_name), Ok(pg_cluster)) = (
            std::env::var("OPERATOR_DB_NAME"),
            std::env::var("PG_CLUSTER"),
        ) {
            builder.db_connstr(format!("{}/{}", pg_cluster, db_name));
        }
        builder.core_threads(
            std::env::var("CORE_THREADS")
                .map(|s| s.parse().unwrap())
                // FIXME: Why not align with Enclave.xml.template?
                .unwrap_or_else(|_| RUNTIME_MAX_WORKER_THREADS),
        );
        if let Ok(bootstrap_nodes) = std::env::var("BOOTSTRAP_NODE_URLS") {
            builder.bootstrap_nodes(BootstrapNodeUrls::new(
                bootstrap_nodes
                    .split(',')
                    .map(|s| s.parse().unwrap())
                    .collect(),
            ));
        }

        if let Ok(contract_deployment) = std::env::var("CONTRACT_DEPLOYMENT") {
            builder.contract_deployment(contract_deployment);
        }
        if let Ok(contract_server_url) = std::env::var("CONTRACT_SERVER_URL") {
            builder.contract_server_url(contract_server_url);
        }
        builder.backoff(BackoffConfig::from_env());
        builder
    }
}

impl FromArgMatches for EnvironmentContext {
    fn from_arg_matches(matches: &ArgMatches) -> std::prelude::v1::Result<Self, clap::Error> {
        // First build from env variables
        let mut builder = EnvironmentContextBuilder::from_env();
        // Override with values provided by arguments if applicable
        if let Some(db_connstr) = matches.get_one::<String>("db_connstr") {
            builder.db_connstr(db_connstr.clone());
        }
        if let Some(core_threads) = matches.get_one::<usize>("core_threads") {
            builder.core_threads(*core_threads);
        }
        if let Some(bootstrap_nodes) = matches.get_one::<String>("bootstrap_nodes") {
            builder.bootstrap_nodes(BootstrapNodeUrls::new(
                bootstrap_nodes
                    .split(',')
                    .map(|s| s.parse().unwrap())
                    .collect(),
            ));
        }
        if let Some(contract_deployment) = matches.get_one::<String>("contract_deployment") {
            builder.contract_deployment(contract_deployment.clone());
        }
        if let Some(contract_server_url) = matches.get_one::<String>("contract_server_url") {
            builder.contract_server_url(contract_server_url.clone());
        }
        if let Ok(backoff) = BackoffConfig::from_arg_matches(matches) {
            builder.backoff(backoff.clone());
        }
        Ok(builder.build().unwrap())
    }

    fn update_from_arg_matches(
        &mut self,
        matches: &ArgMatches,
    ) -> std::prelude::v1::Result<(), clap::Error> {
        if let Some(db_connstr) = matches.get_one::<String>("db_connstr") {
            self.db_connstr = db_connstr.clone();
        }
        if let Some(core_threads) = matches.get_one::<usize>("core_threads") {
            self.core_threads = *core_threads;
        }
        if let Some(bootstrap_nodes) = matches.get_one::<String>("bootstrap_nodes") {
            self.bootstrap_nodes = BootstrapNodeUrls::new(
                bootstrap_nodes
                    .split(',')
                    .map(|s| s.parse().unwrap())
                    .collect(),
            );
        }
        if let Some(contract_deployment) = matches.get_one::<String>("contract_deployment") {
            self.contract_deployment = contract_deployment.clone();
        }
        if let Some(contract_server_url) = matches.get_one::<String>("contract_server_url") {
            self.contract_server_url = contract_server_url.clone();
        }
        if let Ok(backoff) = BackoffConfig::from_arg_matches(matches) {
            self.backoff = backoff.clone();
        }
        Ok(())
    }
}

impl Args for EnvironmentContext {
    fn augment_args(cmd: Command) -> Command {
        let mut cmd = cmd;
        cmd = cmd
            .arg(arg!(--db_connstr [STRING] "Connection string for the PostgreSQL database cluster."))
            .arg( arg!(--core_threads [NUMERIC] "The number of worker threads.")
                    .value_parser(value_parser!(usize))
            )
            .arg( arg!(--bootstrap_nodes [COMMA_SEPARATED_URLS] "Initial set of peer URLs for network discovery.")
            )
            .arg(arg!(--contract_deployment [STRING] "The name of the deployment we are using, ie. devnet."))
            .arg(arg!(--contract_server_url [URL] "URL for the Contract Server that provides blockchain deployment specifications."));
        BackoffConfig::augment_args(cmd)
    }

    fn augment_args_for_update(cmd: Command) -> Command {
        let mut cmd = cmd;
        cmd = cmd
            .arg(arg!(--db_connstr [STRING] "Connection string for the PostgreSQL database cluster."))
            .arg( arg!(--core_threads [NUMERIC] "The number of worker threads.")
                    .value_parser(value_parser!(usize))
            )
            .arg( arg!(--bootstrap_nodes [COMMA_SEPARATED_URLS] "Initial set of peer URLs for network discovery.")
            )
            .arg(arg!(--contract_deployment [STRING] "The name of the deployment we are using, ie. devnet."))
            .arg(arg!(--contract_server_url [URL] "URL for the Contract Server that provides blockchain deployment specifications."));
        BackoffConfig::augment_args(cmd)
    }
}

impl From<&NodeContext> for EnvironmentContext {
    fn from(node_ctx: &NodeContext) -> Self {
        EnvironmentContext {
            db_connstr: node_ctx.db_connstr.clone(),
            core_threads: node_ctx.core_threads,
            bootstrap_nodes: node_ctx.bootstrap_nodes.clone(),
            contract_deployment: node_ctx.contract_deployment.clone(),
            contract_server_url: node_ctx.contract_server_url.clone(),
            backoff: node_ctx.backoff.clone(),
        }
    }
}

/// Configuration for the node.
///
/// Utilizes the builder pattern to accommodate different operating modes.
/// Primarily, `from_env` reads configurations from the environment variables,
/// while `test_defaults` provides defaults suitable for testing, eschewing assumptions
/// about default values. The builder's validation ensures all necessary parameters are provided.
#[derive(Debug, Clone, Builder)]
pub struct DdxNodeContext {
    pub node_context: NodeContext,
    pub nb_confirmations: u64,
    pub bootstrap_state: Option<BootstrapState>,
    // TODO: remove this since its only relevant for the eth-bridge
    pub submit_withdrawal_threshold: u64,
    // TODO: remove this since its only relevant for the eth-bridge
    pub submit_interval: u64,
    // TODO: Watch out with this as it skips signature validation. Place behind a feature?
    pub dev_mode: bool,
}

impl DdxNodeContextBuilder {
    /// Create a new DdxNodeContextBuilder from a NodeContext using environment variables.
    pub fn from_env(base_ctx: NodeContext) -> Self {
        let mut builder = Self::default();
        builder.node_context(base_ctx);
        builder.nb_confirmations(*NB_CONFIRMATION as u64);
        builder.submit_withdrawal_threshold(
            std::env::var("SUBMIT_WITHDRAWAL_THRESHOLD")
                .map(|s| s.parse().unwrap())
                .unwrap_or_else(|_| SUBMIT_WITHDRAWAL_THRESHOLD),
        );
        let daily_epochs: u64 = (Decimal::new(24 * 3600, 0) / Into::<Decimal>::into(*EPOCH_SIZE))
            .ceil()
            .try_into()
            .unwrap();
        builder.submit_interval(
            std::env::var("SUBMIT_INTERVAL")
                .map(|s| s.parse().unwrap())
                .unwrap_or_else(|_| daily_epochs),
        );
        // NOTE: Defaulting to `Some(None)` (meaning a normal follower node) if BOOTSTRAP_STATE is
        // not set or set to `false`.
        builder.bootstrap_state(match std::env::var("BOOTSTRAP_STATE") {
            Ok(s) if s == "false" => None,
            Ok(s) => Some(serde_json::from_str(&s).expect("Malformed BOOTSTRAP_STATE")),
            Err(_) => None,
        });
        // Sets false by default as it is the secure option, and only acceptable option for production nodes.
        builder.dev_mode(false);
        builder
    }

    #[cfg(feature = "test_harness")]
    pub fn test_defaults() -> Self {
        let mut builder = Self::default();
        builder.nb_confirmations(DEFAULT_NB_CONFIRMATIONS);
        builder.bootstrap_state(None);
        builder.submit_withdrawal_threshold(0);
        builder.submit_interval(0);
        builder.dev_mode(true);
        builder
    }
}

/// Contextual/configuration variables applicable to the trusted context
#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct TrustedContext {
    pub nb_confirmations: u32,
    pub ema_periods: u64,
    pub clock_tick_len: u64,
    // TODO: We should consider getting this from market specs.
    pub price_checkpoint_len: u64,
    pub epoch_len: u64,
    pub settlement_epoch_len: u64,
    pub static_settlement_action_periods: HashMap<SettlementAction, u64>,
    #[cfg(feature = "fixed_expiry_future")]
    pub expiry_price_leaves_duration: u64,
    pub trade_mining_len: u64,
    pub trade_mining_reward_per_epoch: UnscaledI128,
    pub trade_mining_maker_reward_percentage: UnscaledI128,
    pub trade_mining_taker_reward_percentage: UnscaledI128,
}

#[cfg(feature = "test_harness")]
impl TrustedContext {
    pub fn test_defaults() -> Self {
        TrustedContext {
            nb_confirmations: DEFAULT_NB_CONFIRMATIONS as u32,
            clock_tick_len: DEFAULT_TEST_CLOCK_TICK_MS,
            ema_periods: DEFAULT_EMA_PERIODS,
            epoch_len: DEFAULT_EPOCH_LEN,
            price_checkpoint_len: DEFAULT_PRICE_CHECKPOINT_INTERVAL,
            settlement_epoch_len: DEFAULT_SETTLEMENT_EPOCH_LEN,
            static_settlement_action_periods: [
                (
                    SettlementAction::PnlRealization,
                    DEFAULT_PNL_REALIZATION_PERIOD_LEN,
                ),
                (
                    SettlementAction::FundingDistribution,
                    DEFAULT_FUNDING_PERIOD_LEN,
                ),
                (
                    SettlementAction::TradeMining,
                    DEFAULT_TRADE_MINING_PERIOD_LEN,
                ),
            ]
            .into(),
            trade_mining_len: DEFAULT_TRADE_MINING_DURATION_IN_SETTLEMENT_EPOCHS,
            #[cfg(feature = "fixed_expiry_future")]
            expiry_price_leaves_duration: DEFAULT_EXPIRY_PRICE_LEAVES_DURATION,
            trade_mining_reward_per_epoch: default_trade_mining_reward_per_epoch().into(),
            trade_mining_maker_reward_percentage: default_trade_mining_maker_reward_percentage()
                .into(),
            trade_mining_taker_reward_percentage: default_trade_mining_taker_reward_percentage()
                .into(),
        }
    }
}

impl ConfigurableFromEnv for TrustedContext {
    fn from_env() -> Self {
        let clock_tick_len = std::env::var("CLOCK_TICK_SIZE")
            .ok()
            .map(|s| s.parse::<u64>().unwrap())
            .unwrap_or(crate::constants::DEFAULT_CLOCK_TICK_MS);

        let settlement_epoch_len = *EPOCH_SIZE * *SETTLEMENT_EPOCH_MULTIPLIER;
        TrustedContext {
            nb_confirmations: *NB_CONFIRMATION,
            ema_periods: *EMA_PERIODS,
            clock_tick_len,
            epoch_len: *EPOCH_SIZE,
            price_checkpoint_len: *PRICE_CHECKPOINT_SIZE,
            settlement_epoch_len,
            static_settlement_action_periods: [
                (
                    SettlementAction::PnlRealization,
                    settlement_epoch_len * *PNL_REALIZATION_SETTLEMENT_MULTIPLIER,
                ),
                (
                    SettlementAction::FundingDistribution,
                    settlement_epoch_len * *FUNDING_SETTLEMENT_MULTIPLIER,
                ),
                (
                    SettlementAction::TradeMining,
                    settlement_epoch_len * *TRADE_MINING_SETTLEMENT_MULTIPLIER,
                ),
            ]
            .into(),
            trade_mining_len: *TRADE_MINING_LENGTH,
            #[cfg(feature = "fixed_expiry_future")]
            expiry_price_leaves_duration: *EXPIRY_PRICE_LEAVES_DURATION,
            trade_mining_reward_per_epoch: *TRADE_MINING_REWARD_PER_EPOCH,
            trade_mining_maker_reward_percentage: *TRADE_MINING_MAKER_REWARD_PERCENTAGE,
            trade_mining_taker_reward_percentage: *TRADE_MINING_TAKER_REWARD_PERCENTAGE,
        }
    }
}

#[cfg(feature = "database")]
impl ToSql for Epoch {
    fn to_sql(
        &self,
        ty: &Type,
        out: &mut bytes::BytesMut,
    ) -> Result<IsNull, Box<dyn std::error::Error + 'static + Sync + Send>> {
        let json: String = serde_json::to_string(&self)?;
        json.to_sql(ty, out)
    }

    fn accepts(ty: &Type) -> bool {
        <String as ToSql>::accepts(ty)
    }

    to_sql_checked!();
}

#[cfg(feature = "database")]
impl<'a> FromSql<'a> for Epoch {
    fn from_sql(
        ty: &Type,
        raw: &'a [u8],
    ) -> Result<Self, Box<dyn std::error::Error + Sync + Send>> {
        let s: String = String::from_sql(ty, raw)?;
        let decoded: Epoch = serde_json::from_str(&s)?;
        Ok(decoded)
    }

    fn accepts(ty: &Type) -> bool {
        <String as FromSql>::accepts(ty)
    }
}

#[derive(AbiToken, Debug)]
pub struct LatestCheckpoint {
    pub block_number: U256,
    pub state_root: B256,
    pub transaction_root: B256,
    pub epoch_id: U256,
}

/// Request log commands for the transition of each epoch type.
///
/// This is generally discovered by find the last command of each type in the request log.
/// Both the sequencer and processor need this to know when to advance to the next epoch.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TickCmds {
    pub epoch_cmd: AdvanceEpoch,
    pub settlement_cmd: AdvanceSettlementEpoch,
    pub price_checkpoint_cmd: MintPriceCheckpoint,
    pub update_product_listings_cmd: UpdateProductListings,
}

#[derive(Debug, Default, Clone, Serialize, Deserialize, PartialEq)]
pub struct AllCmds {
    pub time: StampedTimeValue,
    pub block_cmd: Block,
    pub epoch_cmd: AdvanceEpoch,
    pub settlement_cmd: AdvanceSettlementEpoch,
    pub price_checkpoint_cmd: MintPriceCheckpoint,
    pub update_product_listings_cmd: UpdateProductListings,
    pub index_price_cmds: Vec<IndexPrice>,
}

impl AllCmds {
    pub fn split(self) -> (TickCmds, TimeValue, Block, Vec<IndexPrice>) {
        let AllCmds {
            time,
            epoch_cmd,
            settlement_cmd,
            price_checkpoint_cmd,
            update_product_listings_cmd,
            block_cmd,
            index_price_cmds,
        } = self;
        (
            TickCmds {
                epoch_cmd,
                settlement_cmd,
                price_checkpoint_cmd,
                update_product_listings_cmd,
            },
            time.value,
            block_cmd,
            index_price_cmds,
        )
    }
}

impl TryFrom<Vec<Cmd>> for AllCmds {
    type Error = Error;

    fn try_from(value: Vec<Cmd>) -> Result<Self, Self::Error> {
        // TODO: Do we need to check number of IndexPrice? If so then need env var specifying the
        // number of products expected
        ensure!(
            value.iter().fold(0, |acc, x| {
                if !matches!(x, Cmd::IndexPrice(_) | Cmd::Genesis,) {
                    acc + 1
                } else {
                    acc
                }
            }) == NB_INIT_CMDS,
            "Expected {:?} non-index-price commands, found {:?}",
            NB_INIT_CMDS,
            value
        );
        let mut all_cmds = AllCmds::default();
        let mut index_price_cmds = vec![];
        for cmd in value {
            match cmd {
                Cmd::Block(b) => all_cmds.block_cmd = b,
                Cmd::AdvanceTime(t) => all_cmds.time = t,
                Cmd::AdvanceEpoch(e) => all_cmds.epoch_cmd = e,
                Cmd::AdvanceSettlementEpoch(s) => all_cmds.settlement_cmd = s,
                Cmd::PriceCheckpoint(c) => all_cmds.price_checkpoint_cmd = c,
                Cmd::IndexPrice(p) => index_price_cmds.push(p),
                Cmd::UpdateProductListings(u) => all_cmds.update_product_listings_cmd = u,
                Cmd::UpdateEnrollment(_k) => continue,
                _ => bail!("Unexpected command {:?}", cmd),
            }
        }
        all_cmds.index_price_cmds = index_price_cmds;
        Ok(all_cmds)
    }
}

// TODO: Link with the codes
#[derive(Debug, Clone, PartialEq, Eq, std::hash::Hash, Serialize, Deserialize)]
pub enum CmdKind {
    AdvanceEpoch,
    AdvanceSettlementEpoch,
    MintPriceCheckpoint,
    AdvanceTime,
    AdvanceBlock,
    UpdateProductListings,
}

/// Holds commands at the tail of the request log.
///
/// The tail represents the latest (or current) commands for each kind. For example, to query the current
/// epoch at the request log level, we fetch the `TailCmds` and select the `CmdKind::AdvanceEpoch` entry.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TailCmds {
    pub cmds: AllCmds,
    pub next_index_to_assign: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct EpochInitParams {
    // TODO: Consider storing the sequenced request list and cast in the enclave while verifying signatures
    pub cmds: AllCmds,
    /// Index of the last request to process, may exist in the request log but not the tx log.
    pub next_index_to_process: u64,
}

pub type SidedBook = BTreeMap<Decimal, Vec<BookOrder>>;

/// An insurance fund contribution
#[cfg_attr(feature = "python", pyclass(get_all, set_all))]
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize, AbiToken, Eq)]
#[serde(rename_all = "camelCase")]
#[repr(C)]
pub struct InsuranceFundContribution {
    /// Total contribution to the insurance fund, minus any withdrawals
    pub avail_balance: Balance,
    /// Balance locked for withdrawal
    pub locked_balance: Balance,
}

impl VoidableItem for InsuranceFundContribution {
    fn is_void(&self) -> bool {
        self.avail_balance.is_zero() && self.locked_balance.is_zero()
    }
}

#[cfg(feature = "python")]
#[pymethods]
impl InsuranceFundContribution {
    #[new]
    fn new_py(avail_balance: Balance, locked_balance: Balance) -> Self {
        Self {
            avail_balance,
            locked_balance,
        }
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for InsuranceFundContribution {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Self {
            avail_balance: Arbitrary::arbitrary(g),
            locked_balance: Arbitrary::arbitrary(g),
        }
    }
}

/// Metadata about an epoch that has been transitioned.
#[cfg_attr(feature = "python", pyclass(get_all, set_all))]
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize, AbiToken, Eq)]
#[serde(rename_all = "camelCase")]
pub struct EpochMetadata {
    /// The DDX fee pool. This represents the total DDX fees collected in this epoch and are
    /// distributed among custodians during a valid checkpoint.
    pub ddx_fee_pool: UnscaledI128,
    /// The next book ordinals for all of the active markets. This mapping
    /// allows follower nodes to reliably generate the market index from the
    /// sparse merkle tree. The ordinals are logged at the end of the epoch and are None if this is
    /// the current epoch.
    pub next_book_ordinals: HashMap<ProductSymbol, u64>,
}

impl VoidableItem for EpochMetadata {
    fn is_void(&self) -> bool {
        false
    }
}

#[cfg(feature = "python")]
#[pymethods]
impl EpochMetadata {
    #[new]
    fn new_py(ddx_fee_pool: UnscaledI128, next_book_ordinals: HashMap<ProductSymbol, u64>) -> Self {
        Self {
            ddx_fee_pool,
            next_book_ordinals,
        }
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for EpochMetadata {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Self {
            ddx_fee_pool: Arbitrary::arbitrary(g),
            next_book_ordinals: Arbitrary::arbitrary(g),
        }
    }
}

#[derive(PartialEq, PartialOrd)]
pub struct SchemaVersion {
    pub major: u64,
    pub minor: u64,
    pub patch: u64,
}

impl FromStr for SchemaVersion {
    type Err = Error;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let mut version_array = [0_u64; 3];
        if !s.is_empty() {
            for (i, v) in s.splitn(3, '.').enumerate() {
                version_array[i] = v
                    .parse::<u64>()
                    .map_err(|_| Error::Parse(format!("Failed to parse version schema {}", s)))?;
            }
        }
        Ok(SchemaVersion {
            major: version_array[0],
            minor: version_array[1],
            patch: version_array[2],
        })
    }
}

impl std::fmt::Debug for SchemaVersion {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}.{}.{}", self.major, self.minor, self.patch)
    }
}

impl std::fmt::Display for SchemaVersion {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:?}", self)
    }
}

#[cfg(feature = "database")]
impl ToSql for SchemaVersion {
    fn to_sql(
        &self,
        ty: &Type,
        out: &mut bytes::BytesMut,
    ) -> Result<IsNull, Box<dyn std::error::Error + 'static + Sync + Send>> {
        self.to_string().to_sql(ty, out)
    }

    fn accepts(ty: &Type) -> bool {
        <String as ToSql>::accepts(ty)
    }

    to_sql_checked!();
}

#[cfg(feature = "database")]
impl<'a> FromSql<'a> for SchemaVersion {
    fn from_sql(
        ty: &Type,
        raw: &'a [u8],
    ) -> Result<Self, Box<dyn std::error::Error + Sync + Send>> {
        let version_string: String = String::from_sql(ty, raw)?;
        Ok(version_string.parse::<Self>()?)
    }

    fn accepts(ty: &Type) -> bool {
        <String as FromSql>::accepts(ty)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use alloy_dyn_abi::{DynSolType, DynSolValue};
    use core_common::util::tokenize::generate_schema;
    use quickcheck::QuickCheck;

    #[test]
    fn test_serialize_tick_cmd() {
        let tick_cmd = TickCmds {
            epoch_cmd: AdvanceEpoch::default(),
            settlement_cmd: AdvanceSettlementEpoch::default(),
            price_checkpoint_cmd: MintPriceCheckpoint::default(),
            update_product_listings_cmd: UpdateProductListings::default(),
        };
        let serialized = cbor4ii::serde::to_vec(vec![], &tick_cmd).unwrap();
        let deserialized = cbor4ii::serde::from_slice(&serialized).unwrap();
        assert_eq!(tick_cmd, deserialized);
    }

    #[test]
    fn test_serialize_all_cmds() {
        let all_cmds = AllCmds::default();
        let serialized = cbor4ii::serde::to_vec(vec![], &all_cmds).unwrap();
        let deserialized = cbor4ii::serde::from_slice(&serialized).unwrap();
        assert_eq!(all_cmds, deserialized);
    }

    #[test]
    fn prop_ethabi_roundtrip_item() {
        fn ethabi_roundtrip_item(input: Item) -> bool {
            println!("input: {:?}", input);
            let token = DynSolValue::Tuple(vec![input.clone().into_token()]);
            let bytes = token.abi_encode();
            let schema: DynSolType = generate_schema(&token).into();
            println!("schema: {:?}", schema);
            let decoded_token = schema
                .abi_decode(&bytes)
                .unwrap()
                .as_tuple()
                .unwrap()
                .first()
                .unwrap()
                .clone();
            let decoded = Item::from_token(decoded_token).unwrap();
            decoded == input
        }
        QuickCheck::new()
            .gen(quickcheck::Gen::new(10))
            .quickcheck(ethabi_roundtrip_item as fn(Item) -> bool);
    }

    #[test]
    fn parse_schema_version() {
        let empty_version = "";
        let schema_version = empty_version.parse::<SchemaVersion>().unwrap();
        assert_eq!(schema_version.to_string(), String::from("0.0.0"));

        let version_string = "1.2.3";
        let schema_version = version_string.parse::<SchemaVersion>().unwrap();
        assert_eq!(
            schema_version,
            SchemaVersion {
                major: 1,
                minor: 2,
                patch: 3
            }
        );
    }
}
