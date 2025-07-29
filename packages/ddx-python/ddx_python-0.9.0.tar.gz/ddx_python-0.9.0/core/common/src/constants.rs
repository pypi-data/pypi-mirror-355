use crate::{B520, types::accounting::StrategyId};
use alloy_primitives::Address;
use core_macros::dec;

// Chain constants
pub const CHAIN_ETHEREUM: u8 = 0;
pub const CHAIN_ID_ETHEREUM_MAINNET: u64 = 1;

// Symmetric crypto
pub const MIN_CIPHERTEXT_SIZE: usize = 4 + 1;
pub const MAX_PLAINTEXT_SIZE: usize = 8192;
pub const ENCRYPTED_CONTEXT_SUFFIX_SIZE: usize = 12 + 33;

// Shared buffer size
pub const KYC_MAX_LEN: usize = 1024;
pub const ENCRYPTED_CONTENT_MAX_LEN: usize = 1024;
// Cryptography related.
pub const AES_KEY_LEN: usize = 16;
pub const AES_NONCE_LEN: usize = 12;
pub const AES_TAG_LEN: usize = 16;
pub const SCALAR_BYTE_LEN: usize = std::mem::size_of::<libsecp256k1::curve::Scalar>();
pub const SECRET_KEY_LEN: usize = libsecp256k1::util::SECRET_KEY_SIZE;
pub const SIGNATURE_BYTE_LEN: usize = size_of::<B520>();
pub const ADDRESS_BYTE_LEN: usize = size_of::<Address>();
pub const COMPRESSED_KEY_BYTE_LEN: usize = 33;
pub const SIGNER_ADDRESS_BYTE_LEN: usize = 21;
pub const CUSTODIAN_ADDRESS_BYTE_LEN: usize = 21;
pub const TRADER_ADDRESS_BYTE_LEN: usize = 21;
pub const NONCE_BYTE_LEN: usize = 32;
// This value is manually evaluated since `AttestationUserData` is a private type in `core-enclave`.
pub const USER_DATA_LEN: usize = ADDRESS_BYTE_LEN * 2;
pub const KECCAK256_DIGEST_SIZE: usize = 256 / 8;
pub const STRATEGY_ID_BYTE_LEN: usize = size_of::<StrategyId>();
// Snapshot eth rpc url
pub const SNAPSHOT_ETH_RPC_URL: &str = "http://ethereum:8545";
// Alchemy endpoint path
pub const ALCHEMY_ENDPOINT_PATH: &str = "g.alchemy.com/v2";
// Unit for scaling up decimals to integer representing units of tokens (i.e. 10**18)
pub const TOKEN_UNIT_SCALE: u32 = 6;
// The max decimal number than can be scaled to u128 and then unscaled back to Decimal without overflowing
// Calculated with: Decimal::MAX / Decimal::exp10(6)
pub const MAX_UNSCALED_DECIMAL: rust_decimal::Decimal = dec!(79228162514264337593543.950335);

pub const RUNTIME_MAX_WORKER_THREADS: usize = 4;
// The blocking threads are mainly used for waiting on SGX ECALL
// Must be less than TCS_NUM in `Enclave.config.xml`
pub const MAX_BLOCKING_THREADS: usize = 256;
/// The maximum allowed delay between kyc auth updates
pub const KYC_AUTH_EXPIRY_BLOCK_DELTA: u64 = 7199;
// Application id for smart contract storage, padded to fit 32 bytes
pub const DDX_APPLICATION_ID: &[u8; 32] = b"exchange-operator\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0";
pub const KYC_APPLICATION_ID: &[u8; 32] = b"kyc-operator\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0";
pub const DDX_APPLICATION_ID_LEN: usize = 17;
pub const KYC_APPLICATION_ID_LEN: usize = 12;
