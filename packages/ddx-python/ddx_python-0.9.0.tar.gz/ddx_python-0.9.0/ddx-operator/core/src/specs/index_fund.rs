use crate::{
    specs::{Atom, Expr, StructRepr, eval_from_str},
    types::primitives::UnderlyingSymbol,
};
use core_common::{Error, Result, types::primitives::UnscaledI128};
#[cfg(feature = "python")]
use pyo3::{prelude::*, types::PyDict};
use serde::{Deserialize, Serialize};
use std::{
    collections::BTreeMap,
    convert::{TryFrom, TryInto},
    str::FromStr,
    string::ToString,
    vec::Vec,
};

pub type AllocationWeight = UnscaledI128;

#[cfg_attr(feature = "python", pyclass(frozen, get_all))]
#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct IndexFundPerpetual {
    pub allocation: BTreeMap<UnderlyingSymbol, AllocationWeight>,
    pub rebalance_interval: u64,
    pub initial_index_price: UnscaledI128,
    pub tick_size: UnscaledI128,
    pub max_order_notional: UnscaledI128,
    pub max_taker_price_deviation: UnscaledI128,
    pub min_order_size: UnscaledI128,
}

#[cfg(feature = "python")]
#[pymethods]
impl IndexFundPerpetual {
    #[new]
    #[pyo3(signature = (**kwds))]
    pub(crate) fn new_py(kwds: Option<&PyDict>) -> PyResult<Self> {
        let _kwds = kwds.ok_or_else(|| {
            core_common::types::exported::python::CoreCommonError::new_err(
                "Expected keyword dictionary containing specs".to_string(),
            )
        })?;
        // TODO 3979: Implement this, respecting/reusing code from TryFrom<StructRepr>. This may
        // cause some changes in SingleNamePerpetual and QuarterlyExpiryFuture to keep consistency
        // between all specs types.
        todo!()
    }
}

#[cfg(feature = "test_harness")]
impl Default for IndexFundPerpetual {
    fn default() -> Self {
        Self {
            allocation: Default::default(),
            rebalance_interval: 3600 * 24 * 7,
            initial_index_price: Default::default(),
            tick_size: Default::default(),
            max_order_notional: Default::default(),
            max_taker_price_deviation: Default::default(),
            min_order_size: Default::default(),
        }
    }
}

impl FromStr for IndexFundPerpetual {
    type Err = Error;

    fn from_str(expr: &str) -> Result<Self, Self::Err> {
        if let Expr::Constant(Atom::Struct(repr)) = eval_from_str(expr)? {
            repr.try_into()
        } else {
            Err(Error::Parse(expr.to_string()))
        }
    }
}

impl TryFrom<StructRepr> for IndexFundPerpetual {
    type Error = Error;

    fn try_from(mut repr: StructRepr) -> Result<Self, Self::Error> {
        repr.ensure_match("IndexFundPerpetual", 4)?;
        // TODO: Be able to convert a list of pairs into a hash map
        let underlying: Vec<UnderlyingSymbol> = repr
            .try_take("underlying")?
            .try_list()?
            .into_iter()
            .map(|s| s.try_into())
            .collect::<Result<Vec<_>>>()?;
        let weights: Vec<AllocationWeight> = repr
            .try_take("weights")?
            .try_list()?
            .into_iter()
            .map(|s| s.try_into())
            .collect::<Result<Vec<_>>>()?;
        let allocation = underlying
            .into_iter()
            .zip(weights)
            .collect::<BTreeMap<_, _>>();
        Ok(IndexFundPerpetual {
            allocation,
            rebalance_interval: repr.try_take("rebalance-interval")?.try_into()?,
            initial_index_price: repr.try_take("initial-index-price")?.try_into()?,
            tick_size: repr.try_take("tick-size")?.try_into()?,
            max_order_notional: repr.try_take("max-order-notional")?.try_into()?,
            max_taker_price_deviation: repr.try_take("max-taker-price-deviation")?.try_into()?,
            min_order_size: repr.try_take("min-order-size")?.try_into()?,
        })
    }
}
