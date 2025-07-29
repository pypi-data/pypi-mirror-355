use alloy_dyn_abi::DynSolValue;
use alloy_primitives::U128;
use core_common::{
    Address, B256,
    types::{
        identifiers::ChainVariant,
        primitives::{Bytes32, Hash, Signature, TimeValue},
        transaction::EpochId,
    },
    util::tokenize::Tokenizable,
};
use core_crypto::{hash_with_eth_prefix, hash_without_prefix};
use core_macros::AbiToken;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

// TODO: The types in this file should be cleaned up given all of the
// refactors that took place in the Checkpoint and Registration facets.
// Additionally, these types would probably be better suited for an
// individual file rather than being lumped with all of the other
// transaction types.
#[derive(Debug, Clone, PartialEq, Default, Serialize, Deserialize, AbiToken)]
#[serde(rename_all = "camelCase")]
pub struct Checkpoint {
    /// Including the block number and hash to ensure that the checkpoint is
    /// only valid on the fork that the operator was tracking.
    /// Use u128 to align with the on-chain type.
    pub block_number: u128,
    pub block_hash: Hash,
    pub state_root: Hash,
    pub transaction_root: Hash,
}

impl From<SignedCheckpoint> for Checkpoint {
    fn from(signed_checkpoint: SignedCheckpoint) -> Self {
        Self {
            block_number: signed_checkpoint.block_number as u128,
            block_hash: signed_checkpoint.block_hash,
            state_root: signed_checkpoint.state_root,
            transaction_root: signed_checkpoint.transaction_root,
        }
    }
}

pub type SignedCheckpoints = HashMap<ChainVariant, SignedCheckpoint>;

/// Signed checkpoint data to be sent to the contract.
/// Corresponds to `OperatorDefs.CheckpointData` data on-chain
#[derive(Debug, Copy, Clone, PartialEq, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
#[repr(C)]
pub struct SignedCheckpoint {
    /// Including the block number and hash to ensure that the checkpoint is
    /// only valid on the fork that the operator was tracking.
    // should use u128 to align with the on-chain type.
    // TODO: use u64 since u128 is not supported by Serde JSON, try to use u128
    // if revert to CBOR encoding.
    pub block_number: u64,
    pub block_hash: Hash,
    pub state_root: Hash,
    pub transaction_root: Hash,
    // TODO: Should this be included in checkpoints
    // submitted to the contracts for some reason? I don't really see the
    // value as of right now considering that it will (1) increase the cost
    // of check-pointing meaningfully and (2) isn't helpful in determining
    // how many trade mining periods have elapsed considering that trade
    // mining periods are measured in checkpoint epochs rather than time value
    // ticks.
    pub time_value: TimeValue,
    /// Including the signer to avoid needing to recover the signer from the
    /// signature if the signer is required to establish an order.
    pub signer: Address,
    /// Including the signature as a field for consistency with other
    /// structures
    pub signature: Signature,
}

#[cfg(not(target_family = "wasm"))]
core_common::impl_contiguous_marker_for!(SignedCheckpoint);

#[cfg(not(target_family = "wasm"))]
core_common::impl_unsafe_byte_slice_for!(SignedCheckpoint);

// TODO: Include time_value in the sig and hash
impl SignedCheckpoint {
    /// Hash the abi encoded parts then hash again with the Ethereum prefix
    pub fn hash(&self, address: &Address, chain_id: u64, epoch_id: EpochId) -> B256 {
        let padded_epoch_id = Bytes32::from(epoch_id);
        let block_number = U128::from(self.block_number);
        let message = DynSolValue::Tuple(vec![
            address.into_token(),
            chain_id.into_token(),
            padded_epoch_id.into_token(),
            block_number.into_token(),
            self.block_hash.into_token(),
            self.state_root.into_token(),
            self.transaction_root.into_token(),
        ])
        .abi_encode();
        let intermediary_hash = hash_without_prefix(message);

        // Move the double hashing here for the signing fn to ensure we can recover from this hash.
        // Signing and recovering should not modify the input hash.
        hash_with_eth_prefix(intermediary_hash)
    }
}

#[derive(Debug, Clone, PartialEq, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CheckpointSubmission {
    pub checkpoint: Checkpoint,
    pub signatures: Vec<Signature>,
}

// TODO: It would be better to just encapsulate this in the AbiToken trait.
impl CheckpointSubmission {
    pub fn into_tokens_for_verification(self) -> DynSolValue {
        let payload = self.checkpoint.into_token();
        let signatures = DynSolValue::Array(
            self.signatures
                .iter()
                .map(|s| {
                    let vrs_signature = s.as_vrs();
                    DynSolValue::Bytes(vrs_signature.as_slice().to_vec())
                })
                .collect::<Vec<_>>(),
        );
        DynSolValue::Tuple(vec![payload, signatures])
    }
}
