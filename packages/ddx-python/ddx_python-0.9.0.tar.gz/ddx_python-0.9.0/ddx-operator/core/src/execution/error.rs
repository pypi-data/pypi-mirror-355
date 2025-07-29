use crate::{
    constants::EXEC_OUTCOME_MSG_MAX_SIZE,
    types::{
        identifiers::StrategyIdHash,
        primitives::{OrderHash, ProductSymbol},
        request::OrderType,
        transaction::{ExecutionOps, OrderRejection},
    },
};
use core_common::Error as DDXCommonError;
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};

#[derive(Debug, thiserror::Error, Clone, PartialEq, Eq, Deserialize, Serialize)]
pub enum SafetyFailure {
    #[error("Trader not found")]
    TraderNotFound,
    #[error("Minimum collateral requirements breached")]
    NotEnoughCollateral,
    #[error("Trader making request has no strategies")]
    NoStrategies,
    #[error("Specified strategy id with hash {strategy_id_hash} not found for trader")]
    StrategyNotFound { strategy_id_hash: StrategyIdHash },
    #[error("EIP-712 recovery returned a mismatching trader")]
    SignatureRecoveryMismatch,
    #[error("Insurance fund contribution not found")]
    InsuranceFundContributionNotFound,
    #[error(
        "Max order notional ({amount:?} * {mark_price:?}) breached safety: {notional_safety:?}"
    )]
    MaxOrderNotionalBreached {
        amount: Decimal,
        mark_price: Decimal,
        notional_safety: Decimal,
    },
    // TODO: This should be updated to be clearer. As of right now it's somewhat
    // confusing.
    #[error(
        "Max taker price deviation breached: taker price {taker_price:?} deviates from mark price {mark_price:?} by more than {max_taker_price_deviation:?}"
    )]
    MaxTakerPriceDeviationBreached {
        taker_price: Decimal,
        mark_price: Decimal,
        max_taker_price_deviation: Decimal,
    },
    #[error("Not an open order symbol={symbol:?} order hash={order_hash:?}")]
    OrderNotFound {
        symbol: ProductSymbol,
        order_hash: OrderHash,
    },
    #[error("OMF is less than IMF: {omf:?} < {imf:?}")]
    OMFLessThanIMF { omf: Decimal, imf: Decimal },
    #[error("Max withdrawal amount breached: {amount:?} > {maximum_withdraw_amount:?}")]
    MaxWithdrawAmountBreached {
        amount: Decimal,
        maximum_withdraw_amount: Decimal,
    },
    #[error("Max DDX withdrawal amount breached: {amount:?} > {maximum_withdraw_amount:?}")]
    MaxDDXWithdrawAmountBreached {
        amount: Decimal,
        maximum_withdraw_amount: Decimal,
    },
    #[error("Too much collateral to withdraw {amount:?} DDX: {balance:?} > {limit:?}")]
    TooMuchCollateralToWithdrawDDX {
        amount: Decimal,
        balance: Decimal,
        limit: Decimal,
    },
    #[error(
        "Max Insurance Fund withdrawal amount breached: {amount:?} > {maximum_withdraw_amount:?} ({reason:?})"
    )]
    MaxInsuranceFundWithdrawBreached {
        amount: Decimal,
        maximum_withdraw_amount: Decimal,
        reason: MaxInsuranceFundWithdrawBreachedReason,
    },
    #[error("Order price is negative")]
    OrderPriceNeg,
    #[error("Order amount is zero or negative")]
    OrderAmountZeroNeg,
    #[error(
        "Order amount {order_amount:?} is not a multiple of minimum order size {minimum_order_size:?}"
    )]
    OrderAmountNotMultipleOfMinOrderSize {
        order_amount: Decimal,
        minimum_order_size: Decimal,
    },
    #[error(
        "Order type {order_type:?} incompatible with price {price:?} and/or stop price {stop_price:?}"
    )]
    OrderTypeIncompatibleWithPrice {
        order_type: OrderType,
        price: Decimal,
        stop_price: Decimal,
    },
    #[error("Order price {price:?} is not a multiple of tick size {tick_size:?}")]
    PriceNotMultipleOfTickSize { price: Decimal, tick_size: Decimal },
    #[error("Order symbol {symbol:?} does not refer to a supported market")]
    UnsupportedMarket { symbol: ProductSymbol },
    #[error("USDC is the only supported currency at this time")]
    UnsupportedCurrency,
    #[error("Too many open orders for the current market")]
    TooManyOrders,
    #[error("Withdraw amount is zero or negative")]
    WithdrawAmountZeroNeg,
    #[error("Withdraw DDX amount is zero or negative")]
    WithdrawDDXAmountZeroNeg,
    #[error("Withdraw insurance fund amount is zero or negative")]
    WithdrawInsuranceFundZeroNeg,
    #[error("Access denied")]
    AccessDenied,
    #[error("Unexpected error: {}", _0)]
    Unexpected(String),
}

impl SafetyFailure {
    pub fn name(&self) -> String {
        format!("{:?}", self)
            .chars()
            .take_while(|c| c.is_alphabetic())
            .collect::<String>()
    }
}

impl From<anyhow::Error> for SafetyFailure {
    fn from(err: anyhow::Error) -> Self {
        SafetyFailure::Unexpected(format!("{}", err))
    }
}

impl From<DDXCommonError> for SafetyFailure {
    fn from(err: DDXCommonError) -> Self {
        SafetyFailure::Unexpected(format!("{}", err))
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Deserialize, Serialize, Eq)]
pub enum MaxInsuranceFundWithdrawBreachedReason {
    TooLittleRemaining,
    InsufficientContribution,
}

#[derive(thiserror::Error, Debug)]
pub enum ValidationError {
    #[error("Order Rejection: {0}")]
    OrderRejection(OrderRejection),
}

/// The result of a transaction execution including possible recoverable errors
///
/// Execution is a multi step process, this delivers a `PostProcessingRequest` containing
/// the inputs for commitment in untrusted context.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ExecutionOutcome {
    Success(ExecutionOps),
    Skip(String),
}

impl From<anyhow::Error> for ExecutionOutcome {
    fn from(e: anyhow::Error) -> Self {
        let mut msg = e.root_cause().to_string();
        msg.truncate(EXEC_OUTCOME_MSG_MAX_SIZE);
        ExecutionOutcome::Skip(msg)
    }
}

impl TryFrom<ExecutionOutcome> for anyhow::Error {
    type Error = anyhow::Error;

    fn try_from(value: ExecutionOutcome) -> Result<Self, Self::Error> {
        match value {
            ExecutionOutcome::Skip(inner) => Ok(anyhow::anyhow!(inner)),
            ExecutionOutcome::Success(_) => Err(anyhow::anyhow!(
                "Trying to convert ExecutionOutcome::Success into ExecutionError"
            )),
        }
    }
}

#[cfg(test)]
pub mod tests {
    use crate::{ExecutionOutcome, types::transaction::ExecutionOps};
    use anyhow::Error;
    use core::convert::TryInto;

    #[test]
    fn try_from_execution_error_to_outcome() {
        let msg = "A".to_string();
        let error: Error = ExecutionOutcome::Skip(msg.clone()).try_into().unwrap();
        assert_eq!(error.to_string(), msg);
    }

    #[test]
    #[should_panic]
    fn try_from_execution_error_to_outcome_panics() {
        let _x: Error = ExecutionOutcome::Success(ExecutionOps::NonStateTransitioning(Vec::new()))
            .try_into()
            .unwrap();
    }
}
