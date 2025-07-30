from astrodynx.towbody.orb_integrals import ang_momentum

import jax.numpy as jnp


class TestAngMomentum:
    def test_basic(self) -> None:
        r = jnp.array([1.0, 0.0, 0.0])
        v = jnp.array([0.0, 1.0, 0.0])
        expected = jnp.array([0.0, 0.0, 1.0])
        result = ang_momentum(r, v)
        assert jnp.allclose(result, expected)

    def test_negative(self) -> None:
        r = jnp.array([0.0, 1.0, 0.0])
        v = jnp.array([1.0, 0.0, 0.0])
        expected = jnp.array([0.0, 0.0, -1.0])
        result = ang_momentum(r, v)
        assert jnp.allclose(result, expected)

    def test_zero(self) -> None:
        r = jnp.array([0.0, 0.0, 0.0])
        v = jnp.array([1.0, 2.0, 3.0])
        expected = jnp.array([0.0, 0.0, 0.0])
        result = ang_momentum(r, v)
        assert jnp.allclose(result, expected)

    def test_parallel_vectors(self) -> None:
        r = jnp.array([1.0, 2.0, 3.0])
        v = jnp.array([2.0, 4.0, 6.0])
        expected = jnp.array([0.0, 0.0, 0.0])
        result = ang_momentum(r, v)
        assert jnp.allclose(result, expected)

    def test_arbitrary_vectors(self) -> None:
        r = jnp.array([2.0, -1.0, 0.5])
        v = jnp.array([0.5, 2.0, -1.0])
        expected = jnp.cross(r, v)
        result = ang_momentum(r, v)
        assert jnp.allclose(result, expected)
