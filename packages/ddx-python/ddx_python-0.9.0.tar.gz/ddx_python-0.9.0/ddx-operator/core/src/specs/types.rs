#[cfg(all(feature = "arbitrary", feature = "test_harness"))]
use crate::execution::test_utils::{BTCP_MARKET_SPECS, DOGEP_MARKET_SPECS, ETHP_MARKET_SPECS};
#[cfg(feature = "index_fund")]
use crate::specs::index_fund::IndexFundPerpetual;
#[cfg(feature = "fixed_expiry_future")]
use crate::specs::quarterly_expiry_future::QuarterlyExpiryFuture;
use crate::types::{
    identifiers::VerifiedStateKey,
    primitives::ProductSymbol,
    state::{ITEM_SPECS, TradableProductKey, VoidableItem},
};
#[cfg(feature = "fixed_expiry_future")]
use chrono::{DateTime, Utc};
use core_common::{
    Error, Result, ensure, error, types::primitives::Hash, util::tokenize::Tokenizable,
};
use core_macros::AbiToken;
#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "arbitrary")]
use quickcheck::Arbitrary;
use serde::{Deserialize, Serialize, de::Deserializer, ser::Serializer};
use std::{collections::HashMap, fmt, str::FromStr, string::ToString};
use strum_macros::{Display, EnumString};

use super::{MarketGateway, ProductSpecs, SingleNamePerpetual};

pub type Specs = HashMap<SpecsKey, SpecsExpr>;

#[cfg_eval]
#[cfg_attr(feature = "python", pyclass(frozen))]
#[derive(
    Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, std::hash::Hash, Display, EnumString,
)]
#[strum(serialize_all = "UPPERCASE")]
#[non_exhaustive]
pub enum SpecsKind {
    #[strum(serialize = "SINGLENAMEPERP")]
    SingleNamePerpetual,
    #[strum(serialize = "INDEXFUNDPERP")]
    IndexFundPerpetual,
    #[cfg(feature = "fixed_expiry_future")]
    QuarterlyExpiryFuture,
    #[strum(serialize = "GATEWAY")]
    MarketGateway,
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for SpecsKind {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        let discriminant = u8::arbitrary(g) % 3;
        match discriminant {
            0 => SpecsKind::SingleNamePerpetual,
            1 => SpecsKind::IndexFundPerpetual,
            #[cfg(feature = "fixed_expiry_future")]
            2 => SpecsKind::QuarterlyExpiryFuture,
            _ => unreachable!(),
        }
    }
}

impl Serialize for SpecsKind {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        serializer.serialize_str(&self.to_string())
    }
}

impl<'de> Deserialize<'de> for SpecsKind {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        let kind = String::deserialize(deserializer)?;
        kind.parse().map_err(serde::de::Error::custom)
    }
}

impl SpecsKind {
    // TODO: Make sure reordering the discriminants doesn't affect anything on frontend
    pub fn discriminant(&self) -> u8 {
        match self {
            SpecsKind::SingleNamePerpetual => 0,
            SpecsKind::MarketGateway => 1,
            SpecsKind::IndexFundPerpetual => 2,
            #[cfg(feature = "fixed_expiry_future")]
            SpecsKind::QuarterlyExpiryFuture => 3,
        }
    }
}

impl From<u8> for SpecsKind {
    fn from(value: u8) -> Self {
        match value {
            0 => SpecsKind::SingleNamePerpetual,
            1 => SpecsKind::MarketGateway,
            2 => SpecsKind::IndexFundPerpetual,
            #[cfg(feature = "fixed_expiry_future")]
            3 => SpecsKind::QuarterlyExpiryFuture,
            _ => panic!("Unexpected specs kind discriminant {:?}", value),
        }
    }
}

/// Specs expression.
///
/// This has no constructor. We always instantiate by parsing the specs expression and never edit
/// the specs data directly.
#[cfg_attr(feature = "python", derive(FromPyObject))]
#[derive(Clone, Debug, PartialEq, Deserialize, Serialize, Eq, Default)]
pub struct SpecsExpr(String);

#[cfg(feature = "python")]
impl IntoPy<PyObject> for SpecsExpr {
    fn into_py(self, py: Python) -> PyObject {
        self.0.into_py(py)
    }
}

impl VoidableItem for SpecsExpr {
    fn is_void(&self) -> bool {
        self.0.is_empty()
    }
}

impl SpecsExpr {
    pub fn new(expr: String) -> Self {
        SpecsExpr(expr)
    }

    pub fn empty() -> Self {
        SpecsExpr("".to_string())
    }

    pub fn is_some(&self) -> bool {
        !self.0.is_empty()
    }

    pub fn as_str(&self) -> &str {
        self.0.as_str()
    }

    pub fn as_market_gateway(&self) -> Result<MarketGateway> {
        MarketGateway::from_str(self.as_str())
            .map_err(|e| Error::Parse(format!("Cannot parse {:?}", e)))
    }

    pub fn as_product_specs(&self, specs_kind: SpecsKind) -> Result<ProductSpecs> {
        match specs_kind {
            SpecsKind::SingleNamePerpetual => {
                SingleNamePerpetual::from_str(self.as_str()).map(ProductSpecs::SingleNamePerpetual)
            }
            #[cfg(feature = "index_fund")]
            SpecsKind::IndexFundPerpetual => {
                IndexFundPerpetual::from_str(self.as_str()).map(ProductSpecs::IndexFundPerpetual)
            }
            #[cfg(feature = "fixed_expiry_future")]
            SpecsKind::QuarterlyExpiryFuture => QuarterlyExpiryFuture::from_str(self.as_str())
                .map(ProductSpecs::QuarterlyExpiryFuture),
            _ => Err(error!("Cannot convert other specs expr to product specs")),
        }
    }
}

impl fmt::Display for SpecsExpr {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl<T: AsRef<str>> From<T> for SpecsExpr {
    fn from(expr: T) -> Self {
        SpecsExpr(expr.as_ref().to_string())
    }
}

impl Tokenizable for SpecsExpr {
    fn from_token(token: alloy_dyn_abi::DynSolValue) -> Result<Self>
    where
        Self: Sized,
    {
        let expr = token
            .as_str()
            .ok_or_else(|| error!("Invalid specs expression"))?;
        Ok(SpecsExpr(expr.to_string()))
    }

    fn into_token(self) -> alloy_dyn_abi::DynSolValue {
        // We store the original expression instead of generating a new one.
        alloy_dyn_abi::DynSolValue::String(self.0)
    }
}

#[cfg(all(feature = "arbitrary", feature = "test_harness"))]
impl Arbitrary for SpecsExpr {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        // TODO: Create an actual fuzzer for specs to use here and also validate the parser.
        let expr = g
            .choose(&[BTCP_MARKET_SPECS, ETHP_MARKET_SPECS, DOGEP_MARKET_SPECS])
            .map(|s| s.to_string())
            .unwrap();
        SpecsExpr(expr)
    }
}

/// Common key for all specs kind.
#[cfg_attr(feature = "python", pyclass(frozen, get_all))]
#[derive(Debug, Clone, PartialEq, Eq, std::hash::Hash, PartialOrd, Ord, Deserialize, Serialize)]
pub struct SpecsKey {
    pub kind: SpecsKind,
    /// Defined by convention associated with the specs kind.
    /// At the time of writing, the naming conventions are:
    ///
    /// - `SingleNamePerpetual`: The product market symbol for the single name perpetuals in our universe (e.g. ETHP, BTCP).
    /// - `MarketGateway`: The host name (e.g. api.binance.com, api.exchange.coinbase.com).
    pub name: String,
}

#[cfg(feature = "python")]
#[pymethods]
impl SpecsKey {
    #[new]
    pub(crate) fn new_py(kind: SpecsKind, name: String) -> PyResult<Self> {
        Ok(Self::new(kind, name)?)
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for SpecsKey {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        SpecsKey {
            kind: SpecsKind::arbitrary(g),
            name: String::arbitrary(g),
        }
    }
}

impl SpecsKey {
    // The first byte is the kind of specs and the second type is the length of the name.
    const SPEC_KEY_BYTE_LEN: usize = 30;

    fn new(kind: SpecsKind, name: String) -> Result<Self> {
        ensure!(name.len() <= 28, "Specs name too long {}", name);
        Ok(SpecsKey { kind, name })
    }

    pub fn market_gateway<T: AsRef<str>>(id: T) -> Self {
        let id = id.as_ref();
        assert!(id.len() <= 28, "Specs name too long {}", id);
        SpecsKey {
            kind: SpecsKind::MarketGateway,
            name: id.to_string(),
        }
    }

    pub fn single_name_perpetual<T: Into<ProductSymbol>>(symbol: T) -> Self {
        let symbol: ProductSymbol = symbol.into();
        SpecsKey {
            kind: SpecsKind::SingleNamePerpetual,
            name: symbol.to_string(),
        }
    }

    #[cfg(feature = "index_fund")]
    pub fn index_fund_perpetual<T: Into<ProductSymbol>>(symbol: T) -> Self {
        let symbol: ProductSymbol = symbol.into();
        SpecsKey {
            kind: SpecsKind::IndexFundPerpetual,
            name: symbol.to_string(),
        }
    }

    pub(crate) fn decode(bytes: &[u8]) -> Result<Self> {
        let kind = SpecsKind::from(bytes[0]);
        let size = bytes[1] as usize;

        ensure!(
            size <= 28,
            "Given size greater than available storage {:?}",
            bytes
        );
        let name = String::from_utf8_lossy(&bytes[2..size + 2]).to_string();
        Ok(SpecsKey { kind, name })
    }

    pub(crate) fn encode(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(Self::SPEC_KEY_BYTE_LEN);
        // Specs kind discriminant
        bytes.push(self.kind.discriminant());
        debug_assert!(
            self.name.len() <= Self::SPEC_KEY_BYTE_LEN - 2,
            "Given size {:?} greater than available storage",
            self.name.len()
        );
        // We've verified the size on construction so this cast is safe.
        bytes.push(self.name.len() as u8);
        // Max 28 utf-8 bytes left for the name
        bytes.extend_from_slice(self.name.as_bytes());
        bytes
    }

    pub fn current_tradable_products(
        &self,
        #[cfg(feature = "fixed_expiry_future")] current_time: DateTime<Utc>,
    ) -> Vec<TradableProductKey> {
        let res = match self.kind {
            SpecsKind::MarketGateway => return Vec::new(),
            #[cfg(feature = "fixed_expiry_future")]
            SpecsKind::QuarterlyExpiryFuture => {
                QuarterlyExpiryFuture::current_tradable_products(self.clone(), current_time)
            }
            _ => vec![TradableProductKey {
                specs: self.clone(),
                parameters: None,
            }],
        };
        debug_assert!(
            !res.is_empty(),
            "Expected at least one tradable product for any existing spec"
        );
        tracing::debug!("Current tradable products: {:?}", res);
        res
    }

    pub fn has_lifecycle(&self) -> Option<bool> {
        Some(match self.kind {
            SpecsKind::MarketGateway => return None,
            #[cfg(feature = "fixed_expiry_future")]
            SpecsKind::QuarterlyExpiryFuture => true,
            _ => false,
        })
    }
}

impl FromStr for SpecsKey {
    type Err = Error;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let (kind_label, name) = s
            .split_once('-')
            .ok_or_else(|| Error::Parse("Expected [KIND]-[NAME] scheme".to_string()))?;
        let kind = kind_label.parse::<SpecsKind>()?;
        SpecsKey::new(kind, name.to_string())
    }
}

impl fmt::Display for SpecsKey {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}-{}", self.kind, self.name)
    }
}

impl VerifiedStateKey for SpecsKey {
    fn encode_key(&self) -> Hash {
        let mut bytes = vec![
            ITEM_SPECS,
            core_common::types::identifiers::ChainVariant::Ethereum.discriminant(),
        ];
        // Get the last 30 bytes by encoding the key.
        bytes.extend(self.encode());
        bytes.resize(32, 0_u8);
        Hash::from_slice(&bytes)
    }

    fn decode_key(value: &Hash) -> Result<Self> {
        let bytes = value.as_bytes();
        ensure!(
            bytes[0] == ITEM_SPECS,
            "Expected a specs key, got {:?}",
            bytes[0]
        );
        ensure!(
            bytes[1] == core_common::types::identifiers::ChainVariant::Ethereum.discriminant(),
            "Expected the Ethereum chain discriminant, got {:?}",
            bytes[1]
        );
        Self::decode(&bytes[2..])
    }
}

impl Tokenizable for SpecsKey {
    fn from_token(token: alloy_dyn_abi::DynSolValue) -> Result<Self>
    where
        Self: Sized,
    {
        let (bytes, size) = token
            .as_fixed_bytes()
            .ok_or_else(|| error!("Expected fixed bytes token"))?;
        ensure!(size == 30, "Expected bytes30 token for SpecsKey");
        SpecsKey::decode(bytes)
    }

    fn into_token(self) -> alloy_dyn_abi::DynSolValue {
        alloy_dyn_abi::DynSolValue::FixedBytes(
            alloy_primitives::B256::right_padding_from(self.encode().as_slice()),
            30,
        )
    }
}

#[derive(Debug, Clone, PartialEq, Deserialize, Serialize, AbiToken)]
#[serde(rename_all = "camelCase")]
pub struct SpecsUpdate {
    pub key: SpecsKey,
    pub expr: SpecsExpr,
    // TODO: BlockTxStamp with flatten
    pub block_number: u64,
    pub tx_hash: Hash,
}
