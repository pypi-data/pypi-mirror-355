use rust_decimal::{
    Decimal,
    prelude::{FromPrimitive, One},
};

#[cfg(not(target_family = "wasm"))]
pub(crate) mod convert;
#[cfg(not(target_family = "wasm"))]
pub mod eip712;
#[cfg(not(target_family = "wasm"))]
pub mod env;
pub mod serde;

/// The default trade mining reward per epoch. This is the amount that will be
/// used in production, and will be used throughout our tests.
///
/// This is calculated as 35,000,000 / (3 * 10 * 365). This is 35 million
/// divided by the number of epochs of trade mining that will occur (3 per
/// day 365 days a year for 10 years).
pub fn default_trade_mining_reward_per_epoch() -> Decimal {
    Decimal::from(35000000) / (Decimal::from(3) * Decimal::from(10) * Decimal::from(365))
}

pub fn default_trade_mining_maker_reward_percentage() -> Decimal {
    Decimal::from_f32(0.2).unwrap()
}

pub fn default_trade_mining_taker_reward_percentage() -> Decimal {
    Decimal::one() - default_trade_mining_maker_reward_percentage()
}

#[cfg(feature = "database")]
pub mod db {
    use std::{
        path::{Path, PathBuf},
        str::FromStr,
    };

    use anyhow::{Result, bail};
    use core_common::types::identifiers::OperatorNodeId;

    use crate::constants::{PG_DUMP_DIR, PG_DUMP_FORMAT};

    pub fn dump_subdir(prefix: &str, node_id: OperatorNodeId) -> PathBuf {
        PathBuf::from(format!("{}{}", prefix, node_id).as_str())
    }

    pub fn pg_dump_file_path(snapshot_id: &str, subdir: &Path) -> Result<PathBuf> {
        let mut path = PathBuf::from_str(PG_DUMP_DIR)?;
        path.push(subdir);
        let file_name = match PG_DUMP_FORMAT {
            "tar" => format!("{}.tar", snapshot_id),
            "custom" => format!("{}.dump", snapshot_id),
            _ => bail!("pg_dump format {} not supported", PG_DUMP_FORMAT),
        };
        path.push(file_name);
        Ok(path)
    }
}

#[cfg(test)]
mod tests {
    use crate::{
        specs::types::SpecsKey,
        types::accounting::{Balance, Strategy},
    };
    use alloy_dyn_abi::DynSolType;
    use core_common::{
        B256, DynSolValue, U128, U256,
        constants::TOKEN_UNIT_SCALE,
        types::{global::TokenAddress, primitives::TokenSymbol},
        util::tokenize::{Tokenizable, generate_schema},
    };
    use core_macros::{AbiToken, dec};
    use std::collections::HashMap;

    #[derive(AbiToken, Debug, Default, PartialEq, Clone)]
    struct TestNewType(U128);

    #[derive(AbiToken, Debug, Default, PartialEq, Clone)]
    struct TestWithNamedFields {
        foo: U128,
        bar: U128,
        many: Vec<U128>,
        raw: Vec<u8>,
        mapping: HashMap<B256, U128>,
        bool: bool,
    }

    #[derive(AbiToken, Debug, PartialEq, Clone)]
    enum Foo {
        A,
        B,
    }

    #[derive(AbiToken, Debug, PartialEq, Clone)]
    enum Bar {
        D,
        E(B256),
        F(B256, U256),
    }

    #[derive(AbiToken, Debug, PartialEq, Clone)]
    struct TestWithSimpleEnum {
        foo: Foo,
    }

    #[derive(AbiToken, Debug, PartialEq, Clone)]
    struct TestWithEnums {
        foo: Foo,
        bar: Bar,
        many: Vec<TestNewType>,
    }

    #[derive(Debug, PartialEq, Clone, AbiToken)]
    pub enum TestComplexEnum {
        Number(Vec<U128>),
        NoTransition,
    }

    #[test]
    fn test_abi_encode_complex_enum() {
        let test = TestComplexEnum::NoTransition;
        let token = test.clone().into_token();
        assert_eq!(format!("{:?}", token), "Tuple([Uint(1, 256)])");
        let test2 = TestComplexEnum::from_token(token).unwrap();
        assert_eq!(test, test2);

        let test = TestComplexEnum::Number(vec![]);
        let token = test.clone().into_token();
        assert_eq!(format!("{:?}", token), "Tuple([Uint(0, 256), Array([])])");
        let test2 = TestComplexEnum::from_token(token).unwrap();
        assert_eq!(test, test2);
    }

    #[test]
    fn test_abi_encode_newtype() {
        let test = TestNewType(U128::ZERO);
        let token = test.clone().into_token();
        assert_eq!(format!("{:?}", token), "Uint(0, 128)");
        let test2 = TestNewType::from_token(token).unwrap();
        assert_eq!(test, test2);
    }

    #[test]
    fn test_abi_encode_fields() {
        let mut mapping = HashMap::new();
        let _num: U256 = U256::from(1);
        mapping.insert(B256::ZERO, U128::from(1));
        let test = TestWithNamedFields {
            foo: Default::default(),
            bar: Default::default(),
            many: vec![U128::ZERO, U128::from(1)],
            raw: vec![0_u8, 1_u8],
            mapping,
            bool: true,
        };
        let token = DynSolValue::Tuple(vec![test.clone().into_token()]);
        let bytes = token.abi_encode();
        let schema: DynSolType = generate_schema(&token).into();
        let token2 = schema
            .abi_decode(&bytes)
            .unwrap()
            .as_tuple()
            .unwrap()
            .first()
            .unwrap()
            .clone();
        assert_eq!(
            format!("{:?}", token2),
            "Tuple([Uint(0, 128), Uint(0, 128), Array([Uint(0, 128), Uint(1, 128)]), Bytes([0, 1]), Tuple([Array([FixedBytes(0x0000000000000000000000000000000000000000000000000000000000000000, 32)]), Array([Uint(1, 128)])]), Bool(true)])"
        );
        let test2 = TestWithNamedFields::from_token(token2).unwrap();
        assert_eq!(test, test2);
    }

    #[test]
    fn test_abi_encode_with_simple_enum() {
        let test = TestWithSimpleEnum { foo: Foo::A };
        let token = test.clone().into_token();
        assert_eq!(format!("{:?}", token), "Tuple([Tuple([Uint(0, 256)])])");
        let test2 = TestWithSimpleEnum::from_token(token).unwrap();
        assert_eq!(test, test2);
    }

    #[test]
    fn test_abi_encode_with_enums() {
        let test = TestWithEnums {
            foo: Foo::A,
            bar: Bar::E(B256::ZERO),
            many: vec![TestNewType::default(), TestNewType(U128::from(1))],
        };
        let token = test.into_token();
        assert_eq!(
            format!("{:?}", token),
            "Tuple([Tuple([Uint(0, 256)]), Tuple([Uint(1, 256), FixedBytes(0x0000000000000000000000000000000000000000000000000000000000000000, 32)]), Array([Uint(0, 128), Uint(1, 128)])])"
        );
        let test = TestWithEnums {
            foo: Foo::B,
            bar: Bar::F(B256::ZERO, U256::from(1)),
            many: vec![TestNewType::default(), TestNewType(U128::from(1))],
        };
        let token = test.into_token();
        assert_eq!(
            format!("{:?}", token),
            "Tuple([Tuple([Uint(1, 256)]), Tuple([Uint(2, 256), FixedBytes(0x0000000000000000000000000000000000000000000000000000000000000000, 32), Uint(1, 256)]), Array([Uint(0, 128), Uint(1, 128)])])"
        );
    }

    #[test]
    fn test_abi_encode_strategy() {
        let mut scaled_dec = dec!(1);
        scaled_dec.set_scale(TOKEN_UNIT_SCALE).unwrap();
        let strategy = Strategy {
            avail_collateral: Balance::new(scaled_dec.into(), TokenSymbol::USDC),
            locked_collateral: Balance::new(scaled_dec.into(), TokenSymbol::USDC),
            max_leverage: 20,
            frozen: false,
        };
        let token = DynSolValue::Tuple(vec![strategy.clone().into_token()]);
        let bytes = token.abi_encode();
        let schema: DynSolType = generate_schema(&token).into();
        let token2 = schema
            .abi_decode(&bytes)
            .unwrap()
            .as_tuple()
            .unwrap()
            .first()
            .unwrap()
            .clone();
        // Based on the struct StrategyData in DepositDefs.sol, the available collateral is uint256 and the locked collateral is uint128
        assert_eq!(
            format!("{:?}", token2),
            format!(
                "Tuple([Tuple([Array([Address({})]), Array([Uint(1, 256)])]), Tuple([Array([Address({})]), Array([Uint(1, 128)])]), Uint(20, 64), Bool(false)])",
                TokenAddress::from(TokenSymbol::USDC),
                TokenAddress::from(TokenSymbol::USDC)
            )
        );
        let strategy2 = Strategy::from_token(token2).unwrap();
        assert_eq!(strategy, strategy2);
    }

    #[test]
    fn test_abi_encode_specs_key() {
        let specs_key = SpecsKey::single_name_perpetual("TESTP".to_string());
        let token = specs_key.clone().into_token();
        let bytes = token.abi_encode();
        let schema: DynSolType = generate_schema(&token).into();
        println!("specs key token schema: {:?}", schema);
        let token2 = schema.abi_decode(&bytes).unwrap();
        // Based on the struct StrategyData in DepositDefs.sol, the available collateral is uint256 and the locked collateral is uint128
        let specs_key2 = SpecsKey::from_token(token2).unwrap();
        assert_eq!(specs_key, specs_key2);
    }
}
