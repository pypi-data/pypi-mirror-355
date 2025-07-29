/// Simplified crypto tooling inspired by Rust web3 but using the secp256k1 tooling directly
///
/// While the Web3 public accounts/signing modules have many can are only usable with a full
/// Ethereum client, this one has no external dependency so can run in the enclave.
/// The Web3 tooling uses several complex intermediary structures but we stick to
/// alloy and libsecp256k1 primitives.
///
/// We're using Parity's libsecp256k1 which is a pure Rust implementation with an SGX port,
/// `no_std` support and Ethereum recovery id built-in. Web3 uses rust-secp256k1, a wrapper around
/// Bitcoin's secp256k1 C library.
use libsecp256k1::{Message, RecoveryId, SecretKey, Signature, curve::ECMultGenContext};

#[cfg(not(target_vendor = "teaclave"))]
pub(crate) mod untrusted {
    use super::*;

    /// Sign with the HMAC utility detected by `libsecp256k1`
    pub fn sign_with_context(
        message: &Message,
        secret_key: &SecretKey,
        context: &ECMultGenContext,
    ) -> (Signature, RecoveryId) {
        libsecp256k1::sign_with_context(message, secret_key, context)
    }
}

#[cfg(target_vendor = "teaclave")]
pub(crate) mod trusted {
    use super::*;
    use libsecp256k1::curve::Scalar;
    use sgx_crypto::mac::{HMac, HashType};

    /// Sign using the SGX hardware accelerated HMAC utility
    pub fn sign_with_context(
        message: &Message,
        secret_key: &SecretKey,
        context: &ECMultGenContext,
    ) -> (Signature, RecoveryId) {
        tracing::trace!("Signing message {:?} with SGX hmac", message);
        let seckey_b32 = secret_key.serialize();
        let message_b32 = message.serialize();

        let mut nonce = Scalar::default();
        // Expecting the SGX hmac to never overflow.
        let hash = HashType::Sha256;
        let hmac = HMac::hmac(&seckey_b32, hash, message_b32.as_slice())
            .expect("Failed SGX hmac instructions");
        tracing::trace!("The SGX hmac bytes {:?}", hmac);
        let _overflowed = nonce.set_b32(&hmac);

        let mut seckey = Scalar::default();
        let _overflowed = seckey.set_b32(&seckey_b32);

        let mut message = Scalar::default();
        let _overflowed = message.set_b32(&message_b32);

        // This will never fail as long as the SGX hmac does not not overflow.
        let (r, s, recid) = context
            .sign_raw(&seckey, &message, &nonce)
            .expect("Failed libsecp256k1 signature");
        tracing::trace!("The signature - r {:?} - s {:?} - recid {:?}", r, s, recid);
        (Signature { r, s }, RecoveryId::parse(recid).unwrap())
    }
}
