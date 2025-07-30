from astrodynx.towbody.orb_integrals import (
    ang_momentum_vec,
    eccentricity_vec,
    semimajor_axis,
)

import jax.numpy as jnp


class TestAngMomentum:
    def test_basic(self) -> None:
        r = jnp.array([1.0, 0.0, 0.0])
        v = jnp.array([0.0, 1.0, 0.0])
        expected = jnp.array([0.0, 0.0, 1.0])
        result = ang_momentum_vec(r, v)
        assert jnp.allclose(result, expected)

    def test_negative(self) -> None:
        r = jnp.array([0.0, 1.0, 0.0])
        v = jnp.array([1.0, 0.0, 0.0])
        expected = jnp.array([0.0, 0.0, -1.0])
        result = ang_momentum_vec(r, v)
        assert jnp.allclose(result, expected)

    def test_zero(self) -> None:
        r = jnp.array([0.0, 0.0, 0.0])
        v = jnp.array([1.0, 2.0, 3.0])
        expected = jnp.array([0.0, 0.0, 0.0])
        result = ang_momentum_vec(r, v)
        assert jnp.allclose(result, expected)

    def test_parallel_vectors(self) -> None:
        r = jnp.array([1.0, 2.0, 3.0])
        v = jnp.array([2.0, 4.0, 6.0])
        expected = jnp.array([0.0, 0.0, 0.0])
        result = ang_momentum_vec(r, v)
        assert jnp.allclose(result, expected)

    def test_arbitrary_vectors(self) -> None:
        r = jnp.array([2.0, -1.0, 0.5])
        v = jnp.array([0.5, 2.0, -1.0])
        expected = jnp.cross(r, v)
        result = ang_momentum_vec(r, v)
        assert jnp.allclose(result, expected)


class TestEccentricityVec:
    def test_zero_position(self) -> None:
        r = jnp.array([0.0, 0.0, 0.0])
        v = jnp.array([1.0, 2.0, 3.0])
        mu = 1.0
        # Should return nan or inf due to division by zero norm
        result = eccentricity_vec(r, v, mu)
        assert jnp.isnan(result).all() or jnp.isinf(result).all()

    def test_circular_orbit(self) -> None:
        r = jnp.array([1.0, 0.0, 0.0])
        v = jnp.array([0.0, 1.0, 0.0])
        mu = 1.0
        result = eccentricity_vec(r, v, mu)
        assert jnp.allclose(result, 0)

    def test_arbitrary_vectors(self) -> None:
        r = jnp.array([2.0, -1.0, 0.5])
        v = jnp.array([0.5, 2.0, -1.0])
        mu = 3.0
        h = jnp.cross(r, v)
        expected = (jnp.cross(v, h) / mu) - (r / jnp.linalg.norm(r))
        result = eccentricity_vec(r, v, mu)
        assert jnp.allclose(result, expected)

    def test_large_mu(self) -> None:
        r = jnp.array([1.0, 2.0, 3.0])
        v = jnp.array([4.0, 5.0, 6.0])
        mu = 1e10
        h = jnp.cross(r, v)
        expected = (jnp.cross(v, h) / mu) - (r / jnp.linalg.norm(r))
        result = eccentricity_vec(r, v, mu)
        assert jnp.allclose(result, expected)


class TestSemimajorAxis:
    def test_example_case(self) -> None:
        r = 1.0
        v = 1.0
        mu = 1.0
        expected = 1.0
        result = semimajor_axis(r, v, mu)
        assert jnp.allclose(result, expected)

    def test_circular_orbit(self) -> None:
        # For a circular orbit: v^2 = mu/r, so a = r
        r = 2.0
        mu = 4.0
        v = jnp.sqrt(mu / r)
        expected = r
        result = semimajor_axis(r, v, mu)
        assert jnp.allclose(result, expected)

    def test_elliptical_orbit(self) -> None:
        r = 2.0
        v = 1.0
        mu = 2.0
        expected = 1 / (2 / r - (v**2) / mu)
        result = semimajor_axis(r, v, mu)
        assert jnp.allclose(result, expected)

    def test_hyperbolic_orbit(self) -> None:
        # For hyperbolic: v^2 > 2*mu/r, so denominator negative, a < 0
        r = 1.0
        mu = 1.0
        v = 2.0
        result = semimajor_axis(r, v, mu)
        assert result < 0

    def test_zero_velocity(self) -> None:
        r = 3.0
        v = 0.0
        mu = 2.0
        expected = 1 / (2 / r)
        result = semimajor_axis(r, v, mu)
        assert jnp.allclose(result, expected)
