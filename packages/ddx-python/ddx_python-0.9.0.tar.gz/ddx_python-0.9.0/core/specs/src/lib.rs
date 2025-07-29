#![feature(extract_if)]

use crate::eval::{Atom, StructRepr, Transform};
use core_common::{Error, Result, error};
use serde::{Deserialize, Serialize};

pub mod eval;
mod float_parser;
mod str_parser;

pub type Hostname = String;

#[derive(Debug, Clone, PartialEq, Deserialize, Serialize)]
pub enum StrValue {
    Literal(String),
    Transform(Transform),
}

impl StrValue {
    pub fn literal(&self) -> Option<String> {
        if let StrValue::Literal(s) = self {
            Some(s.clone())
        } else {
            None
        }
    }

    pub fn transform(&self) -> Option<Transform> {
        if let StrValue::Transform(s) = self {
            Some(s.clone())
        } else {
            None
        }
    }
}

#[derive(Debug, Clone, PartialEq, Deserialize, Serialize)]
pub struct GetOp {
    pub query: StrValue,
    pub reader: Transform,
}

impl TryFrom<StructRepr> for GetOp {
    type Error = Error;

    fn try_from(mut repr: StructRepr) -> Result<Self, Self::Error> {
        repr.ensure_match("Get", 1)?;
        let reader = repr
            .try_take("reader")
            .and_then(Transform::try_from)
            .unwrap_or(Transform::Passthrough);
        let query = repr.try_take("query").and_then(|a| match a {
            Atom::Str(s) => Ok(StrValue::Literal(s)),
            Atom::Transform(t) => Ok(StrValue::Transform(t)),
            _ => Err(error!("Unexpected query type {:?}", a)),
        })?;
        Ok(GetOp { query, reader })
    }
}

#[cfg(feature = "arbitrary")]
impl quickcheck::Arbitrary for GetOp {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Self {
            query: StrValue::Literal(quickcheck::Arbitrary::arbitrary(g)),
            reader: quickcheck::Arbitrary::arbitrary(g),
        }
    }
}
