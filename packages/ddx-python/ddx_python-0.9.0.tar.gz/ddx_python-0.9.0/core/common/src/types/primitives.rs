use crate::{
    Address, B520, Error, Result, U128, U256, bail,
    constants::{CHAIN_ETHEREUM, KECCAK256_DIGEST_SIZE},
    ensure,
    util::tokenize::Tokenizable,
};
use alloy_dyn_abi::{DynSolValue, Error as DynAbiError};
use alloy_primitives::{B256, FixedBytes};
use chrono::{DateTime, Utc};
use core_macros::{AbiToken, AsKeccak256, FixedBytesWrapper};
#[cfg(feature = "database")]
use postgres_types::{FromSql, IsNull, ToSql, Type, to_sql_checked};
#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "arbitrary")]
use quickcheck::Arbitrary;
use rustc_hex::{FromHex, ToHex};
use serde::{Deserialize, Serialize};
use sparse_merkle_tree::H256;
use std::{str::FromStr, time::SystemTime};
use strum_macros::{Display, EnumString};
use zerocopy::IntoBytes;

pub mod numbers;
pub use numbers::*;

pub type TimeValue = u64;

#[cfg(feature = "arbitrary")]
pub fn arbitrary_h160(g: &mut quickcheck::Gen) -> alloy_primitives::Address {
    use crate::constants::ADDRESS_BYTE_LEN;

    let vec: Vec<u8> = (0..ADDRESS_BYTE_LEN).map(|_| u8::arbitrary(g)).collect();
    let arr: [u8; ADDRESS_BYTE_LEN] = vec.try_into().unwrap();
    alloy_primitives::Address::new(arr)
}

#[cfg(feature = "arbitrary")]
fn arbitrary_h520(g: &mut quickcheck::Gen) -> B520 {
    const BYTE_LEN: usize = size_of::<B520>();
    let vec: Vec<u8> = (0..BYTE_LEN).map(|_| u8::arbitrary(g)).collect();
    let arr: [u8; BYTE_LEN] = std::convert::TryInto::try_into(vec).unwrap();
    let mut fixed_bytes = [0_u8; BYTE_LEN];
    fixed_bytes.copy_from_slice(&arr);
    B520::new(fixed_bytes)
}

pub fn from_hex<B: AsRef<str>>(hex: B) -> Result<Vec<u8>> {
    hex.as_ref()
        .replace("0x", "")
        .from_hex::<Vec<u8>>()
        .map_err(|source| Error::Parse(format!("{:?}", source)))
}

#[cfg(feature = "arbitrary")]
pub fn arbitrary_b256(g: &mut quickcheck::Gen) -> B256 {
    let vec: Vec<u8> = (0..256 / 8).map(|_| u8::arbitrary(g)).collect();
    let arr: [u8; 256 / 8] = std::convert::TryInto::try_into(vec).unwrap();
    B256::new(arr)
}

/// A trait that will hash using Keccak256 the object it's implemented on.
pub trait Keccak256<T> {
    /// This will return a sized object with the hash
    fn keccak256(&self) -> T
    where
        T: Sized;
}

impl Keccak256<[u8; KECCAK256_DIGEST_SIZE]> for [u8] {
    fn keccak256(&self) -> [u8; KECCAK256_DIGEST_SIZE] {
        alloy_primitives::keccak256(self).into()
    }
}

pub mod as_scaled_fraction {
    use crate::types::primitives::UnscaledI128;
    use serde::{
        Deserialize, Serialize, Serializer,
        de::{Deserializer, Error as DeError},
        ser::Error as SerError,
    };
    use std::convert::TryFrom;

    // Serialize scaled fraction to an unscaled float.
    pub fn serialize<T, S>(value: &T, serializer: S) -> Result<S::Ok, S::Error>
    where
        // All number kinds implement copy
        T: Into<UnscaledI128> + Copy,
        S: Serializer,
    {
        // Normalizing the decimal when serializing numbers into string to use the simplest
        // representation instead a zero padded scheme
        let d = UnscaledI128::from(value);
        let v = serde_json::to_value(d).map_err(S::Error::custom)?;
        v.serialize(serializer)
    }

    // Deserialize float into scaled integer.
    pub fn deserialize<'de, T, D>(deserializer: D) -> Result<T, D::Error>
    where
        T: From<UnscaledI128>,
        D: Deserializer<'de>,
    {
        // Try to deserialize any string (by trying to parse it) or number types.
        let v = serde_json::Value::deserialize(deserializer)?;
        // TODO 1208: Is this enough to prevent all numeric overflows with external inputs
        let d = UnscaledI128::try_from(v).map_err(D::Error::custom)?;
        Ok(d.into())
    }
}

/// Signed integer adapter
#[derive(Debug, Clone, Copy, Default, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct I128 {
    pub negative_sign: bool,
    #[serde(with = "as_scaled_fraction")]
    pub abs: U128,
}

impl Tokenizable for I128 {
    fn from_token(token: DynSolValue) -> Result<Self> {
        match token {
            DynSolValue::Uint(num, num_size) => {
                if num_size != 256 {
                    Err(Error::EthAbiStd(DynAbiError::TopicLengthMismatch {
                        expected: 256,
                        actual: num_size,
                    }))
                } else {
                    let num_bytes: [u8; 32] = num.to_be_bytes();
                    let negative_sign = num_bytes[15] == 1_u8;
                    let mut abs_bytes = [0_u8; 16];
                    abs_bytes.copy_from_slice(&num_bytes[16..]);
                    let abs = U128::from_be_bytes(abs_bytes);
                    Ok(I128 { negative_sign, abs })
                }
            }
            _ => Err(Error::EthAbiStd(DynAbiError::TypeMismatch {
                expected: "FixedBytes".to_string(),
                actual: token
                    .as_type()
                    .map(|t| t.to_string())
                    .unwrap_or("Type not known".to_string()),
            })),
        }
    }
    fn into_token(self) -> DynSolValue {
        let mut num_slice = vec![];
        // We use byte index 15 (first before value) for the boolean sign
        let mut sign_bytes = [0_u8; 16];
        if self.negative_sign {
            sign_bytes[15] = 1_u8;
        }
        num_slice.extend_from_slice(sign_bytes.as_slice());
        let abs: [u8; 16] = self.abs.to_be_bytes::<16>();
        num_slice.extend_from_slice(abs.as_slice());
        let mut num_bytes = [0_u8; 32];
        num_bytes.copy_from_slice(&num_slice);
        let num = U256::from_be_bytes(num_bytes);
        DynSolValue::Uint(num, 256)
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for I128 {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Self {
            negative_sign: bool::arbitrary(g),
            abs: U128::from(u128::arbitrary(g)),
        }
    }
}

pub type CustodianAddress = Bytes21;
pub type TraderAddress = Bytes21;

#[derive(
    Clone,
    Default,
    Copy,
    std::hash::Hash,
    PartialEq,
    Eq,
    Serialize,
    Deserialize,
    PartialOrd,
    Ord,
    FixedBytesWrapper,
)]
#[serde(transparent)]
pub struct Bytes21(FixedBytes<21>);

#[cfg(feature = "python")]
impl FromPyObject<'_> for Bytes21 {
    fn extract(ob: &PyAny) -> PyResult<Self> {
        let value = ob.extract::<String>()?;
        Ok(from_hex(value).and_then(|v| Bytes21::try_from_slice(&v))?)
    }
}

#[cfg(feature = "python")]
impl ToPyObject for Bytes21 {
    fn to_object(&self, py: Python) -> PyObject {
        self.hex().to_object(py)
    }
}

#[cfg(feature = "python")]
impl IntoPy<PyObject> for Bytes21 {
    fn into_py(self, py: Python) -> PyObject {
        self.to_object(py)
    }
}

impl Bytes21 {
    pub fn to_eth_address(&self) -> Address {
        Address::from_slice(&self.as_bytes()[1..])
    }

    /// From normal 0x prefixed Ethereum address injecting the chain id.
    pub fn parse_eth_address(value: &str) -> Result<Self> {
        let result: Address = serde_json::from_str(format!(r#""{}""#, value).as_str())?;
        Ok(result.into())
    }

    #[cfg(any(feature = "python", feature = "test_harness"))]
    pub fn hex(&self) -> String {
        format!("0x{}", self.as_bytes().to_hex::<String>())
    }
}

impl<T: Into<Bytes21> + Copy> From<&T> for Bytes21 {
    fn from(value: &T) -> Self {
        (*value).into()
    }
}

impl Tokenizable for Bytes21 {
    fn from_token(token: DynSolValue) -> Result<Self> {
        let token_bytes32 = Bytes32::from_token(token)?;
        Ok(Bytes21::from_slice(
            &token_bytes32.as_bytes()[..Self::BYTE_LEN],
        ))
    }
    fn into_token(self) -> DynSolValue {
        let mut bytes = self.0.to_vec();
        bytes.resize(32, 0_u8);
        let mut fixed_bytes = [0_u8; Bytes32::BYTE_LEN];
        fixed_bytes.copy_from_slice(&bytes);
        let bytes32: Bytes32 = fixed_bytes.into();
        bytes32.into_token()
    }
}

impl From<Address> for Bytes21 {
    /// From Ethereum address injecting the chain id.
    fn from(value: Address) -> Self {
        let mut bytes = vec![CHAIN_ETHEREUM];
        bytes.extend_from_slice(value.as_bytes());
        Bytes21::from_slice(&bytes)
    }
}

impl From<u16> for Bytes21 {
    fn from(value: u16) -> Self {
        let bytes = Bytes32::from(value as u64);
        Address::from_word(bytes.0).into()
    }
}

impl From<Bytes21> for [u8; Bytes21::BYTE_LEN] {
    fn from(val: Bytes21) -> Self {
        val.0.0
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for Bytes21 {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        let h = arbitrary_h160(g);
        let mut bytes = vec![0_u8];
        bytes.extend_from_slice(h.as_bytes());
        Bytes21::from_slice(&bytes)
    }
}

#[cfg(feature = "database")]
impl ToSql for Bytes21 {
    fn to_sql(
        &self,
        ty: &Type,
        out: &mut bytes::BytesMut,
    ) -> Result<IsNull, Box<dyn std::error::Error + 'static + Sync + Send>> {
        self.as_bytes().to_sql(ty, out)
    }

    fn accepts(ty: &Type) -> bool {
        <&[u8] as ToSql>::accepts(ty)
    }

    to_sql_checked!();
}

#[cfg(feature = "database")]
impl<'a> FromSql<'a> for Bytes21 {
    fn from_sql(
        ty: &Type,
        raw: &'a [u8],
    ) -> Result<Self, Box<dyn std::error::Error + Sync + Send>> {
        let decoded_bytes: &[u8] = <&[u8]>::from_sql(ty, raw)?;
        let bytes: Self = Self::from_slice(decoded_bytes);
        Ok(bytes)
    }

    fn accepts(ty: &Type) -> bool {
        <&[u8] as FromSql>::accepts(ty)
    }
}

impl From<Bytes21> for Bytes32 {
    fn from(value: Bytes21) -> Self {
        let mut bytes = [0_u8; Self::BYTE_LEN];
        bytes[0..21].copy_from_slice(value.as_bytes());
        Bytes32(B256::new(bytes))
    }
}

impl std::fmt::Debug for TraderAddress {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_tuple("TraderAddress")
            .field(&format!("0x{}", self.as_bytes().to_hex::<String>()))
            .finish()
    }
}

impl std::fmt::Display for TraderAddress {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let hex = self.as_bytes().to_hex::<String>();
        write!(f, "0x{}..{}", &hex[2..5], &hex[hex.len() - 2..])
    }
}

#[cfg(feature = "test_harness")]
impl From<&str> for TraderAddress {
    fn from(value: &str) -> Self {
        TraderAddress::parse_eth_address(value).unwrap()
    }
}

#[derive(
    Debug,
    Clone,
    Copy,
    Default,
    std::hash::Hash,
    PartialEq,
    Eq,
    PartialOrd,
    Ord,
    AbiToken,
    Serialize,
    Deserialize,
    FixedBytesWrapper,
)]
#[serde(transparent)]
pub struct Bytes32(pub B256);

/*
impl Tokenizable for Bytes32 {
    fn from_token(token: DynSolValue) -> Result<Self> {
        Ok(Bytes32(B256::from_token(token)?))
    }
    fn into_token(self) -> DynSolValue {
        self.0.into_token()
    }
}
*/

#[cfg(feature = "python")]
impl FromPyObject<'_> for Bytes32 {
    fn extract(ob: &PyAny) -> PyResult<Self> {
        let hex = ob.extract::<String>()?;
        Ok(Self(B256::from_str(&hex).map_err(|e| {
            crate::types::exported::python::CoreCommonError::new_err(e.to_string())
        })?))
    }
}

impl From<u64> for Bytes32 {
    fn from(value: u64) -> Self {
        let val = U256::from(value);
        Bytes32(val.into())
    }
}

impl From<Address> for Bytes32 {
    fn from(value: Address) -> Self {
        Bytes32(value.into_word())
    }
}

impl FromStr for Bytes32 {
    type Err = Error;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        let str_bytes = value.as_bytes();
        let str_len = str_bytes.len();
        ensure!(
            str_len < Self::BYTE_LEN,
            "Bytes32 has 31 utf8 bytes prefixed with 1 length byte"
        );
        // First byte is the string length
        let mut bytes = [0u8; Self::BYTE_LEN];
        bytes[0] = str_len as u8;
        bytes[1..str_len + 1].copy_from_slice(str_bytes);
        Ok(Bytes32::from_slice(&bytes))
    }
}

// Also implements `ToString` for free
impl std::fmt::Display for Bytes32 {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let mut bytes = self.as_bytes().to_vec();
        // First byte is the string length
        let length = bytes.remove(0);
        bytes.truncate(length as usize);
        write!(f, "{}", String::from_utf8_lossy(&bytes))
    }
}

impl From<Bytes32> for B256 {
    fn from(value: Bytes32) -> Self {
        value.0
    }
}

impl From<Bytes32> for [u8; Bytes32::BYTE_LEN] {
    fn from(value: Bytes32) -> Self {
        value.0.0
    }
}

impl From<[u8; Bytes32::BYTE_LEN]> for Bytes32 {
    fn from(value: [u8; 32]) -> Self {
        Bytes32(B256::new(value))
    }
}

impl From<B256> for Bytes32 {
    fn from(value: B256) -> Self {
        Bytes32(value)
    }
}

// TODO: Either use this Hash adapter everywhere except internally when interfacing with either Ethereum or the SMT
// Or, fork the SMT to standardize both H256 into a single system-wide structure, then remove this adapter.
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
    AsKeccak256,
    FixedBytesWrapper,
)]
#[serde(transparent)]
pub struct Hash(B256);

#[cfg(feature = "python")]
impl FromPyObject<'_> for Hash {
    fn extract(ob: &PyAny) -> PyResult<Self> {
        let hex = ob.extract::<String>()?;
        Ok(Self(B256::from_str(&hex).map_err(|e| {
            crate::types::exported::python::CoreCommonError::new_err(e.to_string())
        })?))
    }
}

#[cfg(feature = "python")]
impl IntoPy<PyObject> for Hash {
    fn into_py(self, py: Python) -> PyObject {
        format!("{}", self).into_py(py)
    }
}

impl std::fmt::Display for Hash {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "0x{}", self.as_bytes().to_hex::<String>())
    }
}

impl From<Hash> for H256 {
    fn from(value: Hash) -> Self {
        let bytes: [u8; 32] = value.into();
        bytes.into()
    }
}

impl From<H256> for Hash {
    fn from(value: H256) -> Self {
        let bytes: [u8; 32] = value.into();
        Hash(B256::new(bytes))
    }
}

impl From<U256> for Hash {
    fn from(value: U256) -> Self {
        Hash(value.into())
    }
}

impl From<Hash> for U256 {
    fn from(value: Hash) -> Self {
        value.0.into()
    }
}

impl From<Bytes32> for Hash {
    fn from(value: Bytes32) -> Self {
        Hash(value.0)
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for Hash {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Self(arbitrary_b256(g))
    }
}

impl FromStr for Hash {
    type Err = <B256 as FromStr>::Err;

    fn from_str(text: &str) -> Result<Self, Self::Err> {
        let hash = B256::from_str(text)?;
        Ok(Hash(hash))
    }
}

impl From<B256> for Hash {
    fn from(value: B256) -> Self {
        Hash(value)
    }
}

impl From<Hash> for B256 {
    fn from(value: Hash) -> Self {
        value.0
    }
}

// Conversion from refs is reasonable for trivial byte copying
impl<T: Copy + Into<Hash>> From<&T> for Hash {
    fn from(value: &T) -> Self {
        (*value).into()
    }
}

impl From<[u8; 32]> for Hash {
    fn from(value: [u8; 32]) -> Self {
        Hash(B256::new(value))
    }
}

impl From<Hash> for [u8; 32] {
    fn from(value: Hash) -> Self {
        value.0.0
    }
}

impl From<u32> for Hash {
    fn from(value: u32) -> Self {
        Bytes32::from(value as u64).into()
    }
}

impl std::fmt::LowerHex for Hash {
    /// #Examples
    ///
    /// ```
    /// use core_common::types::primitives::Hash;
    /// let x = Hash::from([1; 32]);
    /// assert_eq!(
    ///     format!("{:#x}", x),
    ///     "0x0101010101010101010101010101010101010101010101010101010101010101"
    /// );
    /// ```
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let val = self.0;

        std::fmt::LowerHex::fmt(&val, f) // delegate to EthH256 implementation
    }
}

// This section contains SQL conversion implementations

#[cfg(feature = "database")]
impl ToSql for Hash {
    fn to_sql(
        &self,
        ty: &Type,
        out: &mut bytes::BytesMut,
    ) -> Result<IsNull, Box<dyn std::error::Error + 'static + Sync + Send>> {
        self.as_bytes().to_sql(ty, out)
    }

    fn accepts(ty: &Type) -> bool {
        <&[u8] as ToSql>::accepts(ty)
    }

    to_sql_checked!();
}

#[cfg(feature = "database")]
impl<'a> FromSql<'a> for Hash {
    fn from_sql(
        ty: &Type,
        raw: &'a [u8],
    ) -> Result<Self, Box<dyn std::error::Error + Sync + Send>> {
        let raw_bytes = Vec::from_sql(ty, raw)?;
        let hash = Hash::try_from_slice(&raw_bytes)?;
        Ok(hash)
    }

    fn accepts(ty: &Type) -> bool {
        <Vec<u8> as FromSql>::accepts(ty)
    }
}

pub type CompressedKey = Bytes33;

#[derive(
    Debug,
    Clone,
    Copy,
    std::hash::Hash,
    PartialEq,
    Eq,
    Serialize,
    Deserialize,
    PartialOrd,
    Ord,
    FixedBytesWrapper,
)]
#[serde(transparent)]
pub struct Bytes33(FixedBytes<33>);

impl<T: Into<Bytes33> + Copy> From<&T> for Bytes33 {
    fn from(value: &T) -> Self {
        (*value).into()
    }
}

impl From<Bytes33> for [u8; Bytes33::BYTE_LEN] {
    fn from(value: Bytes33) -> Self {
        value.0.0
    }
}

impl From<Bytes33> for [u8; KECCAK256_DIGEST_SIZE] {
    fn from(value: Bytes33) -> Self {
        // Only hash the last 32 bytes of the public key, the tag byte is ignored
        let mut bytes = [0_u8; KECCAK256_DIGEST_SIZE];
        bytes.copy_from_slice(&value.as_bytes()[1..KECCAK256_DIGEST_SIZE + 1]);
        bytes
    }
}

impl Tokenizable for Bytes33 {
    fn from_token(token: DynSolValue) -> Result<Self> {
        match token {
            DynSolValue::Bytes(bytes) => Ok(Bytes33(Bytes33::copy_fixed_bytes(&bytes)?)),
            _ => Err(Error::EthAbiStd(DynAbiError::TypeMismatch {
                expected: "Bytes".to_string(),
                actual: token
                    .as_type()
                    .map(|t| t.to_string())
                    .unwrap_or("Type not known".to_string()),
            })),
        }
    }
    fn into_token(self) -> DynSolValue {
        DynSolValue::Bytes(self.as_bytes().to_vec())
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for Bytes33 {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        let h = arbitrary_b256(g);
        let mut bytes = h.as_bytes().to_vec();
        bytes.resize(Self::BYTE_LEN, 0_u8);
        Bytes33::from_slice(&bytes)
    }
}

#[derive(Clone, Copy, PartialEq, Serialize, Deserialize, FixedBytesWrapper)]
#[serde(transparent)]
pub struct Signature(FixedBytes<65>);

#[cfg(feature = "python")]
impl FromPyObject<'_> for Signature {
    fn extract(ob: &PyAny) -> PyResult<Self> {
        let str_repr = ob.extract::<String>()?;
        Ok(Self::from_str(&str_repr)?)
    }
}

#[cfg(feature = "python")]
impl IntoPy<PyObject> for Signature {
    fn into_py(self, py: Python) -> PyObject {
        self.to_string().into_py(py)
    }
}

impl Signature {
    pub fn new(fixed_bytes: [u8; Self::BYTE_LEN]) -> Self {
        Signature(FixedBytes::new(fixed_bytes))
    }

    /// Convert to vrs format, the recovery id is encoded in the first byte
    pub fn as_vrs(&self) -> B520 {
        let rsv_slice = self.as_bytes();
        let mut vrs_bytes: Vec<u8> = Vec::with_capacity(Self::BYTE_LEN);
        vrs_bytes.push(rsv_slice[64]);
        vrs_bytes.extend_from_slice(&rsv_slice[..Self::BYTE_LEN - 1]);
        B520::from_slice(&vrs_bytes)
    }

    /// Convert from vrs format, the recovery id is encoded in the first byte
    pub fn from_vrs(vrs: B520) -> Self {
        let mut bytes = [0u8; Self::BYTE_LEN];
        bytes[..Self::BYTE_LEN - 1].copy_from_slice(&vrs.as_slice()[1..]);
        bytes[Self::BYTE_LEN - 1] = vrs.as_slice()[0];
        Signature(FixedBytes::new(bytes))
    }

    /// Convert from parts of r, s, v
    pub fn from_parts(r: &[u8], s: &[u8], v: u8) -> Self {
        let mut bytes = [0u8; Self::BYTE_LEN];
        bytes[..r.len()].copy_from_slice(r);
        bytes[r.len()..r.len() + s.len()].copy_from_slice(s);
        bytes[Self::BYTE_LEN - 1] = v;
        Signature(FixedBytes::new(bytes))
    }

    fn serialize(&self) -> String {
        format!("0x{}", self.as_bytes().to_hex::<String>())
    }
}

impl std::fmt::Debug for Signature {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_tuple("Signature").field(&self.serialize()).finish()
    }
}

impl std::fmt::Display for Signature {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.serialize())
    }
}

impl Default for Signature {
    fn default() -> Self {
        Signature(FixedBytes::new([0; Self::BYTE_LEN]))
    }
}

impl From<Signature> for B520 {
    fn from(value: Signature) -> Self {
        B520::new(value.0.0)
    }
}

impl From<B520> for Signature {
    fn from(value: B520) -> Self {
        Signature(FixedBytes::new(value.0))
    }
}

impl From<Signature> for [u8; Signature::BYTE_LEN] {
    fn from(value: Signature) -> Self {
        value.0.0
    }
}

impl FromStr for Signature {
    type Err = Error;

    /// Parse by encoding symbol text into the 5-bit internal representation
    fn from_str(value: &str) -> Result<Self, Self::Err> {
        Ok(Signature::from_slice(&from_hex(value)?))
    }
}

impl From<&str> for Signature {
    fn from(value: &str) -> Self {
        value.parse().unwrap()
    }
}

impl From<String> for Signature {
    fn from(val: String) -> Self {
        val.as_str().into()
    }
}

// TODO: Do we ever want to tokenize the signature as an rsv value? All
// of our smart contracts are using vrs, so this seems less useful than
// the alternative.
impl Tokenizable for Signature {
    fn from_token(token: DynSolValue) -> Result<Self> {
        match token {
            DynSolValue::Bytes(bytes) => Ok(Signature(Signature::copy_fixed_bytes(&bytes)?)),
            _ => Err(Error::EthAbiStd(DynAbiError::TypeMismatch {
                expected: "Bytes".to_string(),
                actual: token
                    .as_type()
                    .map(|t| t.to_string())
                    .unwrap_or("Type not known".to_string()),
            })),
        }
    }

    fn into_token(self) -> DynSolValue {
        DynSolValue::Bytes(self.as_bytes().to_vec())
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for Signature {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        arbitrary_h520(g).into()
    }
}

#[cfg(feature = "database")]
impl ToSql for Signature {
    fn to_sql(
        &self,
        ty: &Type,
        out: &mut bytes::BytesMut,
    ) -> Result<IsNull, Box<dyn std::error::Error + 'static + Sync + Send>> {
        self.0.to_vec().to_sql(ty, out)
    }

    fn accepts(ty: &Type) -> bool {
        <&[u8] as ToSql>::accepts(ty)
    }

    to_sql_checked!();
}

#[cfg(feature = "database")]
impl<'a> FromSql<'a> for Signature {
    fn from_sql(
        ty: &Type,
        raw: &'a [u8],
    ) -> Result<Self, Box<dyn std::error::Error + Sync + Send>> {
        let bytes: Vec<u8> = Vec::from_sql(ty, raw)?;
        Ok(Signature::from_slice(&bytes))
    }

    fn accepts(ty: &Type) -> bool {
        <Vec<u8> as FromSql>::accepts(ty)
    }
}

pub type SessionSignature = Option<Signature>;

/// Verified state relative time value in seconds with a wall clock timestamp.
#[derive(Debug, Default, Clone, Copy, PartialEq, Serialize, Deserialize, AbiToken, AsKeccak256)]
pub struct StampedTimeValue {
    pub value: TimeValue,
    pub timestamp: i64,
}

impl StampedTimeValue {
    pub fn with_now_timestamp(value: TimeValue) -> Self {
        Self {
            value,
            timestamp: DateTime::<Utc>::from(SystemTime::now()).timestamp_millis(),
        }
    }
}

impl std::fmt::Display for StampedTimeValue {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "{:?}", self)
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for StampedTimeValue {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Self {
            value: u64::arbitrary(g),
            timestamp: i64::arbitrary(g),
        }
    }
}

/// Well-known ERC20 tokens used in the underpinning of the protocol
#[cfg_attr(feature = "python", pyclass(frozen))]
#[derive(Debug, Clone, Copy, Hash, PartialEq, Serialize, Deserialize, Eq, Display, EnumString)]
pub enum TokenSymbol {
    USDC,
    DDX,
}

#[cfg(feature = "database")]
impl ToSql for TokenSymbol {
    fn to_sql(
        &self,
        ty: &Type,
        out: &mut bytes::BytesMut,
    ) -> Result<IsNull, Box<dyn std::error::Error + 'static + Sync + Send>> {
        self.to_string().to_sql(ty, out)
    }

    fn accepts(ty: &Type) -> bool {
        <String as ToSql>::accepts(ty)
    }

    to_sql_checked!();
}

#[cfg(feature = "database")]
impl<'a> FromSql<'a> for TokenSymbol {
    fn from_sql(
        ty: &Type,
        raw: &'a [u8],
    ) -> Result<Self, Box<dyn std::error::Error + Sync + Send>> {
        let decoded_string = String::from_sql(ty, raw)?;
        let symbol: Self = decoded_string.parse()?;
        Ok(symbol)
    }

    fn accepts(ty: &Type) -> bool {
        <String as FromSql>::accepts(ty)
    }
}

#[cfg_attr(feature = "python", pyclass(frozen))]
#[derive(
    Debug,
    Copy,
    Clone,
    PartialEq,
    Deserialize,
    Serialize,
    std::hash::Hash,
    AbiToken,
    Eq,
    Default,
    Display,
    EnumString,
)]
pub enum OrderSide {
    #[default]
    Bid,
    Ask,
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for OrderSide {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        let discriminator = g.choose(&[0, 1]).unwrap();
        match discriminator {
            0 => OrderSide::Bid,
            1 => OrderSide::Ask,
            _ => panic!("invalid discriminator"),
        }
    }
}

impl OrderSide {
    pub fn reverse(&self) -> &OrderSide {
        match *self {
            OrderSide::Bid => &OrderSide::Ask,
            OrderSide::Ask => &OrderSide::Bid,
        }
    }
}

impl From<OrderSide> for i16 {
    fn from(order_side: OrderSide) -> Self {
        order_side as i16
    }
}

impl From<OrderSide> for i32 {
    fn from(order_side: OrderSide) -> Self {
        order_side as i32
    }
}

// All short enums codes are u8 to ensure that we can use only 1 byte in binary encoding
impl From<OrderSide> for u8 {
    fn from(value: OrderSide) -> Self {
        match value {
            OrderSide::Bid => 0,
            OrderSide::Ask => 1,
        }
    }
}

// All short enums codes are u8 to ensure that we can use only 1 byte in binary encoding
impl From<&OrderSide> for u8 {
    fn from(value: &OrderSide) -> Self {
        match value {
            OrderSide::Bid => 0,
            OrderSide::Ask => 1,
        }
    }
}

impl TryFrom<u8> for OrderSide {
    type Error = Error;

    fn try_from(value: u8) -> Result<Self, Self::Error> {
        Ok(match value {
            0 => OrderSide::Bid,
            1 => OrderSide::Ask,
            _ => bail!("Invalid order type code {:?}", value),
        })
    }
}

impl TryFrom<i16> for OrderSide {
    type Error = Error;

    fn try_from(value: i16) -> Result<Self, Self::Error> {
        let byte: u8 = value.try_into()?;
        byte.try_into()
    }
}

impl TryFrom<i32> for OrderSide {
    type Error = Error;

    fn try_from(value: i32) -> Result<Self, Self::Error> {
        let byte: u8 = value.try_into()?;
        byte.try_into()
    }
}

#[cfg(feature = "database")]
impl<'a> FromSql<'a> for OrderSide {
    fn from_sql(
        ty: &Type,
        raw: &'a [u8],
    ) -> Result<Self, Box<dyn std::error::Error + Sync + Send>> {
        let decoded: i32 = i32::from_sql(ty, raw)?;
        let result: Self = Self::try_from(decoded)?;
        Ok(result)
    }

    fn accepts(ty: &Type) -> bool {
        <i32 as FromSql>::accepts(ty)
    }
}

#[cfg(feature = "database")]
impl ToSql for OrderSide {
    fn to_sql(
        &self,
        ty: &Type,
        out: &mut bytes::BytesMut,
    ) -> Result<IsNull, Box<dyn std::error::Error + 'static + Sync + Send>> {
        let value: i32 = (*self).into();
        value.to_sql(ty, out)
    }

    fn accepts(ty: &Type) -> bool {
        <i32 as ToSql>::accepts(ty)
    }

    to_sql_checked!();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_enclave_signature() {
        let sig: Signature = Default::default();
        let value = serde_json::to_value(sig).unwrap();
        tracing::debug!("The encoded value {:?}", value);
        let _sig2: Signature = serde_json::from_value(value).unwrap();
    }
}
