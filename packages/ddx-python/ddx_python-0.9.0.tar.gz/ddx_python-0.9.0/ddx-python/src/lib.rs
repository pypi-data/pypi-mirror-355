#![allow(clippy::needless_option_as_deref)]
use pyo3::prelude::*;

mod ddx;
mod decimal;
mod h256;

trait SubModule {
    const NAME: &'static str;

    fn init_submodule(py: Python, module: &PyModule) -> PyResult<()>;
    fn finish_submodule(py: &Python, module: &PyModule) -> PyResult<()>;

    fn add_submodule(py: Python, parent_mod: &PyModule) -> PyResult<()> {
        let module = PyModule::new(py, Self::NAME)?;
        Self::init_submodule(py, module)?;
        parent_mod.add_submodule(module)?;
        Self::finish_submodule(&py, module)?;
        Ok(())
    }
}

/// Rust bindings and utils for Python
///
/// Note the pyo3 name aliasing to `_rust`, expected usage is: `from ddx._rust import ...`.
#[pymodule]
#[pyo3(name = "_rust")]
pub fn ddx_python(py: Python, module: &PyModule) -> PyResult<()> {
    decimal::add_submodule(py, module)?;
    h256::add_submodule(py, module)?;
    ddx::add_submodule(py, module)?;

    Ok(())
}
