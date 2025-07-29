"""Integration tests with Redis cluster using testcontainers."""


import pytest
from typer.testing import CliRunner

from slicesight_next.cli import app
from slicesight_next.metrics import load_ratio, redis_cluster_slot


class MockRedisCluster:
    """Mock Redis cluster for testing without actual containers."""

    def __init__(self, nodes: int = 3):
        self.nodes = nodes
        self.data: dict[str, str] = {}
        self.access_counts: dict[int, int] = dict.fromkeys(range(nodes), 0)

    def set(self, key: str, value: str) -> None:
        """Set a key-value pair."""
        self.data[key] = value
        slot = redis_cluster_slot(key) % self.nodes
        self.access_counts[slot] += 1

    def get(self, key: str) -> str | None:
        """Get a value by key."""
        slot = redis_cluster_slot(key) % self.nodes
        self.access_counts[slot] += 1
        return self.data.get(key)

    def get_load_distribution(self) -> list[float]:
        """Get current load distribution across nodes."""
        return [float(count) for count in self.access_counts.values()]

    def reset_counters(self) -> None:
        """Reset access counters."""
        self.access_counts = dict.fromkeys(range(self.nodes), 0)


class TestRedisClusterIntegration:
    """Integration tests simulating Redis cluster behavior."""

    @pytest.fixture
    def cluster(self) -> MockRedisCluster:
        """Create a mock Redis cluster."""
        return MockRedisCluster(nodes=3)

    def test_uniform_key_distribution(self, cluster: MockRedisCluster) -> None:
        """Test uniform key distribution doesn't trigger hotspot detection."""
        # Generate keys that should distribute relatively evenly
        keys = [f"user:{i:06d}" for i in range(1000)]

        for key in keys:
            cluster.set(key, f"data_{key}")

        loads = cluster.get_load_distribution()
        ratio = load_ratio(loads)

        # With 1000 keys across 3 nodes, distribution should be reasonably balanced
        assert ratio < 2.0  # Not perfectly balanced but reasonable

    def test_hotspot_scenario(self, cluster: MockRedisCluster) -> None:
        """Test scenario that should trigger hotspot detection."""
        # Create keys that will likely go to same slot using hashtags
        hotspot_keys = [f"hot{{user:123}}:data:{i}" for i in range(500)]
        normal_keys = [f"normal:user:{i}" for i in range(100)]

        # Access hotspot keys multiple times
        for key in hotspot_keys:
            cluster.set(key, "hot_data")
            cluster.get(key)  # Additional access

        # Access normal keys once
        for key in normal_keys:
            cluster.set(key, "normal_data")

        loads = cluster.get_load_distribution()
        ratio = load_ratio(loads)

        # Should detect significant imbalance
        assert ratio > 3.0

    def test_gradual_hotspot_development(self, cluster: MockRedisCluster) -> None:
        """Test detection of gradually developing hotspot."""
        # Start with balanced load
        base_keys = [f"base:user:{i}" for i in range(300)]
        for key in base_keys:
            cluster.set(key, "base_data")

        initial_loads = cluster.get_load_distribution()
        initial_ratio = load_ratio(initial_loads)

        # Add hotspot traffic
        hotspot_keys = [f"trending{{topic:viral}}:post:{i}" for i in range(200)]
        for key in hotspot_keys:
            for _ in range(3):  # Multiple accesses per key
                cluster.set(key, "viral_content")
                cluster.get(key)

        final_loads = cluster.get_load_distribution()
        final_ratio = load_ratio(final_loads)

        # Ratio should have increased
        assert final_ratio > initial_ratio
        assert final_ratio > 2.0

    def test_cluster_rebalancing_simulation(self, cluster: MockRedisCluster) -> None:
        """Test simulation of cluster rebalancing effects."""
        # Create initial imbalanced state
        imbalanced_keys = [f"imbalanced{{shard:0}}:key:{i}" for i in range(400)]
        for key in imbalanced_keys:
            cluster.set(key, "data")

        loads_before = cluster.get_load_distribution()
        ratio_before = load_ratio(loads_before)

        # Simulate rebalancing by adding more diverse keys
        cluster.reset_counters()
        balanced_keys = [f"balanced:key:{i}:hash:{hash(i) % 1000}" for i in range(400)]
        for key in balanced_keys:
            cluster.set(key, "rebalanced_data")

        loads_after = cluster.get_load_distribution()
        ratio_after = load_ratio(loads_after)

        # After rebalancing, distribution should be more balanced
        assert ratio_after < ratio_before


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def test_simulate_integration(self) -> None:
        """Test simulate command integration."""
        runner = CliRunner()

        # Test with parameters that should NOT trigger hotspot
        result = runner.invoke(app, [
            "simulate",
            "--keys", "1000",
            "--buckets", "3",
            "--seed", "42",
            "--json"
        ])

        assert result.exit_code == 0

        # Parse output and verify structure
        import json
        data = json.loads(result.stdout)

        assert "simulation" in data
        assert "metrics" in data
        assert "verdict" in data

        # Verify metrics are calculated
        metrics = data["metrics"]
        assert "load_ratio" in metrics
        assert "coefficient_of_variation" in metrics
        assert "gini_coefficient" in metrics
        assert "chi_square_p_value" in metrics

    def test_score_integration(self) -> None:
        """Test score command with known hotspot scenario."""
        runner = CliRunner()

        # Loads representing clear hotspot (one node heavily loaded)
        result = runner.invoke(app, [
            "score",
            "1000.0", "50.0", "30.0",  # Clear imbalance
            "--ratio-thresh", "2.0",
            "--json"
        ])

        assert result.exit_code == 0

        import json
        data = json.loads(result.stdout)

        # Should detect hotspot
        verdict_data = data["verdict"]
        assert verdict_data["load_imbalance"] is True
        assert verdict_data["hotspot_detected"] is True

    def test_auto_threshold_integration(self) -> None:
        """Test auto threshold functionality integration."""
        runner = CliRunner()

        # Test with different key counts to verify threshold adaptation
        results = []
        for key_count in [100, 1000, 10000]:
            result = runner.invoke(app, [
                "simulate",
                "--keys", str(key_count),
                "--buckets", "5",
                "--auto-thresh",
                "--seed", "123",
                "--json"
            ])

            assert result.exit_code == 0

            import json
            data = json.loads(result.stdout)
            results.append(data["thresholds"]["ratio_threshold"])

        # Thresholds should decrease as key count increases
        assert results[0] > results[1] > results[2]

    def test_end_to_end_workflow(self) -> None:
        """Test complete end-to-end workflow."""
        runner = CliRunner()

        # 1. Check health
        health_result = runner.invoke(app, ["health", "--json"])
        assert health_result.exit_code == 0

        # 2. Run simulation
        sim_result = runner.invoke(app, [
            "simulate",
            "--keys", "500",
            "--buckets", "3",
            "--auto-thresh",
            "--json"
        ])
        assert sim_result.exit_code == 0

        # 3. Parse simulation results and use for scoring
        import json
        sim_data = json.loads(sim_result.stdout)
        loads = sim_data["distribution"]

        # 4. Score the same distribution
        load_args = [str(load) for load in loads]
        score_result = runner.invoke(app, ["score"] + load_args + ["--auto-thresh", "--json"])
        assert score_result.exit_code == 0

        # 5. Results should be consistent
        score_data = json.loads(score_result.stdout)

        # Metrics should be identical (within floating point precision)
        sim_metrics = sim_data["metrics"]
        score_metrics = score_data["metrics"]

        assert abs(sim_metrics["load_ratio"] - score_metrics["load_ratio"]) < 1e-10
        assert abs(sim_metrics["coefficient_of_variation"] - score_metrics["coefficient_of_variation"]) < 1e-10
