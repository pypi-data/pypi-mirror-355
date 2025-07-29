pub mod fasta;
pub mod newick;
pub mod sam;

#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
pub fn pymodule(py: Python) -> PyResult<Bound<PyModule>> {
	let m = PyModule::new(py, "_io_rust_impl")?;

	m.add_class::<newick::python::PyNode>()?;
	m.add_class::<newick::python::PyTree>()?;
	m.add_class::<fasta::python::PyFastaDnaRecord>()?;
	m.add_class::<fasta::python::PyFastaDnaReader>()?;

	Ok(m)
}
