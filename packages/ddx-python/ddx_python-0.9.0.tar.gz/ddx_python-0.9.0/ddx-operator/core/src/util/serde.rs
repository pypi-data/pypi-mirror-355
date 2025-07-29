use serde::{
    de::{Deserialize, Deserializer, Error as DeError, Visitor},
    ser::{Error, Serialize, Serializer},
};
use std::fmt;

pub mod as_u64 {
    use super::*;
    use alloy_primitives::U64;

    // Unwrap `U64` and serialize
    pub fn serialize<S>(value: &U64, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let num = value.to::<u64>();
        let ser = serde_json::to_value(num).map_err(S::Error::custom)?;
        ser.serialize(serializer)
    }

    // Deserialize and wrap `U64`
    pub fn deserialize<'de, D>(deserializer: D) -> Result<U64, D::Error>
    where
        D: Deserializer<'de>,
    {
        let num: u64 = Deserialize::deserialize(deserializer)?;
        Ok(U64::from(num))
    }
}

pub mod as_underlying_symbol {
    use super::*;
    use crate::types::primitives::UnderlyingSymbol;

    pub fn serialize<S>(value: &[u8; 4], serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let text = std::str::from_utf8(value.trim_ascii_end()).map_err(S::Error::custom)?;
        text.serialize(serializer)
    }

    struct AsciiBytesVisitor;

    impl Visitor<'_> for AsciiBytesVisitor {
        type Value = [u8; 4];

        fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
            formatter.write_str("A fixed length 4-byte array of ASCII characters")
        }

        fn visit_str<E: serde::de::Error>(self, text: &str) -> Result<Self::Value, E> {
            UnderlyingSymbol::from_ascii_bytes(text.as_bytes())
                .map(|symbol| symbol.0)
                .map_err(serde::de::Error::custom)
        }
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<[u8; 4], D::Error>
    where
        D: Deserializer<'de>,
    {
        deserializer.deserialize_str(AsciiBytesVisitor)
    }
}

pub mod as_product_symbol {
    use super::*;
    use crate::types::primitives::ProductSymbol;

    pub fn serialize<S>(value: &[u8; 6], serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        // Serializing as string by unpacking using our custom scheme
        let text = ProductSymbol::unpack_bytes(value).map_err(S::Error::custom)?;
        text.serialize(serializer)
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<[u8; 6], D::Error>
    where
        D: Deserializer<'de>,
    {
        // Deserialize into string then storing using our custom bit packing scheme
        let text: String = Deserialize::deserialize(deserializer)?;
        ProductSymbol::parse_parts(&text)
            .map(|(s, p)| ProductSymbol::pack_bytes(s, p))
            .map_err(D::Error::custom)
    }
}

#[cfg(not(target_family = "wasm"))]
pub mod as_specs {
    use super::*;
    use crate::specs::types::{Specs, SpecsExpr};
    use std::collections::HashMap;

    pub fn serialize<S>(value: &Specs, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let labeled = value
            .iter()
            .map(|(k, v)| (k.to_string(), v))
            .collect::<HashMap<_, _>>();
        labeled.serialize(serializer)
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<Specs, D::Error>
    where
        D: Deserializer<'de>,
    {
        let labeled: HashMap<String, SpecsExpr> = Deserialize::deserialize(deserializer)?;
        let mut specs = HashMap::default();
        for (l, v) in labeled {
            match l.parse() {
                Ok(k) => {
                    specs.insert(k, v);
                }
                Err(e) => {
                    tracing::error!(?e, "Invalid specs expression");
                }
            }
        }
        Ok(specs)
    }
}
