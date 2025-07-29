use crate::{
    constants::FIRST_EPOCH_ID,
    specs::types::{SpecsExpr, SpecsKey},
    tree::shared_store::ConcurrentStore,
    types::{
        accounting::Balance,
        identifiers::{EpochMetadataKey, InsuranceFundKey, VerifiedStateKey},
        state::{EpochMetadata, Item, TradableProduct},
    },
};
use alloy_dyn_abi::DynSolValue;
use alloy_primitives::Keccak256;
#[cfg(feature = "fixed_expiry_future")]
use chrono::{DateTime, Utc};
use core_common::{
    Result,
    constants::KECCAK256_DIGEST_SIZE,
    types::primitives::{Hash, UnscaledI128},
    util::tokenize::{TokenSchema, Tokenizable, generate_schema},
};
use sparse_merkle_tree::{
    CompiledMerkleProof, H256, SparseMerkleTree, traits::Value, tree::LeafNode,
};
use std::{
    collections::HashMap,
    fmt,
    sync::{Arc, RwLock},
};

/// Key, leaf hash, abi schema, tokenized value
pub type PackedLeaves = HashMap<Hash, Option<(Hash, TokenSchema, Vec<u8>)>>;

pub struct Keccak256Hasher(Keccak256);

impl Default for Keccak256Hasher {
    fn default() -> Self {
        Keccak256Hasher(Keccak256::new())
    }
}

impl fmt::Debug for Keccak256Hasher {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Keccak256Hasher")
    }
}

impl sparse_merkle_tree::traits::Hasher for Keccak256Hasher {
    fn write_h256(&mut self, h: &H256) {
        // Changed to the 0.4.0-rc1 format
        let input_array: [u8; KECCAK256_DIGEST_SIZE] = h.copy_bits(0_u8).into();
        self.0.update(input_array);
    }

    fn finish(self) -> H256 {
        let output = self.0.finalize();
        let output_array: [u8; KECCAK256_DIGEST_SIZE] = output.into();
        output_array.into()
    }
}

#[cfg(feature = "python")]
pub mod exported {
    pub mod python {
        use core_common::constants::KECCAK256_DIGEST_SIZE;
        use pyo3::{
            create_exception,
            exceptions::PyException,
            prelude::*,
            types::{PyBytes, PyType},
        };
        use rustc_hex::ToHex;
        use sparse_merkle_tree::H256 as RustH256;
        use std::borrow::Cow;

        create_exception!(h256, H256Error, PyException);

        /// Wrapped sparse_merkle_tree::H256.
        #[pyclass]
        #[derive(Eq, PartialEq, Debug, Default, Hash, Clone, Copy)]
        pub struct H256 {
            inner: RustH256,
        }

        #[pymethods]
        impl H256 {
            #[classmethod]
            pub fn from_bytes(_cls: &PyType, b: &[u8]) -> PyResult<Self> {
                TryInto::<[u8; KECCAK256_DIGEST_SIZE]>::try_into(b)
                    .map_err(|e| H256Error::new_err(format!("Invalid length for H256: {}", e)))
                    .map(|b| H256 {
                        inner: RustH256::from(b),
                    })
            }

            pub fn as_bytes(&self) -> Cow<[u8]> {
                self.inner.as_slice().into()
            }

            #[staticmethod]
            pub fn zero() -> Self {
                H256 {
                    inner: RustH256::zero(),
                }
            }

            pub fn is_zero(&self) -> bool {
                self.inner == RustH256::zero()
            }

            pub fn get_bit(&self, i: u8) -> bool {
                self.inner.get_bit(i)
            }

            pub fn set_bit(&mut self, i: u8) {
                self.inner.set_bit(i)
            }

            pub fn clear_bit(&mut self, i: u8) {
                self.inner.clear_bit(i)
            }

            pub fn fork_height(&self, key: &H256) -> u8 {
                self.inner.fork_height(&key.inner)
            }

            pub fn parent_path(&self, height: u8) -> Self {
                H256 {
                    inner: self.inner.parent_path(height),
                }
            }

            pub fn copy_bits(&self, start: u8) -> Self {
                H256 {
                    inner: self.inner.copy_bits(start),
                }
            }

            // ######################################################################
            // # State methods
            //
            // These state implementations may be best served by the `#[get]` and `#[set]` macros.
            // Infallible code returning result monads is probably not correct.
            //
            // See https://gist.github.com/ethanhs/fd4123487974c91c7e5960acc9aa2a77
            fn __setstate__(&mut self, py: Python, state: PyObject) -> PyResult<()> {
                state.extract::<&PyBytes>(py).map(|bytes| {
                    let mut buf: [u8; KECCAK256_DIGEST_SIZE] = Default::default();
                    buf.copy_from_slice(bytes.as_bytes());
                    self.inner = buf.into()
                })
            }

            fn __getstate__(&mut self, py: Python) -> PyResult<PyObject> {
                Ok(PyBytes::new(py, self.inner.as_slice()).to_object(py))
            }
            // ######################################################################

            fn __repr__(&self) -> String {
                format!("0x{}", self.inner.as_slice().to_hex::<String>())
            }

            fn __str__(&self) -> String {
                self.__repr__()
            }

            fn __eq__(&self, other: &Self) -> bool {
                self == other
            }
        }

        impl From<RustH256> for H256 {
            fn from(h256: RustH256) -> Self {
                H256 { inner: h256 }
            }
        }

        impl From<H256> for RustH256 {
            fn from(h256: H256) -> Self {
                h256.inner
            }
        }
    }
}

pub type SharedSparseMerkleTree = SparseMerkleTree<Keccak256Hasher, Item, ConcurrentStore<Item>>;
pub type LeavesMap = Arc<RwLock<HashMap<H256, LeafNode<Item>>>>;

/// Pruned SMT keeping only the leaves
///
/// This is useful to package the SMT data for backup or external copies.
pub type NonEmptyLeaves = HashMap<Hash, Item>;

pub(crate) fn from_genesis(
    insurance_fund_cap: Balance,
    ddx_fee_pool: UnscaledI128,
    specs: &HashMap<SpecsKey, SpecsExpr>,
    #[cfg(feature = "fixed_expiry_future")] current_time: DateTime<Utc>,
) -> Result<SharedSparseMerkleTree> {
    let mut tree = SharedSparseMerkleTree::new(Default::default(), ConcurrentStore::empty());

    // TODO: Consider whether to split the insurance fund across multiple leaves
    let leaf_key = InsuranceFundKey::new().encode_key();
    tracing::debug!(?leaf_key, "Inserting empty insurance fund into smt");
    tree.update(leaf_key.into(), Item::InsuranceFund(insurance_fund_cap))?;
    // Insert an empty epoch metadata
    let leaf_key = EpochMetadataKey::new(&FIRST_EPOCH_ID).encode_key();
    tracing::debug!(?leaf_key, "Inserting empty epoch metadata into smt");
    tree.update(
        leaf_key.into(),
        Item::EpochMetadata(EpochMetadata {
            ddx_fee_pool,
            next_book_ordinals: HashMap::new(),
        }),
    )?;

    for (specs_key, specs) in specs.iter() {
        let leaf_key = specs_key.encode_key();
        tracing::debug!(?specs_key, ?leaf_key, "Inserting specs leaf key into smt");
        tree.update(leaf_key.into(), Item::Specs(specs.clone()))?;

        #[cfg(feature = "fixed_expiry_future")]
        tracing::debug!(
            ?current_time,
            ?specs_key,
            "Determining tradable products from specs"
        );
        let tradable_products = specs_key.current_tradable_products(
            #[cfg(feature = "fixed_expiry_future")]
            current_time,
        );
        tracing::debug!(?tradable_products, "Inserting tradable products into smt");
        for tradable_product_key in tradable_products {
            let leaf_key = tradable_product_key.encode_key();
            tracing::debug!(
                ?tradable_product_key,
                ?leaf_key,
                "Inserting tradable product leaf key into smt"
            );
            tree.update(leaf_key.into(), Item::TradableProduct(TradableProduct))?;
        }
    }

    Ok(tree)
}

pub struct SharedTree(SharedSparseMerkleTree);

impl SharedTree {
    pub fn from_genesis(
        insurance_fund_cap: Balance,
        ddx_fee_pool: UnscaledI128,
        specs: &HashMap<SpecsKey, SpecsExpr>,
        #[cfg(feature = "fixed_expiry_future")] current_time: DateTime<Utc>,
    ) -> Result<Self> {
        let tree = from_genesis(
            insurance_fund_cap,
            ddx_fee_pool,
            specs,
            #[cfg(feature = "fixed_expiry_future")]
            current_time,
        )?;
        Ok(Self(tree))
    }

    pub fn from_store(store: ConcurrentStore<Item>, root: Hash) -> Self {
        debug_assert!(!store.is_empty() && !H256::from(root).is_zero());
        let smt = SharedSparseMerkleTree::new(root.into(), store);
        Self(smt)
    }

    #[cfg(test)]
    pub fn with_empty_store() -> Self {
        let root: H256 = Default::default();
        let smt = SharedSparseMerkleTree::new(root, ConcurrentStore::empty());
        Self(smt)
    }

    #[cfg(test)]
    pub fn is_empty(&self) -> bool {
        self.0.root().is_zero()
    }

    pub fn root(&self) -> Hash {
        self.0.root().into()
    }

    pub fn get(&self, key: &Hash) -> Result<Item> {
        tracing::trace!("Get key {:?} from tree {:#?}", key, self);
        let item = self.0.get(&H256::from(*key))?;
        tracing::trace!("Got item {:?}", item);
        Ok(item)
    }

    pub fn update(&mut self, key: Hash, value: Item) -> Result<()> {
        tracing::trace!("Update key {:?} with value {:?}", key, value);
        self.0.update(H256::from(key), value)?;
        Ok(())
    }

    fn collect_leaves(&self, keys: &[Hash]) -> Result<Vec<(H256, H256)>> {
        keys.iter()
            .map(|k| {
                let k = H256::from(*k);
                let v = self.0.get(&k)?;
                Ok((k, v.to_h256()))
            })
            .collect()
    }

    pub fn leaves_map(&self) -> LeavesMap {
        self.0.store().leaves_map()
    }

    /// Collect all leaves at once in memory
    ///
    /// This simple approach minimizes lock duration by copying values to a buffer
    /// but should evolve into a streaming or paging reader past some leaf threashold.
    pub fn pack_leaves(&mut self) -> PackedLeaves {
        let leaves_ = self.0.store().leaves_map();
        let leaves = leaves_.read().unwrap();
        leaves
            .iter()
            .map(|(hash, leaf)| {
                debug_assert!(
                    !matches!(leaf.value, Item::Empty),
                    "Unexpected empty value in leaves_map {:?}",
                    Hash::from(leaf.key)
                );
                let token = DynSolValue::Tuple(vec![leaf.value.clone().into_token()]);
                let schema = generate_schema(&token);
                let content = token.abi_encode();
                (leaf.key.into(), Some((hash.into(), schema, content)))
            })
            .collect()
    }

    #[tracing::instrument(level = "trace", skip_all, fields(keys=%keys.len()))]
    pub fn compiled_merkle_proof(&self, keys: &[Hash]) -> Result<CompiledMerkleProof> {
        // No keys require no proof. It's easier than adding error conditions.
        if keys.is_empty() {
            return Ok(CompiledMerkleProof(vec![]));
        }
        let proof = self
            .0
            .merkle_proof(keys.iter().map(|k| (*k).into()).collect())?;
        let leaves = self.collect_leaves(keys)?;
        let compiled_proof = proof.compile(leaves)?;
        Ok(compiled_proof)
    }
}

/// Displaying only the root and leaves of the inner `SMT`
impl fmt::Debug for SharedTree {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let leaves_ref = self.0.store().leaves_map();
        let leaves = leaves_ref.read().unwrap();
        let root = self.0.root();
        f.debug_struct("SharedTree")
            .field("root", &Hash::from(root))
            .field(
                "leaves",
                &leaves
                    .iter()
                    .map(|(h, v)| {
                        format!(
                            "{:?} -> {:?} {:?}",
                            Hash::from(v.key),
                            v.value,
                            Hash::from(h),
                        )
                    })
                    .collect::<Vec<String>>(),
            )
            .finish()
    }
}

#[cfg(test)]
pub mod tests {
    use super::*;
    use crate::{
        execution::test_utils::current_time,
        types::{
            accounting::Price,
            identifiers::VerifiedStateKey,
            state::{BookOrder, Item, Trader},
        },
    };
    use core_common::{
        constants::{MAX_UNSCALED_DECIMAL, TOKEN_UNIT_SCALE, TRADER_ADDRESS_BYTE_LEN},
        types::primitives::{OrderSide, TraderAddress},
    };
    use rand::Rng;
    use rust_decimal::Decimal;
    use serde::{Deserialize, Serialize};
    use sparse_merkle_tree::{H256, MerkleProof, error::Error as SmtError};

    /// List of keys used to request a Merkle proof
    type ProofRequest = Vec<Hash>;

    #[derive(Debug, Clone, Serialize, Deserialize)]
    struct LeafKeyValue {
        key: Hash,
        value: Item,
    }

    #[derive(Debug, Clone, Serialize, Deserialize)]
    #[serde(rename_all = "camelCase")]
    struct MerkleProofDump {
        pub root_hash: Hash,
        pub proof_request: ProofRequest,
        pub leaves_map: HashMap<Hash, LeafKeyValue>,
        pub compiled_proof: Vec<u8>,
    }

    impl MerkleProofDump {
        pub fn take(
            self,
        ) -> (
            H256,
            Vec<H256>,
            SharedSparseMerkleTree,
            CompiledMerkleProof,
            Vec<(H256, H256)>,
        ) {
            let MerkleProofDump {
                root_hash,
                proof_request,
                leaves_map,
                compiled_proof,
            } = self;
            let mut smt = SharedSparseMerkleTree::default();
            let mut kv = vec![];
            for (_, leaf_kv) in leaves_map.into_iter() {
                kv.push((leaf_kv.key.into(), leaf_kv.value.to_h256()));
                smt.update(leaf_kv.key.into(), leaf_kv.value).unwrap();
            }
            (
                root_hash.into(),
                proof_request.into_iter().map(|h| h.into()).collect(),
                smt,
                CompiledMerkleProof(compiled_proof),
                kv,
            )
        }
    }

    #[test]
    fn test_get_by_key() {
        let mut tree = SharedSparseMerkleTree::default();
        assert_eq!(tree.get(&H256::zero()).expect("get"), Item::default());
        let key = H256::from([1; 32]);
        let value = Item::Price(Default::default());
        tree.update(key, value.clone()).expect("update");
        let item = tree.get(&key).unwrap();
        assert_eq!(value, item);
    }

    #[test]
    fn test_default_tree() {
        let mut tree = SharedSparseMerkleTree::default();
        assert_eq!(tree.get(&H256::zero()).expect("get"), Item::default());
        tree.update(H256::from([1; 32]), Item::default())
            .expect("update");
        let proof = tree.merkle_proof(vec![H256::zero()]).expect("merkle proof");
        let _root = proof
            .compute_root::<Keccak256Hasher>(vec![(H256::zero(), H256::zero())])
            .expect("root");
        let proof = tree.merkle_proof(vec![H256::zero()]).expect("merkle proof");
        let _root2 = proof
            .compute_root::<Keccak256Hasher>(vec![(H256::zero(), [42u8; 32].into())])
            .expect("root");
    }

    fn test_merkle_proof_verify_only(
        tree: &mut SharedSparseMerkleTree,
        key: H256,
        value: H256,
        index: u64,
    ) {
        const EXPECTED_PROOF_SIZE: usize = 16;
        if !tree.is_empty() {
            let proof = tree.merkle_proof(vec![key]).expect("proof");
            let compiled_proof = proof
                .clone()
                .compile(vec![(key, value)])
                .expect("compile proof");
            assert!(
                (index == 0 && proof.proof().is_empty())
                    || (!proof.proof().is_empty() && proof.proof().len() < EXPECTED_PROOF_SIZE)
            );
            assert!(
                proof
                    .verify::<Keccak256Hasher>(tree.root(), vec![(key, value)])
                    .expect("verify")
            );
            assert!(
                compiled_proof
                    .verify::<Keccak256Hasher>(tree.root(), vec![(key, value)])
                    .expect("compiled verify")
            );
        }
    }

    #[test]
    fn test_multiple_leaves_merkle_proof() {
        let mut tree = SharedSparseMerkleTree::default();
        for i in 0..5_u64 {
            let mut key = [0_u8; KECCAK256_DIGEST_SIZE];
            rand::thread_rng().fill(&mut key);
            let price = rand::thread_rng().gen_range(0_i128..79228162514264337593543950335_i128);
            let amount = rand::thread_rng().gen_range(0_i128..79228162514264337593543950335_i128);
            let item = Item::BookOrder(BookOrder {
                side: OrderSide::Bid,
                amount: Decimal::from_i128_with_scale(amount, TOKEN_UNIT_SCALE).into(),
                price: Decimal::from_i128_with_scale(price, TOKEN_UNIT_SCALE).into(),
                trader_address: Default::default(),
                strategy_id_hash: Default::default(),
                book_ordinal: 0,
                time_value: current_time(),
            });
            tree.update(key.into(), item.clone()).expect("update");
            test_merkle_proof_verify_only(&mut tree, key.into(), item.to_h256(), i)
        }
    }

    #[test]
    fn test_default_merkle_proof() {
        let proof = MerkleProof::new(Default::default(), Default::default());
        let result =
            proof.compute_root::<Keccak256Hasher>(vec![([42u8; 32].into(), [42u8; 32].into())]);
        assert_eq!(
            result.unwrap_err(),
            SmtError::IncorrectNumberOfLeaves {
                expected: 0,
                actual: 1,
            }
        );
        // makes room for leaves
        let proof = MerkleProof::new(vec![Vec::new()], Default::default());
        let root = proof
            .compute_root::<Keccak256Hasher>(vec![([42u8; 32].into(), [42u8; 32].into())])
            .expect("compute root");
        assert_ne!(root, H256::zero());
    }

    #[test]
    fn test_delete_a_leaf() {
        let mut tree = SharedSparseMerkleTree::default();
        let key = [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0,
        ]
        .into();
        let value = Item::Trader(Trader::default());
        tree.update(key, value).unwrap();
        assert_ne!(tree.root(), &H256::zero());
        let root = *tree.root();
        let _store = tree.store().clone();

        // insert another leaf
        let key = [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 1,
        ]
        .into();
        let value = Item::Trader(Trader::default());
        tree.update(key, value).unwrap();
        assert_ne!(tree.root(), &root);

        // delete a leaf by inserting an empty `Item`
        tree.update(key, Item::Empty).unwrap();
        assert_eq!(tree.root(), &root);
    }

    #[test]
    fn test_shared_tree() {
        let mut tree = SharedTree::with_empty_store();
        let key = [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0,
        ]
        .into();
        let value = Item::Trader(Trader::default());
        tree.0.update(key, value).unwrap();
        assert_ne!(tree.0.root(), &H256::zero());
        // The second tree should have a copy of the root and reference to the data
        let mut tree2 = SharedTree::from_store(tree.0.store().clone(), tree.root());
        assert_ne!(tree.0.root(), &H256::zero());
        // Confirm the same data by forcing root recalculation
        tree2.0.update(key, Item::Empty).unwrap();
        assert_eq!(tree2.0.root(), &H256::zero());
    }

    fn test_merkle_proof(key: H256, value: Item) {
        const EXPECTED_PROOF_SIZE: usize = 16;

        let mut tree = SharedTree::with_empty_store();
        tree.0.update(key, value.clone()).expect("update");
        if !tree.is_empty() {
            let proof = tree.0.merkle_proof(vec![key]).expect("proof");
            let compiled_proof = proof
                .clone()
                .compile(vec![(key, value.to_h256())])
                .expect("compile proof");
            assert!(proof.proof().len() < EXPECTED_PROOF_SIZE);
            assert!(
                proof
                    .verify::<Keccak256Hasher>(tree.0.root(), vec![(key, value.to_h256())])
                    .expect("verify")
            );
            assert!(
                compiled_proof
                    .verify::<Keccak256Hasher>(tree.0.root(), vec![(key, value.to_h256())])
                    .expect("compiled verify")
            );
        }
    }

    #[test]
    fn test_simple_merkle_proof() {
        let key = [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 1,
        ]
        .into();
        let value = Item::Price(Price {
            index_price: Default::default(),
            mark_price_metadata: Default::default(),
            ordinal: 0,
            time_value: 0,
        });
        test_merkle_proof(key, value);
    }

    #[test]
    #[ignore = "No failing proof to test with"]
    fn test_failing_proof1() {
        let json = r#"
{
  "rootHash": "0x12cd8f4170f9462677cff72aefbd79b41bdc4a28bdc0241d8a37b0f76582eeb8",
  "proofRequest": [
    "0x16b9f0008b1c67badb7675314757bbf175412a506e7b2109a66fca16d323a324",
    "0x3d70bffb22e1d485906d0297f7e45af165c2604fca1081f9a29252491ecd670b"
  ],
  "leavesMap": {
    "0x8f0b625474ff15bfff48f5a233e1f538d8da94027e83658d81079a848d966737": {
      "key": "0x16b9f0008b1c67badb7675314757bbf175412a506e7b2109a66fca16d323a324",
      "value": {
        "Strategy": {
          "margin": {
            "0x0b1ba0af832d7c05fd64161e0db78e85978e8082": "0x43c33c1937564800000"
          },
          "lockedCollateral": {},
          "maxLeverage": "0x14",
          "frozen": false
        }
      }
    },
    "0xe3ac50e5e2dd1149d768550c29473d91e5dce8004c250921bd3d8f5915f391e5": {
      "key": "0x3d70bffb22e1d485906d0297f7e45af165c2604fca1081f9a29252491ecd670b",
      "value": {
        "Trader": {
          "avail_ddx_balance": "0x0",
          "locked_ddx_balance": "0x0",
          "referral_address": "0x0000000000000000000000000000000000000000"
        }
      }
    }
  },
  "compiledProof": [
    76,
    76,
    72,
    253
  ]
}
"#;
        let dump: MerkleProofDump = serde_json::from_str(json).unwrap();
        let (root_hash, proof_request, mut tree, proof, kv) = dump.take();
        let computed_root_hash = *tree.root();
        assert_eq!(root_hash, computed_root_hash);
        for (i, (key, value)) in kv.iter().enumerate() {
            test_merkle_proof_verify_only(&mut tree, *key, *value, i as u64);
        }
        let uncompiled_proof = tree.merkle_proof(proof_request).unwrap();
        println!("Uncompiled proof {:?}", uncompiled_proof);
        // TODO: Is these normal? Is proving the whole tree resulting in empty proof?
        // assert!(
        //     !uncompiled_proof.proof().is_empty(),
        //     "Empty uncompiled proof"
        // );
        let compiled_proof = uncompiled_proof.compile(kv).unwrap();
        println!("Compiled proof {:?}", compiled_proof);
        assert_eq!(compiled_proof.0, proof.0);
    }

    /// this test shows that a single proof from an initial state
    /// can be used to verify the state root after updates as well,
    /// so long as the updates are constrained to the same leaves in the
    /// initial proof request
    #[test]
    fn single_proof_works_after_updates() {
        let mut rng = rand::thread_rng();
        let mut smt = SharedSparseMerkleTree::default();

        let trader_address_one =
            TraderAddress::from_slice(&rng.gen::<[u8; TRADER_ADDRESS_BYTE_LEN]>());

        let trader_one = Trader {
            ..Default::default()
        };

        let trader_address_two =
            TraderAddress::from_slice(&rng.gen::<[u8; TRADER_ADDRESS_BYTE_LEN]>());

        let mut trader_two = Trader {
            ..Default::default()
        };

        smt.update(
            trader_address_one.encode_key().into(),
            Item::Trader(trader_one.clone()),
        )
        .unwrap();
        smt.update(
            trader_address_two.encode_key().into(),
            Item::Trader(trader_two.clone()),
        )
        .unwrap();

        let root_before = *smt.root();

        let proof = smt
            .merkle_proof(vec![
                trader_address_two.encode_key().into(),
                trader_address_one.encode_key().into(),
            ])
            .unwrap();

        assert!(
            proof
                .clone()
                .verify::<Keccak256Hasher>(
                    &root_before,
                    vec!(
                        (
                            trader_address_two.encode_key().into(),
                            Item::Trader(trader_two.clone()).to_h256()
                        ),
                        (
                            trader_address_one.encode_key().into(),
                            Item::Trader(trader_one.clone()).to_h256()
                        )
                    )
                )
                .unwrap()
        );

        trader_two.avail_ddx_balance = MAX_UNSCALED_DECIMAL.into();

        smt.update(
            trader_address_two.encode_key().into(),
            Item::Trader(trader_two.clone()),
        )
        .unwrap();

        let root_after = *smt.root();

        assert!(
            proof
                .verify::<Keccak256Hasher>(
                    &root_after,
                    vec!(
                        (
                            trader_address_two.encode_key().into(),
                            Item::Trader(trader_two).to_h256()
                        ),
                        (
                            trader_address_one.encode_key().into(),
                            Item::Trader(trader_one).to_h256()
                        )
                    )
                )
                .unwrap()
        );
    }

    /// this test shows that a change to a leaf not in the original proof request
    /// causes verification to fail
    #[test]
    fn single_proof_works_no_out_of_band_update() {
        let mut rng = rand::thread_rng();
        let mut smt = SharedSparseMerkleTree::default();

        let trader_address_one =
            TraderAddress::from_slice(&rng.gen::<[u8; TRADER_ADDRESS_BYTE_LEN]>());

        let trader_one = Trader {
            ..Default::default()
        };

        let trader_address_two =
            TraderAddress::from_slice(&rng.gen::<[u8; TRADER_ADDRESS_BYTE_LEN]>());

        let mut trader_two = Trader {
            ..Default::default()
        };

        let trader_address_three =
            TraderAddress::from_slice(&rng.gen::<[u8; TRADER_ADDRESS_BYTE_LEN]>());

        let mut trader_three = Trader {
            ..Default::default()
        };

        smt.update(
            trader_address_one.encode_key().into(),
            Item::Trader(trader_one.clone()),
        )
        .unwrap();
        smt.update(
            trader_address_two.encode_key().into(),
            Item::Trader(trader_two.clone()),
        )
        .unwrap();
        smt.update(
            trader_address_three.encode_key().into(),
            Item::Trader(trader_three.clone()),
        )
        .unwrap();

        let root_before = *smt.root();

        let proof = smt
            .merkle_proof(vec![
                trader_address_two.encode_key().into(),
                trader_address_one.encode_key().into(),
            ])
            .unwrap();

        assert!(
            proof
                .clone()
                .verify::<Keccak256Hasher>(
                    &root_before,
                    vec!(
                        (
                            trader_address_two.encode_key().into(),
                            Item::Trader(trader_two.clone()).to_h256()
                        ),
                        (
                            trader_address_one.encode_key().into(),
                            Item::Trader(trader_one.clone()).to_h256()
                        )
                    )
                )
                .unwrap()
        );

        trader_two.avail_ddx_balance = MAX_UNSCALED_DECIMAL.into();

        smt.update(
            trader_address_two.encode_key().into(),
            Item::Trader(trader_two.clone()),
        )
        .unwrap();

        // here is the out of band change to a leaf not included in
        // the original proof request
        trader_three.avail_ddx_balance = MAX_UNSCALED_DECIMAL.into();

        smt.update(
            trader_address_three.encode_key().into(),
            Item::Trader(trader_three),
        )
        .unwrap();

        let root_after = *smt.root();

        assert!(
            !proof
                .verify::<Keccak256Hasher>(
                    &root_after,
                    vec!(
                        (
                            trader_address_two.encode_key().into(),
                            Item::Trader(trader_two).to_h256()
                        ),
                        (
                            trader_address_one.encode_key().into(),
                            Item::Trader(trader_one).to_h256()
                        )
                    )
                )
                .unwrap()
        );
    }
}
