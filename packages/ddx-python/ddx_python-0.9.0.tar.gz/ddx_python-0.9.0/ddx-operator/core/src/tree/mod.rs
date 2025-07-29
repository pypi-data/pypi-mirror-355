use crate::types::state::Item;
use core_common::{Result, types::primitives::Hash};
/// # Sparse Merkle Tree
/// The execution state includes all data structures that settlement operator reads and write to during execution. The state necessary for execution is stored in a sparse merkle tree. This us allows to generate proofs of inclusion (or non-inclusion) against the root hash (to be stored on-chain).
///
/// ## Construction
/// A sparse merkle tree is a perfectly balanced tree contains 2 ^ N leaves:
///
/// ```ignore
/// # N = 256 sparse merkle tree
/// height:
/// 255                0
///                 /     \
/// 254            0        1
///
/// .............................
///
///            /   \          /  \
/// 2         0     1        0    1
/// 1        / \   / \      / \   / \
/// 0       0   1 0  1 ... 0   1 0   1
///        0x00..00 0x00..01   ...   0x11..11
/// ```
/// The above graph demonstrates a sparse merkle tree with 2 ^ 256 leaves, which can map **every possible H256 value into leaves**. So it can contain lots of data without collisions. The height of the tree is 256, from top to bottom, we denote 0 for each left branch and denote 1 for each right branch, so we can get a 256 bits path. It follows that we may represent any path as `H256`. We use the path as the key of leaves, the most left leaf's key is 0x00..00, and the next key is 0x00..01, the most right key is 0x11..11.
///
/// We use a root `H256` and a map `map[(usize, H256)] -> (H256, H256)` to represent a tree, the key of map is parent node and height, values are children nodes, an empty tree represented in an empty map plus a zero `H256` root.
///
/// This may seem inefficient but, because the tree is only sparsely populated, most nodes have predictable hash values. This gives a simple structure with Merkle proofs that can be compiled "client-side" by simply by pruning the tree.
///
/// #### Schema
///
/// ![](https:///i.imgur.com/JfXjZzL.png)
///
/// The diagram above represents our entity type as leaves of one tree. Each leaf has a key (top) and value (bottom). We established that keys must be `H256` to constitute a path, so we hash each key object `H(key)`. The tree storage contains the key (hashed) / value pairs. This allows us to get the value of a leaf `get(&H(key)) -> Result<V>`. Because we care about relationships between entities and ordering (of the order book for instance), we store indexes that help us find and iterate through leaves.
///
/// #### Use cases for Merkle proofs
/// The use of Merkle proofs includes, but may not be limited to:
///
/// 1. Audit state changes for each checkpoint. The `state_hash` of the previous checkpoint gives us the initial state. Then, we verify the end state by incrementally executing the included settlement transactions.
/// 2. At a more granular level, audit the side-effects of each transaction by comparing the state before / after using their `state_hash`.
/// 3. Audit withdrawals by verifying the inclusion of the frozen margin amount withdrawn in before the `Withdraw` settlement transaction.
/// 4. Audit mark price calculations by verifying the `order book_root_hash` against the order book data available, combined with the `index_price`, resulting in the `mark_price` included in `price_root_hash`.
/// 5. Audit matching engine fairness `Fill` by comparing the order book snapshot included in the `state_hash` of the tx compared to the previous tx.
/// 5. Audit `AccountLiquidation` by evaluating the order book snapshot and latest `mark_price = index_price * ema` included in the `state_hash`.
use std::collections::HashMap;

pub mod shared_smt;
pub mod shared_store;

/// Consistent read interface for low-level verifiable maps
pub trait Read: std::fmt::Debug {
    // Get value from tree by hash
    fn get(&self, key: Hash) -> Result<Item>;
}

/// Logs write access to the verified map with updated values
pub type UpdateLog = HashMap<Hash, Item>;
