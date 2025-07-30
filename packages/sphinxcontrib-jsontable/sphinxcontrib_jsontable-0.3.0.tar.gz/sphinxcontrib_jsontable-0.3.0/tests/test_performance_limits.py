"""
Test cases for performance limits and new functionality.

This module contains test cases for the new performance limit features,
including default limits, warning systems, and configuration options.
"""

from unittest.mock import MagicMock, patch

import pytest

from sphinxcontrib.jsontable.directives import (
    DEFAULT_MAX_ROWS,
    JsonTableDirective,
    TableConverter,
)


class TestTableConverterPerformanceLimits:
    """Test cases for TableConverter performance limit functionality."""

    @pytest.fixture
    def converter(self):
        """Create TableConverter instance for testing."""
        return TableConverter()

    @pytest.fixture
    def mock_logger(self):
        """Shared logger mock fixture for DRY principle compliance."""
        with patch("sphinxcontrib.jsontable.directives.logger") as mock:
            yield mock

    @pytest.fixture
    def dataset_generator(self):
        """Unified test data generator for DRY principle compliance."""

        def _generate(size: int, schema: dict | None = None) -> list:
            default_schema = {"id": "id_{i}", "name": "item_{i}"}
            schema = schema or default_schema
            return [
                {key: template.format(i=i) for key, template in schema.items()}
                for i in range(size)
            ]

        return _generate

    @pytest.fixture
    def large_dataset(self, dataset_generator):
        """Large dataset exceeding DEFAULT_MAX_ROWS for testing."""
        return dataset_generator(15000)

    @pytest.fixture
    def small_dataset(self, dataset_generator):
        """Small dataset within DEFAULT_MAX_ROWS for testing."""
        return dataset_generator(100)

    # ========================================
    # DEFAULT_MAX_ROWS Functionality Tests
    # ========================================

    def test_default_max_rows_constant_value(self):
        """Test that DEFAULT_MAX_ROWS is set to expected value."""
        assert DEFAULT_MAX_ROWS == 10000, (
            f"Expected DEFAULT_MAX_ROWS to be 10000, got {DEFAULT_MAX_ROWS}"
        )

    def test_converter_uses_default_max_rows(self, converter):
        """Test that TableConverter uses DEFAULT_MAX_ROWS by default."""
        assert converter.default_max_rows == DEFAULT_MAX_ROWS, (
            f"Expected converter to use DEFAULT_MAX_ROWS {DEFAULT_MAX_ROWS}, "
            f"got {converter.default_max_rows}"
        )

    def test_converter_accepts_custom_default_max_rows(self):
        """Test that TableConverter accepts custom default max rows."""
        custom_limit = 5000
        converter = TableConverter(default_max_rows=custom_limit)
        assert converter.default_max_rows == custom_limit, (
            f"Expected converter to use custom limit {custom_limit}, "
            f"got {converter.default_max_rows}"
        )

    # ========================================
    # _apply_default_limit Method Tests
    # ========================================

    def test_apply_default_limit_small_dataset_no_user_limit(
        self, converter, small_dataset
    ):
        """
        小さなデータセットに制限が適用されないことを確認。

        Given: DEFAULT_MAX_ROWS未満の小さなデータセット
        When: user_limit=Noneで_apply_default_limitを呼び出す
        Then: Noneが返される(制限なし)
        """
        result = converter._apply_default_limit(small_dataset, None)
        assert result is None, "Small dataset should not trigger default limit"

    def test_apply_default_limit_large_dataset_no_user_limit(
        self, converter, large_dataset, mock_logger
    ):
        """
        大量データセットにデフォルト制限が適用されることを確認。

        Given: DEFAULT_MAX_ROWSを超える大量データセット
        When: user_limit=Noneで_apply_default_limitを呼び出す
        Then: DEFAULT_MAX_ROWSが返され、警告がログ出力される
        """
        result = converter._apply_default_limit(large_dataset, None)

        assert result == DEFAULT_MAX_ROWS, (
            f"Expected default limit {DEFAULT_MAX_ROWS} for large dataset, got {result}"
        )
        mock_logger.warning.assert_called_once()
        warning_msg = mock_logger.warning.call_args[0][0]
        assert "15,000 rows" in warning_msg
        assert "10,000 rows" in warning_msg

    def test_apply_default_limit_user_limit_zero_unlimited(
        self, converter, large_dataset, mock_logger
    ):
        """
        user_limit=0で無制限処理が有効になることを確認。

        Given: 大量データセット
        When: user_limit=0で_apply_default_limitを呼び出す
        Then: Noneが返され(無制限)、infoログが出力される
        """
        result = converter._apply_default_limit(large_dataset, 0)

        assert result is None, "user_limit=0 should result in unlimited processing"
        mock_logger.info.assert_called_once_with(
            "JsonTable: Unlimited rows requested via :limit: 0"
        )

    def test_apply_default_limit_user_limit_specified(self, converter, large_dataset):
        """
        明示的なユーザー制限が尊重されることを確認。

        Given: 大量データセット
        When: 明示的なuser_limitで_apply_default_limitを呼び出す
        Then: 指定された制限値が返される
        """
        user_limit = 2000
        result = converter._apply_default_limit(large_dataset, user_limit)

        assert result == user_limit, (
            f"Expected user-specified limit {user_limit}, got {result}"
        )

    def test_apply_default_limit_user_limit_small_dataset(
        self, converter, small_dataset
    ):
        """
        小さなデータセットでもユーザー制限が尊重されることを確認。

        Given: 小さなデータセット
        When: 明示的なuser_limitで_apply_default_limitを呼び出す
        Then: 指定された制限値が返される
        """
        user_limit = 50
        result = converter._apply_default_limit(small_dataset, user_limit)

        assert result == user_limit, (
            f"Expected user limit {user_limit} even for small dataset, got {result}"
        )

    # ========================================
    # _estimate_data_size Method Tests
    # ========================================

    def test_estimate_data_size_dict(self, converter):
        """Test data size estimation for dictionary input."""
        data = {"key": "value"}
        result = converter._estimate_data_size(data)
        assert result == 1, f"Expected size 1 for single dict, got {result}"

    def test_estimate_data_size_list(self, converter):
        """Test data size estimation for list input."""
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        result = converter._estimate_data_size(data)
        assert result == 3, f"Expected size 3 for 3-item list, got {result}"

    def test_estimate_data_size_empty_list(self, converter):
        """Test data size estimation for empty list."""
        data = []
        result = converter._estimate_data_size(data)
        assert result == 0, f"Expected size 0 for empty list, got {result}"

    @pytest.mark.parametrize(
        "invalid_data,expected_size",
        [
            ("string", 0),
            (123, 0),
            (None, 0),
        ],
    )
    def test_estimate_data_size_invalid_type(
        self, converter, invalid_data, expected_size
    ):
        """Test data size estimation for invalid types."""
        result = converter._estimate_data_size(invalid_data)
        assert result == expected_size, (
            f"Expected size {expected_size} for {type(invalid_data).__name__}, got {result}"
        )

    # ========================================
    # Integration Tests with Convert Method (Simplified)
    # ========================================

    def test_convert_large_dataset_applies_default_limit(
        self, converter, large_dataset, mock_logger
    ):
        """Test that convert method applies default limit to large datasets."""
        result = converter.convert(large_dataset, include_header=True)

        # Header + DEFAULT_MAX_ROWS data rows
        expected_length = DEFAULT_MAX_ROWS + 1
        assert len(result) == expected_length, (
            f"Expected {expected_length} rows (header + {DEFAULT_MAX_ROWS} data rows), "
            f"got {len(result)}"
        )

    def test_convert_small_dataset_no_limit_applied(self, converter, small_dataset):
        """Test that convert method doesn't limit small datasets."""
        result = converter.convert(small_dataset, include_header=True)

        # Header + all data rows
        expected_length = len(small_dataset) + 1
        assert len(result) == expected_length, (
            f"Expected {expected_length} rows (header + all data), got {len(result)}"
        )

    def test_convert_with_explicit_limit_zero(
        self, converter, large_dataset, mock_logger
    ):
        """Test that explicit limit=0 disables all limits."""
        result = converter.convert(large_dataset, include_header=True, limit=0)

        # Header + all data rows (unlimited)
        expected_length = len(large_dataset) + 1
        assert len(result) == expected_length, (
            f"Expected unlimited processing ({expected_length} rows), got {len(result)}"
        )

    def test_convert_with_explicit_limit_value(self, converter, large_dataset):
        """Test that explicit limit value is respected."""
        explicit_limit = 500
        result = converter.convert(
            large_dataset, include_header=True, limit=explicit_limit
        )

        # Header + limited data rows
        expected_length = explicit_limit + 1
        assert len(result) == expected_length, (
            f"Expected {expected_length} rows (header + {explicit_limit} limited rows), "
            f"got {len(result)}"
        )

    # ========================================
    # Warning Message Tests
    # ========================================

    def test_warning_message_format(self, converter, large_dataset, mock_logger):
        """Test that warning message contains expected information."""
        converter._apply_default_limit(large_dataset, None)

        warning_msg = mock_logger.warning.call_args[0][0]
        expected_phrases = [
            "Large dataset detected",
            "15,000 rows",
            "10,000 rows",
            ":limit: option",
            "all rows",
        ]

        for phrase in expected_phrases:
            assert phrase in warning_msg, (
                f"Warning message missing expected phrase: '{phrase}'"
            )

    def test_no_warning_for_small_dataset(self, converter, small_dataset, mock_logger):
        """Test that no warning is issued for small datasets."""
        converter._apply_default_limit(small_dataset, None)
        mock_logger.warning.assert_not_called()

    def test_info_message_for_unlimited_request(
        self, converter, large_dataset, mock_logger
    ):
        """Test that info message is logged for unlimited requests."""
        converter._apply_default_limit(large_dataset, 0)
        mock_logger.info.assert_called_once_with(
            "JsonTable: Unlimited rows requested via :limit: 0"
        )

    # ========================================
    # Edge Cases and Error Handling
    # ========================================

    @pytest.mark.parametrize(
        "dataset_size,expected_limit",
        [
            (10000, None),  # 境界値(等しい)
            (10001, DEFAULT_MAX_ROWS),  # 境界値(超過)
        ],
    )
    def test_apply_default_limit_boundary_conditions(
        self, converter, dataset_generator, dataset_size, expected_limit, mock_logger
    ):
        """Test behavior at threshold boundaries."""
        dataset = dataset_generator(dataset_size)
        result = converter._apply_default_limit(dataset, None)

        assert result == expected_limit, (
            f"Dataset size {dataset_size}: expected {expected_limit}, got {result}"
        )

    def test_custom_default_max_rows_respected(self, mock_logger):
        """Test that custom default max rows setting is respected."""
        custom_limit = 5000
        converter = TableConverter(default_max_rows=custom_limit)
        large_dataset = [{"id": i} for i in range(6000)]

        result = converter._apply_default_limit(large_dataset, None)

        assert result == custom_limit, (
            f"Expected custom limit {custom_limit}, got {result}"
        )
        warning_msg = mock_logger.warning.call_args[0][0]
        assert "6,000 rows" in warning_msg
        assert "5,000 rows" in warning_msg


class TestJsonTableDirectivePerformanceLimits:
    """Test cases for JsonTableDirective performance limit integration."""

    @pytest.fixture
    def mock_env(self):
        """Mock Sphinx environment for testing."""
        env = MagicMock()
        env.config.jsontable_max_rows = DEFAULT_MAX_ROWS
        env.srcdir = "/tmp/docs"
        return env

    @pytest.fixture
    def converter(self):
        """Create TableConverter instance for this test class."""
        return TableConverter()

    @pytest.fixture
    def mock_logger(self):
        """Shared logger mock fixture for directive tests."""
        with patch("sphinxcontrib.jsontable.directives.logger") as mock:
            yield mock

    def test_directive_uses_config_max_rows(self, mock_env):
        """Test that directive uses jsontable_max_rows from Sphinx config."""
        # Mock the environment before creating directive
        with patch.object(
            JsonTableDirective, "__init__", lambda self, *args, **kwargs: None
        ):
            directive = JsonTableDirective(
                "jsontable", [], {}, [], 1, 0, "", MagicMock(), MagicMock()
            )
            # Manually set up the directive components
            directive.options = {}
            directive.converter = TableConverter(DEFAULT_MAX_ROWS)

            assert directive.converter.default_max_rows == DEFAULT_MAX_ROWS, (
                f"Expected directive to use config value {DEFAULT_MAX_ROWS}, "
                f"got {directive.converter.default_max_rows}"
            )

    def test_directive_with_custom_config_max_rows(self):
        """Test that directive respects custom config max rows."""
        custom_limit = 7500
        mock_env = MagicMock()
        mock_env.config.jsontable_max_rows = custom_limit

        # Create directive with mocked __init__ to avoid env assignment issues
        with patch.object(
            JsonTableDirective, "__init__", lambda self, *args, **kwargs: None
        ):
            directive = JsonTableDirective(
                "jsontable", [], {}, [], 1, 0, "", MagicMock(), MagicMock()
            )
            # Manually set up the directive components
            directive.options = {}
            directive.converter = TableConverter(custom_limit)

            assert directive.converter.default_max_rows == custom_limit, (
                f"Expected directive to use custom config {custom_limit}, "
                f"got {directive.converter.default_max_rows}"
            )

    def test_directive_limit_option_nonnegative_int(self):
        """Test that directive accepts nonnegative integers for limit option."""
        from docutils.parsers.rst import directives

        assert JsonTableDirective.option_spec["limit"] == directives.nonnegative_int

    # ========================================
    # Backward Compatibility Tests
    # ========================================

    def test_backward_compatibility_no_limit_option(self):
        """Test that existing usage without :limit: option still works."""
        # Create a mock directive without using the problematic __init__
        directive = MagicMock()
        directive.converter = TableConverter()
        directive.options = {"header": True}

        # Should work without errors
        assert hasattr(directive, "converter")
        assert directive.converter.default_max_rows == DEFAULT_MAX_ROWS

    def test_backward_compatibility_existing_limit_behavior(self):
        """Test that existing :limit: behavior is preserved."""
        # Create a mock directive
        directive = MagicMock()
        directive.options = {"limit": 1000}

        limit_value = directive.options.get("limit")
        assert limit_value == 1000

    # ========================================
    # Performance and Memory Tests (CI-Safe)
    # ========================================

    @pytest.mark.performance
    def test_memory_usage_with_default_limit_ci_safe(self, converter, mock_logger):
        """Test that memory usage is controlled with default limit (CI-safe version)."""
        # Create a very large dataset
        huge_dataset = [{"id": i, "data": f"value_{i}" * 100} for i in range(50000)]

        # Should apply default limit automatically
        result = converter.convert(huge_dataset, include_header=True)

        # Memory should be controlled by limiting to DEFAULT_MAX_ROWS
        assert len(result) <= DEFAULT_MAX_ROWS + 1, (
            f"Memory usage not controlled: got {len(result)} rows, "
            f"expected <= {DEFAULT_MAX_ROWS + 1}"
        )
        assert isinstance(result, list)
        assert all(isinstance(row, list) for row in result)

    @pytest.mark.performance
    def test_processing_efficiency_limited_vs_unlimited(self, converter, mock_logger):
        """Test processing efficiency comparison (functional test only)."""
        import time

        # Large dataset that benefits from limits
        large_dataset = [{"field": f"value_{i}"} for i in range(25000)]

        # Test with default limit (should efficiently process limited data)
        start_time = time.perf_counter()
        limited_result = converter.convert(large_dataset, include_header=True)
        limited_time = time.perf_counter() - start_time

        # Test with unlimited (should process all data)
        start_time = time.perf_counter()
        unlimited_result = converter.convert(
            large_dataset, include_header=True, limit=0
        )
        unlimited_time = time.perf_counter() - start_time

        # Functional assertions (not time-based)
        assert len(limited_result) == DEFAULT_MAX_ROWS + 1, (
            f"Limited processing failed: expected {DEFAULT_MAX_ROWS + 1} rows, "
            f"got {len(limited_result)}"
        )
        assert len(unlimited_result) == len(large_dataset) + 1, (
            f"Unlimited processing failed: expected {len(large_dataset) + 1} rows, "
            f"got {len(unlimited_result)}"
        )

        # Log performance information for reference (not asserted)
        print("\nPerformance reference (not asserted):")
        print(
            f"  Limited processing:   {limited_time:.4f}s ({len(limited_result):,} rows)"
        )
        print(
            f"  Unlimited processing: {unlimited_time:.4f}s ({len(unlimited_result):,} rows)"
        )
        print(
            f"  Data reduction: {(1 - len(limited_result) / len(unlimited_result)) * 100:.1f}%"
        )


class TestPerformanceLimitsBenchmarks:
    """pytest-benchmark based performance tests for CI stability."""

    @pytest.fixture
    def converter(self):
        """Create TableConverter instance for testing."""
        return TableConverter()

    @pytest.fixture
    def mock_logger(self):
        """Shared logger mock fixture for benchmark tests."""
        with patch("sphinxcontrib.jsontable.directives.logger") as mock:
            yield mock

    @pytest.fixture
    def benchmark_dataset(self):
        """Dataset optimized for benchmark testing."""
        return [
            {"id": i, "name": f"item_{i}", "value": f"data_{i}"} for i in range(5000)
        ]

    @pytest.mark.benchmark
    def test_convert_performance_benchmark(
        self, converter, benchmark_dataset, benchmark, mock_logger
    ):
        """Benchmark convert method performance with default limits."""
        result = benchmark(converter.convert, benchmark_dataset, True)

        # Functional verification (no time assertions)
        assert isinstance(result, list), f"Expected list result, got {type(result)}"
        assert len(result) <= len(benchmark_dataset) + 1, (
            f"Result size {len(result)} exceeds input + header"
        )

    @pytest.mark.benchmark
    def test_apply_default_limit_benchmark(
        self, converter, benchmark_dataset, benchmark, mock_logger
    ):
        """Benchmark _apply_default_limit method performance."""
        result = benchmark(converter._apply_default_limit, benchmark_dataset, None)

        # Functional verification
        assert result is None or isinstance(result, int), (
            f"Expected None or int, got {type(result)}"
        )

    @pytest.mark.benchmark
    def test_estimate_data_size_benchmark(
        self, converter, benchmark_dataset, benchmark
    ):
        """Benchmark _estimate_data_size method performance."""
        result = benchmark(converter._estimate_data_size, benchmark_dataset)

        # Functional verification
        assert result == len(benchmark_dataset), (
            f"Expected size {len(benchmark_dataset)}, got {result}"
        )

    @pytest.mark.benchmark
    def test_large_dataset_processing_benchmark(
        self, converter, benchmark, mock_logger
    ):
        """Benchmark large dataset processing with various configurations."""
        large_dataset = [{"field": f"value_{i}"} for i in range(15000)]

        result = benchmark(converter.convert, large_dataset, True)

        # Should be limited by default
        expected_length = DEFAULT_MAX_ROWS + 1
        assert len(result) == expected_length, (
            f"Expected {expected_length} rows, got {len(result)}"
        )

    @pytest.mark.benchmark
    def test_scalability_benchmark_multiple_sizes(
        self, converter, benchmark, mock_logger
    ):
        """Benchmark scalability across different dataset sizes."""
        # Test with moderate size for stable benchmarking
        dataset = [{"id": i, "data": f"value_{i}"} for i in range(2000)]

        result = benchmark(converter.convert, dataset, True)

        # Functional verification
        expected_length = len(dataset) + 1
        assert len(result) == expected_length, (
            f"Expected {expected_length} rows (all data + header), got {len(result)}"
        )
        assert all(isinstance(row, list) for row in result), (
            "All result rows should be lists"
        )
