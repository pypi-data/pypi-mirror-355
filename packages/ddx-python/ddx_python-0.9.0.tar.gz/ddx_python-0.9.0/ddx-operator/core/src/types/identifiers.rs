use crate::types::{
    primitives::{Bytes4, Bytes25, IndexPriceHash, OrderHash, ProductSymbol},
    state::{
        ITEM_BOOK_ORDER, ITEM_EPOCH_METADATA, ITEM_INSURANCE_FUND,
        ITEM_INSURANCE_FUND_CONTRIBUTION, ITEM_POSITION, ITEM_PRICE, ITEM_SIGNER, ITEM_STATS,
        ITEM_STRATEGY, ITEM_TRADER,
    },
};

use alloy_dyn_abi::DynSolValue;
use alloy_primitives::FixedBytes;
#[cfg(feature = "python")]
use core_common::types::primitives::from_hex;
use core_common::{
    Address, Result, ensure,
    types::{
        accounting::StrategyId,
        primitives::{Bytes21, Hash, Keccak256, TraderAddress},
        transaction::EpochId,
    },
    util::tokenize::Tokenizable,
};
use core_macros::{AbiToken, FixedBytesWrapper};
#[cfg(feature = "database")]
use postgres_types::{FromSql, IsNull, ToSql, Type, to_sql_checked};
#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "arbitrary")]
use quickcheck::Arbitrary;
use rust_decimal::prelude::Zero;
use rustc_hex::ToHex;
use serde::{Deserialize, Serialize};
use std::{
    convert::From,
    fmt::{self, Formatter},
};

fn build_trader_group_key(item_kind: u8, trader_address: &TraderAddress) -> Vec<u8> {
    let mut bytes = vec![item_kind];
    bytes.extend_from_slice(trader_address.as_bytes());
    bytes
}

fn build_market_group_key(item_kind: u8, symbol: &ProductSymbol) -> Vec<u8> {
    let mut bytes = vec![item_kind];
    // TODO: Consider passing the chain discriminant instead of reading a global
    bytes.extend_from_slice(symbol.0.as_slice());
    bytes
}

fn decode_bytes21_key(value: &Hash, discriminant: u8) -> Result<Bytes21> {
    // Starting with a vector of 32 bytes to split off in parts
    let bytes = value.as_bytes();
    ensure!(
        bytes[0] == discriminant,
        "Expected discriminant {:?}, got {:?}",
        discriminant,
        bytes[0]
    );
    let bytes21 = Bytes21::from_slice(&bytes[1..22]);
    ensure!(
        bytes[22..].iter().all(|x| x.is_zero()),
        "Expected only zeroes to remain after extracting the trader address"
    );
    Ok(bytes21)
}

pub trait VerifiedStateKey {
    /// Generates a verified state (smt) key based on the impl type
    ///
    /// A verified state key is essentially an encoded representation of a data structure.
    /// This functions contains the type-specific encoding logic. Contrarily to hash,
    /// this custom encoding is bi-directional.
    fn encode_key(&self) -> Hash;

    fn decode_key(value: &Hash) -> Result<Self>
    where
        Self: Sized;
}

impl VerifiedStateKey for TraderAddress {
    fn encode_key(&self) -> Hash {
        let mut bytes = build_trader_group_key(ITEM_TRADER, self);
        bytes.resize(32, 0_u8);
        Hash::from_slice(&bytes)
    }

    fn decode_key(value: &Hash) -> Result<Self> {
        decode_bytes21_key(value, ITEM_TRADER)
    }
}

#[cfg_attr(feature = "python", pyclass(frozen, get_all))]
#[derive(
    Debug,
    Clone,
    Copy,
    Default,
    PartialEq,
    Eq,
    std::hash::Hash,
    PartialOrd,
    Ord,
    Deserialize,
    Serialize,
    AbiToken,
)]
pub struct StatsKey {
    pub trader: TraderAddress,
}

#[cfg(feature = "python")]
#[pymethods]
impl StatsKey {
    #[new]
    fn new_py(trader: TraderAddress) -> Self {
        Self::new(trader)
    }
}

impl VerifiedStateKey for StatsKey {
    fn encode_key(&self) -> Hash {
        let mut bytes = build_trader_group_key(ITEM_STATS, &self.trader);
        bytes.resize(32, 0_u8);
        Hash::from_slice(&bytes)
    }

    fn decode_key(value: &Hash) -> Result<Self> {
        // Starting with a vector of 32 bytes to split off in parts
        let bytes = value.as_bytes();
        ensure!(
            bytes[0] == ITEM_STATS,
            "Expected a stats key, got {:?}",
            bytes[0]
        );
        let trader_address = TraderAddress::from_slice(&bytes[1..22]);
        ensure!(
            bytes[22..].iter().all(|x| x.is_zero()),
            "Expected only zeroes to remain after extracting the trader address"
        );
        Ok(StatsKey {
            trader: trader_address,
        })
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for StatsKey {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Self {
            trader: Arbitrary::arbitrary(g),
        }
    }
}

impl StatsKey {
    pub fn new(trader: TraderAddress) -> Self {
        StatsKey { trader }
    }
}

impl From<StatsKey> for Hash {
    fn from(val: StatsKey) -> Self {
        let token = DynSolValue::Tuple(vec!["Trader Stats".to_string().into(), val.into_token()]);
        let message = token.abi_encode();
        let hash = message.keccak256();
        hash.into()
    }
}

#[derive(
    Clone,
    Copy,
    PartialEq,
    Eq,
    std::hash::Hash,
    PartialOrd,
    Ord,
    Deserialize,
    Serialize,
    FixedBytesWrapper,
)]
#[serde(transparent)]
pub struct StrategyIdHash(FixedBytes<4>);

impl From<StrategyId> for StrategyIdHash {
    fn from(value: StrategyId) -> Self {
        // Parse deterministically because the string length is validated upon instantiation
        let fixed_bytes = value.0.as_bytes().keccak256();
        StrategyIdHash::from_slice(&fixed_bytes[..4])
    }
}

#[cfg(feature = "python")]
impl FromPyObject<'_> for StrategyIdHash {
    fn extract(ob: &PyAny) -> PyResult<Self> {
        let text = ob.extract::<String>()?;
        Ok(from_hex(text).and_then(|v| StrategyIdHash::try_from_slice(&v))?)
    }
}

#[cfg(feature = "python")]
impl IntoPy<PyObject> for StrategyIdHash {
    fn into_py(self, py: Python) -> PyObject {
        self.to_string().into_py(py)
    }
}

impl Tokenizable for StrategyIdHash {
    fn from_token(token: DynSolValue) -> Result<Self> {
        let token_bytes4 = Bytes4::from_token(token)?;
        Ok(StrategyIdHash::from_slice(
            &token_bytes4.as_bytes()[..Self::BYTE_LEN],
        ))
    }
    fn into_token(self) -> DynSolValue {
        let bytes = Bytes4::from(self);
        bytes.into_token()
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for StrategyIdHash {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        let size: i32 = *g
            .choose(&(0..Self::BYTE_LEN as i32).collect::<Vec<i32>>())
            .unwrap();
        let label: String = (0..size).map(|_| char::arbitrary(g)).collect();
        StrategyId::from_string(label).unwrap().into()
    }
}

impl Default for StrategyIdHash {
    fn default() -> Self {
        StrategyId::default().into()
    }
}

impl From<StrategyIdHash> for Bytes4 {
    fn from(value: StrategyIdHash) -> Self {
        Bytes4(value.0)
    }
}

#[cfg(feature = "test_harness")]
impl From<&str> for StrategyIdHash {
    fn from(value: &str) -> Self {
        let strategy_id: StrategyId = value.into();
        strategy_id.into()
    }
}

// Also implements `ToString` for free
impl fmt::Display for StrategyIdHash {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        write!(f, "0x{}", self.0.to_hex::<String>())
    }
}

impl fmt::Debug for StrategyIdHash {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_tuple("StrategyIdHash")
            .field(&self.to_string())
            .finish()
    }
}

#[cfg(feature = "database")]
impl ToSql for StrategyIdHash {
    fn to_sql(
        &self,
        ty: &Type,
        out: &mut bytes::BytesMut,
    ) -> Result<IsNull, Box<dyn std::error::Error + 'static + Sync + Send>> {
        self.0.to_vec().to_sql(ty, out)
    }

    fn accepts(ty: &Type) -> bool {
        <Vec<u8> as ToSql>::accepts(ty)
    }

    to_sql_checked!();
}

#[cfg(feature = "database")]
impl<'a> FromSql<'a> for StrategyIdHash {
    fn from_sql(
        ty: &Type,
        raw: &'a [u8],
    ) -> Result<Self, Box<dyn std::error::Error + Sync + Send>> {
        let bytes: Vec<u8> = Vec::from_sql(ty, raw)?;
        Ok(StrategyIdHash::from_slice(&bytes[..4]))
    }

    fn accepts(ty: &Type) -> bool {
        <Vec<u8> as FromSql>::accepts(ty)
    }
}

#[cfg_attr(feature = "python", pyclass(frozen, get_all))]
#[cfg_attr(feature = "test_harness", derive(Default))]
#[derive(
    Debug,
    Clone,
    Copy,
    PartialEq,
    Eq,
    std::hash::Hash,
    PartialOrd,
    Ord,
    Deserialize,
    Serialize,
    AbiToken,
)]
#[serde(rename_all = "camelCase")]
pub struct StrategyKey {
    pub trader_address: TraderAddress,
    pub strategy_id_hash: StrategyIdHash,
}

#[cfg(feature = "python")]
#[pymethods]
impl StrategyKey {
    #[new]
    pub(crate) fn new_py(trader_address: TraderAddress, strategy_id_hash: StrategyIdHash) -> Self {
        Self::new(trader_address, strategy_id_hash)
    }
}

impl StrategyKey {
    pub fn new<T: Into<TraderAddress>, H: Into<StrategyIdHash>>(
        trader_address: T,
        strategy_id_hash: H,
    ) -> Self {
        StrategyKey {
            trader_address: trader_address.into(),
            strategy_id_hash: strategy_id_hash.into(),
        }
    }

    #[cfg(feature = "test_harness")]
    pub fn main<T: Into<TraderAddress>>(trader: T) -> StrategyKey {
        StrategyKey {
            trader_address: trader.into(),
            strategy_id_hash: StrategyIdHash::default(),
        }
    }

    pub fn as_position_key<S: Into<ProductSymbol>>(&self, symbol: S) -> PositionKey {
        PositionKey {
            trader_address: self.trader_address,
            strategy_id_hash: self.strategy_id_hash,
            symbol: symbol.into(),
        }
    }
}

impl From<(TraderAddress, StrategyIdHash)> for StrategyKey {
    fn from(k: (TraderAddress, StrategyIdHash)) -> Self {
        StrategyKey {
            trader_address: k.0,
            strategy_id_hash: k.1,
        }
    }
}

impl VerifiedStateKey for StrategyKey {
    fn encode_key(&self) -> Hash {
        let mut bytes = build_trader_group_key(ITEM_STRATEGY, &self.trader_address);
        bytes.extend_from_slice(self.strategy_id_hash.0.as_slice());
        bytes.resize(32, 0_u8);
        Hash::from_slice(&bytes)
    }

    fn decode_key(value: &Hash) -> Result<Self> {
        tracing::trace!("Decoding strategy key {:?}", value);
        let bytes = value.as_bytes();
        ensure!(
            bytes[0] == ITEM_STRATEGY,
            "Expected a strategy key, got {:?}",
            bytes[0]
        );
        let trader_address = TraderAddress::from_slice(&bytes[1..22]);
        let strategy_id_hash = StrategyIdHash::from_slice(&bytes[22..26]);
        ensure!(
            bytes[26..].iter().all(|x| x.is_zero()),
            "Expected only zeroes to remain after extracting the trader address"
        );
        Ok(StrategyKey {
            trader_address,
            strategy_id_hash,
        })
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for StrategyKey {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Self {
            trader_address: Arbitrary::arbitrary(g),
            strategy_id_hash: Arbitrary::arbitrary(g),
        }
    }
}

#[cfg_attr(feature = "python", pyclass(frozen, get_all))]
#[cfg_attr(feature = "test_harness", derive(Default))]
#[derive(
    Debug,
    Clone,
    Copy,
    PartialEq,
    Eq,
    std::hash::Hash,
    Ord,
    PartialOrd,
    AbiToken,
    Deserialize,
    Serialize,
)]
#[serde(rename_all = "camelCase")]
pub struct PositionKey {
    pub trader_address: TraderAddress,
    pub strategy_id_hash: StrategyIdHash,
    pub symbol: ProductSymbol,
}

#[cfg(feature = "python")]
#[pymethods]
impl PositionKey {
    #[new]
    fn new_py(
        trader_address: TraderAddress,
        strategy_id_hash: StrategyIdHash,
        symbol: ProductSymbol,
    ) -> Self {
        Self::new(trader_address, strategy_id_hash, symbol)
    }
}

impl PositionKey {
    pub fn new<A: Into<TraderAddress>, H: Into<StrategyIdHash>, S: Into<ProductSymbol>>(
        trader_address: A,
        strategy_id_hash: H,
        symbol: S,
    ) -> Self {
        PositionKey {
            trader_address: trader_address.into(),
            strategy_id_hash: strategy_id_hash.into(),
            symbol: symbol.into(),
        }
    }
}

impl VerifiedStateKey for PositionKey {
    fn encode_key(&self) -> Hash {
        let mut bytes = build_market_group_key(ITEM_POSITION, &self.symbol);
        bytes.extend_from_slice(self.trader_address.as_bytes());
        bytes.extend_from_slice(self.strategy_id_hash.0.as_slice());
        Hash::from_slice(&bytes)
    }

    fn decode_key(value: &Hash) -> Result<Self> {
        let bytes = value.as_bytes();
        ensure!(
            bytes[0] == ITEM_POSITION,
            "Expected a position key, got {:?}",
            bytes[0]
        );
        let symbol = ProductSymbol::from_slice(&bytes[1..7])?;
        let trader_address = TraderAddress::from_slice(&bytes[7..28]);
        let strategy_id_hash = StrategyIdHash::from_slice(&bytes[28..]);
        Ok(PositionKey {
            trader_address,
            strategy_id_hash,
            symbol,
        })
    }
}

impl From<PositionKey> for StrategyKey {
    fn from(value: PositionKey) -> Self {
        StrategyKey {
            trader_address: value.trader_address,
            strategy_id_hash: value.strategy_id_hash,
        }
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for PositionKey {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Self {
            trader_address: TraderAddress::arbitrary(g),
            strategy_id_hash: StrategyIdHash::arbitrary(g),
            symbol: ProductSymbol::arbitrary(g),
        }
    }
}

#[cfg_attr(feature = "python", pyclass(frozen, get_all))]
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, std::hash::Hash, PartialOrd, Ord)]
pub struct BookOrderKey {
    pub symbol: ProductSymbol,
    pub order_hash: OrderHash,
}

#[cfg(feature = "python")]
#[pymethods]
impl BookOrderKey {
    #[new]
    fn new_py(symbol: ProductSymbol, order_hash: OrderHash) -> Self {
        Self::new(symbol, order_hash)
    }
}

impl BookOrderKey {
    pub fn new<S: Into<ProductSymbol>>(symbol: S, order_hash: OrderHash) -> Self {
        BookOrderKey {
            symbol: symbol.into(),
            order_hash,
        }
    }
}

impl VerifiedStateKey for BookOrderKey {
    fn encode_key(&self) -> Hash {
        let mut bytes = build_market_group_key(ITEM_BOOK_ORDER, &self.symbol);
        bytes.extend_from_slice(self.order_hash.as_bytes());
        Hash::from_slice(&bytes)
    }

    fn decode_key(value: &Hash) -> Result<Self> {
        let bytes = value.as_bytes();
        ensure!(
            bytes[0] == ITEM_BOOK_ORDER,
            "Expected a book order key, got {:?}",
            bytes[0]
        );
        let symbol = ProductSymbol::from_slice(&bytes[1..7])?;
        let mut order_hash_bytes = vec![];
        order_hash_bytes.extend_from_slice(&bytes[7..]);
        let abbrev_order_hash = Bytes25::from_slice(&order_hash_bytes);
        Ok(BookOrderKey {
            symbol,
            order_hash: abbrev_order_hash,
        })
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for BookOrderKey {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Self {
            symbol: ProductSymbol::arbitrary(g),
            order_hash: Bytes25::arbitrary(g),
        }
    }
}

#[cfg_attr(feature = "python", pyclass(frozen, get_all))]
#[derive(
    Debug,
    Clone,
    Copy,
    Default,
    PartialEq,
    Eq,
    std::hash::Hash,
    Serialize,
    Deserialize,
    PartialOrd,
    Ord,
)]
#[serde(rename_all = "camelCase")]
pub struct PriceKey {
    pub symbol: ProductSymbol,
    pub index_price_hash: IndexPriceHash,
}

#[cfg(feature = "python")]
#[pymethods]
impl PriceKey {
    #[new]
    fn new_py(symbol: ProductSymbol, index_price_hash: IndexPriceHash) -> Self {
        Self::new(symbol, index_price_hash)
    }
}

impl PriceKey {
    pub fn new<S: Into<ProductSymbol>>(symbol: S, index_price_hash: IndexPriceHash) -> Self {
        PriceKey {
            symbol: symbol.into(),
            index_price_hash,
        }
    }
}

impl VerifiedStateKey for PriceKey {
    fn encode_key(&self) -> Hash {
        let mut bytes = build_market_group_key(ITEM_PRICE, &self.symbol);
        bytes.extend_from_slice(self.index_price_hash.as_bytes());
        Hash::from_slice(&bytes)
    }

    fn decode_key(value: &Hash) -> Result<Self> {
        let bytes = value.as_bytes();
        ensure!(
            bytes[0] == ITEM_PRICE,
            "Expected a price key, got {:?}",
            bytes[0]
        );
        let symbol = ProductSymbol::from_slice(&bytes[1..7])?;
        let mut index_price_hash = vec![];
        index_price_hash.extend_from_slice(&bytes[7..]);
        let abbrev_order_hash = Bytes25::from_slice(&index_price_hash);
        Ok(PriceKey {
            symbol,
            index_price_hash: abbrev_order_hash,
        })
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for PriceKey {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Self {
            symbol: Arbitrary::arbitrary(g),
            index_price_hash: Arbitrary::arbitrary(g),
        }
    }
}

#[cfg_attr(feature = "python", pyclass(frozen))]
#[derive(Debug, Clone, Default, PartialEq, Eq, std::hash::Hash, Ord, PartialOrd)]
pub struct InsuranceFundKey([u8; 31]); // TODO: Static value placeholder pending enhancements

#[cfg(feature = "python")]
#[pymethods]
impl InsuranceFundKey {
    #[new]
    fn new_py() -> Self {
        Self::new()
    }
}

impl InsuranceFundKey {
    pub fn new() -> Self {
        // Encoding using the `from_utf8` function
        let mut bytes = "OrganicInsuranceFund".as_bytes().to_vec();
        bytes.resize(31, 0_u8);
        let mut fixed_bytes = [0_u8; 31];
        fixed_bytes.copy_from_slice(&bytes);
        InsuranceFundKey(fixed_bytes)
    }
}

impl VerifiedStateKey for InsuranceFundKey {
    fn encode_key(&self) -> Hash {
        let mut bytes = vec![ITEM_INSURANCE_FUND];
        bytes.extend_from_slice(self.0.as_slice());
        Hash::from_slice(&bytes)
    }

    fn decode_key(value: &Hash) -> Result<Self> {
        let bytes = value.as_bytes();
        ensure!(
            bytes[0] == ITEM_INSURANCE_FUND,
            "Expected an insurance fund key, got {:?}",
            bytes[0],
        );
        Ok(InsuranceFundKey::new())
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for InsuranceFundKey {
    fn arbitrary(_g: &mut quickcheck::Gen) -> Self {
        Self::new()
    }
}

#[cfg_attr(feature = "python", derive(FromPyObject))]
#[derive(
    Clone, Copy, Default, PartialEq, Eq, Hash, Deserialize, Serialize, AbiToken, PartialOrd, Ord,
)]
pub struct InsuranceFundContributorAddress(pub Bytes21);

#[cfg(feature = "arbitrary")]
impl Arbitrary for InsuranceFundContributorAddress {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Self(Bytes21::arbitrary(g))
    }
}

impl VerifiedStateKey for InsuranceFundContributorAddress {
    fn encode_key(&self) -> Hash {
        let mut bytes = build_trader_group_key(ITEM_INSURANCE_FUND_CONTRIBUTION, &self.0);
        bytes.resize(32, 0_u8);
        Hash::from_slice(&bytes)
    }

    fn decode_key(value: &Hash) -> Result<Self> {
        Ok(Self(decode_bytes21_key(
            value,
            ITEM_INSURANCE_FUND_CONTRIBUTION,
        )?))
    }
}

impl fmt::Debug for InsuranceFundContributorAddress {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        f.debug_tuple("InsuranceFundContributorAddress")
            .field(&format!("0x{}", self.0.as_bytes().to_hex::<String>()))
            .finish()
    }
}

impl fmt::Display for InsuranceFundContributorAddress {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        let hex = self.0.as_bytes().to_hex::<String>();
        write!(f, "0x{}..{}", &hex[2..5], &hex[hex.len() - 2..])
    }
}

impl From<Bytes21> for InsuranceFundContributorAddress {
    fn from(bytes: Bytes21) -> Self {
        Self(bytes)
    }
}

impl From<&str> for InsuranceFundContributorAddress {
    fn from(value: &str) -> Self {
        Self(Bytes21::parse_eth_address(value).unwrap())
    }
}

#[cfg_attr(feature = "python", derive(FromPyObject))]
#[derive(
    Clone,
    Copy,
    Default,
    PartialEq,
    Eq,
    Deserialize,
    Serialize,
    AbiToken,
    std::hash::Hash,
    PartialOrd,
    Ord,
)]
pub struct SignerAddress(pub Bytes21);

#[cfg(feature = "arbitrary")]
impl Arbitrary for SignerAddress {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Self(Bytes21::arbitrary(g))
    }
}

impl<T: Into<Bytes21> + Copy> From<&T> for SignerAddress {
    fn from(value: &T) -> Self {
        Self((*value).into())
    }
}

impl VerifiedStateKey for SignerAddress {
    fn encode_key(&self) -> Hash {
        let mut bytes = build_trader_group_key(ITEM_SIGNER, &self.0);
        bytes.resize(32, 0_u8);
        Hash::from_slice(&bytes)
    }

    fn decode_key(value: &Hash) -> Result<Self> {
        Ok(Self(decode_bytes21_key(value, ITEM_SIGNER)?))
    }
}

impl fmt::Debug for SignerAddress {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        f.debug_tuple("SignerAddress")
            .field(&format!("0x{}", self.0.as_bytes().to_hex::<String>()))
            .finish()
    }
}

impl fmt::Display for SignerAddress {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        let hex = self.0.as_bytes().to_hex::<String>();
        write!(f, "0x{}..{}", &hex[2..5], &hex[hex.len() - 2..])
    }
}

impl From<Bytes21> for SignerAddress {
    fn from(bytes: Bytes21) -> Self {
        Self(bytes)
    }
}

impl From<Address> for SignerAddress {
    fn from(address: Address) -> Self {
        Self(address.into())
    }
}

impl From<&str> for SignerAddress {
    fn from(value: &str) -> Self {
        Self(Bytes21::parse_eth_address(value).unwrap())
    }
}

#[cfg_attr(feature = "python", pyclass(frozen, get_all))]
#[derive(Debug, Clone, Default, PartialEq, Eq, std::hash::Hash, Ord, PartialOrd)]
pub struct EpochMetadataKey {
    pub epoch_id: u64,
}

#[cfg(feature = "python")]
#[pymethods]
impl EpochMetadataKey {
    #[new]
    fn new_py(epoch_id: EpochId) -> Self {
        Self::new(&epoch_id)
    }
}

impl EpochMetadataKey {
    pub fn new(epoch: &EpochId) -> Self {
        EpochMetadataKey { epoch_id: *epoch }
    }
}

impl VerifiedStateKey for EpochMetadataKey {
    fn encode_key(&self) -> Hash {
        let mut bytes = vec![ITEM_EPOCH_METADATA];
        bytes.extend_from_slice(&self.epoch_id.to_be_bytes());
        bytes.resize(32, 0_u8);
        Hash::from_slice(&bytes)
    }

    fn decode_key(value: &Hash) -> Result<Self> {
        let bytes = value.as_bytes();
        ensure!(
            bytes[0] == ITEM_EPOCH_METADATA,
            "Expected a EpochMetadata key, got {:?}",
            bytes[0],
        );
        let mut epoch_id = [0_u8; 8];
        epoch_id.copy_from_slice(&bytes[1..9]);
        ensure!(
            bytes[9..].iter().all(|x| x.is_zero()),
            "Expected only zeroes to remain after extracting the epoch ID"
        );
        Ok(u64::from_be_bytes(epoch_id).into())
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for EpochMetadataKey {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Self {
            epoch_id: Arbitrary::arbitrary(g),
        }
    }
}

impl From<u64> for EpochMetadataKey {
    fn from(value: u64) -> Self {
        Self { epoch_id: value }
    }
}

#[cfg(test)]
pub mod tests {
    use super::*;
    use crate::{
        execution::test_utils::ETHP,
        specs::types::{SpecsKey, SpecsKind},
        types::{
            identifiers::VerifiedStateKey,
            primitives::{Product, ProductSymbol, UnderlyingSymbol},
            state::{ITEM_TRADABLE_PRODUCT, TradableProductKey},
        },
    };
    use alloy_dyn_abi::DynSolType;
    use core_common::util::tokenize::generate_schema;
    use core_crypto::test_accounts::{ALICE, BOB};
    use quickcheck::QuickCheck;
    use std::str::FromStr;

    #[test]
    #[should_panic]
    fn test_underlying_symbol() {
        let symbol = "ETH".parse::<UnderlyingSymbol>().unwrap();
        assert_eq!(symbol.trim().len(), 3);
        assert_eq!(symbol.to_string().len(), 3);
        let symbol = "BTC".parse::<UnderlyingSymbol>().unwrap();
        assert_eq!(symbol.trim().len(), 3);
        let symbol = "BULL".parse::<UnderlyingSymbol>().unwrap();
        assert_eq!(symbol.trim().len(), 4);
        // Illegal chars should fail (including digits at the moment)
        assert!("BUL1".parse::<UnderlyingSymbol>().is_err());
        // More than 4 chars should fail
        "PRIVACY".parse::<UnderlyingSymbol>().unwrap();
    }

    #[test]
    #[core_macros::setup]
    fn test_product_symbol() {
        let symbol = ProductSymbol::from_str("ETHP").unwrap();
        assert_eq!(symbol.to_string().len(), 4);
        assert_eq!(
            symbol.split(),
            (
                "ETH".parse::<UnderlyingSymbol>().unwrap(),
                Product::Perpetual
            )
        );
        let symbol = ProductSymbol::from("BTCP");
        assert_eq!(
            symbol.split(),
            (
                "BTC".parse::<UnderlyingSymbol>().unwrap(),
                Product::Perpetual
            )
        );
    }

    #[test]
    fn prop_ethabi_symbols() {
        fn ethabi_roundtrip_symbols(symbol: ProductSymbol) -> bool {
            let token = DynSolValue::Tuple(vec![symbol.into_token()]);
            let bytes = token.abi_encode();
            let schema: DynSolType = generate_schema(&token).into();
            let decoded_token = schema
                .abi_decode(&bytes)
                .unwrap()
                .as_tuple()
                .unwrap()
                .first()
                .unwrap()
                .clone();
            let decoded = ProductSymbol::from_token(decoded_token).unwrap();
            decoded == symbol
        }
        QuickCheck::new()
            .gen(quickcheck::Gen::new(10))
            .quickcheck(ethabi_roundtrip_symbols as fn(ProductSymbol) -> bool);
    }

    #[derive(Debug, Clone, PartialEq)]
    pub enum VerifiedStateKeyVariant {
        TraderAddress(TraderAddress),
        StatsKey(StatsKey),
        StrategyKey(StrategyKey),
        PositionKey(PositionKey),
        BookOrderKey(BookOrderKey),
        PriceKey(PriceKey),
        InsuranceFundKey(InsuranceFundKey),
        EpochMetadataKey(EpochMetadataKey),
        TradableProductKey(TradableProductKey),
    }

    impl Arbitrary for VerifiedStateKeyVariant {
        fn arbitrary(g: &mut quickcheck::Gen) -> Self {
            let discriminator = *g.choose(&[1, 2, 3, 4, 5, 6, 11]).unwrap();
            match discriminator {
                ITEM_TRADER => Self::TraderAddress(Arbitrary::arbitrary(g)),
                ITEM_STATS => Self::StatsKey(Arbitrary::arbitrary(g)),
                ITEM_STRATEGY => Self::StrategyKey(Arbitrary::arbitrary(g)),
                ITEM_POSITION => Self::PositionKey(Arbitrary::arbitrary(g)),
                ITEM_BOOK_ORDER => Self::BookOrderKey(Arbitrary::arbitrary(g)),
                ITEM_PRICE => Self::PriceKey(Arbitrary::arbitrary(g)),
                ITEM_INSURANCE_FUND => Self::InsuranceFundKey(Arbitrary::arbitrary(g)),
                ITEM_EPOCH_METADATA => Self::EpochMetadataKey(Arbitrary::arbitrary(g)),
                ITEM_TRADABLE_PRODUCT => Self::TradableProductKey(Arbitrary::arbitrary(g)),
                _ => panic!("Invalid discriminator"),
            }
        }
    }

    fn encode_decode_key(key_variant: VerifiedStateKeyVariant) -> bool {
        match key_variant {
            VerifiedStateKeyVariant::TraderAddress(val) => {
                let key = val.encode_key();
                let decoded_val = TraderAddress::decode_key(&key).unwrap();
                decoded_val == val
            }
            VerifiedStateKeyVariant::StatsKey(val) => {
                let key = val.encode_key();
                let decoded_val = StatsKey::decode_key(&key).unwrap();
                decoded_val == val
            }
            VerifiedStateKeyVariant::StrategyKey(val) => {
                let key = val.encode_key();
                let decoded_val = StrategyKey::decode_key(&key).unwrap();
                decoded_val == val
            }
            VerifiedStateKeyVariant::PositionKey(val) => {
                let key = val.encode_key();
                let decoded_val = PositionKey::decode_key(&key).unwrap();
                decoded_val == val
            }
            VerifiedStateKeyVariant::BookOrderKey(val) => {
                let key = val.encode_key();
                let decoded_val = BookOrderKey::decode_key(&key).unwrap();
                decoded_val == val
            }
            VerifiedStateKeyVariant::PriceKey(val) => {
                let key = val.encode_key();
                let decoded_val = PriceKey::decode_key(&key).unwrap();
                decoded_val == val
            }
            VerifiedStateKeyVariant::InsuranceFundKey(val) => {
                let key = val.encode_key();
                let decoded_val = InsuranceFundKey::decode_key(&key).unwrap();
                decoded_val == val
            }
            VerifiedStateKeyVariant::EpochMetadataKey(val) => {
                let key = val.encode_key();
                let decoded_val = EpochMetadataKey::decode_key(&key).unwrap();
                decoded_val == val
            }
            VerifiedStateKeyVariant::TradableProductKey(val) => {
                let key = val.encode_key();
                let decoded_val = TradableProductKey::decode_key(&key).unwrap();
                decoded_val == val
            }
        }
    }

    #[test]
    fn test_encode_decode_keys() {
        assert!(encode_decode_key(VerifiedStateKeyVariant::TraderAddress(
            ALICE.into()
        )));
        assert!(encode_decode_key(VerifiedStateKeyVariant::StatsKey(
            StatsKey {
                trader: ALICE.into()
            }
        )));
        assert!(encode_decode_key(VerifiedStateKeyVariant::StrategyKey(
            StrategyKey::new(BOB, StrategyIdHash::default())
        )));
        assert!(encode_decode_key(VerifiedStateKeyVariant::PositionKey(
            PositionKey::new(BOB, StrategyIdHash::default(), ETHP)
        )));
        assert!(encode_decode_key(VerifiedStateKeyVariant::BookOrderKey(
            BookOrderKey::new(
                ETHP,
                Bytes25::from_slice(&[
                    0_u8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1
                ])
            )
        )));
        assert!(encode_decode_key(VerifiedStateKeyVariant::PriceKey(
            PriceKey::new(
                ETHP,
                Bytes25::from_slice(&[
                    0_u8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1
                ])
            )
        )));
        assert!(encode_decode_key(
            VerifiedStateKeyVariant::EpochMetadataKey(12.into())
        ));
        assert!(encode_decode_key(
            VerifiedStateKeyVariant::TradableProductKey(TradableProductKey {
                specs: SpecsKey {
                    kind: SpecsKind::SingleNamePerpetual,
                    name: "ETHP".to_string()
                },
                parameters: None,
            })
        ));
    }

    #[test]
    fn prop_encode_decode_keys() {
        QuickCheck::new()
            .gen(quickcheck::Gen::new(10))
            .tests(1000)
            .quickcheck(encode_decode_key as fn(VerifiedStateKeyVariant) -> bool);
    }
}
