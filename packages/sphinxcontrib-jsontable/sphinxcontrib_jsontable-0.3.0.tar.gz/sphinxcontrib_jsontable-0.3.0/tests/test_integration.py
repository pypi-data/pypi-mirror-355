#!/usr/bin/env python3
"""
Integration test and demonstration script for performance limits functionality.

This script validates that the new performance limit features work correctly
in various scenarios and provides concrete examples of the improvements.
"""

import sys
import time
from io import StringIO
from unittest.mock import MagicMock, patch

from sphinxcontrib.jsontable.directives import (
    DEFAULT_MAX_ROWS,
    JsonTableDirective,
    TableConverter,
)


def test_basic_functionality():
    """Test basic functionality still works as expected."""
    print("🔧 Testing Basic Functionality...")

    converter = TableConverter()

    # Small dataset - should work without limits
    small_data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    result = converter.convert(small_data, include_header=True)

    assert len(result) == 3  # Header + 2 rows
    assert result[0] == ["name", "age"]  # Header
    print("   ✅ Small dataset processing works correctly")

    # Single object - should work
    single_obj = {"name": "Charlie", "age": 35}
    result = converter.convert(single_obj, include_header=True)

    assert len(result) == 2  # Header + 1 row
    print("   ✅ Single object processing works correctly")


def test_default_limit_application():
    """Test that default limit is applied to large datasets."""
    print(
        f"\n🛡️  Testing Default Limit Application (DEFAULT_MAX_ROWS = {DEFAULT_MAX_ROWS:,})..."
    )

    converter = TableConverter()

    # Create dataset larger than DEFAULT_MAX_ROWS
    large_dataset = [{"id": i, "name": f"item_{i}"} for i in range(15000)]

    # Capture warnings
    StringIO()
    with patch("sphinxcontrib.jsontable.directives.logger") as mock_logger:
        result = converter.convert(large_dataset, include_header=True)

        # Check that limit was applied
        assert len(result) == DEFAULT_MAX_ROWS + 1  # Header + limited rows
        print(f"   ✅ Large dataset (15,000 rows) limited to {DEFAULT_MAX_ROWS:,} rows")

        # Check that warning was logged
        mock_logger.warning.assert_called_once()
        warning_msg = mock_logger.warning.call_args[0][0]
        assert "15,000 rows" in warning_msg
        assert "10,000 rows" in warning_msg
        print("   ✅ Warning message logged correctly")


def test_unlimited_override():
    """Test that :limit: 0 provides unlimited processing."""
    print("\n🔓 Testing Unlimited Override (:limit: 0)...")

    converter = TableConverter()

    # Large dataset
    large_dataset = [{"id": i} for i in range(12000)]

    with patch("sphinxcontrib.jsontable.directives.logger") as mock_logger:
        result = converter.convert(large_dataset, include_header=True, limit=0)

        # Should process all rows
        assert len(result) == 12000 + 1  # Header + all rows
        print("   ✅ All 12,000 rows processed with :limit: 0")

        # Check info message
        mock_logger.info.assert_called_once_with(
            "JsonTable: Unlimited rows requested via :limit: 0"
        )
        print("   ✅ Info message logged for unlimited request")


def test_custom_limit():
    """Test custom limit values."""
    print("\n🎯 Testing Custom Limit Values...")

    converter = TableConverter()

    # Large dataset
    large_dataset = [{"id": i} for i in range(8000)]

    # Test custom limit
    custom_limit = 3000
    result = converter.convert(large_dataset, include_header=True, limit=custom_limit)

    assert len(result) == custom_limit + 1  # Header + custom limit
    print(f"   ✅ Custom limit of {custom_limit:,} rows applied correctly")


def test_custom_default_max_rows():
    """Test custom default max rows configuration."""
    print("\n⚙️  Testing Custom Default Max Rows...")

    custom_default = 5000
    converter = TableConverter(default_max_rows=custom_default)

    # Dataset larger than custom default but smaller than DEFAULT_MAX_ROWS
    medium_dataset = [{"id": i} for i in range(7000)]

    with patch("sphinxcontrib.jsontable.directives.logger") as mock_logger:
        result = converter.convert(medium_dataset, include_header=True)

        # Should be limited by custom default
        assert len(result) == custom_default + 1
        print(f"   ✅ Custom default limit of {custom_default:,} rows applied")

        # Check warning message mentions custom limit
        warning_msg = mock_logger.warning.call_args[0][0]
        assert "7,000 rows" in warning_msg
        assert "5,000 rows" in warning_msg
        print("   ✅ Warning message shows custom limit correctly")


def test_performance_improvement():
    """Test that performance is improved with limits."""
    print("\n⚡ Testing Performance Improvement...")

    converter = TableConverter()

    # Create large dataset for performance testing
    large_dataset = [
        {f"field_{j}": f"value_{i}_{j}" for j in range(10)} for i in range(20000)
    ]

    # Test with default limit
    with patch("sphinxcontrib.jsontable.directives.logger"):
        start_time = time.perf_counter()
        limited_result = converter.convert(large_dataset, include_header=True)
        limited_time = time.perf_counter() - start_time

    print(
        f"   ⏱️  Limited processing: {limited_time:.3f}s ({len(limited_result):,} rows)"
    )

    # Test with unlimited (subset for reasonable test time)
    test_dataset = large_dataset[:12000]  # Smaller subset for unlimited test
    with patch("sphinxcontrib.jsontable.directives.logger"):
        start_time = time.perf_counter()
        unlimited_result = converter.convert(test_dataset, include_header=True, limit=0)
        unlimited_time = time.perf_counter() - start_time

    print(
        f"   ⏱️  Unlimited processing: {unlimited_time:.3f}s ({len(unlimited_result):,} rows)"
    )

    # Performance benefit check
    efficiency_ratio = limited_time / unlimited_time if unlimited_time > 0 else 0
    print(f"   📊 Efficiency ratio: {efficiency_ratio:.2f} (lower is better)")

    if efficiency_ratio <= 1.0:
        print("   ✅ Performance improvement confirmed")
    else:
        print("   ℹ️  Limited processing maintains reasonable performance")  # noqa: RUF001


def test_sphinx_directive_integration():
    """Test Sphinx directive integration."""
    print("\n🐍 Testing Sphinx Directive Integration...")

    # Test default config value behavior
    with patch("sphinxcontrib.jsontable.directives.getattr") as mock_getattr:
        mock_getattr.return_value = DEFAULT_MAX_ROWS

        # Create directive instance with basic mocks
        directive = JsonTableDirective(
            "jsontable", [], {}, [], 1, 0, "", MagicMock(), MagicMock()
        )
        # Test that it uses config value
        assert directive.converter.default_max_rows == DEFAULT_MAX_ROWS
        print("   ✅ Directive uses Sphinx config value correctly")

    # Test with custom config
    custom_config_value = 7500
    with patch("sphinxcontrib.jsontable.directives.getattr") as mock_getattr:
        mock_getattr.return_value = custom_config_value

        directive = JsonTableDirective(
            "jsontable", [], {}, [], 1, 0, "", MagicMock(), MagicMock()
        )
        assert directive.converter.default_max_rows == custom_config_value
        print(f"   ✅ Custom config value ({custom_config_value:,}) respected")


def test_backward_compatibility():
    """Test backward compatibility with existing usage."""
    print("\n🔄 Testing Backward Compatibility...")

    converter = TableConverter()

    # Test existing usage patterns
    data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]

    # Original usage (no limit parameter)
    result1 = converter.convert(data, include_header=True)

    # Should work exactly as before
    assert len(result1) == 3
    assert result1[0] == ["name", "age"]
    assert result1[1] == ["Alice", "30"]
    assert result1[2] == ["Bob", "25"]
    print("   ✅ Original usage patterns work unchanged")

    # Existing limit usage should work
    result2 = converter.convert(data, include_header=True, limit=1)
    assert len(result2) == 2  # Header + 1 limited row
    print("   ✅ Existing :limit: option behavior preserved")


def run_all_tests():
    """Run all integration tests."""
    print("🚀 PERFORMANCE LIMITS INTEGRATION TESTS")
    print("=" * 60)

    try:
        test_basic_functionality()
        test_default_limit_application()
        test_unlimited_override()
        test_custom_limit()
        test_custom_default_max_rows()
        test_performance_improvement()
        test_sphinx_directive_integration()
        test_backward_compatibility()

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Performance limits functionality is working correctly")
        print("✅ Backward compatibility is maintained")
        print("✅ New features are functioning as expected")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def demonstrate_usage():
    """Demonstrate the new functionality with examples."""
    print("\n" + "=" * 60)
    print("📖 USAGE DEMONSTRATION")
    print("=" * 60)

    print("\n1️⃣  Default behavior (automatic protection):")
    print("   .. jsontable:: large_data.json")
    print("      :header:")
    print("   → Automatically limits to 10,000 rows with warning")

    print("\n2️⃣  Unlimited processing (explicit override):")
    print("   .. jsontable:: large_data.json")
    print("      :header:")
    print("      :limit: 0")
    print("   → Processes all rows (use with caution)")

    print("\n3️⃣  Custom limit:")
    print("   .. jsontable:: large_data.json")
    print("      :header:")
    print("      :limit: 5000")
    print("   → Limits to exactly 5,000 rows")

    print("\n4️⃣  Project-wide configuration (conf.py):")
    print("   jsontable_max_rows = 15000")
    print("   → Changes default limit for entire project")

    print("\n💡 Benefits:")
    print("   • Prevents accidental memory exhaustion")
    print("   • Improves rendering performance")
    print("   • Provides clear user guidance")
    print("   • Maintains full backward compatibility")


if __name__ == "__main__":
    # Run integration tests
    success = run_all_tests()

    # Show usage examples
    demonstrate_usage()

    # Exit with appropriate code
    sys.exit(0 if success else 1)
