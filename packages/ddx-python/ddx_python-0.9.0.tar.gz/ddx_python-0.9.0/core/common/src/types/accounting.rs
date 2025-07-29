use crate::{Result, types::primitives::Bytes32};
use core_macros::AbiToken;
#[cfg(feature = "database")]
use postgres_types::{FromSql, IsNull, ToSql, Type, to_sql_checked};
#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "arbitrary")]
use quickcheck::Arbitrary;
use serde::{Deserialize, Serialize};
use std::str::FromStr;

pub const MAIN_STRAT: &str = "main";

/// This module is for serialization of strategy id stored as bytes32.
pub mod as_bytes32_text {
    use crate::types::primitives::Bytes32;
    use core::{fmt, str::FromStr};
    use serde::{
        de::{Deserializer, Error as DeError, Visitor},
        ser::Serializer,
    };
    struct StrategyIdVisitor;

    impl Visitor<'_> for StrategyIdVisitor {
        type Value = Bytes32;
        fn visit_str<E>(self, v: &str) -> core::result::Result<Self::Value, E>
        where
            E: DeError,
        {
            Bytes32::from_str(v).map_err(|_e| DeError::invalid_length(v.len(), &self))
        }

        fn visit_string<E>(self, v: String) -> Result<Self::Value, E>
        where
            E: DeError,
        {
            self.visit_str(&v)
        }

        fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
            formatter.write_str("An string take less than 32 bytes")
        }
    }

    pub fn serialize<S>(value: &Bytes32, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&value.to_string())
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<Bytes32, D::Error>
    where
        D: Deserializer<'de>,
    {
        deserializer.deserialize_string(StrategyIdVisitor)
    }
}

#[derive(
    Clone, Copy, PartialEq, Eq, PartialOrd, Ord, std::hash::Hash, AbiToken, Deserialize, Serialize,
)]
pub struct StrategyId(#[serde(with = "as_bytes32_text")] pub Bytes32);

#[cfg(feature = "python")]
impl FromPyObject<'_> for StrategyId {
    fn extract(ob: &PyAny) -> PyResult<Self> {
        let string: String = ob.extract()?;
        Ok(StrategyId::from_string(string)?)
    }
}

#[cfg(feature = "python")]
impl IntoPy<PyObject> for StrategyId {
    fn into_py(self, py: Python) -> PyObject {
        self.0.to_string().into_py(py)
    }
}

impl std::fmt::Display for StrategyId {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl StrategyId {
    fn new(value: Bytes32) -> Self {
        // First validate that the bytes 32 value is valid utf8
        // If not, default to using the main strategy
        let val_bytes = value.as_bytes();
        let str_len = val_bytes[0];

        if str_len > 31 {
            tracing::warn!("Length of Bytes32 can't be greater than 31");
            return StrategyId::from_string(MAIN_STRAT.to_string()).unwrap();
        }

        let str_bytes = &val_bytes[1..str_len as usize + 1];
        if let Err(e) = std::str::from_utf8(str_bytes) {
            tracing::warn!(
                ?e,
                "Strategy Id bytes were not valid, using default strategy instead"
            );
            StrategyId::from_string(MAIN_STRAT.to_string()).unwrap()
        } else {
            StrategyId(value)
        }
    }
    // This constructor is used to enforce regularity conditions on the contents
    // of StrategyIds that ensures that every StrategyId can be abi-encoded as a
    // Bytes32 value.
    pub fn from_string(string: String) -> Result<Self> {
        let id = Bytes32::from_str(&string)?;
        Ok(StrategyId(id))
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for StrategyId {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        let size: i32 = *g.choose(&(0..32 / 4).collect::<Vec<i32>>()).unwrap();
        let strategy = (0..size).map(|_| char::arbitrary(g)).collect();
        Self::from_string(strategy).unwrap()
    }
}

impl Default for StrategyId {
    fn default() -> Self {
        StrategyId::from_string(MAIN_STRAT.to_string()).unwrap()
    }
}

#[cfg(feature = "test_harness")]
impl From<&str> for StrategyId {
    fn from(val: &str) -> Self {
        StrategyId(Bytes32::from_str(val).unwrap())
    }
}

impl From<StrategyId> for Bytes32 {
    fn from(value: StrategyId) -> Self {
        value.0
    }
}

impl From<Bytes32> for StrategyId {
    fn from(value: Bytes32) -> Self {
        StrategyId::new(value)
    }
}

impl std::fmt::Debug for StrategyId {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_tuple("StrategyId")
            .field(&self.0.to_string())
            .finish()
    }
}

#[cfg(feature = "database")]
impl ToSql for StrategyId {
    fn to_sql(
        &self,
        ty: &Type,
        out: &mut bytes::BytesMut,
    ) -> Result<IsNull, Box<dyn std::error::Error + 'static + Sync + Send>> {
        self.0.to_string().to_sql(ty, out)
    }

    fn accepts(ty: &Type) -> bool {
        <String as ToSql>::accepts(ty)
    }

    to_sql_checked!();
}

#[cfg(feature = "database")]
impl<'a> FromSql<'a> for StrategyId {
    fn from_sql(
        ty: &Type,
        raw: &'a [u8],
    ) -> Result<Self, Box<dyn std::error::Error + Sync + Send>> {
        let decoded_string: String = String::from_sql(ty, raw)?;
        let strategy_id: StrategyId = Self::from_string(decoded_string)?;
        Ok(strategy_id)
    }

    fn accepts(ty: &Type) -> bool {
        <String as FromSql>::accepts(ty)
    }
}

#[cfg(test)]
pub mod tests {
    use super::*;
    use core_common::types::primitives::Bytes32;
    #[test]
    fn test_strategy_id_parsing() {
        // Non main strategy
        let non_main_bytes32 = "abcd".parse::<Bytes32>().unwrap();
        let non_main_strat: StrategyId = non_main_bytes32.into();
        assert_eq!(
            non_main_strat,
            StrategyId::from_string("abcd".to_string()).unwrap()
        );

        // invalid utf8 sequence
        let mut invalid_bytes = non_main_bytes32.as_bytes().to_vec();
        invalid_bytes[1] = 255;
        invalid_bytes[2] = 255;
        let invalid_strat: StrategyId = Bytes32::from_slice(invalid_bytes.as_slice()).into();
        assert_eq!(invalid_strat, StrategyId::default());

        //misencoded non main where length byte is missing
        let mut misencoded_bytes_vec = non_main_bytes32.as_bytes().to_vec();
        misencoded_bytes_vec.remove(0);
        misencoded_bytes_vec.resize(32, 0_u8);
        let misencoded_strat: StrategyId =
            Bytes32::from_slice(misencoded_bytes_vec.as_slice()).into();
        assert_eq!(misencoded_strat, StrategyId::default());
    }
}
