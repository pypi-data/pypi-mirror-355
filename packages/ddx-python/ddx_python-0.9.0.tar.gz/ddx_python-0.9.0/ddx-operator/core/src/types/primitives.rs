use crate::util::serde::{as_product_symbol, as_underlying_symbol};
use alloy_dyn_abi::DynSolValue;
use alloy_primitives::FixedBytes;
use bitvec::{
    prelude::{BitSlice, Lsb0},
    vec::BitVec,
};
#[cfg(feature = "arbitrary")]
use core_common::types::primitives::arbitrary_b256;
use core_common::{
    B256, Error, Result, ensure,
    types::primitives::{Bytes32, Hash},
    util::tokenize::Tokenizable,
};
use core_macros::FixedBytesWrapper;
use core_specs::eval::Atom;
#[cfg(feature = "database")]
use postgres_types::{FromSql, IsNull, ToSql, Type, to_sql_checked};
#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "arbitrary")]
use quickcheck::Arbitrary;
use rustc_hex::ToHex;
use serde::{Deserialize, Serialize};
use std::{
    fmt::{self, Formatter},
    mem::size_of,
    str::{FromStr, from_utf8},
};

const SYMBOL_CHARSET: &str = "0ABCDEFGHIJKLMNOPQRSTUVWXYZ";

// Aliasing commonly used primitives for business context.
pub type OrderHash = Bytes25;
pub type IndexPriceHash = Bytes25;

/// Symbol of the underlying asset, usually a spot market symbol
///
/// This holds 4 bytes representing ASCII characters. If the symbol is shorter than 4 bytes, it is
/// is suffix padded with zeros.
///
/// There's no imperative to pack the underlying symbol bytes like with the product symbol, so we don't.
#[derive(
    Clone, Copy, Default, PartialEq, Eq, std::hash::Hash, PartialOrd, Ord, Deserialize, Serialize,
)]
pub struct UnderlyingSymbol(#[serde(with = "as_underlying_symbol")] pub(crate) [u8; 4]);

#[cfg(feature = "python")]
impl FromPyObject<'_> for UnderlyingSymbol {
    fn extract(ob: &PyAny) -> PyResult<Self> {
        let string: String = ob.extract()?;
        Ok(string.parse()?)
    }
}

#[cfg(feature = "python")]
impl IntoPy<PyObject> for UnderlyingSymbol {
    fn into_py(self, py: Python) -> PyObject {
        self.to_string().into_py(py)
    }
}

impl FromStr for UnderlyingSymbol {
    type Err = Error;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        UnderlyingSymbol::from_ascii_bytes(s.as_bytes())
    }
}

impl From<&str> for UnderlyingSymbol {
    fn from(value: &str) -> Self {
        value.parse().unwrap()
    }
}

impl fmt::Display for UnderlyingSymbol {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        write!(f, "{}", from_utf8(self.trim()).unwrap())
    }
}

impl fmt::Debug for UnderlyingSymbol {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_tuple("UnderlyingSymbol")
            .field(&self.to_string())
            .finish()
    }
}

impl Tokenizable for UnderlyingSymbol {
    fn from_token(token: DynSolValue) -> Result<Self> {
        let text = Bytes32::from_token(token)?.to_string();
        text.parse()
    }
    fn into_token(self) -> DynSolValue {
        let bytes = Bytes32::from(self);
        bytes.into_token()
    }
}

impl From<UnderlyingSymbol> for Bytes32 {
    fn from(value: UnderlyingSymbol) -> Self {
        // Delegate the conversion to the string type
        // Can't fail because we know that the length fits in 32 bytes
        value.to_string().parse().unwrap()
    }
}

impl UnderlyingSymbol {
    pub const BYTE_LEN: usize = size_of::<Self>();

    /// Return a ASCII bytes slice excluding whitespace
    pub(super) fn trim(&self) -> &[u8] {
        self.0.trim_ascii_end()
    }

    /// Tries to encode the given ASCII bytes into the 4 byte symbol convention
    ///
    /// This means ending with whitespace if needed and validating against the character subset.
    #[tracing::instrument(level = "trace", fields(text=?from_utf8(ascii_bytes)))]
    pub(crate) fn from_ascii_bytes(ascii_bytes: &[u8]) -> Result<Self> {
        if ascii_bytes.len() > Self::BYTE_LEN {
            return Err(Error::Parse(format!(
                "Expected up to {} ASCII characters for underlying symbol; got {:?}",
                Self::BYTE_LEN,
                from_utf8(ascii_bytes)
            )));
        }
        let mut bytes = [0_u8; Self::BYTE_LEN];
        for i in 0..bytes.len() {
            if i < ascii_bytes.trim_ascii_end().len() {
                // Allows the type system to guarantee that this is usable as the root of `ProductSymbol`.
                if !SYMBOL_CHARSET.contains(ascii_bytes[i] as char) {
                    return Err(Error::Conversion(format!(
                        "Illegal character in {} charset={}",
                        ascii_bytes[i], SYMBOL_CHARSET
                    )));
                }
                bytes[i] = ascii_bytes[i];
            } else {
                bytes[i] = 32;
            }
        }
        Ok(UnderlyingSymbol(bytes))
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for UnderlyingSymbol {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        let sizes = (2..4).collect::<Vec<i32>>();
        let size = *g.choose(&sizes).unwrap();
        let symbol: String = (0..size)
            .map(|_| {
                // FIXME: Revisit the inclusion of '0' in the charset
                let charset = SYMBOL_CHARSET
                    .chars()
                    .filter(|c| c != &'0')
                    .collect::<Vec<char>>();
                g.choose(&charset).cloned().unwrap()
            })
            .collect();
        symbol.parse().unwrap()
    }
}

impl TryFrom<Atom> for UnderlyingSymbol {
    type Error = Error;

    fn try_from(value: Atom) -> Result<Self, Self::Error> {
        if let Atom::Str(v) = value {
            Ok(v.as_str().into())
        } else {
            Err(core_common::error!("Wrong type {:?}", value))
        }
    }
}

/// The kinds of derivative products that can be traded on the exchange
#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize, Serialize)]
#[non_exhaustive]
pub enum Product {
    Perpetual,
    #[cfg(feature = "fixed_expiry_future")]
    QuarterlyExpiryFuture {
        month_code: char,
    },
}

impl fmt::Display for Product {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{}",
            match self {
                Product::Perpetual => "P".to_string(),
                #[cfg(feature = "fixed_expiry_future")]
                Product::QuarterlyExpiryFuture { month_code } => format!("F{}", month_code),
            }
        )
    }
}

impl Product {
    pub const BYTE_LEN: usize = 3;

    fn split(&self) -> (char, Option<char>) {
        match self {
            Product::Perpetual => ('P', None),
            #[cfg(feature = "fixed_expiry_future")]
            Product::QuarterlyExpiryFuture { month_code } => ('F', Some(*month_code)),
        }
    }

    fn from_fixed_bytes(bytes: [u8; Self::BYTE_LEN]) -> Result<Product> {
        let kind = bytes[0];
        match kind {
            b'P' => Ok(Product::Perpetual),
            #[cfg(feature = "fixed_expiry_future")]
            b'F' => {
                let month_code = bytes[1] as char;
                Ok(Product::QuarterlyExpiryFuture { month_code })
            }
            _ => Err(Error::Parse(format!("Unknown product kind {}", kind))),
        }
    }

    /// Tries to construct a Product from the given ASCII bytes
    #[tracing::instrument(level = "debug", fields(text=?from_utf8(ascii_bytes)))]
    fn from_ascii_bytes(ascii_bytes: &[u8]) -> Result<Self> {
        let kind = ascii_bytes.first().ok_or_else(|| {
            Error::Parse(format!(
                "Expected at least 1 ASCII character for underlying symbol; got {:?}",
                from_utf8(ascii_bytes)
            ))
        })?;
        match kind {
            b'P' => Ok(Product::Perpetual),
            #[cfg(feature = "fixed_expiry_future")]
            b'F' => {
                let month_code = ascii_bytes
                    .get(1)
                    .ok_or_else(|| {
                        Error::Parse(format!(
                            "Expected more characters to represent days until expiry, got {:?}",
                            from_utf8(ascii_bytes)
                        ))
                    })
                    .and_then(|&params| {
                        from_utf8(&[params])
                            .map_err(|_| Error::Parse("Expected a utf8 string".to_string()))
                            .map(|params| params.chars().next().unwrap())
                    })?;
                Ok(Product::QuarterlyExpiryFuture { month_code })
            }
            _ => Err(Error::Parse(format!("Unknown product kind {}", kind))),
        }
    }
}

/// Symbol of a product (derivative contract) traded on the exchange
///
/// This symbol is packed into 6 bytes using a custom "5-bit scheme" to adhere to space limitation.
///
/// When unpacked into regular ASCII, the first 3-4 bytes are the root (underlying symbol) followed by one character for the product kind.
/// For example, the symbol for a perpetual contract on BTC would be `BTCP`.
///
/// Some products, like options, may additional digits to reference externally defined attributes like strike price and date.
#[derive(Clone, Copy, PartialEq, Eq, std::hash::Hash, PartialOrd, Ord, Deserialize, Serialize)]
pub struct ProductSymbol(#[serde(with = "as_product_symbol")] pub [u8; 6]);

// TODO: this should be feature gated behind development
impl Default for ProductSymbol {
    fn default() -> Self {
        "ETHP".into()
    }
}

#[cfg(feature = "python")]
impl FromPyObject<'_> for ProductSymbol {
    fn extract(ob: &PyAny) -> PyResult<Self> {
        let str_repr = if let Ok(symbol) =
            ob.extract::<crate::types::state::exported::python::ProductSymbol>()
        {
            symbol.to_string()
        } else {
            ob.extract::<String>()?
        };
        Ok(Self::from_str(&str_repr)?)
    }
}

#[cfg(feature = "python")]
impl IntoPy<PyObject> for ProductSymbol {
    fn into_py(self, py: Python) -> PyObject {
        crate::types::state::exported::python::ProductSymbol::from(self).into_py(py)
    }
}

impl ProductSymbol {
    pub const BYTE_LEN: usize = size_of::<Self>();
    // Collect ASCII bytes from the parts; currently limited to 5 bytes but this will change we define more products.
    const ASCII_LEN: usize = 5;

    #[cfg(feature = "arbitrary")]
    pub(super) fn new(underlying: UnderlyingSymbol, product: Product) -> Self {
        ProductSymbol(ProductSymbol::pack_bytes(underlying, product))
    }

    pub fn product(&self) -> Product {
        self.split().1
    }

    /// Parse the parts (underlying symbol and product) from the given ASCII string
    ///
    /// This avoids unnecessarily encoding and decoding an intermediary product symbol.
    #[tracing::instrument(level = "trace")]
    pub(crate) fn parse_parts(text: &str) -> Result<(UnderlyingSymbol, Product)> {
        if text.len() < 2 {
            return Err(Error::Parse(
                "Expected at least 2 characters for product symbol".to_string(),
            ));
        }

        // Find either "P" or "F" from the back
        let product_start_index = text.len()
            - (text
                .chars()
                .rev()
                .position(|c| c == 'P' || c == 'F')
                .ok_or_else(|| {
                    Error::Parse("Expected a character representing the product type".to_string())
                })?
                + 1);

        let bytes = text.as_bytes();
        let u_bytes = &bytes[..product_start_index];
        let p_bytes = &bytes[product_start_index..];
        Ok((
            UnderlyingSymbol::from_ascii_bytes(u_bytes)?,
            Product::from_ascii_bytes(p_bytes)?,
        ))
    }

    /// Convert to ASCII bytes then extract the underlying symbol and product
    pub(crate) fn split(&self) -> (UnderlyingSymbol, Product) {
        // TODO: Split this fn to return a slice of ascii bytes instead of a String
        ProductSymbol::unpack_bytes(&self.0)
            .and_then(|t| ProductSymbol::parse_parts(&t))
            .expect("Unpacking bytes from a ProductSymbol should never fail")
    }

    #[cfg(not(target_family = "wasm"))]
    /// Try to create from a bytes slice packed with the 5-bit scheme
    pub(super) fn from_slice(bytes: &[u8]) -> Result<Self> {
        debug_assert_eq!(
            bytes.len(),
            Self::BYTE_LEN,
            "Expected symbol size to be 6 bytes"
        );
        let mut fixed_bytes = [0_u8; Self::BYTE_LEN];
        fixed_bytes.copy_from_slice(bytes);
        ProductSymbol::try_from(&fixed_bytes)
    }

    /// Slice of inner 5-bit scheme bytes
    pub fn as_bytes(&self) -> &[u8] {
        self.0.as_slice()
    }

    /// Pack the symbol text into our 5-bit custom scheme
    ///
    /// We pack 5-bit chars instead of ASCII because 6 bytes is the maximum size we can afford
    /// to use symbol in our cryptography without resorting to a one-way hash.
    #[tracing::instrument(level = "trace")]
    pub(crate) fn pack_bytes(
        underlying: UnderlyingSymbol,
        product: Product,
    ) -> [u8; Self::BYTE_LEN] {
        let mut ascii_buf = [0_u8; Self::ASCII_LEN];
        let u_bytes = underlying.trim();
        for i in 0..ascii_buf.len() {
            if i < u_bytes.len() {
                ascii_buf[i] = u_bytes[i];
            } else {
                ascii_buf[i] = 32;
            }
        }
        let (t, params) = product.split();
        ascii_buf[u_bytes.len()] = t as u8;

        let mut symbol_bits: BitVec<Lsb0, u8> = BitVec::new();
        for c in ascii_buf.trim_ascii_end().iter().map(|&b| b as char) {
            let mut is_valid_char = false;
            for (i, sc) in SYMBOL_CHARSET.chars().enumerate() {
                if sc == c {
                    let index = i as u8;
                    // Forcing least significant bit ordering to know where to slice
                    let bits = BitSlice::<Lsb0, u8>::from_element(&index);
                    // Our charset index fits in 5-bit so we only keep the first five
                    // This restricts our charset to max 32 chars (enough for alpha symbols)
                    symbol_bits.extend_from_bitslice(&bits[..5]);
                    is_valid_char = true;
                    break;
                }
            }
            debug_assert!(
                is_valid_char,
                "Illegal char {} charset={}",
                c, SYMBOL_CHARSET
            );
        }
        // Pack concatenated bits into a vector of bytes
        let mut bytes: Vec<u8> = symbol_bits.into_vec();
        debug_assert!(
            bytes.len() <= 4,
            "Expected the symbol to unpack into 4 bytes > 5 * 5 / 8 or less but found {:?} bytes",
            bytes.len()
        );
        bytes.resize(Self::BYTE_LEN, 0_u8);
        let mut fixed_bytes = [0_u8; Self::BYTE_LEN];
        fixed_bytes.copy_from_slice(&bytes);
        if let Some(params) = params {
            fixed_bytes[4] = params as u8;
        }
        fixed_bytes
    }

    /// Decode the symbol fixed bytes by unpacking 5-bit char into ASCII
    pub fn unpack_bytes(fixed_bytes: &[u8; Self::BYTE_LEN]) -> Result<String> {
        // Not sure why we have this
        // if fixed_bytes == &[0_u8; Self::BYTE_LEN] {
        //     return Ok("".to_string());
        // }

        let encoded_bits =
            BitVec::<Lsb0, u8>::from_vec(fixed_bytes[..UnderlyingSymbol::BYTE_LEN].to_vec());
        let mut symbol = String::new();
        // Group into 5-bit chunks each containing an encoded char
        for char_bits_ in encoded_bits.chunks_exact(5) {
            // Resizing our 5-bit encoded char to a byte to compare with our charset
            let mut char_bits = char_bits_.to_bitvec();
            char_bits.resize(8, false);
            let mut is_valid_char = false;
            for (i, c) in SYMBOL_CHARSET.chars().enumerate() {
                let index = i as u8; // Can't non-deterministically fail with our own charset
                let bits = BitSlice::<Lsb0, u8>::from_element(&index);
                if char_bits == bits {
                    // Trimming zero padding chars
                    if i > 0 {
                        symbol.push(c);
                    }
                    is_valid_char = true;
                    break;
                }
            }
            ensure!(
                is_valid_char,
                "Illegal characters packed in {:?} charset={}",
                fixed_bytes,
                SYMBOL_CHARSET
            );
        }
        let mut product_bytes = [0u8; Product::BYTE_LEN];
        product_bytes[0] = symbol.pop().expect("Expected a trailing product char") as u8;
        product_bytes[1..].copy_from_slice(&fixed_bytes[UnderlyingSymbol::BYTE_LEN..]);
        let product = Product::from_fixed_bytes(product_bytes)?;
        Ok(format!("{}{}", symbol, product))
    }
}

impl Tokenizable for ProductSymbol {
    fn from_token(token: DynSolValue) -> Result<Self>
    where
        Self: Sized,
    {
        let text = Bytes32::from_token(token)?.to_string();
        text.parse()
    }

    fn into_token(self) -> DynSolValue {
        let bytes = Bytes32::from(self);
        bytes.into_token()
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for ProductSymbol {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        let root = UnderlyingSymbol::arbitrary(g);
        ProductSymbol::new(root, Product::Perpetual)
    }
}

impl FromStr for ProductSymbol {
    type Err = Error;

    /// Parse by encoding symbol text into the 5-bit internal representation
    fn from_str(value: &str) -> Result<Self, Self::Err> {
        let (s, p) = ProductSymbol::parse_parts(value)?;
        let bytes = ProductSymbol::pack_bytes(s, p);
        Ok(ProductSymbol(bytes))
    }
}

impl From<ProductSymbol> for UnderlyingSymbol {
    fn from(value: ProductSymbol) -> Self {
        value.split().0
    }
}

// TODO: Restrict usage to development and testing only
impl From<&str> for ProductSymbol {
    fn from(value: &str) -> Self {
        value.parse().unwrap()
    }
}

impl From<String> for ProductSymbol {
    fn from(val: String) -> Self {
        val.as_str().into()
    }
}

impl TryFrom<&[u8; 6]> for ProductSymbol {
    type Error = Error;

    fn try_from(value: &[u8; 6]) -> Result<Self> {
        // Unpack the bytes to ensure they all match the charset
        let _ = ProductSymbol::unpack_bytes(value)?;
        Ok(ProductSymbol(*value))
    }
}

// Also implements `ToString` for free
impl fmt::Display for ProductSymbol {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        // Can't non-deterministically fail to unpack our validated bytes
        write!(f, "{}", ProductSymbol::unpack_bytes(&self.0).unwrap())
    }
}

impl fmt::Debug for ProductSymbol {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_tuple("ProductSymbol")
            .field(&self.to_string())
            .finish()
    }
}

impl From<ProductSymbol> for Bytes32 {
    fn from(value: ProductSymbol) -> Self {
        // Delegate the conversion to the string type
        // Can't fail because we know that the length fits in 32 bytes
        value.to_string().parse().unwrap()
    }
}

#[cfg(feature = "database")]
impl ToSql for ProductSymbol {
    fn to_sql(
        &self,
        ty: &Type,
        out: &mut bytes::BytesMut,
    ) -> Result<IsNull, Box<dyn std::error::Error + 'static + Sync + Send>> {
        self.to_string().to_sql(ty, out)
    }

    fn accepts(ty: &Type) -> bool {
        <String as ToSql>::accepts(ty)
    }

    to_sql_checked!();
}

#[cfg(feature = "database")]
impl<'a> FromSql<'a> for ProductSymbol {
    fn from_sql(
        ty: &Type,
        raw: &'a [u8],
    ) -> Result<Self, Box<dyn std::error::Error + Sync + Send>> {
        let decoded_string = String::from_sql(ty, raw)?;
        let symbol: ProductSymbol = decoded_string.as_str().into();
        Ok(symbol)
    }

    fn accepts(ty: &Type) -> bool {
        <String as FromSql>::accepts(ty)
    }
}

#[derive(
    Debug,
    Clone,
    Copy,
    Default,
    std::hash::Hash,
    PartialEq,
    Eq,
    Serialize,
    Deserialize,
    PartialOrd,
    Ord,
    FixedBytesWrapper,
)]
#[serde(transparent)]
pub struct Bytes25(FixedBytes<25>);

#[cfg(feature = "python")]
impl FromPyObject<'_> for Bytes25 {
    fn extract(ob: &PyAny) -> PyResult<Self> {
        let text = ob.extract::<String>()?;
        Ok(core_crypto::from_hex(text).and_then(|v| Bytes25::try_from_slice(&v))?)
    }
}

#[cfg(feature = "python")]
impl IntoPy<PyObject> for Bytes25 {
    fn into_py(self, py: Python) -> PyObject {
        self.hex().into_py(py)
    }
}

impl Bytes25 {
    pub fn hex(&self) -> String {
        format!("0x{}", self.as_bytes().to_hex::<String>())
    }
}

impl From<Hash> for Bytes25 {
    fn from(value: Hash) -> Self {
        let fixed_bytes = value.as_bytes();
        Bytes25::from_slice(&fixed_bytes[..Self::BYTE_LEN])
    }
}

impl<T: Into<Bytes25> + Copy> From<&T> for Bytes25 {
    fn from(value: &T) -> Self {
        (*value).into()
    }
}

impl Tokenizable for Bytes25 {
    fn from_token(token: DynSolValue) -> Result<Self> {
        let token_bytes32 = Bytes32::from_token(token)?;
        Ok(Bytes25::from_slice(
            &token_bytes32.as_bytes()[..Self::BYTE_LEN],
        ))
    }
    fn into_token(self) -> DynSolValue {
        let mut bytes = self.0.to_vec();
        bytes.resize(32, 0_u8);
        let mut fixed_bytes = [0_u8; Bytes32::BYTE_LEN];
        fixed_bytes.copy_from_slice(&bytes);
        let bytes32: Bytes32 = fixed_bytes.into();
        bytes32.into_token()
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for Bytes25 {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        let hash = arbitrary_b256(g);
        let fixed_bytes = hash.0;
        Bytes25::from_slice(&fixed_bytes[..25])
    }
}

impl From<Bytes25> for Bytes32 {
    fn from(value: Bytes25) -> Self {
        let mut bytes = [0_u8; Self::BYTE_LEN];
        bytes[0..25].copy_from_slice(value.as_bytes());
        Bytes32(B256::new(bytes))
    }
}

#[cfg(feature = "database")]
impl ToSql for Bytes25 {
    fn to_sql(
        &self,
        ty: &Type,
        out: &mut bytes::BytesMut,
    ) -> Result<IsNull, Box<dyn std::error::Error + 'static + Sync + Send>> {
        self.0.to_vec().to_sql(ty, out)
    }

    fn accepts(ty: &Type) -> bool {
        <Vec<u8> as ToSql>::accepts(ty)
    }

    to_sql_checked!();
}

#[cfg(feature = "database")]
impl<'a> FromSql<'a> for Bytes25 {
    fn from_sql(
        ty: &Type,
        raw: &'a [u8],
    ) -> Result<Self, Box<dyn std::error::Error + Sync + Send>> {
        let bytes: Vec<u8> = Vec::from_sql(ty, raw)?;
        let fixed_bytes = Bytes25::copy_fixed_bytes(&bytes)?;
        Ok(Bytes25(fixed_bytes))
    }

    fn accepts(ty: &Type) -> bool {
        <Vec<u8> as FromSql>::accepts(ty)
    }
}

#[derive(
    Debug, Clone, Default, Copy, std::hash::Hash, PartialEq, Eq, PartialOrd, Ord, FixedBytesWrapper,
)]
pub struct Bytes4(pub FixedBytes<4>);

/// Abbreviates the `Hash` by copying its first four bytes
impl From<Hash> for Bytes4 {
    fn from(h: Hash) -> Self {
        let mut fb = [0_u8; Self::BYTE_LEN];
        fb.copy_from_slice(&h.as_bytes()[..Self::BYTE_LEN]);
        Bytes4(FixedBytes::new(fb))
    }
}

impl From<Bytes25> for Bytes4 {
    fn from(b: Bytes25) -> Self {
        let mut fb = [0_u8; Self::BYTE_LEN];
        fb.copy_from_slice(&b.as_bytes()[..Self::BYTE_LEN]);
        Bytes4(FixedBytes::new(fb))
    }
}

impl From<Bytes4> for [u8; Bytes4::BYTE_LEN] {
    fn from(value: Bytes4) -> Self {
        value.0.0
    }
}

impl From<[u8; Bytes4::BYTE_LEN]> for Bytes4 {
    fn from(value: [u8; Bytes4::BYTE_LEN]) -> Self {
        Bytes4(FixedBytes::new(value))
    }
}

impl Tokenizable for Bytes4 {
    fn from_token(token: DynSolValue) -> Result<Self> {
        let bytes: [u8; 4] = <[u8; 4]>::from_token(token)?;
        Ok(Bytes4(FixedBytes::new(bytes)))
    }
    fn into_token(self) -> DynSolValue {
        self.0.into_token()
    }
}

impl From<Bytes4> for Bytes32 {
    fn from(val: Bytes4) -> Self {
        let mut bytes = [0_u8; Bytes32::BYTE_LEN];
        bytes[0..4].copy_from_slice(val.as_bytes());
        Bytes32(B256::new(bytes))
    }
}

#[cfg(test)]
mod tests {
    use core_common::types::node::NodeUrl;

    use super::*;

    #[test]
    fn test_bytes32_str_conversion() {
        let text = "TEST".to_string();
        let bytes: Bytes32 = text.parse().unwrap();
        let text2 = bytes.to_string();
        assert_eq!(text, text2);
    }

    #[test]
    fn test_node_url() {
        let _ = "http://localhost:8080".parse::<NodeUrl>().unwrap();
        let _ = "http://127.0.0.1:8080".parse::<NodeUrl>().unwrap();
        let _ = "https://127.0.0.1:8080".parse::<NodeUrl>().unwrap();
        let _ = "https://127.0.0.1:8080/foo".parse::<NodeUrl>().unwrap();
        let _ = "http://localhost:8080/foo".parse::<NodeUrl>().unwrap();
        let _ = "http://localhost:8080/foo/bar".parse::<NodeUrl>().unwrap();
        assert!("foo".parse::<NodeUrl>().is_err());
        assert!("tcp://localhost:8080/foo/bar".parse::<NodeUrl>().is_err());
        // IPv6 not tested so not supported yet
        assert!(
            "http://2345:0425:2CA1:0000:0000:0567:5673:23b5"
                .parse::<NodeUrl>()
                .is_err()
        );
        assert_eq!(
            NodeUrl::with_localhost(8080).to_string(),
            "http://127.0.0.1:8080"
        );
        assert_eq!(
            NodeUrl::with_service(10).to_string(),
            "http://operator-node10:8080"
        );
    }

    #[test]
    fn test_product_symbol_roundtrip() {
        let symbol = ProductSymbol::from_str("ETHP").unwrap();
        let (underlying, product) = symbol.split();
        assert_eq!(
            (underlying, product),
            (
                UnderlyingSymbol::from_str("ETH").unwrap(),
                Product::Perpetual
            )
        );
        let symbol_str = symbol.to_string();
        assert_eq!(symbol_str, "ETHP");
        assert_eq!(symbol, ProductSymbol::from_str(&symbol_str).unwrap());

        #[cfg(feature = "fixed_expiry_future")]
        {
            let symbol = ProductSymbol::from_str("ETHFH").unwrap();
            let (underlying, product) = symbol.split();
            assert_eq!(
                (underlying, product),
                (
                    UnderlyingSymbol::from_str("ETH").unwrap(),
                    Product::QuarterlyExpiryFuture { month_code: 'H' },
                )
            );
            let symbol_str = symbol.to_string();
            assert_eq!(symbol_str, "ETHFH");
            assert_eq!(symbol, ProductSymbol::from_str(&symbol_str).unwrap());
        }
    }
}
