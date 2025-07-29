use crate::{Address, B256, B520, Result, U128, U256, ensure, error};
use alloy_dyn_abi::{DynSolType, DynSolValue};
use arrayvec::ArrayVec;
use serde::{Deserialize, Serialize};

// TODO: I took the `Tokenizable` and `Tokenize` trait and implementation in the
// module from Rust Web3. I didn't want to import the whole thing and didn't have
// a way to get just this feature. I'll ask them to create one, but everything we
// need is here in the meantime.

/// Tokens conversion trait
pub trait Tokenize {
    /// Convert to list of tokens
    fn into_tokens(self) -> Vec<DynSolValue>;
}

impl Tokenize for &[DynSolValue] {
    fn into_tokens(self) -> Vec<DynSolValue> {
        self.to_vec()
    }
}

impl<T: Tokenizable> Tokenize for T {
    fn into_tokens(self) -> Vec<DynSolValue> {
        vec![self.into_token()]
    }
}

impl Tokenize for () {
    fn into_tokens(self) -> Vec<DynSolValue> {
        vec![]
    }
}

macro_rules! impl_tokens {
  ($( $ty: ident : $no: tt, )+) => {
    impl<$($ty, )+> Tokenize for ($($ty,)+) where
      $(
        $ty: Tokenizable,
      )+
    {
      fn into_tokens(self) -> Vec<DynSolValue> {
        vec![
          $( self.$no.into_token(), )+
        ]
      }
    }
  }
}

impl_tokens!(A:0, );
impl_tokens!(A:0, B:1, );
impl_tokens!(A:0, B:1, C:2, );
impl_tokens!(A:0, B:1, C:2, D:3, );
impl_tokens!(A:0, B:1, C:2, D:3, E:4, );
impl_tokens!(A:0, B:1, C:2, D:3, E:4, F:5, );
impl_tokens!(A:0, B:1, C:2, D:3, E:4, F:5, G:6, );
impl_tokens!(A:0, B:1, C:2, D:3, E:4, F:5, G:6, H:7, );
impl_tokens!(A:0, B:1, C:2, D:3, E:4, F:5, G:6, H:7, I:8, );
impl_tokens!(A:0, B:1, C:2, D:3, E:4, F:5, G:6, H:7, I:8, J:9, );
impl_tokens!(A:0, B:1, C:2, D:3, E:4, F:5, G:6, H:7, I:8, J:9, K:10, );
impl_tokens!(A:0, B:1, C:2, D:3, E:4, F:5, G:6, H:7, I:8, J:9, K:10, L:11, );
impl_tokens!(A:0, B:1, C:2, D:3, E:4, F:5, G:6, H:7, I:8, J:9, K:10, L:11, M:12, );
impl_tokens!(A:0, B:1, C:2, D:3, E:4, F:5, G:6, H:7, I:8, J:9, K:10, L:11, M:12, N:13, );
impl_tokens!(A:0, B:1, C:2, D:3, E:4, F:5, G:6, H:7, I:8, J:9, K:10, L:11, M:12, N:13, O:14, );
impl_tokens!(A:0, B:1, C:2, D:3, E:4, F:5, G:6, H:7, I:8, J:9, K:10, L:11, M:12, N:13, O:14, P:15, );

/// Simplified output type for single value.
pub trait Tokenizable {
    /// Converts a `Token` into expected type.
    fn from_token(token: DynSolValue) -> Result<Self>
    where
        Self: Sized;
    /// Converts a specified type back into token.
    fn into_token(self) -> DynSolValue;
}

impl Tokenizable for DynSolValue {
    fn from_token(token: DynSolValue) -> Result<Self> {
        Ok(token)
    }
    fn into_token(self) -> DynSolValue {
        self
    }
}

impl Tokenizable for String {
    fn from_token(token: DynSolValue) -> Result<Self> {
        match token {
            DynSolValue::String(s) => Ok(s),
            other => Err(error!("Expected `String`, got {:?}", other)),
        }
    }

    fn into_token(self) -> DynSolValue {
        DynSolValue::String(self)
    }
}

pub fn token_from_vec<T: Tokenizable>(v: Vec<T>) -> DynSolValue {
    DynSolValue::Array(v.into_iter().map(T::into_token).collect())
}

pub fn vec_from_token<T: Tokenizable>(token: DynSolValue) -> Result<Vec<T>> {
    match token {
        DynSolValue::Array(tokens) => tokens.into_iter().map(T::from_token).collect(),
        other => Err(error!("Expected Token::Array(...), got {:?}", other)),
    }
}

impl Tokenizable for B256 {
    fn from_token(token: DynSolValue) -> Result<Self> {
        token.as_word().ok_or_else(|| error!("Token not B256"))
    }

    fn into_token(self) -> DynSolValue {
        DynSolValue::FixedBytes(self, 32)
    }
}

impl Tokenizable for Address {
    fn from_token(token: DynSolValue) -> Result<Self> {
        token
            .as_address()
            .ok_or_else(|| core_common::error!("Token not Address"))
    }

    fn into_token(self) -> DynSolValue {
        DynSolValue::Address(self)
    }
}

macro_rules! eth_uint_tokenizable {
    ($uint: ident, $name: expr) => {
        impl Tokenizable for $uint {
            fn from_token(token: DynSolValue) -> Result<Self> {
                match token {
                    DynSolValue::Int(n, _) => {
                        let u: U256 = n.try_into().unwrap();
                        Ok(u.to::<$uint>())
                    }
                    DynSolValue::Uint(n, _) => Ok(n.to::<$uint>()),
                    other => Err(error!("Expected `{}`, got {:?}", $name, other)).into(),
                }
            }

            fn into_token(self) -> DynSolValue {
                DynSolValue::Uint(self.to::<U256>(), $uint::BITS)
            }
        }
    };
}

eth_uint_tokenizable!(U256, "U256");
eth_uint_tokenizable!(U128, "U128");

macro_rules! int_tokenizable {
    ($int: ident, $token: ident) => {
        impl Tokenizable for $int {
            fn from_token(token: DynSolValue) -> Result<Self> {
                match token {
                    DynSolValue::Int(data, _) => {
                        let n: u128 = data.try_into().unwrap();
                        Ok(n as _)
                    }
                    DynSolValue::Uint(data, _) => Ok(data.to::<u128>() as _),
                    other => Err(error!("Expected `{}`, got {:?}", stringify!($int), other)),
                }
            }

            fn into_token(self) -> DynSolValue {
                self.into()
            }
        }
    };
}

int_tokenizable!(i8, Int);
int_tokenizable!(i16, Int);
int_tokenizable!(i32, Int);
int_tokenizable!(i64, Int);
int_tokenizable!(i128, Int);
int_tokenizable!(u8, Uint);
int_tokenizable!(u16, Uint);
int_tokenizable!(u32, Uint);
int_tokenizable!(u64, Uint);
int_tokenizable!(u128, Uint);

impl Tokenizable for bool {
    fn from_token(token: DynSolValue) -> Result<Self> {
        match token {
            DynSolValue::Bool(data) => Ok(data),
            other => Err(error!("Expected `bool`, got {:?}", other)),
        }
    }
    fn into_token(self) -> DynSolValue {
        DynSolValue::Bool(self)
    }
}

/// Marker trait for `Tokenizable` types that are can tokenized to and from a
/// `Token::Array` and `Token:FixedArray`.
pub trait TokenizableItem: Tokenizable {}

macro_rules! tokenizable_item {
    ($($type: ty,)*) => {
        $(
            impl TokenizableItem for $type {}
        )*
    };
}

tokenizable_item! {
    String, Address, B256, U256, U128, bool, Vec<u8>,
    i8, i16, i32, i64, i128, u16, u32, u64, u128,
}

impl Tokenizable for Vec<u8> {
    fn from_token(token: DynSolValue) -> Result<Self> {
        match token {
            DynSolValue::Bytes(data) => Ok(data),
            other => Err(error!("Expected `bytes`, got {:?}", other)),
        }
    }
    fn into_token(self) -> DynSolValue {
        DynSolValue::Bytes(self)
    }
}

const H520_BYTE_LEN: usize = B520::len_bytes();

impl Tokenizable for [u8; H520_BYTE_LEN] {
    fn from_token(token: DynSolValue) -> Result<Self> {
        match token {
            DynSolValue::Bytes(data) => {
                ensure!(data.len() == H520_BYTE_LEN, "65 bytes token");
                let mut fixed_bytes = [0_u8; H520_BYTE_LEN];
                fixed_bytes.copy_from_slice(&data);
                Ok(fixed_bytes)
            }
            other => Err(error!("Expected `bytes`, got {:?}", other)),
        }
    }
    fn into_token(self) -> DynSolValue {
        DynSolValue::Bytes(self.to_vec())
    }
}

impl<T: TokenizableItem> Tokenizable for Vec<T> {
    fn from_token(token: DynSolValue) -> Result<Self> {
        match token {
            DynSolValue::FixedArray(tokens) | DynSolValue::Array(tokens) => {
                tokens.into_iter().map(Tokenizable::from_token).collect()
            }
            other => Err(error!("Expected `Array`, got {:?}", other)),
        }
    }

    fn into_token(self) -> DynSolValue {
        DynSolValue::Array(self.into_iter().map(Tokenizable::into_token).collect())
    }
}

impl Tokenizable for B520 {
    fn from_token(token: DynSolValue) -> Result<Self> {
        match token {
            // TODO: Why not Token::FixedBytes?
            DynSolValue::Bytes(data) => {
                ensure!(data.len() == H520_BYTE_LEN, "65 bytes token");
                let mut fixed_bytes = [0_u8; H520_BYTE_LEN];
                fixed_bytes.copy_from_slice(&data);
                Ok(B520::new(fixed_bytes))
            }
            other => Err(error!("Expected `bytes`, got {:?}", other)),
        }
    }
    fn into_token(self) -> DynSolValue {
        DynSolValue::Bytes(self.as_slice().to_vec())
    }
}

impl<T: TokenizableItem> TokenizableItem for Vec<T> {}

macro_rules! impl_fixed_types {
    ($num: expr) => {
        impl Tokenizable for [u8; $num] {
            fn from_token(token: DynSolValue) -> Result<Self> {
                match token {
                    DynSolValue::FixedBytes(bytes, size) => {
                        if size != $num {
                            return Err(error!(
                                "Expected `FixedBytes({})`, got FixedBytes({})",
                                $num, size,
                            ));
                        }

                        let mut arr = [0; $num];
                        arr.copy_from_slice(&bytes[0..size]);
                        Ok(arr)
                    }
                    other => Err(error!("Expected `FixedBytes({})`, got {:?}", $num, other)).into(),
                }
            }

            fn into_token(self) -> DynSolValue {
                DynSolValue::FixedBytes(B256::right_padding_from(self.as_slice()), $num)
            }
        }

        impl TokenizableItem for [u8; $num] {}

        impl<T: TokenizableItem + Clone> Tokenizable for [T; $num] {
            fn from_token(token: DynSolValue) -> Result<Self> {
                match token {
                    DynSolValue::FixedArray(tokens) => {
                        if tokens.len() != $num {
                            return Err(error!(
                                "Expected `FixedArray({})`, got FixedArray({})",
                                $num,
                                tokens.len()
                            ));
                        }

                        let mut arr = ArrayVec::<T, $num>::new();
                        let mut it = tokens.into_iter().map(T::from_token);
                        for _ in 0..$num {
                            arr.push(it.next().expect("Length validated in guard; qed")?);
                        }
                        // Can't use expect here because [T; $num]: Debug is not satisfied.
                        match arr.into_inner() {
                            Ok(arr) => Ok(arr),
                            Err(_) => panic!("All elements inserted so the array is full; qed"),
                        }
                    }
                    other => Err(error!("Expected `FixedArray({})`, got {:?}", $num, other)),
                }
            }

            fn into_token(self) -> DynSolValue {
                DynSolValue::FixedArray(
                    ArrayVec::from(self)
                        .into_iter()
                        .map(T::into_token)
                        .collect(),
                )
            }
        }

        impl<T: TokenizableItem + Clone> TokenizableItem for [T; $num] {}
    };
}

impl_fixed_types!(1);
impl_fixed_types!(2);
impl_fixed_types!(3);
impl_fixed_types!(4);
impl_fixed_types!(5);
impl_fixed_types!(6);
impl_fixed_types!(7);
impl_fixed_types!(8);
impl_fixed_types!(9);
impl_fixed_types!(10);
impl_fixed_types!(11);
impl_fixed_types!(12);
impl_fixed_types!(13);
impl_fixed_types!(14);
impl_fixed_types!(15);
impl_fixed_types!(16);
impl_fixed_types!(32);
impl_fixed_types!(64);
impl_fixed_types!(128);
impl_fixed_types!(256);
//impl_fixed_types!(512);
//impl_fixed_types!(1024);

// End of sources copied from rust-web3

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(tag = "t", content = "c")]
pub enum TokenSchema {
    /// Address.
    Address,
    /// Bytes.
    Bytes,
    /// Signed integer.
    Int(usize),
    /// Unsigned integer.
    Uint(usize),
    /// Boolean.
    Bool,
    /// String.
    String,
    /// Array of unknown size.
    Array(Box<TokenSchema>),
    /// Vector of bytes with fixed size.
    FixedBytes(usize),
    /// Array with fixed size.
    FixedArray(Box<TokenSchema>, usize),
    /// Tuple containing different types
    Tuple(Vec<TokenSchema>),
    /// Placeholder type for empty containers with a mandatory type field
    Void,
    Function,
}

/// Recursively generates a token schema containing the type and all sub-types of a token
/// The schema is required to get the types of
pub fn generate_schema(token: &DynSolValue) -> TokenSchema {
    match token {
        DynSolValue::Address(_) => TokenSchema::Address,
        DynSolValue::Bytes(_) => TokenSchema::Bytes,
        DynSolValue::String(_) => TokenSchema::String,
        DynSolValue::FixedBytes(_, size) => TokenSchema::FixedBytes(*size),
        DynSolValue::Int(_, size) => TokenSchema::Int(*size), // Length in 64-bit registries
        // To my knowledge, the `Token` enum only allows the U256 type here, so calculating the
        // length seems redundant.
        DynSolValue::Uint(_, size) => TokenSchema::Uint(*size),
        DynSolValue::Bool(_) => TokenSchema::Bool,
        DynSolValue::Array(ref tokens) => {
            let inner = match tokens.first() {
                Some(token) => generate_schema(token),
                // Using Bool as a placeholder for the inner type of empty arrays
                None => TokenSchema::Void,
            };
            TokenSchema::Array(Box::new(inner))
        }
        DynSolValue::FixedArray(ref tokens) => {
            let inner = match tokens.first() {
                Some(token) => generate_schema(token),
                // Using Bool as a placeholder for the inner type of empty arrays
                None => TokenSchema::Void,
            };
            TokenSchema::FixedArray(Box::new(inner), tokens.len())
        }
        DynSolValue::Tuple(ref tokens) => {
            TokenSchema::Tuple(tokens.iter().map(generate_schema).collect())
        }
        DynSolValue::Function(_) => TokenSchema::Function,
    }
}

impl From<TokenSchema> for DynSolType {
    fn from(value: TokenSchema) -> Self {
        match value {
            TokenSchema::Address => DynSolType::Address,
            TokenSchema::Bytes => DynSolType::Bytes,
            TokenSchema::Int(len) => DynSolType::Int(len),
            TokenSchema::Uint(len) => DynSolType::Uint(len),
            TokenSchema::Bool => DynSolType::Bool,
            TokenSchema::String => DynSolType::String,
            TokenSchema::Array(inner) => DynSolType::Array(Box::new(DynSolType::from(*inner))),
            TokenSchema::FixedBytes(len) => DynSolType::FixedBytes(len),
            TokenSchema::FixedArray(inner, len) => {
                DynSolType::FixedArray(Box::new(DynSolType::from(*inner)), len)
            }
            TokenSchema::Tuple(inner) => {
                DynSolType::Tuple(inner.into_iter().map(DynSolType::from).collect())
            }
            TokenSchema::Function => DynSolType::Function,
            // By convention, we map Void to Bool. Since Void only exists to satisfy the inner type
            // requirement of empty arrays, it won't ever actually get decoded into any value
            // so the DynSolType given does not matter.
            TokenSchema::Void => DynSolType::Bool,
        }
    }
}
