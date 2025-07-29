"""Performance benchmarks using pytest-benchmark."""

import random

import pytest

from slicesight_next.metrics import (
    auto_ratio_thresh,
    calc_cv,
    calc_gini,
    crc16,
    load_ratio,
    redis_cluster_slot,
    verdict,
)


class TestMetricsBenchmarks:
    """Performance benchmarks for metrics functions."""

    @pytest.fixture
    def small_dataset(self) -> list[float]:
        """Small dataset for benchmarking."""
        random.seed(42)
        return [random.uniform(1.0, 100.0) for _ in range(100)]

    @pytest.fixture
    def medium_dataset(self) -> list[float]:
        """Medium dataset for benchmarking."""
        random.seed(42)
        return [random.uniform(1.0, 100.0) for _ in range(1000)]

    @pytest.fixture
    def large_dataset(self) -> list[float]:
        """Large dataset for benchmarking."""
        random.seed(42)
        return [random.uniform(1.0, 100.0) for _ in range(10000)]

    def test_crc16_performance(self, benchmark) -> None:
        """Benchmark CRC16 calculation."""
        keys = [f"key_{i:06d}" for i in range(1000)]

        def run_crc16():
            return [crc16(key) for key in keys]

        result = benchmark(run_crc16)
        assert len(result) == 1000

    def test_redis_cluster_slot_performance(self, benchmark) -> None:
        """Benchmark Redis cluster slot calculation."""
        keys = [f"user:{i}:session:{j}" for i in range(100) for j in range(10)]

        def run_slot_calc():
            return [redis_cluster_slot(key) for key in keys]

        result = benchmark(run_slot_calc)
        assert len(result) == 1000

    def test_load_ratio_small(self, benchmark, small_dataset: list[float]) -> None:
        """Benchmark load ratio calculation on small dataset."""
        result = benchmark(load_ratio, small_dataset)
        assert result >= 1.0

    def test_load_ratio_medium(self, benchmark, medium_dataset: list[float]) -> None:
        """Benchmark load ratio calculation on medium dataset."""
        result = benchmark(load_ratio, medium_dataset)
        assert result >= 1.0

    def test_load_ratio_large(self, benchmark, large_dataset: list[float]) -> None:
        """Benchmark load ratio calculation on large dataset."""
        result = benchmark(load_ratio, large_dataset)
        assert result >= 1.0

    def test_calc_cv_small(self, benchmark, small_dataset: list[float]) -> None:
        """Benchmark coefficient of variation on small dataset."""
        result = benchmark(calc_cv, small_dataset)
        assert result >= 0.0

    def test_calc_cv_medium(self, benchmark, medium_dataset: list[float]) -> None:
        """Benchmark coefficient of variation on medium dataset."""
        result = benchmark(calc_cv, medium_dataset)
        assert result >= 0.0

    def test_calc_cv_large(self, benchmark, large_dataset: list[float]) -> None:
        """Benchmark coefficient of variation on large dataset."""
        result = benchmark(calc_cv, large_dataset)
        assert result >= 0.0

    def test_calc_gini_small(self, benchmark, small_dataset: list[float]) -> None:
        """Benchmark Gini coefficient on small dataset."""
        result = benchmark(calc_gini, small_dataset)
        assert 0.0 <= result <= 1.0

    def test_calc_gini_medium(self, benchmark, medium_dataset: list[float]) -> None:
        """Benchmark Gini coefficient on medium dataset."""
        result = benchmark(calc_gini, medium_dataset)
        assert 0.0 <= result <= 1.0

    def test_calc_gini_large(self, benchmark, large_dataset: list[float]) -> None:
        """Benchmark Gini coefficient on large dataset."""
        result = benchmark(calc_gini, large_dataset)
        assert 0.0 <= result <= 1.0

    def test_auto_ratio_thresh_performance(self, benchmark) -> None:
        """Benchmark adaptive threshold calculation."""
        def run_auto_thresh():
            results = []
            for n in range(100, 10000, 100):
                for k in range(3, 20):
                    results.append(auto_ratio_thresh(n, k))
            return results

        result = benchmark(run_auto_thresh)
        assert len(result) > 0
        assert all(0.0 < thresh <= 1.0 for thresh in result)

    def test_verdict_performance(self, benchmark, medium_dataset: list[float]) -> None:
        """Benchmark verdict calculation."""
        # Pre-calculate metrics
        load_ratio_val = load_ratio(medium_dataset)
        cv_val = calc_cv(medium_dataset)
        gini_val = calc_gini(medium_dataset)
        p_val = 0.05  # Mock p-value

        def run_verdict():
            return verdict(load_ratio_val, cv_val, gini_val, p_val, 2.0, 0.05)

        result = benchmark(run_verdict)
        assert isinstance(result, dict)
        assert "hotspot_detected" in result


class TestEndToEndBenchmarks:
    """End-to-end performance benchmarks."""

    @pytest.fixture
    def key_dataset(self) -> list[str]:
        """Dataset of Redis keys for testing."""
        random.seed(42)
        patterns = [
            "user:{user_id}:profile",
            "session:{session_id}",
            "cache:product:{product_id}",
            "temp:upload:{upload_id}",
            "queue:job:{job_id}",
        ]

        keys = []
        for pattern in patterns:
            for i in range(200):
                if "{user_id}" in pattern:
                    key = pattern.replace("{user_id}", str(random.randint(1, 10000)))
                elif "{session_id}" in pattern:
                    key = pattern.replace("{session_id}", f"sess_{random.randint(1, 50000)}")
                elif "{product_id}" in pattern:
                    key = pattern.replace("{product_id}", str(random.randint(1, 1000)))
                elif "{upload_id}" in pattern:
                    key = pattern.replace("{upload_id}", f"up_{random.randint(1, 100000)}")
                elif "{job_id}" in pattern:
                    key = pattern.replace("{job_id}", f"job_{random.randint(1, 20000)}")
                keys.append(key)

        return keys

    def test_full_analysis_pipeline(self, benchmark, key_dataset: list[str]) -> None:
        """Benchmark complete analysis pipeline."""
        def run_full_analysis():
            # Simulate key distribution across 5 nodes
            buckets = 5
            slot_counts = [0] * buckets

            for key in key_dataset:
                slot = redis_cluster_slot(key) % buckets
                slot_counts[slot] += 1

            loads = [float(count) for count in slot_counts]

            # Calculate all metrics
            load_ratio_val = load_ratio(loads)
            cv_val = calc_cv(loads)
            gini_val = calc_gini(loads)

            # Mock chi-square p-value for performance testing
            p_val = 0.1

            # Calculate adaptive threshold
            n_keys = len(key_dataset)
            threshold = auto_ratio_thresh(n_keys, buckets)

            # Generate verdict
            result = verdict(load_ratio_val, cv_val, gini_val, p_val, threshold, 0.05)

            return {
                "loads": loads,
                "metrics": {
                    "load_ratio": load_ratio_val,
                    "cv": cv_val,
                    "gini": gini_val,
                    "p_value": p_val,
                },
                "threshold": threshold,
                "verdict": result,
            }

        result = benchmark(run_full_analysis)
        assert "loads" in result
        assert "metrics" in result
        assert "verdict" in result
        assert len(result["loads"]) == 5

    def test_high_frequency_simulation(self, benchmark) -> None:
        """Benchmark high-frequency key access simulation."""
        def simulate_high_frequency():
            # Simulate 10,000 key accesses
            buckets = 3
            access_counts = [0] * buckets

            random.seed(42)
            for _ in range(10000):
                # Generate key with some hotspot bias
                if random.random() < 0.3:  # 30% chance of hotspot key
                    key = f"hot{{shared:cache}}:item:{random.randint(1, 10)}"
                else:
                    key = f"normal:user:{random.randint(1, 1000)}:data"

                slot = redis_cluster_slot(key) % buckets
                access_counts[slot] += 1

            loads = [float(count) for count in access_counts]

            # Quick analysis
            ratio = load_ratio(loads)
            cv = calc_cv(loads)
            gini = calc_gini(loads)
            threshold = auto_ratio_thresh(10000, buckets)

            return {
                "ratio": ratio,
                "cv": cv,
                "gini": gini,
                "threshold": threshold,
                "hotspot": ratio > threshold,
            }

        result = benchmark(simulate_high_frequency)
        assert "ratio" in result
        assert "hotspot" in result
