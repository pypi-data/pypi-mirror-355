use crate::types::request::RequestWithReceipt;
use core_ddx::types::state::CmdKind;
use std::collections::HashMap;

// The type definition of outcome from ticking the trusted clock
pub type ClockTickOutcome = (bool, i64, HashMap<CmdKind, RequestWithReceipt>);

#[cfg(test)]
mod tests {
    use crate::types::request::{Cmd, Receipt, Request};

    use super::*;

    #[test]
    fn test_serialize_clock_tick_outcome() {
        let request = RequestWithReceipt {
            request: Request::Cmd(Cmd::AdvanceTime(Default::default())),
            receipt: Receipt::Sequenced {
                nonce: Default::default(),
                request_hash: Default::default(),
                request_index: 0,
                sender: Default::default(),
                enclave_signature: Default::default(),
            },
        };
        let outcome: ClockTickOutcome = (
            false,
            100,
            HashMap::from([(CmdKind::UpdateProductListings, request)]),
        );
        let serialized = cbor4ii::serde::to_vec(vec![], &outcome).unwrap();
        let deserialized: ClockTickOutcome = cbor4ii::serde::from_slice(&serialized).unwrap();
        assert_eq!(outcome, deserialized);
    }
}
