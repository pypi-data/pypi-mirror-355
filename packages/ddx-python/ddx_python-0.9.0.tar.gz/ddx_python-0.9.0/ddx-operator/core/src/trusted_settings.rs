//! Trusted Settings are Defined as Constants
//!
//! Using these settings in trusted context includes them in the enclave measurement, making them trusted.
//! We include them in the common library for portability, but all are used in trusted context.
//!
//! Changing any setting requires governance approval. Therefore, we include changes in scope of a release.
//!
//! Here's the change request procedure:
//!
//! 1. Communicate a change request as a DIP, or other public channel visible to the community.
//! 2. Upon tentative community consensus, schedule the change for an upcoming release.
//! 3. Document the change in the release CHANGELOG, referencing the corresponding lines in the module.
//! 4. When ready, send the release proposal (including documented change requests) for governance approval.
//! 5. Deploy the release to apply the settings changes included.
// TODO: Include all such trusted settings in this module for clarity

/// Holds the collateral rules
///
/// Tranches are defined by mapping the upper bound of a DDX balance to a collateral limit.
/// For example "0-1_000_000 DDX => max collateral of 10_000".
// TODO: Please update the parameters without the alpha guard.
#[cfg(not(feature = "alpha1"))]
pub const COLLATERAL_TRANCHES: &[(u64, u64)] =
    &[(1_000, 10_000), (1_000_000, 1_000_000), (0, 100_000_000)];
#[cfg(feature = "alpha1")]
pub const COLLATERAL_TRANCHES: &[(u64, u64)] = &[(1_000_000, 10_000), (0, 10_000_000)];
