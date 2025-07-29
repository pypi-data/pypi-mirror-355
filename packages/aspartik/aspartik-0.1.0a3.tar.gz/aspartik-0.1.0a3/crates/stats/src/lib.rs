//! This crate aims to be a functional port of the Math.NET Numerics
//! Distribution package and in doing so providing the Rust numerical computing
//! community with a robust, well-tested statistical distribution package. This
//! crate also ports over some of the special statistical functions from
//! Math.NET in so far as they are used in the computation of distribution
//! values. This crate depends on the `rand` crate to provide RNG.
//!
//! # Sampling
//!
//! The common use case is to set up the distributions and sample from them
//! which depends on the `Rand` crate for random number generation.
//!
#![cfg_attr(feature = "rand", doc = "```")]
#![cfg_attr(not(feature = "rand"), doc = "```ignore")]
//! use stats::distribution::Exp;
//! use rand::distr::Distribution;
//!
//! let mut r = rand::rng();
//! let n = Exp::new(0.5).unwrap();
//! print!("{}", n.sample(&mut r));
//! ```
//!
//! # Introspecting distributions
//!
//! Statrs also comes with a number of useful utility traits for more detailed
//! introspection of distributions.
//!
//! ```
//! use stats::distribution::{
//!     Exp,
//!     // `cdf` and `pdf` methods
//!     Continuous, ContinuousCDF,
//! };
//! use stats::statistics::Distribution; // statistical moments and entropy
//!
//! let n = Exp::new(1.0).unwrap();
//! assert_eq!(n.mean(), Some(1.0));
//! assert_eq!(n.variance(), Some(1.0));
//! assert_eq!(n.entropy(), Some(1.0));
//! assert_eq!(n.skewness(), Some(2.0));
//! assert_eq!(n.cdf(1.0), 0.6321205588285576784045);
//! assert_eq!(n.pdf(1.0), 0.3678794411714423215955);
//! ```
//!
//! # Utility functions
//!
//! As well as utility functions including `erf`, `gamma`, `ln_gamma`, `beta`,
//! etc.
//!
//! ```
//! use stats::distribution::FisherSnedecor;
//! use stats::statistics::Distribution;
//!
//! let n = FisherSnedecor::new(1.0, 1.0).unwrap();
//! assert!(n.variance().is_none());
//! ```
//!
//! ## Distributions implemented
//!
//! Statrs comes with a number of commonly used distributions including Normal,
//! Gamma, Student's T, Exponential, Weibull, etc. view all implemented in
//! `distributions` module.

#![crate_type = "lib"]
#![expect(clippy::excessive_precision)]
#![forbid(unsafe_code)]
#![cfg_attr(docsrs, feature(doc_cfg))]
#![cfg_attr(not(feature = "std"), no_std)]

pub(crate) mod consts;
#[macro_use]
pub mod distribution;
pub mod function;
#[macro_use]
mod prec;
#[cfg(feature = "python")]
pub(crate) mod python_macros;
pub mod statistics;

// used in the `assert_almost_eq` macro
#[doc(hidden)]
pub use prec::almost_eq;

#[cfg(feature = "python")]
use pyo3::prelude::*;

/// Short title.
///
/// Description.
#[cfg(feature = "python")]
pub fn pymodule(py: Python) -> PyResult<Bound<PyModule>> {
	let m = PyModule::new(py, "_stats_rust_impl")?;
	m.add_submodule(&distribution::pymodule(py)?)?;

	Ok(m)
}
