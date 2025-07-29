pub mod accounting;
pub mod auth;
pub mod contract;
#[cfg(feature = "python")]
pub mod exported;
pub mod global;
pub mod identifiers;
#[cfg(not(target_family = "wasm"))]
pub mod node;
pub mod primitives;
pub mod state;
pub mod transaction;

/// # Safety
/// Adding this trait means the marked struct uses contiguous memory.
/// It implies that the struct may be `memcpy` if using the same struct representation.
///
/// A macro rule for adding unsafe marker trait for struct.
#[cfg(not(target_family = "wasm"))]
#[macro_export]
macro_rules! impl_contiguous_marker_for {
    ($($ty:ty)*) => {
        $(
            unsafe impl $crate::util::mem::ContiguousMemory for $ty { }
        )*
    }
}

/// # Safety
/// The data type must use contiguous memory, which do not contain pointers.
///
/// A macro rule for unsafe byte slicing.
/// Using this macro to derive unsafe re-interpretation of a contiguous memory into and from a byte slice.
#[cfg(not(target_family = "wasm"))]
#[macro_export]
macro_rules! impl_unsafe_byte_slice_for {
    ($($ty:ty)*) => {
        $(
            unsafe impl $crate::util::mem::ByteSlice for $ty {
                unsafe fn to_byte_slice(self) -> [u8; std::mem::size_of::<$ty>()] {
                    std::mem::transmute::<$ty, [u8; std::mem::size_of::<$ty>()]>(self)
                }

                unsafe fn from_byte_slice(d: &[u8]) -> $ty {
                    let mut slice = [0; std::mem::size_of::<$ty>()];
                    // This method will check the length of the slice in runtime.
                    slice.copy_from_slice(d);
                    std::mem::transmute::<[u8; std::mem::size_of::<$ty>()], $ty>(slice)
                }
            }
        )*
    }
}

#[cfg(test)]
mod tests {
    use super::primitives::as_scaled_fraction;
    use crate::U128;
    use rust_decimal::Decimal;
    use serde::{Deserialize, Serialize};
    use serde_json::json;

    #[derive(Serialize, Deserialize)]
    struct ScaledFraction {
        /// Deserializes a decimal value into integer by scaling it up: I=D**18
        #[serde(with = "as_scaled_fraction")]
        pub value: U128,
    }

    #[test]
    fn test_scaled_fractions() {
        let message = json!({ "value": "1234.4444" });
        let _res: ScaledFraction = serde_json::from_value(message).unwrap();
        let message = json!({ "value": "1234" });
        let _res: ScaledFraction = serde_json::from_value(message).unwrap();
        let message = json!({ "value": ".4444" });
        let _res: ScaledFraction = serde_json::from_value(message).unwrap();
    }

    #[test]
    fn test_bad_scaled_fractions() {
        let max_dec = format!("{}", Decimal::MAX.floor());
        let message = json!({ "value": max_dec });
        let maybe_s: Result<ScaledFraction, _> = serde_json::from_value(message);
        if maybe_s.is_ok() {
            panic!(
                "Expected number greater than MAX_UNSCALED_DECIMAL to be caught by our deserializer max_dec={}",
                max_dec
            )
        }
        let fract = "79228162514264337593543950335.994276";
        let message = json!({ "value": fract });
        let maybe_s: Result<ScaledFraction, _> = serde_json::from_value(message);
        if maybe_s.is_ok() {
            panic!("Expected failure");
        }
        // Being left-aligned, the number is either truncated or filled with zeroes.
        let over_dec = format!(
            "{:0<width$}",
            max_dec,
            // Append zeroes to cause overflow
            width = max_dec.len() + 1
        );
        let message = json!({ "value": over_dec });
        let maybe_s: Result<ScaledFraction, _> = serde_json::from_value(message);
        if maybe_s.is_ok() {
            panic!(
                "Expected number greater than Decimal::MAX to be caught by Decimal's deserializer over_dec={}",
                over_dec
            )
        }
    }

    #[test]
    fn test_bad_decimal() {
        let fract = "79228162514264337593543950335.994276";
        let res: Result<Decimal, _> = serde_json::from_str(fract);
        if let Err(err) = res {
            println!("Handled deserialization error {}", err);
        }
    }
}
