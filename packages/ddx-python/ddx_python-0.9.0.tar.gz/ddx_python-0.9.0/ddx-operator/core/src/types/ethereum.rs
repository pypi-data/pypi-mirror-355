use alloy::{
    consensus::{Eip658Value, Header, TxReceipt, TxType},
    eips::{Encodable2718, Typed2718},
    primitives::{Bytes, LogData},
    rlp::{Encodable, Header as RlpHeader},
    rpc::types::TransactionReceipt,
};
use alloy_primitives::{Bloom, U256};
use core_common::{Address, B256, constants::KECCAK256_DIGEST_SIZE};
use hash_db::Hasher;
use plain_hasher::PlainHasher;
use serde::{Deserialize, Serialize};
use serde_big_array::big_array;
use serde_repr::*;

big_array! { BigArray; }

#[derive(Debug, Clone, Default, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ConfirmedBlock {
    pub header: Header,
    pub receipts: Vec<TypedReceipt>,
}

// Wrapper for Alloy EIP658Value, which currently cannot be deserialized correctly with CBOR
#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize)]
pub enum TransactionOutcome {
    StateRoot(B256),
    StatusCode(bool),
}

impl From<Eip658Value> for TransactionOutcome {
    fn from(val: Eip658Value) -> Self {
        match val {
            Eip658Value::Eip658(b) => TransactionOutcome::StatusCode(b),
            Eip658Value::PostState(h) => TransactionOutcome::StateRoot(h),
        }
    }
}

impl From<TransactionOutcome> for Eip658Value {
    fn from(val: TransactionOutcome) -> Self {
        match val {
            TransactionOutcome::StatusCode(b) => Eip658Value::Eip658(b),
            TransactionOutcome::StateRoot(h) => Eip658Value::PostState(h),
        }
    }
}

#[derive(Clone, PartialEq, Eq, Deserialize, Serialize)]
pub struct LegacyReceipt {
    pub gas_used: U256,
    pub bloom: Bloom,
    pub logs: Vec<LogEntry>,
    pub outcome: TransactionOutcome,
}

impl std::fmt::Debug for LegacyReceipt {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        f.debug_struct("LegacyReceipt")
            .field("gas_used", &self.gas_used)
            .field("bloom", &self.bloom)
            .field("logs_summary", &self.logs.iter().map(LogSummary::from))
            .field("outcome", &self.outcome)
            .finish()
    }
}

impl LegacyReceipt {
    pub fn new(
        outcome: TransactionOutcome,
        bloom: Bloom,
        gas_used: u64,
        logs: Vec<LogEntry>,
    ) -> Self {
        LegacyReceipt {
            gas_used: U256::from(gas_used),
            bloom,
            logs,
            outcome,
        }
    }

    /// Returns length of RLP-encoded receipt fields with the given [`Bloom`] without an RLP header.
    pub fn rlp_encoded_fields_length_with_bloom(&self) -> usize {
        let status: Eip658Value = self.outcome.clone().into();
        status.length() + self.gas_used.length() + self.bloom.length() + self.logs.length()
    }

    /// RLP-encodes receipt fields with the given [`Bloom`] without an RLP header.
    pub fn rlp_encode_fields_with_bloom(&self, out: &mut dyn alloy::rlp::BufMut) {
        let status: Eip658Value = self.outcome.clone().into();
        status.encode(out);
        self.gas_used.encode(out);
        self.bloom.encode(out);
        self.logs.encode(out);
    }

    /// Returns RLP header for this receipt encoding with the given [`Bloom`].
    pub fn rlp_header_with_bloom(&self) -> RlpHeader {
        RlpHeader {
            list: true,
            payload_length: self.rlp_encoded_fields_length_with_bloom(),
        }
    }
}

impl Encodable for LegacyReceipt {
    fn encode(&self, out: &mut dyn alloy::rlp::BufMut) {
        self.rlp_header_with_bloom().encode(out);
        self.rlp_encode_fields_with_bloom(out);
    }

    fn length(&self) -> usize {
        self.rlp_header_with_bloom().length_with_payload()
    }
}

#[derive(Serialize_repr, Eq, Hash, Deserialize_repr, Debug, Copy, Clone, PartialEq)]
#[repr(u8)]
pub(crate) enum TypedTxId {
    EIP7702Transaction = 0x04,
    EIP4484Transaction = 0x03,
    EIP1559Transaction = 0x02,
    EIP2930Transaction = 0x01,
    Legacy = 0x00,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum TypedReceipt {
    Legacy(LegacyReceipt),
    EIP2930Transaction(LegacyReceipt),
    EIP1559Transaction(LegacyReceipt),
    EIP4484Transaction(LegacyReceipt),
    EIP7702Transaction(LegacyReceipt),
}

impl TypedReceipt {
    fn type_flag(&self) -> Option<u8> {
        match self.ty() {
            0 => None,
            ty => Some(ty),
        }
    }

    fn as_legacy_receipt(&self) -> &LegacyReceipt {
        match self {
            Self::Legacy(t)
            | Self::EIP2930Transaction(t)
            | Self::EIP1559Transaction(t)
            | Self::EIP4484Transaction(t)
            | Self::EIP7702Transaction(t) => t,
        }
    }
}

impl Typed2718 for TypedReceipt {
    fn ty(&self) -> u8 {
        match self {
            Self::Legacy(_) => 0,
            Self::EIP2930Transaction(_) => 1,
            Self::EIP1559Transaction(_) => 2,
            Self::EIP4484Transaction(_) => 3,
            Self::EIP7702Transaction(_) => 4,
        }
    }
}

impl Encodable2718 for TypedReceipt {
    fn encode_2718_len(&self) -> usize {
        self.as_legacy_receipt().length() + !self.is_legacy() as usize
    }

    fn encode_2718(&self, out: &mut dyn alloy::rlp::BufMut) {
        match self.type_flag() {
            None => {}
            Some(ty) => out.put_u8(ty),
        }
        self.as_legacy_receipt().encode(out);
    }
}

impl From<TransactionReceipt> for TypedReceipt {
    fn from(val: TransactionReceipt) -> Self {
        let envelope = val.as_ref();
        let r = LegacyReceipt::new(
            envelope.status_or_post_state().into(),
            *envelope.logs_bloom(),
            envelope.cumulative_gas_used(),
            envelope
                .logs()
                .iter()
                .cloned()
                .map(|l| LogEntry {
                    address: l.address(),
                    log_data: l.data().clone(),
                    tx_hash: val.transaction_hash,
                })
                .collect(),
        );
        match envelope.tx_type() {
            TxType::Legacy => TypedReceipt::Legacy(r),
            TxType::Eip2930 => TypedReceipt::EIP2930Transaction(r),
            TxType::Eip1559 => TypedReceipt::EIP1559Transaction(r),
            TxType::Eip4844 => TypedReceipt::EIP4484Transaction(r),
            TxType::Eip7702 => TypedReceipt::EIP7702Transaction(r),
        }
    }
}

#[allow(dead_code)]
#[derive(Default, Debug, Clone)]
struct LogSummary {
    address: Address,
    topics: Vec<B256>,
    size: usize,
    tx_hash: B256,
}

impl From<&LogEntry> for LogSummary {
    fn from(log: &LogEntry) -> Self {
        LogSummary {
            address: log.address,
            topics: log.log_data.topics().to_vec(),
            size: log.log_data.data.len(),
            tx_hash: log.tx_hash,
        }
    }
}

#[derive(Default, Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LogEntry {
    pub address: Address,
    pub log_data: LogData,
    // TODO: This isn't trusted and thus shouldn't be used for anything security
    // critical. This seems fine for now since it's primarily used in the frontend.
    pub tx_hash: B256,
}

impl LogEntry {
    pub fn topics(&self) -> &[B256] {
        self.log_data.topics()
    }

    pub fn data(&self) -> &Bytes {
        &self.log_data.data
    }
}

impl Encodable for LogEntry {
    fn encode(&self, out: &mut dyn alloy::rlp::BufMut) {
        let payload_length = self.address.length()
            + self.log_data.data.length()
            + self.log_data.topics().to_vec().length();

        RlpHeader {
            list: true,
            payload_length,
        }
        .encode(out);
        self.address.encode(out);
        self.log_data.topics().to_vec().encode(out);
        self.log_data.data.encode(out);
    }

    fn length(&self) -> usize {
        let payload_length = self.address.length()
            + self.log_data.data.length()
            + self.log_data.topics().to_vec().length();
        payload_length + alloy::rlp::length_of_length(payload_length)
    }
}

#[tracing::instrument(level = "debug", skip_all, fields(receipts=%receipts.len()))]
pub fn extract_contract_events_from_receipts(
    receipts: Vec<TypedReceipt>,
) -> core_common::Result<Vec<super::contract_events::ContractEvent>> {
    let logs: Vec<LogEntry> = receipts
        .into_iter()
        .flat_map(|r| r.as_legacy_receipt().logs.clone())
        .collect();
    let contract_address = core_common::global::app_context().contract_address;
    tracing::debug!(
        ?contract_address,
        "Parsing events from {:?} logs",
        logs.len(),
    );
    let events = logs
        .into_iter()
        .filter(|l| {
            tracing::trace!(address=?l.address, ?contract_address, is_empty=?l.log_data.topics().is_empty(), event_sigs=?crate::types::contract_events::all_event_signatures(), "Filtering contract event");
            l.address == contract_address
                && !l.log_data.topics().is_empty()
                && crate::types::contract_events::all_event_signatures().contains(&l.log_data.topics()[0])
        })
        .map(crate::types::contract_events::decode_contract_events)
        .fold(vec![], |mut acc, v| {
            acc.extend(v);
            acc
        });
    Ok(events)
}

/// Concrete `Hasher` impl for the Keccak-256 hash
#[derive(Default, Debug, Clone, PartialEq)]
struct KeccakHasher;
impl Hasher for KeccakHasher {
    type Out = B256;
    type StdHasher = PlainHasher;
    const LENGTH: usize = KECCAK256_DIGEST_SIZE;
    fn hash(x: &[u8]) -> Self::Out {
        alloy_primitives::keccak256(x)
    }
}

fn ordered_trie_root<I, V>(input: I) -> B256
where
    I: IntoIterator<Item = V>,
    V: AsRef<[u8]>,
{
    triehash::ordered_trie_root::<KeccakHasher, I>(input)
}

pub fn calculate_receipts_root(receipts: &[TypedReceipt]) -> B256 {
    ordered_trie_root(receipts.iter().map(|r| {
        let mut buf = Vec::<u8>::new();
        r.encode_2718(&mut buf);
        buf
    }))
}

#[cfg(feature = "test_harness")]
#[tracing::instrument(level = "debug")]
pub(crate) fn sign_message_with_blockchain_sender(
    sender: &core_common::types::state::BlockchainSender,
    message_hash: B256,
) -> core_common::Result<core_common::B520> {
    let secret_key = if let core_common::types::state::BlockchainSender::SecretKey(secret_key_ser) =
        sender
    {
        core_crypto::SecretKey::parse(&secret_key_ser.0)
            .map_err(|_| core_common::Error::Parse("Couldn't parse secret key from B256.".into()))?
    } else {
        core_common::bail!("TODO: Can't sign message with unlocked account.");
    };
    core_crypto::sign_message(&secret_key, message_hash)
}

#[cfg(test)]
mod test {
    use super::*;
    use alloy::{
        consensus::Receipt,
        primitives::{FixedBytes, Log as PrimitiveLog, b64, fixed_bytes},
        rlp::Encodable,
    };
    use anyhow::Result;
    use core_common::{
        U256,
        types::primitives::{Hash, Keccak256},
    };
    use core_crypto::from_hex;
    use std::str::FromStr;

    const BLOOM_SIZE: usize = 256;

    #[test]
    fn test_block_hash1() -> Result<()> {
        let expected_hash: Hash =
            fixed_bytes!("0x2b5101ecfbaaddd4e37fb21ab43096888ff0e7d25e2e89eb7b3c807965232e73")
                .into();
        let mut bloom = [0; BLOOM_SIZE];
        bloom.copy_from_slice(&from_hex("0x10204000400000011002000080220001101210000000000000000040a800c0000000810000c004000800708008810100023080040a000800000000030830280500000006006221030882000800002070008010001400021000800404c0056120520000000200000080050000000088000010842022004040080008b4010d00200000a02800040000820000002000200000001021110800080020804608104010128c8004000038024a0200b10808801090000001200000041000000808000080000020030000002020000000000c110008000200000a801600801180c00220002138200800000000000400000100000080000004010080404000180000005000")?[..256]);
        let header = Header {
            parent_hash: fixed_bytes!(
                "0x9889ed9e78d883433f6599ede659dfc5105ba69b3ad33fefc8e83e92efdf8409"
            ),
            ommers_hash: fixed_bytes!(
                "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"
            ),
            beneficiary: Address::from_str("0x52bc44d5378309ee2abf1539bf71de1b7d7be3b5")?,
            state_root: fixed_bytes!(
                "0x64591c628e1fec6f8309c4ac05c2b0568974da809337fba2ca14929aa0f805a9"
            ),
            transactions_root: fixed_bytes!(
                "0xe1ff2b3f490298cbd69bd6c8f94af9aa6d95774c53ca16e2729ee4c1b447f022"
            ),
            receipts_root: fixed_bytes!(
                "0xd7fd3b9e7a22b2dcaeb3ef2aaf237bac3ee4679f6e5bfe82bb6eb0e9858a5451"
            ),
            logs_bloom: Bloom(FixedBytes::new(bloom)),
            difficulty: U256::from(8926624369618029_u64),
            number: 13284899,
            gas_limit: 30000000,
            gas_used: 2169791,
            timestamp: 1632438972,
            extra_data: vec![110, 97, 110, 111, 112, 111, 111, 108, 46, 111, 114, 103].into(),
            mix_hash: fixed_bytes!(
                "0x2fba3c00a2a942df87df4941562e288fce6678a90b2a9479352683d4a0df20d6"
            ),
            nonce: b64!("0x5305755edef1be39"),
            base_fee_per_gas: Some(59032141527_u64),
            withdrawals_root: None,
            blob_gas_used: None,
            excess_blob_gas: None,
            parent_beacon_block_root: None,
            requests_hash: None,
        };
        let mut header_buf = Vec::<u8>::new();
        header.encode(&mut header_buf);
        let actual_hash: Hash = header_buf.keccak256().into();
        assert_eq!(actual_hash, expected_hash);

        Ok(())
    }

    #[test]
    fn test_block_hash2() -> Result<()> {
        let expected_hash: Hash =
            fixed_bytes!("0x4fed6603f749a4bd18a5e3cd21922327a18b20167d084e9e25a36e0a3ffcb334")
                .into();
        let mut bloom = [0; BLOOM_SIZE];
        let bloom_bytes = from_hex(
            "0xe1f500c004995004205e0bc3a4008fa98e1123f47cd2081410710010d0b721144222d104302663930051004041dc219442c338c007077381853076a400bf73020a3564120444292cca0e816b227c92e441004008074cf821e0dcac02e22001b1c24461205ea027236008b8e400b6e9d511c3007260096e48e0290790c4280844338a21e56a17e86a244b1440e0312810408804c96847818c0429314850da31c00605102f912290281a0030c3164c302a24546252258600089101174c272242724d3044a2a10cd8582d80109185e6de0381e9080000e861dc091371821f466b2236d0642da2538c20800299a200560a12a2110a2c5990074481e21883220a4708",
        )?;
        bloom.copy_from_slice(&bloom_bytes[..BLOOM_SIZE]);
        let header = Header {
            parent_hash: fixed_bytes!(
                "0x1469313981cb69286cbfbda5c4e9e02018ca6b091939e99cb888ff3fc5ae8cb7"
            ),
            ommers_hash: fixed_bytes!(
                "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"
            ),
            beneficiary: Address::from_str("0x4d496ccc28058b1d74b7a19541663e21154f9c84")?,
            state_root: fixed_bytes!(
                "0x347343a7b838d95ce12f36f12bdc2bdd9e52ca7f7b83fc82bd3ed3fb72973fdd"
            ),
            transactions_root: fixed_bytes!(
                "0x0163a0f504da105424bac01fa7919072af1c3ddc25a041b867f10f5415e7e0b7"
            ),
            receipts_root: fixed_bytes!(
                "0x357f0a0a8c1d51fb7bc487e0b2022ebbbad9f3af47fc48ae5c095766c5e4cf72"
            ),
            logs_bloom: Bloom(FixedBytes::new(bloom)),
            difficulty: Default::default(),
            number: 8656123,
            gas_limit: 30000000_u64,
            gas_used: 29992912_u64,
            timestamp: 1678832784,
            extra_data: from_hex("0xd883010b04846765746888676f312e32302e32856c696e7578")?.into(),
            mix_hash: fixed_bytes!(
                "0xf570e9f413634790998f5af69d0abcd77db8c83f6f8a94496c1ff9b160e4f2c8"
            ),
            nonce: Default::default(),
            base_fee_per_gas: Some(3048311736_u64),
            withdrawals_root: Some(fixed_bytes!(
                "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
            )),
            blob_gas_used: None,
            excess_blob_gas: None,
            parent_beacon_block_root: None,
            requests_hash: None,
        };
        let mut header_buf = Vec::<u8>::new();
        header.encode(&mut header_buf);
        let actual_hash: Hash = header_buf.keccak256().into();
        assert_eq!(actual_hash, expected_hash);

        Ok(())
    }

    #[test]
    fn test_basic_legacy() {
        let expected: Vec<u8> = rustc_hex::FromHex::from_hex("f90162a02f697d671e9ae4ee24a43c4b0d7e15f1cb4ba6de1561120d43b9a4e8c4a8a6ee83040caeb9010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000f838f794dcf421d093428b096ca501a7cd1a740855a7976fc0a00000000000000000000000000000000000000000000000000000000000000000").unwrap();
        let log_data = LogData::new_unchecked(vec![], vec![0u8; 32].into());
        let receipt = Receipt {
            status: fixed_bytes!(
                "2f697d671e9ae4ee24a43c4b0d7e15f1cb4ba6de1561120d43b9a4e8c4a8a6ee"
            )
            .into(),
            cumulative_gas_used: 265390,
            logs: vec![PrimitiveLog {
                address: Address::from_str("dcf421d093428b096ca501a7cd1a740855a7976f").unwrap(),
                data: log_data,
            }],
        };
        let receipt_with_bloom = receipt.with_bloom();
        let legacy_receipt = LegacyReceipt::new(
            receipt_with_bloom.status_or_post_state().into(),
            receipt_with_bloom.logs_bloom,
            receipt_with_bloom.cumulative_gas_used(),
            receipt_with_bloom
                .logs()
                .iter()
                .map(|l| LogEntry {
                    address: l.address,
                    log_data: l.data.clone(),
                    tx_hash: B256::ZERO,
                })
                .collect::<_>(),
        );
        let r = TypedReceipt::Legacy(legacy_receipt);
        let mut encoded = Vec::<u8>::new();
        r.encode_2718(&mut encoded);
        assert_eq!(&encoded, &expected);
    }

    #[test]
    fn test_basic_access_list() {
        let expected: Vec<u8> = rustc_hex::FromHex::from_hex("01f90162a02f697d671e9ae4ee24a43c4b0d7e15f1cb4ba6de1561120d43b9a4e8c4a8a6ee83040caeb9010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000f838f794dcf421d093428b096ca501a7cd1a740855a7976fc0a00000000000000000000000000000000000000000000000000000000000000000").unwrap();
        let log_data = LogData::new_unchecked(vec![], vec![0u8; 32].into());
        let receipt = Receipt {
            status: fixed_bytes!(
                "2f697d671e9ae4ee24a43c4b0d7e15f1cb4ba6de1561120d43b9a4e8c4a8a6ee"
            )
            .into(),
            cumulative_gas_used: 265390,
            logs: vec![PrimitiveLog {
                address: Address::from_str("dcf421d093428b096ca501a7cd1a740855a7976f").unwrap(),
                data: log_data,
            }],
        };
        let receipt_with_bloom = receipt.with_bloom();
        let legacy_receipt = LegacyReceipt::new(
            receipt_with_bloom.status_or_post_state().into(),
            receipt_with_bloom.logs_bloom,
            receipt_with_bloom.cumulative_gas_used(),
            receipt_with_bloom
                .logs()
                .iter()
                .map(|l| LogEntry {
                    address: l.address,
                    log_data: l.data.clone(),
                    tx_hash: B256::ZERO,
                })
                .collect::<_>(),
        );
        let r = TypedReceipt::EIP2930Transaction(legacy_receipt);
        let mut encoded = Vec::<u8>::new();
        r.encode_2718(&mut encoded);
        assert_eq!(&encoded, &expected);
    }

    #[test]
    fn test_basic_eip1559() {
        let expected: Vec<u8> = rustc_hex::FromHex::from_hex("02f90162a02f697d671e9ae4ee24a43c4b0d7e15f1cb4ba6de1561120d43b9a4e8c4a8a6ee83040caeb9010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000f838f794dcf421d093428b096ca501a7cd1a740855a7976fc0a00000000000000000000000000000000000000000000000000000000000000000").unwrap();
        let log_data = LogData::new_unchecked(vec![], vec![0u8; 32].into());
        let receipt = Receipt {
            status: fixed_bytes!(
                "2f697d671e9ae4ee24a43c4b0d7e15f1cb4ba6de1561120d43b9a4e8c4a8a6ee"
            )
            .into(),
            cumulative_gas_used: 265390,
            logs: vec![PrimitiveLog {
                address: Address::from_str("dcf421d093428b096ca501a7cd1a740855a7976f").unwrap(),
                data: log_data,
            }],
        };
        let receipt_with_bloom = receipt.with_bloom();
        let legacy_receipt = LegacyReceipt::new(
            receipt_with_bloom.status_or_post_state().into(),
            receipt_with_bloom.logs_bloom,
            receipt_with_bloom.cumulative_gas_used(),
            receipt_with_bloom
                .logs()
                .iter()
                .map(|l| LogEntry {
                    address: l.address,
                    log_data: l.data.clone(),
                    tx_hash: B256::ZERO,
                })
                .collect::<_>(),
        );
        let r = TypedReceipt::EIP1559Transaction(legacy_receipt);
        let mut encoded = Vec::<u8>::new();
        r.encode_2718(&mut encoded);
        assert_eq!(&encoded, &expected);
    }

    #[test]
    fn test_status_code() {
        let expected: Vec<u8> = rustc_hex::FromHex::from_hex("f901428083040caeb9010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000f838f794dcf421d093428b096ca501a7cd1a740855a7976fc0a00000000000000000000000000000000000000000000000000000000000000000").unwrap();
        let log_data = LogData::new_unchecked(vec![], vec![0u8; 32].into());
        let receipt = Receipt {
            status: false.into(),
            cumulative_gas_used: 265390,
            logs: vec![PrimitiveLog {
                address: Address::from_str("dcf421d093428b096ca501a7cd1a740855a7976f").unwrap(),
                data: log_data,
            }],
        };
        let receipt_with_bloom = receipt.with_bloom();
        let legacy_receipt = LegacyReceipt::new(
            receipt_with_bloom.status_or_post_state().into(),
            receipt_with_bloom.logs_bloom,
            receipt_with_bloom.cumulative_gas_used(),
            receipt_with_bloom
                .logs()
                .iter()
                .map(|l| LogEntry {
                    address: l.address,
                    log_data: l.data.clone(),
                    tx_hash: B256::ZERO,
                })
                .collect::<_>(),
        );
        let r = TypedReceipt::Legacy(legacy_receipt);
        let mut encoded = Vec::<u8>::new();
        r.encode_2718(&mut encoded);
        assert_eq!(&encoded, &expected);
    }
}
