use super::VoidableItem;
use crate::types::transaction::{BalanceUpdate, FeeMeta, FillOutcomeMeta, PriceDetailMeta};
#[cfg(feature = "arbitrary")]
use core_common::types::primitives::arbitrary_h160;
use core_common::{Address, Result, ensure, types::primitives::UnscaledI128};
use core_macros::{AbiToken, dec};
#[cfg(feature = "arbitrary")]
use quickcheck::Arbitrary;
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};

/// An individual trader
#[cfg_eval]
#[cfg_attr(feature = "python", pyclass)]
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize, AbiToken, Eq)]
#[serde(rename_all = "camelCase")]
#[repr(C)]
pub struct Trader {
    /// The DDX balance stated / usable for trading
    #[cfg_attr(feature = "python", pyo3(get, set))]
    pub avail_ddx_balance: UnscaledI128,
    /// The DDX balance locked for withdrawal
    #[cfg_attr(feature = "python", pyo3(get, set))]
    pub locked_ddx_balance: UnscaledI128,
    /// The Ethereum account who referred the trader (receives DDX rewards as per referral program)
    pub referral_address: Address,
    /// Switch to paying fees with DDX
    #[cfg_attr(feature = "python", pyo3(get, set))]
    pub pay_fees_in_ddx: bool,
    /// Whether the trader is denied access to the platform
    #[cfg_attr(feature = "python", pyo3(get, set))]
    pub access_denied: bool,
}

cfg_if::cfg_if! {
    if #[cfg(feature = "python")] {
        use rustc_hex::ToHex;
        use std::str::FromStr;
        use pyo3::prelude::*;

        #[pymethods]
        impl Trader {
            #[new]
            fn new_py(
                avail_ddx_balance: UnscaledI128,
                locked_ddx_balance: UnscaledI128,
                referral_address: String,
                pay_fees_in_ddx: bool,
            ) -> PyResult<Self> {
                Ok(Self {
                    avail_ddx_balance,
                    locked_ddx_balance,
                    referral_address: Address::from_str(&referral_address).map_err(|e| {
                        core_common::types::exported::python::CoreCommonError::new_err(e.to_string())
                    })?,
                    pay_fees_in_ddx,
                    access_denied: false,
                })
            }

            #[getter]
            fn referral_address(&self) -> String {
                self.referral_address.as_slice().to_hex::<String>()
            }

            #[setter]
            fn set_referral_address(&mut self, hex: &str) -> PyResult<()> {
                self.referral_address = Address::from_str(hex).map_err(|e| {
                    core_common::types::exported::python::CoreCommonError::new_err(e.to_string())
                })?;
                Ok(())
            }
        }
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for Trader {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Self {
            avail_ddx_balance: UnscaledI128::arbitrary(g),
            locked_ddx_balance: UnscaledI128::arbitrary(g),
            referral_address: arbitrary_h160(g),
            pay_fees_in_ddx: bool::arbitrary(g),
            access_denied: false,
        }
    }
}

impl VoidableItem for Trader {
    fn is_void(&self) -> bool {
        false
    }
}

impl Trader {
    /// Adds DDX fees if the trader has enough available DDX available.
    ///
    /// The given fill includes a fee amount in the default currently, which we swap
    /// for the converted DDX amount if applicable.
    #[tracing::instrument(level = "debug", skip(self))]
    pub fn apply_ddx_fee_and_capture_outcome(
        &mut self,
        outcome: &mut FillOutcomeMeta,
        ddx_price: &PriceDetailMeta,
        discount: Decimal,
    ) -> Result<bool> {
        ensure!(
            discount <= dec!(1) && discount >= Decimal::ZERO,
            "Invalid discount percentage"
        );
        if outcome.base_fee.is_zero() {
            tracing::debug!(base_fee=?outcome.base_fee, "Found base fee of zero, no fees to apply");
            return Ok(false);
        }
        let fee_in_ddx = (outcome.base_fee / *ddx_price.inner.index_price) * (dec!(1) - discount);
        if UnscaledI128::from(fee_in_ddx).is_zero() {
            tracing::debug!(base_fee=?outcome.base_fee, ?fee_in_ddx, "Fee in DDX is zero after conversion and discount, no fees to apply");
            return Ok(false);
        }
        if *self.avail_ddx_balance < fee_in_ddx {
            tracing::debug!(base_fee=?outcome.base_fee, ?fee_in_ddx, ddx_balance=?self.avail_ddx_balance, "Not enough DDX to pay fees");
            return Ok(false);
        }
        let old_balance = *self.avail_ddx_balance;
        self.avail_ddx_balance = (old_balance - fee_in_ddx).into();
        // Recalculate the fee in DDX from the rounded trader balance update to capture the correct fee amount for validation.
        outcome.fee = FeeMeta::DDX(BalanceUpdate::new(
            (old_balance - *self.avail_ddx_balance).into(),
            self.avail_ddx_balance,
        ));
        tracing::debug!(
            ?old_balance,
            fee_paid=?outcome.fee,
            "Applied DDX fee to fill and reconciled with trader balance",
        );
        Ok(true)
    }
}

#[cfg(test)]
mod tests {
    use crate::{
        constants::DDX_FEE_DISCOUNT,
        execution::test_utils::{ETHP, price_with_single_name_perp_defaults},
        types::{
            accounting::{Price, PriceDirection, PriceMetadata, TradeSide},
            transaction::Fill,
        },
    };
    use core_common::types::primitives::{OrderSide, TraderAddress};
    use core_crypto::test_accounts::{BOB, CHARLIE};
    use core_macros::unscaled;
    use rust_decimal::prelude::Zero;

    use super::*;

    fn compare_outcomes(
        fill: &Fill<FillOutcomeMeta>,
        side: &TradeSide,
        expected: &FillOutcomeMeta,
    ) {
        let actual = match fill {
            Fill::Trade {
                maker_outcome,
                taker_outcome,
                ..
            } => match side {
                TradeSide::Maker => maker_outcome,
                TradeSide::Taker => taker_outcome,
            },
            Fill::Liquidation { maker_outcome, .. } => maker_outcome,
        };
        assert_eq!(actual, expected);
    }

    fn create_trader_and_fill(
        avail_ddx_balance: UnscaledI128,
        pay_fees_in_ddx: bool,
        maker_fee: UnscaledI128,
        taker_fee: UnscaledI128,
        liquidation: bool,
    ) -> (Trader, Fill<FillOutcomeMeta>) {
        let symbol = ETHP.into();
        let t = Trader {
            avail_ddx_balance,
            locked_ddx_balance: unscaled!(0),
            referral_address: Default::default(),
            pay_fees_in_ddx,
            access_denied: false,
        };
        let maker_outcome = FillOutcomeMeta::new_with_strategy(BOB, Default::default(), maker_fee);
        let taker_outcome =
            FillOutcomeMeta::new_with_strategy(CHARLIE, Default::default(), taker_fee);
        let fill = if !liquidation {
            Fill::Trade {
                maker_outcome,
                taker_outcome,
                symbol,
                maker_order_hash: Default::default(),
                maker_order_remaining_amount: Default::default(),
                taker_order_hash: Default::default(),
                amount: Default::default(),
                price: Default::default(),
                taker_side: OrderSide::Bid,
            }
        } else {
            Fill::Liquidation {
                maker_outcome,
                symbol,
                maker_order_hash: Default::default(),
                maker_order_remaining_amount: Default::default(),
                amount: Default::default(),
                price: Default::default(),
                taker_side: OrderSide::Bid,
                index_price_hash: Default::default(),
            }
        };
        (t, fill)
    }

    /// Helper for a narrow set of tests that expect the .
    fn expected_traders(
        maker: TraderAddress,
        taker: TraderAddress,
        base_maker_fee: Decimal,
        base_taker_fee: Decimal,
        maker_fee: UnscaledI128,
        taker_fee: UnscaledI128,
        maker_ddx_balance: Decimal,
        taker_ddx_balance: Decimal,
        ddx_fee_election: bool,
    ) -> (FillOutcomeMeta, FillOutcomeMeta) {
        let expected_maker_outcome = FillOutcomeMeta {
            trader_address: maker,
            base_fee: base_maker_fee,
            fee: if ddx_fee_election {
                FeeMeta::DDX(BalanceUpdate::new(maker_fee, maker_ddx_balance.into()))
            } else {
                FeeMeta::DefaultCurrency(maker_fee)
            },
            ..Default::default()
        };
        let expected_taker_outcome = FillOutcomeMeta {
            trader_address: taker,
            base_fee: base_taker_fee,
            fee: if ddx_fee_election {
                FeeMeta::DDX(BalanceUpdate::new(taker_fee, taker_ddx_balance.into()))
            } else {
                FeeMeta::DefaultCurrency(taker_fee)
            },
            ..Default::default()
        };
        (expected_maker_outcome, expected_taker_outcome)
    }

    #[test]
    fn test_trader_ddx_fee_has_enough_ddx_fill_invalid_discount_returns_err() {
        let price = PriceDetailMeta::new(
            Default::default(),
            Price::from_price_value(unscaled!(10), 1, Default::default()),
            PriceMetadata::SingleNamePerpetual,
            PriceDirection::Up,
        );
        let (maker_fee, taker_fee) = (dec!(10), dec!(90));
        let avail_ddx_balance = dec!(10000);
        let (mut t, mut fill) = create_trader_and_fill(
            avail_ddx_balance.into(),
            true,
            maker_fee.into(),
            taker_fee.into(),
            false,
        );
        for discount in &[dec!(-3), dec!(1.1), dec!(2)] {
            assert!(
                t.apply_ddx_fee_and_capture_outcome(
                    fill.outcome_mut(&TradeSide::Maker).unwrap(),
                    &price,
                    *discount,
                )
                .is_err()
            );
            assert!(
                t.apply_ddx_fee_and_capture_outcome(
                    fill.outcome_mut(&TradeSide::Taker).unwrap(),
                    &price,
                    *discount,
                )
                .is_err()
            );
        }
    }

    /// Confusing naming, but this tests that the DDX fees property is only set when DDX fees are actually used.
    #[test]
    fn test_trader_ddx_fee_has_not_enough_ddx_fill_returns_ddx_fees_only() {
        let discount = Decimal::ZERO;
        let (maker_fee, taker_fee) = (dec!(10), dec!(90));
        let avail_ddx_balance = dec!(0);
        let price = price_with_single_name_perp_defaults(unscaled!(10), 1);
        let (mut t, mut fill) = create_trader_and_fill(
            avail_ddx_balance.into(),
            true,
            maker_fee.into(),
            taker_fee.into(),
            false,
        );
        t.apply_ddx_fee_and_capture_outcome(
            fill.outcome_mut(&TradeSide::Maker).unwrap(),
            &price,
            discount,
        )
        .unwrap();
        assert!(!fill.fees().0.unwrap().is_ddx());
        t.apply_ddx_fee_and_capture_outcome(
            fill.outcome_mut(&TradeSide::Taker).unwrap(),
            &price,
            discount,
        )
        .unwrap();
        assert!(!fill.fees().1.unwrap().is_ddx());
    }

    // TODO 3622: Here's a prime example of questionable testing practices. Do we really need to re-tests primitives in every module that use them? Why not testing it just once?
    #[test]
    fn test_trader_apply_ddx_balance_scales_to_6_places() {
        let mut t = Trader {
            avail_ddx_balance: unscaled!(0),
            locked_ddx_balance: unscaled!(0),
            referral_address: Default::default(),
            pay_fees_in_ddx: false,
            access_denied: false,
        };

        let pi = dec!(3.1415926535897932384);

        // this crashes because of too many decimal places (19)
        t.avail_ddx_balance = (*t.avail_ddx_balance + pi).into();

        assert_eq!(*t.avail_ddx_balance, dec!(3.141592));
    }

    #[test]
    #[core_macros::setup]
    fn test_trader_ddx_fee_has_enough_ddx_fill() {
        let discount = Decimal::ZERO;

        let index_price = dec!(10);
        let (maker_fee, taker_fee) = (dec!(10), dec!(90));
        let (maker_fee_ddx, taker_fee_ddx) = (maker_fee / index_price, taker_fee / index_price);
        let avail_ddx_balance = dec!(10000);

        // Setting a DDX price of 10, meaning 10x the base currency.
        let price = price_with_single_name_perp_defaults(index_price.into(), 1);
        let (expected_maker_outcome, expected_taker_outcome) = expected_traders(
            BOB.into(),
            CHARLIE.into(),
            maker_fee,
            taker_fee,
            maker_fee_ddx.into(),
            taker_fee_ddx.into(),
            avail_ddx_balance - maker_fee_ddx,
            // We'll debit both the maker and taker fee from Charlie.
            avail_ddx_balance - maker_fee_ddx - taker_fee_ddx,
            true,
        );
        let (mut t, mut fill) = create_trader_and_fill(
            avail_ddx_balance.into(),
            true,
            maker_fee.into(),
            taker_fee.into(),
            false,
        );
        t.apply_ddx_fee_and_capture_outcome(
            fill.outcome_mut(&TradeSide::Maker).unwrap(),
            &price,
            discount,
        )
        .unwrap();
        compare_outcomes(&fill, &TradeSide::Maker, &expected_maker_outcome);
        assert_eq!(*t.avail_ddx_balance, avail_ddx_balance - maker_fee_ddx);

        t.apply_ddx_fee_and_capture_outcome(
            fill.outcome_mut(&TradeSide::Taker).unwrap(),
            &price,
            discount,
        )
        .unwrap();
        compare_outcomes(&fill, &TradeSide::Taker, &expected_taker_outcome);
        assert_eq!(
            t.avail_ddx_balance,
            (avail_ddx_balance - maker_fee_ddx - taker_fee_ddx).into()
        );
    }

    #[test]
    fn test_trader_ddx_fee_has_enough_ddx_fill_returns_correct_fees() {
        let discount = Decimal::ZERO;

        let index_price = dec!(10);
        let (maker_fee, taker_fee) = (dec!(10), dec!(90));
        let (maker_fee_ddx, taker_fee_ddx) = (maker_fee / index_price, taker_fee / index_price);
        assert_eq!(maker_fee_ddx, dec!(1));
        assert_eq!(taker_fee_ddx, dec!(9));
        let avail_ddx_balance = dec!(10000);

        let price = price_with_single_name_perp_defaults(index_price.into(), 1);
        let (expected_maker_outcome, expected_taker_outcome) = expected_traders(
            BOB.into(),
            CHARLIE.into(),
            maker_fee,
            taker_fee,
            maker_fee_ddx.into(),
            taker_fee_ddx.into(),
            avail_ddx_balance - maker_fee_ddx,
            // We'll debit both the maker and taker fee from Charlie.
            avail_ddx_balance - maker_fee_ddx - taker_fee_ddx,
            true,
        );
        // TODO 3622: This approach is confusing, we explicitly create a maker and a taker should to apply both fees to the same one trader instance.
        let (mut t, mut fill) = create_trader_and_fill(
            avail_ddx_balance.into(),
            true,
            maker_fee.into(),
            taker_fee.into(),
            false,
        );

        t.apply_ddx_fee_and_capture_outcome(
            fill.outcome_mut(&TradeSide::Maker).unwrap(),
            &price,
            discount,
        )
        .unwrap();
        let fee = *fill
            .fees()
            .0
            .unwrap()
            .ddx()
            .expect("Expected fee paid in DDX");
        assert_eq!(fee, maker_fee_ddx);
        compare_outcomes(&fill, &TradeSide::Maker, &expected_maker_outcome);

        t.apply_ddx_fee_and_capture_outcome(
            fill.outcome_mut(&TradeSide::Taker).unwrap(),
            &price,
            discount,
        )
        .unwrap();
        let fee = *fill
            .fees()
            .1
            .unwrap()
            .ddx()
            .expect("Expected fee paid in DDX");
        assert_eq!(fee, taker_fee_ddx);
        compare_outcomes(&fill, &TradeSide::Taker, &expected_taker_outcome);
    }

    #[test]
    fn test_trader_ddx_fee_has_enough_ddx_fill_with_discount() {
        let discount = DDX_FEE_DISCOUNT;
        let index_price = dec!(10);
        let (maker_fee, taker_fee) = (dec!(100), dec!(900));

        let (maker_fee_ddx, taker_fee_ddx) = ((maker_fee / index_price), (taker_fee / index_price));
        let avail_ddx_balance = dec!(10000);

        let price_checkpoint = price_with_single_name_perp_defaults(index_price.into(), 1);
        let discounted_maker_fee = maker_fee_ddx * (dec!(1) - discount);
        assert_eq!(discounted_maker_fee, dec!(5));
        let discounted_taker_fee = taker_fee_ddx * (dec!(1) - discount);
        assert_eq!(discounted_taker_fee, dec!(45));

        let (expected_maker_outcome, expected_taker_outcome) = expected_traders(
            BOB.into(),
            CHARLIE.into(),
            maker_fee,
            taker_fee,
            discounted_maker_fee.into(),
            discounted_taker_fee.into(),
            avail_ddx_balance - discounted_maker_fee,
            // We'll debit both the maker and taker fee from Charlie.
            avail_ddx_balance - discounted_maker_fee - discounted_taker_fee,
            true,
        );
        let (mut t, mut fill) = create_trader_and_fill(
            avail_ddx_balance.into(),
            true,
            maker_fee.into(),
            taker_fee.into(),
            false,
        );
        t.apply_ddx_fee_and_capture_outcome(
            fill.outcome_mut(&TradeSide::Maker).unwrap(),
            &price_checkpoint,
            discount,
        )
        .unwrap();
        compare_outcomes(&fill, &TradeSide::Maker, &expected_maker_outcome);
        assert_eq!(
            t.avail_ddx_balance,
            UnscaledI128::new(avail_ddx_balance - discounted_maker_fee)
        );

        t.apply_ddx_fee_and_capture_outcome(
            fill.outcome_mut(&TradeSide::Taker).unwrap(),
            &price_checkpoint,
            discount,
        )
        .unwrap();
        compare_outcomes(&fill, &TradeSide::Taker, &expected_taker_outcome);
        assert_eq!(
            t.avail_ddx_balance,
            UnscaledI128::new(avail_ddx_balance - discounted_maker_fee - discounted_taker_fee)
        );
    }

    #[test]
    fn test_trader_ddx_fee_has_not_enough_ddx_fill_no_ddx_paid() {
        let discount = Decimal::ZERO;
        let index_price = dec!(100);
        let (maker_fee, taker_fee) = (dec!(1000), dec!(9000));
        let avail_ddx_balance = dec!(0);

        let price_checkpoint = price_with_single_name_perp_defaults(index_price.into(), 1);
        let (expected_maker_outcome, expected_taker_outcome) = expected_traders(
            BOB.into(),
            CHARLIE.into(),
            maker_fee,
            taker_fee,
            unscaled!(0),
            unscaled!(0),
            dec!(0),
            dec!(0),
            false,
        );

        let (mut t, mut fill) = create_trader_and_fill(
            avail_ddx_balance.into(),
            true,
            maker_fee.into(),
            taker_fee.into(),
            false,
        );

        t.apply_ddx_fee_and_capture_outcome(
            fill.outcome_mut(&TradeSide::Maker).unwrap(),
            &price_checkpoint,
            discount,
        )
        .unwrap();
        compare_outcomes(&fill, &TradeSide::Maker, &expected_maker_outcome);
        assert_eq!(*t.avail_ddx_balance, avail_ddx_balance);

        t.apply_ddx_fee_and_capture_outcome(
            fill.outcome_mut(&TradeSide::Taker).unwrap(),
            &price_checkpoint,
            discount,
        )
        .unwrap();
        compare_outcomes(&fill, &TradeSide::Taker, &expected_taker_outcome);
    }

    #[test]
    fn test_trader_ddx_fee_has_enough_ddx_liquidation() {
        let discount = Decimal::ZERO;

        let index_price = dec!(10);
        let (maker_fee, taker_fee) = (dec!(100), dec!(90));
        let (maker_fee_ddx, _) = (maker_fee / index_price, taker_fee / index_price);
        let avail_ddx_balance = dec!(10000);

        let price_checkpoint = price_with_single_name_perp_defaults(index_price.into(), 1);
        let (expected_maker_outcome, _) = expected_traders(
            BOB.into(),
            CHARLIE.into(),
            maker_fee,
            taker_fee,
            maker_fee_ddx.into(),
            unscaled!(0),
            avail_ddx_balance - maker_fee_ddx,
            // We don't debit the taker fee in this test.
            avail_ddx_balance,
            true,
        );
        let (mut t, mut fill) = create_trader_and_fill(
            avail_ddx_balance.into(),
            true,
            maker_fee.into(),
            taker_fee.into(),
            true,
        );

        t.apply_ddx_fee_and_capture_outcome(
            fill.outcome_mut(&TradeSide::Maker).unwrap(),
            &price_checkpoint,
            discount,
        )
        .unwrap();
        assert_eq!(*t.avail_ddx_balance, avail_ddx_balance - maker_fee_ddx);
        compare_outcomes(&fill, &TradeSide::Maker, &expected_maker_outcome);
    }

    #[test]
    /// Scenario where DDX fees are supposed to be used to pay for the liquidation fees (if any),
    /// but here there isn't enough DDX available to actually pay. Therefore no DDX fees are
    /// applied.
    fn test_trader_ddx_fee_has_not_enough_ddx_liquidation_no_ddx_paid() {
        let discount = Decimal::ZERO;

        let index_price = dec!(100);
        let (maker_fee, taker_fee) = (dec!(1000), dec!(9000));
        let avail_ddx_balance = Decimal::zero();

        let price = price_with_single_name_perp_defaults(index_price.into(), 1);
        let (expected_maker_outcome, _) = expected_traders(
            BOB.into(),
            CHARLIE.into(),
            maker_fee,
            taker_fee,
            Default::default(),
            Default::default(),
            avail_ddx_balance - maker_fee,
            // We don't debit the taker fee in this test.
            avail_ddx_balance,
            false,
        );
        let (mut t, mut fill) = create_trader_and_fill(
            avail_ddx_balance.into(),
            true,
            maker_fee.into(),
            taker_fee.into(),
            false,
        );

        t.apply_ddx_fee_and_capture_outcome(
            fill.outcome_mut(&TradeSide::Maker).unwrap(),
            &price,
            discount,
        )
        .unwrap();
        compare_outcomes(&fill, &TradeSide::Maker, &expected_maker_outcome);
        assert_eq!(*t.avail_ddx_balance, avail_ddx_balance);
    }
}
