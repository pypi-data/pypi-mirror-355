#[cfg(feature = "fixed_expiry_future")]
use crate::constants::DEFAULT_EXPIRY_PRICE_LEAVES_DURATION;
use crate::{
    constants::{
        DEFAULT_EPOCH_LEN, DEFAULT_FUNDING_SETTLEMENT_MULTIPLIER, DEFAULT_NB_CONFIRMATIONS,
        DEFAULT_PNL_REALIZATION_SETTLEMENT_MULTIPLIER, DEFAULT_PRICE_CHECKPOINT_INTERVAL,
        DEFAULT_SETTLEMENT_EPOCH_MULTIPLIER, DEFAULT_TRADE_MINING_DURATION_IN_SETTLEMENT_EPOCHS,
        DEFAULT_TRADE_MINING_SETTLEMENT_MULTIPLIER,
    },
    util::{default_trade_mining_maker_reward_percentage, default_trade_mining_reward_per_epoch},
};
use core_common::{U128, types::primitives::UnscaledI128};
use lazy_static::lazy_static;
use rust_decimal::prelude::{Decimal, One};
use std::{env, string::ToString};

// ##
// ###
// ####
// #####
// ######
// TODO: DEPRECATED - Do not add anything here and migrate what is here into TrustedContext or NodeContext.
// ######
// #####
// ####
// ###
// ##

// FIXME: Remove these environment variables in favor of the untrusted context.
lazy_static! {
    // The name of the contract deployment that should be used. This is used to sanity check the
    // output of the contract server.
    pub static ref CONTRACT_DEPLOYMENT: String =
        env::var("CONTRACT_DEPLOYMENT").unwrap();
    // The URL to use when making "deployment" or "snapshot" requests to the contract server.
    pub static ref CONTRACT_SERVER_URL: String =
        env::var("CONTRACT_SERVER_URL").unwrap();
    // The number of block confirmations required for a block to be seen as "confirmed".
    // We utilize confirmed blocks rather than new Ethereum blocks because they
    // have a much smaller probability of being dropped from the main Ethereum
    // chain in a block re-organization.
    pub static ref NB_CONFIRMATION: u32 = env::var("NB_CONFIRMATION")
        .unwrap_or(format!("{:?}", DEFAULT_NB_CONFIRMATIONS))
        .parse::<u32>()
        .unwrap();
    // The number of periods that should be considered when computing the exponential
    // moving average component of the mark price.
    pub static ref EMA_PERIODS: u64 = env::var("EMA_PERIODS")
        .unwrap_or_else(|_| "30".to_string())
        .parse::<u64>()
        .unwrap();
    // The length of checkpoint epochs in milliseconds.
    pub static ref EPOCH_SIZE: u64 = env::var("EPOCH_SIZE")
        .unwrap_or(format!("{:?}", DEFAULT_EPOCH_LEN))
        .parse::<u64>()
        .unwrap();
    // A multiplier that specifies the length of a settlement epoch in checkpoint epochs.
    pub static ref SETTLEMENT_EPOCH_MULTIPLIER: u64 = env::var("SETTLEMENT_EPOCH_MULTIPLIER")
        .unwrap_or(format!("{:?}", DEFAULT_SETTLEMENT_EPOCH_MULTIPLIER))
        .parse::<u64>()
        .unwrap();
    // A multiplier/factor that specifies the period of pnl realizations in settlement epochs.
    pub static ref PNL_REALIZATION_SETTLEMENT_MULTIPLIER: u64 = env::var("PNL_REALIZATION_SETTLEMENT_MULTIPLIER")
        .unwrap_or(format!("{:?}", DEFAULT_PNL_REALIZATION_SETTLEMENT_MULTIPLIER))
        .parse::<u64>()
        .unwrap();
    /// A multiplier/factor that specifies the period of funding distributions in settlement
    /// epochs.
    pub static ref FUNDING_SETTLEMENT_MULTIPLIER: u64 = env::var("FUNDING_SETTLEMENT_MULTIPLIER")
        .unwrap_or(format!("{:?}", DEFAULT_FUNDING_SETTLEMENT_MULTIPLIER))
        .parse::<u64>()
        .unwrap();
    pub static ref TRADE_MINING_SETTLEMENT_MULTIPLIER: u64 = env::var("TRADE_MINING_SETTLEMENT_MULTIPLIER")
        .unwrap_or(format!("{:?}", DEFAULT_TRADE_MINING_SETTLEMENT_MULTIPLIER))
        .parse::<u64>()
        .unwrap();
    // The length of price checkpoint epochs in milliseconds.
    pub static ref PRICE_CHECKPOINT_SIZE: u64 = env::var("PRICE_CHECKPOINT_SIZE")
        .unwrap_or(format!("{:?}", DEFAULT_PRICE_CHECKPOINT_INTERVAL))
        .parse::<u64>()
        .unwrap();
    pub static ref MAX_RAFT_RPC_TIMEOUT_IN_SECS: u64 = env::var("MAX_RAFT_RPC_TIMEOUT_IN_SECS").unwrap().parse::<u64>().unwrap();
    // The length of trade mining in trade mining periods. Trade mining distributions
    // stop after this amount of trade mining periods.
    pub static ref TRADE_MINING_LENGTH: u64 = env::var("TRADE_MINING_LENGTH")
        .unwrap_or(format!("{:?}", DEFAULT_TRADE_MINING_DURATION_IN_SETTLEMENT_EPOCHS))
        .parse()
        .unwrap();
    // The percentage of trade mining rewards that should be paid to makers in
    // each trade mining period.
    pub static ref TRADE_MINING_MAKER_REWARD_PERCENTAGE: UnscaledI128 =
        get_trade_mining_maker_reward_percentage().into();
    // The percentage of trade mining rewards that should be paid to takers in
    // each trade mining period.
    pub static ref TRADE_MINING_TAKER_REWARD_PERCENTAGE: UnscaledI128 =
        get_trade_mining_taker_reward_percentage().into();
    // The total amount of DDX that should be awarded every epoch.
    pub static ref TRADE_MINING_REWARD_PER_EPOCH: UnscaledI128 = env::var("TRADE_MINING_REWARD_PER_EPOCH").map_or(UnscaledI128::new(default_trade_mining_reward_per_epoch()), |v| v.parse::<U128>().expect("TRADE_MINING_REWARD_PER_EPOCH to be a U128").into());
    pub static ref USE_FAUCET: bool = env::var("USE_FAUCET").unwrap_or_else(|_|"false".to_string()).parse::<bool>().expect("USE_FAUCET to be a boolean");
}

#[cfg(feature = "fixed_expiry_future")]
lazy_static! {
    /// The duration of price leaves to compute the futures expiry price from
    pub static ref EXPIRY_PRICE_LEAVES_DURATION: u64 = env::var("EXPIRY_PRICE_LEAVES_DURATION")
        .unwrap_or(format!("{:?}", DEFAULT_EXPIRY_PRICE_LEAVES_DURATION))
        .parse::<u64>()
        .unwrap();
}

fn get_trade_mining_maker_reward_percentage() -> Decimal {
    let trade_mining_maker_reward_percentage = env::var("TRADE_MINING_MAKER_REWARD_PERCENTAGE")
        .unwrap_or(format!(
            "{:?}",
            default_trade_mining_maker_reward_percentage()
        ))
        .parse::<Decimal>()
        .expect("TRADE_MINING_MAKER_REWARD_PERCENTAGE to be parsed");
    if trade_mining_maker_reward_percentage > Decimal::from(1) {
        panic!("TRADE_MINING_MAKER_REWARD_PERCENTAGE can't be greater than 1");
    }
    trade_mining_maker_reward_percentage
}

fn get_trade_mining_taker_reward_percentage() -> Decimal {
    Decimal::one() - get_trade_mining_maker_reward_percentage()
}
