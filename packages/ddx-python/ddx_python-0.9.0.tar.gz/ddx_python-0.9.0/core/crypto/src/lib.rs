#![allow(unexpected_cfgs)]
use core_common::{
    Address, B256, B520, Error, Result,
    constants::{
        AES_KEY_LEN, AES_NONCE_LEN, COMPRESSED_KEY_BYTE_LEN, ENCRYPTED_CONTEXT_SUFFIX_SIZE,
        MAX_PLAINTEXT_SIZE, MIN_CIPHERTEXT_SIZE, SCALAR_BYTE_LEN, SECRET_KEY_LEN,
    },
    ensure, error,
    types::{
        primitives::{Keccak256, TraderAddress},
        state::BlockchainSender,
    },
};
use digest::{Digest, Output, generic_array::GenericArray};
use lazy_static::lazy_static;
use libsecp256k1::{Message, RecoveryId, SharedSecret, Signature, util::FULL_PUBLIC_KEY_SIZE};
use rustc_hex::{FromHex, ToHex};
use std::{boxed::Box, format, mem::size_of, vec::Vec};
use tiny_keccak::keccak256;
use typenum::Unsigned;

#[cfg(not(target_family = "wasm"))]
pub mod eip712;
mod encryption;
mod signing;
#[cfg(all(not(target_family = "wasm"), feature = "test_account"))]
pub mod test_accounts;

#[cfg(target_vendor = "teaclave")]
extern crate sgx_types;

pub const DUMMY_PRNG_SEED: [u8; 32] = [
    1, 0, 0, 0, 23, 0, 0, 0, 200, 1, 0, 0, 210, 30, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0,
];

#[cfg(target_vendor = "teaclave")]
pub use encryption::trusted::{do_decrypt, do_encrypt};
#[cfg(not(target_vendor = "teaclave"))]
pub use encryption::untrusted::{do_decrypt, do_encrypt};
#[cfg(target_vendor = "teaclave")]
pub use signing::trusted::sign_with_context;
#[cfg(not(target_vendor = "teaclave"))]
pub use signing::untrusted::sign_with_context;

pub use libsecp256k1::{PublicKey, SecretKey, util::COMPRESSED_PUBLIC_KEY_SIZE};

const RAW_PUBLIC_KEY_SIZE: usize = FULL_PUBLIC_KEY_SIZE - 1;

lazy_static! {
    /// A static ECMult context.
    static ref ECMULT_CONTEXT: Box<libsecp256k1::curve::ECMultContext> = libsecp256k1::curve::ECMultContext::new_boxed();

    /// A static ECMultGen context.
    static ref ECMULT_GEN_CONTEXT: Box<libsecp256k1::curve::ECMultGenContext> = libsecp256k1::curve::ECMultGenContext::new_boxed();
}

/// Gets the address of a public key.
///
/// The public address is defined as the low 20 bytes of the keccak hash of
/// the public key.
pub fn public_key_address(public_key: PublicKey) -> Address {
    let raw_public_key = raw_public_key(public_key);
    let hash = keccak256(raw_public_key.as_slice());
    Address::from_slice(&hash[12..])
}

/// EIP-191 hashes a public key
///
/// This function hashes a public key and returns a 32 byte hash.
/// The hash is used to sign a message with the public key.
pub fn hash_public_key(public_key: PublicKey) -> B256 {
    let session_signer_bytes = public_key.serialize();
    // 1CT signs the session signer hex string as the message
    let session_signer_hex_string = format!("0x{}", session_signer_bytes.to_hex::<String>());
    let session_signer_hex_string_bytes = session_signer_hex_string.as_bytes();
    let mut eth_message = format!(
        "\x19Ethereum Signed Message:\n{}",
        session_signer_hex_string_bytes.len()
    )
    .into_bytes();
    eth_message.extend_from_slice(session_signer_hex_string_bytes);
    let session_signer_hash = keccak256(&eth_message);
    session_signer_hash.into()
}

/// Removes the uncompressed key prefix from the `PublicKey`
///
/// The public key returned from the `secp256k1`
/// crate is 65 bytes long, that is because it is prefixed by `0x04` to
/// indicate an uncompressed public key; this first byte is ignored when
/// computing the hash. What we call raw is the uncompressed public key bytes without the prefix.
fn raw_public_key(public_key: PublicKey) -> [u8; RAW_PUBLIC_KEY_SIZE] {
    let bytes = public_key.serialize();
    debug_assert_eq!(bytes[0], 0x04);
    let mut raw_bytes = [0_u8; RAW_PUBLIC_KEY_SIZE];
    raw_bytes.copy_from_slice(&bytes[1..]);
    raw_bytes
}

/// Derive the public key from the given private key.
pub fn derive_pub_key(key: &SecretKey) -> PublicKey {
    PublicKey::from_secret_key_with_context(key, &ECMULT_GEN_CONTEXT)
}

/// Gets the public address of a private key.
///
/// The signer pub key abridged to 20 bytes for Ethereum verification.
pub fn secret_key_address(key: &SecretKey) -> Address {
    let public_key = PublicKey::from_secret_key_with_context(key, &ECMULT_GEN_CONTEXT);
    public_key_address(public_key)
}

/// Hash a message without any system-specific prefix
///
/// Contains all of the data that shows that a signatory signed a message without any
/// system-specific context.
pub fn hash_without_prefix<S>(message: S) -> B256
where
    S: AsRef<[u8]>,
{
    let message = message.as_ref();
    keccak256(message).into()
}

/// Hash an intermediary according to EIP-191.
///
/// All our prefixed hashes must be double-hashed. This ensures the availability of hash
/// representations free of system-specific context.
///
/// The data is a UTF-8 encoded string and will enveloped as follows:
/// `"\x19Ethereum Signed Message:\n" + message.length + message` and hashed
/// using keccak256.
pub fn hash_with_eth_prefix(intermediary_hash: B256) -> B256 {
    let message = intermediary_hash.as_slice();
    let mut eth_message = format!("\x19Ethereum Signed Message:\n{}", message.len()).into_bytes();
    eth_message.extend_from_slice(message);
    keccak256(&eth_message).into()
}

fn sign_message_internal(
    key: &SecretKey,
    message_hash: B256,
) -> Result<(u8, [u8; SCALAR_BYTE_LEN], [u8; SCALAR_BYTE_LEN])> {
    let message = Message::parse_slice(message_hash.as_slice())?;
    let (signature, recovery_id) = sign_with_context(&message, key, &ECMULT_GEN_CONTEXT);
    let standard_v: u8 = recovery_id.into();
    let v = standard_v + 27_u8;
    Ok((v, signature.r.b32(), signature.s.b32()))
}

/// Sign pre-constructed message hash
///
/// The data is UTF-8 encoded and enveloped the same way as with
/// `hash_message`. The returned signed data's signature is in 'Electrum'
/// notation, that is the recovery value `v` is either `27` or `28` (as
/// opposed to the standard notation where `v` is either `0` or `1`). This
/// is important to consider when using this signature with other crates.
///
/// This should be compatible with the ethers.js equivalent: https://github.com/ethers-io/ethers.js/blob/2df9dd11204726bdf9a1af3d5b72d7e5549179ec/packages/abstract-signer/src.ts/index.ts#L71
/// assuming a message hashed with prefix.
pub fn sign_message(key: &SecretKey, message_hash: B256) -> Result<B520> {
    let mut bytes: Vec<u8> = Vec::with_capacity(size_of::<B520>());
    let (v, r, s) = sign_message_internal(key, message_hash)?;
    bytes.extend_from_slice(&r);
    bytes.extend_from_slice(&s);
    bytes.push(v);

    let mut slice = [0_u8; size_of::<B520>()];
    slice.copy_from_slice(&bytes);
    Ok(B520::new(slice))
}

fn split_signature(signature: B520) -> Result<(core_common::B512, RecoveryId)> {
    let bytes = signature.as_slice();
    let v = bytes[64];
    let mut sig = [0u8; 64];
    sig[..32].copy_from_slice(&bytes[0..32]);
    sig[32..].copy_from_slice(&bytes[32..64]);
    let recovery_id = RecoveryId::parse_rpc(v)?;
    Ok((core_common::B512::new(sig), recovery_id))
}

pub fn recover_public_key(message_hash: &B256, signature: B520) -> Result<PublicKey> {
    let message = Message::parse_slice(message_hash.as_slice())?;
    let (signature, recovery_id) = split_signature(signature)?;
    let sig = Signature::parse_standard_slice(&signature.0)?;
    if sig.s.is_high() {
        return Err(error!("Signature is not compliant with EIP-2"));
    }
    Ok(libsecp256k1::recover_with_context(
        &message,
        &sig,
        &recovery_id,
        &ECMULT_CONTEXT,
    )?)
}

pub fn recover(message_hash: B256, signature: B520) -> Result<Address> {
    let public_key = recover_public_key(&message_hash, signature)?;
    Ok(public_key_address(public_key))
}

fn derive_aes_key(secret_key: &SecretKey, public_key: &PublicKey) -> Result<[u8; AES_KEY_LEN]> {
    let shared_secret: SharedSecret<Keccak256Digest> =
        SharedSecret::new_with_context(public_key, secret_key, &ECMULT_CONTEXT)?;
    // Generating 128-bit key from keccak256 hash
    let bytes = shared_secret.as_ref()[..AES_KEY_LEN].to_vec();
    let mut result = [0_u8; AES_KEY_LEN];
    result.copy_from_slice(&bytes);
    Ok(result)
}

/// Encrypts the given message by deriving an aes key from the asymmetric key pair provided.
///
/// This function is mostly called from where inputs are deterministic so it is not the place
/// to put validation. Only do validation where inputs are non-deterministic (user provided).
pub fn encrypt(
    message: Vec<u8>,
    secret_key_bytes: &[u8; SECRET_KEY_LEN],
    network_public_key: &[u8; COMPRESSED_PUBLIC_KEY_SIZE],
    nonce_bytes: [u8; AES_NONCE_LEN],
) -> Result<Vec<u8>> {
    let network_public_key = PublicKey::parse_compressed(network_public_key)?;
    let secret_key = SecretKey::parse(secret_key_bytes)?;
    let enc_content = encrypt_with_nonce(message, &secret_key, &network_public_key, nonce_bytes)?;
    Ok(enc_content.serialize())
}

/// Encrypts an arbitrary message with with the specified nonce
///
/// A nonce is a 12-bytes value that salts the message for uniqueness. This prevents attackers
/// from reusing message and makes encryption less secure by entropy. We use a random number
/// generator to avoid leaking any pattern that could be reverse engineered.
///
/// We expect clients to encrypt using JavaScript on the frontend. To help test this workflow,
/// here is an equivalent function using the Forge crypto library.
///
/// ```javascript
/// function encryptWithNonce(message, keyHex, nonce = forge.random.getBytesSync(12)) {
//   let key = forge.util.hexToBytes(keyHex);
//   const cipher = forge.cipher.createCipher('AES-GCM', key);
//
//   cipher.start({iv: nonce});
//   cipher.update(forge.util.createBuffer(message));
//   cipher.finish();
//
//   let result = cipher.output.putBuffer(cipher.mode.tag).putBytes(nonce);
//
//   return result.toHex();
// }
/// ```
///
pub fn encrypt_with_nonce(
    message: Vec<u8>,
    secret_key: &SecretKey,
    public_key: &PublicKey,
    nonce: [u8; AES_NONCE_LEN],
) -> Result<EncryptedContent> {
    ensure!(
        message.len() <= MAX_PLAINTEXT_SIZE,
        "Expected the plaintext size to be at most {:?}",
        MAX_PLAINTEXT_SIZE
    );
    tracing::debug!(
        "Encrypting {:?} byte(s) with nonce {:?}",
        message.len(),
        nonce
    );
    let derived_key = derive_aes_key(secret_key, public_key)?;
    // Safe cast because we verify the message size
    let plaintext_len = message.len() as u32;
    let plaintext_len_fixed_bytes: [u8; size_of::<u32>()] = plaintext_len.to_be_bytes();
    // Encoding plaintext size before the message to reliably truncate on decryption.
    // Including in the encrypted message, not as tags, to avoid unnecessarily leaking data.
    let mut ciphertext = plaintext_len_fixed_bytes.to_vec();
    ciphertext.extend(message);
    do_encrypt(&mut ciphertext, derived_key, nonce)?;
    tracing::debug!(
        "Encrypted message - Size before {:?} / size after {:?}",
        plaintext_len,
        ciphertext.len()
    );
    Ok(EncryptedContent {
        ciphertext,
        nonce,
        public_key: PublicKey::from_secret_key_with_context(secret_key, &ECMULT_GEN_CONTEXT)
            .serialize_compressed(),
    })
}

/// Decrypts a cipher text encrypted with a 12 bytes nonce
///
/// The `encrypt_with_nonce` function above is an example for such encryption. Use it to
/// validate any external encryption tooling. Clients may use the tooling of their choice.
/// We have tested JavaScript using Forge: https://github.com/digitalbazaar/forge#aes
pub fn decrypt(encrypted_content: EncryptedContent, secret_key: &SecretKey) -> Result<Vec<u8>> {
    let EncryptedContent {
        mut ciphertext,
        nonce,
        public_key,
    } = encrypted_content;
    let public_key = PublicKey::parse_compressed(&public_key)?;
    let key_fixed_bytes = derive_aes_key(secret_key, &public_key)?;
    do_decrypt(&mut ciphertext, key_fixed_bytes, nonce)?;
    // Truncating the plaintext using encoded len bytes
    let mut plaintext = ciphertext.split_off(size_of::<u32>());
    let mut plaintext_len_fixed_bytes = [0_u8; size_of::<u32>()];
    plaintext_len_fixed_bytes.copy_from_slice(&ciphertext);
    let plaintext_len = u32::from_be_bytes(plaintext_len_fixed_bytes);
    plaintext.truncate(plaintext_len as usize);
    Ok(plaintext)
}

pub fn parse_secret_key<S: AsRef<str>>(hex_str: S) -> Result<SecretKey> {
    let bytes = from_hex(hex_str)?;
    let key = SecretKey::parse_slice(&bytes)?;
    Ok(key)
}

pub fn from_hex<B: AsRef<str>>(hex: B) -> Result<Vec<u8>> {
    hex.as_ref()
        .replace("0x", "")
        .from_hex::<Vec<u8>>()
        .map_err(|source| Error::Parse(format!("{:?}", source)))
}

#[derive(Debug, Clone)]
pub struct EncryptedContent {
    // The MAC is appended to the ciphertext
    ciphertext: Vec<u8>,
    nonce: [u8; AES_NONCE_LEN],
    public_key: [u8; COMPRESSED_KEY_BYTE_LEN],
}

impl EncryptedContent {
    pub fn serialize(&self) -> Vec<u8> {
        let mut bytes = self.ciphertext.clone();
        bytes.extend_from_slice(self.nonce.as_slice());
        bytes.extend_from_slice(self.public_key.as_slice());
        bytes
    }

    pub fn deserialize(mut bytes: Vec<u8>) -> Result<EncryptedContent> {
        EncryptedContent::check(&bytes)?;
        // Split the ciphertext apart from the nonce and public key
        let suffix = bytes.split_off(bytes.len() - ENCRYPTED_CONTEXT_SUFFIX_SIZE);
        ensure!(
            suffix.len() == ENCRYPTED_CONTEXT_SUFFIX_SIZE,
            "Expected the encrypted payload suffix size be {:?} bytes but got {:?} byte(s)",
            ENCRYPTED_CONTEXT_SUFFIX_SIZE,
            suffix.len()
        );
        let mut nonce = [0_u8; AES_NONCE_LEN];
        nonce.copy_from_slice(&suffix[..AES_NONCE_LEN]);
        let mut public_key = [0_u8; COMPRESSED_KEY_BYTE_LEN];
        public_key.copy_from_slice(&suffix[AES_NONCE_LEN..]);
        Ok(EncryptedContent {
            ciphertext: bytes,
            nonce,
            public_key,
        })
    }

    // TODO: Catch this at the infrastructure (nginx) layer
    pub fn check(bytes: &[u8]) -> Result<()> {
        ensure!(
            bytes.len() >= MIN_CIPHERTEXT_SIZE + ENCRYPTED_CONTEXT_SUFFIX_SIZE,
            "Expected the encrypted payload size to be at least {:?} bytes but got {:?} bytes",
            MIN_CIPHERTEXT_SIZE + ENCRYPTED_CONTEXT_SUFFIX_SIZE,
            bytes.len()
        );
        Ok(())
    }
}

pub trait SenderAddress {
    fn address(&self) -> TraderAddress;
    fn eth_address(&self) -> Address;
    fn abbrev_id(&self) -> u64;
}

impl SenderAddress for BlockchainSender {
    fn address(&self) -> TraderAddress {
        self.eth_address().into()
    }

    fn eth_address(&self) -> Address {
        match self {
            BlockchainSender::UnlockedAccount(address) => *address,
            BlockchainSender::SecretKey(_secret_key) => secret_key_address(
                &libsecp256k1::SecretKey::parse(_secret_key)
                    .expect("Private key to be a valid Secp256k1 private key"),
            ),
        }
    }

    fn abbrev_id(&self) -> u64 {
        let address = self.eth_address();
        let mut fixed = [0; 8];
        fixed.copy_from_slice(&address.0[0..8]);
        u64::from_be_bytes(fixed)
    }
}

/// Wrapper around tiny-keccak that implements the standard `Digest` trait
#[derive(Clone, Debug, Default)]
struct Keccak256Digest(Vec<u8>);

impl Digest for Keccak256Digest {
    type OutputSize = typenum::U32;

    fn new() -> Self {
        Default::default()
    }

    fn update(&mut self, data: impl AsRef<[u8]>) {
        self.0.extend_from_slice(data.as_ref())
    }

    fn chain(self, data: impl AsRef<[u8]>) -> Self
    where
        Self: Sized,
    {
        let mut digest = self;
        digest.update(data);
        digest
    }

    fn finalize(self) -> Output<Self> {
        GenericArray::from(self.0.keccak256())
    }

    fn finalize_reset(&mut self) -> Output<Self> {
        let hash = GenericArray::from(self.0.keccak256());
        self.reset();
        hash
    }

    fn reset(&mut self) {
        self.0 = vec![];
    }

    fn output_size() -> usize {
        Self::OutputSize::to_usize()
    }

    fn digest(data: &[u8]) -> GenericArray<u8, Self::OutputSize> {
        let mut hasher = Self::default();
        hasher.update(data);
        hasher.finalize()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use core_common::constants::{AES_NONCE_LEN, SECRET_KEY_LEN};
    use rand::{RngCore, SeedableRng, prelude::StdRng};
    use rustc_hex::ToHex;
    use std::string::String;

    #[test]
    fn test_encryption_workflow() {
        // Emulates the network key sealed by each operator. This key is never visible outside of
        // a registered enclave.
        let mut network_key = vec![0_u8; SECRET_KEY_LEN];
        StdRng::from_seed(DUMMY_PRNG_SEED).fill_bytes(&mut network_key);
        let network_secret_key = SecretKey::parse_slice(&network_key).expect("Parse network key");

        // The well-know network public key. Expect each client to store it as a static constant.
        let network_public_key = derive_pub_key(&network_secret_key);
        tracing::debug!(
            "Created key material for this test \
             - Private {:?}\
             - Public (compressed) {:?} => 0x{}",
            network_secret_key.serialize(),
            network_public_key.serialize_compressed(),
            network_public_key.serialize_compressed().to_hex::<String>(),
        );
        // Emulates the ephemeral key material a client would generate before sending requests.
        // See E2E encrypted messaging apps like RocketChat for examples of randomness used
        // and whether to reuse the same key between requests.
        let client_secret_key = {
            let mut client_key = [0_u8; SECRET_KEY_LEN];
            StdRng::from_seed(DUMMY_PRNG_SEED).fill_bytes(&mut client_key);
            SecretKey::parse_slice(client_key.as_slice()).expect("Parse client key")
        };
        // The client public key (included in the client generated key material)
        let client_public_key = derive_pub_key(&client_secret_key);
        let derived_key = derive_aes_key(&network_secret_key, &client_public_key).unwrap();
        assert_eq!(
            derived_key,
            derive_aes_key(&client_secret_key, &network_public_key).unwrap()
        );
        tracing::debug!("The common derived key {:?}", derived_key);
        // Emulates a random 12 bytes number generated by the client. Again, there are examples
        // in apps like RocketChat. This can be pseudo-randomly generated.
        let mut nonce = [0_u8; AES_NONCE_LEN];
        StdRng::from_seed(DUMMY_PRNG_SEED).fill_bytes(&mut nonce);
        // Emulates the client message bytes to encrypt. We use simple UTF-8 bytes to keep the
        // test minimal. A client is expected to use the CBOR encoded bytes of a request.
        let message = "Hello World!".as_bytes();
        // Emulates client-side encryption. The client has all of the parameters as we've
        // established above. However, we expect clients to call their own secp256 and aes tooling.
        // JS clients may use this actual utility via the npm package generated by `ddx-wasm`.
        let enc_content = encrypt_with_nonce(
            message.to_vec(),
            &client_secret_key,
            &network_public_key,
            nonce,
        )
        .unwrap();
        // The actual decryption fn the operator calls upon receiving a request. The
        // `EncryptedContent` is deserialized from input bytes. The network secret key is sealed
        // in protected memory.
        let bytes = decrypt(enc_content, &network_secret_key).unwrap();
        let plaintext = String::from_utf8_lossy(&bytes);
        assert_eq!(plaintext, "Hello World!");
    }

    #[test]
    fn test_signature_recovery_with_high_s() {
        let mut bytes = [0u8; 32];
        StdRng::from_seed(DUMMY_PRNG_SEED).fill_bytes(&mut bytes);
        let message_hash = B256::new(bytes);
        let client_secret_key = {
            let mut client_key = [0_u8; SECRET_KEY_LEN];
            StdRng::from_seed(DUMMY_PRNG_SEED).fill_bytes(&mut client_key);
            SecretKey::parse_slice(client_key.as_slice()).expect("Parse client key")
        };
        let original_sig = sign_message(&client_secret_key, message_hash).unwrap();
        // Recover signature normally
        let _address = recover(message_hash, original_sig).unwrap();
        let (signature, rec_id) = split_signature(original_sig).unwrap();
        // Confirm that signature is low s
        let mut sig = Signature::parse_standard_slice(&signature.0).unwrap();
        assert!(!sig.s.is_high());
        // Modify signature to use high s, and try to recover again
        sig.s = -sig.s;
        let new_signature = sig.serialize();
        let mut sig = [0u8; 65];
        sig[..64].copy_from_slice(&new_signature);
        sig[64] = rec_id.serialize() + 27_u8;
        let invalid_recovery = recover(message_hash, sig.into());
        assert!(invalid_recovery.is_err());
        let err = invalid_recovery.expect_err("Expected signature recovery to fail");
        assert!(
            err.to_string().contains("not compliant with EIP-2"),
            "Expected signature to not be compliant with EIP-2, got: {}",
            err
        );
    }
}
