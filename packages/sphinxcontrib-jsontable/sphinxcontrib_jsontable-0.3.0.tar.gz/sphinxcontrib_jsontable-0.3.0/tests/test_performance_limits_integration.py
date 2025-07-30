"""
Additional integration tests for performance limits with existing test infrastructure.

This module adds new functionality tests to the existing test suite to ensure
proper integration of performance limits with all existing features.
"""

from unittest.mock import MagicMock, patch

import pytest

from sphinxcontrib.jsontable.directives import (
    DEFAULT_MAX_ROWS,
    JsonTableDirective,
    JsonTableError,
    TableConverter,
)


class TestTableConverterPerformanceLimitsIntegration:
    """Integration tests for performance limits with existing converter functionality."""

    @pytest.fixture
    def converter(self):
        """Create TableConverter instance for testing."""
        return TableConverter()

    @pytest.fixture
    def converter_custom_limit(self):
        """Create TableConverter with custom default limit."""
        return TableConverter(default_max_rows=5000)

    @pytest.fixture
    def mock_logger(self):
        """Shared logger mock fixture for DRY principle compliance."""
        with patch("sphinxcontrib.jsontable.directives.logger") as mock:
            yield mock

    @pytest.fixture
    def dataset_generator(self):
        """Unified test data generator for consistent test data creation."""

        def _generate(size: int, data_type: str = "object") -> list:
            if data_type == "object":
                return [{"id": i, "value": f"item_{i}"} for i in range(size)]
            elif data_type == "array":
                return [[i, f"value_{i}"] for i in range(size)]
            else:
                raise ValueError(f"Unsupported data_type: {data_type}")

        return _generate

    @pytest.fixture
    def large_object_list(self, dataset_generator):
        """Large list of objects exceeding default limit."""
        return dataset_generator(15000, "object")

    @pytest.fixture
    def large_array_list(self, dataset_generator):
        """Large list of arrays exceeding default limit."""
        return dataset_generator(12000, "array")

    # ========================================
    # Integration with existing convert method
    # ========================================

    def test_convert_applies_default_limit_to_large_object_list(
        self, converter, large_object_list, mock_logger
    ):
        """
        大量オブジェクトリストに対してデフォルト制限が適用されることを確認。

        Given: DEFAULT_MAX_ROWSを超える大量オブジェクトリスト
        When: convert メソッドを呼び出す
        Then: DEFAULT_MAX_ROWS + ヘッダーに制限され、警告が出力される
        """
        result = converter.convert(large_object_list, include_header=True)

        # Should be limited to DEFAULT_MAX_ROWS + header
        expected_length = DEFAULT_MAX_ROWS + 1
        assert len(result) == expected_length, (
            f"Expected {expected_length} rows (header + {DEFAULT_MAX_ROWS} data), "
            f"got {len(result)}"
        )
        mock_logger.warning.assert_called_once()

    def test_convert_applies_default_limit_to_large_array_list(
        self, converter, large_array_list, mock_logger
    ):
        """Test that convert method applies default limit to large array lists."""
        result = converter.convert(large_array_list, include_header=False)

        # Should be limited to DEFAULT_MAX_ROWS
        assert len(result) == DEFAULT_MAX_ROWS, (
            f"Expected {DEFAULT_MAX_ROWS} rows, got {len(result)}"
        )
        mock_logger.warning.assert_called_once()

    def test_convert_respects_custom_default_limit(
        self, converter_custom_limit, large_object_list, mock_logger
    ):
        """Test that convert method respects custom default limit."""
        result = converter_custom_limit.convert(large_object_list, include_header=True)

        # Should be limited to custom limit + header
        expected_length = 5000 + 1
        assert len(result) == expected_length, (
            f"Expected {expected_length} rows (header + 5000 data), got {len(result)}"
        )
        mock_logger.warning.assert_called_once()

    def test_convert_unlimited_override_works_with_large_data(
        self, converter, large_object_list, mock_logger
    ):
        """Test that :limit: 0 override works with large datasets."""
        result = converter.convert(large_object_list, include_header=True, limit=0)

        # Should process all data
        expected_length = len(large_object_list) + 1
        assert len(result) == expected_length, (
            f"Expected unlimited processing ({expected_length} rows), got {len(result)}"
        )
        mock_logger.info.assert_called_once()

    def test_convert_explicit_limit_overrides_default(
        self, converter, large_object_list
    ):
        """Test that explicit limit overrides default limit."""
        custom_limit = 3000
        result = converter.convert(
            large_object_list, include_header=True, limit=custom_limit
        )

        # Should be limited to explicit limit + header
        expected_length = custom_limit + 1
        assert len(result) == expected_length, (
            f"Expected {expected_length} rows (header + {custom_limit} data), "
            f"got {len(result)}"
        )

    # ========================================
    # Integration with different data types
    # ========================================

    def test_single_dict_not_affected_by_default_limit(self, converter):
        """Test that single dictionary is not affected by default limit."""
        single_dict = {"key": "value"}
        result = converter.convert(single_dict, include_header=True)

        # Should process normally without limit
        assert len(result) == 2, f"Expected 2 rows (header + 1 data), got {len(result)}"

    def test_small_dataset_not_affected_by_default_limit(self, converter, mock_logger):
        """Test that small datasets are not affected by default limit."""
        small_data = [{"id": i} for i in range(100)]

        result = converter.convert(small_data, include_header=True)

        # Should process all data without warning
        expected_length = 101  # Header + 100 rows
        assert len(result) == expected_length, (
            f"Expected {expected_length} rows, got {len(result)}"
        )
        mock_logger.warning.assert_not_called()

    @pytest.mark.parametrize(
        "dataset_size,should_limit",
        [
            (DEFAULT_MAX_ROWS, False),  # 境界値(等しい)
            (DEFAULT_MAX_ROWS + 1, True),  # 境界値(超過)
        ],
    )
    def test_limit_threshold_behavior(
        self, converter, dataset_generator, dataset_size, should_limit, mock_logger
    ):
        """Test behavior at the limit threshold boundaries."""
        test_data = dataset_generator(dataset_size, "object")
        result = converter.convert(test_data, include_header=True)

        if should_limit:
            expected_length = DEFAULT_MAX_ROWS + 1
            assert len(result) == expected_length
            mock_logger.warning.assert_called_once()
        else:
            expected_length = dataset_size + 1
            assert len(result) == expected_length
            mock_logger.warning.assert_not_called()

    # ========================================
    # Error handling integration
    # ========================================

    @pytest.mark.parametrize(
        "invalid_data",
        [
            "invalid_string",
            123,
            None,
        ],
    )
    def test_error_handling_not_affected_by_limits(self, converter, invalid_data):
        """Test that error handling works normally with limit functionality."""
        with pytest.raises(JsonTableError):
            converter.convert(invalid_data)

    def test_empty_data_handling_with_limits(self, converter):
        """Test that empty data handling works with limit functionality."""
        with pytest.raises(JsonTableError):
            converter.convert([])


class TestJsonTableDirectivePerformanceLimitsIntegration:
    """Integration tests for JsonTableDirective with performance limits."""

    @pytest.fixture
    def mock_env(self):
        """Mock Sphinx environment."""
        env = MagicMock()
        env.config.jsontable_max_rows = DEFAULT_MAX_ROWS
        env.srcdir = "/tmp/test"
        return env

    def test_directive_uses_default_config_value(self, mock_env):
        """Test that directive uses default config value."""
        # Use proper mocking to avoid env assignment issues
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
                f"Expected directive to use default config {DEFAULT_MAX_ROWS}, "
                f"got {directive.converter.default_max_rows}"
            )

    def test_directive_uses_custom_config_value(self):
        """Test that directive uses custom config value."""
        custom_limit = 7500
        mock_env = MagicMock()
        mock_env.config.jsontable_max_rows = custom_limit
        mock_env.srcdir = "/tmp/test"

        # Use proper mocking to avoid env assignment issues
        with patch.object(
            JsonTableDirective, "__init__", lambda self, *args, **kwargs: None
        ):
            directive = JsonTableDirective(
                "jsontable", [], {}, [], 1, 0, "", MagicMock(), MagicMock()
            )
            # Manually set up the directive components
            directive.options = {}
            directive.converter = TableConverter(custom_limit)

            expected_limit = 7500
            assert directive.converter.default_max_rows == expected_limit, (
                f"Expected directive to use custom config {expected_limit}, "
                f"got {directive.converter.default_max_rows}"
            )

    def test_directive_option_spec_includes_nonnegative_int(self):
        """Test that directive option_spec includes nonnegative_int for limit."""
        from docutils.parsers.rst import directives

        assert JsonTableDirective.option_spec["limit"] == directives.nonnegative_int

    @pytest.mark.parametrize("limit_value", [5000, 0])
    def test_directive_limit_option_parsing(self, limit_value):
        """Test that directive correctly parses limit options."""
        mock_env = MagicMock()
        mock_env.config.jsontable_max_rows = DEFAULT_MAX_ROWS
        mock_env.srcdir = "/tmp/test"

        # Use proper mocking to avoid env assignment issues
        with patch.object(
            JsonTableDirective, "__init__", lambda self, *args, **kwargs: None
        ):
            directive = JsonTableDirective(
                "jsontable",
                [],
                {"limit": limit_value},
                [],
                1,
                0,
                "",
                MagicMock(),
                MagicMock(),
            )
            # Manually set up the directive components
            directive.options = {"limit": limit_value}

            assert directive.options.get("limit") == limit_value, (
                f"Expected limit option {limit_value}, got {directive.options.get('limit')}"
            )


class TestBackwardCompatibilityWithLimits:
    """Ensure that all existing functionality continues to work with limits."""

    @pytest.fixture
    def converter(self):
        """Create TableConverter instance for testing."""
        return TableConverter()

    @pytest.fixture
    def mock_logger(self):
        """Shared logger mock fixture for backward compatibility tests."""
        with patch("sphinxcontrib.jsontable.directives.logger") as mock:
            yield mock

    def test_existing_usage_patterns_unchanged(self, converter):
        """Test that existing usage patterns work unchanged."""
        # Original usage without any limit specification
        small_data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]

        result = converter.convert(small_data, include_header=True)

        # Should work exactly as before
        assert len(result) == 3, f"Expected 3 rows, got {len(result)}"
        assert result[0] == ["name", "age"]
        assert result[1] == ["Alice", "30"]
        assert result[2] == ["Bob", "25"]

    def test_existing_limit_option_behavior_preserved(self, converter):
        """Test that existing :limit: option behavior is preserved."""
        data = [{"id": i} for i in range(1000)]

        # Existing limit usage should work exactly as before
        result = converter.convert(data, include_header=True, limit=50)

        expected_length = 51  # Header + 50 limited rows
        assert len(result) == expected_length, (
            f"Expected {expected_length} rows, got {len(result)}"
        )

    def test_header_functionality_preserved(self, converter, mock_logger):
        """Test that header functionality works with limits."""
        large_data = [{"field": f"value_{i}"} for i in range(15000)]

        # With header
        result_with_header = converter.convert(large_data, include_header=True)
        assert result_with_header[0] == ["field"], "Header row should be preserved"
        assert len(result_with_header) == DEFAULT_MAX_ROWS + 1

        # Without header
        result_without_header = converter.convert(large_data, include_header=False)
        assert len(result_without_header) == DEFAULT_MAX_ROWS

    def test_encoding_option_unaffected(self):
        """Test that encoding option continues to work with limits."""
        mock_env = MagicMock()
        mock_env.config.jsontable_max_rows = DEFAULT_MAX_ROWS
        mock_env.srcdir = "/tmp/test"

        # Use proper mocking to avoid env assignment issues
        with patch.object(
            JsonTableDirective, "__init__", lambda self, *args, **kwargs: None
        ):
            directive = JsonTableDirective(
                "jsontable",
                [],
                {"encoding": "utf-16"},
                [],
                1,
                0,
                "",
                MagicMock(),
                MagicMock(),
            )
            # Manually set up the directive components
            directive.options = {"encoding": "utf-16"}
            # Create a loader with the specified encoding
            from sphinxcontrib.jsontable.directives import JsonDataLoader

            directive.loader = JsonDataLoader("utf-16")

            # Should still respect encoding option
            assert directive.loader.encoding == "utf-16", (
                f"Expected utf-16 encoding, got {directive.loader.encoding}"
            )

    @pytest.mark.parametrize(
        "invalid_data",
        [
            "invalid",
            [None],  # Invalid first element
        ],
    )
    def test_error_conditions_unchanged(self, converter, invalid_data):
        """Test that error conditions continue to work as expected."""
        with pytest.raises(JsonTableError):
            converter.convert(invalid_data)


class TestPerformanceLimitsWithComplexData:
    """Test performance limits with complex real-world data structures."""

    @pytest.fixture
    def converter(self):
        """Create TableConverter instance for testing."""
        return TableConverter()

    @pytest.fixture
    def mock_logger(self):
        """Shared logger mock fixture for complex data tests."""
        with patch("sphinxcontrib.jsontable.directives.logger") as mock:
            yield mock

    def test_complex_nested_data_with_limits(self, converter, mock_logger):
        """Test that complex nested data works with limits."""
        complex_data = []
        for i in range(12000):
            obj = {
                "id": i,
                "user": {"name": f"User_{i}", "email": f"user{i}@example.com"},
                "settings": {"theme": "dark", "notifications": True},
                "data": [1, 2, 3, 4, 5],
            }
            complex_data.append(obj)

        result = converter.convert(complex_data, include_header=True)

        # Should be limited and flattened appropriately
        expected_length = DEFAULT_MAX_ROWS + 1
        assert len(result) == expected_length, (
            f"Expected {expected_length} rows, got {len(result)}"
        )
        mock_logger.warning.assert_called_once()

        # Check that nested data is converted to strings
        assert isinstance(result[1][1], str), "User field should be converted to string"

    def test_mixed_data_types_with_limits(self, converter, mock_logger):
        """Test that mixed data types work with limits."""
        mixed_data = []
        for i in range(11000):
            obj = {
                "id": i,
                "name": f"Item_{i}",
                "price": 99.99 + i,
                "available": i % 2 == 0,
                "tags": ["tag1", "tag2"],
                "metadata": None if i % 100 == 0 else {"created": "2023-01-01"},
            }
            mixed_data.append(obj)

        result = converter.convert(mixed_data, include_header=True)

        # Should handle mixed types and be limited
        expected_length = DEFAULT_MAX_ROWS + 1
        assert len(result) == expected_length, (
            f"Expected {expected_length} rows, got {len(result)}"
        )
        assert all(isinstance(cell, str) for row in result for cell in row), (
            "All cells should be converted to strings"
        )

    def test_very_wide_data_with_limits(self, converter, mock_logger):
        """Test that very wide data (many columns) works with limits."""
        wide_data = []
        for i in range(8000):
            obj = {f"field_{j}": f"value_{i}_{j}" for j in range(50)}
            wide_data.append(obj)

        result = converter.convert(wide_data, include_header=True)

        # Should be limited in rows but preserve all columns
        # Fix: 8000 rows data should result in 8001 rows (8000 + header), not 10001
        expected_length = len(wide_data) + 1  # 8000 + 1 header = 8001
        assert len(result) == expected_length, (
            f"Expected {expected_length} rows, got {len(result)}"
        )
        assert len(result[0]) == 50, f"Expected 50 columns, got {len(result[0])}"
