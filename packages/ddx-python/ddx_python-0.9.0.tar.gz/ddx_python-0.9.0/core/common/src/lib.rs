#![allow(non_local_definitions)]
#![feature(generic_const_exprs)]
#![allow(incomplete_features)]

pub mod constants;
pub mod error;
pub mod global;
pub mod types;
pub mod util;

// Allows this crate to refer to itself as core_common when using core_macros,
// which allows macros that need to bring this crate into scope to be used externally.
extern crate self as core_common;

pub type B520 = alloy_primitives::FixedBytes<65>;
pub use alloy_dyn_abi::DynSolValue;
pub use alloy_primitives::{
    Address, B256, B512, BlockNumber, I64, I128 as AlloyI128, I256, U64, U128, U256,
};

pub use crate::error::{Error, Result};
