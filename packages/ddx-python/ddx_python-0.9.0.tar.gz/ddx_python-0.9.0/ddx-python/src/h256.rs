pub use core_ddx::tree::shared_smt::exported::python::*;
use pyo3::prelude::*;

use crate::SubModule;

pub(super) struct Module;

// functionality defined in core-ddx/src/tree/shared_smt.rs
impl SubModule for Module {
    const NAME: &'static str = "h256";
    fn init_submodule(py: Python, module: &PyModule) -> PyResult<()> {
        module.add_class::<H256>()?;
        // see https://github.com/PyO3/pyo3/issues/732
        module.add("H256Error", py.get_type::<H256Error>())?;
        Ok(())
    }

    fn finish_submodule(py: &Python, module: &PyModule) -> PyResult<()> {
        // this lets us import like `from ddx_python.decimal import Decimal`
        // https://github.com/PyO3/pyo3/issues/759
        py.import("sys")?
            .getattr("modules")?
            // TODO: Renamed key from `ddx_python.h256` to `ddx._rust.h256`, correct?
            .set_item("ddx._rust.h256", module)?;
        Ok(())
    }
}

pub fn add_submodule(py: Python, parent_mod: &PyModule) -> PyResult<()> {
    Module::add_submodule(py, parent_mod)
}
