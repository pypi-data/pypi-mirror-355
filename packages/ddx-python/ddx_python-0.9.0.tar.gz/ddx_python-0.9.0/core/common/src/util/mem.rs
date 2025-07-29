use std::mem::size_of;

/// # Safety
///
/// This trait should be only used for types with contiguous memory.
pub unsafe trait ContiguousMemory {}

/// # Safety
///
/// This trait should be only used for types with contiguous memory.
///
/// An unsafe trait to convert a type with contiguous memory from and to a byte slice.
pub unsafe trait ByteSlice: Sized + ContiguousMemory {
    /// # Safety
    ///
    /// The struct is converted into a byte slice
    unsafe fn to_byte_slice(self) -> [u8; size_of::<Self>()];
    /// # Safety
    ///
    /// The byte slice argument must have equal or longer length than the size of the resulted struct.
    unsafe fn from_byte_slice(d: &[u8]) -> Self;
}
