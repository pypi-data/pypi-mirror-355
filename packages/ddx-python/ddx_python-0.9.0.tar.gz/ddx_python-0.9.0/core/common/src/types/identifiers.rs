use crate::{Error, Result};
use alloy_dyn_abi::DynSolValue;
use alloy_primitives::B256;
use core_macros::AbiToken;
#[cfg(feature = "database")]
use postgres_types::{FromSql, IsNull, ToSql, Type, to_sql_checked};
#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "arbitrary")]
use quickcheck::Arbitrary;
use serde::{Deserialize, Serialize};
use std::str::FromStr;

use super::primitives::{Bytes32, Hash};

pub type OperatorNodeId = u64;

/// Supported chain variants
#[derive(
    Debug,
    Clone,
    Copy,
    Serialize,
    Deserialize,
    AbiToken,
    PartialEq,
    Eq,
    PartialOrd,
    Ord,
    std::hash::Hash,
)]
pub enum ChainVariant {
    Ethereum,
}

impl ChainVariant {
    #[cfg(feature = "database")]
    fn from_u8(n: u8) -> ChainVariant {
        match n {
            0 => ChainVariant::Ethereum,
            _ => panic!("Unexpected chain discriminant {:?}", n),
        }
    }

    #[cfg(not(target_family = "wasm"))]
    pub fn discriminant(&self) -> u8 {
        match self {
            ChainVariant::Ethereum => 0,
        }
    }
}

#[cfg(feature = "database")]
impl ToSql for ChainVariant {
    fn to_sql(
        &self,
        ty: &Type,
        out: &mut bytes::BytesMut,
    ) -> Result<IsNull, Box<dyn std::error::Error + 'static + Sync + Send>> {
        let value = self.discriminant() as i32;
        value.to_sql(ty, out)
    }

    fn accepts(ty: &Type) -> bool {
        <i32 as ToSql>::accepts(ty)
    }

    to_sql_checked!();
}

#[cfg(feature = "database")]
impl<'a> FromSql<'a> for ChainVariant {
    fn from_sql(
        ty: &Type,
        raw: &'a [u8],
    ) -> Result<Self, Box<dyn std::error::Error + Sync + Send>> {
        let discriminant: i32 = i32::from_sql(ty, raw)?;
        let result: Self = Self::from_u8(discriminant.try_into()?);
        Ok(result)
    }

    fn accepts(ty: &Type) -> bool {
        <i32 as FromSql>::accepts(ty)
    }
}

/// Digest of MRENCLAVE and ISV SVN (Security Version Number)
///
/// See [Remote Attestation EGETKEY](https://sgx101.gitbook.io/sgx101/sgx-bootstrap/attestation#detailed-stages)
#[cfg_attr(feature = "python", derive(FromPyObject))]
#[derive(
    Debug,
    Clone,
    Copy,
    Default,
    PartialEq,
    Eq,
    Hash,
    PartialOrd,
    Ord,
    Serialize,
    Deserialize,
    AbiToken,
)]
pub struct ReleaseHash(pub Hash);

#[cfg(not(target_family = "wasm"))]
crate::impl_contiguous_marker_for!(ReleaseHash);
#[cfg(not(target_family = "wasm"))]
crate::impl_unsafe_byte_slice_for!(ReleaseHash);

#[cfg(feature = "python")]
impl IntoPy<PyObject> for ReleaseHash {
    fn into_py(self, py: Python) -> PyObject {
        self.0.into_py(py)
    }
}

impl ReleaseHash {
    pub fn new(mr_enclave_slice: &[u8], isvsvn: u16) -> Self {
        let isvsvn_slice = isvsvn.to_be_bytes();
        // TODO: Consider using the naked mrenclave to use the Enclave Identity security consistent with sealing https://www.intel.com/content/www/us/en/developer/articles/technical/innovative-technology-for-cpu-based-attestation-and-sealing.html (section 2.1)
        let token = DynSolValue::Tuple(vec![
            DynSolValue::FixedBytes(B256::from_slice(mr_enclave_slice), B256::len_bytes()),
            // Right pad the isvsvn to 32 bytes according to the abi encoding https://docs.soliditylang.org/en/develop/abi-spec.html
            DynSolValue::FixedBytes(B256::right_padding_from(&isvsvn_slice), B256::len_bytes()),
        ]);
        let pre_image = token.abi_encode();
        let hash: B256 = alloy_primitives::keccak256(&pre_image);
        ReleaseHash(hash.into())
    }
}

impl From<Bytes32> for ReleaseHash {
    fn from(bytes: Bytes32) -> Self {
        Self(bytes.into())
    }
}

impl FromStr for ReleaseHash {
    type Err = Error;
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Ok(Self(
            Hash::from_str(s).map_err(|e| Error::Parse(e.to_string()))?,
        ))
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for ReleaseHash {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Self(Arbitrary::arbitrary(g))
    }
}
