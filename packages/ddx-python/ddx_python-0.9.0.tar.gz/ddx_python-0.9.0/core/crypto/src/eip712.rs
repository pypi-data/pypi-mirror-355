use crate::{hash_public_key, public_key_address, recover, recover_public_key};
use core_common::{
    Address, B256, Result, U256,
    constants::KECCAK256_DIGEST_SIZE,
    types::{
        primitives::{Bytes32, Hash, Keccak256, SessionSignature, Signature, TraderAddress},
        state::Chain,
    },
};

pub trait HashEIP712 {
    /// Computes the EIP-712 hash with no context
    fn hash_eip712_raw(&self, chain: Chain, contract_address: Address) -> Hash;
    /// Computes the EIP-712 hash with the application context
    fn hash_eip712(&self) -> Hash {
        let context = core_common::global::app_context();
        self.hash_eip712_raw(context.chain, context.contract_address)
    }
}

pub trait Signed1ctEIP712 {
    fn eip712_signature(&self) -> Signature;

    fn session_key_signature(&self) -> SessionSignature;
}

pub trait SignedEIP712: HashEIP712 {
    /// Returns the included signature
    fn signature(&self) -> Signature;

    /// Recovers the message hash and signer
    #[tracing::instrument(level = "debug", skip_all, fields(hash, signature, signer))]
    fn recover_signer(&self) -> Result<(Hash, TraderAddress)> {
        let hash = self.hash_eip712();
        tracing::Span::current().record("hash", hash.to_string());
        let signature = self.signature();
        tracing::Span::current().record("signature", format!("{:?}", signature));
        let signer = TraderAddress::from(recover(hash.into(), signature.into())?);
        tracing::Span::current().record("signer", signer.to_string());
        Ok((hash, signer))
    }
}

pub trait MultisigEIP712: HashEIP712 {
    /// Returns the included signatures
    fn signatures(&self) -> Vec<Signature>;

    /// Recovers the message hash and signers
    fn recover_signers(&self) -> Result<(Hash, Vec<TraderAddress>)> {
        let hash = self.hash_eip712();
        let signers = self
            .signatures()
            .into_iter()
            .map(|signature| recover(hash.into(), signature.into()))
            .collect::<Result<Vec<_>>>()?
            .iter()
            .map(TraderAddress::from)
            .collect();
        Ok((hash, signers))
    }
}

pub struct Message(Vec<u8>);

impl Message {
    pub fn new(chain: Chain, contract_address: Address) -> Self {
        let mut message: Vec<u8> = Vec::new();
        // EIP191 header for EIP712 prefix
        message.extend_from_slice(b"\x19\x01");
        let mut domain_message: Vec<u8> = Vec::new();
        let eip712_domain_separator =
            b"EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
                .keccak256();
        let domain_name_hash = b"DerivaDEX".keccak256();
        let domain_version_hash = b"1".keccak256();
        let Chain::Ethereum(chain_id) = chain;
        domain_message.extend_from_slice(eip712_domain_separator.as_ref());
        domain_message.extend_from_slice(domain_name_hash.as_ref());
        domain_message.extend_from_slice(domain_version_hash.as_ref());
        domain_message.extend_from_slice(&B256::from(U256::from(chain_id)).0);
        domain_message.extend_from_slice(Bytes32::from(contract_address).as_bytes());
        // Adding the domain header to the message
        let domain_hash = domain_message.keccak256();
        message.extend_from_slice(domain_hash.as_ref());
        Message(message)
    }

    pub fn append_payload(&mut self, payload: Payload) {
        self.0.extend_from_slice(payload.0.keccak256().as_ref());
    }

    pub fn finalize(&self) -> Hash {
        let bytes: [u8; KECCAK256_DIGEST_SIZE] = self.0.keccak256();
        Hash::from(bytes)
    }
}

pub struct Payload(Vec<u8>);

impl Payload {
    pub fn from_signature(abi_signature: Vec<u8>) -> Payload {
        let mut payload: Vec<u8> = Vec::new();
        let payload_separator_hash = abi_signature.keccak256();
        payload.extend_from_slice(payload_separator_hash.as_ref());
        Payload(payload)
    }

    pub fn append<F: Into<B256>>(&mut self, field: F) {
        self.0.extend_from_slice(&field.into().0);
    }
}

impl<T> SignedEIP712 for T
where
    T: Signed1ctEIP712 + HashEIP712,
{
    /// Returns the included signature
    fn signature(&self) -> Signature {
        self.eip712_signature()
    }

    /// Recovers the message hash and signer
    #[tracing::instrument(level = "debug", skip_all, fields(hash, signature, signer))]
    fn recover_signer(&self) -> Result<(Hash, TraderAddress)> {
        // Get the session public key
        let hash = self.hash_eip712();
        tracing::Span::current().record("1CT intent hash", hash.to_string());
        let signature = self.signature();
        let initial_public_key = recover_public_key(&hash.into(), signature.into())?;
        tracing::debug!(
            ?initial_public_key,
            "initial public key recovered from 1CT intent",
        );

        // Get the trader address
        let session_key_signature = self.session_key_signature();
        let signer = if let Some(session_sig) = session_key_signature {
            tracing::debug!(
                "1CT intent was signed by a session key, need to recover the trader address still"
            );
            let session_signer_hash = hash_public_key(initial_public_key);
            TraderAddress::from(recover(session_signer_hash, session_sig.into())?)
        } else {
            TraderAddress::from(public_key_address(initial_public_key))
        };
        tracing::debug!("signer recovered from 1CT intent {:?}", &signer.to_string());
        Ok((hash, signer))
    }
}
