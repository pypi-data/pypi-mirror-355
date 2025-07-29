use sparse_merkle_tree::error::Error;
use std::{fmt::Debug, sync::PoisonError};

pub fn poison_err<T: Debug>(e: PoisonError<T>) -> Error {
    Error::Store(format!("{:?}", e))
}
