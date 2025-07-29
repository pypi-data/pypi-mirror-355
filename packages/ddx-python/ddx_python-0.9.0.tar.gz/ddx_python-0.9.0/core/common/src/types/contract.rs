use alloy_primitives::{Address, B256, U128};
use core_macros::AbiToken;
use serde::{Deserialize, Serialize};
use std::{collections::HashMap, vec::Vec};

#[derive(Debug, Clone, PartialEq, AbiToken)]
pub struct CustodianWithoutSigners {
    /// The DDX balance of the custodian.
    pub balance: U128,
    /// The block in which the custodian can unbond themselves.
    pub unbond_eta: U128,
    /// Indicates whether or not the custodian is approved to register
    /// signers.
    pub approved: bool,
    /// Indicates whether or not the custodian was jailed due to submitting
    /// a non-matching hash or at the discretion of governance.
    pub jailed: bool,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Faucet {
    pub address: Address,
    pub private_key: B256,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct ContractAddresses {
    #[serde(rename = "derivaDEXAddress")]
    pub derivadex: Address,
    #[serde(rename = "ddxAddress")]
    pub ddx_token: Address,
    #[serde(rename = "usdcAddress")]
    pub usdc_token: Address,

    #[serde(flatten)]
    pub other: HashMap<String, serde_json::Value>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct DeploymentMeta {
    pub addresses: ContractAddresses,
    pub chain_id: u64,
    pub eth_rpc_url: String,
    pub faucet: Option<Faucet>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
struct AddressesMeta(HashMap<String, DeploymentMeta>);

impl DeploymentMeta {
    pub fn from_deployment(contract_deployment: &str) -> Self {
        let share_dir = std::env::var("APP_CONFIG").expect("APP_CONFIG not set");
        let mut addresses_path = std::path::PathBuf::from(&share_dir);
        addresses_path.push("ethereum/addresses.json");
        tracing::debug!(
            ?contract_deployment,
            ?addresses_path,
            "Environment app context"
        );
        let f = std::fs::File::open(addresses_path)
            .expect("Cannot initialize app context without addresses.json");
        let data =
            serde_json::from_str::<AddressesMeta>(std::io::read_to_string(f).unwrap().as_str())
                .expect("Cannot parse addresses.json");
        let meta = data
            .0
            .get(contract_deployment)
            .expect("CONTRACT_DEPLOYMENT not found in addresses.json");
        tracing::debug!(
            "Read from addresses.json: {:?} {:?}",
            meta.chain_id,
            meta.addresses
        );
        meta.clone()
    }

    pub fn from_env() -> Self {
        let contract_deployment =
            std::env::var("CONTRACT_DEPLOYMENT").unwrap_or_else(|_| "snapshot".to_string());
        Self::from_deployment(&contract_deployment)
    }
}
