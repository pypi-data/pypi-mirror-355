#[cfg(not(target_family = "wasm"))]
use crate::trusted_settings::COLLATERAL_TRANCHES;
use crate::types::{
    accounting::{Position, PositionSide, Strategy, TradeSide},
    transaction::{FeeMeta, FillOutcomeMeta},
};
use core_common::{
    Error, Result, bail,
    types::primitives::{OrderSide, TokenSymbol},
};
use core_macros::dec;
use rust_decimal::{
    Decimal,
    prelude::{One, Zero},
};

#[tracing::instrument(level = "debug")]
pub fn calculate_funding_payment(
    mark_price: &Decimal,
    position: &Position,
    funding_rate: &Decimal,
) -> Decimal {
    let balance = position.balance;
    match position.side {
        PositionSide::Long => funding_rate * -Decimal::one() * *balance * mark_price,
        PositionSide::Short => funding_rate * *balance * mark_price,
        PositionSide::None => {
            panic!("Accounts pre-filtered by symbol should not contain empty positions");
        }
    }
}

/// Calculate the trade mining reward for this trader.
///
/// The reward_share parameter a number between 0 and 1 that specifies the weight
/// that the users trades have. To start, our profiles are maker and taker with
/// maker receiving 20%  and taker receiving 80% of trade mining rewards.
#[tracing::instrument(level = "debug")]
pub fn calculate_trade_mining_reward(
    epoch_reward: &Decimal,
    reward_share: &Decimal,
    total_volume: &Decimal,
    trader_volume: &Decimal,
) -> Decimal {
    debug_assert!(
        *total_volume > dec!(0),
        "Total volume is zero. Trader volume is {}",
        trader_volume
    );
    let res = reward_share * ((epoch_reward * trader_volume) / total_volume);
    tracing::debug!(?res, "Calculated trade mining reward");
    res
}

/// Calculate the maximum available collateral allowed by a trader given the DDX balance
///
/// This is a cumulative collateral amount based on the sum of all strategies.
#[tracing::instrument(level = "debug")]
pub fn max_collateral(ddx_balance: Decimal) -> (u32, Decimal) {
    let mut limit = Decimal::zero();
    let mut tranche_tier = 0_u32;
    for tranche in COLLATERAL_TRANCHES
        .iter()
        .map(|t| (Decimal::from(t.0), Decimal::from(t.1)))
    {
        limit = tranche.1;
        // Stop if our balance is lower than the tranche's upper bound.
        if ddx_balance < tranche.0 {
            break;
        }
        tranche_tier += 1;
    }
    (tranche_tier, limit)
}

// Verify if the DDX withdrawal will lower the available collateral tier of the trader.
#[tracing::instrument(level = "debug")]
pub fn verify_withdraw_col_ddx_guard(
    old_ddx: Decimal,
    new_ddx: Decimal,
    collateral: Decimal,
) -> bool {
    let (old_tier, _) = max_collateral(old_ddx);
    let (new_tier, new_limit) = max_collateral(new_ddx);
    old_tier <= new_tier || collateral <= new_limit
}

impl Strategy {
    /// Applies the realized value to this strategy
    ///
    /// Realized pnl from trading is always applied using the default currency.
    /// Other currencies are exchanged into the default a priori.
    ///
    /// See issue #1488. This fails if the balance is negative which could occur under
    /// specific market swings. In general, the outcome of such failure should be to reject
    /// the trade.
    #[tracing::instrument(level = "debug", skip(self))]
    pub fn realize_trade_and_capture_outcome(
        &mut self,
        outcome: &mut FillOutcomeMeta,
    ) -> Result<()> {
        // TODO: What now? Do we expect this to occur here? If so, how to recover? If not, just use a debug_assert invariant for clarity.
        if self.frozen {
            return Err(Error::Other(
                "Cannot realize pnl from a locked strategy".to_string(),
            ));
        }
        debug_assert!(
            outcome.realized_pnl.amount.is_none(),
            "Realized PNL already finalized"
        );
        let original_balance = *self.avail_collateral[TokenSymbol::USDC];
        // Apply the calculated P&L value (not rounded) to the margin balance.
        self.avail_collateral.insert(
            TokenSymbol::USDC,
            (original_balance + outcome.realized_pnl.pnl_amount).into(),
        );
        if !outcome.fee.is_ddx() && outcome.base_fee > Decimal::zero() {
            // If the fee is not paid in DDX, then we apply the raw fee (not rounded) to the margin balance and
            // calculate the final fee from the rounded balance differences, which avoids rounding errors.
            let old_balance = *self.avail_collateral[TokenSymbol::USDC];
            self.avail_collateral
                .insert(TokenSymbol::USDC, (old_balance - outcome.base_fee).into());
            // Capture the raw fee in the realized P&L because it is paid in the default currency.
            // We can now verify: new_balance_rounded == old_balance_rounded.apply(pnl.amount).apply(-pnl.fee)
            outcome.realized_pnl.discounted_fee = outcome.base_fee;
            let available_balance = *self.avail_collateral[TokenSymbol::USDC];
            // Subtract the new from the old because the fee is negative.
            debug_assert!(old_balance > available_balance);
            outcome.fee = FeeMeta::DefaultCurrency((old_balance - available_balance).into());
        };
        let available_balance = *self.avail_collateral[TokenSymbol::USDC];
        outcome.realized_pnl.new_balance = available_balance.into();
        outcome.realized_pnl.amount = Some((available_balance - original_balance).into());
        Ok(())
    }
}

impl Position {
    /// Records the fill into this position then mutates the fill by setting the calculated realized value.
    ///
    /// This deliberately exclude DDX fees, which must be applied to the P&L using a different function.
    #[tracing::instrument(level = "debug", skip(self))]
    pub fn apply_fill_and_capture_outcome(
        &mut self,
        order_side: &OrderSide,
        amount: Decimal,
        price: Decimal,
        trade_side: &TradeSide,
        outcome: &mut FillOutcomeMeta,
    ) -> Result<()> {
        outcome.base_fee = trade_side.trading_fee(amount, price);

        let old_balance = *self.balance;
        // This changes the balance.
        outcome.realized_pnl.pnl_amount = self.apply_trade(amount, price, order_side)?;
        outcome.position_update.amount = (*self.balance - old_balance).into();
        outcome.position_update.balance = *self.balance;
        outcome.position_update.side = self.side;
        outcome.position_update.avg_entry_price = *self.avg_entry_price;
        Ok(())
    }

    /// Applies the trade to this position resulting in an accounting equation that changes
    /// the state and return the pnl
    #[tracing::instrument(level = "debug", skip(self))]
    pub fn apply_trade(
        &mut self,
        amount: Decimal,
        price: Decimal,
        side: &OrderSide,
    ) -> Result<Decimal> {
        let pnl = match side {
            OrderSide::Bid if self.side == PositionSide::Long => self.increase(price, amount),
            OrderSide::Bid if self.side == PositionSide::Short => {
                // If the buy amount is greater than the short position, we have a position crossover
                if amount > *self.balance {
                    self.cross_over(price, amount)?
                } else {
                    self.decrease(price, amount)
                }
            }
            OrderSide::Bid if self.side == PositionSide::None => {
                self.side = PositionSide::Long;
                self.increase(price, amount)
            }
            OrderSide::Ask if self.side == PositionSide::Short => self.increase(price, amount),
            OrderSide::Ask if self.side == PositionSide::Long => {
                // If the sell amount is greater than the long position, we have a position crossover
                if amount > *self.balance {
                    self.cross_over(price, amount)?
                } else {
                    self.decrease(price, amount)
                }
            }
            OrderSide::Ask if self.side == PositionSide::None => {
                self.side = PositionSide::Short;
                self.increase(price, amount)
            }
            _ => bail!(
                "Illegal order / position side combo: {:?} / {:?}",
                side,
                self.side
            ),
        };
        Ok(pnl)
    }
}

#[cfg(test)]
pub mod tests {
    use super::*;
    use crate::types::{accounting::TAKER_FEE_BPS, transaction::Fill};
    use core_macros::unscaled;

    #[test]
    fn test_ddx_withdrawal_check() {
        // collateral < limit will withdraw
        let mut collateral = dec!(10000);
        let mut balance = dec!(1000000);
        assert!(verify_withdraw_col_ddx_guard(
            balance,
            balance - dec!(1),
            collateral
        ));
        // collateral > limit but didn't downgrade tranche will withdraw
        collateral = dec!(15000000);
        balance = dec!(1000001);
        assert!(verify_withdraw_col_ddx_guard(
            balance,
            balance - dec!(1),
            collateral
        ));
        // collateral > limit and tranche downgrade throw an error
        balance = dec!(1000000);
        assert!(!verify_withdraw_col_ddx_guard(
            balance,
            balance - dec!(1),
            collateral
        ));
    }

    #[test]
    fn test_calculate_fees() {
        let amount = dec!(10);
        let price = dec!(100);
        let taker_fee = TradeSide::Taker.trading_fee(amount, price);
        let notional = amount * price;
        let fee = notional * *TAKER_FEE_BPS;
        assert_eq!(taker_fee, fee);
    }

    #[test]
    fn test_apply_fill() {
        let mut position = Position {
            side: PositionSide::Long,
            balance: unscaled!(100.0),
            avg_entry_price: unscaled!(200.0),
        };
        let mut fill = Fill::Trade {
            symbol: Default::default(),
            taker_order_hash: Default::default(),
            maker_order_hash: Default::default(),
            amount: unscaled!(100.0),
            price: unscaled!(400.0),
            maker_outcome: Default::default(),
            maker_order_remaining_amount: Default::default(),
            taker_outcome: Default::default(),
            taker_side: OrderSide::Ask,
        };
        position
            .apply_fill_and_capture_outcome(
                &OrderSide::Bid,
                *fill.amount(),
                *fill.price(),
                &TradeSide::Taker,
                fill.outcome_mut(&TradeSide::Taker).unwrap(),
            )
            .unwrap();
        assert_eq!(position.balance, unscaled!(200));
        assert_eq!(position.avg_entry_price, unscaled!(300));
        assert_eq!(
            fill.outcome_mut(&TradeSide::Taker)
                .unwrap()
                .position_update
                .amount,
            unscaled!(100)
        );
    }
}
