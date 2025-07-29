//! Statistical computation traits

pub trait Distribution {
	/// Mean, or `None` if it doesn't exist
	///
	/// # Examples
	///
	/// ```
	/// use stats::statistics::Distribution;
	/// use stats::distribution::Uniform;
	///
	/// let n = Uniform::new(0.0, 1.0).unwrap();
	/// assert_eq!(0.5, n.mean().unwrap());
	/// ```
	fn mean(&self) -> Option<f64> {
		None
	}

	/// Median
	///
	/// # Examples
	///
	/// ```
	/// use stats::statistics::Distribution;
	/// use stats::distribution::Uniform;
	///
	/// let n = Uniform::new(0.0, 1.0).unwrap();
	/// assert_eq!(Some(0.5), n.median());
	/// ```
	fn median(&self) -> Option<f64> {
		None
	}

	/// Variance, or `None` if it doesn't exist
	///
	/// # Examples
	///
	/// ```
	/// use stats::statistics::Distribution;
	/// use stats::distribution::Uniform;
	///
	/// let n = Uniform::new(0.0, 1.0).unwrap();
	/// assert_eq!(1.0 / 12.0, n.variance().unwrap());
	/// ```
	fn variance(&self) -> Option<f64> {
		None
	}

	/// Standard deviation, or `None` if it doesn't exist
	///
	/// # Examples
	///
	/// ```
	/// use stats::statistics::Distribution;
	/// use stats::distribution::Uniform;
	///
	/// let n = Uniform::new(0.0, 1.0).unwrap();
	/// assert_eq!((1f64 / 12f64).sqrt(), n.std_dev().unwrap());
	/// ```
	fn std_dev(&self) -> Option<f64> {
		self.variance().map(|var| var.sqrt())
	}

	/// Entropy, or `None` if it doesn't exist
	///
	/// # Examples
	///
	/// ```
	/// use stats::statistics::Distribution;
	/// use stats::distribution::Uniform;
	///
	/// let n = Uniform::new(0.0, 1.0).unwrap();
	/// assert_eq!(0.0, n.entropy().unwrap());
	/// ```
	fn entropy(&self) -> Option<f64> {
		None
	}

	/// Skewness, of `None` if it doesn't exist
	///
	/// # Examples
	///
	/// ```
	/// use stats::statistics::Distribution;
	/// use stats::distribution::Uniform;
	///
	/// let n = Uniform::new(0.0, 1.0).unwrap();
	/// assert_eq!(0.0, n.skewness().unwrap());
	/// ```
	fn skewness(&self) -> Option<f64> {
		None
	}
}

/// The `Mode` trait specifies that an object has a closed form solution
/// for its mode(s)
pub trait Mode<T> {
	/// Returns the mode, if one exists.
	///
	/// # Examples
	///
	/// ```
	/// use stats::statistics::Mode;
	/// use stats::distribution::Uniform;
	///
	/// let n = Uniform::new(0.0, 1.0).unwrap();
	/// assert_eq!(Some(0.5), n.mode());
	/// ```
	fn mode(&self) -> T;
}
