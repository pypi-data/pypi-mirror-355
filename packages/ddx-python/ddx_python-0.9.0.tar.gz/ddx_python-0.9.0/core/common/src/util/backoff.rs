use backoff::{ExponentialBackoff, ExponentialBackoffBuilder};
use core_common::types::node::BackoffConfig;

impl BackoffConfig {
    /// Makes a std-dependent `ExponentialBackoff` from the given config
    pub fn build(&self) -> ExponentialBackoff {
        ExponentialBackoffBuilder::new()
            .with_initial_interval(self.initial_interval)
            .with_max_interval(self.max_interval)
            .with_max_elapsed_time(Some(self.max_elapsed_time))
            .build()
    }
}
