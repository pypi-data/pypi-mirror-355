#[cfg(not(target_family = "wasm"))]
pub mod clock;
#[cfg(feature = "eth-base")]
pub mod contract_events;
#[cfg(feature = "eth-base")]
pub mod ethereum;

// Err on the side of supported all modes (sgx, std and wasm) for core types when doing so is practical.
// We want to expand logic exposed to the wasm library in the future, so the aim to minimize rework.
//
// This is not a strict rule, but a guideline, it makes sense to restrict the scope of more specialized
// types to avoid internal scoping of dependencies.
//
pub mod accounting;
pub mod checkpoint;
#[cfg(not(target_family = "wasm"))]
pub mod identifiers;
pub mod primitives;
#[cfg(not(target_family = "wasm"))]
pub mod request;
#[cfg(not(target_family = "wasm"))]
pub mod state;
#[cfg(not(target_family = "wasm"))]
pub mod transaction;
