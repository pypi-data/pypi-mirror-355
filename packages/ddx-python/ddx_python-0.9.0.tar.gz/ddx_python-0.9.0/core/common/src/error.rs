#[cfg(not(target_family = "wasm"))]
use std::string::String;

#[derive(thiserror::Error, Debug)]
pub enum Error {
    #[error("Error with crypto tooling: {0}")]
    Crypto(String),
    #[error(transparent)]
    EnvVar(#[from] std::env::VarError),
    #[error(transparent)]
    EthAbiStd(#[from] alloy_dyn_abi::Error),
    #[cfg(not(target_family = "wasm"))]
    #[error(transparent)]
    AlloySolType(#[from] alloy_sol_types::Error),
    #[error(transparent)]
    InfallibleConversion(#[from] core::convert::Infallible),
    #[error("{0}")]
    Other(String),
    #[error("Error parsing string into struct: {0}")]
    Parse(String),
    #[error("Conversion error: {0}")]
    Conversion(String),
    #[error(transparent)]
    Regex(#[from] regex::Error),
    #[error("Error with serde serialize/deserialize: {0}")]
    Serde(String),
    #[error("Error with Sparse Merkle Tree tooling: {0}")]
    SparseMerkleTree(String),
    #[error(transparent)]
    TryFromInt(#[from] std::num::TryFromIntError),
}

pub type Result<T, E = Error> = std::result::Result<T, E>;

impl From<sparse_merkle_tree::error::Error> for Error {
    fn from(e: sparse_merkle_tree::error::Error) -> Self {
        Error::SparseMerkleTree(format!("{:?}", e))
    }
}

impl From<libsecp256k1::Error> for Error {
    fn from(e: libsecp256k1::Error) -> Self {
        Error::Crypto(format!("{:?}", e))
    }
}

impl From<serde_json::Error> for Error {
    fn from(e: serde_json::Error) -> Self {
        Error::Serde(format!("{:?}", e))
    }
}

impl From<strum::ParseError> for Error {
    fn from(e: strum::ParseError) -> Self {
        Error::Parse(format!("{:?}", e))
    }
}

#[inline]
#[must_use]
pub fn must_use(error: Error) -> Error {
    error
}

#[macro_export]
macro_rules! ensure {
    ($cond:expr, $msg:literal $(,)?) => {
        if !$cond {
            return $crate::Result::Err($crate::Error::Other(format!("{}", $msg)))
        }
    };
    ($cond:expr, $err:expr $(,)?) => {
        if !$cond {
            return $crate::Result::Err($crate::Error::Other(format!("{:?}", $err)))
        }
    };
    ($cond:expr, $fmt:expr, $($arg:tt)*) => {
        if !$cond {
            return $crate::Result::Err($crate::Error::Other(format!($fmt, $($arg)*)))
        }
    };
}

#[macro_export]
macro_rules! bail {
    ($msg:literal $(,)?) => {
        return $crate::Result::Err($crate::Error::Other(format!("{}", $msg)))
    };
    ($err:expr $(,)?) => {
        return $crate::Result::Err($crate::Error::Other(format!("{:?}", $err)))
    };
    ($fmt:expr, $($arg:tt)*) => {
        return $crate::Result::Err($crate::Error::Other(format!($fmt, $($arg)*)))
    };
}

#[macro_export]
macro_rules! error {
    ($msg:literal $(,)?) => {
        $crate::error::must_use({
            core_common::Error::Other(format!("{}", $msg))
        })
    };
    ($err:expr $(,)?) => {
        $crate::error::must_use({
            let error = match $err {
                error => core_common::Error::Other(format!("{:?}", error)),
            };
            error
        })
    };
    ($fmt:expr, $($arg:tt)*) => {
        core_common::Error::Other(format!($fmt, $($arg)*))
    };
}
