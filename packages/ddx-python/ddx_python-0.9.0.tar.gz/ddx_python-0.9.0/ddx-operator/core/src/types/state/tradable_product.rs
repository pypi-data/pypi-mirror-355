#[cfg(feature = "fixed_expiry_future")]
use crate::specs::quarterly_expiry_future::Quarter;
#[cfg(all(feature = "arbitrary", feature = "fixed_expiry_future"))]
use crate::specs::types::SpecsKind;
#[cfg(feature = "python")]
use crate::types::state::exported;
use crate::{
    specs::types::SpecsKey,
    types::{identifiers::VerifiedStateKey, primitives::ProductSymbol},
};
use alloy_dyn_abi::DynSolValue;
use core_common::{
    B256, Result, ensure, error, types::primitives::Hash, util::tokenize::Tokenizable,
};
use core_macros::AbiToken;
#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "arbitrary")]
use quickcheck::Arbitrary;
use serde::{Deserialize, Serialize};

use super::{ITEM_TRADABLE_PRODUCT, VoidableItem};

#[cfg_eval]
#[derive(
    Debug, Clone, Copy, PartialEq, Serialize, Deserialize, Eq, std::hash::Hash, PartialOrd, Ord,
)]
#[serde(tag = "t", content = "c")]
#[non_exhaustive]
pub enum TradableProductParameters {
    #[cfg(feature = "fixed_expiry_future")]
    QuarterlyExpiryFuture(Quarter),
}

#[cfg(feature = "python")]
impl FromPyObject<'_> for TradableProductParameters {
    fn extract(ob: &PyAny) -> PyResult<Self> {
        let action = ob.extract::<exported::python::TradableProductParameters>()?;
        Ok(action.into())
    }
}

#[cfg(feature = "python")]
impl IntoPy<PyObject> for TradableProductParameters {
    fn into_py(self, py: Python) -> PyObject {
        exported::python::TradableProductParameters::from(self).into_py(py)
    }
}

impl TradableProductParameters {
    fn symbol_extension(&self) -> String {
        match self {
            #[cfg(feature = "fixed_expiry_future")]
            TradableProductParameters::QuarterlyExpiryFuture(quarter) => {
                format!("{}", char::from(*quarter))
            }
            #[allow(unreachable_patterns)]
            _ => unreachable!("Unsupported tradable product parameters"),
        }
    }
}

#[cfg_attr(feature = "python", pyclass(frozen, get_all))]
#[derive(Debug, Clone, PartialEq, Eq, std::hash::Hash, Ord, PartialOrd, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct TradableProductKey {
    pub specs: SpecsKey,
    pub parameters: Option<TradableProductParameters>,
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for TradableProductKey {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        let specs = SpecsKey::arbitrary(g);
        #[cfg(feature = "fixed_expiry_future")]
        if matches!(specs.kind, SpecsKind::QuarterlyExpiryFuture) {
            return TradableProductKey {
                specs,
                parameters: Some(TradableProductParameters::QuarterlyExpiryFuture(
                    Quarter::arbitrary(g),
                )),
            };
        }
        TradableProductKey {
            specs,
            parameters: None,
        }
    }
}

#[cfg(feature = "python")]
#[pymethods]
impl TradableProductKey {
    #[new]
    fn new_py(
        specs: SpecsKey,
        parameters: Option<crate::types::state::exported::python::TradableProductParameters>,
    ) -> Self {
        Self {
            specs,
            parameters: parameters.map(Into::into),
        }
    }
}

impl TradableProductKey {
    const TRADABLE_PRODUCT_KEY_BYTE_LEN: usize = 32;

    pub(crate) fn decode(bytes: &[u8]) -> Result<Self> {
        let specs_len = bytes[0] as usize;
        let specs = SpecsKey::decode(&bytes[1..1 + specs_len])?;
        let parameters_start = 1 + specs_len;
        let coded_parameters = bytes[parameters_start] as usize;
        let parameters = if coded_parameters > 0 {
            #[cfg(feature = "fixed_expiry_future")]
            {
                let quarter = bytes[parameters_start];
                Some(TradableProductParameters::QuarterlyExpiryFuture(
                    quarter.into(),
                ))
            }
            #[cfg(not(feature = "fixed_expiry_future"))]
            {
                None
            }
        } else {
            None
        };
        Ok(TradableProductKey { specs, parameters })
    }

    pub(crate) fn encode(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(Self::TRADABLE_PRODUCT_KEY_BYTE_LEN);
        let encoded = self.specs.encode();
        let encoded_len = encoded.len();
        bytes.push(encoded_len as u8);
        bytes.extend(encoded);
        if let Some(_parameters) = &self.parameters {
            #[cfg(feature = "fixed_expiry_future")]
            {
                let TradableProductParameters::QuarterlyExpiryFuture(quarter) = _parameters;
                bytes.push(*quarter as u8);
            }
            #[cfg(not(feature = "fixed_expiry_future"))]
            bytes.push(0);
        } else {
            bytes.push(0);
        }
        debug_assert!(
            bytes.len() <= Self::TRADABLE_PRODUCT_KEY_BYTE_LEN,
            "Given size {:?} greater than available storage",
            bytes.len()
        );
        bytes
    }
}

impl From<&TradableProductKey> for ProductSymbol {
    fn from(key: &TradableProductKey) -> Self {
        let symbol_str = key.specs.name.replace(
            r#"{}"#,
            &key.parameters.as_ref().map_or_else(
                || "".to_string(),
                |parameters| parameters.symbol_extension(),
            ),
        );
        debug_assert!(
            symbol_str != key.specs.name || key.parameters.is_none(),
            "No place for symbol extension in specs name"
        );
        symbol_str.parse().unwrap()
    }
}

impl From<TradableProductKey> for ProductSymbol {
    fn from(key: TradableProductKey) -> Self {
        Self::from(&key)
    }
}

impl VerifiedStateKey for TradableProductKey {
    fn encode_key(&self) -> Hash {
        let mut bytes = vec![ITEM_TRADABLE_PRODUCT];
        bytes.extend(self.encode());
        debug_assert!(bytes.len() <= 32, "Key length exceeds 32 bytes");
        bytes.resize(32, 0_u8);
        Hash::from_slice(&bytes)
    }

    fn decode_key(value: &Hash) -> Result<Self> {
        let bytes = value.as_bytes();
        ensure!(
            bytes[0] == ITEM_TRADABLE_PRODUCT,
            "Expected a tradable product key, got {:?}",
            bytes[0]
        );
        Self::decode(&bytes[1..])
    }
}

impl Tokenizable for TradableProductKey {
    fn from_token(token: DynSolValue) -> Result<Self>
    where
        Self: Sized,
    {
        let (bytes, size) = token
            .as_fixed_bytes()
            .ok_or_else(|| error!("Expected fixed bytes token"))?;
        ensure!(size == 30, "Not a bytes30 token");
        TradableProductKey::decode(bytes)
    }
    fn into_token(self) -> DynSolValue {
        DynSolValue::FixedBytes(B256::right_padding_from(&self.encode()), size_of::<Self>())
    }
}

#[cfg_attr(feature = "python", pyclass(frozen))]
#[derive(Debug, Default, Clone, PartialEq, Deserialize, Serialize, AbiToken, Eq, Copy)]
#[serde(rename_all = "camelCase")]
#[repr(C)]
pub struct TradableProduct;

#[cfg(feature = "arbitrary")]
impl Arbitrary for TradableProduct {
    fn arbitrary(_: &mut quickcheck::Gen) -> Self {
        TradableProduct
    }
}

impl VoidableItem for TradableProduct {
    fn is_void(&self) -> bool {
        false
    }
}

#[cfg(feature = "python")]
#[pymethods]
impl TradableProduct {
    #[new]
    fn new_py() -> Self {
        TradableProduct
    }
}

#[cfg(all(test, feature = "fixed_expiry_future"))]
mod tests {
    use super::*;
    use crate::specs::types::SpecsKind;

    #[test]
    fn test_encode_decode_tradable_product_key() {
        let parameters = TradableProductParameters::QuarterlyExpiryFuture(Quarter::March);
        let key = TradableProductKey {
            specs: SpecsKey {
                kind: SpecsKind::QuarterlyExpiryFuture,
                name: "QUARTERLYEXPIRYFUTURE-ETHF{}".to_string(),
            },
            parameters: Some(parameters),
        };
        let serialized = key.encode();
        let deserialized: TradableProductKey = TradableProductKey::decode(&serialized).unwrap();
        assert_eq!(key, deserialized);
        let key = TradableProductKey {
            specs: SpecsKey {
                kind: SpecsKind::SingleNamePerpetual,
                name: "BTC".to_string(),
            },
            parameters: None,
        };
        let serialized = key.encode();
        let deserialized: TradableProductKey = TradableProductKey::decode(&serialized).unwrap();
        assert_eq!(key, deserialized);
    }
}
