"""Unit tests for CLI module."""

import json

from typer.testing import CliRunner

from slicesight_next.cli import app

runner = CliRunner()


class TestSimulateCommand:
    """Tests for simulate command."""

    def test_simulate_basic(self) -> None:
        """Test basic simulate command."""
        result = runner.invoke(app, ["simulate", "--keys", "100", "--buckets", "3"])
        assert result.exit_code == 0
        assert "SliceSight-Next Simulation Results" in result.stdout

    def test_simulate_json_output(self) -> None:
        """Test simulate with JSON output."""
        result = runner.invoke(app, ["simulate", "--keys", "100", "--json"])
        assert result.exit_code == 0

        # Should be valid JSON
        output_data = json.loads(result.stdout)
        assert "simulation" in output_data
        assert "metrics" in output_data
        assert "verdict" in output_data

    def test_simulate_with_seed(self) -> None:
        """Test simulate with seed for reproducibility."""
        result1 = runner.invoke(app, ["simulate", "--seed", "42", "--json"])
        result2 = runner.invoke(app, ["simulate", "--seed", "42", "--json"])

        assert result1.exit_code == 0
        assert result2.exit_code == 0

        # Results should be identical with same seed
        data1 = json.loads(result1.stdout)
        data2 = json.loads(result2.stdout)
        assert data1["distribution"] == data2["distribution"]

    def test_simulate_auto_thresh(self) -> None:
        """Test simulate with auto threshold."""
        result = runner.invoke(app, ["simulate", "--auto-thresh", "--json"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["thresholds"]["auto_threshold"] is True
        assert "ratio_threshold" in data["thresholds"]


class TestScanCommand:
    """Tests for scan command."""

    def test_scan_basic(self) -> None:
        """Test basic scan command."""
        result = runner.invoke(app, ["scan"])
        assert result.exit_code == 0
        assert "Scanning Redis" in result.stdout

    def test_scan_json_output(self) -> None:
        """Test scan with JSON output."""
        result = runner.invoke(app, ["scan", "--json"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert "scan" in data
        assert "metrics" in data
        assert data["scan"]["host"] == "localhost"
        assert data["scan"]["port"] == 6379

    def test_scan_custom_host_port(self) -> None:
        """Test scan with custom host and port."""
        result = runner.invoke(app, ["scan", "--host", "redis.example.com", "--port", "6380", "--json"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["scan"]["host"] == "redis.example.com"
        assert data["scan"]["port"] == 6380


class TestScoreCommand:
    """Tests for score command."""

    def test_score_basic(self) -> None:
        """Test basic score command."""
        result = runner.invoke(app, ["score", "10.0", "20.0", "30.0"])
        assert result.exit_code == 0
        assert "SliceSight-Next Simulation Results" in result.stdout

    def test_score_json_output(self) -> None:
        """Test score with JSON output."""
        result = runner.invoke(app, ["score", "10.0", "20.0", "30.0", "--json"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert "input" in data
        assert data["input"]["loads"] == [10.0, 20.0, 30.0]
        assert data["input"]["buckets"] == 3

    def test_score_auto_thresh(self) -> None:
        """Test score with auto threshold."""
        result = runner.invoke(app, ["score", "10.0", "20.0", "30.0", "--auto-thresh", "--json"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["thresholds"]["auto_threshold"] is True

    def test_score_custom_buckets(self) -> None:
        """Test score with custom bucket count."""
        result = runner.invoke(app, ["score", "10.0", "20.0", "--buckets", "5", "--json"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["input"]["buckets"] == 5


class TestHealthCommand:
    """Tests for health command."""

    def test_health_basic(self) -> None:
        """Test basic health command."""
        result = runner.invoke(app, ["health"])
        assert result.exit_code == 0
        assert "SliceSight-Next is healthy" in result.stdout
        assert "Version: 0.1.0" in result.stdout

    def test_health_json_output(self) -> None:
        """Test health with JSON output."""
        result = runner.invoke(app, ["health", "--json"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert "dependencies" in data
        assert "features" in data


class TestAppHelp:
    """Tests for application help."""

    def test_app_help(self) -> None:
        """Test main application help."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "SliceSight-Next" in result.stdout
        assert "simulate" in result.stdout
        assert "scan" in result.stdout
        assert "score" in result.stdout
        assert "health" in result.stdout

    def test_simulate_help(self) -> None:
        """Test simulate command help."""
        result = runner.invoke(app, ["simulate", "--help"])
        assert result.exit_code == 0
        assert "Simulate Redis key distribution" in result.stdout
        assert "--keys" in result.stdout
        assert "--buckets" in result.stdout
