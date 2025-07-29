"""Core metrics and algorithms for Redis hotspot detection."""

import math


def crc16(key: str) -> int:
    """Calculate CRC16 checksum for Redis cluster key hashing.

    Args:
        key: Input string key

    Returns:
        CRC16 checksum as integer
    """
    crc = 0
    for byte in key.encode('utf-8'):
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def redis_cluster_slot(key: str) -> int:
    """Calculate Redis cluster slot for a given key.

    Args:
        key: Redis key string

    Returns:
        Cluster slot number (0-16383)
    """
    hashtag_start = key.find('{')
    if hashtag_start != -1:
        hashtag_end = key.find('}', hashtag_start + 1)
        if hashtag_end != -1 and hashtag_end > hashtag_start + 1:
            key = key[hashtag_start + 1:hashtag_end]

    return crc16(key) % 16384


def load_ratio(node_loads: list[float]) -> float:
    """Calculate load ratio (max/min) for node loads.

    Args:
        node_loads: List of load values per node

    Returns:
        Load ratio (max/min), or 1.0 if min is zero
    """
    if not node_loads:
        return 1.0

    max_load = max(node_loads)
    min_load = min(node_loads)

    if min_load == 0.0:
        return 1.0 if max_load == 0.0 else float('inf')

    return max_load / min_load


def calc_cv(values: list[float]) -> float:
    """Calculate coefficient of variation.

    Args:
        values: List of numeric values

    Returns:
        Coefficient of variation (std/mean)
    """
    if not values:
        return 0.0

    mean = sum(values) / len(values)
    if mean == 0.0:
        return 0.0

    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std_dev = math.sqrt(variance)

    return std_dev / mean


def calc_gini(values: list[float]) -> float:
    """Calculate Gini coefficient for inequality measurement.

    Args:
        values: List of numeric values

    Returns:
        Gini coefficient (0 = perfect equality, 1 = perfect inequality)
    """
    if not values:
        return 0.0

    sorted_values = sorted(values)
    n = len(sorted_values)
    total = sum(sorted_values)

    if total == 0.0:
        return 0.0

    cumsum = 0.0
    gini_sum = 0.0

    for i, value in enumerate(sorted_values):
        cumsum += value
        gini_sum += (2 * (i + 1) - n - 1) * value

    return gini_sum / (n * total)


def chisq_p(observed: list[int], expected: list[float]) -> float:
    """Calculate chi-square p-value for goodness of fit test.

    Args:
        observed: Observed frequency counts
        expected: Expected frequency values

    Returns:
        Chi-square p-value
    """
    if len(observed) != len(expected):
        raise ValueError("Observed and expected lists must have same length")

    if not observed:
        return 1.0

    chi_square = 0.0
    degrees_of_freedom = len(observed) - 1

    for obs, exp in zip(observed, expected, strict=False):
        if exp > 0:
            chi_square += (obs - exp) ** 2 / exp

    if degrees_of_freedom <= 0:
        return 1.0

    # Simplified chi-square p-value approximation
    # For production use, consider scipy.stats.chi2.sf(chi_square, df)
    if chi_square == 0:
        return 1.0

    # Rough approximation for demonstration
    # This is a simplified version - real implementation would use gamma function
    if degrees_of_freedom == 1:
        # For df=1, approximate using normal distribution
        z = math.sqrt(chi_square)
        if z > 3.0:
            return 0.001
        elif z > 2.0:
            return 0.05
        elif z > 1.0:
            return 0.3
        else:
            return 0.7
    else:
        # Very rough approximation for higher df
        if chi_square > degrees_of_freedom * 3:
            return 0.001
        elif chi_square > degrees_of_freedom * 2:
            return 0.05
        elif chi_square > degrees_of_freedom:
            return 0.3
        else:
            return 0.7


def auto_ratio_thresh(n: int, k: int) -> float:
    """Calculate adaptive threshold ratio.

    Formula: ρ_auto(n,k) = 1 / (1 + 3√((k−1)/n))

    Args:
        n: Total number of keys
        k: Number of buckets/nodes

    Returns:
        Adaptive threshold ratio
    """
    if n <= 0 or k <= 1:
        return 1.0

    ratio = (k - 1) / n
    return 1.0 / (1.0 + 3.0 * math.sqrt(ratio))


def verdict(
    load_ratio_val: float,
    cv_val: float,
    gini_val: float,
    p_val: float,
    ratio_thresh: float,
    p_thresh: float = 0.05
) -> dict[str, bool]:
    """Generate hotspot detection verdict based on multiple metrics.

    Args:
        load_ratio_val: Load ratio value
        cv_val: Coefficient of variation
        gini_val: Gini coefficient
        p_val: Chi-square p-value
        ratio_thresh: Threshold for load ratio
        p_thresh: P-value threshold for significance

    Returns:
        Dictionary with boolean verdicts for each metric
    """
    return {
        "load_imbalance": load_ratio_val > ratio_thresh,
        "high_variability": cv_val > 1.0,
        "inequality": gini_val > 0.5,
        "non_uniform": p_val < p_thresh,
        "hotspot_detected": (
            load_ratio_val > ratio_thresh and
            (cv_val > 1.0 or gini_val > 0.5 or p_val < p_thresh)
        )
    }
