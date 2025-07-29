"""Unit tests for metrics module."""

import math

import pytest

from slicesight_next.metrics import (
    auto_ratio_thresh,
    calc_cv,
    calc_gini,
    chisq_p,
    crc16,
    load_ratio,
    redis_cluster_slot,
    verdict,
)


class TestCRC16:
    """Tests for CRC16 function."""

    def test_crc16_known_values(self) -> None:
        """Test CRC16 with known values."""
        assert crc16("") == 0
        assert crc16("a") == 49345
        assert crc16("123456789") == 47933

    def test_crc16_consistency(self) -> None:
        """Test CRC16 consistency."""
        key = "test_key"
        assert crc16(key) == crc16(key)

    def test_crc16_different_keys(self) -> None:
        """Test CRC16 produces different values for different keys."""
        assert crc16("key1") != crc16("key2")


class TestRedisClusterSlot:
    """Tests for Redis cluster slot calculation."""

    def test_slot_range(self) -> None:
        """Test slot values are in valid range."""
        keys = ["key1", "key2", "key3", "user:123", "session:abc"]
        for key in keys:
            slot = redis_cluster_slot(key)
            assert 0 <= slot <= 16383

    def test_hashtag_support(self) -> None:
        """Test hashtag support for key routing."""
        # Keys with same hashtag should go to same slot
        assert redis_cluster_slot("{user:123}:profile") == redis_cluster_slot("{user:123}:settings")
        assert redis_cluster_slot("prefix{tag}suffix") == redis_cluster_slot("other{tag}data")

    def test_no_hashtag(self) -> None:
        """Test keys without hashtags."""
        slot = redis_cluster_slot("simple_key")
        assert 0 <= slot <= 16383


class TestLoadRatio:
    """Tests for load ratio calculation."""

    def test_empty_list(self) -> None:
        """Test empty list returns 1.0."""
        assert load_ratio([]) == 1.0

    def test_single_value(self) -> None:
        """Test single value returns 1.0."""
        assert load_ratio([10.0]) == 1.0

    def test_equal_loads(self) -> None:
        """Test equal loads return 1.0."""
        assert load_ratio([10.0, 10.0, 10.0]) == 1.0

    def test_different_loads(self) -> None:
        """Test different loads."""
        ratio = load_ratio([10.0, 20.0, 5.0])
        expected = 20.0 / 5.0  # max/min
        assert ratio == expected

    def test_zero_min_load(self) -> None:
        """Test zero minimum load."""
        assert load_ratio([0.0, 10.0]) == float('inf')
        assert load_ratio([0.0, 0.0]) == 1.0


class TestCalcCV:
    """Tests for coefficient of variation."""

    def test_empty_list(self) -> None:
        """Test empty list returns 0.0."""
        assert calc_cv([]) == 0.0

    def test_zero_mean(self) -> None:
        """Test zero mean returns 0.0."""
        assert calc_cv([0.0, 0.0, 0.0]) == 0.0

    def test_no_variation(self) -> None:
        """Test no variation returns 0.0."""
        assert calc_cv([5.0, 5.0, 5.0]) == 0.0

    def test_known_values(self) -> None:
        """Test with known values."""
        # Values: [1, 2, 3], mean=2, std=sqrt(2/3)≈0.816, cv≈0.408
        cv = calc_cv([1.0, 2.0, 3.0])
        expected = math.sqrt(2.0/3.0) / 2.0
        assert abs(cv - expected) < 1e-10


class TestCalcGini:
    """Tests for Gini coefficient."""

    def test_empty_list(self) -> None:
        """Test empty list returns 0.0."""
        assert calc_gini([]) == 0.0

    def test_perfect_equality(self) -> None:
        """Test perfect equality returns 0.0."""
        assert calc_gini([1.0, 1.0, 1.0]) == 0.0

    def test_perfect_inequality(self) -> None:
        """Test perfect inequality approaches 1.0."""
        gini = calc_gini([0.0, 0.0, 100.0])
        assert gini > 0.6  # Should be high inequality

    def test_zero_sum(self) -> None:
        """Test zero sum returns 0.0."""
        assert calc_gini([0.0, 0.0, 0.0]) == 0.0


class TestChisqP:
    """Tests for chi-square p-value."""

    def test_empty_lists(self) -> None:
        """Test empty lists return 1.0."""
        assert chisq_p([], []) == 1.0

    def test_mismatched_lengths(self) -> None:
        """Test mismatched lengths raise ValueError."""
        with pytest.raises(ValueError):
            chisq_p([1, 2], [1.0])

    def test_perfect_fit(self) -> None:
        """Test perfect fit returns high p-value."""
        p_val = chisq_p([10, 10, 10], [10.0, 10.0, 10.0])
        assert p_val > 0.5

    def test_poor_fit(self) -> None:
        """Test poor fit returns low p-value."""
        p_val = chisq_p([100, 1, 1], [34.0, 34.0, 34.0])
        assert p_val < 0.1


class TestAutoRatioThresh:
    """Tests for adaptive ratio threshold."""

    def test_invalid_inputs(self) -> None:
        """Test invalid inputs return 1.0."""
        assert auto_ratio_thresh(0, 3) == 1.0
        assert auto_ratio_thresh(100, 1) == 1.0
        assert auto_ratio_thresh(-10, 3) == 1.0

    def test_monotonic_decrease_with_n(self) -> None:
        """Test threshold decreases as n increases."""
        k = 3
        thresh_100 = auto_ratio_thresh(100, k)
        thresh_1000 = auto_ratio_thresh(1000, k)
        assert thresh_100 > thresh_1000

    def test_monotonic_increase_with_k(self) -> None:
        """Test threshold increases as k increases."""
        n = 1000
        thresh_k3 = auto_ratio_thresh(n, 3)
        thresh_k10 = auto_ratio_thresh(n, 10)
        assert thresh_k3 < thresh_k10

    def test_formula_accuracy(self) -> None:
        """Test formula implementation accuracy."""
        n, k = 1000, 5
        expected = 1.0 / (1.0 + 3.0 * math.sqrt((k - 1) / n))
        actual = auto_ratio_thresh(n, k)
        assert abs(actual - expected) < 1e-10


class TestVerdict:
    """Tests for verdict function."""

    def test_no_hotspot(self) -> None:
        """Test no hotspot detected."""
        result = verdict(1.5, 0.5, 0.3, 0.5, 2.0, 0.05)
        assert not result["hotspot_detected"]
        assert not result["load_imbalance"]
        assert not result["high_variability"]
        assert not result["inequality"]
        assert not result["non_uniform"]

    def test_hotspot_detected(self) -> None:
        """Test hotspot detected."""
        result = verdict(3.0, 1.5, 0.7, 0.01, 2.0, 0.05)
        assert result["hotspot_detected"]
        assert result["load_imbalance"]
        assert result["high_variability"]
        assert result["inequality"]
        assert result["non_uniform"]

    def test_partial_hotspot(self) -> None:
        """Test partial hotspot conditions."""
        # High load ratio but other metrics normal
        result = verdict(3.0, 0.5, 0.3, 0.5, 2.0, 0.05)
        assert not result["hotspot_detected"]  # Need load imbalance + another metric
        assert result["load_imbalance"]

        # Load ratio high + one other metric
        result = verdict(3.0, 1.5, 0.3, 0.5, 2.0, 0.05)
        assert result["hotspot_detected"]
        assert result["load_imbalance"]
        assert result["high_variability"]
