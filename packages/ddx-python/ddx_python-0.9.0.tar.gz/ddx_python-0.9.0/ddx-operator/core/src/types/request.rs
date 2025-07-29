#[cfg(feature = "insurance_fund_client_req")]
use crate::constants::REQ_INSURANCE_FUND_WITHDRAW;
#[cfg(feature = "fixed_expiry_future")]
use crate::specs::quarterly_expiry_future::Quarter;
#[cfg(feature = "python")]
use crate::types::state::exported;
use crate::{
    constants::{
        REQ_ADVANCE_EPOCH, REQ_ADVANCE_SETTLEMENT_EPOCH, REQ_ADVANCE_TIME, REQ_BLOCK,
        REQ_CANCEL_ALL, REQ_CANCEL_ORDER, REQ_DISASTER_RECOVERY, REQ_GENESIS,
        REQ_MINT_PRICE_CHECKPOINT, REQ_MODIFY_ORDER, REQ_ORDER, REQ_PRICE, REQ_UPDATE_ENROLLMENT,
        REQ_UPDATE_PRODUCT_LISTINGS, REQ_UPDATE_PROFILE, REQ_WITHDRAW, REQ_WITHDRAW_DDX,
    },
    types::{
        accounting::PriceMetadata,
        identifiers::StrategyIdHash,
        primitives::{IndexPriceHash, OrderHash, ProductSymbol},
        state::{BookOrder, Epoch, EpochKind, TradableProductKey},
        transaction::{self, Ordinal},
    },
};
use alloy_dyn_abi::DynSolValue;
use alloy_primitives::BlockNumber;
use core_common::{
    B256, Error, Result, error,
    types::{
        accounting::StrategyId,
        auth::EnrollmentEvent,
        global::TokenAddress,
        primitives::{
            Hash, Keccak256, OrderSide, SessionSignature, Signature, StampedTimeValue, TimeValue,
            TraderAddress, UnscaledI128, as_scaled_fraction,
        },
    },
    util::tokenize::Tokenizable,
};
use core_crypto::{eip712::SignedEIP712, hash_with_eth_prefix, hash_without_prefix};
use core_macros::{AbiToken, AsKeccak256, Nonced, SignedEIP712};
use downcast_rs::Downcast;
#[cfg(feature = "database")]
use postgres_types::{IsNull, ToSql, Type, to_sql_checked};
#[cfg(feature = "python")]
use pyo3::prelude::*;
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use std::{convert::TryFrom, fmt};

// Data structures in this section are used directly in the websocket api
pub type Nonce = Hash;
#[cfg(not(feature = "no_rate_limit"))]
pub type RateLimitTier = u64;
pub type SenderAlias = Hash;

pub trait Nonced {
    fn nonce(&self) -> Nonce;
}

impl Nonced for transaction::MatchableIntent {
    fn nonce(&self) -> Nonce {
        match self {
            transaction::MatchableIntent::OrderIntent(i) => i.nonce,
            transaction::MatchableIntent::ModifyOrderIntent(i) => i.nonce,
        }
    }
}

pub trait UniqueHash {
    fn hash(&self) -> Result<Hash>;
}

impl<T: core_crypto::eip712::SignedEIP712> UniqueHash for T {
    fn hash(&self) -> Result<Hash> {
        let eip712_hash = self.hash_eip712();
        let signer = core_crypto::recover(eip712_hash.into(), self.signature().into())?;
        let mut keccak = alloy_primitives::Keccak256::new();
        keccak.update(signer.as_slice());
        keccak.update(eip712_hash.as_bytes());
        let result = keccak.finalize();
        Ok(result.into())
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Deserialize, Serialize, AbiToken, AsKeccak256)]
#[serde(tag = "action")]
pub enum MembershipRequestKind {
    Join,
    Leave,
}

#[derive(Debug, Clone, PartialEq, Deserialize, Serialize, AbiToken, AsKeccak256)]
/// request sent by nodes to modify their cluster membership
pub struct MembershipRequest {
    /// the node's unique identifier
    pub node_id: u64,
    /// Node base URL
    pub url: String,
    /// a recent unix timetamp for a nonce
    pub timestamp: i64,
    /// what kind of cluster membership modification
    pub kind: MembershipRequestKind,
    /// signature over (node_id || request_index || kind)
    pub signature: Signature,
}

impl MembershipRequest {
    pub fn hash_abi_encoded(&self) -> B256 {
        let token = DynSolValue::Tuple(vec![
            self.node_id.into(),
            self.timestamp.into(),
            self.kind.into_token(),
        ]);
        let message = token.abi_encode();
        let intermediary_hash = hash_without_prefix(message);
        hash_with_eth_prefix(intermediary_hash)
    }
}

#[cfg_eval]
#[cfg_attr(feature = "python", pyclass(name = "ProfileUpdateIntent", get_all))]
#[derive(Debug, Clone, PartialEq, Deserialize, Serialize, Nonced)]
#[cfg_attr(not(target_family = "wasm"), derive(SignedEIP712))]
#[serde(rename_all = "camelCase")]
pub struct ProfileUpdate {
    /// A salt for uniqueness of the EIP-712 hash function. May optionally have business meaning to the client.
    pub nonce: Nonce,
    /// Sets the flag in the trader profile
    pub pay_fees_in_ddx: bool,
    /// EIP-712 signature of the order intent attributes
    #[cfg_attr(feature = "python", pyo3(set))]
    pub signature: Signature,
}

#[cfg(feature = "python")]
#[pymethods]
impl ProfileUpdate {
    #[new]
    pub fn new_py(nonce: Nonce, pay_fees_in_ddx: bool, signature: Option<Signature>) -> Self {
        Self {
            nonce,
            pay_fees_in_ddx,
            signature: signature.unwrap_or_default(),
        }
    }
}

/// Request enriched with data collected during pre-processing if any
// TODO 3591: Consider using a trait instead where only pre-processed payload are types, then use type alias for Request and PreProcessedRequest
#[allow(clippy::large_enum_variant)]
#[derive(Debug, Clone, PartialEq, Deserialize, Serialize)]
pub enum PreProcessedRequest {
    Order(OrderIntent),
    ModifyOrder(ModifyOrderIntent),
    CancelOrder(CancelOrderIntent),
    CancelAll(CancelAllIntent),
    IndexPrice(IndexPrice),
    #[cfg(feature = "eth-base")]
    Block(Block, super::ethereum::ConfirmedBlock),
    Withdraw(WithdrawIntent),
    WithdrawDDX(WithdrawDDXIntent),
    #[cfg(feature = "insurance_fund_client_req")]
    InsuranceFundWithdraw(InsuranceFundWithdrawIntent),
    AdvanceEpoch(AdvanceEpoch),
    AdvanceTime(StampedTimeValue),
    AdvanceSettlementEpoch(AdvanceSettlementEpoch),
    MintPriceCheckpoint(MintPriceCheckpoint),
    UpdateProductListings(UpdateProductListings),
    ProfileUpdate(ProfileUpdate),
    DisasterRecovery(DisasterRecovery),
    UpdateEnrollment(EnrollmentEvent),
}

impl From<PreProcessedRequest> for Request {
    fn from(value: PreProcessedRequest) -> Self {
        match value {
            PreProcessedRequest::Order(o) => ClientRequest::Order(o).into(),
            PreProcessedRequest::ModifyOrder(m) => ClientRequest::ModifyOrder(m).into(),
            PreProcessedRequest::CancelOrder(c) => ClientRequest::CancelOrder(c).into(),
            PreProcessedRequest::CancelAll(c) => ClientRequest::CancelAll(c).into(),
            PreProcessedRequest::Withdraw(w) => ClientRequest::Withdraw(w).into(),
            PreProcessedRequest::WithdrawDDX(w) => ClientRequest::WithdrawDDX(w).into(),
            #[cfg(feature = "insurance_fund_client_req")]
            PreProcessedRequest::InsuranceFundWithdraw(w) => {
                ClientRequest::InsuranceFundWithdraw(w).into()
            }
            PreProcessedRequest::ProfileUpdate(p) => ClientRequest::ProfileUpdate(p).into(),
            PreProcessedRequest::IndexPrice(p) => Cmd::IndexPrice(p).into(),
            #[cfg(feature = "eth-base")]
            PreProcessedRequest::Block(b, ..) => Cmd::Block(b).into(),
            PreProcessedRequest::AdvanceEpoch(e) => Cmd::AdvanceEpoch(e).into(),
            PreProcessedRequest::AdvanceTime(t) => Cmd::AdvanceTime(t).into(),
            PreProcessedRequest::AdvanceSettlementEpoch(f) => Cmd::AdvanceSettlementEpoch(f).into(),
            PreProcessedRequest::MintPriceCheckpoint(c) => Cmd::PriceCheckpoint(c).into(),
            PreProcessedRequest::UpdateProductListings(u) => Cmd::UpdateProductListings(u).into(),
            PreProcessedRequest::DisasterRecovery(dr) => AdminCmd::DisasterRecovery(dr).into(),
            PreProcessedRequest::UpdateEnrollment(e) => Cmd::UpdateEnrollment(e).into(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Deserialize, Serialize, Nonced)]
#[serde(tag = "t", content = "c")]
pub enum ClientRequest {
    Order(OrderIntent),
    ModifyOrder(ModifyOrderIntent),
    CancelOrder(CancelOrderIntent),
    CancelAll(CancelAllIntent),
    Withdraw(WithdrawIntent),
    WithdrawDDX(WithdrawDDXIntent),
    #[cfg(feature = "insurance_fund_client_req")]
    InsuranceFundWithdraw(InsuranceFundWithdrawIntent),
    ProfileUpdate(ProfileUpdate),
}

impl ClientRequest {
    pub fn recover_signer(&self) -> Result<(Hash, TraderAddress)> {
        match self {
            ClientRequest::Order(o) => o.recover_signer(),
            ClientRequest::ModifyOrder(m) => m.recover_signer(),
            ClientRequest::CancelOrder(c) => c.recover_signer(),
            ClientRequest::CancelAll(c) => c.recover_signer(),
            ClientRequest::Withdraw(w) => w.recover_signer(),
            ClientRequest::WithdrawDDX(w) => w.recover_signer(),
            #[cfg(feature = "insurance_fund_client_req")]
            ClientRequest::InsuranceFundWithdraw(i) => i.recover_signer(),
            ClientRequest::ProfileUpdate(p) => p.recover_signer(),
        }
    }
}

impl From<ClientRequest> for Request {
    fn from(value: ClientRequest) -> Self {
        Request::ClientRequest(value)
    }
}

impl TryFrom<Request> for ClientRequest {
    type Error = Error;

    fn try_from(value: Request) -> Result<Self, Self::Error> {
        if let Request::ClientRequest(req) = value {
            Ok(req)
        } else {
            Err(error!("Not a client request"))
        }
    }
}

// CmdTimeValue is a wrapper around StampedTimeValue to allow for custom python implementation
// This is needed in core-ddx module since we need to implement python methods with `Cmd` enum
#[cfg_attr(feature = "python", pyclass(name = "AdvanceTime", frozen))]
#[derive(Debug, Clone, PartialEq, Deserialize, Serialize)]
pub struct CmdTimeValue(StampedTimeValue);

#[cfg(feature = "python")]
#[pymethods]
impl CmdTimeValue {
    #[new]
    fn new_py(value: TimeValue, timestamp: i64) -> Self {
        Self(StampedTimeValue { value, timestamp })
    }

    #[getter]
    fn value(&self) -> TimeValue {
        self.0.value
    }

    #[getter]
    fn timestamp(&self) -> i64 {
        self.0.timestamp
    }
}

impl From<StampedTimeValue> for CmdTimeValue {
    fn from(value: StampedTimeValue) -> Self {
        Self(value)
    }
}

impl From<CmdTimeValue> for StampedTimeValue {
    fn from(value: CmdTimeValue) -> Self {
        value.0
    }
}

#[derive(Debug, Clone, PartialEq, Deserialize, Serialize)]
#[serde(tag = "t", content = "c")]
pub enum Cmd {
    Genesis,
    IndexPrice(IndexPrice),
    Block(Block),
    AdvanceTime(StampedTimeValue),
    AdvanceEpoch(AdvanceEpoch),
    AdvanceSettlementEpoch(AdvanceSettlementEpoch),
    PriceCheckpoint(MintPriceCheckpoint),
    UpdateProductListings(UpdateProductListings),
    UpdateEnrollment(EnrollmentEvent),
}

impl Cmd {
    fn hash(&self) -> Hash {
        match self {
            Cmd::Genesis => Default::default(),
            Cmd::IndexPrice(i) => i.keccak256(),
            Cmd::Block(b) => b.keccak256(),
            Cmd::AdvanceTime(t) => t.keccak256(),
            Cmd::AdvanceEpoch(e) => e.keccak256(),
            Cmd::AdvanceSettlementEpoch(s) => s.keccak256(),
            Cmd::PriceCheckpoint(p) => p.keccak256(),
            Cmd::UpdateProductListings(u) => u.keccak256(),
            Cmd::UpdateEnrollment(e) => e.keccak256(),
        }
    }
}

impl From<Cmd> for Request {
    fn from(value: Cmd) -> Self {
        Request::Cmd(value)
    }
}

impl TryFrom<Request> for Cmd {
    type Error = Error;

    fn try_from(value: Request) -> Result<Self, Self::Error> {
        if let Request::Cmd(cmd) = value {
            Ok(cmd)
        } else {
            Err(error!("Not a command: {:?}", value))
        }
    }
}

#[derive(Debug, Clone, PartialEq, Deserialize, Serialize, AbiToken)]
#[serde(rename_all = "camelCase")]
pub struct DisasterRecovery {
    pub request_index: RequestIndex,
    pub signatures: Vec<Signature>,
}

#[derive(Debug, Clone, PartialEq, Deserialize, Serialize, AbiToken, AsKeccak256)]
#[serde(tag = "t", content = "c")]
pub enum AdminCmd {
    DisasterRecovery(DisasterRecovery),
}

impl From<AdminCmd> for Request {
    fn from(value: AdminCmd) -> Self {
        Request::Admin(value)
    }
}

impl TryFrom<Request> for AdminCmd {
    type Error = Error;

    fn try_from(value: Request) -> Result<Self> {
        if let Request::Admin(admin_cmd) = value {
            Ok(admin_cmd)
        } else {
            Err(error!("Not an admin command: {:?}", value))
        }
    }
}

#[allow(clippy::large_enum_variant)]
#[derive(Debug, Clone, PartialEq, Deserialize, Serialize)]
#[serde(untagged)]
pub enum Request {
    ClientRequest(ClientRequest),
    Cmd(Cmd),
    Admin(AdminCmd),
}

impl Request {
    pub fn to_topic(&self) -> i16 {
        match self {
            Request::ClientRequest(req) => match req {
                ClientRequest::Order(_) => REQ_ORDER,
                ClientRequest::ModifyOrder(_) => REQ_MODIFY_ORDER,
                ClientRequest::CancelOrder(_) => REQ_CANCEL_ORDER,
                ClientRequest::CancelAll(_) => REQ_CANCEL_ALL,
                ClientRequest::Withdraw(_) => REQ_WITHDRAW,
                ClientRequest::WithdrawDDX(_) => REQ_WITHDRAW_DDX,
                #[cfg(feature = "insurance_fund_client_req")]
                ClientRequest::InsuranceFundWithdraw(_) => REQ_INSURANCE_FUND_WITHDRAW,
                ClientRequest::ProfileUpdate(_) => REQ_UPDATE_PROFILE,
            },
            Request::Cmd(cmd) => match cmd {
                Cmd::Genesis => REQ_GENESIS,
                Cmd::IndexPrice(_) => REQ_PRICE,
                Cmd::Block(_) => REQ_BLOCK,
                Cmd::AdvanceEpoch(_) => REQ_ADVANCE_EPOCH,
                Cmd::AdvanceTime(_) => REQ_ADVANCE_TIME,
                Cmd::AdvanceSettlementEpoch(_) => REQ_ADVANCE_SETTLEMENT_EPOCH,
                Cmd::PriceCheckpoint(_) => REQ_MINT_PRICE_CHECKPOINT,
                Cmd::UpdateProductListings(_) => REQ_UPDATE_PRODUCT_LISTINGS,
                Cmd::UpdateEnrollment(_) => REQ_UPDATE_ENROLLMENT,
            },
            Request::Admin(admin_cmd) => match admin_cmd {
                AdminCmd::DisasterRecovery(_) => REQ_DISASTER_RECOVERY,
            },
        }
    }

    /// Serializes the request inner data as JSON
    pub fn inner_as_json(&self) -> serde_json::Value {
        // This is our structure so we don't catch systemic serialization error
        match self {
            Request::ClientRequest(req) => match req {
                ClientRequest::Order(o) => serde_json::to_value(o).unwrap(),
                ClientRequest::ModifyOrder(m) => serde_json::to_value(m).unwrap(),
                ClientRequest::CancelOrder(c) => serde_json::to_value(c).unwrap(),
                ClientRequest::CancelAll(c) => serde_json::to_value(c).unwrap(),
                ClientRequest::Withdraw(w) => serde_json::to_value(w).unwrap(),
                ClientRequest::WithdrawDDX(w) => serde_json::to_value(w).unwrap(),
                #[cfg(feature = "insurance_fund_client_req")]
                ClientRequest::InsuranceFundWithdraw(w) => serde_json::to_value(w).unwrap(),
                ClientRequest::ProfileUpdate(p) => serde_json::to_value(p).unwrap(),
            },
            Request::Cmd(cmd) => match cmd {
                Cmd::Genesis => serde_json::Value::default(),
                Cmd::IndexPrice(p) => serde_json::to_value(p).unwrap(),
                Cmd::Block(b) => serde_json::to_value(b).unwrap(),
                Cmd::AdvanceEpoch(e) => serde_json::to_value(e).unwrap(),
                Cmd::AdvanceTime(t) => serde_json::to_value(t).unwrap(),
                Cmd::AdvanceSettlementEpoch(e) => serde_json::to_value(e).unwrap(),
                Cmd::PriceCheckpoint(c) => serde_json::to_value(c).unwrap(),
                Cmd::UpdateProductListings(u) => serde_json::to_value(u).unwrap(),
                Cmd::UpdateEnrollment(e) => serde_json::to_value(e).unwrap(),
            },
            Request::Admin(admin_cmd) => match admin_cmd {
                AdminCmd::DisasterRecovery(dr) => serde_json::to_value(dr).unwrap(),
            },
        }
    }

    pub fn summary(&self) -> String {
        match self {
            Request::ClientRequest(req) => match req {
                ClientRequest::Order(o) => {
                    format!(
                        "Order(trader={} symbol={} amount={} price={})",
                        o.trader_address().unwrap_or_default(),
                        o.symbol,
                        (*o.amount).round_dp(2),
                        (*o.price).round_dp(2),
                    )
                }
                ClientRequest::ModifyOrder(m) => {
                    format!(
                        "ModifyOrder(order_hash={} trader={} symbol={} amount={} price={})",
                        m.order_hash.hex(),
                        m.trader_address().unwrap_or_default(),
                        m.symbol,
                        (*m.amount).round_dp(2),
                        (*m.price).round_dp(2),
                    )
                }
                ClientRequest::CancelOrder(c) => {
                    format!("CancelOrder({} {:?})", c.symbol, c.order_hash)
                }
                ClientRequest::CancelAll(c) => {
                    format!("CancelAll({} {})", c.symbol, c.strategy)
                }
                ClientRequest::Withdraw(w) => match w.recover_signer() {
                    Ok((_, withdraw_address)) => format!(
                        "Withdraw(trader={} amount={})",
                        withdraw_address,
                        (*w.amount).round_dp(2)
                    ),
                    Err(_) => String::from("Unable to recover signer address!"),
                },
                ClientRequest::WithdrawDDX(w) => match w.recover_signer() {
                    Ok((_, withdraw_address)) => format!(
                        "WithdrawDDX(trader={} amount={})",
                        withdraw_address,
                        (*w.amount).round_dp(2)
                    ),
                    Err(_) => String::from("Unable to recover signer address!"),
                },
                #[cfg(feature = "insurance_fund_client_req")]
                ClientRequest::InsuranceFundWithdraw(w) => match w.recover_signer() {
                    Ok((_, withdraw_address)) => format!(
                        "InsuranceFundWithdraw(contributor={} amount={})",
                        withdraw_address,
                        (*w.amount).round_dp(2)
                    ),
                    Err(_) => String::from("Unable to recover signer address!"),
                },
                ClientRequest::ProfileUpdate(p) => format!("{:?}", p),
            },
            Request::Cmd(cmd) => match cmd {
                Cmd::Genesis => "Genesis".to_string(),
                Cmd::Block(b) => format!("Block({})", b.0),
                Cmd::IndexPrice(p) => {
                    format!("IndexPrice({} {})", p.symbol, (*p.price).round_dp(2))
                }
                Cmd::AdvanceEpoch(e) => format!("AdvanceEpoch({})", e.epoch_id),
                Cmd::AdvanceTime(t) => format!("AdvanceTime({:?})", t),
                Cmd::AdvanceSettlementEpoch(e) => {
                    format!("AdvanceSettlementEpoch({})", e.epoch_id)
                }
                Cmd::PriceCheckpoint(_c) => "PriceCheckpoint".to_string(),
                Cmd::UpdateProductListings(u) => format!("UpdateProductListings({:?})", u),
                Cmd::UpdateEnrollment(e) => format!("UpdateKyc({})", e),
            },
            Request::Admin(admin_cmd) => match admin_cmd {
                AdminCmd::DisasterRecovery(dr) => format!("DisasterRecovery({:?})", dr),
            },
        }
    }
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct RequestWithReceipt {
    pub request: Request,
    pub receipt: Receipt,
}

pub type RequestIndex = u64;

/// Acknowledge receipt of each request referenced by request id.
/// At this stage, we have verified and sequenced the request, but it has not yet been part
/// of a transaction.
// TODO: If the api wraps this in any way, it is wrong. Use exactly as is.
#[derive(Debug, PartialEq, Clone, Deserialize, Serialize)]
#[serde(tag = "t", content = "c")]
pub enum Receipt {
    /// The signed receipt of a successfully sequenced client request.
    #[serde(rename_all = "camelCase")]
    Sequenced {
        nonce: Nonce,
        request_hash: Hash,
        request_index: RequestIndex,
        sender: TraderAddress,
        enclave_signature: Signature,
    },
    /// The safety failure of a valid client request.
    ///
    /// Safeties are business rules we use to validate client request after authenticating them. For example,
    /// if a trader send a well-formed request to place an order without enough margin, we respond with
    /// a safety failure receipt.
    SafetyFailure {
        nonce: Nonce,
        message: String,
        inner: String,
    },
    /// The signed receipt of a successfully sequenced command.
    ///
    /// Note that the enclave signs on the command hash. Since sequencing of command should be done
    /// entirely in the enclave, there is no need for a separate signature on the `Request` itself.
    #[serde(rename_all = "camelCase")]
    SequencedCmd {
        request_index: u64,
        request_hash: Hash,
        enclave_signature: Signature,
    },
    #[serde(rename_all = "camelCase")]
    SequencedAdminCmd {
        request_index: u64,
        request_hash: Hash,
        enclave_signature: Signature,
    },
}

impl Receipt {
    pub fn hash_unsigned(&self) -> Hash {
        match self {
            Receipt::Sequenced {
                nonce,
                request_hash,
                request_index,
                sender,
                ..
            } => {
                let token = DynSolValue::Tuple(vec![
                    (*sender).into_token(),
                    (*nonce).into_token(),
                    (*request_hash).into_token(),
                    (*request_index).into(),
                ]);
                let pre_image = token.abi_encode();
                let intermediary_hash = hash_without_prefix(pre_image);
                hash_with_eth_prefix(intermediary_hash).into()
            }
            // TODO: Get the request hash so we can remove inner signatures
            Receipt::SequencedCmd {
                request_index,
                request_hash,
                ..
            } => {
                let token =
                    DynSolValue::Tuple(vec![(*request_hash).into_token(), (*request_index).into()]);
                let pre_image = token.abi_encode();
                let intermediary_hash = hash_without_prefix(pre_image);
                hash_with_eth_prefix(intermediary_hash).into()
            }
            Receipt::SequencedAdminCmd {
                request_hash,
                request_index,
                ..
            } => {
                let token =
                    DynSolValue::Tuple(vec![(*request_hash).into_token(), (*request_index).into()]);
                let pre_image = token.abi_encode();
                let intermediary_hash = hash_without_prefix(pre_image);
                hash_with_eth_prefix(intermediary_hash).into()
            }
            Receipt::SafetyFailure { .. } => panic!("Unexpected safety failure hashing"),
        }
    }

    pub fn signature(&self) -> Signature {
        match self {
            Receipt::SequencedCmd {
                enclave_signature, ..
            }
            | Receipt::Sequenced {
                enclave_signature, ..
            }
            | Receipt::SequencedAdminCmd {
                enclave_signature, ..
            } => *enclave_signature,
            Receipt::SafetyFailure { .. } => {
                panic!("Unexpected signature request on a failed receipt")
            }
        }
    }

    pub fn set_signature(&mut self, signature: Signature) {
        match self {
            Receipt::SequencedCmd {
                enclave_signature, ..
            }
            | Receipt::SequencedAdminCmd {
                enclave_signature, ..
            }
            | Receipt::Sequenced {
                enclave_signature, ..
            } => *enclave_signature = signature,
            Receipt::SafetyFailure { .. } => panic!("Cannot sign a safety failure"),
        }
    }

    pub fn make_sequenced(
        request_index: u64,
        request: &Request,
        signature: Signature,
    ) -> Result<Receipt> {
        match request {
            Request::ClientRequest(client_request) => {
                let (request_hash, sender) = client_request.recover_signer()?;
                Ok(Receipt::Sequenced {
                    nonce: client_request.nonce(),
                    request_hash,
                    request_index,
                    sender,
                    enclave_signature: signature,
                })
            }
            Request::Cmd(cmd) => Ok(Receipt::SequencedCmd {
                request_index,
                request_hash: cmd.hash(),
                enclave_signature: signature,
            }),
            Request::Admin(admin_cmd) => Ok(Receipt::SequencedAdminCmd {
                request_index,
                request_hash: admin_cmd.keccak256(),
                enclave_signature: signature,
            }),
        }
    }

    pub fn request_index(&self) -> Option<u64> {
        match self {
            Receipt::SequencedCmd { request_index, .. }
            | Receipt::SequencedAdminCmd { request_index, .. }
            | Receipt::Sequenced { request_index, .. } => Some(*request_index),
            Receipt::SafetyFailure { .. } => None,
        }
    }

    pub fn safety_failure_msg(&self) -> Option<String> {
        match self {
            Receipt::SafetyFailure { message, .. } => Some(message.clone()),
            _ => None,
        }
    }
}

// End of websocket api structures
#[derive(Debug, PartialEq, Eq, Clone, Copy)]
pub enum OrderType {
    Limit { post_only: bool },
    Market,
    StopLimit,
}

impl Default for OrderType {
    fn default() -> Self {
        Self::Limit { post_only: false }
    }
}

#[cfg(feature = "python")]
impl FromPyObject<'_> for OrderType {
    fn extract(ob: &PyAny) -> PyResult<Self> {
        ob.extract::<exported::python::OrderType>().map(Self::from)
    }
}

#[cfg(feature = "python")]
impl IntoPy<PyObject> for OrderType {
    fn into_py(self, py: Python) -> PyObject {
        exported::python::OrderType::from(self).into_py(py)
    }
}

impl Serialize for OrderType {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        serializer.serialize_u8((*self).into())
    }
}

impl<'de> Deserialize<'de> for OrderType {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        let value = u8::deserialize(deserializer)?;
        Self::try_from(value).map_err(serde::de::Error::custom)
    }
}

impl From<OrderType> for i32 {
    fn from(value: OrderType) -> Self {
        u8::from(value).into()
    }
}

impl From<OrderType> for u8 {
    fn from(value: OrderType) -> Self {
        match value {
            OrderType::Limit { post_only } => {
                if post_only {
                    3
                } else {
                    0
                }
            }
            OrderType::Market => 1,
            OrderType::StopLimit => 2,
        }
    }
}

impl TryFrom<u8> for OrderType {
    type Error = Error;
    fn try_from(value: u8) -> Result<Self> {
        match value {
            0 => Ok(OrderType::Limit { post_only: false }),
            1 => Ok(OrderType::Market),
            2 => Ok(OrderType::StopLimit),
            3 => Ok(OrderType::Limit { post_only: true }),
            _ => Err(error!("Invalid order type: {}", value)),
        }
    }
}

pub trait MatchableIntent:
    Downcast + core_crypto::eip712::SignedEIP712 + UniqueHash + Nonced + fmt::Debug
{
    fn trader_address(&self) -> Result<TraderAddress> {
        let (_, signer) = self.recover_signer()?;
        Ok(signer)
    }
    fn symbol(&self) -> ProductSymbol;
    fn side(&self) -> OrderSide;
    fn strategy(&self) -> StrategyId;
    fn strategy_id_hash(&self) -> StrategyIdHash {
        self.strategy().into()
    }
    fn price(&self) -> UnscaledI128;
    fn amount(&self) -> UnscaledI128;
    fn stop_price(&self) -> UnscaledI128;
    fn order_hash(&self) -> Result<OrderHash> {
        Ok(self.hash()?.into())
    }
    fn order_type(&self) -> OrderType;

    fn book_order(&self, book_ordinal: Ordinal, time_value: TimeValue) -> Result<BookOrder>;
}

downcast_rs::impl_downcast!(MatchableIntent);

pub trait CancelableIntent: core_crypto::eip712::SignedEIP712 + Nonced + fmt::Debug {
    fn symbol(&self) -> ProductSymbol;
    fn order_hash(&self) -> OrderHash;
}

/// Order intents are meta-transactions signed by traders Ethereum wallets and submitted to operators.
///
/// They come in through the API, signed by their maker. We verify that:
///
/// a) the signatures recovers the `trader_address`
/// b) the maker has enough collateral to be solvent when the order gets filled
///
/// Following verification, we match an order intent against the order book. This may result in
/// fill(s) or posting into the order book depending on the matches found.
#[cfg_eval]
#[cfg_attr(feature = "python", pyclass(get_all))]
#[derive(Debug, Clone, PartialEq, Deserialize, Serialize, Nonced)]
#[serde(rename_all = "camelCase")]
pub struct OrderIntent {
    /// Symbol of the market
    pub symbol: ProductSymbol,
    /// Strategy Id (label)
    pub strategy: StrategyId,
    /// Side: 0-Long, 1-Short
    pub side: OrderSide,
    /// 0-Limit, 1-Market, 2-Stop-Limit
    pub order_type: OrderType,
    /// A salt for uniqueness of the EIP-712 hash function. May optionally have business meaning to the client.
    pub nonce: Nonce,
    /// Order amount
    pub amount: UnscaledI128,
    /// Order price. For a limit order, it is the limit price.
    pub price: UnscaledI128,
    /// Stop price. Set to 0 if the order is not a Stop-Limit.
    pub stop_price: UnscaledI128,
    /// EIP-191 signature of the 1CT session public key
    #[cfg_attr(feature = "python", pyo3(set))]
    pub session_key_signature: SessionSignature,
    /// EIP-712 signature of the order intent attributes
    #[cfg_attr(feature = "python", pyo3(set))]
    pub signature: Signature,
}

#[cfg(feature = "python")]
#[pymethods]
impl OrderIntent {
    #[new]
    pub fn new_py(
        symbol: ProductSymbol,
        strategy: StrategyId,
        side: OrderSide,
        order_type: OrderType,
        nonce: Nonce,
        amount: UnscaledI128,
        price: UnscaledI128,
        stop_price: UnscaledI128,
        session_key_signature: SessionSignature,
        signature: Option<Signature>,
    ) -> Self {
        Self {
            symbol,
            strategy,
            side,
            order_type,
            nonce,
            amount,
            price,
            stop_price,
            session_key_signature,
            signature: signature.unwrap_or_default(),
        }
    }
}

#[cfg(feature = "test_harness")]
impl Default for OrderIntent {
    fn default() -> Self {
        OrderIntent {
            symbol: Default::default(),
            strategy: Default::default(),
            side: OrderSide::Bid,
            order_type: OrderType::Limit { post_only: false },
            nonce: Default::default(),
            amount: Default::default(),
            price: Default::default(),
            stop_price: Default::default(),
            session_key_signature: Default::default(),
            signature: Default::default(),
        }
    }
}

impl MatchableIntent for OrderIntent {
    fn symbol(&self) -> ProductSymbol {
        self.symbol
    }

    fn side(&self) -> OrderSide {
        self.side
    }

    fn strategy(&self) -> StrategyId {
        self.strategy
    }

    fn price(&self) -> UnscaledI128 {
        self.price
    }

    fn amount(&self) -> UnscaledI128 {
        self.amount
    }

    fn stop_price(&self) -> UnscaledI128 {
        self.stop_price
    }

    // Order hash of an OrderIntent is the same when canceling and matching so the default
    // implementation is used, which is CancelableIntent::order_hash.

    fn order_type(&self) -> OrderType {
        self.order_type
    }

    fn book_order(&self, book_ordinal: Ordinal, time_value: TimeValue) -> Result<BookOrder> {
        Ok(BookOrder {
            side: self.side,
            amount: self.amount,
            price: self.price,
            trader_address: self.trader_address()?,
            strategy_id_hash: self.strategy_id_hash(),
            book_ordinal,
            time_value,
        })
    }
}

/// Modify order intents are intents that modify the original order details of a specific order
/// identified by its order hash.
///
/// This is identical to a cancel and a re-placing of the new order,
/// the only difference from doing them separately being that the execution is atomic when executed
/// as a ModifyOrderIntent.
#[cfg_eval]
#[cfg_attr(feature = "python", pyclass(get_all))]
#[derive(Debug, Clone, PartialEq, Deserialize, Serialize, Nonced)]
#[serde(rename_all = "camelCase")]
pub struct ModifyOrderIntent {
    /// Order hash of the order to modify
    pub order_hash: OrderHash,

    // Mirroring OrderIntent fields
    /// Symbol of the market
    pub symbol: ProductSymbol,
    /// Strategy Id (label)
    pub strategy: StrategyId,
    /// Side: 0-Long, 1-Short
    pub side: OrderSide,
    /// 0-Limit, 1-Market, 2-Stop-Limit
    pub order_type: OrderType,
    /// A salt for uniqueness of the EIP-712 hash function. May optionally have business meaning to the client.
    pub nonce: Nonce,
    /// Order amount
    pub amount: UnscaledI128,
    /// Order price. For a limit order, it is the limit price.
    pub price: UnscaledI128,
    /// Stop price. Set to 0 if the order is not a Stop-Limit.
    pub stop_price: UnscaledI128,
    /// EIP-191 signature of the 1CT session public key
    #[cfg_attr(feature = "python", pyo3(set))]
    pub session_key_signature: SessionSignature,
    /// EIP-712 signature of the order intent attributes
    #[cfg_attr(feature = "python", pyo3(set))]
    pub signature: Signature,
}

#[cfg(feature = "python")]
#[pymethods]
impl ModifyOrderIntent {
    #[new]
    pub fn new_py(
        order_hash: OrderHash,
        symbol: ProductSymbol,
        strategy: StrategyId,
        side: OrderSide,
        order_type: OrderType,
        nonce: Nonce,
        amount: UnscaledI128,
        price: UnscaledI128,
        stop_price: UnscaledI128,
        session_key_signature: SessionSignature,
        signature: Option<Signature>,
    ) -> Self {
        Self {
            order_hash,
            symbol,
            strategy,
            side,
            order_type,
            nonce,
            amount,
            price,
            stop_price,
            session_key_signature,
            signature: signature.unwrap_or_default(),
        }
    }
}

impl CancelableIntent for ModifyOrderIntent {
    fn symbol(&self) -> ProductSymbol {
        self.symbol
    }

    fn order_hash(&self) -> OrderHash {
        // Order hash of a ModifyOrderIntent is NOT the same when canceling and matching.
        // When canceling, the order hash is the order hash of the pre-existing order from the
        // book.
        self.order_hash
    }
}

impl MatchableIntent for ModifyOrderIntent {
    fn symbol(&self) -> ProductSymbol {
        self.symbol
    }

    fn side(&self) -> OrderSide {
        self.side
    }

    fn strategy(&self) -> StrategyId {
        self.strategy
    }

    fn price(&self) -> UnscaledI128 {
        self.price
    }

    fn amount(&self) -> UnscaledI128 {
        self.amount
    }

    fn stop_price(&self) -> UnscaledI128 {
        self.stop_price
    }

    // When matching, the order hash is the hash of the ModifyOrder's internal order intent
    // information.
    // We override the default implementation of CancelableIntent::order_hash to return the hash of the
    // the order intent itself.

    fn order_type(&self) -> OrderType {
        self.order_type
    }

    fn book_order(&self, book_ordinal: Ordinal, time_value: TimeValue) -> Result<BookOrder> {
        Ok(BookOrder {
            side: self.side,
            amount: self.amount,
            price: self.price,
            trader_address: self.trader_address()?,
            strategy_id_hash: self.strategy_id_hash(),
            book_ordinal,
            time_value,
        })
    }
}

#[cfg(any(test, feature = "test_harness"))]
impl ModifyOrderIntent {
    pub fn from_order_intent_unsigned(
        order_intent: OrderIntent,
        existing_order_hash: OrderHash,
    ) -> Self {
        Self {
            order_hash: existing_order_hash,
            symbol: order_intent.symbol,
            strategy: order_intent.strategy,
            side: order_intent.side,
            order_type: order_intent.order_type,
            nonce: order_intent.nonce,
            amount: order_intent.amount,
            price: order_intent.price,
            stop_price: order_intent.stop_price,
            session_key_signature: Default::default(),
            signature: Default::default(),
        }
    }
}

#[cfg_eval]
#[cfg_attr(feature = "python", pyclass(get_all))]
#[derive(Debug, Clone, PartialEq, Deserialize, Serialize, Nonced)]
#[serde(rename_all = "camelCase")]
pub struct CancelOrderIntent {
    pub symbol: ProductSymbol,
    /// hash of the corresponding order intent
    pub order_hash: OrderHash,
    /// `nonce` specified in the order intent to cancel (to lookup the order without storing its hash)
    /// A salt for uniqueness of the EIP-712 hash function. May optionally have business meaning to the client.
    pub nonce: Nonce,
    /// EIP-191 signature of the 1CT session public key
    #[cfg_attr(feature = "python", pyo3(set))]
    pub session_key_signature: SessionSignature,
    /// EIP-712 signature of the order cancellation intent attributes
    #[cfg_attr(feature = "python", pyo3(set))]
    pub signature: Signature,
}

#[cfg(feature = "python")]
#[pymethods]
impl CancelOrderIntent {
    #[new]
    pub fn new_py(
        symbol: ProductSymbol,
        order_hash: OrderHash,
        nonce: Nonce,
        session_key_signature: SessionSignature,
        signature: Option<Signature>,
    ) -> Self {
        Self {
            symbol,
            order_hash,
            nonce,
            session_key_signature,
            signature: signature.unwrap_or_default(),
        }
    }
}

impl CancelableIntent for CancelOrderIntent {
    fn symbol(&self) -> ProductSymbol {
        self.symbol
    }
    // The order hash is of a pre-existing order from the book.
    fn order_hash(&self) -> OrderHash {
        self.order_hash
    }
}

/// Batch cancel all orders for a given strategy
#[cfg_eval]
#[cfg_attr(feature = "python", pyclass(get_all))]
#[derive(Debug, Clone, PartialEq, Deserialize, Serialize, Nonced)]
#[serde(rename_all = "camelCase")]
pub struct CancelAllIntent {
    pub symbol: ProductSymbol,
    /// Strategy to cancel orders for
    pub strategy: StrategyId,
    /// A salt for uniqueness of the EIP-712 hash function.
    pub nonce: Nonce,
    /// EIP-191 signature of the 1CT session public key
    #[cfg_attr(feature = "python", pyo3(set))]
    pub session_key_signature: SessionSignature,
    /// EIP-712 signature of the order cancellation intent attributes
    #[cfg_attr(feature = "python", pyo3(set))]
    pub signature: Signature,
}

#[cfg(feature = "python")]
#[pymethods]
impl CancelAllIntent {
    #[new]
    pub fn new_py(
        symbol: ProductSymbol,
        strategy: StrategyId,
        nonce: Nonce,
        session_key_signature: SessionSignature,
        signature: Option<Signature>,
    ) -> Self {
        Self {
            symbol,
            strategy,
            nonce,
            session_key_signature,
            signature: signature.unwrap_or_default(),
        }
    }
}

/// An index price is the price update of an instrument coming from the price feed.
///
/// It is signed by the price feed's enclave.
#[cfg_eval]
#[cfg_attr(feature = "python", pyclass(frozen))]
#[derive(Debug, Clone, PartialEq, Deserialize, Serialize, AbiToken, AsKeccak256)]
#[serde(rename_all = "camelCase")]
pub struct IndexPrice {
    /// Symbol of the instrument
    #[cfg_attr(feature = "python", pyo3(get))]
    pub symbol: ProductSymbol,
    /// Current market price in the source exchange
    #[cfg_attr(feature = "python", pyo3(get))]
    #[serde(with = "as_scaled_fraction")]
    pub price: UnscaledI128,
    /// The previous price update. Useful to prove that no prices were skipped.
    #[cfg_attr(feature = "python", pyo3(get))]
    #[serde(with = "as_scaled_fraction")]
    pub prev_price: UnscaledI128,
    /// Additional metadata required by the price feed to initialize
    #[cfg_attr(feature = "python", pyo3(get))]
    pub metadata: PriceMetadata,
    /// Time at which the price feed read the update from its TCP socket. It also salt of the hashing function.
    pub timestamp: u64,
}

impl IndexPrice {
    pub fn hash(&self) -> IndexPriceHash {
        self.keccak256().into()
    }
}

#[cfg(feature = "python")]
#[pymethods]
impl IndexPrice {
    #[new]
    pub fn new_py(
        symbol: ProductSymbol,
        price: UnscaledI128,
        prev_price: UnscaledI128,
        metadata: PriceMetadata,
        timestamp: u64,
    ) -> Self {
        Self {
            symbol,
            price,
            prev_price,
            metadata,
            timestamp,
        }
    }

    #[getter]
    pub fn timestamp(&self) -> u64 {
        self.timestamp
    }
}

/// We use a single `BlockProducer` to sequence blocks along with other requests to ensure that
/// all Execution Operators synchronize their state with Ethereum event in the same order.
///
/// # Notes
///
/// Some Ethereum events (e.g. Deposits) must only be processed on confirmed blocks.
/// Block confirmation count is handled client-side during execution. The block producer's
/// responsibility is just to post block numbers into the `RequestQueue`.
#[cfg_attr(feature = "python", pyclass(frozen))]
#[derive(Debug, Default, Clone, PartialEq, Deserialize, Serialize, AbiToken, AsKeccak256)]
#[serde(rename_all = "camelCase")]
pub struct Block(pub BlockNumber); // TODO: Include the confirmed block hash

#[cfg(feature = "python")]
#[pymethods]
impl Block {
    #[new]
    pub fn new_py(number: u64) -> Self {
        Self::new(number)
    }
}

impl Block {
    pub fn new(number: u64) -> Self {
        Block(number)
    }

    pub fn number(&self) -> u64 {
        self.0
    }
}

#[cfg_attr(feature = "python", pyclass(frozen))]
#[derive(Debug, Default, Clone, PartialEq, Deserialize, Serialize, AbiToken, AsKeccak256)]
#[serde(rename_all = "camelCase")]
pub struct AdvanceEpoch {
    pub epoch_id: u64,
    pub time: StampedTimeValue,
}

#[cfg(feature = "python")]
#[pymethods]
impl AdvanceEpoch {
    #[new]
    pub fn new_py(epoch_id: u64, time: CmdTimeValue) -> Self {
        Self {
            epoch_id,
            time: time.into(),
        }
    }

    #[getter]
    fn time(&self) -> CmdTimeValue {
        self.time.into()
    }

    #[getter]
    fn epoch_id(&self) -> u64 {
        self.epoch_id
    }
}

impl AdvanceEpoch {
    pub fn new(epoch_id: u64, time: StampedTimeValue) -> Self {
        AdvanceEpoch { epoch_id, time }
    }

    pub fn as_epoch(&self, length: u64) -> Epoch {
        Epoch::new(EpochKind::Regular, self.epoch_id, self.time, length)
    }
}

#[derive(Debug, Clone, PartialEq, Deserialize, Serialize, Eq, std::hash::Hash, AbiToken)]
#[serde(rename_all = "camelCase", tag = "t", content = "c")]
#[non_exhaustive]
pub enum SettlementAction {
    TradeMining,
    PnlRealization,
    FundingDistribution,
    #[cfg(feature = "fixed_expiry_future")]
    FuturesExpiry {
        quarter: Quarter,
    },
}

#[cfg(feature = "python")]
impl FromPyObject<'_> for SettlementAction {
    fn extract(ob: &PyAny) -> PyResult<Self> {
        let action = ob.extract::<exported::python::SettlementAction>()?;
        Ok(action.into())
    }
}

#[cfg(feature = "python")]
impl IntoPy<PyObject> for SettlementAction {
    fn into_py(self, py: Python) -> PyObject {
        exported::python::SettlementAction::from(self).into_py(py)
    }
}

#[cfg_attr(feature = "python", pyclass(frozen))]
#[derive(Debug, Default, Clone, PartialEq, Deserialize, Serialize, AbiToken, AsKeccak256)]
#[serde(rename_all = "camelCase")]
pub struct AdvanceSettlementEpoch {
    /// The settlement epoch id
    pub epoch_id: u64,
    pub time: StampedTimeValue,
    /// The list of actions covered by this settlement epoch
    pub actions: Vec<SettlementAction>,
}

#[cfg(feature = "python")]
#[pymethods]
impl AdvanceSettlementEpoch {
    #[new]
    pub fn new_py(epoch_id: u64, time: CmdTimeValue, actions: Vec<SettlementAction>) -> Self {
        Self {
            epoch_id,
            time: time.into(),
            actions,
        }
    }

    #[getter]
    fn time(&self) -> CmdTimeValue {
        self.time.into()
    }

    #[getter]
    fn actions(&self) -> Vec<SettlementAction> {
        self.actions.clone()
    }

    #[getter]
    fn epoch_id(&self) -> u64 {
        self.epoch_id
    }
}

impl AdvanceSettlementEpoch {
    pub fn new(epoch_id: u64, time: StampedTimeValue, actions: Vec<SettlementAction>) -> Self {
        debug_assert!(epoch_id > 0);
        AdvanceSettlementEpoch {
            epoch_id,
            time,
            actions,
        }
    }

    pub fn as_epoch(&self, length: u64) -> Epoch {
        debug_assert!(self.epoch_id > 0);
        Epoch::new(EpochKind::Settlement, self.epoch_id, self.time, length)
    }
}

#[cfg_attr(feature = "python", pyclass(frozen, get_all))]
#[derive(Debug, Default, Clone, PartialEq, Deserialize, Serialize, AbiToken, AsKeccak256)]
#[serde(rename_all = "camelCase")]
pub struct MintPriceCheckpoint {
    pub time_value: TimeValue,
}

#[cfg(feature = "python")]
#[pymethods]
impl MintPriceCheckpoint {
    #[new]
    pub fn new_py(time_value: TimeValue) -> Self {
        Self { time_value }
    }
}

impl MintPriceCheckpoint {
    pub fn new(time_value: TimeValue) -> Self {
        MintPriceCheckpoint { time_value }
    }
}

/// A signal to update product listings is sent by the operator clock tick mechanism based on the
/// current wall clock time. It is used to add or remove products from the exchange's product
/// listings.
///
/// Motivating example: there are different futures products all corresponding to the same futures
/// specs class, but each future is listed/available to trade at different times. For example, ETHF{}
/// is a specs class representing futures tracking the price of ETH. ETHFH is a specific tradable
/// product referring to the ETH future expiring in March that is listed at the time of writing one
/// week before the expiry of the preceding September future until its expiry in March. The operator
/// will update the listings to add ETHFH and remove ETHFH at the appropriate times.
#[cfg_attr(feature = "python", pyclass(frozen, get_all))]
#[derive(Debug, Default, Clone, PartialEq, Deserialize, Serialize, AbiToken, AsKeccak256)]
#[serde(rename_all = "camelCase")]
pub struct UpdateProductListings {
    pub additions: Vec<TradableProductKey>,
    pub removals: Vec<TradableProductKey>,
}

#[cfg(feature = "python")]
#[pymethods]
impl UpdateProductListings {
    #[new]
    pub fn new_py(additions: Vec<TradableProductKey>, removals: Vec<TradableProductKey>) -> Self {
        Self {
            additions,
            removals,
        }
    }
}

/// Traders signal their intent to withdraw which freezes the requested collateral in their account.
///
/// Funds may be available on-chain at the next checkpoint the operator is kind enough to "prove"
/// the withdrawals on behalf of traders. Otherwise, traders may submit a merkle proof
/// at any time after a `Checkpoint` to collect their funds.
#[cfg_eval]
#[cfg_attr(feature = "python", pyclass(get_all))]
#[derive(Debug, Clone, PartialEq, Deserialize, Serialize, Nonced)]
#[cfg_attr(not(target_family = "wasm"), derive(SignedEIP712))]
#[serde(rename_all = "camelCase")]
pub struct WithdrawIntent {
    /// Strategy Id (label)
    pub strategy_id: StrategyId,
    /// Ethereum address of the collateral token (ERC-20)
    pub currency: TokenAddress,
    /// Amount to withdraw
    #[serde(with = "as_scaled_fraction")]
    pub amount: UnscaledI128,
    /// A salt for uniqueness of the EIP-712 hash function. May optionally have business meaning to the client.
    pub nonce: Nonce,
    /// EIP-712 signature of the withdraw intent attributes
    #[cfg_attr(feature = "python", pyo3(set))]
    pub signature: Signature,
}

#[cfg(feature = "python")]
#[pymethods]
impl WithdrawIntent {
    #[new]
    pub fn new_py(
        strategy_id: StrategyId,
        currency: TokenAddress,
        amount: UnscaledI128,
        nonce: Nonce,
        signature: Option<Signature>,
    ) -> Self {
        Self {
            strategy_id,
            currency,
            amount,
            nonce,
            signature: signature.unwrap_or_default(),
        }
    }
}

/// Traders signal their intent to withdraw ddx which freezes the specified amount
/// in their account.
///
/// Funds may be available on-chain at the next checkpoint the operator is kind enough to
/// "prove" the withdrawals on behalf of traders.
///
/// Otherwise, traders may submit a merkle proof at any time after a `Checkpoint` to collect
/// their funds.
#[cfg_eval]
#[cfg_attr(feature = "python", pyclass(get_all))]
#[derive(Debug, Clone, PartialEq, Deserialize, Serialize, Nonced)]
#[cfg_attr(not(target_family = "wasm"), derive(SignedEIP712))]
#[serde(rename_all = "camelCase")]
pub struct WithdrawDDXIntent {
    /// Amount to withdraw
    #[serde(with = "as_scaled_fraction")]
    pub amount: UnscaledI128,
    /// A salt for uniqueness of the EIP-712 hash function. May optionally have
    /// business meaning to the client.
    pub nonce: Nonce,
    /// EIP-712 signature of the withdraw ddx intent attributes
    #[cfg_attr(feature = "python", pyo3(set))]
    pub signature: Signature,
}

#[cfg(feature = "python")]
#[pymethods]
impl WithdrawDDXIntent {
    #[new]
    pub fn new_py(amount: UnscaledI128, nonce: Nonce, signature: Option<Signature>) -> Self {
        Self {
            amount,
            nonce,
            signature: signature.unwrap_or_default(),
        }
    }
}

#[cfg(feature = "insurance_fund_client_req")]
#[cfg_eval]
#[cfg_attr(feature = "python", pyclass(get_all))]
#[derive(Debug, Clone, PartialEq, Deserialize, Serialize, Nonced)]
#[cfg_attr(not(target_family = "wasm"), derive(SignedEIP712))]
#[serde(rename_all = "camelCase")]
pub struct InsuranceFundWithdrawIntent {
    /// Ethereum address of the collateral token (ERC-20)
    pub currency: TokenAddress,
    /// Amount to withdraw
    #[serde(with = "as_scaled_fraction")]
    pub amount: UnscaledI128,
    /// A salt for uniqueness of the EIP-712 hash function. May optionally have business meaning to the client.
    pub nonce: Nonce,
    /// EIP-712 signature of the withdraw intent attributes
    #[cfg_attr(feature = "python", pyo3(set))]
    pub signature: Signature,
}

#[cfg(all(feature = "insurance_fund_client_req", feature = "python"))]
#[pymethods]
impl InsuranceFundWithdrawIntent {
    #[new]
    pub fn new_py(
        currency: TokenAddress,
        amount: UnscaledI128,
        nonce: Nonce,
        signature: Option<Signature>,
    ) -> Self {
        Self {
            currency,
            amount,
            nonce,
            signature: signature.unwrap_or_default(),
        }
    }
}

#[cfg(feature = "database")]
impl ToSql for OrderType {
    fn to_sql(
        &self,
        ty: &Type,
        out: &mut bytes::BytesMut,
    ) -> Result<IsNull, Box<dyn std::error::Error + 'static + Sync + Send>> {
        let value: i32 = (*self).into();
        value.to_sql(ty, out)
    }

    fn accepts(ty: &Type) -> bool {
        // TODO: Confirm resolution then cleanup
        // error[E0034]: multiple applicable items in scope
        //    --> src/types/request.rs:455:14
        //     |
        // 455 |         i32::accepts(ty)
        //     |              ^^^^^^^ multiple `accepts` found
        //     |
        //     = note: candidate #1 is defined in an impl of the trait `FromSql` for the type `i32`
        //     = note: candidate #2 is defined in an impl of the trait `ToSql` for the type `i32`
        <i32 as ToSql>::accepts(ty)
    }

    to_sql_checked!();
}

#[cfg(test)]
pub mod tests {
    use crate::{
        execution::test_utils::ETHP,
        types::ethereum::{ConfirmedBlock, TypedReceipt},
    };
    use alloy::{consensus::Header, rpc::types::TransactionReceipt};
    use core_common::types::accounting::MAIN_STRAT;
    use core_macros::unscaled;
    use serde_json::json;

    use super::*;

    #[test]
    fn test_adjacent_format() {
        let order_intent = OrderIntent {
            symbol: ETHP.into(),
            strategy: Default::default(),
            side: OrderSide::Bid,
            order_type: OrderType::Limit { post_only: false },
            nonce: Default::default(),
            amount: unscaled!(10),
            price: unscaled!(200),
            stop_price: Default::default(),
            session_key_signature: Default::default(),
            signature: Default::default(),
        };
        let request = ClientRequest::Order(order_intent);
        let ser = serde_json::to_value(request).expect("ser");
        let expected = json!({
            "t": "Order",
            "c": {
                "symbol": ETHP,
                "strategy": MAIN_STRAT,
                "side": "Bid",
                "orderType": 0,
                "nonce": "0x0000000000000000000000000000000000000000000000000000000000000000",
                "amount": "10",
                "price": "200",
                "stopPrice": "0",
                "sessionKeySignature": null,
                "signature": "0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
            }
        });
        assert_eq!(ser, expected);
        let _request_: Request = serde_json::from_value(ser).unwrap();
    }

    #[test]
    fn test_serde_order_intent() {
        let order = OrderIntent {
            symbol: "ETHP".into(),
            strategy: Default::default(),
            side: OrderSide::Bid,
            order_type: OrderType::Limit { post_only: false },
            nonce: Default::default(),
            amount: unscaled!(10),
            price: unscaled!(200),
            stop_price: Default::default(),
            session_key_signature: Default::default(),
            signature: Default::default(),
        };
        let ser = serde_json::to_value(order).expect("ser");
        let expected = json!({
            "symbol": ETHP,
            "strategy": MAIN_STRAT,
            "side": "Bid",
            "orderType": 0,
            "nonce": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "amount": "10",
            "price": "200",
            "stopPrice": "0",
            "sessionKeySignature": null,
            "signature": "0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
        });
        assert_eq!(ser, expected);
    }

    #[test]
    fn test_serde_cancel_order_intent() {
        let cancel_order = CancelOrderIntent {
            symbol: "ETHP".into(),
            order_hash: OrderHash::default(),
            nonce: Default::default(),
            session_key_signature: Default::default(),
            signature: Default::default(),
        };
        let ser = serde_json::to_value(cancel_order).expect("ser");
        let json = json!({
             "symbol": "ETHP",
             "orderHash": OrderHash::default(),
             "nonce": "0x0000000000000000000000000000000000000000000000000000000000000000",
             "sessionKeySignature": null,
             "signature": "0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
        });
        assert_eq!(ser, json);
    }

    #[test]
    fn test_serde_index_price() {
        let index_price = IndexPrice {
            symbol: "ETHP".into(),
            price: Default::default(),
            prev_price: Default::default(),
            metadata: PriceMetadata::SingleNamePerpetual,
            timestamp: Default::default(),
        };
        let request = Cmd::IndexPrice(index_price);
        let encoded = serde_json::to_string(&request).unwrap();
        tracing::debug!("The encoded event: {}", encoded);

        let decoded: Request = serde_json::from_str(&encoded).unwrap();
        tracing::debug!("The decoded event: {:?}", decoded);
    }

    #[test]
    fn test_sub_enum_ser() {
        let order_intent = OrderIntent {
            symbol: ETHP.into(),
            strategy: Default::default(),
            side: OrderSide::Bid,
            order_type: OrderType::Limit { post_only: false },
            nonce: Default::default(),
            amount: unscaled!(10),
            price: unscaled!(200),
            stop_price: Default::default(),
            session_key_signature: Default::default(),
            signature: Default::default(),
        };
        let request = Request::ClientRequest(ClientRequest::Order(order_intent));
        let ser = serde_json::to_value(request).expect("ser");
        let expected = json!({
            "t": "Order",
            "c": {
                "symbol": ETHP,
                "strategy": MAIN_STRAT,
                "side": "Bid",
                "orderType": 0,
                "nonce": "0x0000000000000000000000000000000000000000000000000000000000000000",
                "amount": "10",
                "price": "200",
                "stopPrice": "0",
                "sessionKeySignature": null,
                "signature": "0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
            }
        });
        assert_eq!(ser, expected);
        let _request_: Request = serde_json::from_value(ser).unwrap();
    }

    #[test]
    #[cfg(feature = "eth-base")]
    fn test_serde_pre_processed_request() {
        let json_str = r#"{"transactionHash":"0x21f6554c28453a01e7276c1db2fc1695bb512b170818bfa98fa8136433100616","blockHash":"0x4acbdefb861ef4adedb135ca52865f6743451bfbfa35db78076f881a40401a5e","blockNumber":"0x129f4b9","logsBloom":"0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000200000000000000000040000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000400000800000000000000000000000000000000004000000000000000000800000000100000020000000000000000000080000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000010000000000000000000000000000","gasUsed":"0xbde1","contractAddress":null,"cumulativeGasUsed":"0xa42aec","transactionIndex":"0x7f","from":"0x9a53bfba35269414f3b2d20b52ca01b15932c7b2","to":"0xdac17f958d2ee523a2206206994597c13d831ec7","type":"0x2","effectiveGasPrice":"0xfb0f6e8c9","logs":[{"blockHash":"0x4acbdefb861ef4adedb135ca52865f6743451bfbfa35db78076f881a40401a5e","address":"0xdac17f958d2ee523a2206206994597c13d831ec7","logIndex":"0x118","data":"0x00000000000000000000000000000000000000000052b7d2dcc80cd2e4000000","removed":false,"topics":["0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925","0x0000000000000000000000009a53bfba35269414f3b2d20b52ca01b15932c7b2","0x00000000000000000000000039e5dbb9d2fead31234d7c647d6ce77d85826f76"],"blockNumber":"0x129f4b9","transactionIndex":"0x7f","transactionHash":"0x21f6554c28453a01e7276c1db2fc1695bb512b170818bfa98fa8136433100616"}],"status":"0x1"}"#;
        let receipt: TransactionReceipt = serde_json::from_str(json_str).unwrap();
        let receipt: TypedReceipt = receipt.into();
        // serialize and deserialize the receipt
        let receipt_ser = cbor4ii::serde::to_vec(vec![], &receipt).expect("ser");
        let receipt_de = cbor4ii::serde::from_slice(&receipt_ser).expect("de");
        assert_eq!(receipt, receipt_de);
        let confirmed_block = ConfirmedBlock {
            header: Header::default(),
            receipts: vec![receipt],
        };
        // serialize and deserialize the confirmed block
        let confirmed_block_ser = cbor4ii::serde::to_vec(vec![], &confirmed_block).expect("ser");
        let confirmed_block_de = cbor4ii::serde::from_slice(&confirmed_block_ser).expect("de");
        assert_eq!(confirmed_block, confirmed_block_de);
        let pre_processed_request = PreProcessedRequest::Block(Block(1), confirmed_block);
        let ser = cbor4ii::serde::to_vec(vec![], &pre_processed_request).expect("ser");
        let de = cbor4ii::serde::from_slice(&ser).expect("de");
        assert_eq!(pre_processed_request, de);
    }
}
