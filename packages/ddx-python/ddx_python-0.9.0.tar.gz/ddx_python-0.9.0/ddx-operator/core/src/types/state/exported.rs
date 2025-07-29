// TODO: proceduralize these macros for cleaner code
use super::*;

pub mod python {
    use super::{
        Balance, BookOrder, EpochMetadata, ITEM_BOOK_ORDER, ITEM_EMPTY, ITEM_EPOCH_METADATA,
        ITEM_INSURANCE_FUND, ITEM_INSURANCE_FUND_CONTRIBUTION, ITEM_POSITION, ITEM_PRICE,
        ITEM_SIGNER, ITEM_SPECS, ITEM_STATS, ITEM_STRATEGY, ITEM_TRADABLE_PRODUCT, ITEM_TRADER,
        InsuranceFundContribution, Item as RustItem, Position, Price, ReleaseHash, SpecsExpr,
        Stats, Strategy, TradableProduct,
        TradableProductParameters as RustTradableProductParameters, Trader, VoidableItem,
    };
    #[cfg(feature = "index_fund")]
    use crate::specs::index_fund::IndexFundPerpetual;
    #[cfg(feature = "fixed_expiry_future")]
    use crate::specs::quarterly_expiry_future::{Quarter, QuarterlyExpiryFuture};
    #[cfg(feature = "insurance_fund_client_req")]
    use crate::types::request::InsuranceFundWithdrawIntent;
    use crate::{
        specs::{
            ProductSpecs as RustProductSpecs, SingleNamePerpetual,
            types::{SpecsKey, SpecsKind},
        },
        tree::{
            shared_smt::{SharedSparseMerkleTree, exported::python::H256, from_genesis},
            shared_store::ConcurrentStore,
        },
        types::{
            accounting::{MarkPriceMetadata as RustMarkPriceMetadata, PriceMetadata, TradeSide},
            identifiers::{
                BookOrderKey, EpochMetadataKey, InsuranceFundContributorAddress, InsuranceFundKey,
                PositionKey, PriceKey, SignerAddress, StatsKey, StrategyIdHash, StrategyKey,
                VerifiedStateKey,
            },
            primitives::{
                IndexPriceHash, OrderHash, Product, ProductSymbol as RustProductSymbol,
                UnderlyingSymbol,
            },
            request::{
                AdvanceEpoch, AdvanceSettlementEpoch, Block, CancelAllIntent, CancelOrderIntent,
                ClientRequest, Cmd, CmdTimeValue, IndexPrice, MatchableIntent, MintPriceCheckpoint,
                ModifyOrderIntent, OrderIntent, OrderType as RustOrderType, ProfileUpdate, Request,
                SettlementAction as RustSettlementAction, UpdateProductListings, WithdrawDDXIntent,
                WithdrawIntent,
            },
            state::TradableProductKey,
            transaction::{InsuranceFundUpdateKind, StrategyUpdateKind, TraderUpdateKind},
        },
    };
    use alloy_dyn_abi::{DynSolType, DynSolValue};
    #[cfg(feature = "fixed_expiry_future")]
    use chrono::prelude::*;
    use core_common::{
        Address,
        global::ApplicationContext,
        types::{
            accounting::StrategyId,
            exported::python::CoreCommonError,
            primitives::{
                Hash, TokenSymbol, TraderAddress, UnscaledI128, exported::python::Decimal,
            },
        },
        util::tokenize::Tokenizable,
    };
    use core_crypto::eip712::{HashEIP712, SignedEIP712};
    use lazy_static::lazy_static;
    use pyo3::{
        exceptions::PyValueError,
        prelude::*,
        types::{PyDict, PyType},
    };
    use pythonize;
    use sparse_merkle_tree::{
        CompiledMerkleProof, H256 as RustH256, traits::Value, tree::LeafNode,
    };
    use std::{borrow::Cow, collections::HashMap, fmt, str::FromStr};

    #[pyfunction]
    pub fn get_operator_context() -> ApplicationContext {
        core_common::global::app_context().clone()
    }

    #[pyfunction]
    pub fn reinit_operator_context() {
        core_common::global::reinit_app_context_from_env()
    }

    // GENERAL TYPES------------------------------------------------------------

    #[pyclass(frozen)]
    #[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, std::hash::Hash, Debug)]
    pub struct ProductSymbol {
        inner: RustProductSymbol,
    }

    #[pymethods]
    impl ProductSymbol {
        #[new]
        fn new(symbol: &str) -> PyResult<Self> {
            Ok(Self {
                inner: RustProductSymbol::from_str(symbol)?,
            })
        }

        fn __deepcopy__(&self, _memo: &PyDict) -> Self {
            *self
        }

        fn __repr__(&self) -> String {
            format!("{:?}", self)
        }

        fn __str__(&self) -> String {
            self.inner.to_string()
        }

        fn __len__(&self) -> usize {
            self.inner.0.len()
        }

        fn __eq__(&self, other: &Self) -> bool {
            self.inner == other.inner
        }

        fn __lt__(&self, other: &Self) -> bool {
            self.inner < other.inner
        }

        fn __hash__(&self) -> u64 {
            use std::hash::{Hash, Hasher};
            let mut hasher = std::collections::hash_map::DefaultHasher::new();
            self.inner.hash(&mut hasher);
            hasher.finish()
        }

        fn is_perpetual(&self) -> bool {
            matches!(self.inner.product(), Product::Perpetual)
        }

        #[cfg(feature = "fixed_expiry_future")]
        fn is_future(&self) -> bool {
            matches!(self.inner.product(), Product::QuarterlyExpiryFuture { .. })
        }

        #[cfg(feature = "fixed_expiry_future")]
        fn futures_quarter(&self) -> Option<Quarter> {
            match self.inner.product() {
                Product::QuarterlyExpiryFuture { month_code } => Some(month_code.into()),
                _ => None,
            }
        }

        fn price_metadata(&self) -> PriceMetadata {
            match self.inner.product() {
                // TODO: distinguish between single and index perps
                Product::Perpetual => PriceMetadata::SingleNamePerpetual,
                #[cfg(feature = "fixed_expiry_future")]
                Product::QuarterlyExpiryFuture { .. } => PriceMetadata::QuarterlyExpiryFuture,
            }
        }
    }

    impl fmt::Display for ProductSymbol {
        fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
            write!(f, "{}", self.inner)
        }
    }

    impl From<RustProductSymbol> for ProductSymbol {
        fn from(symbol: RustProductSymbol) -> Self {
            Self { inner: symbol }
        }
    }

    impl From<ProductSymbol> for RustProductSymbol {
        fn from(symbol: ProductSymbol) -> Self {
            symbol.inner
        }
    }

    #[pyclass(frozen)]
    #[derive(Clone, Copy, PartialEq, Eq, Debug)]
    pub struct OrderType {
        inner: RustOrderType,
    }

    #[allow(non_upper_case_globals)]
    #[pymethods]
    impl OrderType {
        #[classattr]
        const Limit: Self = Self {
            inner: RustOrderType::Limit { post_only: false },
        };

        #[classattr]
        const Market: Self = Self {
            inner: RustOrderType::Market,
        };

        #[classattr]
        const StopLimit: Self = Self {
            inner: RustOrderType::StopLimit,
        };

        #[classattr]
        const PostOnlyLimit: Self = Self {
            inner: RustOrderType::Limit { post_only: true },
        };

        fn __repr__(&self) -> String {
            format!("{:?}", self)
        }

        fn __eq__(&self, other: &Self) -> bool {
            self.inner == other.inner
        }
    }

    impl From<RustOrderType> for OrderType {
        fn from(order_type: RustOrderType) -> Self {
            Self { inner: order_type }
        }
    }

    impl From<OrderType> for RustOrderType {
        fn from(order_type: OrderType) -> Self {
            order_type.inner
        }
    }

    #[pymethods]
    impl TradeSide {
        #[pyo3(name = "trading_fee")]
        fn trading_fee_py(&self, amount: Decimal, price: Decimal) -> Decimal {
            self.trading_fee(amount.into(), price.into()).into()
        }
    }

    #[pymethods]
    impl SpecsKind {
        #[new]
        fn new(kind: &str) -> PyResult<Self> {
            Self::from_str(kind).map_err(|e| CoreCommonError::new_err(e.to_string()))
        }
    }

    #[pymethods]
    impl InsuranceFundUpdateKind {
        #[new]
        fn new(name: &str) -> PyResult<Self> {
            Self::from_str(name).map_err(|e| CoreCommonError::new_err(e.to_string()))
        }
    }

    #[pymethods]
    impl TraderUpdateKind {
        #[new]
        fn new(name: &str) -> PyResult<Self> {
            Self::from_str(name).map_err(|e| CoreCommonError::new_err(e.to_string()))
        }
    }

    #[pymethods]
    impl StrategyUpdateKind {
        #[new]
        fn new(name: &str) -> PyResult<Self> {
            Self::from_str(name).map_err(|e| CoreCommonError::new_err(e.to_string()))
        }
    }

    #[pyclass(frozen)]
    #[derive(Clone, PartialEq, Eq, Debug)]
    pub struct ProductSpecs {
        inner: RustProductSpecs,
    }

    #[pymethods]
    impl ProductSpecs {
        #[allow(non_snake_case)]
        #[classmethod]
        fn SingleNamePerpetual(_cls: &PyType, single_name_perpetual: SingleNamePerpetual) -> Self {
            Self {
                inner: RustProductSpecs::SingleNamePerpetual(single_name_perpetual),
            }
        }

        #[allow(non_snake_case)]
        #[cfg(feature = "index_fund")]
        #[classmethod]
        fn IndexFundPerpetual(_cls: &PyType, index_fund_perpetual: IndexFundPerpetual) -> Self {
            Self {
                inner: RustProductSpecs::IndexFundPerpetual(index_fund_perpetual),
            }
        }

        #[allow(non_snake_case)]
        #[cfg(feature = "fixed_expiry_future")]
        #[classmethod]
        fn QuarterlyExpiryFuture(
            _cls: &PyType,
            quarterly_expiry_future: QuarterlyExpiryFuture,
        ) -> Self {
            Self {
                inner: RustProductSpecs::QuarterlyExpiryFuture(quarterly_expiry_future),
            }
        }

        fn __repr__(&self) -> String {
            format!("{:?}", self)
        }

        fn __eq__(&self, other: &Self) -> bool {
            self.inner == other.inner
        }

        fn underlying_symbols(&self) -> Vec<UnderlyingSymbol> {
            self.inner.underlying_symbols()
        }

        #[getter(tick_size)]
        fn tick_size(&self) -> UnscaledI128 {
            self.inner.tick_size()
        }

        #[getter(max_order_notional)]
        fn max_order_notional(&self) -> UnscaledI128 {
            self.inner.max_order_notional()
        }

        #[getter(max_taker_price_deviation)]
        fn max_taker_price_deviation(&self) -> UnscaledI128 {
            self.inner.max_taker_price_deviation()
        }

        #[getter(min_order_size)]
        fn min_order_size(&self) -> UnscaledI128 {
            self.inner.min_order_size()
        }
    }

    impl From<RustProductSpecs> for ProductSpecs {
        fn from(product_specs: RustProductSpecs) -> Self {
            Self {
                inner: product_specs,
            }
        }
    }

    impl From<ProductSpecs> for RustProductSpecs {
        fn from(product_specs: ProductSpecs) -> Self {
            product_specs.inner
        }
    }

    #[pyclass(frozen)]
    #[derive(Clone, Copy, PartialEq, Eq, Debug)]
    pub struct MarkPriceMetadata {
        inner: RustMarkPriceMetadata,
    }

    #[allow(non_snake_case)]
    #[pymethods]
    impl MarkPriceMetadata {
        #[classmethod]
        fn Ema(_cls: &PyType, ema: UnscaledI128) -> Self {
            Self {
                inner: RustMarkPriceMetadata::Ema(ema),
            }
        }

        #[cfg(feature = "fixed_expiry_future")]
        #[classmethod]
        fn Average(_cls: &PyType, accum: UnscaledI128, count: u64) -> Self {
            Self {
                inner: RustMarkPriceMetadata::Average { accum, count },
            }
        }

        fn ema(&self) -> Option<UnscaledI128> {
            match self.inner {
                RustMarkPriceMetadata::Ema(ema) => Some(ema),
                _ => None,
            }
        }

        #[cfg(feature = "fixed_expiry_future")]
        fn average(&self) -> Option<(UnscaledI128, u64)> {
            match self.inner {
                RustMarkPriceMetadata::Average { accum, count } => Some((accum, count)),
                _ => None,
            }
        }

        #[classmethod]
        fn from_dict(_cls: &PyType, ob: &PyAny) -> PyResult<Self> {
            Ok(Self {
                inner: pythonize::depythonize(ob)
                    .map_err(|e| CoreCommonError::new_err(e.to_string()))?,
            })
        }

        fn __repr__(&self) -> String {
            format!("{:?}", self)
        }

        fn __eq__(&self, other: &Self) -> bool {
            self.inner == other.inner
        }

        fn __deepcopy__(&self, _memo: &PyDict) -> Self {
            *self
        }
    }

    impl From<RustMarkPriceMetadata> for MarkPriceMetadata {
        fn from(metadata: RustMarkPriceMetadata) -> Self {
            Self { inner: metadata }
        }
    }

    impl From<MarkPriceMetadata> for RustMarkPriceMetadata {
        fn from(metadata: MarkPriceMetadata) -> Self {
            metadata.inner
        }
    }

    #[pyclass(frozen)]
    #[derive(Clone, PartialEq, Eq, Debug, std::hash::Hash, PartialOrd, Ord)]
    pub struct TradableProductParameters {
        inner: RustTradableProductParameters,
    }

    #[allow(non_upper_case_globals)]
    #[pymethods]
    impl TradableProductParameters {
        #[allow(non_snake_case)]
        #[cfg(feature = "fixed_expiry_future")]
        #[classmethod]
        fn QuarterlyExpiryFuture(_cls: &PyType, quarter: Quarter) -> Self {
            Self {
                inner: RustTradableProductParameters::QuarterlyExpiryFuture(quarter),
            }
        }

        #[cfg(feature = "fixed_expiry_future")]
        fn futures_quarter(&self) -> Option<Quarter> {
            #[allow(unreachable_patterns)]
            match self.inner {
                RustTradableProductParameters::QuarterlyExpiryFuture(quarter) => Some(quarter),
                _ => None,
            }
        }

        #[classmethod]
        fn from_dict(_cls: &PyType, ob: &PyAny) -> PyResult<Self> {
            Ok(Self {
                inner: pythonize::depythonize(ob)
                    .map_err(|e| CoreCommonError::new_err(e.to_string()))?,
            })
        }

        fn __repr__(&self) -> String {
            format!("{:?}", self)
        }

        fn __eq__(&self, other: &Self) -> bool {
            self.inner == other.inner
        }

        fn __hash__(&self) -> u64 {
            use std::hash::{Hash, Hasher};
            let mut hasher = std::collections::hash_map::DefaultHasher::new();
            self.inner.hash(&mut hasher);
            hasher.finish()
        }

        fn __lt__(&self, other: &Self) -> bool {
            self < other
        }
    }

    impl From<RustTradableProductParameters> for TradableProductParameters {
        fn from(params: RustTradableProductParameters) -> Self {
            Self { inner: params }
        }
    }

    impl From<TradableProductParameters> for RustTradableProductParameters {
        fn from(params: TradableProductParameters) -> Self {
            params.inner
        }
    }

    #[pyclass(frozen)]
    #[derive(Clone, PartialEq, Eq, std::hash::Hash, Debug)]
    pub struct SettlementAction {
        inner: RustSettlementAction,
    }

    #[allow(non_upper_case_globals)]
    #[pymethods]
    impl SettlementAction {
        #[classattr]
        const TradeMining: RustSettlementAction = RustSettlementAction::TradeMining;

        #[classattr]
        const PnlRealization: RustSettlementAction = RustSettlementAction::PnlRealization;

        #[classattr]
        const FundingDistribution: RustSettlementAction = RustSettlementAction::FundingDistribution;

        #[allow(non_snake_case)]
        #[cfg(feature = "fixed_expiry_future")]
        #[classmethod]
        fn FuturesExpiry(_cls: &PyType, quarter: Quarter) -> Self {
            Self {
                inner: RustSettlementAction::FuturesExpiry { quarter },
            }
        }

        #[cfg(feature = "fixed_expiry_future")]
        fn futures_quarter(&self) -> Option<Quarter> {
            match self.inner {
                RustSettlementAction::FuturesExpiry { quarter } => Some(quarter),
                _ => None,
            }
        }

        fn __repr__(&self) -> String {
            format!("{:?}", self)
        }

        fn __eq__(&self, other: &Self) -> bool {
            self.inner == other.inner
        }

        fn __hash__(&self) -> u64 {
            use std::hash::{Hash, Hasher};
            let mut hasher = std::collections::hash_map::DefaultHasher::new();
            self.inner.hash(&mut hasher);
            hasher.finish()
        }
    }

    impl From<RustSettlementAction> for SettlementAction {
        fn from(action: RustSettlementAction) -> Self {
            Self { inner: action }
        }
    }

    impl From<SettlementAction> for RustSettlementAction {
        fn from(action: SettlementAction) -> Self {
            action.inner
        }
    }

    #[cfg(feature = "fixed_expiry_future")]
    #[pymethods]
    impl Quarter {
        fn __repr__(&self) -> String {
            format!("{:?}", self)
        }

        fn __str__(&self) -> String {
            self.to_string()
        }

        fn __eq__(&self, other: &Self) -> bool {
            self == other
        }

        fn __lt__(&self, other: &Self) -> bool {
            self < other
        }

        fn __hash__(&self) -> u64 {
            use std::hash::{Hash, Hasher};
            let mut hasher = std::collections::hash_map::DefaultHasher::new();
            self.hash(&mut hasher);
            hasher.finish()
        }

        #[new]
        fn new(name: &str) -> PyResult<Self> {
            Self::from_str(name).map_err(|e| CoreCommonError::new_err(e.to_string()))
        }

        #[classmethod]
        #[pyo3(name = "find_quarter")]
        fn find_quarter_py(_cls: &PyType, datetime: DateTime<Utc>) -> Self {
            Self::find_quarter(datetime)
        }

        #[pyo3(name = "expiry_date_after")]
        fn expiry_date_after_py(&self, datetime: DateTime<Utc>) -> DateTime<Utc> {
            self.expiry_date_after(datetime)
        }

        #[classmethod]
        #[pyo3(name = "upcoming_expiry_date")]
        fn upcoming_expiry_date_py(_cls: &PyType, current_time: DateTime<Utc>) -> DateTime<Utc> {
            Self::upcoming_expiry_date(current_time)
        }

        #[pyo3(name = "next")]
        fn next_py(&self) -> Self {
            self.next()
        }
    }

    // REQUESTS---------------------------------------------------------------------

    macro_rules! delegate_request_methods {
        ($( ($name:ty, $variant:ident), )*) => {
            $(
                #[pymethods]
                impl $name {
                    fn __repr__(&self) -> String {
                        format!("{:?}", self)
                    }

                    #[getter(json)]
                    fn request_repr(&self, py: Python) -> PyObject {
                        pythonize::pythonize(py, &Request::from(Cmd::$variant(self.clone().into()))).unwrap()
                    }
                }
            )*
        };
    }

    delegate_request_methods!(
        (CmdTimeValue, AdvanceTime),
        (AdvanceEpoch, AdvanceEpoch),
        (AdvanceSettlementEpoch, AdvanceSettlementEpoch),
        (Block, Block),
        (IndexPrice, IndexPrice),
        (MintPriceCheckpoint, PriceCheckpoint),
        (UpdateProductListings, UpdateProductListings),
    );

    #[pymethods]
    impl IndexPrice {
        #[pyo3(name = "hash")]
        fn hash_py(&self) -> IndexPriceHash {
            self.hash()
        }
    }

    // INTENTS----------------------------------------------------------------------

    macro_rules! delegate_intent_methods {
        ($( ($name:ty, $variant:ident), )*) => {
            $(
                #[pymethods]
                impl $name {
                    fn __repr__(&self) -> String {
                        format!("{:?}", self)
                    }

                    #[getter(json)]
                    fn request_repr(&self, py: Python) -> PyObject {
                        pythonize::pythonize(py, &Request::from(ClientRequest::$variant(self.clone()))).unwrap()
                    }

                    #[pyo3(name = "hash_eip712")]
                    fn hash_eip712_py(&self, message_metadata: Option<(u64, &str)>) -> PyResult<Hash> {
                        if let Some((chain_id, contract_address)) = message_metadata {
                            return Ok(self.hash_eip712_raw(
                                core_common::types::state::Chain::Ethereum(chain_id),
                                Address::from_str(contract_address).map_err(|e| CoreCommonError::new_err(e.to_string()))?,
                            ));
                        }
                        Ok(self.hash_eip712())
                    }

                    #[pyo3(name = "recover_signer")]
                    fn recover_signer_py(&self) -> PyResult<(Hash, TraderAddress)> {
                        Ok(self.recover_signer()?)
                    }
                }
            )*
        };
    }

    #[cfg(feature = "insurance_fund_client_req")]
    delegate_intent_methods!((InsuranceFundWithdrawIntent, InsuranceFundWithdraw),);
    delegate_intent_methods!(
        (OrderIntent, Order),
        (ModifyOrderIntent, ModifyOrder),
        (WithdrawIntent, Withdraw),
        (CancelAllIntent, CancelAll),
        (CancelOrderIntent, CancelOrder),
        (ProfileUpdate, ProfileUpdate),
        (WithdrawDDXIntent, WithdrawDDX),
    );

    #[pymethods]
    impl OrderIntent {
        #[pyo3(name = "hash")]
        fn hash_py(&self) -> PyResult<OrderHash> {
            Ok(self.order_hash()?)
        }
    }

    #[pymethods]
    impl ModifyOrderIntent {
        #[pyo3(name = "hash")]
        fn hash_py(&self) -> PyResult<OrderHash> {
            Ok(self.order_hash()?)
        }
    }

    // ITEM/ BASE TYPES------------------------------------------------------------

    #[pyclass(frozen)]
    #[repr(u8)]
    #[derive(Clone, Copy, PartialEq, Eq, std::hash::Hash)]
    pub enum ItemKind {
        Empty = ITEM_EMPTY,
        Trader = ITEM_TRADER,
        Strategy = ITEM_STRATEGY,
        Position = ITEM_POSITION,
        BookOrder = ITEM_BOOK_ORDER,
        Price = ITEM_PRICE,
        InsuranceFund = ITEM_INSURANCE_FUND,
        Stats = ITEM_STATS,
        Signer = ITEM_SIGNER,
        Specs = ITEM_SPECS,
        TradableProduct = ITEM_TRADABLE_PRODUCT,
        InsuranceFundContribution = ITEM_INSURANCE_FUND_CONTRIBUTION,
        EpochMetadata = ITEM_EPOCH_METADATA,
    }

    #[pymethods]
    impl ItemKind {
        #[new]
        fn new(value: u8) -> PyResult<Self> {
            Ok(match value {
                ITEM_EMPTY => ItemKind::Empty,
                ITEM_TRADER => ItemKind::Trader,
                ITEM_STRATEGY => ItemKind::Strategy,
                ITEM_POSITION => ItemKind::Position,
                ITEM_BOOK_ORDER => ItemKind::BookOrder,
                ITEM_PRICE => ItemKind::Price,
                ITEM_INSURANCE_FUND => ItemKind::InsuranceFund,
                ITEM_STATS => ItemKind::Stats,
                ITEM_SIGNER => ItemKind::Signer,
                ITEM_SPECS => ItemKind::Specs,
                ITEM_TRADABLE_PRODUCT => ItemKind::TradableProduct,
                ITEM_INSURANCE_FUND_CONTRIBUTION => ItemKind::InsuranceFundContribution,
                ITEM_EPOCH_METADATA => ItemKind::EpochMetadata,
                _ => {
                    return Err(PyValueError::new_err(format!(
                        "{} is not a valid ItemKind",
                        value
                    )));
                }
            })
        }

        #[classattr]
        fn discriminants(py: Python) -> Py<PyDict> {
            let members = PyDict::new(py);
            members.set_item("Empty", ItemKind::Empty as u8).unwrap();
            members.set_item("Trader", ItemKind::Trader as u8).unwrap();
            members
                .set_item("Strategy", ItemKind::Strategy as u8)
                .unwrap();
            members
                .set_item("Position", ItemKind::Position as u8)
                .unwrap();
            members
                .set_item("BookOrder", ItemKind::BookOrder as u8)
                .unwrap();
            members.set_item("Price", ItemKind::Price as u8).unwrap();
            members
                .set_item("InsuranceFund", ItemKind::InsuranceFund as u8)
                .unwrap();
            members.set_item("Stats", ItemKind::Stats as u8).unwrap();
            members.set_item("Signer", ItemKind::Signer as u8).unwrap();
            members.set_item("Specs", ItemKind::Specs as u8).unwrap();
            members
                .set_item("TradableProduct", ItemKind::TradableProduct as u8)
                .unwrap();
            members
                .set_item(
                    "InsuranceFundContribution",
                    ItemKind::InsuranceFundContribution as u8,
                )
                .unwrap();
            members
                .set_item("EpochMetadata", ItemKind::EpochMetadata as u8)
                .unwrap();
            members.into_py(py)
        }
    }

    impl ToPyObject for ItemKind {
        fn to_object(&self, py: Python) -> PyObject {
            self.into_py(py)
        }
    }

    #[pyclass(frozen)]
    #[derive(Clone, PartialEq, Debug, Eq)]
    pub struct Item {
        inner: RustItem,
    }

    macro_rules! generate_item_abi_decode {
        ($( $variants:ident, $key_variants:ident; )*) => {
            #[pymethods]
            impl Item {
                fn __repr__(&self) -> String {
                    format!("{:?}", self)
                }

                fn __eq__(&self, other: &Self) -> bool {
                    self == other
                }

                fn item_kind(&self) -> ItemKind {
                    ItemKind::new(self.inner.discriminant()).unwrap()
                }

                fn abi_encoded_value(&self) -> Cow<[u8]> {
                    match &self.inner {
                        RustItem::Empty => Vec::new().into(),
                        $(
                            RustItem::$variants(inner) => <$variants>::from(inner.clone()).abi_encoded_value().into_owned().into(),
                        )*
                    }
                }

                #[classmethod]
                fn abi_decode_value_into_item(
                    cls: &PyType,
                    kind: ItemKind,
                    abi_encoded_value: &[u8],
                ) -> PyResult<Option<Self>> {
                    match kind {
                        ItemKind::Empty if abi_encoded_value.is_empty() => Ok(Some(Self {
                            inner: RustItem::Empty,
                        })),
                        ItemKind::Empty => {
                            return Err(CoreCommonError::new_err(
                                "invalid abi representation: empty schema but non-empty value",
                            ))
                        }
                        $(
                            ItemKind::$variants => <$variants>::abi_decode_value_into_item(
                                PyType::new::<$variants>(cls.py()),
                                abi_encoded_value,
                            ),
                        )*
                    }
                }

                #[classmethod]
                fn decode_key(
                    cls: &PyType,
                    kind: ItemKind,
                    encoded_key: H256,
                ) -> PyResult<PyObject> {
                    match kind {
                        ItemKind::Empty => {
                            return Err(CoreCommonError::new_err(
                                "cannot decode key for empty item kind",
                            ))
                        }
                        $(
                            ItemKind::$variants => <$key_variants>::decode_key_py(
                                PyType::new::<$key_variants>(cls.py()),
                                encoded_key,
                            ).map(|v| v.into_py(cls.py())),
                        )*
                    }
                }
            }
        }
    }

    generate_item_abi_decode!(
        Trader, TraderKey;
        Strategy, StrategyKey;
        Position, PositionKey;
        BookOrder, BookOrderKey;
        Price, PriceKey;
        InsuranceFund, InsuranceFundKey;
        Stats, StatsKey;
        Signer, SignerKey;
        Specs, SpecsKey;
        TradableProduct, TradableProductKey;
        InsuranceFundContribution, InsuranceFundContributionKey;
        EpochMetadata, EpochMetadataKey;
    );

    impl From<Item> for RustItem {
        fn from(item: Item) -> Self {
            item.inner
        }
    }

    // INNER TYPES------------------------------------------------------------

    // Renaming is used to avoid name conflicts with the corresponding Rust methods
    #[pymethods]
    impl Balance {
        fn __repr__(&self) -> String {
            format!("{:?}", self)
        }

        fn __len__(&self) -> PyResult<usize> {
            Ok(self.len())
        }

        fn __getitem__(&self, key: TokenSymbol) -> Decimal {
            Decimal::from(*self.get_or_default(key))
        }

        fn __setitem__(&mut self, key: TokenSymbol, value: Decimal) {
            self.insert(key, value.clone().into());
        }

        #[classmethod]
        #[pyo3(name = "default")]
        fn default_py(_cls: &PyType) -> Self {
            Balance::default()
        }

        #[classmethod]
        #[pyo3(name = "new_from_many")]
        fn new_from_many_py(
            _cls: &PyType,
            amounts: HashMap<TokenSymbol, Decimal>,
        ) -> PyResult<Self> {
            Ok(Balance::new_from_many(
                &amounts
                    .into_iter()
                    .map(|(symbol, amount)| (symbol, amount.into()))
                    .collect(),
            )?)
        }

        #[pyo3(name = "total_value")]
        fn total_value_py(&self) -> Decimal {
            self.total_value().into()
        }

        #[pyo3(name = "amounts")]
        fn amounts_py(&self) -> Vec<Decimal> {
            self.amounts().into_iter().map(|v| (*v).into()).collect()
        }
    }

    // TODO: this really sucks but it has to be done. we definitely should proceduralize all of this later

    macro_rules! delegate_balance_methods {
        ($item_name:ty) => {
            #[pymethods]
            impl $item_name {
                fn __len__(&self) -> PyResult<usize> {
                    self.inner.__len__()
                }

                fn __getitem__(&self, key: TokenSymbol) -> Decimal {
                    self.inner.__getitem__(key)
                }

                fn __setitem__(&mut self, key: TokenSymbol, value: Decimal) {
                    self.inner.__setitem__(key, value)
                }

                #[new]
                fn new(amount: Decimal, symbol: TokenSymbol) -> Self {
                    Self {
                        inner: Balance::new_py(amount, symbol),
                    }
                }

                #[classmethod]
                fn default(cls: &PyType) -> Self {
                    Self {
                        inner: Balance::default_py(PyType::new::<Balance>(cls.py())),
                    }
                }

                #[classmethod]
                fn new_from_many(
                    cls: &PyType,
                    amounts: HashMap<TokenSymbol, Decimal>,
                ) -> PyResult<Self> {
                    Ok(Self {
                        inner: Balance::new_from_many_py(
                            PyType::new::<Balance>(cls.py()),
                            amounts,
                        )?,
                    })
                }

                fn total_value(&self) -> Decimal {
                    self.inner.total_value_py()
                }

                fn amounts(&self) -> Vec<Decimal> {
                    self.inner.amounts_py()
                }
            }
        };
    }

    // ITEM/ TYPES------------------------------------------------------------

    // Note: unfortunately macros cannot be called inside of pymethods, or else a lot of extraneous
    // code could be removed and replaced with paste! or internal macros.
    macro_rules! impl_item {
        ($item_name:ident, $key_name:ident) => {
            impl_item!(@common $item_name, $key_name; $item_name);
        };
        ($item_name:ident, $key_name:ident;; $key_type:ty) => {
            impl_item!(@key $key_name, $key_type);
            impl_item!(@common $item_name, $key_name; $item_name);
        };
        ($item_name:ident, $key_name:ident; $inner:ty;) => {
            impl_item!(@item $item_name, $inner);
            impl_item!(@common $item_name, $key_name; $inner);
        };
        ($item_name:ident, $key_name:ident; $inner:ty; $key_type:ty) => {
            impl_item!(@item $item_name, $inner);
            impl_item!(@key $key_name, $key_type);
            impl_item!(@common $item_name, $key_name; $inner);
        };
        (@item $name:ident, $inner:ty) => {
            #[pyclass]
            #[derive(Clone, PartialEq, Eq, Debug, Default)]
            pub struct $name {
                inner: $inner,
            }

            impl VoidableItem for $name {
                fn is_void(&self) -> bool {
                    self.inner.is_void()
                }
            }

            impl Tokenizable for $name {
                fn from_token(token: DynSolValue) -> core_common::Result<Self>
                where
                    Self: Sized,
                {
                    <$inner>::from_token(token).map(|inner| Self { inner })
                }
                fn into_token(self) -> DynSolValue {
                    self.inner.into_token()
                }
            }

            impl From<$name> for $inner {
                fn from(item: $name) -> Self {
                    item.inner
                }
            }

            impl From<&$name> for $inner {
                fn from(item: &$name) -> Self {
                    item.inner.clone()
                }
            }

            impl From<$inner> for $name {
                fn from(inner: $inner) -> Self {
                    Self { inner }
                }
            }
        };
        (@key $name:ident, $key_type:ty) => {
            #[pyclass(frozen)]
            #[derive(Clone, PartialEq, Eq, std::hash::Hash, Debug, PartialOrd, Ord)]
            pub struct $name {
                inner: $key_type,
            }

            #[pymethods]
            impl $name {
                #[new]
                fn new(inner: $key_type) -> Self {
                    Self { inner }
                }
            }

            impl VerifiedStateKey for $name {
                fn encode_key(&self) -> Hash {
                    self.inner.encode_key()
                }

                fn decode_key(value: &Hash) -> core_common::Result<Self> {
                    Ok(Self {
                        inner: <$key_type>::decode_key(value)?,
                    })
                }
            }

            impl From<$name> for $key_type {
                fn from(item: $name) -> Self {
                    item.inner
                }
            }

            impl<'a> From<&'a $name> for &'a $key_type {
                fn from(item: &'a $name) -> &'a $key_type {
                    &item.inner
                }
            }

            impl From<$key_type> for $name {
                fn from(inner: $key_type) -> Self {
                    Self { inner }
                }
            }
        };
        (@common $item_name:ident, $key_name:ident; $inner:ty) => {
            #[pymethods]
            impl $key_name {
                fn __eq__(&self, other: &Self) -> bool {
                    self == other
                }

                fn __repr__(&self) -> String {
                    format!("{:?}", self)
                }

                fn __hash__(&self) -> u64 {
                    use std::hash::{Hasher, Hash};
                    let mut hasher = std::collections::hash_map::DefaultHasher::new();
                    self.hash(&mut hasher);
                    hasher.finish()
                }

                fn __deepcopy__(&self, _memo: &PyDict) -> Self {
                    self.clone()
                }

                fn __lt__(&self, other: &Self) -> bool {
                    self < other
                }

                #[pyo3(name = "encode_key")]
                fn encode_key_py(&self) -> H256 {
                    RustH256::from(<$key_name>::from(self.clone()).encode_key()).into()
                }

                #[classmethod]
                #[pyo3(name = "decode_key")]
                fn decode_key_py(_cls: &PyType, value: H256) -> PyResult<Self> {
                    Ok(<$key_name>::decode_key(&RustH256::from(value).into())?.into())
                }
            }

            #[pymethods]
            impl $item_name {
                fn __eq__(&self, other: &Self) -> bool {
                    self == other
                }

                fn __repr__(&self) -> String {
                    format!("{:?}", self)
                }

                fn __deepcopy__(&self, _memo: &PyDict) -> Self {
                    self.clone()
                }

                fn as_item(&self) -> Item {
                    Item {
                        inner: RustItem::$item_name(<$inner>::from(self.clone())),
                    }
                }

                #[classmethod]
                fn from_item(_cls: &PyType, item: Item) -> PyResult<Self> {
                    match item.inner {
                        RustItem::$item_name(inner) => Ok(inner.into()),
                        _ => Err(CoreCommonError::new_err("invalid item kind")),
                    }
                }

                fn abi_encoded_value(&self) -> Cow<[u8]> {
                    alloy_dyn_abi::DynSolValue::Tuple(vec![self.as_item().inner.into_token()]).abi_encode().into()
                }

                #[classmethod]
                fn abi_decode_value_into_item(
                    _cls: &PyType,
                    abi_encoded_value: &[u8],
                ) -> PyResult<Option<Item>> {
                    for abi_schema in &ITEM_PARAM_TYPES[&ItemKind::$item_name] {
                        match abi_schema.abi_decode(abi_encoded_value).map_err(|e|CoreCommonError::new_err(format!("invalid abi representation: {}", e.to_string())))
                            .and_then(|v|
                                match v.as_tuple() {
                                    Some(t) => RustItem::from_token(t[0].clone()).map_err(|_| {
                                    CoreCommonError::new_err(format!("Failed to deserialize token into Item"))
                                }),
                                    None => Err(CoreCommonError::new_err("failed to deserialize token as tuple".to_string())),
                                })
                        {
                            Ok(item) => {
                                return Ok(Some(Item { inner: item }));
                            }
                            Err(_) => continue,
                        }
                    }
                    Err(CoreCommonError::new_err(
                        "invalid abi representation: all schemas failed".to_string(),
                    ))
                }

                #[pyo3(name = "is_void")]
                fn is_void_py(&self) -> bool {
                    self.is_void()
                }
            }
        };
    }

    lazy_static! {
        static ref ITEM_PARAM_TYPES: HashMap<ItemKind, Vec<DynSolType>> = {
            [
                (
                    ItemKind::Trader,
                    vec![DynSolType::Tuple(vec![
                        DynSolType::Uint(256),
                        DynSolType::Uint(256),
                        DynSolType::Address,
                        DynSolType::Bool,
                        DynSolType::Bool,
                    ])],
                ),
                (
                    ItemKind::Strategy,
                    vec![DynSolType::Tuple(vec![
                        DynSolType::Tuple(vec![
                            DynSolType::Array(Box::new(DynSolType::Address)),
                            DynSolType::Array(Box::new(DynSolType::Uint(128))),
                        ]),
                        DynSolType::Tuple(vec![
                            DynSolType::Array(Box::new(DynSolType::Address)),
                            DynSolType::Array(Box::new(DynSolType::Uint(128))),
                        ]),
                        DynSolType::Uint(64),
                        DynSolType::Bool,
                    ])],
                ),
                (
                    ItemKind::Position,
                    vec![DynSolType::Tuple(vec![
                        DynSolType::Tuple(vec![DynSolType::Uint(256)]),
                        DynSolType::Uint(256),
                        DynSolType::Uint(256),
                    ])],
                ),
                (
                    ItemKind::BookOrder,
                    vec![DynSolType::Tuple(vec![
                        DynSolType::Tuple(vec![DynSolType::Uint(256)]),
                        DynSolType::Uint(256),
                        DynSolType::Uint(256),
                        DynSolType::FixedBytes(32),
                        DynSolType::FixedBytes(4),
                        DynSolType::Uint(64),
                        DynSolType::Uint(64),
                    ])],
                ),
                (
                    ItemKind::Price,
                    vec![
                        DynSolType::Tuple(vec![
                            DynSolType::Uint(256),
                            DynSolType::Tuple(vec![DynSolType::Uint(256), DynSolType::Uint(256)]),
                            DynSolType::Uint(64),
                            DynSolType::Uint(64),
                        ]),
                        DynSolType::Tuple(vec![
                            DynSolType::Uint(256),
                            DynSolType::Tuple(vec![
                                DynSolType::Uint(256),
                                DynSolType::Uint(256),
                                DynSolType::Uint(64),
                            ]),
                            DynSolType::Uint(64),
                            DynSolType::Uint(64),
                        ]),
                    ],
                ),
                (
                    ItemKind::InsuranceFund,
                    vec![DynSolType::Tuple(vec![
                        DynSolType::Array(Box::new(DynSolType::Address)),
                        DynSolType::Array(Box::new(DynSolType::Uint(128))),
                    ])],
                ),
                (
                    ItemKind::Stats,
                    vec![DynSolType::Tuple(vec![
                        DynSolType::Uint(256),
                        DynSolType::Uint(256),
                    ])],
                ),
                (ItemKind::Signer, vec![DynSolType::FixedBytes(32)]),
                (ItemKind::Specs, vec![DynSolType::String]),
                (ItemKind::TradableProduct, vec![DynSolType::Tuple(vec![])]),
                (
                    ItemKind::InsuranceFundContribution,
                    vec![DynSolType::Tuple(vec![
                        DynSolType::Tuple(vec![
                            DynSolType::Array(Box::new(DynSolType::Address)),
                            DynSolType::Array(Box::new(DynSolType::Uint(128))),
                        ]),
                        DynSolType::Tuple(vec![
                            DynSolType::Array(Box::new(DynSolType::Address)),
                            DynSolType::Array(Box::new(DynSolType::Uint(128))),
                        ]),
                    ])],
                ),
                (
                    ItemKind::EpochMetadata,
                    vec![DynSolType::Tuple(vec![
                        DynSolType::Uint(256),
                        DynSolType::Tuple(vec![
                            DynSolType::Array(Box::new(DynSolType::FixedBytes(32))),
                            DynSolType::Array(Box::new(DynSolType::Uint(64))),
                        ]),
                    ])],
                ),
            ]
            .into_iter()
            .map(|(k, inner)| {
                (
                    k,
                    inner
                        .into_iter()
                        .map(|pt| {
                            DynSolType::Tuple(vec![DynSolType::Tuple(vec![
                                DynSolType::Uint(256),
                                pt,
                            ])])
                        })
                        .collect(),
                )
            })
            .collect()
        };
    }

    impl_item!(
        Trader,
        TraderKey
        ;;
        TraderAddress
    );

    #[pymethods]
    impl Trader {
        #[classmethod]
        #[pyo3(name = "default")]
        fn default_py(_cls: &PyType) -> Self {
            Self::default()
        }
    }

    impl_item!(Strategy, StrategyKey);

    #[pymethods]
    impl Strategy {
        fn update_avail_collateral(&self, symbol: TokenSymbol, amount: Decimal) -> Balance {
            let mut new = self.avail_collateral.clone();
            new.insert(symbol, amount.into());
            new
        }

        fn update_locked_collateral(&self, symbol: TokenSymbol, amount: Decimal) -> Balance {
            let mut new = self.locked_collateral.clone();
            new.insert(symbol, amount.into());
            new
        }
    }

    #[pymethods]
    impl StrategyKey {
        #[staticmethod]
        fn generate_strategy_id_hash(strategy_id: StrategyId) -> StrategyIdHash {
            strategy_id.into()
        }

        #[pyo3(name = "as_position_key")]
        fn as_position_key_py(&self, symbol: ProductSymbol) -> PositionKey {
            self.as_position_key::<RustProductSymbol>(symbol.into())
        }
    }

    impl_item!(Position, PositionKey);

    // Renaming is used to avoid name conflicts with the corresponding Rust methods
    #[pymethods]
    impl Position {
        #[classmethod]
        #[pyo3(name = "default")]
        fn default_py(_cls: &PyType) -> Self {
            Self::default()
        }

        #[pyo3(name = "bankruptcy_price")]
        fn bankruptcy_price_py(
            &self,
            mark_price: Decimal,
            account_total_value: Decimal,
        ) -> Decimal {
            self.bankruptcy_price(mark_price.into(), account_total_value.into())
                .into()
        }

        #[pyo3(name = "unrealized_pnl")]
        fn unrealized_pnl_py(&self, price: Decimal) -> Decimal {
            self.unrealized_pnl(price.into()).into()
        }

        #[pyo3(name = "avg_pnl")]
        fn avg_pnl_py(&self, price: Decimal) -> Decimal {
            self.avg_pnl(price.into()).into()
        }

        // HACK: have to clone here because of this annoying #[pyo3(get)] cloning behavior
        // https://pyo3.rs/v0.21.2/faq#pyo3get-clones-my-field
        #[pyo3(name = "increase")]
        fn increase_py(&self, price: Decimal, amount: Decimal) -> (Self, Decimal) {
            let mut new = self.clone();
            let res = new.increase(price.into(), amount.into()).into();
            (new, res)
        }

        // HACK: have to clone here because of this annoying #[pyo3(get)] cloning behavior
        // https://pyo3.rs/v0.21.2/faq#pyo3get-clones-my-field
        #[pyo3(name = "decrease")]
        fn decrease_py(&self, price: Decimal, amount: Decimal) -> (Self, Decimal) {
            let mut new = self.clone();
            let res = new.decrease(price.into(), amount.into()).into();
            (new, res)
        }

        // HACK: have to clone here because of this annoying #[pyo3(get)] cloning behavior
        // https://pyo3.rs/v0.21.2/faq#pyo3get-clones-my-field
        #[pyo3(name = "cross_over")]
        fn cross_over_py(&self, price: Decimal, amount: Decimal) -> (Self, Decimal) {
            let mut new = self.clone();
            let res = new.cross_over(price.into(), amount.into()).unwrap().into();
            (new, res)
        }
    }

    #[pymethods]
    impl PositionKey {
        fn as_strategy_key(&self) -> StrategyKey {
            StrategyKey::from(*self)
        }
    }

    impl_item!(BookOrder, BookOrderKey);
    impl_item!(Price, PriceKey);

    // Renaming is used to avoid name conflicts with the corresponding Rust methods
    #[pymethods]
    impl Price {
        #[getter(mark_price)]
        fn mark_price_py(&self) -> Decimal {
            self.mark_price().into()
        }
    }

    impl_item!(
        InsuranceFund,
        InsuranceFundKey
        ;
        Balance;
    );
    delegate_balance_methods!(InsuranceFund);
    impl_item!(Stats, StatsKey);

    #[pymethods]
    impl Stats {
        #[classmethod]
        #[pyo3(name = "default")]
        fn default_py(_cls: &PyType) -> Self {
            Self::default()
        }
    }

    #[pymethods]
    impl StatsKey {
        fn as_trader_key(&self) -> TraderKey {
            TraderKey { inner: self.trader }
        }
    }

    impl_item!(
        Signer,
        SignerKey
        ;
        ReleaseHash;
        SignerAddress
    );

    #[pymethods]
    impl Signer {
        #[new]
        fn new(inner: ReleaseHash) -> Self {
            Self { inner }
        }
    }

    impl_item!(
        Specs,
        SpecsKey
        ;
        SpecsExpr;
    );

    #[pymethods]
    impl Specs {
        #[new]
        fn new(inner: SpecsExpr) -> Self {
            Self { inner }
        }

        fn as_product_specs(&self, specs_kind: SpecsKind) -> PyResult<ProductSpecs> {
            Ok(self
                .inner
                .as_product_specs(specs_kind)
                .map(|rust_specs| rust_specs.into())?)
        }
    }

    #[pymethods]
    impl SpecsKey {
        #[cfg(feature = "fixed_expiry_future")]
        #[pyo3(name = "current_tradable_products")]
        fn current_tradable_products_py(
            &self,
            current_time: DateTime<Utc>,
        ) -> Vec<TradableProductKey> {
            self.current_tradable_products(current_time)
        }

        #[cfg(not(feature = "fixed_expiry_future"))]
        #[pyo3(name = "current_tradable_products")]
        fn current_tradable_products_py(&self) -> Vec<TradableProductKey> {
            self.current_tradable_products()
        }

        #[pyo3(name = "has_lifecycle")]
        fn has_lifecycle_py(&self) -> Option<bool> {
            self.has_lifecycle()
        }
    }

    impl_item!(TradableProduct, TradableProductKey);

    #[pymethods]
    impl TradableProductKey {
        fn as_product_symbol(&self) -> ProductSymbol {
            RustProductSymbol::from(self).into()
        }
    }

    impl_item!(
        InsuranceFundContribution,
        InsuranceFundContributionKey
        ;;
        InsuranceFundContributorAddress
    );

    #[pymethods]
    impl InsuranceFundContribution {
        #[classmethod]
        #[pyo3(name = "default")]
        fn default_py(_cls: &PyType) -> Self {
            Self::default()
        }

        fn update_avail_balance(&self, symbol: TokenSymbol, amount: Decimal) -> Balance {
            let mut new = self.avail_balance.clone();
            new.insert(symbol, amount.into());
            new
        }

        fn update_locked_balance(&self, symbol: TokenSymbol, amount: Decimal) -> Balance {
            let mut new = self.locked_balance.clone();
            new.insert(symbol, amount.into());
            new
        }
    }

    impl_item!(EpochMetadata, EpochMetadataKey);

    #[pymethods]
    impl EpochMetadata {
        #[classmethod]
        #[pyo3(name = "default")]
        fn default_py(_cls: &PyType) -> Self {
            Self::default()
        }
    }

    // SMT TYPES------------------------------------------------------------

    #[pyclass(frozen)]
    #[derive(Clone, Debug)]
    pub struct MerkleProof {
        inner: CompiledMerkleProof,
    }

    #[pymethods]
    impl MerkleProof {
        fn __repr__(&self) -> String {
            format!("{:?}", self)
        }

        fn as_bytes(&self) -> Cow<[u8]> {
            self.inner.0.clone().into()
        }
    }

    impl From<CompiledMerkleProof> for MerkleProof {
        fn from(proof: CompiledMerkleProof) -> Self {
            MerkleProof { inner: proof }
        }
    }

    /// Wrapped DerivaDEX Sparse Merkle Tree.
    #[pyclass]
    #[derive(Debug)]
    pub struct DerivadexSMT {
        inner: SharedSparseMerkleTree,
    }

    #[pymethods]
    impl DerivadexSMT {
        fn __repr__(&self) -> String {
            format!("{:?}", self)
        }

        #[new]
        fn new() -> Self {
            Self {
                inner: SharedSparseMerkleTree::new(Default::default(), ConcurrentStore::empty()),
            }
        }

        #[cfg(not(feature = "fixed_expiry_future"))]
        #[classmethod]
        fn from_genesis(
            _cls: &PyType,
            py: Python,
            insurance_fund_cap: Balance,
            ddx_fee_pool: UnscaledI128,
            specs: PyObject,
        ) -> PyResult<Self> {
            let specs = &specs.extract::<HashMap<SpecsKey, SpecsExpr>>(py)?;
            Ok(Self {
                inner: from_genesis(insurance_fund_cap, ddx_fee_pool, specs)?,
            })
        }

        #[cfg(feature = "fixed_expiry_future")]
        #[classmethod]
        fn from_genesis(
            _cls: &PyType,
            py: Python,
            insurance_fund_cap: Balance,
            ddx_fee_pool: UnscaledI128,
            specs: PyObject,
            current_time: DateTime<Utc>,
        ) -> PyResult<Self> {
            let specs = &specs.extract::<HashMap<SpecsKey, SpecsExpr>>(py)?;
            Ok(Self {
                inner: from_genesis(insurance_fund_cap, ddx_fee_pool, specs, current_time)?,
            })
        }

        fn root(&self) -> H256 {
            (*self.inner.root()).into()
        }

        fn merkle_proof(&self, keys: Vec<H256>) -> PyResult<MerkleProof> {
            // No keys require no proof. It's easier than adding error conditions.
            if keys.is_empty() {
                return Ok(CompiledMerkleProof(vec![]).into());
            }
            let leaves = keys
                .iter()
                .map(|k| {
                    let k: RustH256 = (*k).into();
                    let v = self.inner.get(&k).map_err(|e| {
                        CoreCommonError::new_err(format!("merkle proof error: {}", e))
                    })?;
                    Ok((k, v.to_h256()))
                })
                .collect::<PyResult<Vec<_>>>()?;
            let compiled_proof = self
                .inner
                .merkle_proof(keys.iter().map(|&k| k.into()).collect())
                .and_then(|proof| proof.compile(leaves))
                .map_err(|e| CoreCommonError::new_err(format!("merkle proof error: {}", e)))?;
            Ok(compiled_proof.into())
        }

        #[pyo3(signature = (key, maybe_inner))]
        fn store_item_by_key(&mut self, key: H256, maybe_inner: Option<Item>) -> PyResult<H256> {
            let key: RustH256 = key.into();
            let item = match maybe_inner {
                Some(inner) => {
                    let item = RustItem::from(inner);
                    if key.as_slice()[0] != item.discriminant() {
                        return Err(CoreCommonError::new_err(
                            "key and item discriminant mismatch",
                        ));
                    }
                    item
                }
                None => RustItem::zero(),
            };
            self.inner
                .update(key, item)
                .map(|&key| key.into())
                .map_err(|e| CoreCommonError::new_err(format!("smt update error: {}", e)))
        }

        fn __deepcopy__(&self, _memo: &PyDict) -> Self {
            DerivadexSMT {
                inner: SharedSparseMerkleTree::new(
                    *self.inner.root(),
                    self.inner.store().deep_copy(),
                ),
            }
        }
    }

    // Note: unfortunately macros cannot be called inside of pymethods, or else a lot of extraneous
    // code could be removed and replaced with paste! or internal macros.
    macro_rules! impl_get_and_store_for_smt {
        ($get_name:ident, $get_all_name:ident, $store_name:ident; $variant:ident, $key_type:ty) => {
            #[pymethods]
            impl DerivadexSMT {
                fn $get_name(&self, key: &$key_type) -> PyResult<Option<$variant>> {
                    let item = self
                        .inner
                        .get(&(key.encode_key().into()))
                        .map_err(|e| CoreCommonError::new_err(format!("smt get error: {}", e)))?;
                    if let RustItem::$variant(val) = item {
                        Ok(Some(val.into()))
                    } else if item == RustItem::zero() {
                        Ok(None)
                    } else {
                        Err(CoreCommonError::new_err(concat!(
                            "invalid ",
                            stringify!($variant),
                            " item"
                        )))
                    }
                }

                #[pyo3(signature = (key, maybe_inner))]
                fn $store_name(
                    &mut self,
                    key: $key_type,
                    maybe_inner: Option<$variant>,
                ) -> PyResult<H256> {
                    let item = match maybe_inner {
                        Some(inner) if !inner.is_void() => RustItem::$variant(inner.into()),
                        _ => RustItem::zero(),
                    };
                    self.inner
                        .update(key.encode_key().into(), item)
                        .map(|&root| root.into())
                        .map_err(|e| CoreCommonError::new_err(format!("smt update error: {}", e)))
                }

                fn $get_all_name(&self) -> Vec<($key_type, $variant)> {
                    self.inner
                        .store()
                        .leaves_map()
                        .read()
                        .unwrap()
                        .iter()
                        .filter_map(|(_, item)| {
                            if let RustItem::$variant(val) = &item.value {
                                Some((
                                    <$key_type>::decode_key(&item.key.into())
                                        .expect("key item mismatch"),
                                    <$variant>::from(val.clone()),
                                ))
                            } else {
                                None
                            }
                        })
                        .collect()
                }
            }
        };
    }

    impl_get_and_store_for_smt!(
        trader,
        all_traders,
        store_trader;
        Trader,
        TraderKey
    );
    impl_get_and_store_for_smt!(
        strategy,
        all_strategies,
        store_strategy;
        Strategy,
        StrategyKey
    );
    impl_get_and_store_for_smt!(
        position,
        all_positions,
        store_position;
        Position,
        PositionKey
    );
    impl_get_and_store_for_smt!(
        book_order,
        all_book_orders,
        store_book_order;
        BookOrder,
        BookOrderKey
    );
    impl_get_and_store_for_smt!(
        price,
        all_prices,
        store_price;
        Price,
        PriceKey
    );
    impl_get_and_store_for_smt!(
        insurance_fund,
        all_insurance_funds,
        store_insurance_fund;
        InsuranceFund,
        InsuranceFundKey
    );
    impl_get_and_store_for_smt!(
        stats,
        all_stats,
        store_stats;
        Stats,
        StatsKey
    );
    impl_get_and_store_for_smt!(
        signer,
        all_signers,
        store_signer;
        Signer,
        SignerKey
    );
    impl_get_and_store_for_smt!(
        specs,
        all_specs,
        store_specs;
        Specs,
        SpecsKey
    );
    impl_get_and_store_for_smt!(
        tradable_product,
        all_tradable_products,
        store_tradable_product;
        TradableProduct,
        TradableProductKey
    );
    impl_get_and_store_for_smt!(
        insurance_fund_contribution,
        all_insurance_fund_contributions,
        store_insurance_fund_contribution;
        InsuranceFundContribution,
        InsuranceFundContributionKey
    );
    impl_get_and_store_for_smt!(
        epoch_metadata,
        all_epoch_metadatas,
        store_epoch_metadata;
        EpochMetadata,
        EpochMetadataKey
    );

    // Note: unfortunately macros cannot be called inside of pymethods, or else a lot of extraneous
    // code could be removed and replaced with paste! or internal macros.
    macro_rules! impl_extra_get_all_for_smt {
        ($name:ident($( $args:tt )*), $variant_type:ident, $key_type:ident, $filter_map:expr) => {
            #[pymethods]
            impl DerivadexSMT {
                fn $name(&self, $($args)*) -> Vec<($key_type, $variant_type)> {
                    self.inner
                        .store()
                        .leaves_map()
                        .read()
                        .unwrap()
                        .iter()
                        .filter_map(|(key, item)| {
                            #[allow(unused_variables, clippy::redundant_closure_call)]
                            $filter_map(key, item)
                        })
                        .collect()
                }
            }
        }
    }

    impl_extra_get_all_for_smt!(
        all_leaves(),
        Item,
        H256,
        (|_hash: &RustH256, item: &LeafNode<RustItem>| {
            Some((
                H256::from(item.key),
                Item {
                    inner: item.value.clone(),
                },
            ))
        })
    );
    impl_extra_get_all_for_smt!(
        all_prices_for_symbol(symbol: RustProductSymbol),
        Price,
        PriceKey,
        (|_hash: &RustH256, item: &LeafNode<RustItem>| {
            if let RustItem::Price(val) = &item.value {
                let key = PriceKey::decode_key(&item.key.into()).expect("invalid price key");
                if key.symbol == symbol {
                    return Some((key, *val));
                }
            }
            None
        })
    );
    impl_extra_get_all_for_smt!(
        all_positions_for_symbol(symbol: RustProductSymbol),
        Position,
        PositionKey,
        (|_hash: &RustH256, item: &LeafNode<RustItem>| {
            if let RustItem::Position(val) = &item.value {
                let key = PositionKey::decode_key(&item.key.into()).expect("invalid position key");
                if key.symbol == symbol {
                    return Some((key, val.clone()));
                }
            }
            None
        })
    );
    impl_extra_get_all_for_smt!(
        all_book_orders_for_symbol(symbol: RustProductSymbol),
        BookOrder,
        BookOrderKey,
        (|_hash: &RustH256, item: &LeafNode<RustItem>| {
            if let RustItem::BookOrder(val) = &item.value {
                let key =
                    BookOrderKey::decode_key(&item.key.into()).expect("invalid book order key");
                if key.symbol == symbol {
                    return Some((key, val.clone()));
                }
            }
            None
        })
    );

    #[cfg(test)]
    mod tests {
        use super::*;
        use crate::tree::shared_smt::Keccak256Hasher;
        #[cfg(feature = "fixed_expiry_future")]
        use crate::types::state::exported::UnscaledI128;

        macro_rules! generate_roundtrip_tests {
            ($($test_name:ident, $name:ident;)*) => {
                $(
                    #[test]
                    fn $test_name() {
                        pyo3::prepare_freethreaded_python();
                        Python::with_gil(|py| {
                            let item = $name::default_py(PyType::new::<$name>(py));
                            let expected_token = RustItem::$name(item.clone().into()).into_token();
                            let expected_token = alloy_dyn_abi::DynSolValue::Tuple(vec![expected_token]);
                            let bytes = expected_token.abi_encode();
                            let schema: alloy_dyn_abi::DynSolType = core_common::util::tokenize::generate_schema(&expected_token).into();
                            println!("abi schema: {:?}", schema);
                            let actual_token = item.abi_encoded_value().into_owned();
                            assert_eq!(
                                actual_token,
                                Item {
                                    inner: RustItem::$name(item.clone().into())
                                }
                                .abi_encoded_value()
                                .into_owned()
                            );
                            assert_eq!(bytes, actual_token);
                            let expected_item = RustItem::from_token(
                                schema.abi_decode(&bytes)
                                    .unwrap()
                                    .as_tuple()
                                    .unwrap()
                                    .get(0).unwrap().clone(),
                            )
                            .unwrap();
                            let actual_item =
                                $name::abi_decode_value_into_item(PyType::new::<$name>(py), &actual_token)
                                    .unwrap()
                                    .unwrap()
                                    .into();
                            assert_eq!(expected_item, actual_item);
                            assert_eq!(
                                actual_item,
                                Item::abi_decode_value_into_item(
                                    PyType::new::<Item>(py),
                                    ItemKind::$name,
                                    &actual_token
                                )
                                .unwrap()
                                .unwrap()
                                .into()
                            );
                        })
                    }
                )*
            };
        }

        macro_rules! generate_roundtrip_tests_with_default {
            ($($test_name:ident, $name:ident;)*) => {
                $(
                    #[pymethods]
                    impl $name {
                        #[classmethod]
                        #[pyo3(name = "default")]
                        fn default_py(_cls: &PyType) -> Self {
                            $name::default()
                        }
                    }
                )*

                generate_roundtrip_tests!($($test_name, $name;)*);
            };
        }

        generate_roundtrip_tests!(
            test_abi_roundtrip_trader, Trader;
            test_abi_roundtrip_position, Position;
            test_abi_roundtrip_stats, Stats;
            test_abi_roundtrip_insurance_fund_contribution, InsuranceFundContribution;
            test_abi_roundtrip_epoch_metadata, EpochMetadata;
        );

        generate_roundtrip_tests_with_default!(
            test_abi_roundtrip_strategy, Strategy;
            test_abi_roundtrip_book_order, BookOrder;
            test_abi_roundtrip_price, Price;
            test_abi_roundtrip_signer, Signer;
            test_abi_roundtrip_specs, Specs;
            test_abi_roundtrip_tradable_product, TradableProduct;
        );

        #[cfg(feature = "fixed_expiry_future")]
        #[test]
        fn test_abi_roundtrip_price_different_variant() {
            pyo3::prepare_freethreaded_python();
            Python::with_gil(|py| {
                let item = Price {
                    index_price: UnscaledI128::from_str("200").unwrap(),
                    mark_price_metadata: crate::types::accounting::MarkPriceMetadata::Average {
                        accum: UnscaledI128::ZERO,
                        count: 0,
                    },
                    ordinal: 4,
                    time_value: 241,
                };
                let expected_token =
                    alloy_dyn_abi::DynSolValue::Tuple(vec![RustItem::Price(item).into_token()])
                        .abi_encode();
                let actual_token = item.abi_encoded_value().into_owned();
                assert_eq!(
                    actual_token,
                    Item {
                        inner: RustItem::Price(item)
                    }
                    .abi_encoded_value()
                    .into_owned()
                );
                assert_eq!(expected_token, actual_token);
                let expected_item = RustItem::from_token(
                    ITEM_PARAM_TYPES[&ItemKind::Price][1]
                        .abi_decode(&actual_token)
                        .unwrap()
                        .as_tuple()
                        .unwrap()
                        .first()
                        .unwrap()
                        .clone(),
                )
                .unwrap();
                let actual_item =
                    Price::abi_decode_value_into_item(PyType::new::<Price>(py), &actual_token)
                        .unwrap()
                        .unwrap()
                        .into();
                assert_eq!(expected_item, actual_item);
                assert_eq!(
                    actual_item,
                    Item::abi_decode_value_into_item(
                        PyType::new::<Item>(py),
                        ItemKind::Price,
                        &actual_token
                    )
                    .unwrap()
                    .unwrap()
                    .into()
                );
            })
        }

        #[test]
        fn test_abi_roundtrip_merkle_proof_single_key() {
            pyo3::prepare_freethreaded_python();
            Python::with_gil(|py| {
                let mut smt = DerivadexSMT::from_genesis(
                    PyType::new::<DerivadexSMT>(py),
                    py,
                    Balance::default(),
                    UnscaledI128::default(),
                    HashMap::from([(SpecsKey::new_py(SpecsKind::SingleNamePerpetual, "ETHP".to_string()).unwrap(), SpecsExpr::new("\n(SingleNamePerpetual :name \"ETHP\"\n :underlying \"ETH\"\n :tick-size 0.1\n :max-order-notional 1000000\n :max-taker-price-deviation 0.02\n :min-order-size 0.0001\n)".to_string()))]).into_py(py),
                    #[cfg(feature = "fixed_expiry_future")]
                    Utc::now()
                ).unwrap();
                let strategy_key = StrategyKey::new_py(
                    TraderAddress::parse_eth_address("0x0000000000000000000000000000000000000001")
                        .unwrap(),
                    StrategyIdHash::default(),
                );
                smt.store_strategy(strategy_key, Some(Strategy::new_py()))
                    .unwrap();
                let expected_root = smt.root();

                let keys = vec![strategy_key.encode_key_py()];
                let proof = smt.merkle_proof(keys.clone()).unwrap();
                assert!(
                    proof
                        .inner
                        .verify::<Keccak256Hasher>(
                            &expected_root.into(),
                            keys.into_iter()
                                .map(|k| {
                                    let k = k.into();
                                    (k, smt.inner.get(&k).unwrap().to_h256())
                                })
                                .collect(),
                        )
                        .unwrap()
                );
            })
        }
    }
}
