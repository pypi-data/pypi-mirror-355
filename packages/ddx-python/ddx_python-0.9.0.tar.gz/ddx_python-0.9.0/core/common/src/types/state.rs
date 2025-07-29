use crate::{Address, B256, Error, Result, constants::ALCHEMY_ENDPOINT_PATH};

use core_macros::AbiToken;
use regex::Regex;
use serde::{Deserialize, Serialize};
use std::{collections::HashMap, str::FromStr};
use strum::{Display, EnumString};
use url::Url;

use super::{identifiers::ChainVariant, primitives::TraderAddress};

#[derive(Clone, Eq, PartialEq, Hash)]
pub enum BlockchainSender {
    UnlockedAccount(Address),
    SecretKey(B256),
}

/// For security reasons, printing only the Ethereum address even when using private keys.
impl std::fmt::Debug for BlockchainSender {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let text = match self {
            BlockchainSender::UnlockedAccount(ref address) => {
                format!("Unlocked Account {}", address)
            }
            BlockchainSender::SecretKey(_) => "Hidden Private Key".to_string(),
        };
        f.debug_tuple("BlockchainSender").field(&text).finish()
    }
}

impl FromStr for BlockchainSender {
    type Err = Error;

    fn from_str(text: &str) -> Result<Self, Self::Err> {
        if text.len() == 42 {
            let address: Address = serde_json::from_str(format!(r#""{}""#, text).as_str())
                .map_err(|e| Error::Parse(format!("Address from str {:?}", e)))?;
            Ok(BlockchainSender::UnlockedAccount(address))
        } else if text.len() == 66 {
            let secret_key: B256 = serde_json::from_str(format!(r#""{}""#, text).as_str())
                .map_err(|e| Error::Parse(format!("B256 from str {:?}", e)))?;
            Ok(BlockchainSender::SecretKey(secret_key))
        } else {
            Err(Error::Parse(
                "Expected a 0x prefixed 20 bytes address or 32 bytes secret key".to_string(),
            ))
        }
    }
}

impl From<&TraderAddress> for BlockchainSender {
    fn from(bytes: &TraderAddress) -> Self {
        Self::UnlockedAccount(bytes.to_eth_address())
    }
}

impl From<TraderAddress> for BlockchainSender {
    fn from(bytes: TraderAddress) -> Self {
        (&bytes).into()
    }
}

/// Supported chain variants with the environment identifier
#[derive(Debug, Copy, Clone, Serialize, Deserialize, AbiToken, PartialEq)]
pub enum Chain {
    /// Ethereum contains a chain_id to identify the network
    Ethereum(u64),
}

impl Chain {
    pub fn variant(&self) -> ChainVariant {
        match self {
            Chain::Ethereum(_) => ChainVariant::Ethereum,
        }
    }
}

#[repr(i16)]
#[derive(Debug, Clone, PartialEq, Eq, std::hash::Hash, Serialize, Deserialize)]
pub enum SealedDataKey {
    SecretUserData = 0,
}

impl TryFrom<i16> for SealedDataKey {
    type Error = Error;
    fn try_from(value: i16) -> Result<Self, Self::Error> {
        match value {
            0 => Ok(SealedDataKey::SecretUserData),
            _ => Err(crate::error!(
                "Invalid sealed data key discriminant {:?}",
                value
            )),
        }
    }
}

#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct SealedData(pub HashMap<SealedDataKey, Vec<u8>>);

impl SealedData {
    pub fn is_empty(&self) -> bool {
        self.0.is_empty()
    }

    pub fn user_data(&self) -> Option<&Vec<u8>> {
        self.0.get(&SealedDataKey::SecretUserData)
    }

    pub fn insert_user_data(&mut self, data: Vec<u8>) {
        self.0.insert(SealedDataKey::SecretUserData, data);
    }
}

// Configuration variables for the trusted context
#[derive(Debug, Clone, PartialEq, Default, Serialize, Deserialize, Display, EnumString)]
#[strum(serialize_all = "snake_case")]
pub enum EthNetwork {
    #[default]
    Geth,
    Mainnet,
    Goerli,
    Sepolia,
    Gnosis,
}

impl TryInto<Chain> for EthNetwork {
    type Error = Error;

    fn try_into(self) -> Result<Chain, Self::Error> {
        match self {
            EthNetwork::Geth => Ok(Chain::Ethereum(1337)),
            EthNetwork::Mainnet => Ok(Chain::Ethereum(1)),
            EthNetwork::Goerli => Ok(Chain::Ethereum(5)),
            EthNetwork::Sepolia => Ok(Chain::Ethereum(11155111)),
            EthNetwork::Gnosis => Ok(Chain::Ethereum(100)),
        }
    }
}

impl TryFrom<Chain> for EthNetwork {
    type Error = Error;

    fn try_from(value: Chain) -> Result<Self, Self::Error> {
        match value {
            Chain::Ethereum(1337) => Ok(EthNetwork::Geth),
            Chain::Ethereum(1) => Ok(EthNetwork::Mainnet),
            Chain::Ethereum(5) => Ok(EthNetwork::Goerli),
            Chain::Ethereum(11155111) => Ok(EthNetwork::Sepolia),
            Chain::Ethereum(100) => Ok(EthNetwork::Gnosis),
            _ => Err(Error::Conversion(format!("Invalid Chain: {:?}", value))),
        }
    }
}

#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct EthContext {
    pub network: EthNetwork,
    /// Pre-validated Alchemy API key URL parameter
    alchemy_api_key: String,
}

impl EthContext {
    pub fn new(network: EthNetwork, alchemy_api_key: String) -> Result<Self, Error> {
        Regex::new(r"^[\w-]+$")
            .unwrap()
            .find(&alchemy_api_key)
            .ok_or_else(|| Error::Conversion("Invalid Alchemy API key".to_string()))?;
        Ok(Self {
            network,
            alchemy_api_key,
        })
    }

    pub fn url(&self) -> Url {
        let url = format!(
            "https://eth-{}.{}/{}",
            self.network, ALCHEMY_ENDPOINT_PATH, self.alchemy_api_key
        );
        url.parse().expect("URL parts must be pre-validated")
    }
}

#[cfg(not(target_family = "wasm"))]
pub trait ConfigurableFromEnv {
    /// Read config from the environment
    fn from_env() -> Self;
}

#[cfg(not(target_family = "wasm"))]
impl ConfigurableFromEnv for EthContext {
    fn from_env() -> Self {
        let meta = core_common::types::contract::DeploymentMeta::from_env();
        let app_network: EthNetwork = Chain::Ethereum(meta.chain_id).try_into().unwrap();
        if app_network != EthNetwork::Geth && app_network != EthNetwork::Gnosis {
            let (network, alchemy_api_key) = extract_network_and_key(&meta.eth_rpc_url).unwrap();
            assert!(
                network == app_network,
                "Mismatch between the network in the ETH_RPC_URL and the CHAIN_ID"
            );
            EthContext {
                network,
                alchemy_api_key,
            }
        } else {
            EthContext {
                network: app_network,
                alchemy_api_key: "".to_string(),
            }
        }
    }
}

pub fn extract_network_and_key(url: &str) -> Result<(EthNetwork, String)> {
    let pattern = r"https://eth-(?P<network>[\w-]+)\.g\.alchemy\.com/v2/(?P<key>[\w-]+)";
    let re = Regex::new(pattern).unwrap();
    if let Some(captures) = re.captures(url) {
        let network_value = captures.name("network").unwrap().as_str();
        let key_value = captures.name("key").unwrap().as_str();
        let network = EthNetwork::try_from(network_value)?;
        Ok((network, key_value.to_string()))
    } else {
        Err(Error::Conversion(
            "Failed to extract network and key from url".to_string(),
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_eth_rpc_url() {
        let url = "https://eth-mainnet.g.alchemy.com/v2/1234567890abcdef";
        let (network, key) = extract_network_and_key(url).unwrap();
        assert_eq!(network, EthNetwork::Mainnet);
        assert_eq!(key, "1234567890abcdef");
    }
}
