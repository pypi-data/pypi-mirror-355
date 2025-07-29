"""Property-based tests using Hypothesis."""


from hypothesis import assume, given
from hypothesis import strategies as st

from slicesight_next.metrics import (
    auto_ratio_thresh,
    calc_cv,
    calc_gini,
    load_ratio,
    redis_cluster_slot,
)


class TestAutoRatioThreshInvariants:
    """Property-based tests for auto_ratio_thresh."""

    @given(
        n1=st.integers(min_value=10, max_value=10000),
        n2=st.integers(min_value=10, max_value=10000),
        k=st.integers(min_value=2, max_value=100)
    )
    def test_monotonic_decrease_with_n(self, n1: int, n2: int, k: int) -> None:
        """Threshold should decrease as n increases."""
        assume(n1 < n2)
        thresh1 = auto_ratio_thresh(n1, k)
        thresh2 = auto_ratio_thresh(n2, k)
        assert thresh1 >= thresh2

    @given(
        n=st.integers(min_value=10, max_value=10000),
        k1=st.integers(min_value=2, max_value=50),
        k2=st.integers(min_value=2, max_value=50)
    )
    def test_monotonic_increase_with_k(self, n: int, k1: int, k2: int) -> None:
        """Threshold should increase as k increases."""
        assume(k1 < k2)
        thresh1 = auto_ratio_thresh(n, k1)
        thresh2 = auto_ratio_thresh(n, k2)
        assert thresh1 <= thresh2

    @given(
        n=st.integers(min_value=10, max_value=10000),
        k=st.integers(min_value=2, max_value=100)
    )
    def test_threshold_bounds(self, n: int, k: int) -> None:
        """Threshold should be bounded between 0 and 1."""
        thresh = auto_ratio_thresh(n, k)
        assert 0.0 < thresh <= 1.0

    @given(
        n=st.integers(min_value=1000, max_value=100000),
        k=st.integers(min_value=2, max_value=100)
    )
    def test_large_n_convergence(self, n: int, k: int) -> None:
        """For large n, threshold should approach 1.0."""
        thresh = auto_ratio_thresh(n, k)
        # For very large n, threshold should be close to 1.0
        if n > 10000:
            assert thresh > 0.9


class TestLoadRatioInvariants:
    """Property-based tests for load_ratio."""

    @given(st.lists(st.floats(min_value=0.1, max_value=1000.0), min_size=1, max_size=100))
    def test_load_ratio_lower_bound(self, loads: list[float]) -> None:
        """Load ratio should be >= 1.0."""
        ratio = load_ratio(loads)
        assert ratio >= 1.0 or ratio == float('inf')

    @given(st.lists(st.floats(min_value=1.0, max_value=1000.0), min_size=2, max_size=100))
    def test_load_ratio_calculation(self, loads: list[float]) -> None:
        """Load ratio should equal max/min."""
        ratio = load_ratio(loads)
        expected = max(loads) / min(loads)
        assert abs(ratio - expected) < 1e-10

    @given(value=st.floats(min_value=0.1, max_value=1000.0))
    def test_uniform_loads(self, value: float) -> None:
        """Uniform loads should give ratio of 1.0."""
        loads = [value] * 10
        assert load_ratio(loads) == 1.0


class TestCoefficientVariationInvariants:
    """Property-based tests for calc_cv."""

    @given(st.lists(st.floats(min_value=0.1, max_value=1000.0), min_size=1, max_size=100))
    def test_cv_non_negative(self, values: list[float]) -> None:
        """Coefficient of variation should be non-negative."""
        cv = calc_cv(values)
        assert cv >= 0.0

    @given(value=st.floats(min_value=0.1, max_value=1000.0))
    def test_cv_constant_values(self, value: float) -> None:
        """CV should be 0 for constant values."""
        values = [value] * 10
        assert calc_cv(values) == 0.0

    @given(st.lists(st.floats(min_value=0.1, max_value=1000.0), min_size=2, max_size=100))
    def test_cv_scale_invariance(self, values: list[float]) -> None:
        """CV should be scale invariant."""
        cv1 = calc_cv(values)
        scaled_values = [v * 2.0 for v in values]
        cv2 = calc_cv(scaled_values)
        assert abs(cv1 - cv2) < 1e-10


class TestGiniCoefficientInvariants:
    """Property-based tests for calc_gini."""

    @given(st.lists(st.floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=100))
    def test_gini_bounds(self, values: list[float]) -> None:
        """Gini coefficient should be between 0 and 1."""
        gini = calc_gini(values)
        assert 0.0 <= gini <= 1.0

    @given(value=st.floats(min_value=0.1, max_value=1000.0))
    def test_gini_perfect_equality(self, value: float) -> None:
        """Perfect equality should give Gini of 0."""
        values = [value] * 10
        assert calc_gini(values) == 0.0

    @given(st.lists(st.floats(min_value=0.1, max_value=1000.0), min_size=2, max_size=100))
    def test_gini_scale_invariance(self, values: list[float]) -> None:
        """Gini should be scale invariant."""
        gini1 = calc_gini(values)
        scaled_values = [v * 3.0 for v in values]
        gini2 = calc_gini(scaled_values)
        assert abs(gini1 - gini2) < 1e-10


class TestRedisClusterSlotInvariants:
    """Property-based tests for redis_cluster_slot."""

    @given(st.text(min_size=1, max_size=100))
    def test_slot_range(self, key: str) -> None:
        """Slot should be in valid Redis cluster range."""
        slot = redis_cluster_slot(key)
        assert 0 <= slot <= 16383

    @given(st.text(min_size=1, max_size=50))
    def test_slot_consistency(self, key: str) -> None:
        """Same key should always produce same slot."""
        slot1 = redis_cluster_slot(key)
        slot2 = redis_cluster_slot(key)
        assert slot1 == slot2

    @given(
        tag=st.text(min_size=1, max_size=20),
        prefix=st.text(max_size=20),
        suffix=st.text(max_size=20)
    )
    def test_hashtag_routing(self, tag: str, prefix: str, suffix: str) -> None:
        """Keys with same hashtag should route to same slot."""
        key1 = f"{prefix}{{{tag}}}{suffix}"
        key2 = f"different{{{tag}}}other"

        slot1 = redis_cluster_slot(key1)
        slot2 = redis_cluster_slot(key2)
        assert slot1 == slot2
