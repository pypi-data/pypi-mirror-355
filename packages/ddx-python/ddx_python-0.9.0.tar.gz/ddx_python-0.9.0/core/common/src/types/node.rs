use std::{net::SocketAddr, str::FromStr, time::Duration};

use crate::{
    Error, Result,
    constants::RUNTIME_MAX_WORKER_THREADS,
    types::state::{BlockchainSender, ConfigurableFromEnv},
};
use clap::{ArgMatches, Args, Command, FromArgMatches, arg, value_parser};
use core_macros::AbiToken;
use derive_builder::Builder;
use lazy_static::lazy_static;
use regex::Regex;
use serde::{Deserialize, Serialize};

lazy_static! {
    /// Regex for HTTP URLs (not IPv6 compatible) with optional port and path
    static ref URL_RE: Regex =
        Regex::new(r"^http(?P<s>s)?://(?P<h>[a-z0-9\.\-]+)(?P<p>:\d+)?(/[a-z0-9\.\-]*)*$")
            .expect("Invalid URL regex");
}

pub const LOCALHOST_ADDRESS: &str = "127.0.0.1";
pub const DEFAULT_PORT_RANGE_START: u16 = 11000;

/// Holds a URL string valid for a node
#[derive(Debug, Default, Clone, Eq, PartialEq, std::hash::Hash, Serialize)]
pub struct NodeUrl(pub String);

impl NodeUrl {
    fn new(url: String) -> Result<Self> {
        if URL_RE.is_match(&url) {
            Ok(NodeUrl(url))
        } else {
            Err(Error::Parse(format!("Invalid URL: {}", url)))
        }
    }

    #[cfg(feature = "test_harness")]
    pub fn with_localhost(port: u16) -> Self {
        NodeUrl(format!("http://{}:{}", LOCALHOST_ADDRESS, port))
    }

    /// Creates a service URL by convention for the given node ID
    pub fn with_service(node_id: u64) -> Self {
        NodeUrl(format!("http://operator-node{}:8080", node_id))
    }
}

impl FromStr for NodeUrl {
    type Err = Error;

    fn from_str(s: &str) -> Result<Self> {
        NodeUrl::new(s.to_string())
    }
}

impl<'de> Deserialize<'de> for NodeUrl {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let url = String::deserialize(deserializer)?;
        NodeUrl::new(url).map_err(serde::de::Error::custom)
    }
}

impl std::fmt::Display for NodeUrl {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

/// List of bootstrap node URLs used for initial peer discovery
#[derive(Debug, Clone, Default)]
pub struct BootstrapNodeUrls(Vec<NodeUrl>);

impl BootstrapNodeUrls {
    pub fn new(urls: Vec<NodeUrl>) -> Self {
        Self(urls)
    }

    /// Copy into `NonEmptyNodeUrls` if not empty
    pub fn to_urls(&self) -> Result<NonEmptyNodeUrls> {
        NonEmptyNodeUrls::new(self.0.to_vec())
    }

    /// Return the inner slice of URLs
    pub fn as_urls(&self) -> &[NodeUrl] {
        &self.0
    }

    pub fn push(&mut self, url: NodeUrl) {
        self.0.push(url);
    }
}

/// List of at least one peer node URLs
#[derive(Debug, Clone)]
pub struct NonEmptyNodeUrls(Vec<NodeUrl>);

impl NonEmptyNodeUrls {
    pub fn new(urls: Vec<NodeUrl>) -> Result<Self, Error> {
        if urls.is_empty() {
            return Err(Error::Conversion(
                "At least one peer node URL must be provided".to_string(),
            ));
        }
        Ok(Self(urls))
    }

    pub fn urls(&self) -> &[NodeUrl] {
        &self.0
    }

    pub fn contains(&self, url: &NodeUrl) -> bool {
        self.0.contains(url)
    }
}

/// Configurable backoff parameters
#[derive(Debug, Clone)]
pub struct BackoffConfig {
    pub initial_interval: Duration,
    pub max_interval: Duration,
    pub max_elapsed_time: Duration,
}

#[cfg(feature = "test_harness")]
impl BackoffConfig {
    pub fn test_defaults() -> Self {
        BackoffConfig {
            initial_interval: Duration::from_millis(50),
            max_interval: Duration::from_secs(1),
            max_elapsed_time: Duration::from_secs(60 * 2),
        }
    }
}

impl ConfigurableFromEnv for BackoffConfig {
    fn from_env() -> Self {
        BackoffConfig {
            initial_interval: Duration::from_millis(
                std::env::var("BACKOFF_INITIAL_INTERVAL_IN_MS")
                    .ok()
                    .map(|s| s.parse::<u64>().unwrap())
                    .unwrap_or(50),
            ),
            max_interval: Duration::from_millis(
                std::env::var("BACKOFF_MAX_INTERVAL_IN_MS")
                    .ok()
                    .map(|s| s.parse::<u64>().unwrap())
                    .unwrap_or(1000),
            ),
            max_elapsed_time: Duration::from_millis(
                std::env::var("BACKOFF_MAX_ELAPSED_TIME_IN_MS")
                    .ok()
                    .map(|s| s.parse::<u64>().unwrap())
                    .unwrap_or(2 * 60 * 1000),
            ),
        }
    }
}

impl FromArgMatches for BackoffConfig {
    fn from_arg_matches(matches: &ArgMatches) -> std::prelude::v1::Result<Self, clap::Error> {
        // First build from env variables
        let mut backoff = BackoffConfig::from_env();
        // Override with values provided by arguments if applicable
        if let Some(initial_interval) = matches.get_one::<u64>("initial_interval") {
            backoff.initial_interval = Duration::from_millis(*initial_interval);
        }
        if let Some(max_interval) = matches.get_one::<u64>("max_interval") {
            backoff.max_interval = Duration::from_millis(*max_interval);
        }
        if let Some(max_elapsed_time) = matches.get_one::<u64>("max_elapsed_time") {
            backoff.max_elapsed_time = Duration::from_millis(*max_elapsed_time);
        }
        Ok(backoff)
    }

    fn update_from_arg_matches(
        &mut self,
        matches: &ArgMatches,
    ) -> std::prelude::v1::Result<(), clap::Error> {
        if let Some(initial_interval) = matches.get_one::<u64>("initial_interval") {
            self.initial_interval = Duration::from_millis(*initial_interval);
        }
        if let Some(max_interval) = matches.get_one::<u64>("max_interval") {
            self.max_interval = Duration::from_millis(*max_interval);
        }
        if let Some(max_elapsed_time) = matches.get_one::<u64>("max_elapsed_time") {
            self.max_elapsed_time = Duration::from_millis(*max_elapsed_time);
        }
        Ok(())
    }
}

impl Args for BackoffConfig {
    fn augment_args(cmd: Command) -> Command {
        cmd.arg(
            arg!(--initial_interval [MILLISECONDS] "Initial backoff interval")
                .value_parser(value_parser!(u64)),
        )
        .arg(
            arg!(--max_interval [MILLISECONDS] "Max backoff interval")
                .value_parser(value_parser!(u64)),
        )
        .arg(
            arg!(--max_elapsed_time [MILLISECONDS] "Max elapsed time before the backoff fails")
                .value_parser(value_parser!(u64)),
        )
    }

    fn augment_args_for_update(cmd: Command) -> Command {
        cmd.arg(
            arg!(--initial_interval [MILLISECONDS] "Initial backoff interval")
                .value_parser(value_parser!(u64)),
        )
        .arg(
            arg!(--max_interval [MILLISECONDS] "Max backoff interval")
                .value_parser(value_parser!(u64)),
        )
        .arg(
            arg!(--max_elapsed_time [MILLISECONDS] "Max elapsed time before the backoff fails")
                .value_parser(value_parser!(u64)),
        )
    }
}

#[derive(Debug, Clone, PartialEq, Deserialize, Serialize, AbiToken)]
pub enum WantRole {
    /// The node is completely passive; replicating entries, but neither voting nor timing out.
    Learner,
    /// Regular node replicating logs from the leader and may be elected as leader.
    RegularNode,
}

/// Configuration for the node.
///
/// Utilizes the builder pattern to accommodate different operating modes.
/// Primarily, `from_env` reads configurations from the environment variables,
/// while `test_defaults` provides defaults suitable for testing, eschewing assumptions
/// about default values. The builder's validation ensures all necessary parameters are provided.
#[derive(Debug, Clone, Builder)]
pub struct NodeContext {
    pub node_id: u64,
    pub custodian: BlockchainSender,
    pub db_connstr: String,
    pub bind_address: String,
    pub bind_port: u16,
    pub node_url: NodeUrl,
    pub core_threads: usize,
    pub eth_polling_interval_in_secs: u64,
    pub contract_deployment: String,
    pub contract_server_url: String,
    pub bootstrap_nodes: BootstrapNodeUrls,
    pub backoff: BackoffConfig,
    pub want_role: WantRole,
}

impl NodeContext {
    pub fn bind_address(&self) -> SocketAddr {
        (format!("{}:{}", self.bind_address, self.bind_port).as_str())
            .parse()
            .unwrap()
    }
}

impl NodeContextBuilder {
    pub fn from_env(db_env: &str) -> Self {
        let mut builder = Self::default();
        builder.node_url(
            std::env::var("OPERATOR_REST_API_URL")
                .unwrap_or_else(|_| "http://localhost:8080".to_string())
                .parse()
                .unwrap(),
        );
        let bind_addr =
            std::env::var("NODE_BIND_ADDRESS").unwrap_or_else(|_| "localhost:8080".to_string());
        let (bind_address, bind_port) = bind_addr
            .rfind(':')
            .map(|split_at| bind_addr.split_at(split_at))
            .and_then(|(addr, port)| {
                match port.trim_matches(|c: char| !c.is_numeric()).parse::<u16>() {
                    Ok(port) => Some((addr.to_string(), port)),
                    Err(e) => {
                        tracing::error!("Couldn't parse '{}': {}", port, e);
                        None
                    }
                }
            })
            .unwrap();
        builder.bind_address(bind_address);
        builder.bind_port(bind_port);

        if let Ok(node_id) = std::env::var("NODE_ID") {
            builder.node_id(node_id.parse().unwrap());
        }
        if let Ok(custodian) = std::env::var("ETH_SENDER") {
            builder.custodian(custodian.parse().unwrap());
        }
        if let (Ok(db_name), Ok(pg_cluster)) = (std::env::var(db_env), std::env::var("PG_CLUSTER"))
        {
            builder.db_connstr(format!("{}/{}", pg_cluster, db_name));
        }
        builder.core_threads(
            std::env::var("CORE_THREADS")
                .map(|s| s.parse().unwrap())
                // FIXME: Why not align with Enclave.xml.template?
                .unwrap_or_else(|_| RUNTIME_MAX_WORKER_THREADS),
        );
        builder.eth_polling_interval_in_secs(
            std::env::var("BLOCK_QUERY_POLLING_INTERVAL_IN_SECS")
                .ok()
                .map(|s| s.parse().unwrap())
                .unwrap_or(5),
        );
        if let Ok(contract_deployment) = std::env::var("CONTRACT_DEPLOYMENT") {
            builder.contract_deployment(contract_deployment);
        }
        if let Ok(contract_server_url) = std::env::var("CONTRACT_SERVER_URL") {
            builder.contract_server_url(contract_server_url);
        }
        if let Ok(bootstrap_nodes) = std::env::var("BOOTSTRAP_NODE_URLS") {
            builder.bootstrap_nodes(BootstrapNodeUrls::new(
                bootstrap_nodes
                    .split(',')
                    .map(|s| s.parse().unwrap())
                    .collect(),
            ));
        }
        // TODO: Make configurable, currently this is the only option.
        builder.want_role(WantRole::RegularNode);

        builder.backoff(BackoffConfig::from_env());

        builder
    }

    #[cfg(feature = "test_harness")]
    pub fn test_defaults() -> Self {
        NodeContextBuilder {
            node_id: None,
            custodian: None,
            db_connstr: None,
            bind_address: Some(LOCALHOST_ADDRESS.to_string()),
            bind_port: Some(DEFAULT_PORT_RANGE_START),
            node_url: None,
            core_threads: Some(RUNTIME_MAX_WORKER_THREADS), // NOTE: Be careful not to starve Tokio with too low a default.
            eth_polling_interval_in_secs: Some(1),
            contract_deployment: None,
            contract_server_url: Some("http://contract-server:4040".to_string()),
            bootstrap_nodes: None,
            want_role: Some(WantRole::RegularNode),
            backoff: Some(BackoffConfig::test_defaults()),
        }
    }
}
