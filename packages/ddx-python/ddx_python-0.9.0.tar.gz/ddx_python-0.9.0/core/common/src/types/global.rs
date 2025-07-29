#[cfg(feature = "arbitrary")]
use super::primitives::arbitrary_h160;
use super::primitives::{Bytes32, TokenSymbol};
use crate::{Address, Result};
use core_macros::AbiToken;
#[cfg(feature = "database")]
use postgres_types::{IsNull, ToSql, Type, to_sql_checked};
#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "arbitrary")]
use quickcheck::Arbitrary;
use rustc_hex::ToHex;
use serde::{Deserialize, Serialize};
use std::str::FromStr;
use zerocopy::IntoBytes;

#[derive(
    Clone, PartialOrd, Ord, Debug, PartialEq, Hash, Eq, AbiToken, Deserialize, Serialize, Copy,
)]
pub struct TokenAddress(Address);

#[cfg(feature = "python")]
impl FromPyObject<'_> for TokenAddress {
    fn extract(ob: &PyAny) -> PyResult<Self> {
        let hex = ob.extract::<String>()?;
        Ok(Self(Address::from_str(&hex).map_err(|e| {
            core_common::types::exported::python::CoreCommonError::new_err(e.to_string())
        })?))
    }
}

#[cfg(feature = "python")]
impl IntoPy<PyObject> for TokenAddress {
    fn into_py(self, py: Python) -> PyObject {
        self.to_string().into_py(py)
    }
}

impl FromStr for TokenAddress {
    type Err = <Address as FromStr>::Err;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let hash = Address::from_str(s)?;
        Ok(Self(hash))
    }
}

impl std::fmt::Display for TokenAddress {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "0x{}", self.0.as_bytes().to_hex::<String>())
    }
}

impl Default for TokenAddress {
    fn default() -> Self {
        TokenSymbol::USDC.into()
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for TokenAddress {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        TokenAddress(arbitrary_h160(g))
    }
}

impl TokenAddress {
    pub fn collateral(address: Address) -> Self {
        core_common::global::app_context()
            .collateral_addresses
            .iter()
            .find_map(|(_, collateral_addr)| {
                if collateral_addr == &address {
                    Some(TokenAddress(address))
                } else {
                    None
                }
            })
            .unwrap()
    }

    pub fn ddx() -> Self {
        TokenAddress(core_common::global::app_context().ddx_token_address)
    }

    fn new(address: Address) -> Self {
        TokenAddress(address)
    }
}

impl From<TokenAddress> for Address {
    fn from(value: TokenAddress) -> Self {
        value.0
    }
}

impl From<TokenSymbol> for TokenAddress {
    fn from(symbol: TokenSymbol) -> Self {
        if symbol == TokenSymbol::DDX {
            return TokenAddress::new(core_common::global::app_context().ddx_token_address);
        }
        TokenAddress::new(core_common::global::app_context().collateral_addresses[&symbol])
    }
}

impl From<TokenAddress> for Bytes32 {
    fn from(value: TokenAddress) -> Self {
        value.0.into()
    }
}

#[cfg(feature = "database")]
impl ToSql for TokenAddress {
    fn to_sql(
        &self,
        ty: &Type,
        out: &mut bytes::BytesMut,
    ) -> Result<IsNull, Box<dyn std::error::Error + 'static + Sync + Send>> {
        self.0.as_bytes().to_sql(ty, out)
    }

    fn accepts(ty: &Type) -> bool {
        <&[u8] as ToSql>::accepts(ty)
    }

    to_sql_checked!();
}

impl From<TokenAddress> for TokenSymbol {
    fn from(value: TokenAddress) -> Self {
        let address = value.0;
        core_common::global::app_context()
            .collateral_addresses
            .iter()
            .find_map(|(symbol, collateral_addr)| {
                if collateral_addr == &address {
                    Some(*symbol)
                } else {
                    None
                }
            })
            .unwrap()
    }
}
