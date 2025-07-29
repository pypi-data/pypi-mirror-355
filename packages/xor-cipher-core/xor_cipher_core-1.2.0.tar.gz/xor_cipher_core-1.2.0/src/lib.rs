use pyo3::{
    exceptions::PyValueError,
    prelude::{PyAnyMethods, PyByteArrayMethods, PyBytesMethods, PyModuleMethods},
    pyfunction as py_function, pymodule as py_module,
    types::{PyByteArray, PyBytes, PyInt, PyModule},
    wrap_pyfunction as wrap_py_function, Bound, PyResult,
};

static EXPECTED_BYTE: &str = "expected `byte` (`int` in range `[0, 255]`)";

#[py_function]
fn xor<'py>(data: &Bound<'py, PyBytes>, key: &Bound<'py, PyInt>) -> PyResult<Bound<'py, PyBytes>> {
    let rust_key = key
        .extract()
        .map_err(|_| PyValueError::new_err(EXPECTED_BYTE))?;

    if rust_key == 0 {
        return Ok(data.to_owned());
    }

    let mut rust_data = data.as_bytes().to_owned();

    xor_cipher::xor(&mut rust_data, rust_key);

    Ok(PyBytes::new(data.py(), &rust_data))
}

#[py_function]
fn cyclic_xor<'py>(data: &Bound<'py, PyBytes>, key: &Bound<'py, PyBytes>) -> Bound<'py, PyBytes> {
    let rust_key = key.as_bytes();

    if rust_key.is_empty() {
        return data.to_owned();
    }

    let mut rust_data = data.as_bytes().to_owned();

    xor_cipher::cyclic_xor(&mut rust_data, rust_key);

    PyBytes::new(data.py(), &rust_data)
}

#[py_function]
fn xor_in_place(data: &Bound<'_, PyByteArray>, key: &Bound<'_, PyInt>) -> PyResult<()> {
    let rust_key = key
        .extract()
        .map_err(|_| PyValueError::new_err(EXPECTED_BYTE))?;

    let rust_data = unsafe { data.as_bytes_mut() };

    xor_cipher::xor(rust_data, rust_key);

    Ok(())
}

#[py_function]
fn cyclic_xor_in_place(data: &Bound<'_, PyByteArray>, key: &Bound<'_, PyBytes>) {
    let rust_key = key.as_bytes();

    let rust_data = unsafe { data.as_bytes_mut() };

    xor_cipher::cyclic_xor(rust_data, rust_key);
}

#[py_module]
fn _xor_cipher_core(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_py_function!(xor, module)?)?;
    module.add_function(wrap_py_function!(cyclic_xor, module)?)?;
    module.add_function(wrap_py_function!(xor_in_place, module)?)?;
    module.add_function(wrap_py_function!(cyclic_xor_in_place, module)?)?;

    Ok(())
}
