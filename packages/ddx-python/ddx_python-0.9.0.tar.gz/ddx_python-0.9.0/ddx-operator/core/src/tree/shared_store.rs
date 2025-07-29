use crate::util::convert::poison_err;
use sparse_merkle_tree::{
    H256,
    error::Error,
    traits::Store,
    tree::{BranchNode, LeafNode},
};
#[cfg(feature = "python")]
use std::ops::Deref;
use std::{
    collections::HashMap,
    fmt::Debug,
    sync::{Arc, RwLock},
};

/// A thread safe implementation of the SMT store that wraps the branch and leaf maps into
/// a reference-counting pointer and reader-writer lock.
///
/// This type of lock allows reading of values without blocking the thread. This is sufficient
/// for our use case since writing is always done on a single thread. An observer thread reads
/// the state following updates to notify external subscribers of changes.
#[derive(Debug, Clone, Default)]
pub struct ConcurrentStore<T> {
    branches_map: Arc<RwLock<HashMap<H256, BranchNode>>>,
    leaves_map: Arc<RwLock<HashMap<H256, LeafNode<T>>>>,
}

impl<T: Debug + Clone + Default> ConcurrentStore<T> {
    pub fn is_empty(&self) -> bool {
        self.branches_map.read().expect("read").is_empty()
            && self.leaves_map.read().expect("read").is_empty()
    }

    pub fn empty() -> Self {
        Self::default()
    }

    pub fn leaves_map(&self) -> Arc<RwLock<HashMap<H256, LeafNode<T>>>> {
        self.leaves_map.clone()
    }

    // get the size of leaves_map
    pub fn leaves_map_size(&self) -> usize {
        self.leaves_map.read().expect("read").len()
    }

    #[cfg(feature = "python")]
    pub fn deep_copy(&self) -> Self {
        let branch_guard = self.branches_map.read().unwrap();
        let branches_map = branch_guard.deref().clone();
        let leaves_guard = self.leaves_map.read().unwrap();
        let leaves_map = leaves_guard.deref().clone();
        ConcurrentStore {
            branches_map: Arc::new(RwLock::new(branches_map)),
            leaves_map: Arc::new(RwLock::new(leaves_map)),
        }
    }
}

impl<T: Debug + Clone> Store<T> for ConcurrentStore<T> {
    fn get_branch(&self, node: &H256) -> Result<Option<BranchNode>, Error> {
        Ok(self
            .branches_map
            .read()
            .map_err(poison_err)?
            .get(node)
            .cloned())
    }
    fn get_leaf(&self, leaf_hash: &H256) -> Result<Option<LeafNode<T>>, Error> {
        Ok(self
            .leaves_map
            .read()
            .map_err(poison_err)?
            .get(leaf_hash)
            .cloned())
    }
    fn insert_branch(&mut self, node: H256, branch: BranchNode) -> Result<(), Error> {
        self.branches_map
            .write()
            .map_err(poison_err)?
            .insert(node, branch);
        Ok(())
    }
    fn insert_leaf(&mut self, leaf_hash: H256, leaf: LeafNode<T>) -> Result<(), Error> {
        self.leaves_map
            .write()
            .map_err(poison_err)?
            .insert(leaf_hash, leaf);
        Ok(())
    }
    fn remove_branch(&mut self, node: &H256) -> Result<(), Error> {
        self.branches_map.write().map_err(poison_err)?.remove(node);
        Ok(())
    }
    fn remove_leaf(&mut self, leaf_hash: &H256) -> Result<(), Error> {
        self.leaves_map
            .write()
            .map_err(poison_err)?
            .remove(leaf_hash);
        Ok(())
    }
}
