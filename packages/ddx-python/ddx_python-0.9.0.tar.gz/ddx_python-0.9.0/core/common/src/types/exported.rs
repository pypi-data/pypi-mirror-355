pub mod python {
    use crate::{
        Error,
        types::{
            global::TokenAddress,
            primitives::{OrderSide, TokenSymbol},
        },
    };
    use pyo3::{PyResult, create_exception, exceptions::PyException, pymethods, types::PyType};
    use std::str::FromStr;

    create_exception!(core_common, CoreCommonError, PyException);

    impl From<Error> for pyo3::PyErr {
        fn from(e: Error) -> Self {
            CoreCommonError::new_err(e.to_string())
        }
    }

    #[pymethods]
    impl TokenSymbol {
        #[classmethod]
        fn from_address(_cls: &PyType, address: TokenAddress) -> Self {
            address.into()
        }

        fn address(&self) -> TokenAddress {
            TokenAddress::from(*self)
        }
    }

    #[pymethods]
    impl OrderSide {
        #[new]
        fn new(name: &str) -> PyResult<Self> {
            Self::from_str(name).map_err(|e| CoreCommonError::new_err(e.to_string()))
        }
    }
}
