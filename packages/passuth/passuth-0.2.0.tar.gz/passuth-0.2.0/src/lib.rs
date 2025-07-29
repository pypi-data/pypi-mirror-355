use password_auth;
use pyo3::prelude::*;

#[derive(FromPyObject)]
enum StrOrBytes {
    Str(String),
    Bytes(Vec<u8>),
}

impl AsRef<[u8]> for StrOrBytes {
    fn as_ref(&self) -> &[u8] {
        match self {
            StrOrBytes::Str(s) => s.as_bytes(),
            StrOrBytes::Bytes(b) => b,
        }
    }
}

#[pyfunction]
fn generate_hash(py: Python<'_>, password: StrOrBytes) -> String {
    py.allow_threads(|| password_auth::generate_hash(&password))
}

#[pyfunction]
fn verify_password(py: Python<'_>, password: StrOrBytes, hash: String) -> bool {
    py.allow_threads(|| password_auth::verify_password(&password, &hash).is_ok())
}

fn get_version() -> PyResult<String> {
    Python::with_gil(|py| {
        let metadata = PyModule::import(py, "importlib.metadata")?;
        let version = metadata.getattr("version")?.call1(("passuth",))?;
        version.extract()
    })
}

#[pymodule(gil_used = false)]
fn passuth(m: &Bound<'_, PyModule>) -> PyResult<()> {
    let version = get_version().unwrap_or_else(|_| "unknown".to_string());
    m.add("__version__", version)?;
    m.add_function(wrap_pyfunction!(generate_hash, m)?)?;
    m.add_function(wrap_pyfunction!(verify_password, m)?)?;
    Ok(())
}
