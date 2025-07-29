use crate::types::primitives::Hash;
use serde::{Deserialize, Serialize};

use super::primitives::StampedTimeValue;

pub type EpochId = u64;
pub type Ordinal = u64;
pub type RequestIndex = u64;

/// A transaction as stored in the transaction log.
/// Represents state-transitioning data.
///
/// The generic event type allows us to hold the side-effect data or not depending
/// on the use case without the need for a wrapper type.
/// Note: it only applies to state-transitioning operations.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Tx<E> {
    /// The epoch id and ordinal uniquely identify a transaction
    pub epoch_id: EpochId,
    pub ordinal: Ordinal,
    /// State root hash before the transaction
    pub state_root_hash: Hash,
    /// Index of the associated request (a transaction always has one request)
    pub request_index: RequestIndex,
    /// Numeric identifier for a batch of transactions.
    pub batch_id: u64,
    /// Distributed time stamp preceding execution.
    pub time: StampedTimeValue,
    /// Event data
    #[serde(bound = "E: Serialize + serde::de::DeserializeOwned")]
    pub event: E,
}

impl<E> Tx<E> {
    pub fn new(
        epoch_id: EpochId,
        ordinal: Ordinal,
        state_root_hash: Hash,
        request_index: u64,
        time: StampedTimeValue,
        event: E,
    ) -> Self {
        Tx {
            epoch_id,
            ordinal,
            state_root_hash,
            request_index,
            batch_id: request_index,
            time,
            event,
        }
    }
}
