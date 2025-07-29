#![feature(extract_if)]
#![feature(cfg_eval)]
#![feature(strict_provenance)]
#![feature(duration_constructors)]
#![allow(clippy::type_complexity)]
#![allow(clippy::too_many_arguments)]
#![allow(incomplete_features)]
#![allow(unexpected_cfgs)]
#![allow(non_local_definitions)]
#![allow(async_fn_in_trait)]
// Allows this crate to refer to itself as core_ddx when using core_macros, which allows macros that need to bring this crate into scope to be used externally.
extern crate self as core_ddx;

#[cfg(not(target_family = "wasm"))]
pub use crate::execution::error::*;

pub mod constants;
pub mod execution;
#[cfg(not(target_family = "wasm"))]
pub mod specs;
#[cfg(not(target_family = "wasm"))]
pub mod tree;
#[cfg(not(target_family = "wasm"))]
pub(crate) mod trusted_settings;
pub mod types;
pub mod util;
