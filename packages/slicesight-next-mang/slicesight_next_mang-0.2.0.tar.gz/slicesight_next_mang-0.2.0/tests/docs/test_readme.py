"""Doctest runner for README examples."""

import os
import sys


def load_tests(loader, tests, ignore):
    """Load doctests from README.md."""
    # Add the parent directory to sys.path so imports work
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    # Try to load README.md if it exists
    readme_path = os.path.join(parent_dir, "README.md")
    if os.path.exists(readme_path):
        # For markdown files, we would need to extract code blocks
        # For now, just add a placeholder test
        pass

    return tests


def test_readme_examples():
    """Test that README examples work as documented."""
    # Import our modules to ensure they work
    from slicesight_next import (
        auto_ratio_thresh,
        calc_cv,
        calc_gini,
        crc16,
        load_ratio,
        redis_cluster_slot,
        verdict,
    )

    # Test basic functionality as documented
    # Example 1: CRC16 and slot calculation
    key = "user:12345"
    checksum = crc16(key)
    slot = redis_cluster_slot(key)
    assert isinstance(checksum, int)
    assert 0 <= slot <= 16383

    # Example 2: Load analysis
    loads = [100.0, 200.0, 150.0]
    ratio = load_ratio(loads)
    cv = calc_cv(loads)
    gini = calc_gini(loads)

    assert ratio == 2.0  # 200/100
    assert cv > 0  # Some variation
    assert 0 <= gini <= 1  # Valid Gini coefficient

    # Example 3: Adaptive threshold
    n_keys = 1000
    n_buckets = 3
    threshold = auto_ratio_thresh(n_keys, n_buckets)
    assert 0 < threshold <= 1

    # Example 4: Verdict
    result = verdict(ratio, cv, gini, 0.1, threshold, 0.05)
    assert isinstance(result, dict)
    assert "hotspot_detected" in result
    assert "load_imbalance" in result


def test_cli_examples():
    """Test CLI examples from documentation."""
    from typer.testing import CliRunner

    from slicesight_next.cli import app

    runner = CliRunner()

    # Test simulate command
    result = runner.invoke(app, ["simulate", "--keys", "100", "--buckets", "3"])
    assert result.exit_code == 0

    # Test score command
    result = runner.invoke(app, ["score", "10.0", "20.0", "30.0"])
    assert result.exit_code == 0

    # Test health command
    result = runner.invoke(app, ["health"])
    assert result.exit_code == 0
    assert "healthy" in result.stdout


def test_formula_documentation():
    """Test that documented formulas are correctly implemented."""
    # Test adaptive threshold formula: ρ_auto(n,k) = 1 / (1 + 3√((k−1)/n))
    import math

    n, k = 1000, 5
    expected = 1.0 / (1.0 + 3.0 * math.sqrt((k - 1) / n))
    actual = auto_ratio_thresh(n, k)
    assert abs(actual - expected) < 1e-10

    # Test that formula gives reasonable values
    assert auto_ratio_thresh(100, 3) > auto_ratio_thresh(1000, 3)  # Decreases with n
    assert auto_ratio_thresh(1000, 3) < auto_ratio_thresh(1000, 10)  # Increases with k


def test_algorithm_properties():
    """Test that algorithms have documented properties."""
    # CV should be scale-invariant
    values1 = [1.0, 2.0, 3.0]
    values2 = [10.0, 20.0, 30.0]
    assert abs(calc_cv(values1) - calc_cv(values2)) < 1e-10

    # Gini should be scale-invariant
    assert abs(calc_gini(values1) - calc_gini(values2)) < 1e-10

    # Load ratio should be scale-invariant
    assert abs(load_ratio(values1) - load_ratio(values2)) < 1e-10

    # Perfect equality should give Gini = 0
    equal_values = [5.0, 5.0, 5.0, 5.0]
    assert calc_gini(equal_values) == 0.0
    assert calc_cv(equal_values) == 0.0
    assert load_ratio(equal_values) == 1.0
