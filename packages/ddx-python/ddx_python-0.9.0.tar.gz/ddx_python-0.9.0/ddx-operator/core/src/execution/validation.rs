#![allow(non_snake_case)]
use crate::{
    constants::IMF_FACTOR,
    types::{
        accounting::{MMR_FRACTION, Position, PositionSide, PriceDirection, StrategyMetrics},
        primitives::ProductSymbol,
    },
};
use core_common::types::primitives::{OrderSide, UnscaledI128};
use rust_decimal::{
    Decimal, RoundingStrategy,
    prelude::{FromPrimitive, One, ToPrimitive, Zero},
};
use serde::Serialize;
use std::{cmp::min, collections::HashSet, fmt, ops::Neg, vec::Vec};

/// Currently, any score greater than zero is in-the-money
pub type SolvencyScore = u8;

type MarkPrice = Decimal;

pub trait ProductStore: fmt::Debug {
    fn mark_price(&self, symbol: &ProductSymbol) -> Decimal;

    fn direction(&self, symbol: &ProductSymbol) -> PriceDirection;

    fn mark_price_detail(&self, symbol: &ProductSymbol) -> (Decimal, PriceDirection);

    fn listed_symbols(&self) -> Vec<ProductSymbol>;

    fn tradable_symbols(&self) -> Vec<ProductSymbol>;
}

/// Accounting metrics for account/position with valued in the default currency
pub trait Valuation {
    /// PNL of the position(s) held
    fn unrealized_pnl(&self) -> Decimal;

    /// Collateral value plus unrealized PNL
    fn total_value(&self) -> Decimal;
}

/// Thin wrapper around strategy and market metrics in storage
///
/// Performs accounting functions without destructuring the metrics borrowed from the state.
/// Intended for performance, not ergonomics, this holds only two references and avoids copying where possible.
// TODO: We may want to implement the same methods on AccountContext, which is more ergonomic for general usage.
#[derive(Debug)]
pub struct AccountMetrics<'a> {
    pub strategy: &'a StrategyMetrics,
    /// Reference to the current product mapping.
    ///
    /// The client must ensure that the mark price covers all the position, or risk a panic.
    pub products: &'a dyn ProductStore,
}

impl<'a> AccountMetrics<'a> {
    pub fn new(sm: &'a StrategyMetrics, products: &'a dyn ProductStore) -> Self {
        debug_assert!(
            sm.positions
                .keys()
                .cloned()
                .collect::<HashSet<_>>()
                .is_subset(&products.tradable_symbols().into_iter().collect()),
            "Missing mark prices"
        );
        AccountMetrics {
            strategy: sm,
            products,
        }
    }

    /// Check if the account is solvent.
    pub fn assess_solvency(&self) -> (Decimal, Decimal, SolvencyScore) {
        let mf = self.margin_fraction();
        let mmr = self.maintenance_margin_requirements();
        if mf < mmr { (mf, mmr, 0) } else { (mf, mmr, 1) }
    }

    fn margin_fraction(&self) -> Decimal {
        let total_value = self.total_value();
        let notional_value = self.notional_value();
        if notional_value == Decimal::zero() {
            // If the total value is negative, this indicates that the account
            // is irredeemably insolvent (there are no positions that could
            // improve the account's solvency).
            if total_value.is_sign_negative() {
                // TODO: Is this the min/max range we want to use? Seems like a hazard for overflow.
                return Decimal::MIN;
            }
            // If the total value is positive, the account has effectively
            // infinite solvency since there are no positions that could
            // jeopardize the account's solvency.
            return Decimal::MAX;
        }
        total_value / notional_value
    }

    /// The notional value (theoretical value of the underlying) for the account/position
    pub fn notional_value(&self) -> Decimal {
        self.strategy
            .positions
            .iter()
            .map(|(s, p)| *p.balance * self.products.mark_price(s))
            .sum::<Decimal>()
    }

    fn maintenance_margin_requirements(&self) -> Decimal {
        *MMR_FRACTION / Decimal::from(self.strategy.max_leverage)
    }

    /// Calculate the account's maintenance margin requirement using
    /// strict standards.
    fn strict_maintenance_margin_requirements(&self) -> Decimal {
        Decimal::one() / Decimal::from(self.strategy.max_leverage)
    }

    /// Calculate the maximum amount that can be withdrawn given the
    /// constraint of solvency.
    pub fn maximum_withdrawal_amount(&self) -> Decimal {
        // We have that the margin fraction after withdrawal is given by:
        //
        //                 mf(a') = (T(a) - δ) / N(a)
        //
        // Setting this equal to γ (our strict solvency requirements) allows us
        // to calculate the maximum allowed withdrawal δ:
        //
        //                  γ = (T(a) - δ) / N(a)
        //
        //                           =>
        //
        //                     δ = T(a) - γN(a)
        //
        // If the margin fraction was previously less than or equal to the
        // strict solvency requirements, the maximum withdrawal amount will be
        // non-positive:
        //
        //                     T(a) / N(a) ≤ γ
        //
        //                           =>
        //
        //                   δ = T(a) - γN(a) ≤ 0
        //
        // If a given withdrawal amount is greater than the calculated δ then
        // we consider this a skippable error and continue.
        self.total_value() - self.strict_maintenance_margin_requirements() * self.notional_value()
    }

    /// Calculate the total base value of collateral in the account
    pub fn margin_value(&self) -> Decimal {
        *self.strategy.margin
    }

    /// Compute the maximum amount that the account's position can be increased.
    ///
    /// ## Notation
    ///
    /// π:    The mark price.
    ///
    /// ψ:    The order price.
    ///
    /// φ:    The fee percentage.
    ///
    /// a:    The account that is being used to compute solvency.
    ///
    /// p_s:  The position for symbol s.
    ///
    /// s(p): The side number of a position. s(p) = 1 if p is long and s(p) = -1
    ///       if p is short.
    ///
    /// N(a): The notional value of account a.
    ///
    /// T(a): The total value of account a.
    fn maximum_fill_amount_increasing(
        &self,
        fee_percentage: Decimal,
        mark_price: Decimal,
        side: OrderSide,
        price: Decimal,
        amount: Decimal,
    ) -> Decimal {
        // If collateral and notional are both 0 (i.e., the strategy is
        // empty in a scenario such as right after a liquidation),
        // no amount should be executed, so we can short-circuit.
        if self.margin_value() == Decimal::zero() && self.notional_value() == Decimal::zero() {
            return Decimal::zero();
        }

        // If the order side is a bid, the position side must be long since we
        // are increasing the position. Similarly, if the the order side is an
        // ask, the position side is short.
        let side = match side {
            OrderSide::Bid => Decimal::one(),
            OrderSide::Ask => Decimal::one().neg(),
        };
        // We define gamma to be 1/max_leverage for convenience in the ensuing
        // calculations.
        let gamma = Decimal::one() / Decimal::from(self.strategy.max_leverage);
        let theoretical_fill_amount = if self.margin_fraction() <= gamma {
            // Since the margin fraction of the account a is less than our
            // strict solvency standards in this case, we need to prevent the
            // margin fraction from decreasing further in this fill. A lower
            // margin fraction represents a risk to the exchange as well as to
            // the trader since it increases the likelihood of liquidations as
            // well as the likelihood that a liquidation will have a negative
            // liquidation spread. With this in mind, we should only allow the
            // order to be filled if the fill increases the trader's solvency.
            //
            // The question of whether or not the margin fraction is increasing
            // as a function of the fill amount can be studied by analyzing the
            // derivative of a modified margin fraction function. Consider the
            // margin fraction of a' (a updated by filling x amount of an order),
            // which can be written as:
            //
            // mf(a') = (T(a) + s(p_s) * (π - ψ) * x - φ * ψ * x) / (N(a) + π * x).
            //
            // The most direct way to evaluate whether or not this function is
            // increasing or decreasing is to compute the derivative. The
            // derivative mf(a')' (calculated using the quotient rule of
            // derivatives) is:
            //
            // mf(a')' = (N(a) * (s(p_s) * (π - ψ) - φ * ψ) - π * T(a)) / (N(a) + π * x)^2.
            //
            // This function has a pole at x = -N(a)/π. Since mf(a) < gamma, we
            // know that N(a) > 0, so this pole lies at a negative `x` value and
            // can be disregarded for this analysis. The denominator (N(a) + π * x)^2
            // will always be positive since it's a square, so we know that the
            // derivative is positive for all x >= 0 (meaning that the function
            // is monotonically increasing) when the numerator is positive. We
            // can express this as:
            //
            // N(a) * (s(p_s) * (π - ψ) - φ * ψ) - π * T(a) > 0.
            //
            // If we find that the above expression is true, the account's
            // solvency will increase as x increases and the maximum fill amount
            // should be the order amount. Otherwise, the account's solvency
            // will decrease as x increases and the maximum fill amount should
            // be zero.
            let derivative_numerator = self.notional_value()
                * (side * (mark_price - price) - fee_percentage * price)
                - mark_price * self.total_value();
            if derivative_numerator.is_sign_negative() {
                Decimal::zero()
            } else {
                Decimal::MAX
            }
        } else {
            // Since the margin fraction of account a is greater than gamma in
            // this case, some of the order can always be filled. We must
            // determine the maximum fill amount that still satisfies
            // mf(a') >= gamma, where a' is account a updated by filling x
            // amount of an order. We can write the margin fraction of a' as:
            //
            // mf(a') = (T(a) + s(p_s) * (π - ψ) * x - φ * ψ * x) / (N(a) + π * x).
            //
            // We can find the maximum fill amount x by setting mf(a') equal to
            // gamma and solving algebraically for the fill amount. This results
            // in the following formula:
            //
            // x = (T(a) - gamma * N(a)) / (s(p_s) * (ψ - π) + φ * ψ + gamma * π).
            //
            // Since mf(a) > gamma in this case, we have that T(a) > gamma * N(a),
            // so the numerator will always be positive. With this said, we need
            // to evaluate the denominator to determine how to interpret the
            // value of x. There are three cases:
            //
            //   1. If the denominator is positive, then x will be a positive
            //      value that will define the maximum fill amount.
            //   2. If the denominator is zero, the margin fraction functions
            //      asymptote lies at gamma and the the maximum fill amount is
            //      not constrained by solvency.
            //   3. If the denominator is negative, there are two cases to
            //      evaluate. In the case that the derivative is negative, and
            //      the negative result indicates that the horizontal asymptote
            //      lies above gamma. In the other case, we note that the margin
            //      fraction is greater than or equal to gamma at zero, so the
            //      non-negative derivative indicates that the margin fraction
            //      function never intersects with gamma in when x is greater
            //      than or equal to zero. In either case, the maximum fill
            //      amount is unconstrained by solvency.
            let denominator =
                side * (price - mark_price) + fee_percentage * price + gamma * mark_price;
            if denominator > Decimal::ZERO {
                (self.total_value() - gamma * self.notional_value()) / denominator
            } else {
                Decimal::MAX
            }
        };
        // The maximum increase amount is the minimum of the maximum amount the
        // position can be decreased without becoming insolvent by strict
        // standards and the order amount.
        theoretical_fill_amount.min(amount)
    }

    /// Compute the maximum amount that the account's position can be decreased.
    ///
    /// ## Notation
    ///
    /// π:    The mark price.
    ///
    /// ψ:    The order price.
    ///
    /// φ:    The fee percentage.
    ///
    /// a:    The account that is being used to compute solvency.
    ///
    /// p_s:  The position for symbol s.
    ///
    /// s(p): The side number of a position. s(p) = 1 if p is long and s(p) = -1
    ///       if p is short.
    ///
    /// N(a): The notional value of account a.
    ///
    /// T(a): The total value of account a.
    fn maximum_fill_amount_decreasing(
        &self,
        fee_percentage: Decimal,
        mark_price: Decimal,
        position: &Position,
        side: OrderSide,
        price: Decimal,
        amount: Decimal,
    ) -> Decimal {
        // If the order side is a bid, the position side must be short since we
        // are decreasing the position. Similarly, if the the order side is an
        // ask, the position side is long.
        let side = match side {
            OrderSide::Bid => Decimal::one().neg(),
            OrderSide::Ask => Decimal::one(),
        };
        // We define gamma to be 1/max_leverage for convenience in the ensuing
        // calculations.
        let gamma = Decimal::one() / Decimal::from(self.strategy.max_leverage);
        let theoretical_fill_amount = if self.margin_fraction() <= gamma {
            // Since the margin fraction of the account a is less than our
            // strict solvency standards in this case, we need to prevent the
            // margin fraction from decreasing further in this fill. A lower
            // margin fraction represents a risk to the exchange as well as to
            // the trader since it increases the likelihood of liquidations as
            // well as the likelihood that a liquidation will have a negative
            // liquidation spread. With this in mind, we should only allow the
            // order to be filled if the fill increases the trader's solvency.
            //
            // The question of whether or not the margin fraction is increasing
            // as a function of the fill amount can be studied by analyzing the
            // derivative of a modified margin fraction function. Consider the
            // margin fraction of a' (a updated by filling x amount of an order),
            // which can be written as:
            //
            // mf(a') = (T(a) + s(p_s) * (ψ - π) * x - φ * ψ * x) / (N(a) - π * x).
            //
            // The most direct way to evaluate whether or not this function is
            // increasing or decreasing is to compute the derivative. The
            // derivative mf(a')' (calculated using the quotient rule of
            // derivatives) is:
            //
            // mf(a')' = (N(a) * (s(p_s) * (ψ - π) - φ * ψ) + π * T(a)) / (N(a) - π * x)^2.
            //
            // This function has a pole at x = N(a)/π, and we know that N(a) > 0
            // since the margin fraction is less than 1/20. Since this pole is
            // greater than zero, we can calculate the derivative of the
            // function at zero, which allows us to determine whether or not
            // some of the order should be filled. The denominator (N(a) - π * x)^2
            // will always be positive since it's a square, so we know that the
            // derivative is positive for all x >= 0 (meaning that the function
            // is monotonically increasing) when the numerator is positive. We
            // can express this as:
            //
            // N(a) * (s(p_s) * (ψ - π) - φ * ψ) + π * T(a) > 0.
            //
            // If we find that the above expression is true, the account's
            // solvency will increase as x increases and the maximum fill amount
            // should be the minimum of the order amount and the position
            // balance. Otherwise, the account's solvency will decrease as x
            // increases and the maximum fill amount should be zero.
            let derivative_numerator = self.notional_value()
                * (side * (price - mark_price) - fee_percentage * price)
                + mark_price * self.total_value();
            if derivative_numerator.is_sign_negative() {
                Decimal::zero()
            } else {
                Decimal::MAX
            }
        } else {
            // Since the margin fraction of account a is greater than gamma in
            // this case, some of the order can always be filled. We must
            // determine the maximum fill amount that still satisfies
            // mf(a') >= gamma, where a' is account a updated by filling x
            // amount of an order. We can write the margin fraction of a' as:
            //
            // mf(a') = (T(a) + s(p_s) * (ψ - π) * x - φ * ψ * x) / (N(a) - π * x).
            //
            // We can find the maximum fill amount x by setting mf(a') equal to
            // gamma and solving algebraically for the fill amount. This results
            // in the following formula:
            //
            // x = (T(a) - gamma * N(a)) / (s(p_s) * (π - ψ) + φ * ψ - gamma * π).
            //
            // Since mf(a) > gamma in this case, we have that T(a) > gamma * N(a),
            // so the numerator will always be positive. With this said, we need
            // to evaluate the denominator to determine how to interpret the
            // value of x. There are three cases:
            //
            //   1. If the denominator is positive, then x will be a positive
            //      value that will define the maximum fill amount.
            //   2. If the denominator is zero, the margin fraction functions
            //      asymptote lies at gamma and the the maximum fill amount is
            //      not constrained by solvency.
            //   3. If the denominator is negative, we must consider if the
            //      derivative is negative or non-negative. If the derivative
            //      is non-negative, then the maximum fill amount is not
            //      constrained by solvency since the margin fraction will
            //      increase as x increases. The case of a negative derivative
            //      is impossible since the denominator is only negative if
            //      we have:
            //
            //      ψ > ((s(p_s) - gamma) / (s(p_s) - φ)) * π.
            //
            //      We also have that if the derivative is negative that:
            //
            //      φ < ((s(p_s) - mf(a)) / (s(p_s) - φ)) * π < ((s(p_s) - gamma) / (s(p_s) - φ)) * π,
            //
            //      which can be seen by solving the inequality mf(a')' < 0
            //      and noting that mf(a) > gamma in this case. This shows that
            //      a negative derivative is impossible, so the fill amount
            //      is never constrained by solvency in this case.
            let denominator =
                side * (mark_price - price) + fee_percentage * price - gamma * mark_price;
            if denominator > Decimal::ZERO {
                (self.total_value() - gamma * self.notional_value()) / denominator
            } else {
                Decimal::MAX
            }
        };
        // The maximum decrease amount is the minimum of the maximum amount
        // the position can be decreased without becoming insolvent by strict
        // standards, the order amount, and the position size.
        theoretical_fill_amount.min(amount).min(*position.balance)
    }

    /// Compute the maximum amount of an order that can be filled in a cross-over.
    /// This function should be used whenever a position is being decreased as
    /// decreasing positions can result in cross-overs if the order amount is
    /// large enough.
    ///
    /// This calculation consists of the following steps:
    /// 1. Calculate the maximum amount that the account's position can be
    ///    decreased.
    /// 2. Check if the maximum amount the position can be decreased is less
    ///    than the position balance. If it is, simply return the decreasing
    ///    amount. Otherwise, proceed to step 3.
    /// 3. Update the account by updating the collateral to reflect the
    ///    realized profit or loss that results from the fill and by removing
    ///    the position that was decreased to have a balance of zero.
    /// 4. Calculate the maximum amount that the account's position can be
    ///    increased.
    /// 5. Return the sum of the decreasing and increasing amounts.
    fn maximum_fill_amount_cross_over(
        &self,
        symbol: ProductSymbol,
        fee_percentage: Decimal,
        mark_price: Decimal,
        position: &Position,
        side: OrderSide,
        price: Decimal,
        amount: Decimal,
    ) -> Decimal {
        // Calculate the maximum amount that the account's position can be
        // decreased without the account becoming insolvent.
        let decreasing_amount = self.maximum_fill_amount_decreasing(
            fee_percentage,
            mark_price,
            position,
            side,
            price,
            amount,
        );
        // If the decreasing amount is equal to the position balance, the fill
        // may cross-over. Otherwise, the maximum decreasing amount is the
        // fill amount.
        let fill_amount = if decreasing_amount == *position.balance {
            // Realize the profit or loss from decreasing the position, debit
            // the fees, and remove the position that was decreased to zero.
            let diff = position.avg_pnl(price) * decreasing_amount
                - fee_percentage * price * decreasing_amount;
            // The amount is calculated with checking. If it is less than zero,
            // The amount will be reset as zero.
            let mut strategy = self.strategy.clone();
            let new_amount = strategy
                .margin
                .checked_add(diff)
                .expect("Account collateral overflow!");
            if new_amount.is_sign_negative() {
                strategy.margin = UnscaledI128::ZERO;
            } else {
                strategy.margin = new_amount.into();
            }
            strategy.positions.retain(|s, _| *s != symbol);
            let account = AccountMetrics::new(&strategy, self.products);
            // Calculate the maximum amount that the position can be increased
            // in the updated account.
            let increasing_amount = account.maximum_fill_amount_increasing(
                fee_percentage,
                mark_price,
                side,
                price,
                amount - decreasing_amount,
            );
            // The maximum fill amount is the sum of the decreasing and
            // increasing amounts.
            decreasing_amount + increasing_amount
        } else {
            decreasing_amount
        };
        fill_amount
    }

    /// Calculate the maximum amount that can be filled given the constraints
    /// of the position size, the order size, and solvency.
    pub fn maximum_fill_amount(
        &self,
        symbol: ProductSymbol,
        fee_percentage: Decimal,
        mark_price: Decimal,
        side: OrderSide,
        price: Decimal,
        amount: Decimal,
        min_order_size: Decimal,
    ) -> Decimal {
        let fill_amount = if let Some(p) = self.strategy.positions.get(&symbol) {
            // Since the account has a position for the given symbol, we
            // need to check whether a fill would increase the current
            // position or decrease it. In the case of a decrease, we need
            // to evaluate the cross-over case.
            // TODO: We should consider removing the side of PositionSide::None;
            // however, this should be fine for now.
            if p.side == PositionSide::Long && side == OrderSide::Bid
                || p.side == PositionSide::Short && side == OrderSide::Ask
                || p.side == PositionSide::None
            {
                self.maximum_fill_amount_increasing(fee_percentage, mark_price, side, price, amount)
            } else {
                self.maximum_fill_amount_cross_over(
                    symbol,
                    fee_percentage,
                    mark_price,
                    p,
                    side,
                    price,
                    amount,
                )
            }
        } else {
            // If the account doesn't have a position for the given symbol,
            // any fill will result in increasing the position's balance in
            // the direction of the order side.
            self.maximum_fill_amount_increasing(fee_percentage, mark_price, side, price, amount)
        };
        // The minimum order size is used to place a lower bound on order
        // amounts placed on the book, and it doubles as a configuration for
        // the maximum amount of precision used in order amounts. The maximum
        // fill amount should respect this configuration since any dust that
        // is left in positions after a fill cannot be closed due to order
        // validation rules.
        if min_order_size.is_zero() {
            fill_amount
        } else {
            fill_amount - (fill_amount % min_order_size)
        }
    }
}

impl Valuation for AccountMetrics<'_> {
    fn unrealized_pnl(&self) -> Decimal {
        self.strategy
            .positions
            .iter()
            .map(|(s, p)| {
                p.side
                    .avg_pnl(*p.avg_entry_price, self.products.mark_price(s))
                    * *p.balance
            })
            .sum::<Decimal>()
    }

    fn total_value(&self) -> Decimal {
        self.margin_value() + self.unrealized_pnl()
    }
}

#[derive(Debug, Clone, Default, Serialize)]
// #[derive(Default, Exported)]
pub struct LiquidityContext {
    // #[exported(constructor, getter)]
    pub symbol: ProductSymbol,
    // #[exported(constructor, getter)]
    pub mark_price: MarkPrice,
    // #[exported(constructor, getter)]
    pub liquidity: Liquidity,
}

#[derive(Debug, Clone, Copy, Default, Serialize)]
// #[derive(Debug, Clone, Copy, Default, Exported)]
pub struct OmfImf {
    // #[exported(constructor, getter)]
    pub omf: Decimal,
    // #[exported(constructor, getter)]
    pub imf: Decimal,
}

/// Bare essential data about an account for key accounting metrics
#[derive(Debug, Clone, Default, Serialize)]
// #[derive(Default, Exported)]
pub struct AccountContext {
    // Use the constructor, getter and/or setter annotation to make a field public in the exported prototype.
    //
    // The macro generates getter/setter implementations, exporting the type according to these rules:
    //
    // 1. Keep primitive exportable types as-is: https://rustwasm.github.io/docs/wasm-bindgen/reference/types.html
    // 2. Convert types that implement `Into<exported::Self>`, deriving `Exported` automatically implements this trait.
    // 3. Convert the inner type of `Vec<Into<exported::Self>>` but generate array accessors instead of regular getter/setter (see examples below).
    //
    // #[exported(constructor, getter)]
    pub margin: Decimal, //<- Implements `Into<exported::Decimal>`
    // Setter and constructor are often inclusive, a setter means intent to mutate the object after initialization.
    // #[exported(constructor, getter, setter)]
    pub max_leverage: u64, //<- Supported primitive type
    // With `Vec<Into<exported::Self>>`, the accessors are:
    // Getter: count_liquidity() and get_liquidity(index) -> Option<T>
    // Setter: push_liquidity(T) and pop_liquidity()-> Option<T>
    // #[exported(setter, getter)]
    pub liquidity: Vec<LiquidityContext>, //<- Implements `Vec<Into<exported::LiquidityContext>>`
}

// #[exported]
impl Valuation for AccountContext {
    /// Total unrealized PNL of all open positions
    fn unrealized_pnl(&self) -> Decimal {
        self.liquidity
            .iter()
            .map(|LiquidityContext { liquidity, .. }| liquidity.unrealized_pnl)
            .sum::<Decimal>()
    }

    /// The total calculated value of all positions in the account
    // #[exported(view)]
    fn total_value(&self) -> Decimal {
        // TODO 1368: Sum of all currencies held as collateral.
        self.margin + self.unrealized_pnl()
    }
}

// TODO: Macro rules generated by hand pending the actual macro. See internal notes.
/// Alternate implementation that wraps the parent instead of converting, potentially simpler and limits copying.
#[cfg(not(target_vendor = "teaclave"))]
pub mod exported {
    use super::*;
    pub mod wasm {
        use super::Valuation;
        use std::convert::TryInto;
        use wasm_bindgen::prelude::*;

        // ##### SIMPLE JSON TYPES #####
        //
        // These types are flagged with `#[exported(json)]` their are deffer to JSON string for conversion.
        //
        // This is meant for simple types like enum values and number, which are intuitively understandable
        // as string by JS programmers.
        //
        // We use JSON because these types implement serde anyway but not always `FromStr`.
        //
        #[wasm_bindgen(inspectable)]
        #[derive(Debug, Clone, Default)]
        pub struct Decimal(super::Decimal);

        #[wasm_bindgen]
        impl Decimal {
            #[wasm_bindgen(constructor)]
            pub fn new(value: String) -> Self {
                Self(serde_json::from_str(format!(r#""{}""#, value).as_str()).unwrap())
            }

            // Js consoles use these two methods to inspect: https://rustwasm.github.io/docs/wasm-bindgen/reference/attributes/on-rust-exports/inspectable.html
            #[wasm_bindgen(js_name = toJSON)]
            pub fn to_json(&self) -> String {
                serde_json::to_string(&self.0).unwrap()
            }

            #[wasm_bindgen(js_name = toString)]
            pub fn to_string_js(&self) -> String {
                // String the double quotes
                self.to_json().replace('"', "")
            }
        }

        // TODO: See if it's possible to convert to JS BigNumber directly instead of String.
        // See: https://rustwasm.github.io/docs/wasm-bindgen/reference/attributes/on-js-imports/js_class.html
        impl From<super::Decimal> for Decimal {
            fn from(v: super::Decimal) -> Self {
                Self(v)
            }
        }

        impl From<Decimal> for super::Decimal {
            fn from(v: Decimal) -> Self {
                v.0
            }
        }

        #[wasm_bindgen(inspectable)]
        #[derive(Debug, Clone, Default)]
        pub struct Symbol(super::ProductSymbol);

        #[wasm_bindgen]
        impl Symbol {
            #[wasm_bindgen(constructor)]
            pub fn new(value: String) -> Self {
                Self(serde_json::from_str(format!(r#""{}""#, value).as_str()).unwrap())
            }

            #[wasm_bindgen(js_name = toJSON)]
            pub fn to_json(&self) -> String {
                serde_json::to_string(&self.0).unwrap()
            }

            #[wasm_bindgen(js_name = toString)]
            pub fn to_string_js(&self) -> String {
                // String the double quotes
                self.to_json().replace('"', "")
            }
        }

        impl From<super::ProductSymbol> for Symbol {
            fn from(v: super::ProductSymbol) -> Self {
                Self(v)
            }
        }

        impl From<Symbol> for super::ProductSymbol {
            fn from(v: Symbol) -> Self {
                v.0
            }
        }

        #[wasm_bindgen(inspectable)]
        #[derive(Debug, Clone, Default)]
        pub struct OrderSide(super::OrderSide);

        #[wasm_bindgen]
        impl OrderSide {
            #[wasm_bindgen(constructor)]
            pub fn new(value: String) -> Self {
                Self(serde_json::from_str(format!(r#""{}""#, value).as_str()).unwrap())
            }

            #[wasm_bindgen(js_name = toJSON)]
            pub fn to_json(&self) -> String {
                serde_json::to_string(&self.0).unwrap()
            }

            #[wasm_bindgen(js_name = toString)]
            pub fn to_string_js(&self) -> String {
                // String the double quotes
                self.to_json().replace('"', "")
            }
        }

        impl From<super::OrderSide> for OrderSide {
            fn from(v: super::OrderSide) -> Self {
                Self(v)
            }
        }

        impl From<OrderSide> for super::OrderSide {
            fn from(v: OrderSide) -> Self {
                v.0
            }
        }

        #[wasm_bindgen(inspectable)]
        #[derive(Debug, Clone, Default)]
        pub struct PositionSide(super::PositionSide);

        #[wasm_bindgen]
        impl PositionSide {
            #[wasm_bindgen(constructor)]
            pub fn new(value: String) -> Self {
                Self(serde_json::from_str(format!(r#""{}""#, value).as_str()).unwrap())
            }

            #[wasm_bindgen(js_name = toJSON)]
            pub fn to_json(&self) -> String {
                serde_json::to_string(&self.0).unwrap()
            }

            #[wasm_bindgen(js_name = toString)]
            pub fn to_string_js(&self) -> String {
                // String the double quotes
                self.to_json().replace('"', "")
            }

            #[wasm_bindgen(js_name = avgPnl)]
            pub fn avg_pnl(&self, avg_entry_price: Decimal, ref_price: Decimal) -> Decimal {
                Into::<super::PositionSide>::into(self.clone())
                    .avg_pnl(avg_entry_price.into(), ref_price.into())
                    .into()
            }

            #[wasm_bindgen(js_name = unrealizedPnl)]
            pub fn unrealized_pnl(
                &self,
                avg_entry_price: Decimal,
                ref_price: Decimal,
                balance: Decimal,
            ) -> Decimal {
                Into::<super::PositionSide>::into(self.clone())
                    .unrealized_pnl(avg_entry_price.into(), ref_price.into(), balance.into())
                    .into()
            }
        }

        impl From<super::PositionSide> for PositionSide {
            fn from(v: super::PositionSide) -> Self {
                Self(v)
            }
        }

        impl From<PositionSide> for super::PositionSide {
            fn from(v: PositionSide) -> Self {
                v.0
            }
        }

        #[wasm_bindgen(inspectable)]
        #[derive(Debug, Clone)]
        pub struct TradeSide(crate::types::accounting::TradeSide);

        #[wasm_bindgen]
        impl TradeSide {
            #[wasm_bindgen(constructor)]
            pub fn new(value: String) -> Self {
                Self(serde_json::from_str(format!(r#""{}""#, value).as_str()).unwrap())
            }

            #[wasm_bindgen(js_name = toJSON)]
            pub fn to_json(&self) -> String {
                serde_json::to_string(&self.0).unwrap()
            }

            #[wasm_bindgen(js_name = toString)]
            pub fn to_string_js(&self) -> String {
                // String the double quotes
                self.to_json().replace('"', "")
            }

            #[wasm_bindgen(js_name = tradingFee)]
            pub fn trading_fee(&self, amount: Decimal, price: Decimal) -> Decimal {
                Into::<crate::types::accounting::TradeSide>::into(self.clone())
                    .trading_fee(amount.into(), price.into())
                    .into()
            }
        }

        impl From<crate::types::accounting::TradeSide> for TradeSide {
            fn from(v: crate::types::accounting::TradeSide) -> Self {
                Self(v)
            }
        }

        impl From<TradeSide> for crate::types::accounting::TradeSide {
            fn from(v: TradeSide) -> Self {
                v.0
            }
        }

        #[wasm_bindgen(inspectable)]
        #[derive(Debug, Clone)]
        pub struct MarkPriceKind(crate::types::accounting::MarkPriceKind);

        #[wasm_bindgen]
        impl MarkPriceKind {
            #[wasm_bindgen(constructor)]
            pub fn new(value: String) -> Self {
                Self(serde_json::from_str(format!(r#""{}""#, value).as_str()).unwrap())
            }

            #[wasm_bindgen(js_name = toJSON)]
            pub fn to_json(&self) -> String {
                serde_json::to_string(&self.0).unwrap()
            }

            #[wasm_bindgen(js_name = toString)]
            pub fn to_string_js(&self) -> String {
                // String the double quotes
                self.to_json().replace('"', "")
            }
        }

        impl From<crate::types::accounting::MarkPriceKind> for MarkPriceKind {
            fn from(v: crate::types::accounting::MarkPriceKind) -> Self {
                Self(v)
            }
        }

        impl From<MarkPriceKind> for crate::types::accounting::MarkPriceKind {
            fn from(v: MarkPriceKind) -> Self {
                v.0
            }
        }
        // ######

        // ###### GENERATED NEWTYPES TO ENCAPSULATE INTERNAL TYPES #####
        // It took me a while to get it, but I believe this is what wasm-bindgen wants us to do.
        // The newType pattern limits the JS concerns to interfaces (getters, setters and public members).
        // With the right getters/setters, the JS object looks as if we redefined the same attributes.
        // See examples here: https://rustwasm.github.io/docs/wasm-bindgen/reference/attributes/on-rust-exports/getter-and-setter.html
        #[wasm_bindgen(inspectable)]
        #[derive(Debug, Clone)]
        pub struct Liquidity(super::Liquidity);

        impl From<super::Liquidity> for Liquidity {
            // The macro simply steps an call `Into` for each field.
            // Its only special processing rules are for containers: `Vec` and `HashMap`.
            fn from(v: super::Liquidity) -> Self {
                Liquidity(v)
            }
        }

        impl From<Liquidity> for super::Liquidity {
            fn from(v: Liquidity) -> Self {
                v.0
            }
        }

        #[wasm_bindgen(inspectable)]
        #[derive(Debug, Clone)]
        pub struct LiquidityContext(super::LiquidityContext);

        impl From<super::LiquidityContext> for LiquidityContext {
            fn from(v: super::LiquidityContext) -> Self {
                LiquidityContext(v)
            }
        }

        impl From<LiquidityContext> for super::LiquidityContext {
            fn from(v: LiquidityContext) -> Self {
                v.0
            }
        }

        #[wasm_bindgen(inspectable)]
        #[derive(Debug, Clone)]
        pub struct AccountContext(super::AccountContext);

        impl From<super::AccountContext> for AccountContext {
            fn from(v: super::AccountContext) -> Self {
                AccountContext(v)
            }
        }

        impl From<AccountContext> for super::AccountContext {
            fn from(v: AccountContext) -> Self {
                v.0
            }
        }

        #[wasm_bindgen(inspectable)]
        #[derive(Debug, Clone)]
        pub struct OmfImf(super::OmfImf);

        impl From<super::OmfImf> for OmfImf {
            fn from(v: super::OmfImf) -> Self {
                OmfImf(v)
            }
        }

        impl From<OmfImf> for super::OmfImf {
            fn from(v: OmfImf) -> Self {
                v.0
            }
        }

        // ##### GENERATED IMPLEMENTATIONS
        //
        // By convention, all Exported types mirror their parent's members and getter/setters according to the rule illustrated here.
        //
        #[wasm_bindgen]
        impl AccountContext {
            // ######### ACCESSORS ##########
            // Always generate this constructor
            // Includes `#[exported(constructor)]` fields, use the Default::default() for others.
            // Implement a separate static method if the parent's constructor includes business rules.
            #[wasm_bindgen(constructor)]
            pub fn new(margin: Decimal, max_leverage: u32) -> Self {
                AccountContext(super::AccountContext {
                    margin: margin.into(),
                    max_leverage: max_leverage.into(),
                    // The macro assumes default for non-constructor values.
                    liquidity: Default::default(),
                })
            }

            #[wasm_bindgen(js_name = toJSON)]
            pub fn to_json(&self) -> String {
                serde_json::to_string(&self.0).unwrap()
            }

            #[wasm_bindgen(js_name = toString)]
            pub fn to_string_js(&self) -> String {
                // String the double quotes
                self.to_json().replace(r#""\""#, "").replace(r#"\"""#, "")
            }

            // ### REGULAR GETTER / SETTER ###
            // These presents the associated fields as attributes of the generated prototype.
            #[wasm_bindgen(getter)]
            pub fn margin(&self) -> Decimal {
                // In wasm-bindgen, getters are supposed to copy (return their field type)
                self.0.margin.into()
            }

            #[wasm_bindgen(getter)]
            #[wasm_bindgen(js_name = maxLeverage)]
            pub fn max_leverage(&self) -> u32 {
                // The clone().into() is redundant here but trying to think like a simple macro.
                self.0.max_leverage.try_into().unwrap()
            }

            #[wasm_bindgen(setter)]
            pub fn set_max_leverage(&mut self, l: u32) {
                self.0.max_leverage = l.into();
            }

            // ### SPECIAL VEC ACCESSORS ###
            // We can't implement regular getters/setters for liquidity because it's not a ffi supported type that fits in contiguous memory.
            // However, our macro does support `Vec<T>` by creating basic accessors assuming that `T` can be exported.
            // If not, it'll simply fail to compile.
            #[wasm_bindgen(js_name = countLiquidity)]
            pub fn count_liquidity(&self) -> usize {
                self.0.liquidity.len()
            }

            #[wasm_bindgen(js_name = getLiquidity)]
            pub fn get_liquidity(&self, index: usize) -> Option<LiquidityContext> {
                // Return a copy of its type like a regular wasm-bindgen getter
                self.0.liquidity.get(index).cloned().map(Into::into)
            }

            #[wasm_bindgen(js_name = pushLiquidity)]
            pub fn push_liquidity(&mut self, l: LiquidityContext) {
                self.0.liquidity.push(l.into());
            }

            #[wasm_bindgen(js_name = popLiquidity)]
            pub fn pop_liquidity(&mut self) -> Option<LiquidityContext> {
                self.0.liquidity.pop().map(Into::into)
            }
            // ###

            // ### GENERATED METHODS ###
            //
            // Non-mutable methods without argument always generated like this.
            #[wasm_bindgen(js_name = marginFraction)]
            pub fn margin_fraction(&self) -> Decimal {
                self.0.margin_fraction().into()
            }

            // Methods with arguments also convert the arguments like so.
            #[wasm_bindgen(js_name = getOmfAndImf)]
            pub fn get_omf_and_imf(&self, symbol: Symbol, side: OrderSide) -> OmfImf {
                self.0.get_omf_and_imf(symbol.into(), side.into()).into()
            }

            #[wasm_bindgen(js_name = notionalValue)]
            pub fn notional_value(&self) -> Decimal {
                self.0.notional_value().into()
            }

            #[wasm_bindgen(js_name = maintenanceMarginRequirements)]
            pub fn maintenance_margin_requirements(&self) -> Decimal {
                self.0.maintenance_margin_requirements().into()
            }

            #[wasm_bindgen(js_name = getWeightedPositionImf)]
            pub fn get_weighted_position_imf(&self) -> Decimal {
                self.0.get_weighted_position_imf().into()
            }

            #[wasm_bindgen(js_name = unrealizedPnl)]
            pub fn unrealized_pnl(&self) -> Decimal {
                self.0.unrealized_pnl().into()
            }

            #[wasm_bindgen(js_name = totalValue)]
            pub fn total_value(&self) -> Decimal {
                self.0.total_value().into()
            }
            // ###
        }

        #[wasm_bindgen]
        impl OmfImf {
            #[wasm_bindgen(js_name = toJSON)]
            pub fn to_json(&self) -> String {
                serde_json::to_string(&self.0).unwrap()
            }

            #[wasm_bindgen(js_name = toString)]
            pub fn to_string_js(&self) -> String {
                // String the double quotes
                self.to_json().replace(r#""\""#, "").replace(r#"\"""#, "")
            }

            #[wasm_bindgen(getter)]
            pub fn omf(&self) -> Decimal {
                // The clone().into() is redundant here but trying to think like a simple macro.
                self.0.omf.into()
            }

            #[wasm_bindgen(getter)]
            pub fn imf(&self) -> Decimal {
                // The clone().into() is redundant here but trying to think like a simple macro.
                self.0.imf.into()
            }
        }

        // ### INCOMPLETE IMPLS, CONSTRUCTORS ONLY ###
        // Only implemented AccountContext for our purpose, the macro will implement the rest.
        // These have constructors so can will be set as per the TS usage example provided.
        #[wasm_bindgen]
        impl Liquidity {
            #[wasm_bindgen(constructor)]
            pub fn new(
                bid_size: Decimal,
                ask_size: Decimal,
                position_side: PositionSide,
                balance: Decimal,
                unrealized_pnl: Decimal,
            ) -> Self {
                Liquidity(super::Liquidity {
                    bid_size: bid_size.into(),
                    ask_size: ask_size.into(),
                    position_side: position_side.into(),
                    balance: balance.into(),
                    unrealized_pnl: unrealized_pnl.into(),
                })
            }

            #[wasm_bindgen(js_name = toJSON)]
            pub fn to_json(&self) -> String {
                serde_json::to_string(&self.0).unwrap()
            }

            #[wasm_bindgen(js_name = toString)]
            pub fn to_string_js(&self) -> String {
                // String the double quotes
                self.to_json().replace(r#""\""#, "").replace(r#"\"""#, "")
            }

            #[wasm_bindgen(getter)]
            #[wasm_bindgen(js_name = bidSize)]
            pub fn bid_size(&self) -> Decimal {
                self.0.bid_size.into()
            }

            #[wasm_bindgen(getter)]
            #[wasm_bindgen(js_name = askSize)]
            pub fn ask_size(&self) -> Decimal {
                self.0.ask_size.into()
            }

            #[wasm_bindgen(getter)]
            #[wasm_bindgen(js_name = positionSide)]
            pub fn position_side(&self) -> PositionSide {
                self.0.position_side.into()
            }

            #[wasm_bindgen(getter)]
            pub fn balance(&self) -> Decimal {
                self.0.balance.into()
            }

            #[wasm_bindgen(getter)]
            #[wasm_bindgen(js_name = unrealizedPnl)]
            pub fn unrealized_pnl(&self) -> Decimal {
                self.0.unrealized_pnl.into()
            }
        }

        #[wasm_bindgen]
        impl LiquidityContext {
            // Always generate this constructor
            // Includes `#[exported(constructor)]` fields, use the Default::default() for others.
            #[wasm_bindgen(constructor)]
            pub fn new(symbol: Symbol, mark_price: Decimal, liquidity: Liquidity) -> Self {
                LiquidityContext(super::LiquidityContext {
                    symbol: symbol.into(),
                    mark_price: mark_price.into(),
                    liquidity: liquidity.into(),
                })
            }

            #[wasm_bindgen(js_name = toJSON)]
            pub fn to_json(&self) -> String {
                serde_json::to_string(&self.0).unwrap()
            }

            #[wasm_bindgen(js_name = toString)]
            pub fn to_string_js(&self) -> String {
                // String the double quotes
                self.to_json().replace(r#""\""#, "").replace(r#"\"""#, "")
            }

            #[wasm_bindgen(getter)]
            pub fn symbol(&self) -> Symbol {
                self.0.symbol.into()
            }

            #[wasm_bindgen(getter)]
            #[wasm_bindgen(js_name = markPrice)]
            pub fn mark_price(&self) -> Decimal {
                self.0.mark_price.into()
            }

            #[wasm_bindgen(getter)]
            pub fn liquidity(&self) -> Liquidity {
                self.0.liquidity.clone().into()
            }
        }
        // ###
    }
}

// #### END GENERATED CODE

// #[exported]
#[cfg(not(target_vendor = "teaclave"))]
impl AccountContext {
    fn margin_fraction(&self) -> Decimal {
        let total_value = self.total_value();
        let notional_value = self.notional_value();
        if notional_value == Decimal::zero() {
            // If the total value is negative, this indicates that the account
            // is irredeemably insolvent (there are no positions that could
            // improve the account's solvency).
            if total_value.is_sign_negative() {
                // TODO: Is this the min/max range we want to use? Seems like a hazard for overflow.
                return Decimal::MIN;
            }
            // If the total value is positive, the account has effectively
            // infinite solvency since there are no positions that could
            // jeopardize the account's solvency.
            return Decimal::MAX;
        }
        total_value / notional_value
    }

    /// The notional value (theoretical value of the underlying) for the account/position
    fn notional_value(&self) -> Decimal {
        self.liquidity
            .iter()
            .map(
                |LiquidityContext {
                     mark_price,
                     liquidity,
                     ..
                 }| liquidity.balance * mark_price,
            )
            .sum::<Decimal>()
    }

    fn maintenance_margin_requirements(&self) -> Decimal {
        *MMR_FRACTION / Decimal::from(self.max_leverage)
    }
}

impl AccountContext {
    // #[exported(view)]
    pub fn get_weighted_position_imf(&self) -> Decimal {
        let imf_factor = Decimal::from_f64(IMF_FACTOR).unwrap();
        let mut weighted_position_imf = Decimal::zero();
        for LiquidityContext {
            mark_price,
            liquidity:
                Liquidity {
                    bid_size,
                    ask_size,
                    position_side,
                    balance,
                    ..
                },
            ..
        } in self.liquidity.iter()
        {
            // Compute the absolute value of the position side if all the bids/asks got filled
            let (total_size_filled_bids, total_size_filled_asks) = match position_side {
                PositionSide::Long => (balance + bid_size, (balance - ask_size).abs()),
                PositionSide::Short => ((balance - bid_size).abs(), balance + ask_size),
                // TODO: How does an empty position fit into this? Assuming long for now.
                PositionSide::None => (balance + bid_size, (balance - ask_size).abs()),
            };
            // Compute position size as absolute value of the above scenarios where all bids or asks are filled
            let position_open_size = total_size_filled_bids.max(total_size_filled_asks);
            // Compute open position notional as the position open size * mark price
            let open_position_notional = position_open_size * mark_price;
            // Exceptionally using floats here because Decimal does not implement square root
            let open_size_sqrt = Decimal::from_f64(
                position_open_size
                    // TODO: Must round to avoid the possibility of overflow. Verify that it's ok.
                    .round_dp_with_strategy(8, RoundingStrategy::ToZero)
                    .to_f64()
                    .unwrap()
                    .sqrt(),
            )
            .unwrap();
            // Position IMF = max(base IMF, IMF Factor * sqrt(position open size))
            let position_imf = (Decimal::one() / Decimal::from(self.max_leverage))
                .max(imf_factor * open_size_sqrt);
            // Increment weighted position IMF weighted by open position notional
            weighted_position_imf += position_imf * open_position_notional;
        }
        weighted_position_imf
    }

    #[tracing::instrument(level = "debug", skip_all, fields(%symbol, ?side, omf, imf))]
    pub fn get_omf_and_imf(&self, symbol: ProductSymbol, side: OrderSide) -> OmfImf {
        let imf_factor = Decimal::from_f64(IMF_FACTOR).unwrap();
        let mut total_open_position_notional = Decimal::zero();
        let mut weighted_position_imf = Decimal::zero();
        for LiquidityContext {
            symbol: symbol_,
            mark_price,
            liquidity:
                Liquidity {
                    bid_size,
                    ask_size,
                    position_side,
                    balance,
                    ..
                },
            ..
        } in self.liquidity.iter()
        {
            // If the order will only decrease the current market's position,
            // we immediately return the order will only improve the trader's
            // exposure in the specified market (solvency guards ensure that the
            // fill won't negatively effect the trader's solvency).
            if symbol_ == &symbol {
                if side == OrderSide::Ask && position_side == &PositionSide::Long {
                    if ask_size <= balance {
                        return Default::default();
                    }
                } else if side == OrderSide::Bid
                    && position_side == &PositionSide::Short
                    && bid_size <= balance
                {
                    return Default::default();
                }
            }
            // Compute the absolute value of the position side if all the bids/asks got filled
            let (total_size_filled_bids, total_size_filled_asks) = match position_side {
                PositionSide::Long => (balance + bid_size, (balance - ask_size).abs()),
                PositionSide::Short => ((balance - bid_size).abs(), balance + ask_size),
                // TODO: How does an empty position fit into this? Assuming long for now.
                PositionSide::None => (balance + bid_size, (balance - ask_size).abs()),
            };
            // Compute position size as absolute value of the above scenarios where all bids or asks are filled
            let position_open_size = total_size_filled_bids.max(total_size_filled_asks);
            // Compute open position notional as the position open size * mark price
            let open_position_notional = position_open_size * mark_price;
            // Increment total open position notional
            total_open_position_notional += open_position_notional;
            // Exceptionally using floats here because Decimal does not implement square root
            let open_size_sqrt = Decimal::from_f64(
                position_open_size
                    // TODO: Must round to avoid the possibility of overflow. Verify that it's ok.
                    .round_dp_with_strategy(8, RoundingStrategy::ToZero)
                    .to_f64()
                    .unwrap()
                    .sqrt(),
            )
            .unwrap();
            tracing::trace!(%symbol_, %self.max_leverage, %imf_factor, %open_size_sqrt, "Calculating position IMF");
            // Position IMF = max(base IMF, IMF Factor * sqrt(position open size))
            let position_imf = (Decimal::one() / Decimal::from(self.max_leverage))
                .max(imf_factor * open_size_sqrt);
            // Increment weighted position IMF weighted by open position notional
            weighted_position_imf += position_imf * open_position_notional;
        }
        tracing::trace!(
            %total_open_position_notional, %weighted_position_imf
        );
        debug_assert!(
            total_open_position_notional > Decimal::zero(),
            "Expected total open position notional to be greater than zero"
        );
        let omf = min(self.total_value(), self.margin) / total_open_position_notional;
        tracing::Span::current().record("omf", format!("{}", omf));
        let imf = weighted_position_imf / total_open_position_notional;
        tracing::Span::current().record("imf", format!("{}", imf));
        OmfImf { omf, imf }
    }
}

#[derive(Debug, Clone, Default, Serialize)]
// #[derive(Debug, Clone, Default, Exported)]
pub struct Liquidity {
    /// Total amount of liquidity in order book
    // #[exported(constructor, getter)]
    pub bid_size: Decimal,
    // #[exported(constructor, getter)]
    pub ask_size: Decimal,
    /// Open position info
    // #[exported(constructor, getter)]
    pub position_side: PositionSide,
    // #[exported(constructor, getter)]
    pub balance: Decimal,
    // #[exported(constructor, getter)]
    pub unrealized_pnl: Decimal,
}

impl Liquidity {
    pub fn is_empty(&self) -> bool {
        debug_assert!(
            !self.balance.is_zero() || self.unrealized_pnl.is_zero(),
            "Unrealized pnl with zero balance"
        );
        self.bid_size.is_zero()
            && self.ask_size.is_zero()
            && self.balance.is_zero()
            && self.unrealized_pnl.is_zero()
    }
}

#[cfg(test)]
pub mod test {
    use super::*;
    use crate::{
        execution::test_utils::{BTCP, DOGEP, ETHP, MarkPriceMap},
        types::primitives::ProductSymbol,
    };
    use core_macros::{dec, unscaled};
    use std::collections::HashMap;
    #[derive(Debug)]
    struct MaximumFillAmountTestCase<'a> {
        account: &'a AccountMetrics<'a>,
        symbol: ProductSymbol,
        mark_price: Decimal,
        price_delta: Decimal,
        fee_percentage: Decimal,
        amount: Decimal,
        min_order_size: Decimal,
    }

    #[derive(Debug, Default)]
    struct MaximumFillAmountTestExpectation {
        bid_amount: Decimal,
        ask_amount: Decimal,
    }

    #[derive(Debug)]
    struct MaximumFillAmountTestFixture<'a> {
        case: MaximumFillAmountTestCase<'a>,
        expected: MaximumFillAmountTestExpectation,
    }

    fn verify_maximum_fill_amount_fixtures(fixtures: Vec<MaximumFillAmountTestFixture>) {
        for fixture in fixtures {
            let actual = fixture.case.account.maximum_fill_amount(
                fixture.case.symbol,
                fixture.case.fee_percentage,
                fixture.case.mark_price,
                OrderSide::Bid,
                fixture.case.mark_price + fixture.case.price_delta,
                fixture.case.amount,
                fixture.case.min_order_size,
            );
            assert!(
                !actual.is_sign_negative(),
                "Actual bid amount is negative for fixture {:#?}",
                fixture
            );
            assert_eq!(
                actual, fixture.expected.bid_amount,
                "Expected bid amount wasn't recovered for fixture {:#?}",
                fixture
            );
            let actual = fixture.case.account.maximum_fill_amount(
                fixture.case.symbol,
                fixture.case.fee_percentage,
                fixture.case.mark_price,
                OrderSide::Ask,
                fixture.case.mark_price - fixture.case.price_delta,
                fixture.case.amount,
                fixture.case.min_order_size,
            );
            assert!(
                !actual.is_sign_negative(),
                "Actual ask amount is negative for fixture {:#?}",
                fixture
            );
            assert_eq!(
                actual, fixture.expected.ask_amount,
                "Expected ask amount wasn't recovered {:#?}",
                fixture
            );
        }
    }

    // TODO: We should add this to the integration test suite.
    //
    // TODO: Remaining test improvements:
    //
    //   1. Use different values of gamma.
    //   2. Add more test cases to get more coverage.
    //   3. Remove the derivations and excessive comments in favor of a
    //      Jupyter notebook that makes the calculations easily
    //      understandable. The math should be fairly easy to parse now
    //      that we effectively prove our approach in the line by line
    //      comments.
    //
    /// # Derivations
    ///
    /// ## Derivation 1
    ///
    /// With a price delta of zero, there will be no additional
    /// unrealized profit or loss taken on when executing the
    /// fill. With this in mind, the constraint on the maximum
    /// fill amount will be the increasing notional value of the
    /// position.
    ///
    /// We can compute the theoretical fill amount with the following
    /// derivation that reasons about the ending total and notional
    /// value of the account:
    ///
    /// gamma <= T(a) / N(a)
    ///   =>
    /// gamma = C(a) - fee_percentage * price * delta  / (mark_price * delta)
    ///   =>
    /// gamma * mark_price * delta + fee_percentage * price * delta = C(a)
    ///   =>
    /// delta = C(a) / (gamma * mark_price + fee_percentage * price)
    ///
    /// ## Derivation 2
    ///
    /// With a positive price delta, the account will be taking on some
    /// unrealized loss when they execute the position. For simplicity,
    /// we only derive the bid case, but the math works out the same
    /// for asks due to symmetry and the difference in the pnl calculations
    /// for asks.
    ///
    /// We can compute the theoretical fill amount with the following
    /// derivation that reasons about the ending total and notional
    /// value of the account:
    ///
    /// gamma <= T(a) / N(a)
    ///   =>
    /// gamma = (C(a) + (mark_price - price) * delta - fee_percentage * price * delta) / (mark_price * delta)
    ///   =>
    /// gamma * mark_price * delta - (mark_price - price) * delta + fee_percentage * price * delta = C(a)
    ///   =>
    /// delta = C(a) / (gamma * mark_price + (price - mark_price) + fee_percentage * price)
    ///
    /// It's possible that the denominator of this expression is negative
    /// or equal to zero since price is an element of [0, ∞). In either
    /// of these cases, the theoretical fill amount (based on solvency
    /// calculations) is ∞ and the fill amount is bounded by the order
    /// amount.
    #[test]
    fn test_maximum_fill_amount_empty_positions() {
        let amount = dec!(1000);
        let mark_price = dec!(10);
        let symbol: ProductSymbol = ETHP.into();
        let mut fixtures = vec![];
        let sm = StrategyMetrics::new(dec!(100), 20u64, HashMap::new());
        let mp = MarkPriceMap(vec![].into_iter().collect());

        // Collateral of 100 and max leverage of 20.
        let account = &AccountMetrics::new(&sm, &mp);
        fixtures.extend(vec![
            // Substituting values into derivation 1:
            //
            // delta = 100 / (10 * 1 / 20) = 200
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: Decimal::zero(),
                    price_delta: Decimal::zero(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(200),
                    ask_amount: dec!(200),
                },
            },
            // Substituting values into derivation 2:
            //
            // delta = 100 / ((1 / 20) * 10 + (10.2 - 10)) = 100 / (1/2 + 1/5) = 1000 / 7
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: Decimal::zero(),
                    price_delta: dec!(0.2),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(1000) / dec!(7),
                    ask_amount: dec!(1000) / dec!(7),
                },
            },
            // Substituting values into derivation 2:
            //
            // delta = 100 / ((1 / 20) * 10 + (9.8 - 10)) = 100 / (1/2 - 1/5) = 1000 / 3
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: Decimal::zero(),
                    price_delta: dec!(0.2).neg(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(1000) / dec!(3),
                    ask_amount: dec!(1000) / dec!(3),
                },
            },
            // Substituting values into derivation 2:
            //
            // delta = 100 / ((1 / 20) * 10 + (15 - 10)) = 100 / (1/2 + 5) = 200 / 11
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: Decimal::zero(),
                    price_delta: dec!(5),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(200) / dec!(11),
                    ask_amount: dec!(200) / dec!(11),
                },
            },
            // Substituting values into derivation 2:
            //
            // delta = 100 / ((1 / 20) * 10 + (9.5 - 10)) = 100 / (1/2 - 1/2) = 100 / 0 = ∞
            //
            // Since the denominator evaluates to 0,  the constraint becomes
            // the order amount since the theoretical fill amount based on
            // solvency calculations is unbounded.
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: Decimal::zero(),
                    price_delta: dec!(0.5).neg(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: amount,
                    ask_amount: amount,
                },
            },
            // Substituting values into derivation 2:
            //
            // delta = 100 / ((1 / 20) * 10 + (5 - 10)) = 100 / (1/2 - 5) = - 200 / 9
            //
            // Since the value of this expression is negative, this indicates
            // that the solvency of this account will approach a value greater
            // than gamma -- 1/20 in this case -- as delta approaches infinity.
            //
            // In this case, the constraint becomes the order amount since the
            // theoretical fill amount based on solvency calculations is
            // unbounded.
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: Decimal::zero(),
                    price_delta: dec!(5).neg(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: amount,
                    ask_amount: amount,
                },
            },
            // Substituting values into derivation 1:
            //
            // delta = 100 / (10 * 1 / 20 + 0.002 * 10) = 100 / (52 / 100) = 10000 / 52
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: Decimal::zero(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(10000) / dec!(52),
                    ask_amount: dec!(10000) / dec!(52),
                },
            },
            // Substituting values into derivation 2 for the bid side:
            //
            // delta = 100 / ((1 / 20) * 10 + (10.2 - 10) + 0.002 * 10.2) = 100 / (1801 / 2500) =
            // 250000 / 1801
            //
            // Substituting values into derivation 2 for the ask side:
            //
            // delta = 100 / ((1 / 20) * 10 + (10 - 9.8) + 0.002 * 9.8) = 100 / (1801 / 2500) =
            // 250000 / 1801
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(0.2),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(250000) / dec!(1801),
                    ask_amount: dec!(250000) / dec!(1799),
                },
            },
            // Substituting values into derivation 2 for the bid side:
            //
            // delta = 100 / ((1 / 20) * 10 + (9.8 - 10) + 0.002 * 9.8) = 100 / (799 / 2500) =
            // 250000 / 799
            //
            // Substituting values into derivation 2 for the ask side:
            //
            // delta = 100 / ((1 / 20) * 10 + (10 - 10.2) + 0.002 * 10.2) = 100 / (799 / 2500) =
            // 250000 / 801
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(0.2).neg(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(250000) / dec!(799),
                    ask_amount: dec!(250000) / dec!(801),
                },
            },
            // Substituting values into derivation 2 for the bid side:
            //
            // delta = 100 / ((1 / 20) * 10 + (15 - 10) + 0.002 * 15) = 100 / (553 / 100) =
            // 10000 / 553
            //
            // Substituting values into derivation 2 for the ask side:
            //
            // delta = 100 / ((1 / 20) * 10 + (10 - 5) + 0.002 * 5) = 100 / (553 / 100) =
            // 10000 / 551
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(5),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(10000) / dec!(553),
                    ask_amount: dec!(10000) / dec!(551),
                },
            },
            // Substituting values into derivation 2:
            //
            // delta = 100 / ((1 / 20) * 10 + (5 - 10) + 0.002 * 5) = 100 / - (449 / 100) =
            // - 10000 / 449.
            //
            // In this case, the constraint becomes the order amount since the
            // theoretical fill amount based on solvency calculations is
            // unbounded.
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(5).neg(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: amount,
                    ask_amount: amount,
                },
            },
        ]);

        // Verify the fixtures.
        verify_maximum_fill_amount_fixtures(fixtures);
    }

    // TODO: We should add this to the integration test suite.
    //
    /// # Methodology
    ///
    /// Since there aren't as many special cases for the case of an account
    /// with non-empty positions, we'll use the standard base equations for
    /// increasing and decreasing cases most of the time.
    ///
    /// The increasing base equation is:
    ///
    /// delta = (T(a) - gamma * N(a)) / (side * (price - mark_price) + fee_percentage * price + gamma * mark_price).
    ///
    /// The decreasing base equation is:
    ///
    /// delta = (T(a) - gamma * N(a)) / (side * (mark_price - price) + fee_percentage * price - gamma * mark_price).
    ///
    /// When the price delta is zero, the denominator is simplified.
    #[test]
    fn test_maximum_fill_amount_nonempty_positions() {
        let amount = dec!(1_000);
        let symbol: ProductSymbol = ETHP.into();
        let mark_prices = MarkPriceMap(
            vec![
                (BTCP.into(), (dec!(50_000), PriceDirection::Unknown)),
                (DOGEP.into(), (dec!(0.15), PriceDirection::Unknown)),
                (ETHP.into(), (dec!(3_000), PriceDirection::Unknown)),
            ]
            .into_iter()
            .collect(),
        );
        let mark_price = mark_prices.mark_price(&symbol);
        let mut fixtures = vec![];

        // TODO: It would be useful to make a note about how to find
        // accounts that are strictly insolvent, exactly strictly solvent,
        // and strictly solvent. This could be useful for fuzzing these
        // cases in the fuzzing framework. The basic gist is that you set
        // up the margin fraction calculation and incrementally define
        // values until you're only solving for a single value. The slightly
        // tricky part is to make sure that you only end up with positive
        // values.
        let sm = StrategyMetrics::new(
            dec!(10_000),
            20u64,
            vec![
                (
                    BTCP.into(),
                    Position {
                        side: PositionSide::Long,
                        balance: unscaled!(0.1),
                        avg_entry_price: unscaled!(100_000),
                    },
                ),
                (
                    DOGEP.into(),
                    Position {
                        side: PositionSide::Short,
                        balance: unscaled!(10_000),
                        avg_entry_price: unscaled!(0.09),
                    },
                ),
                (
                    ETHP.into(),
                    Position {
                        side: PositionSide::Long,
                        balance: unscaled!(2),
                        avg_entry_price: unscaled!(5_000),
                    },
                ),
            ]
            .into_iter()
            .collect(),
        );
        let account = &AccountMetrics::new(&sm, &mark_prices);
        fixtures.extend(vec![
            // Bid:
            //
            // Substituting into the increasing equation gives:
            //
            // delta = (400 - 1/20 * 12,500) / (1 * (3,000 - 3,000) + 0.002 * 3,000 + 1/20 * 3,000) ≈ -1.4423.
            //
            // Since this value is negative and the account is insolvent,
            // this indicates that solvency would not be improved by any
            // incremental fill of this order. The maximum fill amount is zero.
            //
            // Ask:
            //
            // Substituting into the decreasing equation gives:
            //
            // delta = (400 - 1/20 * 12,500) / (1 * (3,000 - 3,000) + 0.002 * 3,000 - 1/20 * 3,000) = 1.5625.
            //
            // Since this delta is positive and the account is currently
            // insolvent, this indicates that the account's solvency will
            // improve the more of the order that is filled. We allow the
            // account to fill the full position balance (since the order
            // amount is much greater than the position balance). Since we
            // fully decrease the position, we must evaluate the cross-over
            // case.
            //
            // The account's total and notional values are updated as follows:
            //
            // C(a) = 10,000 + (3,000 - 5,000) * 2 - 0.002 * 3,000 * 2 = 5,988.
            //
            // U(a) = (50,000 - 100,000) * 0.1 + (0.09 - 0.15) * 10,000 = -5,600.
            //
            // T(a) = 5,988 - 5,600 = 388.
            //
            // N(a) = 12,500 - 3,000 * 2 = 6,500.
            //
            // These updates update the margin fraction. The new margin
            // fraction is 388/6,500 ≈ .0596 > 0.05. This means that the
            // account has become strictly solvent.
            //
            // Substituting into the increasing equation gives:
            //
            // delta = (388 - 1/20 * 6,500) / (-1 * (3,000 - 3,000) + 0.002 * 3,000 + 1/20 * 3,000) ≈ 21/58.
            //
            // Since this delta is positive and the account is strictly solvent,
            // we only fill the given delta on the increasing side.
            //
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: Decimal::zero(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: Decimal::zero(),
                    ask_amount: dec!(2) + dec!(21) / dec!(52),
                },
            },
            // This fixture is identical to the fixture above except for
            // the fact that the order amount is much smaller. The bid
            // amount should still be zero since the account is insolvent.
            // On the other hand, the ask amount should be limited to the
            // order amount, which prevents a cross-over from being evaluated.
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    mark_price,
                    symbol,
                    amount: dec!(1.7),
                    fee_percentage: dec!(0.002),
                    price_delta: Decimal::zero(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: Decimal::zero(),
                    ask_amount: dec!(1.7),
                },
            },
            // Bid:
            //
            // Substituting into the increasing equation gives:
            //
            // delta = (400 - 1/20 * 12,500) / (1 * (3,001 - 3,000) + 0.002 * 3,001 + 1/20 * 3,000) ≈ -1.4331.
            //
            // Since this value is negative and the account is insolvent,
            // this indicates that solvency would not be improved by any
            // incremental fill of this order. The maximum fill amount is zero.
            //
            // Ask:
            //
            // Substituting into the decreasing equation gives:
            //
            // delta = (400 - 1/20 * 12,500) / (1 * (3,000 - 2,999) + 0.002 * 2,999 - 1/20 * 3,000) ≈ 1.5734.
            //
            // Since this delta is positive and the account is currently
            // insolvent, this indicates that the account's solvency will
            // improve the more of the order that is filled. We allow the
            // account to fill the full position balance (since the order
            // amount is much greater than the position balance). Since we
            // fully decrease the position, we must evaluate the cross-over
            // case.
            //
            // The account's total and notional values are updated as follows:
            //
            // C(a) = 10,000 + (2,999 - 5,000) * 2 - 0.002 * 2,999 * 2 = 5,986.004.
            //
            // U(a) = (50,000 - 100,000) * 0.1 + (0.09 - 0.15) * 10,000 = -5,600.
            //
            // T(a) = 5,986.004 - 5,600 = 386.004.
            //
            // N(a) = 12,500 - 3,000 * 2 = 6,500.
            //
            // These updates update the margin fraction. The new margin
            // fraction is 386.004/6,500 ≈ .0593 > 0.05. This means that the
            // account has become strictly solvent.
            //
            // Substituting into the increasing equation gives:
            //
            // delta = (386.004 - 1/20 * 6,500) / (-1 * (2,999 - 3,000) + 0.002 * 2,999 + 1/20 * 3,000) ≈ 30,502/78,499.
            //
            // Since this delta is positive and the account is strictly solvent,
            // we only fill the given delta on the increasing side.
            //
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(1),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: Decimal::zero(),
                    ask_amount: dec!(2) + dec!(30502) / dec!(78499),
                },
            },
            // This fixture is identical to the fixture above except for
            // the fact that the order amount is much smaller. The bid
            // amount should still be zero since the account is insolvent.
            // On the other hand, the ask amount should be limited to the
            // order amount, which prevents a cross-over from being evaluated.
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    mark_price,
                    symbol,
                    amount: dec!(1.7),
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(1),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: Decimal::zero(),
                    ask_amount: dec!(1.7),
                },
            },
            // Bid:
            //
            // Substituting into the increasing equation gives:
            //
            // delta = (400 - 1/20 * 12,500) / (1 * (2,999 - 3,000) + 0.002 * 2,999 + 1/20 * 3,000) ≈ -1.4516.
            //
            // Since this value is negative and the account is insolvent,
            // this indicates that solvency would not be improved by any
            // incremental fill of this order. The maximum fill amount is zero.
            //
            // Ask:
            //
            // Substituting into the decreasing equation gives:
            //
            // delta = (400 - 1/20 * 12,500) / (1 * (3,000 - 3,001) + 0.002 * 3,001 - 1/20 * 3,000) ≈ 1.5517.
            //
            // Since this delta is positive and the account is currently
            // insolvent, this indicates that the account's solvency will
            // improve the more of the order that is filled. We allow the
            // account to fill the full position balance (since the order
            // amount is much greater than the position balance). Since we
            // fully decrease the position, we must evaluate the cross-over
            // case.
            //
            // The account's total and notional values are updated as follows:
            //
            // C(a) = 10,000 + (3,001 - 5,000) * 2 - 0.002 * 3,001 * 2 = 5,989.996.
            //
            // U(a) = (50,000 - 100,000) * 0.1 + (0.09 - 0.15) * 10,000 = -5,600.
            //
            // T(a) = 5,989.996 - 5,600 = 389.996.
            //
            // N(a) = 12,500 - 3,000 * 2 = 6,500.
            //
            // These updates update the margin fraction. The new margin
            // fraction is 389.996/6,500 ≈ .0599 > 0.05. This means that the
            // account has become strictly solvent.
            //
            // Substituting into the increasing equation gives:
            //
            // delta = (389.996 - 1/20 * 6,500) / (-1 * (3,001 - 3,000) + 0.002 * 3,001 + 1/20 * 3,000) ≈ 32,498/77,501.
            //
            // Since this delta is positive and the account is strictly solvent,
            // we only fill the given delta on the increasing side.
            //
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(1).neg(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: Decimal::zero(),
                    ask_amount: dec!(2) + dec!(32498) / dec!(77501),
                },
            },
            // This fixture is identical to the fixture above except for
            // the fact that the order amount is much smaller. The bid
            // amount should still be zero since the account is insolvent.
            // On the other hand, the ask amount should be limited to the
            // order amount, which prevents a cross-over from being evaluated.
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    mark_price,
                    symbol,
                    amount: dec!(1.7),
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(1).neg(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: Decimal::zero(),
                    ask_amount: dec!(1.7),
                },
            },
            // Bid:
            //
            // Substituting into the increasing equation gives:
            //
            // delta = (400 - 1/20 * 12,500) / ((3,200 - 3,000) + 0.002 * 3,200 + 1/20 * 3,000) ≈ -0.6313
            //
            // Since this value is negative and the account is insolvent,
            // this indicates that solvency would not be improved by any
            // incremental fill of this order. The maximum fill amount is zero.
            //
            // Ask:
            //
            // Substituting into the decreasing equation gives:
            //
            // delta = (400 - 1/20 * 12,500) / (1 * (3,000 - 2,800) + 0.002 * 2,800 - 1/20 * 3,000) ≈ -4.0467.
            //
            // Since this value is negative and the account is insolvent,
            // this indicates that solvency would not be improved by any
            // incremental fill of this order. The maximum fill amount is zero.
            //
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(200),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: Decimal::zero(),
                    ask_amount: Decimal::zero(),
                },
            },
            // Bid:
            //
            // Substituting into the increasing equation gives:
            //
            // delta = (400 - 1/20 * 12,500) / (1 * (2,800 - 3,000) + 0.002 * 2,800 + 1/20 * 3,000) ≈ 375/74.
            //
            // Since this delta is positive and the account is currently
            // insolvent, this indicates that the account's solvency will
            // improve the more of the order that is filled. We allow the
            // account to fill the full order.
            //
            // Ask:
            //
            // Substituting into the decreasing equation gives:
            //
            // delta = (400 - 1/20 * 12,500) / (1 * (3,000 - 3,200) + 0.002 * 3,200 - 1/20 * 3,000) ≈ 0.6548.
            //
            // Since this delta is positive and the account is currently
            // insolvent, this indicates that the account's solvency will
            // improve the more of the order that is filled. We allow the
            // account to fill the full position balance (since the order
            // amount is much greater than the position balance). Since we
            // fully decrease the position, we must evaluate the cross-over
            // case.
            //
            // The account's total and notional values are updated as follows:
            //
            // C(a) = 10,000 + (3,200 - 5,000) * 2 - 0.002 * 3,200 * 2 = 6387.2.
            //
            // U(a) = (50,000 - 100,000) * 0.1 + (0.09 - 0.15) * 10,000 = -5,600.
            //
            // T(a) = 6,387.2 - 5,600 = 787.2.
            //
            // N(a) = 12,500 - 3,000 * 2 = 6,500.
            //
            // These updates update the margin fraction. The new margin
            // fraction is 787.2 / 6,500 ≈ .1211 > 0.05. This means that the
            // account has become strictly solvent.
            //
            // Substituting into the increasing equation gives:
            //
            // delta = (787.2 - 1/20 * 6,500) / (-1 * (3,200 - 3,000) + 0.002 * 3,200 + 1/20 * 3,000) ≈ -10.6009.
            //
            // Since this delta is negative and the account is strictly solvent,
            // the full order can be filled.
            //
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(200).neg(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: amount,
                    ask_amount: amount,
                },
            },
            // This fixture is identical to the fixture above except for
            // the fact that the order amount is much smaller. The bid and
            // asks are limited to a much smaller order amount, and this
            // prevents the ask from crossing over.
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    mark_price,
                    symbol,
                    amount: dec!(1.7),
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(200).neg(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(1.7),
                    ask_amount: dec!(1.7),
                },
            },
        ]);

        // Since the margin fraction starts at 1/20 for the account, the
        // heuristic to calculate the maximum fill amount consists of
        // checking if the derivative of the margin fraction with respect
        // to delta is negative at delta = 0. If it is negative, then the
        // theoretical fill amount is zero. Otherwise, the theoretical
        // fill amount is unbounded.
        let sm = StrategyMetrics::new(
            dec!(10_000),
            20u64,
            vec![
                (
                    BTCP.into(),
                    Position {
                        side: PositionSide::Long,
                        balance: unscaled!(0.1),
                        avg_entry_price: unscaled!(100_000),
                    },
                ),
                (
                    DOGEP.into(),
                    Position {
                        side: PositionSide::Short,
                        balance: unscaled!(10_000),
                        avg_entry_price: unscaled!(0.1125),
                    },
                ),
                (
                    ETHP.into(),
                    Position {
                        side: PositionSide::Long,
                        balance: unscaled!(2),
                        avg_entry_price: unscaled!(5_000),
                    },
                ),
            ]
            .into_iter()
            .collect(),
        );
        let account = &AccountMetrics::new(&sm, &mark_prices);
        fixtures.extend(vec![
            // Bid:
            //
            // Substituting into the derivative numerator of the increasing
            // margin fraction gives:
            //
            // derivative_numerator = 12,500 * (1 * (3,000 - 3,000) - 0.002 * 3,000) - 3,000 * 625 = -1,950,000 < 0.
            //
            // From this, the fill amount should be zero.
            //
            // Ask:
            //
            // Substituting into the derivative numerator of the decreasing
            // margin fraction gives:
            //
            // derivative_numerator = 12,500 * (1 * (3,000 - 3,000) - 0.002 * 3,000) + 3,000 * 625 = 1,800,000 > 0.
            //
            // From this, the theoretical fill amount is unbounded. The
            // position balance is only 2, so we must evaluate the cross-over
            // case (since the order amount is much larger than this value).
            //
            // The account is updated as follows:
            //
            // C(a) = 10,000 + (3,000 - 5,000) * 2 - 0.002 * 3,000 * 2 = 5,988
            //
            // U(a) = (50,000 - 100,000) * 0.1 + (0.1125 - 0.15) * 10,000 = -5,375
            //
            // T(a) = 5,988 - 5,375 = 613
            //
            // N(a) = 12,500 - 3,000 * 2 = 6,500
            //
            // The new margin fraction is 613/6,500 = 0.0943 > 0.05, so the
            // account is now strictly solvent and we calculate the maximum
            // increasing amount.
            //
            // Substituting values into the increasing equation gives:
            //
            // delta = (613 - 1/20 * 6,500) / (-1 * (3,000 - 3,000) + 0.002 * 3,000 + 1/20 * 3,000) ≈ 24/13.
            //
            // The decreasing delta is 2 and the increasing delta is 24/13,
            // so the total delta is 2 + 24/13.
            //
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: Decimal::zero(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: Decimal::zero(),
                    ask_amount: dec!(2) + dec!(24) / dec!(13),
                },
            },
            // This fixture is identical to the fixture above except for
            // the fact that the order amount is much smaller. The bid
            // amount should still be zero since the account is insolvent.
            // On the other hand, the ask amount should be limited to the
            // order amount, which prevents a cross-over from being evaluated.
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    mark_price,
                    symbol,
                    amount: dec!(1.7),
                    fee_percentage: dec!(0.002),
                    price_delta: Decimal::zero(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: Decimal::zero(),
                    ask_amount: dec!(1.7),
                },
            },
            // Bid:
            //
            // price = 3,000 + 1 = 3,001
            //
            // Substituting into the derivative numerator of the increasing
            // margin fraction gives:
            //
            // derivative_numerator = 12,500 * (1 * (3,000 - 3,001) - 0.002 * 3,001) - 3,000 * 625 = -1,962,525 < 0.
            //
            // From this, the fill amount should be zero.
            //
            // Ask:
            //
            // price = 3,000 - 1 = 2,999
            //
            // Substituting into the derivative numerator of the decreasing
            // margin fraction gives:
            //
            // derivative_numerator = 12,500 * (1 * (2,999 - 3,000) - 0.002 * 2,999) + 3,000 * 625 = 1,787,525 > 0.
            //
            // From this, the theoretical fill amount is unbounded. The
            // position balance is only 2, so we must evaluate the cross-over
            // case (since the order amount is much larger than this value).
            //
            // The account is updated as follows:
            //
            // C(a) = 10,000 + (2,999 - 5000) * 2 - 0.002 * 2,999 * 2 = 5,986.004
            //
            // U(a) = (50,000 - 100,000) * 0.1 + (0.1125 - 0.15) * 10,000 = -5,375
            //
            // T(a) = 5,986.004 - 5,375 = 611.004
            //
            // N(a) = 12,500 - 3,000 * 2 = 6,500
            //
            // The new margin fraction is 611.004/6,500 = 0.0940 > 0.05, so the
            // account is now strictly solvent and we calculate the maximum
            // increasing amount.
            //
            // Substituting values into the increasing equation gives:
            //
            // delta = (611.004 - 1/20 * 6,500) / (-1 * (2,999 - 3,000) + 0.002 * 2,999 + 1/20 * 3,000) ≈ 143,002/78,499.
            //
            // The decreasing delta is 2 and the increasing delta is 143,002/78,499,
            // so the total delta is 2 + 143,002/78,499.
            //
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(1),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: Decimal::zero(),
                    ask_amount: dec!(2) + dec!(143002) / dec!(78499),
                },
            },
            // This fixture is identical to the fixture above except for
            // the fact that the order amount is much smaller. The bid
            // amount should still be zero since the account is insolvent.
            // On the other hand, the ask amount should be limited to the
            // order amount, which prevents a cross-over from being evaluated.
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    mark_price,
                    symbol,
                    amount: dec!(1.7),
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(1),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: Decimal::zero(),
                    ask_amount: dec!(1.7),
                },
            },
            // Bid:
            //
            // price = 3,000 + (-1) = 2,999
            //
            // Substituting into the derivative numerator of the increasing
            // margin fraction gives:
            //
            // derivative_numerator = 12,500 * (1 * (3,000 - 2,999) - 0.002 * 3,001) - 3,000 * 625 = -1,937,525 < 0.
            //
            // From this, the fill amount should be zero.
            //
            // Ask:
            //
            // price = 3,000 - (-1) = 3,001
            //
            // Substituting into the derivative numerator of the decreasing
            // margin fraction gives:
            //
            // derivative_numerator = 12,500 * (1 * (3,001 - 3,000) - 0.002 * 3,001) + 3,000 * 625 = 1,812,475 > 0.
            //
            // From this, the theoretical fill amount is unbounded. The
            // position balance is only 2, so we must evaluate the cross-over
            // case (since the order amount is much larger than this value).
            //
            // The account is updated as follows:
            //
            // C(a) = 10,000 + (3,001 - 5000) * 2 - 0.002 * 3,001 * 2 = 5,989.996
            //
            // U(a) = (50,000 - 100,000) * 0.1 + (0.1125 - 0.15) * 10,000 = -5,375
            //
            // T(a) = 5,989.996 - 5,375 = 614.996
            //
            // N(a) = 12,500 - 3,000 * 2 = 6,500
            //
            // The new margin fraction is 614.996/6,500 = 0.0946 > 0.05, so the
            // account is now strictly solvent and we calculate the maximum
            // increasing amount.
            //
            // Substituting values into the increasing equation gives:
            //
            // delta = (614.996 - 1/20 * 6,500) / (-1 * (3,001 - 3,000) + 0.002 * 3,001 + 1/20 * 3,000) ≈ 144,998/77,501.
            //
            // The decreasing delta is 2 and the increasing delta is 144,998/77,501,
            // so the total delta is 2 + 144,998/77,501.
            //
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(1).neg(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: Decimal::zero(),
                    ask_amount: dec!(2) + dec!(144998) / dec!(77501),
                },
            },
            // This fixture is identical to the fixture above except for
            // the fact that the order amount is much smaller. The bid
            // amount should still be zero since the account is insolvent.
            // On the other hand, the ask amount should be limited to the
            // order amount, which prevents a cross-over from being evaluated.
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    mark_price,
                    symbol,
                    amount: dec!(1.7),
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(1).neg(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: Decimal::zero(),
                    ask_amount: dec!(1.7),
                },
            },
            // Bid:
            //
            // price = 3,000 + 200 = 3,200
            //
            // Substituting into the derivative numerator of the increasing
            // margin fraction gives:
            //
            // derivative_numerator = 12,500 * (1 * (3,000 - 3,200) - 0.002 * 3,200) - 3,000 * 625 = -4,455,000 < 0.
            //
            // From this, the fill amount should be zero.
            //
            // Ask:
            //
            // price = 3,000 - 200 = 2,800
            //
            // Substituting into the derivative numerator of the decreasing
            // margin fraction gives:
            //
            // derivative_numerator = 12,500 * (1 * (2,800 - 3,000) - 0.002 * 2,800) + 3,000 * 625 = -695,000 < 0.
            //
            // From this, the fill amount should be zero.
            //
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(200),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: Decimal::zero(),
                    ask_amount: Decimal::zero(),
                },
            },
            // Bid:
            //
            // price = 3,000 + (-200) = 2,800
            //
            // Substituting into the derivative numerator of the increasing
            // margin fraction gives:
            //
            // derivative_numerator = 12,500 * (1 * (3,000 - 2,800) - 0.002 * 2,800) - 3,000 * 625 = 555,000 > 0.
            //
            // From this, the theoretical fill amount is unbounded.
            //
            // Ask:
            //
            // price = 3,000 - (-200) = 3,200
            //
            // Substituting into the derivative numerator of the decreasing
            // margin fraction gives:
            //
            // derivative_numerator = 12,500 * (1 * (3,200 - 3,000) - 0.002 * 3,200) + 3,000 * 625 = 4,295,000 > 0.
            //
            // From this, the theoretical fill amount is unbounded. The
            // position balance is only 2, so we must evaluate the cross-over
            // case (since the order amount is much larger than this value).
            //
            // The account is updated as follows:
            //
            // C(a) = 10,000 + (3,200 - 5000) * 2 - 0.002 * 3,200 * 2 = 6,387.2
            //
            // U(a) = (50,000 - 100,000) * 0.1 + (0.1125 - 0.15) * 10,000 = -5,375
            //
            // T(a) = 6,387.2 - 5,375 = 1,012.2
            //
            // N(a) = 12,500 - 3,000 * 2 = 6,500
            //
            // The new margin fraction is 1,012.2/6,500 = 0.1557 > 0.05, so the
            // account is now strictly solvent and we calculate the maximum
            // increasing amount.
            //
            // Substituting values into the increasing equation gives:
            //
            // delta = (1012.2 - 1/20 * 6,500) / (-1 * (3,200 - 3,000) + 0.002 * 3,200 + 1/20 * 3,000) ≈ -15.7614.
            //
            // Since this value is negative and the account is strictly solvent,
            // the theoretical fill amount is unbounded.
            //
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(200).neg(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: amount,
                    ask_amount: amount,
                },
            },
            // This fixture is identical to the fixture above except for
            // the fact that the order amount is much smaller. The bid and
            // asks are limited to a much smaller order amount, and this
            // prevents the ask from crossing over.
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    mark_price,
                    symbol,
                    amount: dec!(1.7),
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(200).neg(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(1.7),
                    ask_amount: dec!(1.7),
                },
            },
        ]);

        // This account is more than strictly solvent. This means that we
        // need to solve the margin fraction equations to find the maximum
        // fill amount.
        let sm = StrategyMetrics::new(
            dec!(10_000),
            20u64,
            vec![
                (
                    BTCP.into(),
                    Position {
                        side: PositionSide::Long,
                        balance: unscaled!(0.1),
                        avg_entry_price: unscaled!(100_000),
                    },
                ),
                (
                    DOGEP.into(),
                    Position {
                        side: PositionSide::Short,
                        balance: unscaled!(10_000),
                        avg_entry_price: unscaled!(1),
                    },
                ),
                (
                    ETHP.into(),
                    Position {
                        side: PositionSide::Long,
                        balance: unscaled!(2),
                        avg_entry_price: unscaled!(5_000),
                    },
                ),
            ]
            .into_iter()
            .collect(),
        );
        let account = &AccountMetrics::new(&sm, &mark_prices);
        fixtures.extend(vec![
            // Bid:
            //
            // price = 3,000
            //
            // Substituting into the increasing equation gives:
            //
            // delta = (9,500 - 1/20 * 12,500) / (1 * (3,000 - 3,000) + 0.002 * 3,000 + 1/20 * 3,000) = 56 + 139/156
            //
            // Since delta is positive, this delta is the theoretical fill amount.
            //
            // Ask:
            //
            // price = 3,000
            //
            // Substituting into the decreasing equation gives:
            //
            // delta = (9,500 - 1/20 * 12,500) / (1 * (3,000 - 3,000) + 0.002 * 3,000 - 1/20 * 3,000) = -61.6319.
            //
            // Since delta is negative and the account is strictly solvent,
            // we can maximally decrease the position. Since the position
            // will be fully decreased, we must evaluate the cross-over.
            //
            // The account will be updated as follows:
            //
            // C(a) = 10,000 + (3,000 - 5,000) * 2 - 0.002 * 3,000 * 2 = 5,988
            //
            // U(a) = (50,000 - 100,000) * 0.1 + (1 - 0.15) * 10,000 = 3,500
            //
            // T(a) = 5,988 + 3,500 = 9,488
            //
            // N(a) = 12,500 - 3,000 * 2 = 6,500
            //
            // The margin fraction is 9,488/6,500 ≈ 1.4596 > 0.05 so the account
            // remains strictly solvent.
            //
            // Substituting into the increasing equation gives:
            //
            // delta = (9,488 - 1/20 * 6,500) / (-1 * (3,000 - 3,000) + 0.002 * 3,000 + 1/20 * 3,000) = 58 + 115/156.
            //
            // The decreasing delta is 2 and the increasing delta is 58 + 115/156,
            // so the total delta is 60 + 115/156.
            //
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: Decimal::zero(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(56) + dec!(139) / dec!(156),
                    ask_amount: dec!(60) + dec!(115) / dec!(156),
                },
            },
            // This fixture is identical to the fixture above except for
            // the fact that the minimum order size is set.
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: Decimal::zero(),
                    min_order_size: dec!(10),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(50),
                    ask_amount: dec!(60),
                },
            },
            // This fixture is identical to the fixture above except for
            // the fact that the order amount is much smaller. The bid and
            // asks are limited to a much smaller order amount, and this
            // prevents the ask from crossing over.
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    mark_price,
                    symbol,
                    amount: dec!(1.7),
                    fee_percentage: dec!(0.002),
                    price_delta: Decimal::zero(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(1.7),
                    ask_amount: dec!(1.7),
                },
            },
            // Bid:
            //
            // price = 3,000 + 1 = 3,001
            //
            // Substituting into the increasing equation gives:
            //
            // delta = (9,500 - 1/20 * 12,500) / (1 * (3,001 - 3,000) + 0.002 * 3,001 + 1/20 * 3,000) = 56 + 41,444/78,501
            //
            // Since delta is positive, this delta is the theoretical fill amount.
            //
            // Ask:
            //
            // price = 3,000 - 1 = 2,999
            //
            // Substituting into the decreasing equation gives:
            //
            // delta = (9,500 - 1/20 * 12,500) / (1 * (3,000 - 2,999) + 0.002 * 2,999 - 1/20 * 3,000) ≈ -62.0620.
            //
            // Since delta is negative and the account is strictly solvent,
            // we can maximally decrease the position. Since the position
            // will be fully decreased, we must evaluate the cross-over.
            //
            // The account will be updated as follows:
            //
            // C(a) = 10,000 + (2,999 - 5,000) * 2 - 0.002 * 2,999 * 2 = 5,986.004
            //
            // U(a) = (50,000 - 100,000) * 0.1 + (1 - 0.15) * 10,000 = 3,500
            //
            // T(a) = 5,986.004 + 3,500 = 9,486.004
            //
            // N(a) = 12,500 - 3,000 * 2 = 6,500
            //
            // The margin fraction is 9,486.004/6,500 ≈ 1.4593 > 0.05 so the account
            // remains strictly solvent.
            //
            // Substituting into the increasing equation gives:
            //
            // delta = (9,486.004 - 1/20 * 6,500) / (-1 * (2,999 - 3,000) + 0.002 * 2,999 + 1/20 * 3,000) = 58 + 27,560/78,499.
            //
            // The decreasing delta is 2 and the increasing delta is 58 + 27,560/78,499,
            // so the total delta is 60 + 27,560/78,499.
            //
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(1),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(56) + dec!(41444) / dec!(78501),
                    ask_amount: dec!(60) + dec!(27560) / dec!(78499),
                },
            },
            // This fixture is identical to the fixture above except for
            // the fact that the minimum order size is set.
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(1),
                    min_order_size: dec!(0.0001),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(56.5279),
                    ask_amount: dec!(60.3510),
                },
            },
            // This fixture is identical to the fixture above except for
            // the fact that the order amount is much smaller. The bid and
            // asks are limited to a much smaller order amount, and this
            // prevents the ask from crossing over.
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    mark_price,
                    symbol,
                    amount: dec!(1.7),
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(1),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(1.7),
                    ask_amount: dec!(1.7),
                },
            },
            // Bid:
            //
            // price = 3,000 + (-1) = 2,999
            //
            // Substituting into the increasing equation gives:
            //
            // delta = (9,500 - 1/20 * 12,500) / (1 * (2,999 - 3,000) + 0.002 * 2,999 + 1/20 * 3,000) = 57 + 20,057/77,499
            //
            // Since delta is positive, this delta is the theoretical fill amount.
            //
            // Ask:
            //
            // price = 3,000 - (-1) = 3,001
            //
            // Substituting into the decreasing equation gives:
            //
            // delta = (9,500 - 1/20 * 12,500) / (1 * (3,000 - 3,001) + 0.002 * 3,001 - 1/20 * 3,000) ≈ -61.2077.
            //
            // Since delta is negative and the account is strictly solvent,
            // we can maximally decrease the position. Since the position
            // will be fully decreased, we must evaluate the cross-over.
            //
            // The account will be updated as follows:
            //
            // C(a) = 10,000 + (3,001 - 5,000) * 2 - 0.002 * 3,001 * 2 = 5989.996
            //
            // U(a) = (50,000 - 100,000) * 0.1 + (1 - 0.15) * 10,000 = 3,500
            //
            // T(a) = 5,989.996 + 3,500 = 9,489.996
            //
            // N(a) = 12,500 - 3,000 * 2 = 6,500
            //
            // The margin fraction is 9,489.996/6,500 ≈ 1.4599 > 0.05 so the account
            // remains strictly solvent.
            //
            // Substituting into the increasing equation gives:
            //
            // delta = (9,489.996 - 1/20 * 6,500) / (-1 * (3,001 - 3,000) + 0.002 * 3,001 + 1/20 * 3,000) = 59 + 9,939/77,501.
            //
            // The decreasing delta is 2 and the increasing delta is 59 + 9,939/77,501,
            // so the total delta is 61 + 9,939/77,501.
            //
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(1).neg(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(57) + dec!(20057) / dec!(77499),
                    ask_amount: dec!(61) + dec!(9939) / dec!(77501),
                },
            },
            // This fixture is identical to the fixture above except for
            // the fact that the minimum order size is set.
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(1).neg(),
                    min_order_size: dec!(1),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(57),
                    ask_amount: dec!(61),
                },
            },
            // This fixture is identical to the fixture above except for
            // the fact that the order amount is much smaller. The bid and
            // asks are limited to a much smaller order amount, and this
            // prevents the ask from crossing over.
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    mark_price,
                    symbol,
                    amount: dec!(1.7),
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(1).neg(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(1.7),
                    ask_amount: dec!(1.7),
                },
            },
            // Bid:
            //
            // price = 3,000 + 200 = 3,200
            //
            // Substituting into the increasing equation gives:
            //
            // delta = (9,500 - 1/20 * 12,500) / (1 * (3,200 - 3,000) + 0.002 * 3,200 + 1/20 * 3,000) = 24 + 1,607/1,782
            //
            // Since delta is positive, this delta is the theoretical fill amount.
            //
            // Ask:
            //
            // price = 3,000 - 200 = 2,800
            //
            // Substituting into the decreasing equation gives:
            //
            // delta = (9,500 - 1/20 * 12,500) / (1 * (3,000 - 2,800) + 0.002 * 2,800 - 1/20 * 3,000) ≈ 159.6223.
            //
            // Since delta is positive but larger than the position balance,
            // we maximally decrease the position. Since the position
            // will be fully decreased, we must evaluate the cross-over.
            //
            // The account will be updated as follows:
            //
            // C(a) = 10,000 + (2,800 - 5,000) * 2 - 0.002 * 2,800 * 2 = 5,588.8
            //
            // U(a) = (50,000 - 100,000) * 0.1 + (1 - 0.15) * 10,000 = 3,500
            //
            // T(a) = 5,588.8 + 3,500 = 9,088.8
            //
            // N(a) = 12,500 - 3,000 * 2 = 6,500
            //
            // The margin fraction is 9,088.8/6,500 ≈ 1.3982 > 0.05 so the account
            // remains strictly solvent.
            //
            // Substituting into the increasing equation gives:
            //
            // delta = (9,088.8 - 1/20 * 6,500) / (-1 * (2,800 - 3,000) + 0.002 * 2,800 + 1/20 * 3,000) = 24 + 1,147/1,778.
            //
            // The decreasing delta is 2 and the increasing delta is 24 + 1,147/1,778,
            // so the total delta is 26 + 1,147/1,778.
            //
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(200),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(24) + dec!(1607) / dec!(1782),
                    ask_amount: dec!(26) + dec!(1147) / dec!(1778),
                },
            },
            // This fixture is identical to the fixture above except for
            // the fact that the minimum order size is set.
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(200),
                    min_order_size: dec!(0.1),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(24.9),
                    ask_amount: dec!(26.6),
                },
            },
            // This fixture is identical to the fixture above except for
            // the fact that the order amount is much smaller. The bid and
            // asks are limited to a much smaller order amount, and this
            // prevents the ask from crossing over.
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    mark_price,
                    symbol,
                    amount: dec!(1.7),
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(200),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(1.7),
                    ask_amount: dec!(1.7),
                },
            },
            // Bid:
            //
            // price = 3,000 - 200 = 2,800
            //
            // Substituting into the increasing equation gives:
            //
            // delta = (9,500 - 1/20 * 12,500) / (1 * (2,800 - 3,000) + 0.002 * 2,800 + 1/20 * 3,000) ≈ -199.8873
            //
            // Since delta is negative, the theoretical fill amount is unbounded
            //
            // Ask:
            //
            // price = 3,000 - (-200) = 3,200
            //
            // Substituting into the decreasing equation gives:
            //
            // delta = (9,500 - 1/20 * 12,500) / (1 * (3,000 - 3,200) + 0.002 * 3,200 - 1/20 * 3,000) ≈ -25.8294.
            //
            // Since delta is negative and the account is strictly solvent,
            // we can maximally decrease the position. Since the position
            // will be fully decreased, we must evaluate the cross-over.
            //
            // The account will be updated as follows:
            //
            // C(a) = 10,000 + (3,200 - 5,000) * 2 - 0.002 * 3,200 * 2 = 6,387.2
            //
            // U(a) = (50,000 - 100,000) * 0.1 + (1 - 0.15) * 10,000 = 3,500
            //
            // T(a) = 6,387.2 + 3,500 = 9,887.2
            //
            // N(a) = 12,500 - 3,000 * 2 = 6,500
            //
            // The margin fraction is 9,887.2/6,500 ≈ 1.5211 > 0.05 so the account
            // remains strictly solvent.
            //
            // Substituting into the increasing equation gives:
            //
            // delta = (9,887.2 - 1/20 * 6,500) / (-1 * (3,200 - 3,000) + 0.002 * 3,200 + 1/20 * 3,000) ≈ -219.3165.
            //
            // The decreasing delta is 2 and the increasing delta is negative,
            // the theoretical fill amount is unbounded.
            //
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    amount,
                    mark_price,
                    symbol,
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(200).neg(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: amount,
                    ask_amount: amount,
                },
            },
            MaximumFillAmountTestFixture {
                case: MaximumFillAmountTestCase {
                    account,
                    mark_price,
                    symbol,
                    amount: dec!(1.7),
                    fee_percentage: dec!(0.002),
                    price_delta: dec!(200).neg(),
                    min_order_size: dec!(0),
                },
                expected: MaximumFillAmountTestExpectation {
                    bid_amount: dec!(1.7),
                    ask_amount: dec!(1.7),
                },
            },
        ]);

        verify_maximum_fill_amount_fixtures(fixtures);
    }
}
