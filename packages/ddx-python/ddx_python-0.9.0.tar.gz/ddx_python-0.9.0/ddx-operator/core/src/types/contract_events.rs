use crate::{
    specs::types::{SpecsExpr, SpecsKey, SpecsUpdate},
    types::{
        ethereum::LogEntry,
        identifiers::{InsuranceFundContributorAddress, SignerAddress, StrategyIdHash},
        state::VoidableItem,
        transaction::{
            BlockTxStamp, CheckpointConfirmed, InsuranceFundUpdate, StrategyUpdate,
            StrategyUpdateKind, TraderUpdate,
        },
    },
};
use alloy::sol_types::{SolEvent, sol};
use core_common::{
    B256, Result, U128, ensure, error,
    types::{
        global::TokenAddress,
        identifiers::ReleaseHash,
        primitives::{Bytes32, Hash, RecordedAmount, TraderAddress},
        transaction::EpochId,
    },
};
use core_macros::AbiToken;
use serde::{Deserialize, Serialize};
use std::convert::TryFrom;

sol! {
    event SpecsUpdated(bytes30 indexed key, string specs, uint8 op);

    event StrategyUpdated(
        address indexed trader,
        address indexed collateralAddress,
        bytes4 indexed strategyIdHash,
        // strategyId will be null in the case of withdrawals.
        bytes32 strategyId,
        uint128 amount,
        uint8 updateKind
    );

    event TraderUpdated(address indexed trader, uint128 amount, uint8 updateKind);

    event FundedInsuranceFundUpdated(
        address indexed contributor,
        address indexed collateralAddress,
        uint128 amount,
        uint8 updateKind
    );

    event Checkpointed(
        bytes32 indexed stateRoot,
        bytes32 indexed transactionRoot,
        uint128 indexed epochId,
        address[] custodians,
        uint128[] bonds,
        address submitter
    );

    event SignerRegistered(bytes32 indexed releaseHash, address indexed custodian, address indexed signer);

    event ReleaseScheduleUpdated(bytes32 indexed mrEnclave, bytes2 indexed isvSvn, uint128 indexed startingEpochId);
}

pub(crate) fn all_event_signatures() -> Vec<B256> {
    vec![
        SpecsUpdated::SIGNATURE_HASH,
        StrategyUpdated::SIGNATURE_HASH,
        TraderUpdated::SIGNATURE_HASH,
        FundedInsuranceFundUpdated::SIGNATURE_HASH,
        Checkpointed::SIGNATURE_HASH,
        SignerRegistered::SIGNATURE_HASH,
        ReleaseScheduleUpdated::SIGNATURE_HASH,
    ]
}

pub(crate) fn decode_contract_events(log: LogEntry) -> Vec<ContractEvent> {
    if !log.topics().is_empty() {
        let signature = log.topics()[0];
        if signature == SpecsUpdated::SIGNATURE_HASH {
            SpecsUpdate::from_log(log)
                .map(ContractEvent::SpecsUpdate)
                .ok()
        } else if signature == StrategyUpdated::SIGNATURE_HASH {
            StrategyUpdate::from_log(log)
                .map(ContractEvent::StrategyUpdate)
                .ok()
        } else if signature == TraderUpdated::SIGNATURE_HASH {
            TraderUpdate::from_log(log)
                .map(ContractEvent::TraderUpdate)
                .ok()
        } else if signature == FundedInsuranceFundUpdated::SIGNATURE_HASH {
            InsuranceFundUpdate::from_log(log)
                .map(ContractEvent::InsuranceFundUpdate)
                .ok()
        } else if signature == Checkpointed::SIGNATURE_HASH {
            CheckpointConfirmed::from_log(log)
                .map(ContractEvent::Checkpointed)
                .ok()
        } else if signature == SignerRegistered::SIGNATURE_HASH {
            SignerRegisteredMeta::from_log(log)
                .map(ContractEvent::SignerRegistered)
                .ok()
        } else if signature == ReleaseScheduleUpdated::SIGNATURE_HASH {
            ReleaseUpdate::from_log(log)
                .map(ContractEvent::ReleaseScheduleUpdated)
                .ok()
        } else {
            None
        }
    } else {
        None
    }
    .map_or(vec![], |e| vec![e])
}

/// All possible relevant events emitted by the smart contract
// TODO 3591: Standardize event common attributes (tx_hash, block_number, etc). Giving the block number to `ParseLog::from_log` is probably easiest.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum ContractEvent {
    SpecsUpdate(SpecsUpdate),
    // TODO 3591: The idea is that we capture the event data into this raw type, and then enrich it with metadata. Make sure this isn't error prone given the use of default values.
    StrategyUpdate(StrategyUpdate<RecordedAmount>),
    TraderUpdate(TraderUpdate<RecordedAmount>),
    InsuranceFundUpdate(InsuranceFundUpdate<RecordedAmount>),
    BalanceTransfer,
    WithdrawConfirmed,
    Checkpointed(CheckpointConfirmed),
    SignerRegistered(SignerRegisteredMeta),
    ReleaseScheduleUpdated(ReleaseUpdate),
}

pub trait ParseLog {
    fn from_log(value: LogEntry) -> Result<Self>
    where
        Self: Sized;
}

impl ParseLog for SpecsUpdate {
    fn from_log(log: LogEntry) -> Result<Self> {
        let event = SpecsUpdated::decode_raw_log(log.topics(), log.data(), true)?;
        let key = SpecsKey::decode(event.key.as_slice())?;
        let specs = SpecsExpr::new(event.specs);
        // Matching enum: `enum SpecsUpdateType { Upsert, Remove }`
        if event.op == 0 {
            ensure!(specs.is_some(), "Got upsert op but the expression is empty");
            Ok(SpecsUpdate {
                key,
                expr: specs,
                block_number: Default::default(),
                tx_hash: log.tx_hash.into(),
            })
        } else if event.op == 1 {
            ensure!(specs.is_void(), "Got remove op but an expression was given");
            Ok(SpecsUpdate {
                key,
                expr: specs,
                block_number: Default::default(),
                tx_hash: log.tx_hash.into(),
            })
        } else {
            Err(error!(
                "Unexpected specs update operation discriminant {:?}",
                event.op
            ))
        }
    }
}

impl ParseLog for StrategyUpdate<RecordedAmount> {
    fn from_log(log: LogEntry) -> Result<Self> {
        let event = StrategyUpdated::decode_raw_log(log.topics(), log.data(), true)?;
        let mut update = StrategyUpdate {
            trader: event.trader.into(),
            collateral_address: TokenAddress::collateral(event.collateralAddress),
            strategy_id_hash: StrategyIdHash::from_slice(event.strategyIdHash.as_slice()),
            strategy_id: {
                // use the contract event strategy id unless it is not valid utf8, in which
                // case default to main
                let raw_value = Bytes32::from(event.strategyId);
                if raw_value == Bytes32::default() {
                    None
                } else {
                    Some(raw_value.into())
                }
            },
            // We need to convert the u128 from SolEvent back to U128 before converting to UnscaledI128
            amount: U128::try_from(event.amount).unwrap().into(),
            update_kind: StrategyUpdateKind::try_from(event.updateKind).unwrap(),
            tx_stamp: Some(BlockTxStamp {
                block_number: 0,
                tx_hash: log.tx_hash.into(),
            }),
        };

        // Compare the strategy id hash and the strategy id
        // If the strategy id hash does not match the strategy id then we set the strategy id hash
        // to that of the strategy id
        if let Some(s) = update.strategy_id.as_ref() {
            let id_hash = (*s).into();
            if update.strategy_id_hash != id_hash {
                tracing::warn!(event_id_hash=?update.strategy_id_hash, ?id_hash, "The strategy id hash from the contract event does not match the hash generated from the strategy id. Setting the strategy id hash to that from the strategy id for consistency");
                update.strategy_id_hash = id_hash;
            }
        }
        Ok(update)
    }
}

impl ParseLog for TraderUpdate<RecordedAmount> {
    fn from_log(log: LogEntry) -> Result<Self> {
        let trader_event = TraderUpdated::decode_raw_log(log.topics(), log.data(), true)?;
        let event = TraderUpdate {
            trader: trader_event.trader.into(),
            amount: Some(U128::try_from(trader_event.amount).unwrap().into()),
            update_kind: trader_event.updateKind.try_into()?,
            tx_stamp: Some(BlockTxStamp {
                block_number: 0,
                tx_hash: log.tx_hash.into(),
            }),
            pay_fees_in_ddx: None,
        };
        Ok(event)
    }
}

impl ParseLog for CheckpointConfirmed {
    fn from_log(log: LogEntry) -> Result<Self> {
        let log_event = Checkpointed::decode_raw_log(log.topics(), log.data(), true)?;
        let event = CheckpointConfirmed {
            state_root: log_event.stateRoot.into(),
            tx_root: log_event.transactionRoot.into(),
            epoch_id: log_event.epochId.try_into().unwrap(),
            custodians: log_event.custodians.into_iter().map(|a| a.into()).collect(),
            bonds: log_event
                .bonds
                .into_iter()
                .map(|b| (U128::from(b) / "1000000000000".parse::<U128>().unwrap()).into())
                .collect(),
            submitter: log_event.submitter.into(),
            tx_stamp: Some(BlockTxStamp {
                block_number: Default::default(),
                tx_hash: log.tx_hash.into(),
            }),
        };
        Ok(event)
    }
}

impl ParseLog for InsuranceFundUpdate<RecordedAmount> {
    fn from_log(log: LogEntry) -> Result<Self> {
        let insurance_event =
            FundedInsuranceFundUpdated::decode_raw_log(log.topics(), log.data(), true)?;
        let event = InsuranceFundUpdate {
            address: InsuranceFundContributorAddress(insurance_event.contributor.into()),
            collateral_address: TokenAddress::collateral(insurance_event.collateralAddress),
            amount: U128::try_from(insurance_event.amount).unwrap().into(),
            update_kind: insurance_event.updateKind.try_into()?,
            tx_hash: log.tx_hash.into(),
        };
        Ok(event)
    }
}

#[derive(Debug, Default, Clone, PartialEq, Deserialize, Serialize, AbiToken)]
#[serde(rename_all = "camelCase")]
pub struct SignerRegisteredMeta {
    pub release_hash: ReleaseHash,
    pub custodian: TraderAddress,
    pub signer_address: SignerAddress,
    pub tx_hash: Hash,
}

impl ParseLog for SignerRegisteredMeta {
    fn from_log(log: LogEntry) -> Result<Self> {
        let signer_registered_event =
            SignerRegistered::decode_raw_log(log.topics(), log.data(), true)?;
        let event = SignerRegisteredMeta {
            release_hash: Bytes32::from(signer_registered_event.releaseHash).into(),
            custodian: signer_registered_event.custodian.into(),
            signer_address: signer_registered_event.signer.into(),
            tx_hash: log.tx_hash.into(),
        };
        Ok(event)
    }
}

#[derive(Debug, Clone, Copy, Default, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ReleaseUpdate {
    pub release_hash: ReleaseHash,
    pub starting_epoch_id: EpochId,
}

impl ParseLog for ReleaseUpdate {
    fn from_log(log: LogEntry) -> Result<Self> {
        let release_schedule_updated_event =
            ReleaseScheduleUpdated::decode_raw_log(log.topics(), log.data(), true)?;
        let mut event = ReleaseUpdate::default();
        let mr_enclave: Bytes32 = release_schedule_updated_event.mrEnclave.into();
        let isvsvn = u16::from_be_bytes(release_schedule_updated_event.isvSvn.0);
        event.starting_epoch_id = release_schedule_updated_event
            .startingEpochId
            .try_into()
            .unwrap();
        event.release_hash = ReleaseHash::new(mr_enclave.as_bytes(), isvsvn);
        tracing::debug!(?event, "Parsed ReleaseUpdate event");
        Ok(event)
    }
}
