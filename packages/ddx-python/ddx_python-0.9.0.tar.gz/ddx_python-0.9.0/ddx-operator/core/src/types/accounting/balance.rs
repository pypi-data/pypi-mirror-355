use crate::constants::MAX_COLLATERAL_TYPES;
#[cfg(not(target_family = "wasm"))]
use crate::types::state::VoidableItem;
use alloy_dyn_abi::DynSolValue;
use alloy_primitives::U128;
use core_common::{
    Error, Result, bail, ensure, error,
    types::{
        global::TokenAddress,
        primitives::{RecordedAmount, TokenSymbol, UnscaledI128},
    },
    util::tokenize::Tokenizable,
};
use heapless::LinearMap;
#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "arbitrary")]
use quickcheck::Arbitrary;
use rust_decimal::{Decimal, prelude::Zero};
use serde::{Deserialize, Serialize};
use std::ops::Index;

/// Maps token address to balance amount
#[cfg_attr(feature = "python", pyclass)]
#[derive(Clone, Debug, PartialEq, Eq, Default, Deserialize, Serialize)]
#[serde(transparent)]
pub struct Balance(LinearMap<TokenAddress, UnscaledI128, { MAX_COLLATERAL_TYPES }>);

#[cfg(feature = "python")]
#[pymethods]
impl Balance {
    #[new]
    pub fn new_py(
        amount: core_common::types::primitives::exported::python::Decimal,
        address: TokenSymbol,
    ) -> Self {
        Self::new(Decimal::from(amount).into(), address)
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for Balance {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        let mut map = LinearMap::new();
        for (_, value) in map.iter_mut() {
            *value = UnscaledI128::arbitrary(g);
        }
        Self(map)
    }
}

#[cfg(not(target_family = "wasm"))]
impl VoidableItem for Balance {
    fn is_void(&self) -> bool {
        self.is_zero()
    }
}

impl Index<TokenSymbol> for Balance {
    type Output = UnscaledI128;

    fn index(&self, symbol: TokenSymbol) -> &Self::Output {
        let address = TokenAddress::from(symbol);
        &self.0[&address]
    }
}

impl Tokenizable for Balance {
    fn from_token(token: DynSolValue) -> Result<Self> {
        let mut tokens = match token {
            DynSolValue::Tuple(v) => v,
            _ => bail!("Not a tuple"),
        };
        ensure!(tokens.len() == 2, "Map in tuple of two");
        let values = tokens
            .pop()
            .unwrap()
            .as_array()
            .map(|a| a.to_vec())
            .ok_or_else(|| error!("Token array"))?;
        let keys = tokens
            .pop()
            .unwrap()
            .as_array()
            .map(|a| a.to_vec())
            .ok_or_else(|| error!("Token array"))?;
        let mut field = LinearMap::new();
        for (key, value) in keys.into_iter().zip(values.into_iter()) {
            let k = TokenAddress::from_token(key.clone())?;
            let v_u128 = U128::from_token(value)?;
            field.insert(k, v_u128.into()).unwrap();
        }
        Ok(Balance(field))
    }

    fn into_token(self) -> DynSolValue {
        let pairs: Vec<(TokenAddress, U128)> =
            self.0.iter().map(|(k, v)| (*k, (*v).into())).collect();
        let mut key_tokens: Vec<DynSolValue> = std::vec![];
        let mut value_tokens: Vec<DynSolValue> = std::vec![];
        for (key, value) in pairs.into_iter() {
            key_tokens.push(key.into_token());
            value_tokens.push(value.into_token());
        }
        let tokens = std::vec![
            DynSolValue::Array(key_tokens),
            DynSolValue::Array(value_tokens),
        ];
        DynSolValue::Tuple(tokens)
    }
}

impl Balance {
    /// Set new balance for a token symbol
    pub fn new(amount: RecordedAmount, symbol: TokenSymbol) -> Self {
        let address = TokenAddress::from(symbol);
        let mut balance = Self::default();
        balance
            .0
            .insert(address, amount)
            .expect("collaterals limit exceeded");
        balance
    }

    pub fn new_from_many(
        collaterals: &LinearMap<TokenSymbol, Decimal, { MAX_COLLATERAL_TYPES }>,
    ) -> Result<Self> {
        if collaterals.is_empty() {
            return Err(Error::Other(
                "Cannot create balance with no collateral addresses".to_string(),
            ));
        }
        let mut balance = Self::default();
        for (symbol, amount) in collaterals.iter() {
            let address = TokenAddress::from(*symbol);
            balance.0.insert(address, amount.into()).unwrap();
        }
        Ok(balance)
    }

    pub fn get_or_default(&self, symbol: TokenSymbol) -> UnscaledI128 {
        self.0
            .get(&TokenAddress::from(symbol))
            .copied()
            .unwrap_or_default()
    }

    pub fn token_addresses(&self) -> Vec<TokenAddress> {
        self.0.keys().copied().collect()
    }

    pub fn insert(&mut self, symbol: TokenSymbol, amount: RecordedAmount) -> Option<UnscaledI128> {
        let address = TokenAddress::from(symbol);
        if amount.is_zero() {
            return self.0.remove(&address);
        }
        self.0
            .insert(address, amount)
            .expect("collaterals limit exceeded")
    }

    pub fn len(&self) -> usize {
        self.0.len()
    }

    pub fn is_empty(&self) -> bool {
        self.0.is_empty()
    }

    /// Returns true if there is no values in the Balance
    pub fn is_zero(&self) -> bool {
        self.0.iter().all(|(_, c)| c.is_zero())
    }

    /// Return the total values of all collaterals.
    pub fn total_value(&self) -> Decimal {
        self.0
            .iter()
            .fold(Decimal::zero(), |acc, (_, c)| acc + c.as_ref())
    }

    pub fn amounts(&self) -> Vec<UnscaledI128> {
        self.0.values().copied().collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_balance_default() {
        let balance = Balance::default();
        assert!(balance.is_zero());
        assert!(balance.is_void());
        // New balance uses a default address with zero balance.
        let balance = Balance::new(Decimal::default().into(), TokenSymbol::USDC);
        assert!(balance.is_zero());
        assert!(balance.is_void());
    }

    #[test]
    fn test_balance_json_serialization() {
        // Default `Balance` is empty, test the serialized json string for an empty balance.
        let balance = Balance::default();
        let balance_json = serde_json::to_string(&balance).unwrap();
        assert_eq!(balance_json.as_str(), "{}");
        let another: Balance = serde_json::from_str(&balance_json).unwrap();
        assert_eq!(another, balance);
    }

    #[test]
    fn test_balance_total_value() {
        let balance = Balance::new(Decimal::ONE_THOUSAND.into(), TokenSymbol::USDC);
        assert_eq!(balance.total_value(), Decimal::ONE_THOUSAND);
    }

    #[test]
    fn test_assign_new_address() {
        // Since the zero balance address will be removed after applying fees, we can reuse the container for new address.
        let mut balance = Balance::new(Decimal::ONE_THOUSAND.into(), TokenSymbol::USDC);
        balance.insert(TokenSymbol::USDC, Decimal::ZERO.into());
        assert!(balance.is_void());
        // Now, the `Balance` is empty, you may apply new amount with new address to it.
        balance.insert(TokenSymbol::DDX, Decimal::ONE_THOUSAND.into());
        assert_eq!(*balance[TokenSymbol::DDX], Decimal::ONE_THOUSAND);
    }

    #[test]
    fn test_balance_apply_works_on_new_token() {
        let mut pool = Balance::default();
        pool.insert(TokenSymbol::USDC, Decimal::ONE.into());
        assert_eq!(*pool[TokenSymbol::USDC], Decimal::ONE)
    }

    #[test]
    fn test_balance_apply_adds_amounts_correctly() {
        let mut pool = Balance::default();
        pool.insert(TokenSymbol::USDC, Decimal::ONE.into());
        pool.insert(
            TokenSymbol::USDC,
            (*pool[TokenSymbol::USDC] + Decimal::ONE).into(),
        );
        assert_eq!(*pool[TokenSymbol::USDC], Decimal::ONE + Decimal::ONE);
    }

    #[test]
    fn test_balance_apply_subs_amounts_correctly() {
        let mut pool = Balance::default();
        pool.insert(TokenSymbol::USDC, Decimal::ONE.into());
        pool.insert(
            TokenSymbol::USDC,
            (*pool[TokenSymbol::USDC] - Decimal::ONE).into(),
        );
        assert_eq!(
            *pool.get_or_default(TokenSymbol::USDC),
            Decimal::ONE - Decimal::ONE
        );
    }
}
