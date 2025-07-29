use crate::{
    Address, B256, DynSolValue,
    global::app_context,
    types::primitives::{Hash, Keccak256},
};
#[cfg(not(target_family = "wasm"))]
use crate::{impl_contiguous_marker_for, impl_unsafe_byte_slice_for};
use alloy_primitives::keccak256;
use serde::{Deserialize, Serialize};
use std::fmt::{Debug, Display, Formatter};

use super::state::Chain;

#[derive(Debug, Clone, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
#[repr(C)]
pub struct KycAuth {
    /// Depositing address who should be KYC authorized
    pub depositor: Address,
    /// Expiry block number for KYC auth
    pub expiry_block: u64,
}

#[cfg(not(target_family = "wasm"))]
impl_contiguous_marker_for!(KycAuth);
#[cfg(not(target_family = "wasm"))]
impl_unsafe_byte_slice_for!(KycAuth);

impl KycAuth {
    pub fn hash(&self) -> B256 {
        let (Chain::Ethereum(chain_id), contract_address) = {
            let context = app_context();
            (context.chain, context.contract_address)
        };
        let token = DynSolValue::Tuple(vec![
            contract_address.into(),
            chain_id.into(),
            self.depositor.into(),
            self.expiry_block.into(),
        ]);
        let message = token.abi_encode();
        let intermediary_hash = keccak256(&message);

        // Move the double hashing here for the signing fn to ensure we can recover from this hash.
        // Signing and recovering should not modify the input hash.
        let message = intermediary_hash.as_slice();
        let mut eth_message =
            format!("\x19Ethereum Signed Message:\n{}", message.len()).into_bytes();
        eth_message.extend_from_slice(message);
        keccak256(&eth_message)
    }
}

#[derive(Default, Debug, PartialEq, Eq, Serialize, Deserialize, Copy, Clone)]
#[repr(u8)]
pub enum EventKind {
    ApprovedApplication,
    #[default]
    Blacklist,
    Unblacklist,
}

impl From<u8> for EventKind {
    fn from(value: u8) -> Self {
        match value {
            0 => EventKind::ApprovedApplication,
            1 => EventKind::Blacklist,
            2 => EventKind::Unblacklist,
            _ => panic!("Invalid EnrollmentEventType"),
        }
    }
}

impl Display for EventKind {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}", self)
    }
}

/// Enrollment event is an event that is emitted by the KYC operator
/// when a trader's enrollment status is updated.
///
/// A timestamp is not included in the event struct because a timestamp is
/// already included in the metadata.
///
/// An untrusted timestamp is inserted into the database when the event is logged.
/// The untrusted timestamp is used for indexing and querying the event.
#[derive(Default, Clone, PartialEq, Serialize, Deserialize)]
pub struct EnrollmentEvent {
    // The trader address of the event
    pub address: Address,
    pub kind: EventKind,
    // The nonce is unique and ascending for each event
    // and is used to prevent replay attacks
    pub nonce: u64,
    // The event metadata is CBOR serialized to byte slice
    // The event metadata is sealed for approved application event
    // and is not sealed for blacklist and unblacklist events
    pub metadata: Vec<u8>,
}

impl Debug for EnrollmentEvent {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self)
    }
}

impl Display for EnrollmentEvent {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "EnrollmentEvent {{ address: {}, kind: {}, nonce: {} }}",
            self.address, self.kind, self.nonce
        )
    }
}

impl EnrollmentEvent {
    pub fn new(metadata: Vec<u8>, kind: EventKind, nonce: u64, address: Address) -> Self {
        Self {
            metadata,
            kind,
            nonce,
            address,
        }
    }
}

// Use simple keccak256 hash for EnrollmentEvent to align with the exchange `Cmd` type
impl Keccak256<Hash> for EnrollmentEvent {
    fn keccak256(&self) -> Hash {
        let pre_image = DynSolValue::Tuple(vec![
            (self.kind as u8).into(),
            self.nonce.into(),
            self.address.into(),
            self.metadata.clone().into(),
        ])
        .abi_encode();
        keccak256(&pre_image).into()
    }
}
