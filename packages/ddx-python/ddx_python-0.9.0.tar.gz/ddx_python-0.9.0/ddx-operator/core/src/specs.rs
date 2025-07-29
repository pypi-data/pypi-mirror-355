//!
//! Dynamic input specifications
//!
//! An exchange is essentially a state machine executing complex business rules for the traded
//! instruments. We strive to limit hardcoded rules to the core logic applicable to all supported
//! instruments. The instruments-specific rules are given via the specification manifests
//! implemented in this module.
//!
//! The smart contract sends the specifications just like deposits and withdrawls. This guarantees
//! their integrity. The exchange engine registers each specification change via a state transition.
//!
//! # Research
//!
//! - [Normalization of Financial Derivatives](http://www.diva-portal.se/smash/get/diva2:890319/FULLTEXT01.pdf):
//!   The emphasis of this paper is on data normalization. This is a key problem of derivatives exchanges
//!   who based their trading rules on external events. It helps us define our `MarketGateway` specs including
//!   its field transformation rules.
//! - [Findel](https://s-tikhomirov.github.io/assets/papers/findel.pdf): Findel is one of the more contemporary
//!   papers that defines DSL for financial derivatives. Our specs has common attributes including the use
//!   of s-expressions. The "Data sources and gateways" is generally aligned with out price feed implementation
//!   including the use of a TLS notary type proof-of-authority.

#[cfg(feature = "index_fund")]
use crate::specs::index_fund::IndexFundPerpetual;
#[cfg(feature = "fixed_expiry_future")]
use crate::specs::quarterly_expiry_future::QuarterlyExpiryFuture;
use crate::{
    constants::{COINGECKO_HOSTNAME, DDX_CONTRACT_ADDRESS},
    types::primitives::UnderlyingSymbol,
};
use chrono::{DateTime, TimeZone, Utc};
use core_common::{Error, Result, ensure, error, types::primitives::UnscaledI128};
#[cfg(feature = "test_harness")]
use core_macros::unscaled;
use core_specs::{
    GetOp, Hostname,
    eval::{Atom, Expr, StructRepr, Transform, eval_from_str},
};
#[cfg(feature = "python")]
use pyo3::{prelude::*, types::PyDict};
#[cfg(feature = "arbitrary")]
use quickcheck::Arbitrary;
use rust_decimal::{Decimal, prelude::ToPrimitive};
use serde::{Deserialize, Serialize};
use std::{
    collections::HashMap,
    convert::{TryFrom, TryInto},
    str::FromStr,
    string::ToString,
};

#[cfg(feature = "index_fund")]
pub mod index_fund;
#[cfg(feature = "fixed_expiry_future")]
pub mod quarterly_expiry_future;
pub mod types;

pub const HTTP_GET_TEMPLATE: &str =
    "GET {} HTTP/1.1\r\nHost: {}\r\nuser-agent: curl/7.77.0\r\nconnection: close\r\n\r\n";

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct QuoteCurrency(String);

impl Default for QuoteCurrency {
    fn default() -> Self {
        Self("USD".to_string())
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for QuoteCurrency {
    fn arbitrary(_g: &mut quickcheck::Gen) -> Self {
        Self("USD".to_string())
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
enum FieldTransform {
    Symbol(Transform),
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for FieldTransform {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Self::Symbol(Arbitrary::arbitrary(g))
    }
}

/// The specification of a price source.
///
/// Declared by `MarketGateway` in the specs.
#[derive(Clone, Debug, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct MarketGateway {
    /// Parsed from `port` (defaults to 80).
    pub port: u16,
    pub hostname: Hostname,
    /// Parsed from `symbols` or by querying the `get-markets` endpoint.
    pub symbols: Vec<UnderlyingSymbol>,
    /// Evaluated from `get-time`.
    time_op: GetOp,
    /// Evaluated from `get-spot-price`.
    spot_price_op: GetOp,
    /// Evaluated from `tr-*`.
    transforms: Vec<FieldTransform>,
    /// Parsed from `quote` (defaults to USD).
    pub quote: QuoteCurrency,
}

impl MarketGateway {
    fn new(
        port: u16,
        hostname: Hostname,
        symbols: Vec<UnderlyingSymbol>,
        time_op: GetOp,
        spot_price_op: GetOp,
        transforms: Vec<FieldTransform>,
        quote: QuoteCurrency,
    ) -> Self {
        MarketGateway {
            port,
            hostname,
            symbols,
            time_op,
            spot_price_op,
            transforms,
            quote,
        }
    }

    fn find_underlying_symbol(&self, source_symbol: &str) -> Result<UnderlyingSymbol> {
        self.source_symbols().and_then(|s| {
            s.iter()
                .find_map(|(k, v)| {
                    if v.as_str() == source_symbol
                        || (v.as_str() == DDX_CONTRACT_ADDRESS && source_symbol == "DDX")
                    {
                        Some(*k)
                    } else {
                        None
                    }
                })
                .ok_or_else(|| error!("Expected one of {:?}, got {}", s.values(), source_symbol))
        })
    }

    fn source_symbol(&self, symbol: &UnderlyingSymbol) -> Result<String> {
        ensure!(
            self.symbols.contains(symbol),
            "Product {} not supported",
            symbol
        );
        // TODO: Is it okay to handle the coingecko case manually?
        if self.hostname == COINGECKO_HOSTNAME {
            return Ok(DDX_CONTRACT_ADDRESS.to_string());
        }
        // NOTE: Assuming running these regexes is cheap enough not to bother with caching.
        // This only takes the first transformation
        if let Some(tr) = self.transforms.first() {
            let FieldTransform::Symbol(ref tr) = tr;
            return tr.apply(symbol.to_string());
        }
        // Fallback
        Ok(symbol.to_string())
    }

    fn source_symbols(&self) -> Result<HashMap<UnderlyingSymbol, String>> {
        self.symbols
            .iter()
            .map(|s| self.source_symbol(s).map(|r| (*s, r)))
            .collect()
    }

    #[tracing::instrument(level = "debug", skip(self))]
    pub fn time_query(&self) -> Result<String> {
        self.time_op
            .query
            .literal()
            .ok_or_else(|| error!("Expected a literal query"))
    }

    #[tracing::instrument(level = "debug", skip(self))]
    pub fn read_time(&self, response: String) -> Result<DateTime<Utc>> {
        let content = self.time_op.reader.apply(response)?;
        let ts: i64 = serde_json::from_str(&content)?;
        let dt = if ts.ilog10() <= 12 {
            chrono::Utc.timestamp_opt(ts, 0).single()
        } else {
            chrono::Utc.timestamp_millis_opt(ts).single()
        }
        .ok_or_else(|| error!("Invalid timestamp"))?;
        Ok(dt)
    }

    #[tracing::instrument(level = "debug", skip(self), fields(source_symbol, transform))]
    pub fn spot_price_query(&self, symbol: &UnderlyingSymbol) -> Result<String> {
        let source_symbol = self.source_symbol(symbol)?;
        tracing::Span::current().record("source_symbol", &source_symbol);
        let transform = self
            .spot_price_op
            .query
            .transform()
            .ok_or_else(|| error!("Expected a transform"))?;
        tracing::Span::current().record("transform", format!("{:?}", transform));
        transform.apply(source_symbol)
    }

    #[tracing::instrument(level = "debug", skip(self))]
    pub fn read_spot_price(&self, response: String) -> Result<(UnderlyingSymbol, Decimal)> {
        let content = self.spot_price_op.reader.apply(response)?;
        // TODO: Is there another way to handle coingecko besides manually?
        let (source_symbol, price): (String, Decimal) = if self.hostname == COINGECKO_HOSTNAME {
            let price: Decimal = serde_json::from_str(&content)?;
            ("DDX".to_string(), price)
        } else {
            serde_json::from_str(&content)?
        };
        tracing::debug!(
            "Found source symbol {} - Markets {:?}",
            source_symbol,
            self.source_symbols()
        );
        let symbol = self.find_underlying_symbol(&source_symbol)?;
        Ok((symbol, price))
    }
}

// Shorthand parser that panics on error.
// Use concrete types for the argument to avoid ambiguity and compiler errors.
impl From<&str> for MarketGateway {
    fn from(expr: &str) -> Self {
        expr.parse().expect("Invalid market gateway specs")
    }
}

impl From<String> for MarketGateway {
    fn from(expr: String) -> Self {
        expr.parse().expect("Invalid market gateway specs")
    }
}

impl FromStr for MarketGateway {
    type Err = Error;

    fn from_str(expr: &str) -> Result<Self, Self::Err> {
        if let Expr::Constant(Atom::Struct(repr)) = eval_from_str(expr)? {
            repr.try_into()
        } else {
            Err(error!("Not a market gateway specs expression"))
        }
    }
}

impl TryFrom<StructRepr> for MarketGateway {
    type Error = Error;

    fn try_from(mut repr: StructRepr) -> Result<Self, Self::Error> {
        repr.ensure_match("MarketGateway", 4)?;
        let mut get_ops = repr
            .take_items("get-")
            .into_iter()
            .map(|(n, a)| GetOp::try_from(a.try_struct()?).map(|o| (n, o)))
            .collect::<Result<HashMap<_, _>>>()?;
        ensure!(!get_ops.is_empty(), "Expected at least one endpoint");
        let transforms = repr
            .take_items("tr-")
            .into_iter()
            .map(|(k, a)| match k.as_str() {
                "tr-symbol" => Ok(FieldTransform::Symbol(a.try_into()?)),
                _ => Err(error!("Unexpected transform kind {}", k)),
            })
            .collect::<Result<Vec<_>>>()?;
        let symbols = repr
            .try_take("symbols")?
            .try_list()?
            .into_iter()
            .map(|a| String::try_from(a).and_then(|s| UnderlyingSymbol::from_str(&s)))
            .collect::<Result<Vec<_>>>()?;
        let port = if let Ok(a) = repr.try_take("port") {
            Decimal::try_from(a)
                .and_then(|d| d.to_u16().ok_or_else(|| error!("Invalid port value")))?
        } else {
            80_u16
        };
        let specs = MarketGateway::new(
            port,
            repr.try_take("hostname")?.try_into()?,
            symbols,
            get_ops
                .remove("get-time")
                .ok_or_else(|| error!("Time op not found"))?,
            get_ops
                .remove("get-spot-price")
                .ok_or_else(|| error!("Spot price op not found"))?,
            transforms,
            Default::default(),
        );
        Ok(specs)
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for MarketGateway {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Self {
            hostname: "api.binance.com".to_string(),
            port: 80,
            symbols: Arbitrary::arbitrary(g),
            time_op: Arbitrary::arbitrary(g),
            spot_price_op: Arbitrary::arbitrary(g),
            transforms: Arbitrary::arbitrary(g),
            quote: Arbitrary::arbitrary(g),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(tag = "kind")]
#[non_exhaustive]
pub enum ProductSpecs {
    SingleNamePerpetual(SingleNamePerpetual),
    #[cfg(feature = "index_fund")]
    IndexFundPerpetual(IndexFundPerpetual),
    #[cfg(feature = "fixed_expiry_future")]
    QuarterlyExpiryFuture(QuarterlyExpiryFuture),
}

impl ProductSpecs {
    pub fn underlying_symbols(&self) -> Vec<UnderlyingSymbol> {
        match self {
            Self::SingleNamePerpetual(p) => vec![p.underlying],
            #[cfg(feature = "index_fund")]
            Self::IndexFundPerpetual(p) => p.allocation.keys().cloned().collect(),
            #[cfg(feature = "fixed_expiry_future")]
            Self::QuarterlyExpiryFuture(p) => vec![p.underlying],
        }
    }

    pub fn tick_size(&self) -> UnscaledI128 {
        match self {
            Self::SingleNamePerpetual(p) => p.tick_size,
            #[cfg(feature = "index_fund")]
            Self::IndexFundPerpetual(p) => p.tick_size,
            #[cfg(feature = "fixed_expiry_future")]
            Self::QuarterlyExpiryFuture(p) => p.tick_size,
        }
    }

    pub fn max_order_notional(&self) -> UnscaledI128 {
        match self {
            Self::SingleNamePerpetual(p) => p.max_order_notional,
            #[cfg(feature = "index_fund")]
            Self::IndexFundPerpetual(p) => p.max_order_notional,
            #[cfg(feature = "fixed_expiry_future")]
            Self::QuarterlyExpiryFuture(p) => p.max_order_notional,
        }
    }

    pub fn max_taker_price_deviation(&self) -> UnscaledI128 {
        match self {
            Self::SingleNamePerpetual(p) => p.max_taker_price_deviation,
            #[cfg(feature = "index_fund")]
            Self::IndexFundPerpetual(p) => p.max_taker_price_deviation,
            #[cfg(feature = "fixed_expiry_future")]
            Self::QuarterlyExpiryFuture(p) => p.max_taker_price_deviation,
        }
    }

    pub fn min_order_size(&self) -> UnscaledI128 {
        match self {
            Self::SingleNamePerpetual(p) => p.min_order_size,
            #[cfg(feature = "index_fund")]
            Self::IndexFundPerpetual(p) => p.min_order_size,
            #[cfg(feature = "fixed_expiry_future")]
            Self::QuarterlyExpiryFuture(p) => p.min_order_size,
        }
    }
}

#[cfg(feature = "python")]
fn extract_field<'a, T: FromPyObject<'a>>(kwds: &'a PyDict, field_name: &str) -> PyResult<T> {
    kwds.get_item(field_name)?
        .ok_or_else(|| {
            core_common::types::exported::python::CoreCommonError::new_err(format!(
                "Expected `{}` field",
                field_name
            ))
        })?
        .extract::<T>()
        .map_err(|e| {
            core_common::types::exported::python::CoreCommonError::new_err(format!(
                "Unexpected type for `{}` field: {}",
                field_name, e
            ))
        })
}

/// A set of specification about each market (aka derivative contracts)
#[cfg_attr(feature = "python", pyclass(frozen, get_all))]
#[derive(Clone, Debug, Default, PartialEq, Deserialize, Serialize, Eq)]
#[serde(rename_all = "camelCase")]
pub struct SingleNamePerpetual {
    pub underlying: UnderlyingSymbol,
    pub tick_size: UnscaledI128,
    pub max_order_notional: UnscaledI128,
    pub max_taker_price_deviation: UnscaledI128,
    pub min_order_size: UnscaledI128,
}

#[cfg(feature = "python")]
#[pymethods]
impl SingleNamePerpetual {
    #[new]
    #[pyo3(signature = (**kwds))]
    pub(crate) fn new_py(kwds: Option<&PyDict>) -> PyResult<Self> {
        let kwds = kwds.ok_or_else(|| {
            core_common::types::exported::python::CoreCommonError::new_err(
                "Expected keyword dictionary containing specs".to_string(),
            )
        })?;
        Ok(Self {
            underlying: extract_field(kwds, "underlying")?,
            tick_size: extract_field(kwds, "tick_size")?,
            max_order_notional: extract_field(kwds, "max_order_notional")?,
            max_taker_price_deviation: extract_field(kwds, "max_taker_price_deviation")?,
            min_order_size: extract_field(kwds, "min_order_size")?,
        })
    }
}

// Shorthand parser that panics on error.
// Use concrete types for the argument to avoid ambiguity and compiler errors.
impl From<&str> for SingleNamePerpetual {
    fn from(expr: &str) -> Self {
        expr.parse().expect("Invalid market specs")
    }
}

impl From<String> for SingleNamePerpetual {
    fn from(expr: String) -> Self {
        expr.parse().expect("Invalid market specs")
    }
}

impl FromStr for SingleNamePerpetual {
    type Err = Error;

    fn from_str(expr: &str) -> Result<Self, Self::Err> {
        if let Expr::Constant(Atom::Struct(repr)) = eval_from_str(expr)? {
            repr.try_into()
        } else {
            Err(Error::Parse(expr.to_string()))
        }
    }
}

impl TryFrom<StructRepr> for SingleNamePerpetual {
    type Error = Error;

    fn try_from(mut repr: StructRepr) -> Result<Self, Self::Error> {
        repr.ensure_match("SingleNamePerpetual", 5)?;
        Ok(SingleNamePerpetual {
            underlying: repr.try_take("underlying")?.try_into()?,
            tick_size: repr.try_take("tick-size")?.try_into()?,
            max_order_notional: repr.try_take("max-order-notional")?.try_into()?,
            max_taker_price_deviation: repr.try_take("max-taker-price-deviation")?.try_into()?,
            min_order_size: repr.try_take("min-order-size")?.try_into()?,
        })
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for SingleNamePerpetual {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Self {
            underlying: Arbitrary::arbitrary(g),
            tick_size: Arbitrary::arbitrary(g),
            max_order_notional: Arbitrary::arbitrary(g),
            max_taker_price_deviation: Arbitrary::arbitrary(g),
            min_order_size: Arbitrary::arbitrary(g),
        }
    }
}

#[cfg(feature = "test_harness")]
impl SingleNamePerpetual {
    pub fn local_defaults(underlying: UnderlyingSymbol) -> Self {
        Self {
            underlying,
            tick_size: unscaled!(1),
            max_order_notional: unscaled!(1_000_000),
            max_taker_price_deviation: unscaled!(0.02),
            min_order_size: unscaled!(0.000_01),
        }
    }

    pub fn btcp_defaults() -> Self {
        Self {
            underlying: "BTC".into(),
            tick_size: unscaled!(1),
            max_order_notional: unscaled!(1_000_000),
            max_taker_price_deviation: unscaled!(0.02),
            min_order_size: unscaled!(0.000_01),
        }
    }

    pub fn dogep_defaults() -> Self {
        Self {
            underlying: "DOGE".into(),
            tick_size: unscaled!(1),
            max_order_notional: unscaled!(1_000_000),
            max_taker_price_deviation: unscaled!(0.02),
            min_order_size: unscaled!(0.000_01),
        }
    }

    pub fn ethp_defaults() -> Self {
        Self {
            underlying: "ETH".into(),
            tick_size: unscaled!(0.1),
            max_order_notional: unscaled!(1_000_000),
            max_taker_price_deviation: unscaled!(0.02),
            min_order_size: unscaled!(0.000_1),
        }
    }

    pub fn max_precision_defaults(underlying: UnderlyingSymbol) -> Self {
        Self {
            underlying,
            tick_size: unscaled!(0.1),
            max_order_notional: unscaled!(1_000_000),
            max_taker_price_deviation: unscaled!(0.02),
            min_order_size: unscaled!(0.000_001),
        }
    }
}

#[cfg(test)]
mod test {
    use super::*;
    use core_specs::{
        StrValue,
        eval::{Atom, Expr, Transform, eval_from_str},
    };

    #[test]
    fn test_serialize_market_gateway() {
        let want = MarketGateway {
            hostname: "api.binance.com".to_string(),
            port: 80,
            symbols: vec!["ETH".into(), "BTC".into()],
            time_op: GetOp {
                query: StrValue::Literal("/api/v3/time".to_string()),
                reader: Transform::Jq("serverTime".to_string()),
            },
            spot_price_op: GetOp {
                query: StrValue::Transform(Transform::Format(
                    "/api/v3/ticker/price?symbol={}".to_string(),
                )),
                reader: Transform::Jq("[symbol,price]".to_string()),
            },
            transforms: vec![],
            quote: Default::default(),
        };
        let serialized = cbor4ii::serde::to_vec(vec![], &want).unwrap();
        let deserialized: MarketGateway = cbor4ii::serde::from_slice(&serialized).unwrap();
        assert_eq!(want, deserialized);
    }

    #[test]
    fn test_parse_spot_price() {
        let want = GetOp {
            query: StrValue::Transform(Transform::Format(
                "/api/v3/ticker/price?symbol={}".to_string(),
            )),
            reader: Transform::Jq("[symbol,price]".to_string()),
        };

        let op = r#"
(Get
    :query (format "/api/v3/ticker/price?symbol={}")
    :reader (jq "[symbol,price]")
)"#;
        let res = eval_from_str(op).unwrap();
        tracing::debug!(?op, ?res);
        if let Expr::Constant(Atom::Struct(repr)) = res {
            assert_eq!(want, repr.try_into().unwrap());
        } else {
            panic!("Unexpected parser expression");
        }
    }

    #[test]
    fn test_parse_market_data_specs() {
        let want = MarketGateway {
            hostname: "api.binance.com".to_string(),
            time_op: GetOp {
                query: StrValue::Literal("/api/v3/time".to_string()),
                reader: Transform::Jq("serverTime".to_string()),
            },
            spot_price_op: GetOp {
                query: StrValue::Transform(Transform::Format(
                    "/api/v3/ticker/price?symbol={}".to_string(),
                )),
                reader: Transform::Jq("[symbol,price]".to_string()),
            },
            symbols: vec!["ETH".into(), "BTC".into()],
            transforms: vec![FieldTransform::Symbol(Transform::Sed(
                "s/XBT/BTC/; s/(?P<base>[A-Z]+)/${base}BUSD/;".to_string(),
            ))],
            quote: Default::default(),
            port: 80,
        };
        // See same specs without the `op` qualifier.
        // `tr-symbol` has to be qualified because its type is not specialized enough.
        let expr = r#"
(MarketGateway :hostname "api.binance.com"
    :symbols '("ETH" "BTC")
    :get-time (Get
        :query "/api/v3/time"
        :reader (jq "serverTime")
    )
    :get-spot-price (Get
        :query (format "/api/v3/ticker/price?symbol={}")
        :reader (jq "[symbol,price]")
    )
    :tr-symbol (sed "s/XBT/BTC/; s/(?P<base>[A-Z]+)/${base}BUSD/;")
)"#;
        let specs = expr.parse::<MarketGateway>().unwrap();
        assert_eq!(want, specs);
        tracing::debug!(" => {:?}", specs);
        tracing::debug!(
            "Spot price callers\n  - ETH: {:?}\n  - BTC: {:?}",
            specs.spot_price_query(&"ETH".into()),
            specs.spot_price_query(&"BTC".into())
        );
    }

    #[test]
    fn test_market_specs() {
        let want = SingleNamePerpetual {
            underlying: "BTC".into(),
            tick_size: unscaled!(1),
            max_order_notional: unscaled!(1000000),
            max_taker_price_deviation: unscaled!(0.02),
            min_order_size: unscaled!(0.00001),
        };
        let expr = r#"
(SingleNamePerpetual :name "BTCP"
    :underlying "BTC"
    :tick-size 1
    :max-order-notional 1000000
    :max-taker-price-deviation 0.02
    :min-order-size 0.00001
)"#;
        let specs = expr.parse::<SingleNamePerpetual>().unwrap();
        assert_eq!(want, specs);

        let want = SingleNamePerpetual {
            underlying: "ETH".into(),
            tick_size: unscaled!(0.1),
            max_order_notional: unscaled!(1000000),
            max_taker_price_deviation: unscaled!(0.02),
            min_order_size: unscaled!(0.0001),
        };
        let expr = r#"
(SingleNamePerpetual :name "ETHP"
    :underlying "ETH"
    :tick-size 0.1
    :max-order-notional 1000000
    :max-taker-price-deviation 0.02
    :min-order-size 0.0001
)"#;
        let specs = expr.parse::<SingleNamePerpetual>().unwrap();
        assert_eq!(want, specs);
    }
}
