from typing import Optional, List

__all__: List[str]

class RNG:
    """Random numbers generator.

    It's backed by a 64-bit output PCG, see the [Rust documentation][pcg] for
    details.

    It can be used standalone, but it was created as a Rust-native RNG which
    can be used efficiently by other Aspartik modules.

    [pcg]: https://docs.rs/rand_pcg/latest/rand_pcg/type.Pcg64.html
    """

    def __init__(self, seed: Optional[int] = None):
        """
        The seed is a positive integer less than $2^{64}$.  If no seed is
        passed the RNG will be seeded from the operating system data source.
        """
    def random_bool(self, ratio: float = 0.5) -> bool:
        """
        Rerturns `True` with the probability of `ratio`, which must be in the
        range $[0, 1]$.
        """
    def random_int(self, lower: int, upper: int) -> int:
        """Returns a random int in $[lower, upper)$."""
    def random_float(self) -> float:
        """Returns a float uniformly distributed on $[0, 1)$

        See the [`rand` notes][float] for details on how the values are
        sampled.

        [float]: https://docs.rs/rand/latest/rand/distr/struct.StandardUniform.html#floating-point-implementation
        """
