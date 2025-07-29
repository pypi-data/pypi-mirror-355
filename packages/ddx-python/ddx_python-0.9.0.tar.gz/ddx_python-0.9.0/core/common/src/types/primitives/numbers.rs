use crate::{
    Error, Result,
    constants::{MAX_UNSCALED_DECIMAL, TOKEN_UNIT_SCALE},
    ensure,
    types::primitives::I128,
    util::tokenize::Tokenizable,
};
use alloy_dyn_abi::DynSolValue;
use alloy_primitives::{U128, U256};
use lazy_static::lazy_static;
#[cfg(feature = "database")]
use postgres_types::{FromSql, IsNull, ToSql, Type, to_sql_checked};
#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "arbitrary")]
use quickcheck::Arbitrary;
use regex::Regex;
use rust_decimal::{
    Decimal, RoundingStrategy,
    prelude::{FromPrimitive, ToPrimitive},
};
use serde::{Deserialize, Serialize};
use std::{
    convert::{From, TryFrom},
    ops::Deref,
    str::FromStr,
};

/// Currency amount recorded in the state (rounded after calculations).
pub type RecordedAmount = UnscaledI128;
pub type RecordedFee = UnscaledI128;

#[cfg(feature = "python")]
pub mod exported {
    pub mod python {
        use crate::types::primitives::{UnscaledI128, numbers::TOKEN_UNIT_SCALE};
        use pyo3::{
            class::basic::CompareOp,
            create_exception,
            exceptions::PyException,
            prelude::*,
            types::{PyBytes, PyType},
        };
        use rust_decimal::{
            Decimal as RustDecimal, RoundingStrategy,
            prelude::{MathematicalOps, ToPrimitive},
        };
        use std::{convert::TryFrom, ops::Neg, str::FromStr};

        create_exception!(decimal, DecimalError, PyException);

        const CHECKED_OP_ERROR: &str = "Check math operation error";

        /// Wrapped rust_decimal::Decimal. Constructor only supports str, e.g d = Decimal("123.456")
        #[pyclass]
        #[derive(PartialEq, Eq, Clone, Hash, PartialOrd, Ord, Debug)]
        pub struct Decimal {
            inner: RustDecimal,
        }

        #[pymethods]
        impl Decimal {
            /// Create a new Decimal In Python:
            /// let d1 = Decimal("123.456")
            /// let d2 = Decimal("-987.654")
            /// let d3 = Decimal("456")
            /// let d4 = Decimal() # Decimal("0")
            #[new]
            fn new(maybe_value: Option<&PyAny>) -> PyResult<Self> {
                match maybe_value {
                    Some(value) if !value.is_none() => Self::try_from(value),
                    _ => Ok(Self::from(RustDecimal::ZERO)),
                }
            }

            fn recorded_amount(&self) -> Self {
                let rounded = UnscaledI128::from(RustDecimal::from(self.clone()));
                RustDecimal::from(rounded).into()
            }

            fn to_usdc_grains(&self) -> PyResult<u128> {
                (self.inner * RustDecimal::TEN.powu(TOKEN_UNIT_SCALE.into()))
                    .to_u128()
                    .ok_or_else(|| DecimalError::new_err("Couldn't cast to u128 because overflow"))
            }

            fn to_ddx_grains(&self) -> PyResult<u128> {
                (self.inner * RustDecimal::TEN.powu(18))
                    .to_u128()
                    .ok_or_else(|| DecimalError::new_err("Couldn't cast to u128 because overflow"))
            }

            #[classmethod]
            fn from_usdc_grains(_cls: &PyType, u: u128) -> PyResult<Self> {
                let u = i128::try_from(u).map_err(|e| DecimalError::new_err(e.to_string()))?;
                let dec = RustDecimal::from_i128_with_scale(u, TOKEN_UNIT_SCALE);
                Ok(dec.into())
            }

            #[classmethod]
            fn from_ddx_grains(_cls: &PyType, u: u128) -> PyResult<Self> {
                let u = i128::try_from(u).map_err(|e| DecimalError::new_err(e.to_string()))?;
                let dec = RustDecimal::from_i128_with_scale(u, 18);
                Ok(dec.into())
            }

            fn quantize(&mut self, precision: u32) -> Self {
                self.inner
                    .round_dp_with_strategy(precision, RoundingStrategy::ToZero)
                    .into()
            }

            // ######################################################################
            // # State methods
            //
            // These state implementations may be best served by the `#[get]` and `#[set]` macros.
            // Infallible code returning result monads is probably not correct.
            //
            // See https://gist.github.com/ethanhs/fd4123487974c91c7e5960acc9aa2a77
            fn __setstate__(&mut self, py: Python, state: PyObject) -> PyResult<()> {
                state.extract::<&PyBytes>(py).map(|bytes| {
                    let mut buf: [u8; 16] = Default::default();
                    buf.copy_from_slice(bytes.as_bytes());
                    self.inner = RustDecimal::deserialize(buf)
                })
            }

            fn __getstate__(&mut self, py: Python) -> PyResult<PyObject> {
                Ok(PyBytes::new(py, &self.inner.serialize()).to_object(py))
            }
            // ######################################################################

            fn __repr__(&self) -> String {
                format!("{:?}", self)
            }

            fn __str__(&self) -> String {
                self.inner.to_string()
            }

            fn __richcmp__(&self, other: &PyAny, op: CompareOp) -> PyResult<bool> {
                let other = Self::try_from(other)?;
                Ok(match op {
                    CompareOp::Lt => *self < other,
                    CompareOp::Le => *self <= other,
                    CompareOp::Eq => *self == other,
                    CompareOp::Ne => *self != other,
                    CompareOp::Gt => *self > other,
                    CompareOp::Ge => *self >= other,
                })
            }

            fn __hash__(&self) -> u64 {
                let bytes = self.inner.normalize().serialize();
                let mut buf: [u8; 8] = Default::default();
                for i in 0..8 {
                    buf[i] = bytes[i] ^ bytes[i + 8];
                }
                u64::from_be_bytes(buf)
            }

            fn __add__(&self, other: &PyAny) -> PyResult<Self> {
                let other = Self::try_from(other)?;
                if let Some(res) = self.inner.checked_add(other.inner) {
                    Ok(res.into())
                } else {
                    Err(DecimalError::new_err(CHECKED_OP_ERROR))
                }
            }

            fn __radd__(&self, other: &PyAny) -> PyResult<Self> {
                self.__add__(other)
            }

            fn __sub__(&self, other: &PyAny) -> PyResult<Self> {
                let other = Self::try_from(other)?;
                if let Some(res) = self.inner.checked_sub(other.inner) {
                    Ok(res.into())
                } else {
                    Err(DecimalError::new_err(CHECKED_OP_ERROR))
                }
            }

            fn __rsub__(&self, other: &PyAny) -> PyResult<Self> {
                let other = Self::try_from(other)?;
                if let Some(res) = other.inner.checked_sub(self.inner) {
                    Ok(res.into())
                } else {
                    Err(DecimalError::new_err(CHECKED_OP_ERROR))
                }
            }

            fn __mul__(&self, other: &PyAny) -> PyResult<Self> {
                let other = Self::try_from(other)?;
                if let Some(res) = self.inner.checked_mul(other.inner) {
                    Ok(res.into())
                } else {
                    Err(DecimalError::new_err(CHECKED_OP_ERROR))
                }
            }

            fn __rmul__(&self, other: &PyAny) -> PyResult<Self> {
                self.__mul__(other)
            }

            fn __truediv__(&self, other: &PyAny) -> PyResult<Self> {
                let other = Self::try_from(other)?;
                if let Some(res) = self.inner.checked_div(other.inner) {
                    Ok(res.into())
                } else {
                    Err(DecimalError::new_err(CHECKED_OP_ERROR))
                }
            }

            fn __rtruediv__(&self, other: &PyAny) -> PyResult<Self> {
                let other = Self::try_from(other)?;
                if let Some(res) = other.inner.checked_div(self.inner) {
                    Ok(res.into())
                } else {
                    Err(DecimalError::new_err(CHECKED_OP_ERROR))
                }
            }

            fn __mod__(&self, other: &PyAny) -> PyResult<Self> {
                let other = Self::try_from(other)?;
                if let Some(res) = self.inner.checked_rem(other.inner) {
                    Ok(res.into())
                } else {
                    Err(DecimalError::new_err(CHECKED_OP_ERROR))
                }
            }

            fn __rmod__(&self, other: &PyAny) -> PyResult<Self> {
                let other = Self::try_from(other)?;
                if let Some(res) = other.inner.checked_rem(self.inner) {
                    Ok(res.into())
                } else {
                    Err(DecimalError::new_err(CHECKED_OP_ERROR))
                }
            }

            fn __pow__(&self, other: &PyAny, _modulo: &PyAny) -> PyResult<Self> {
                let other = Self::try_from(other)?;
                if let Some(res) = self.inner.checked_powd(other.inner) {
                    Ok(res.into())
                } else {
                    Err(DecimalError::new_err(CHECKED_OP_ERROR))
                }
            }

            fn __rpow__(&self, other: &PyAny, _modulo: &PyAny) -> PyResult<Self> {
                let other = Self::try_from(other)?;
                if let Some(res) = other.inner.checked_powd(self.inner) {
                    Ok(res.into())
                } else {
                    Err(DecimalError::new_err(CHECKED_OP_ERROR))
                }
            }

            fn __neg__(&self) -> Self {
                self.inner.neg().into()
            }

            fn __abs__(&self) -> Self {
                self.inner.abs().into()
            }

            fn __int__(&self) -> PyResult<i128> {
                self.inner
                    .round_dp_with_strategy(0, RoundingStrategy::ToZero)
                    .to_i128()
                    .ok_or_else(|| DecimalError::new_err("Couldn't cast to int"))
            }

            fn __float__(&self) -> PyResult<f64> {
                self.inner
                    .to_f64()
                    .ok_or_else(|| DecimalError::new_err("Couldn't cast to float"))
            }
        }

        impl From<RustDecimal> for Decimal {
            fn from(item: RustDecimal) -> Decimal {
                Decimal { inner: item }
            }
        }

        impl From<Decimal> for RustDecimal {
            fn from(item: Decimal) -> RustDecimal {
                item.inner
            }
        }

        impl From<Decimal> for UnscaledI128 {
            fn from(item: Decimal) -> UnscaledI128 {
                item.inner.into()
            }
        }

        impl TryFrom<String> for Decimal {
            type Error = PyErr;
            fn try_from(value: String) -> Result<Decimal, PyErr> {
                if let Ok(val) = RustDecimal::from_str(&value) {
                    Ok(val.into())
                } else if let Ok(val) = RustDecimal::from_scientific(&value) {
                    Ok(val.into())
                } else {
                    Err(DecimalError::new_err("Invalid value for decimal"))
                }
            }
        }

        impl TryFrom<f64> for Decimal {
            type Error = PyErr;
            fn try_from(value: f64) -> Result<Decimal, PyErr> {
                Ok(RustDecimal::try_from(value)
                    .map_err(|_| DecimalError::new_err("Invalid value for decimal"))?
                    .into())
            }
        }

        impl TryFrom<&PyAny> for Decimal {
            type Error = PyErr;
            fn try_from(val: &PyAny) -> PyResult<Self> {
                if let Ok(dec) = val.extract::<Self>() {
                    Ok(dec)
                } else if let Ok(string) = val.extract::<String>() {
                    Self::try_from(string)
                } else if let Ok(int) = val.extract::<i128>() {
                    Ok(RustDecimal::from(int).into())
                } else if let Ok(float) = val.extract::<f64>() {
                    Self::try_from(float)
                } else {
                    Err(DecimalError::new_err("invalid value for decimal"))
                }
            }
        }
    }
}

/// Holds a monetary amount (i.e. unscaled token amount) for storage
///
/// In blockchains, currency and token amounts are defined as "units".
/// A unit is an unsigned integer generally scaled by 10**6 (some tokens have a smaller scale).
/// We care about token units because blockchains are the verification layer for our storage.
/// Wrapping a `Decimal` in this type normalizes it to the scale's precision.
///
/// For simplicity, we standardize all tokens to a 10**6 scale internally, blockchain verifiers
/// must scale up their internal amounts as needed.
///
/// To perform calculations, use the inner `Decimal` directly. Then, convert the result into
/// this type for storage. This should work for all calculations and prevent any manual rounding.
#[derive(Clone, Copy, Default, Debug, PartialEq, Serialize, Deserialize, Eq)]
#[serde(transparent)]
#[repr(transparent)]
pub struct UnscaledI128(Decimal);

#[cfg(feature = "python")]
impl FromPyObject<'_> for UnscaledI128 {
    fn extract(ob: &PyAny) -> PyResult<Self> {
        Ok(Self::new(exported::python::Decimal::try_from(ob)?.into()))
    }
}

#[cfg(feature = "python")]
impl IntoPy<PyObject> for UnscaledI128 {
    fn into_py(self, py: Python) -> PyObject {
        exported::python::Decimal::from(self.0).into_py(py)
    }
}

impl UnscaledI128 {
    pub const ZERO: UnscaledI128 = UnscaledI128(Decimal::ZERO);

    pub fn new(value: Decimal) -> Self {
        // If Decimal value is too large, can't be converted freely between U128 and Decimal
        // UnscaledI128 is bounded by the largest unscaled decimal that would not cause overflow after scaling
        let mut num = value;
        if value > MAX_UNSCALED_DECIMAL {
            tracing::trace!(
                "{:?} would cause overflow when scaling and then unscaling",
                value
            );
            num = MAX_UNSCALED_DECIMAL;
        }
        Self(
            num.round_dp_with_strategy(TOKEN_UNIT_SCALE, RoundingStrategy::ToZero)
                .normalize(),
        )
    }

    pub fn is_zero(&self) -> bool {
        self.0.is_zero()
    }

    /// The sign of the decimal number can be negative even if the value is zero.
    /// The value of the decimal is not necessary less than zero.
    pub fn is_sign_negative(&self) -> bool {
        self.0.is_sign_negative()
    }

    /// The sign of the decimal number can be positive even if the value is zero
    /// The value of the decimal is not necessary greater than zero.
    pub fn is_sign_positive(&self) -> bool {
        self.0.is_sign_positive()
    }

    /// Checks if this unscaled number can be scaled into u128 with TOKEN_UNIT_SCALE
    ///
    /// Use only when a defensive approach is absolutely necessary (with external inputs).
    fn can_scale(&self) -> bool {
        self.0.abs() <= MAX_UNSCALED_DECIMAL
    }
}

impl std::fmt::Display for UnscaledI128 {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl AsRef<Decimal> for UnscaledI128 {
    fn as_ref(&self) -> &Decimal {
        &self.0
    }
}

impl Deref for UnscaledI128 {
    type Target = Decimal;

    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

// Calculated from Decimal::MAX display length
const MAX_DECIMAL_LEN: usize = 29;

lazy_static! {
    static ref DECIMAL_RE: Regex =
        Regex::new(r"[+-]?((?P<whole>\d+)?(?P<dot>[.]))?(?P<decimal>\d+)")
            .expect("Invalid decimal validation pattern");
}

impl FromStr for UnscaledI128 {
    type Err = Error;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let cap = DECIMAL_RE
            .captures(s)
            .ok_or_else(|| Error::Parse(format!("Invalid decimal string: {}", s)))?;
        // Run basic heuristics on the regex captures before attempting any parsing.
        let whole;
        let fract;
        // Case: 1234.4444
        if let Some(whole_) = cap.name("whole") {
            whole = whole_.as_str();
            fract = &cap["decimal"];
        // Case: .4444
        } else if let Some(_dot) = cap.name("dot") {
            whole = "";
            fract = &cap["decimal"];
        // Case: 1234
        } else {
            whole = &cap["decimal"];
            fract = "";
        }
        // Using TOKEN_UNIT_SCALE instead of DEFAULT_CURRENCY_DECIMAL_PRECISION because we're using JSON for more than just `ClientRequest`.
        ensure!(
            fract.len() <= TOKEN_UNIT_SCALE as usize,
            "Too many numbers after the decimal len({}) > {}",
            fract,
            TOKEN_UNIT_SCALE
        );
        // Effectively reducing the Decimal capacity, which is fine here since our internal threshold is lower.
        ensure!(
            whole.len() < MAX_DECIMAL_LEN,
            "Preventing Decimal overflow len({}) > {}",
            whole,
            MAX_DECIMAL_LEN
        );
        let d: UnscaledI128 =
            (Decimal::from_str(s).map_err(|e| Error::Parse(format!("{}, s = {}", e, s)))?).into();
        // Defensively assuming that parsing strings always involves foreign inputs.
        // This is why we should use CBOR, never JSON, to serialize data between trusted and untrusted context.
        ensure!(
            d.can_scale(),
            "Preventing U128 scaling overflow {} > {}",
            d,
            MAX_UNSCALED_DECIMAL
        );
        Ok(d)
    }
}

impl TryFrom<serde_json::Value> for UnscaledI128 {
    type Error = Error;

    fn try_from(value: serde_json::Value) -> Result<Self, Self::Error> {
        // Defend against overflow with strings only because `u64::MAX < Decimal::MAX`.
        if let Some(s) = value.as_str() {
            Ok(s.parse()?)
        } else if let Some(n) = value.as_f64() {
            Ok(
                // Parsing by leveraging float guarantees. i.e. 0.1_f64 => 0.1
                (Decimal::from_f64(n)
                    .ok_or_else(|| Error::Parse(format!("Unable to parse float: {}", n)))?)
                .into(),
            )
        } else if let Some(n) = value.as_i64() {
            Ok(Decimal::from(n).into())
        } else if let Some(n) = value.as_u64() {
            Ok(Decimal::from(n).into())
        } else {
            Err(Error::Parse(format!(
                "Expected either a string or number, got {:?}",
                value
            )))
        }
    }
}

impl Tokenizable for UnscaledI128 {
    fn from_token(token: DynSolValue) -> Result<Self> {
        let scaled_int = I128::from_token(token)?;
        Ok(scaled_int.into())
    }
    fn into_token(self) -> DynSolValue {
        let scaled_int = I128::from(self);
        scaled_int.into_token()
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for UnscaledI128 {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        Decimal::try_new(i64::arbitrary(g), TOKEN_UNIT_SCALE)
            .unwrap_or(Decimal::MAX)
            .into()
    }
}

#[cfg(feature = "database")]
impl ToSql for UnscaledI128 {
    fn to_sql(
        &self,
        ty: &Type,
        out: &mut bytes::BytesMut,
    ) -> Result<IsNull, Box<dyn std::error::Error + 'static + Sync + Send>> {
        self.0.to_sql(ty, out)
    }

    fn accepts(ty: &Type) -> bool {
        matches!(*ty, Type::NUMERIC)
    }

    to_sql_checked!();
}

#[cfg(feature = "database")]
impl<'a> FromSql<'a> for UnscaledI128 {
    fn from_sql(
        ty: &Type,
        raw: &'a [u8],
    ) -> Result<Self, Box<dyn std::error::Error + Sync + Send>> {
        let dec = Decimal::from_sql(ty, raw)?;
        Ok(UnscaledI128::from(dec))
    }

    fn accepts(ty: &Type) -> bool {
        matches!(*ty, Type::NUMERIC)
    }
}

impl<T: Into<UnscaledI128> + Copy> From<&T> for UnscaledI128 {
    fn from(value: &T) -> Self {
        (*value).into()
    }
}

/// We don't need `TryFrom` even though `U128` could overflow because `TryFrom<Value>`
/// validates MIN and MAX bounds for all external inputs.
impl From<U128> for UnscaledI128 {
    fn from(value: U128) -> Self {
        tracing::trace!("{:?} - Into {:?} Decimal", value, TOKEN_UNIT_SCALE);
        // Check if the value is larger than the maximum decimal value
        let u = value.to::<u128>();
        if u > Decimal::MAX.to_u128().unwrap() {
            return UnscaledI128::new(MAX_UNSCALED_DECIMAL);
        }
        // This conversion will not panic because u is bounded by Decimal::MAX
        let dec = Decimal::from_i128_with_scale(u as i128, TOKEN_UNIT_SCALE);
        UnscaledI128::new(dec)
    }
}

impl From<U256> for UnscaledI128 {
    fn from(value: U256) -> Self {
        UnscaledI128::from(value.to::<U128>())
    }
}

impl From<UnscaledI128> for U128 {
    fn from(value: UnscaledI128) -> Self {
        let value = value.0;
        // No rounding needed because this type guarantees rounding of the inner decimal.
        if value.is_zero() {
            return U128::ZERO;
        }
        assert!(
            value.is_sign_positive(),
            "Negatives don't scale into unsigned: {:?}",
            value
        );
        // Scale the decimal value
        let mut num = value;
        let scale = value.scale();
        num.set_scale(0).expect("scale 0");
        tracing::trace!("Converted to unscale: {:?}", num);
        // Now that we have a round number we can cast our U128
        // We can unwrap the u128 conversion because UnscaledI128 is at maximum, the largest Decimal that can be scaled, which is far smaller than max u128.
        let u_num = U128::from(num.to_u128().unwrap());
        // Apply the remaining exponent to the number without fear of overflow
        u_num * U128::from(10).pow(U128::from(TOKEN_UNIT_SCALE - scale))
    }
}

impl From<UnscaledI128> for U256 {
    fn from(value: UnscaledI128) -> Self {
        let num: U128 = value.into();
        num.to()
    }
}

impl From<I128> for UnscaledI128 {
    fn from(value: I128) -> Self {
        let mut num = UnscaledI128::from(value.abs).0;
        num.set_sign_negative(value.negative_sign);
        UnscaledI128::new(num)
    }
}

impl From<UnscaledI128> for I128 {
    fn from(value: UnscaledI128) -> Self {
        // No rounding needed because this type guarantees rounding of the inner decimal.
        let negative_sign = value.0.is_sign_negative();
        let abs = UnscaledI128::new(value.0.abs()).into();
        I128 { negative_sign, abs }
    }
}

impl From<Decimal> for UnscaledI128 {
    fn from(value: Decimal) -> Self {
        UnscaledI128::new(value)
    }
}

impl From<UnscaledI128> for Decimal {
    fn from(value: UnscaledI128) -> Self {
        value.0
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use core_macros::unscaled;
    use rand::{Rng, thread_rng};
    use rust_decimal::Decimal;

    #[test]
    fn test_price_conversion() {
        let ref_price = unscaled!(250.9988);
        let unit_price: U128 = ref_price.into();
        assert_eq!(
            U128::from(2509988) * U128::from(10).pow(U128::from(2)),
            unit_price
        );
        let price: UnscaledI128 = unit_price.into();
        assert_eq!(price, ref_price);
    }

    #[test]
    fn test_decimal() {
        let num = 2509988;
        let scale = 4;
        let num_unscaled = UnscaledI128::from(Decimal::new(num, scale));
        let unit_price: U128 = num_unscaled.into();
        assert_eq!(
            U128::from(num) * U128::from(10).pow(U128::from((TOKEN_UNIT_SCALE - scale) as usize)),
            unit_price
        );
        let price = UnscaledI128::from(unit_price);
        assert_eq!(price, num_unscaled);
    }

    #[test]
    fn test_prec() {
        let bankruptcy_px = Decimal::from_i128_with_scale(31297995110653628409675759135, 27);
        let avg_entry_px = Decimal::from_i128_with_scale(95631500, TOKEN_UNIT_SCALE);
        let match_token_amount = Decimal::from_i128_with_scale(15544000, TOKEN_UNIT_SCALE);
        let amount_to_debit = match_token_amount * (avg_entry_px - bankruptcy_px);
        let target_amount_to_debit = Decimal::from_i128_with_scale(1000, 0);
        assert_eq!(amount_to_debit, target_amount_to_debit);

        let balance = Decimal::from_i128_with_scale(97027007928, 8);
        let new_balance = UnscaledI128::new(balance + amount_to_debit);
        let target_new_balance = UnscaledI128::new(Decimal::from_i128_with_scale(197027007928, 8));
        assert_eq!(new_balance, target_new_balance);
    }

    #[test]
    fn test_decimal_mul() {
        for _ in 0..1000 {
            let multiplier = thread_rng().gen_range(100..1000);
            let num = thread_rng().gen_range(25000000000..99999999999);
            let scale = thread_rng().gen_range(2..5);
            let num_uint = U256::from(num) * U256::from(10).pow(U256::from(6 - scale as usize));
            let multiplier_uint = U256::from(multiplier) * U256::from(10).pow(U256::from(6));
            let mul = (num_uint * multiplier_uint) / U256::from(10).pow(U256::from(6));
            let result_uint = mul.to::<U128>();
            let result = UnscaledI128::new(Decimal::new(num, scale) * Decimal::from(multiplier));
            assert_eq!(result_uint, Into::<U128>::into(result));
            assert_eq!(result, UnscaledI128::from(result_uint));
        }
    }

    #[test]
    fn test_decimal_division() {
        for _ in 0..1000 {
            let divider = thread_rng().gen_range(100..1000);
            let num = thread_rng().gen_range(25000000000..99999999999);
            let scale = 4;
            let num_uint = U128::from(num) * U128::from(10).pow(U128::from(6 - scale as usize));
            let divider_uint = U128::from(divider);
            let result_uint = num_uint / divider_uint;
            tracing::trace!(
                "U128:  {:?} / {:?} = {:?}",
                num_uint,
                divider_uint,
                result_uint
            );
            let result = UnscaledI128::from(Decimal::new(num, scale) / (Decimal::from(divider)));
            tracing::trace!(
                "Decimal {:?} / {:?} = {:?}",
                Decimal::new(num, scale),
                Decimal::from(divider),
                result
            );
            assert_eq!(result_uint, Into::<U128>::into(result));
            assert_eq!(result, UnscaledI128::from(result_uint));
        }
    }
}
