#[cfg(feature = "insurance_fund_client_req")]
use crate::types::request::InsuranceFundWithdrawIntent;
use crate::types::{
    request::{
        AdminCmd, CancelAllIntent, CancelOrderIntent, DisasterRecovery, ModifyOrderIntent,
        OrderIntent, ProfileUpdate, WithdrawDDXIntent, WithdrawIntent,
    },
    transaction::MatchableIntent,
};
use core_common::{
    Address, U256,
    types::{
        primitives::{Bytes32, Hash, SessionSignature, Signature},
        state::Chain,
    },
};
use core_crypto::eip712::{HashEIP712, Message, MultisigEIP712, Payload, Signed1ctEIP712};

#[cfg(not(target_family = "wasm"))]
impl Signed1ctEIP712 for ModifyOrderIntent {
    fn eip712_signature(&self) -> Signature {
        self.signature
    }
    fn session_key_signature(&self) -> SessionSignature {
        self.session_key_signature
    }
}

impl HashEIP712 for ModifyOrderIntent {
    fn hash_eip712_raw(&self, chain: Chain, contract_address: Address) -> Hash {
        let mut message = Message::new(chain, contract_address);
        let mut payload = Payload::from_signature(
            b"ModifyOrderParams(bytes32 orderHash,bytes32 symbol,bytes32 strategy,uint256 side,uint256 orderType,bytes32 nonce,uint256 amount,uint256 price,uint256 stopPrice)"
                .to_vec(),
        );
        payload.append(Bytes32::from(self.order_hash));
        payload.append(Bytes32::from(self.symbol));
        payload.append(Bytes32::from(self.strategy));
        payload.append(U256::from(self.side as u8));
        payload.append(U256::from(u8::from(self.order_type)));
        payload.append(self.nonce);
        payload.append(Into::<U256>::into(self.amount));
        payload.append(Into::<U256>::into(self.price));
        payload.append(Into::<U256>::into(self.stop_price));
        message.append_payload(payload);
        message.finalize()
    }
}

#[cfg(not(target_family = "wasm"))]
impl Signed1ctEIP712 for CancelOrderIntent {
    fn eip712_signature(&self) -> Signature {
        self.signature
    }

    fn session_key_signature(&self) -> SessionSignature {
        self.session_key_signature
    }
}

impl HashEIP712 for CancelOrderIntent {
    fn hash_eip712_raw(&self, chain: Chain, contract_address: Address) -> Hash {
        let mut message = Message::new(chain, contract_address);
        let mut payload = Payload::from_signature(
            b"CancelOrderParams(bytes32 symbol,bytes32 orderHash,bytes32 nonce)".to_vec(),
        );
        payload.append(Bytes32::from(self.symbol));
        payload.append(Bytes32::from(self.order_hash));
        payload.append(self.nonce);
        message.append_payload(payload);
        message.finalize()
    }
}

#[cfg(not(target_family = "wasm"))]
impl Signed1ctEIP712 for CancelAllIntent {
    fn eip712_signature(&self) -> Signature {
        self.signature
    }

    fn session_key_signature(&self) -> SessionSignature {
        self.session_key_signature
    }
}

#[cfg(not(target_family = "wasm"))]
impl Signed1ctEIP712 for OrderIntent {
    fn eip712_signature(&self) -> Signature {
        self.signature
    }

    fn session_key_signature(&self) -> SessionSignature {
        self.session_key_signature
    }
}

impl HashEIP712 for OrderIntent {
    fn hash_eip712_raw(&self, chain: Chain, contract_address: Address) -> Hash {
        let mut message = Message::new(chain, contract_address);
        // TODO: Consider generating the signature using ethabi
        let mut payload = Payload::from_signature(b"OrderParams(bytes32 symbol,bytes32 strategy,uint256 side,uint256 orderType,bytes32 nonce,uint256 amount,uint256 price,uint256 stopPrice)".to_vec());
        // Addresses and strings must be resized to bytes32
        payload.append(Bytes32::from(self.symbol));
        payload.append(Bytes32::from(self.strategy));
        payload.append(U256::from(self.side as u8));
        payload.append(U256::from(u8::from(self.order_type)));
        payload.append(self.nonce);
        payload.append(Into::<U256>::into(self.amount));
        payload.append(Into::<U256>::into(self.price));
        payload.append(Into::<U256>::into(self.stop_price));
        message.append_payload(payload);
        message.finalize()
    }
}

impl HashEIP712 for WithdrawDDXIntent {
    fn hash_eip712_raw(&self, chain: Chain, contract_address: Address) -> Hash {
        let mut message = Message::new(chain, contract_address);
        // TODO: Consider generating the signature using ethabi
        let mut payload =
            Payload::from_signature(b"WithdrawDDXParams(uint128 amount,bytes32 nonce)".to_vec());
        payload.append(Into::<U256>::into(self.amount));
        payload.append(self.nonce);
        message.append_payload(payload);
        message.finalize()
    }
}

impl HashEIP712 for WithdrawIntent {
    fn hash_eip712_raw(&self, chain: Chain, contract_address: Address) -> Hash {
        let mut message = Message::new(chain, contract_address);
        // TODO: Consider generating the signature using ethabi
        let mut payload = Payload::from_signature(
            b"WithdrawParams(bytes32 strategyId,address currency,uint128 amount,bytes32 nonce)"
                .to_vec(),
        );
        // Addresses and strings must be resized to bytes32
        payload.append(Bytes32::from(self.strategy_id));
        payload.append(Bytes32::from(self.currency));
        payload.append(Into::<U256>::into(self.amount));
        payload.append(self.nonce);
        message.append_payload(payload);
        message.finalize()
    }
}

#[cfg(feature = "insurance_fund_client_req")]
impl HashEIP712 for InsuranceFundWithdrawIntent {
    fn hash_eip712_raw(&self, chain: Chain, contract_address: Address) -> Hash {
        let mut message = Message::new(chain, contract_address);
        // TODO: Consider generating the signature using ethabi
        let mut payload = Payload::from_signature(
            b"InsuranceFundWithdrawParams(address currency,uint128 amount,bytes32 nonce)".to_vec(),
        );
        // Addresses and strings must be resized to bytes32
        payload.append(Bytes32::from(self.currency));
        payload.append(U256::from(self.amount));
        payload.append(self.nonce);
        message.append_payload(payload);
        message.finalize()
    }
}

impl HashEIP712 for ProfileUpdate {
    fn hash_eip712_raw(&self, chain: Chain, contract_address: Address) -> Hash {
        let mut message = Message::new(chain, contract_address);
        let mut payload = Payload::from_signature(
            b"UpdateProfileParams(bool payFeesInDdx,bytes32 nonce)".to_vec(),
        );
        payload.append(U256::from(self.pay_fees_in_ddx as u8));
        payload.append(self.nonce);
        message.append_payload(payload);
        message.finalize()
    }
}

impl HashEIP712 for CancelAllIntent {
    fn hash_eip712_raw(&self, chain: Chain, contract_address: Address) -> Hash {
        let mut message = Message::new(chain, contract_address);
        let mut payload = Payload::from_signature(
            b"CancelAllParams(bytes32 symbol,bytes32 strategy,bytes32 nonce)".to_vec(),
        );
        payload.append(Bytes32::from(self.symbol));
        payload.append(Bytes32::from(self.strategy));
        payload.append(self.nonce);
        message.append_payload(payload);
        message.finalize()
    }
}

impl HashEIP712 for AdminCmd {
    /// Computes the EIP-712 hash
    fn hash_eip712_raw(&self, chain: Chain, contract_address: Address) -> Hash {
        match self {
            AdminCmd::DisasterRecovery(DisasterRecovery { request_index, .. }) => {
                let mut message = Message::new(chain, contract_address);
                let mut payload = Payload::from_signature(
                    b"DisasterRecoveryParams(uint128 request_index)".to_vec(),
                );
                payload.append(U256::from(*request_index));
                message.append_payload(payload);
                message.finalize()
            }
        }
    }
}

impl MultisigEIP712 for AdminCmd {
    fn signatures(&self) -> Vec<Signature> {
        match self {
            AdminCmd::DisasterRecovery(DisasterRecovery { signatures, .. }) => signatures.clone(),
        }
    }
}

#[cfg(not(target_family = "wasm"))]
impl Signed1ctEIP712 for MatchableIntent {
    fn eip712_signature(&self) -> Signature {
        match self {
            Self::OrderIntent(intent) => intent.eip712_signature(),
            Self::ModifyOrderIntent(intent) => intent.eip712_signature(),
        }
    }

    fn session_key_signature(&self) -> SessionSignature {
        match self {
            Self::OrderIntent(intent) => intent.session_key_signature(),
            Self::ModifyOrderIntent(intent) => intent.session_key_signature(),
        }
    }
}

impl HashEIP712 for MatchableIntent {
    fn hash_eip712_raw(&self, chain: Chain, contract_address: Address) -> Hash {
        match self {
            Self::OrderIntent(intent) => intent.hash_eip712_raw(chain, contract_address),
            Self::ModifyOrderIntent(intent) => intent.hash_eip712_raw(chain, contract_address),
        }
    }
}

#[cfg(test)]
pub mod tests {
    use super::HashEIP712;
    use crate::types::request::{
        CancelAllIntent, CancelOrderIntent, OrderIntent, OrderType, WithdrawDDXIntent,
        WithdrawIntent,
    };
    use core_common::types::primitives::{OrderSide, TokenSymbol};

    #[test]
    fn test_eip712_cancel_order() {
        let intent = CancelOrderIntent {
            symbol: Default::default(),
            order_hash: Default::default(),
            nonce: Default::default(),
            session_key_signature: Default::default(),
            signature: Default::default(),
        };
        assert_ne!(intent.hash_eip712(), Default::default());
    }

    #[test]
    fn test_eip712_cancel_all_order() {
        let intent = CancelAllIntent {
            symbol: Default::default(),
            strategy: Default::default(),
            nonce: Default::default(),
            session_key_signature: Default::default(),
            signature: Default::default(),
        };
        assert_ne!(intent.hash_eip712(), Default::default());
    }

    #[test]
    fn test_eip712_order() {
        let order_intent = OrderIntent {
            symbol: Default::default(),
            strategy: Default::default(),
            side: OrderSide::Bid,
            order_type: OrderType::Limit { post_only: false },
            nonce: Default::default(),
            amount: Default::default(),
            price: Default::default(),
            stop_price: Default::default(),
            session_key_signature: Default::default(),
            signature: Default::default(),
        };
        assert_ne!(order_intent.hash_eip712(), Default::default());
    }

    #[test]
    fn test_eip712_withdraw_ddx() {
        let withdraw_ddx_intent = WithdrawDDXIntent {
            amount: Default::default(),
            nonce: Default::default(),
            signature: Default::default(),
        };
        assert_ne!(withdraw_ddx_intent.hash_eip712(), Default::default());
    }

    #[test]
    fn test_eip712_withdraw() {
        let withdraw_intent = WithdrawIntent {
            strategy_id: Default::default(),
            currency: TokenSymbol::USDC.into(),
            amount: Default::default(),
            nonce: Default::default(),
            signature: Default::default(),
        };
        assert_ne!(withdraw_intent.hash_eip712(), Default::default());
    }
}
