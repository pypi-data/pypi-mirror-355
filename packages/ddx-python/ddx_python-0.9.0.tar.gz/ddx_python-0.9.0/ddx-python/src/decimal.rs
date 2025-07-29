use core_common::types::primitives::exported::python::{Decimal, DecimalError};
use pyo3::prelude::*;

use crate::SubModule;

struct Module;

// functionality defined in core-ddx/src/types/primitives/numbers.rs
impl SubModule for Module {
    const NAME: &'static str = "decimal";
    fn init_submodule(py: Python, module: &PyModule) -> PyResult<()> {
        module.add_class::<Decimal>()?;
        // see https://github.com/PyO3/pyo3/issues/732
        module.add("DecimalError", py.get_type::<DecimalError>())?;
        Ok(())
    }

    fn finish_submodule(py: &Python, module: &PyModule) -> PyResult<()> {
        // this lets us import like `from ddx_python.decimal import Decimal`
        // https://github.com/PyO3/pyo3/issues/759
        py.import("sys")?
            .getattr("modules")?
            // TODO: Renamed key from `ddx_python.h256` to `ddx._rust.h256`, correct?
            .set_item("ddx._rust.decimal", module)?;
        Ok(())
    }
}

pub fn add_submodule(py: Python, parent_mod: &PyModule) -> PyResult<()> {
    Module::add_submodule(py, parent_mod)
}
