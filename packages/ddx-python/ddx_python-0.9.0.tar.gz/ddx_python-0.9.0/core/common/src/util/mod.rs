use crate::Result;
use chrono::{DateTime, Utc};
use std::time::{Duration, UNIX_EPOCH};

#[cfg(not(target_family = "wasm"))]
pub mod backoff;
#[cfg(not(target_family = "wasm"))]
pub mod mem;
pub mod tokenize;
#[cfg(not(target_family = "wasm"))]
pub mod tracing;

pub fn get_app_share_dir(app_name: &str) -> String {
    let mut share_dir = std::env::var("APP_SHARE").expect("APP_SHARE not set");
    share_dir.push('/');
    share_dir.push_str(app_name);
    share_dir
}

pub fn unix_timestamp_to_datetime(unix_timestamp: i64) -> Result<DateTime<Utc>> {
    Ok(DateTime::<Utc>::from(
        UNIX_EPOCH + Duration::from_secs(unix_timestamp.try_into()?),
    ))
}
