use crate::parse_secret_key;
use core_common::{Result, bail, types::primitives::TraderAddress};
use libsecp256k1::SecretKey;

// A set of addresses and private keys that can be used in tests.
pub const ALICE: &str = "0xA8dDa8d7F5310E4A9E24F8eBA77E091Ac264f872";
pub const ALICE_PK: &str = "0xefb595a0178eb79a8df953f87c5148402a224cdf725e88c0146727c6aceadccd";
pub const BOB: &str = "0x603699848c84529987E14Ba32C8a66DEF67E9eCE";
pub const BOB_PK: &str = "0xf18b03c1ae8e3876d76f20c7a5127a169dd6108c55fe9ce78bc7a91aca67dee3";
pub const CHARLIE: &str = "0x5409ED021D9299bf6814279A6A1411A7e866A631";
pub const CHARLIE_PK: &str = "0xf2f48ee19680706196e2e339e5da3491186e0c4c5030670656b0e0164837257d";
pub const DAN: &str = "0xE36Ea790bc9d7AB70C55260C66D52b1eca985f84";
pub const DAN_PK: &str = "0xdf02719c4df8b9b8ac7f551fcb5d9ef48fa27eef7a66453879f4d8fdc6e78fb1";
pub const ED: &str = "0xE834EC434DABA538cd1b9Fe1582052B880BD7e63";
pub const ED_PK: &str = "0xff12e391b79415e941a94de3bf3a9aee577aed0731e297d5cfa0b8a1e02fa1d0";
pub const FRED: &str = "0x78dc5D2D739606d31509C31d654056A45185ECb6";
pub const FRED_PK: &str = "0x752dd9cf65e68cfaba7d60225cbdbc1f4729dd5e5507def72815ed0d8abc6249";

pub fn get_secret_key(trader: &TraderAddress) -> Result<SecretKey> {
    if trader == &TraderAddress::parse_eth_address(ALICE)? {
        parse_secret_key(ALICE_PK)
    } else if trader == &TraderAddress::parse_eth_address(BOB)? {
        parse_secret_key(BOB_PK)
    } else if trader == &TraderAddress::parse_eth_address(CHARLIE)? {
        parse_secret_key(CHARLIE_PK)
    } else if trader == &TraderAddress::parse_eth_address(DAN)? {
        parse_secret_key(DAN_PK)
    } else if trader == &TraderAddress::parse_eth_address(ED)? {
        parse_secret_key(ED_PK)
    } else if trader == &TraderAddress::parse_eth_address(FRED)? {
        parse_secret_key(FRED_PK)
    } else {
        bail!("Static secret key not found");
    }
}
