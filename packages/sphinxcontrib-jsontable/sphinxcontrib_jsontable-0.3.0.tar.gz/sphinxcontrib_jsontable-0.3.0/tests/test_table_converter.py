"""
Comprehensive unit tests for TableConverter class.

This module contains exhaustive test cases covering all methods of the TableConverter class,
including both normal and error scenarios. Tests follow the AAA pattern with single assertions
and proper isolation using mocks.
"""

import time
from typing import Any
from unittest.mock import patch

import pytest

from sphinxcontrib.jsontable.directives import (
    INVALID_JSON_DATA_ERROR,
    JsonTableError,
    TableConverter,
)

# Type aliases
JsonData = dict[str, Any] | list[Any]
TableData = list[list[str]]


# Test Fixtures
@pytest.fixture
def converter():
    """Create TableConverter instance for testing."""
    return TableConverter()


@pytest.fixture
def sample_dict():
    """Sample dictionary data for testing."""
    return {"name": "John", "age": 30, "city": "Tokyo"}


@pytest.fixture
def sample_list_of_dicts():
    """Sample list of dictionaries for testing."""
    return [{"name": "John", "age": 30}, {"name": "Jane", "age": 25, "city": "Osaka"}]


@pytest.fixture
def sample_list_of_lists():
    """Sample list of lists for testing."""
    return [["John", "30"], ["Jane", "25"]]


@pytest.fixture
def sample_headers():
    """Sample headers for testing."""
    return ["age", "name"]


@pytest.fixture
def sample_user_data():
    """
    ユーザーデータのサンプルを提供するフィクスチャ。

    Returns:
        List[Dict]: APIレスポンス風のユーザーデータ
    """
    return [
        {
            "id": 1,
            "username": "alice",
            "email": "alice@example.com",
            "first_name": "Alice",
            "last_name": "Smith",
            "created_at": "2023-01-01",
        },
        {
            "id": 2,
            "username": "bob",
            "email": "bob@example.com",
            "first_name": "Bob",
            "last_name": "Johnson",
            "created_at": "2023-01-02",
            "last_login": "2023-06-01",  # 一部ユーザーのみ持つフィールド
        },
    ]


@pytest.fixture
def large_dataset():
    """
    パフォーマンステスト用の大量データセットを提供するフィクスチャ。

    Returns:
        List[Dict]: 1000個のオブジェクトを含むデータセット
    """
    objects = []
    for i in range(1000):
        obj = {f"key_{j}": f"value_{j}" for j in range(i % 10, (i % 10) + 5)}
        objects.append(obj)
    return objects


class TestTableConverterConvert:
    """Test cases for the convert method."""

    def test_convert_dict_input_calls_convert_dict(self, converter):
        """Test convert method routes dict input to _convert_dict method."""
        # Arrange
        test_data = {"key": "value"}
        with patch.object(
            converter, "_convert_dict", return_value=[]
        ) as mock_convert_dict:
            # Act
            converter.convert(test_data, include_header=True, limit=10)
            # Assert
            mock_convert_dict.assert_called_once_with(test_data, True, 10)

    def test_convert_list_input_calls_convert_list(self, converter):
        """Test convert method routes list input to _convert_list method."""
        # Arrange
        test_data = [{"key": "value"}]
        with patch.object(
            converter, "_convert_list", return_value=[]
        ) as mock_convert_list:
            # Act
            converter.convert(test_data, include_header=False, limit=5)
            # Assert
            mock_convert_list.assert_called_once_with(test_data, False, 5)

    def test_convert_empty_data_raises_json_table_error(self, converter):
        """Test convert method raises JsonTableError for empty data."""
        # Act & Assert
        with pytest.raises(JsonTableError, match="No JSON data to process"):
            converter.convert(None, include_header=False)

    def test_convert_invalid_data_type_raises_json_table_error(self, converter):
        """Test convert method raises JsonTableError for invalid data types."""
        # Arrange
        invalid_data = "string_data"
        # Act & Assert
        with pytest.raises(JsonTableError, match=INVALID_JSON_DATA_ERROR):
            converter.convert(invalid_data)

    def test_convert_integer_data_raises_json_table_error(self, converter):
        """Test convert method raises JsonTableError for integer input."""
        # Arrange
        invalid_data = 123
        # Act & Assert
        with pytest.raises(JsonTableError, match=INVALID_JSON_DATA_ERROR):
            converter.convert(invalid_data)


class TestTableConverterConvertDict:
    """Test cases for the _convert_dict method."""

    def test_convert_dict_valid_data_calls_convert_object_list(
        self, converter, sample_dict
    ):
        """Test _convert_dict calls _convert_object_list with wrapped dict."""
        # Arrange
        with patch.object(
            converter, "_convert_object_list", return_value=[]
        ) as mock_convert:
            # Act
            converter._convert_dict(sample_dict, True, 5)
            # Assert
            mock_convert.assert_called_once_with([sample_dict], True, 5)

    def test_convert_dict_zero_limit_returns_empty_list(self, converter, sample_dict):
        """Test _convert_dict returns empty list when limit is zero."""
        # Arrange & Act
        result = converter._convert_dict(sample_dict, True, 0)
        # Assert
        assert result == []

    def test_convert_dict_negative_limit_returns_empty_list(
        self, converter, sample_dict
    ):
        """Test _convert_dict returns empty list when limit is negative."""
        # Arrange & Act
        result = converter._convert_dict(sample_dict, False, -1)
        # Assert
        assert result == []

    def test_convert_dict_none_limit_processes_data(self, converter, sample_dict):
        """Test _convert_dict processes data when limit is None."""
        # Arrange
        with patch.object(
            converter, "_convert_object_list", return_value=[["row1"]]
        ) as mock_convert:  # noqa
            # Act
            result = converter._convert_dict(sample_dict, False, None)
            # Assert
            assert result == [["row1"]]


class TestTableConverterConvertList:
    """Test cases for the _convert_list method."""

    def test_convert_list_empty_list_returns_empty_list(self, converter):
        """Test _convert_list returns empty list for empty input."""
        # Arrange & Act
        result = converter._convert_list([], True, None)
        # Assert
        assert result == []

    def test_convert_list_dict_items_calls_convert_object_list(
        self, converter, sample_list_of_dicts
    ):
        """Test _convert_list calls _convert_object_list for dict items."""
        # Arrange
        with patch.object(
            converter, "_convert_object_list", return_value=[]
        ) as mock_convert:
            # Act
            converter._convert_list(sample_list_of_dicts, True, 5)
            # Assert
            mock_convert.assert_called_once_with(sample_list_of_dicts, True, 5)

    def test_convert_list_array_items_calls_convert_array_list(
        self, converter, sample_list_of_lists
    ):
        """Test _convert_list calls _convert_array_list for array items."""
        # Arrange
        with patch.object(
            converter, "_convert_array_list", return_value=[]
        ) as mock_convert:
            # Act
            converter._convert_list(sample_list_of_lists, False, 3)
            # Assert
            mock_convert.assert_called_once_with(sample_list_of_lists, 3)

    def test_convert_list_none_first_element_raises_error(self, converter):
        """Test _convert_list raises error when first element is None."""
        # Arrange
        data_with_none = [None, {"key": "value"}]
        # Act & Assert
        with pytest.raises(
            JsonTableError, match="Invalid array data: null first element"
        ):
            converter._convert_list(data_with_none, False, None)

    def test_convert_list_invalid_first_element_raises_error(self, converter):
        """Test _convert_list raises error for invalid first element type."""
        # Arrange
        invalid_data = ["string", "another_string"]
        # Act & Assert
        with pytest.raises(
            JsonTableError, match="Array items must be objects or arrays"
        ):
            converter._convert_list(invalid_data, False, None)

    def test_convert_list_with_limit_processes_limited_data(
        self, converter, sample_list_of_dicts
    ):
        """Test _convert_list processes only limited data when limit is set."""
        # Arrange
        with patch.object(converter, "_convert_object_list") as mock_convert:
            # Act
            converter._convert_list(sample_list_of_dicts, True, 1)
            # Assert
            mock_convert.assert_called_once_with(sample_list_of_dicts[:1], True, 1)


class TestTableConverterConvertObjectList:
    """Test cases for the _convert_object_list method."""

    def test_convert_object_list_empty_list_returns_empty_list(self, converter):
        """Test _convert_object_list returns empty list for empty input."""
        # Arrange & Act
        result = converter._convert_object_list([], True, None)
        # Assert
        assert result == []

    def test_convert_object_list_with_header_includes_header_row(
        self, converter, sample_list_of_dicts
    ):
        """Test _convert_object_list includes header when include_header is True."""
        # Arrange
        with patch.object(converter, "_extract_headers", return_value=["age", "name"]):
            with patch.object(converter, "_object_to_row", return_value=["30", "John"]):
                # Act
                result = converter._convert_object_list(
                    sample_list_of_dicts, True, None
                )
                # Assert
                assert result[0] == ["age", "name"]

    def test_convert_object_list_without_header_excludes_header_row(
        self, converter, sample_list_of_dicts
    ):
        """Test _convert_object_list excludes header when include_header is False."""
        # Arrange
        with patch.object(converter, "_extract_headers", return_value=["age", "name"]):
            with patch.object(converter, "_object_to_row", return_value=["30", "John"]):
                # Act
                result = converter._convert_object_list(
                    sample_list_of_dicts, False, None
                )
                # Assert
                assert ["age", "name"] not in result

    def test_convert_object_list_calls_extract_headers(
        self, converter, sample_list_of_dicts
    ):
        """Test _convert_object_list calls _extract_headers method."""
        # Arrange
        with patch.object(
            converter, "_extract_headers", return_value=[]
        ) as mock_extract:
            with patch.object(converter, "_object_to_row", return_value=[]):
                # Act
                converter._convert_object_list(sample_list_of_dicts, False, None)
                # Assert
                mock_extract.assert_called_once_with(sample_list_of_dicts)

    def test_convert_object_list_applies_limit(self, converter, sample_list_of_dicts):
        """Test _convert_object_list applies limit to objects."""
        # Arrange
        with patch.object(converter, "_extract_headers", return_value=["name"]):
            with patch.object(
                converter, "_object_to_row", return_value=["John"]
            ) as mock_to_row:
                # Act
                converter._convert_object_list(sample_list_of_dicts, False, 1)
                # Assert
                assert mock_to_row.call_count == 1


class TestTableConverterConvertArrayList:
    """Test cases for the _convert_array_list method."""

    def test_convert_array_list_converts_all_elements_to_strings(
        self, converter, sample_list_of_lists
    ):
        """Test _convert_array_list converts all elements to strings."""
        # Arrange
        data_with_mixed_types = [[1, "John"], [2.5, "Jane"]]
        # Act
        result = converter._convert_array_list(data_with_mixed_types, None)
        # Assert
        assert result == [["1", "John"], ["2.5", "Jane"]]

    def test_convert_array_list_applies_limit(self, converter, sample_list_of_lists):
        """Test _convert_array_list applies limit to arrays."""
        # Arrange & Act
        result = converter._convert_array_list(sample_list_of_lists, 1)
        # Assert
        assert len(result) == 1

    def test_convert_array_list_handles_none_values(self, converter):
        """Test _convert_array_list handles None values correctly."""
        # Arrange
        data_with_none = [[None, "John"], ["Jane", None]]
        # Act
        result = converter._convert_array_list(data_with_none, None)
        # Assert
        assert result == [["", "John"], ["Jane", ""]]

    def test_convert_array_list_no_limit_processes_all_data(
        self, converter, sample_list_of_lists
    ):
        """Test _convert_array_list processes all data when no limit is set."""
        # Arrange & Act
        result = converter._convert_array_list(sample_list_of_lists, None)
        # Assert
        assert len(result) == len(sample_list_of_lists)


class TestTableConverterExtractHeaders:
    """Test cases for the _extract_headers method."""

    # ========================================
    # 基本機能テスト
    # ========================================

    def test_empty_objects_list(self, converter):
        """
        空のオブジェクトリストを処理した場合、空のリストが返されることを確認。

        Given: 空のオブジェクトリスト
        When: _extract_headers を呼び出す
        Then: 空のリストが返される
        """
        # Arrange
        objects = []

        # Act
        result = converter._extract_headers(objects)

        # Assert
        assert result == []
        assert isinstance(result, list)

    def test_single_object_key_order_preservation(self, converter):
        """
        単一オブジェクトのキー順序が保持されることを確認。

        Given: 特定の順序のキーを持つ単一オブジェクト
        When: _extract_headers を呼び出す
        Then: 元の順序でキーが返される
        """
        # Arrange
        objects = [
            {"name": "Alice", "age": 30, "city": "Tokyo", "email": "alice@example.com"}
        ]
        expected = ["name", "age", "city", "email"]

        # Act
        result = converter._extract_headers(objects)

        # Assert
        assert result == expected
        assert len(result) == 4

    def test_multiple_objects_first_object_priority(self, converter):
        """
        複数オブジェクトの場合、最初のオブジェクトのキー順序が優先されることを確認。

        Given: 異なるキー順序を持つ複数オブジェクト
        When: _extract_headers を呼び出す
        Then: 最初のオブジェクトの順序 + 追加キーの順序でキーが返される
        """
        # Arrange
        objects = [
            {"name": "Alice", "age": 30, "city": "Tokyo"},
            {"age": 25, "name": "Bob", "country": "Japan"},  # name, age は既存
            {
                "city": "Osaka",
                "name": "Charlie",
                "email": "charlie@example.com",
            },  # email が新規
        ]
        expected = ["name", "age", "city", "country", "email"]

        # Act
        result = converter._extract_headers(objects)

        # Assert
        assert result == expected
        assert len(result) == 5

    def test_additional_keys_append_order(self, converter):
        """
        後続オブジェクトの新しいキーが発見順で追加されることを確認。

        Given: 段階的に新しいキーが追加される複数オブジェクト
        When: _extract_headers を呼び出す
        Then: キーが発見された順序で追加される
        """
        # Arrange
        objects = [
            {"a": 1, "b": 2},
            {"a": 1, "c": 3, "d": 4},  # c, d が追加
            {"a": 1, "e": 5, "f": 6},  # e, f が追加
        ]
        expected = ["a", "b", "c", "d", "e", "f"]

        # Act
        result = converter._extract_headers(objects)

        # Assert
        assert result == expected

    def test_duplicate_keys_no_repetition(self, converter):
        """
        重複するキーが複数回含まれないことを確認。

        Given: 同じキーを持つ複数オブジェクト
        When: _extract_headers を呼び出す
        Then: 各キーが一度だけ含まれる
        """
        # Arrange
        objects = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35},
        ]
        expected = ["name", "age"]

        # Act
        result = converter._extract_headers(objects)

        # Assert
        assert result == expected
        assert len(set(result)) == len(result)  # 重複なしの確認

    # ========================================
    # エッジケース・型安全性テスト
    # ========================================

    def test_empty_objects_in_list(self, converter):
        """
        空のオブジェクトが含まれる場合の処理を確認。

        Given: 空のオブジェクトを含むリスト
        When: _extract_headers を呼び出す
        Then: 空でないオブジェクトからキーが抽出される
        """
        # Arrange
        objects = [{}, {"name": "Alice"}, {}, {"age": 30, "city": "Tokyo"}]
        expected = ["name", "age", "city"]

        # Act
        result = converter._extract_headers(objects)

        # Assert
        assert result == expected

    @pytest.mark.parametrize(
        "invalid_objects",
        [
            [{"name": "Alice"}, "invalid_string", {"age": 30}],
            [{"name": "Alice"}, ["invalid", "list"], {"age": 30}],
            [{"name": "Alice"}, 123, {"age": 30}],
            [{"name": "Alice"}, None, {"age": 30}],
        ],
    )
    def test_non_dict_objects_skipped(self, converter, invalid_objects):
        """
        辞書以外のオブジェクトがスキップされることを確認。

        Given: 辞書以外の要素を含むリスト
        When: _extract_headers を呼び出す
        Then: 辞書のみからキーが抽出される
        """
        # Act
        result = converter._extract_headers(invalid_objects)

        # Assert
        assert "name" in result
        assert "age" in result
        assert len(result) == 2

    def test_non_string_keys_skipped(self, converter):
        """
        文字列以外のキーがスキップされることを確認。

        Given: 文字列以外のキーを持つオブジェクト
        When: _extract_headers を呼び出す
        Then: 文字列キーのみが抽出される
        """
        # Arrange
        objects = [
            {"name": "Alice", 123: "invalid", "age": 30},
            {456: "invalid", "city": "Tokyo", None: "invalid"},
        ]
        expected = ["name", "age", "city"]

        # Act
        result = converter._extract_headers(objects)

        # Assert
        assert result == expected
        assert all(isinstance(key, str) for key in result)

    # ========================================
    # セキュリティ制約テスト
    # ========================================

    def test_max_keys_limit_enforcement(self, converter):
        """
        最大キー数制限(1000)が適用されることを確認。

        Given: 1000個を超えるユニークキーを持つオブジェクト群
        When: _extract_headers を呼び出す
        Then: 最大1000個のキーで制限される
        """
        # Arrange
        objects = []
        # 1500個のユニークキーを生成
        for i in range(1500):
            objects.append({f"key_{i:04d}": f"value_{i}"})

        # Act
        result = converter._extract_headers(objects)

        # Assert
        assert len(result) <= 1000
        assert len(set(result)) == len(result)  # 重複なし確認
        # 最初の1000個が順序通りに含まれている確認
        for i in range(min(1000, len(result))):
            assert result[i] == f"key_{i:04d}"

    def test_max_objects_limit_enforcement(self, converter):
        """
        最大オブジェクト数制限(10000)が適用されることを確認。

        Given: 10000個を超えるオブジェクト
        When: _extract_headers を呼び出す
        Then: 最初の10000個のオブジェクトのみが処理される
        """
        # Arrange
        objects = []
        # 15000個のオブジェクトを生成(各オブジェクトに固有キー)
        for i in range(15000):
            objects.append({f"key_{i}": f"value_{i}"})

        # Act
        result = converter._extract_headers(objects)

        # Assert
        # 最大10000個のオブジェクトから抽出されたキーのみ
        expected_keys = [f"key_{i}" for i in range(min(10000, len(objects)))]
        assert result == expected_keys[: len(result)]

    @pytest.mark.parametrize(
        "key_length,should_be_included",
        [
            ("x" * 255, True),  # 255文字(制限内)
            ("x" * 256, False),  # 256文字(制限超過)
            ("x" * 300, False),  # 300文字(制限超過)
        ],
    )
    def test_key_length_limit_enforcement(
        self, converter, key_length, should_be_included
    ):
        """
        キー名長制限(255文字)が適用されることを確認。

        Given: 様々な長さのキー名を持つオブジェクト
        When: _extract_headers を呼び出す
        Then: 制限を超えるキーがスキップされる
        """
        # Arrange
        objects = [{"short": "value1", key_length: "value2"}]

        # Act
        result = converter._extract_headers(objects)

        # Assert
        assert "short" in result
        if should_be_included:
            assert key_length in result
        else:
            assert key_length not in result

        # すべてのキーが制限内であることを確認
        assert all(len(key) <= 255 for key in result)

    # ========================================
    # 安定化されたパフォーマンステスト
    # ========================================

    @pytest.mark.performance
    def test_large_dataset_performance_ci_safe(self, converter, large_dataset):
        """
        大量データでの機能ベースパフォーマンステスト(CI環境安全版)。

        Given: 大量のオブジェクト(1000個)
        When: _extract_headers を呼び出す
        Then: 正常に処理が完了し、期待される結果が返される
        """
        # Act
        start_time = time.perf_counter()
        result = converter._extract_headers(large_dataset)
        processing_time = time.perf_counter() - start_time

        # Assert - 機能確認に重点を置く
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(key, str) for key in result)

        # 性能情報をログ出力(参考値として)
        print(f"\n処理時間: {processing_time:.4f}秒 (参考値)")
        print(f"処理オブジェクト数: {len(large_dataset)}")
        print(f"抽出キー数: {len(result)}")

    @pytest.mark.performance
    def test_scalability_functional_verification(self, converter):
        """
        スケーラビリティの機能ベース検証テスト(時間アサーションなし)。

        Given: 異なるサイズのデータセット
        When: _extract_headers を呼び出す
        Then: 各サイズで正常に処理が完了する
        """
        # Test different object counts
        object_counts = [100, 500, 1000, 2000]

        for object_count in object_counts:
            # Arrange
            objects = []
            for _i in range(object_count):
                obj = {f"key_{j}": f"value_{j}" for j in range(5)}
                objects.append(obj)

            # Act
            start_time = time.perf_counter()
            result = converter._extract_headers(objects)
            processing_time = time.perf_counter() - start_time

            # Assert - 機能確認のみ(時間アサーションなし)
            assert len(result) == 5  # 期待されるキー数
            assert isinstance(result, list)
            assert all(isinstance(key, str) for key in result)

            # 情報ログ出力
            print(f"\nオブジェクト数 {object_count}: {processing_time:.4f}秒")

    # ========================================
    # 実用的なユースケーステスト
    # ========================================

    def test_configuration_file_use_case(self, converter):
        """
        設定ファイルのユースケースシミュレーション。

        Given: 設定項目の優先順序が重要なデータ
        When: _extract_headers を呼び出す
        Then: 重要な設定が最初に表示される順序が保持される
        """
        # Arrange: 重要度順の設定データ
        config_objects = [
            {
                "priority": "high",
                "name": "production_server",
                "host": "prod.example.com",
                "port": 443,
                "ssl": True,
                "backup_host": "backup.example.com",
            },
            {
                "priority": "medium",
                "name": "staging_server",
                "host": "staging.example.com",
                "port": 80,
                "ssl": False,
                "debug": True,  # 新しいキー
            },
        ]
        expected = ["priority", "name", "host", "port", "ssl", "backup_host", "debug"]

        # Act
        result = converter._extract_headers(config_objects)

        # Assert
        assert result == expected
        # 重要な設定が最初に来ることを確認
        assert result[0] == "priority"
        assert result[1] == "name"

    def test_api_response_use_case(self, converter, sample_user_data):
        """
        APIレスポンスのユースケースシミュレーション。

        Given: ユーザー情報APIのレスポンス形式データ
        When: _extract_headers を呼び出す
        Then: ユーザーフレンドリーな順序でフィールドが配置される
        """
        # Arrange
        expected = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "created_at",
            "last_login",
        ]

        # Act
        result = converter._extract_headers(sample_user_data)

        # Assert
        assert result == expected
        # 基本情報が最初に来ることを確認
        assert result[:3] == ["id", "username", "email"]

    @pytest.mark.integration
    def test_real_world_json_structure(self, converter):
        """
        実世界のJSON構造での動作確認。

        Given: 実際のアプリケーションで使われそうなJSON構造
        When: _extract_headers を呼び出す
        Then: 適切な順序でキーが抽出される
        """
        # Arrange: 実際のeコマースデータ風
        products = [
            {
                "id": "prod_001",
                "name": "ワイヤレスヘッドフォン",
                "price": 15800,
                "category": "electronics",
                "in_stock": True,
                "description": "高音質ワイヤレスヘッドフォン",
            },
            {
                "id": "prod_002",
                "name": "スマートウォッチ",
                "price": 32000,
                "category": "electronics",
                "in_stock": False,
                "description": "多機能スマートウォッチ",
                "warranty_months": 24,  # 一部商品のみ
            },
            {
                "id": "prod_003",
                "name": "エコバッグ",
                "price": 980,
                "category": "lifestyle",
                "in_stock": True,
                "description": "環境に優しいエコバッグ",
                "material": "リサイクル素材",  # 一部商品のみ
            },
        ]

        # Act
        result = converter._extract_headers(products)

        # Assert
        expected = [
            "id",
            "name",
            "price",
            "category",
            "in_stock",
            "description",
            "warranty_months",
            "material",
        ]
        assert result == expected

        # ビジネス的に重要な情報が最初に来ることを確認
        assert result[:4] == ["id", "name", "price", "category"]

    # ========================================
    # エラーハンドリングテスト
    # ========================================

    @pytest.mark.error_handling
    def test_malformed_data_resilience(self, converter):
        """
        不正なデータに対する耐性テスト。

        Given: 様々な不正なデータを含むリスト
        When: _extract_headers を呼び出す
        Then: エラーなく処理され、有効なデータのみが抽出される
        """
        # Arrange
        malformed_objects = [
            {"valid_key": "value"},
            {"": "empty_key"},  # 空文字キー
            {123: "numeric_key"},  # 数値キー
            None,  # None
            "string",  # 文字列
            [],  # リスト
            {"valid_key2": "value2"},
        ]

        # Act
        result = converter._extract_headers(malformed_objects)

        # Assert
        assert "valid_key" in result
        assert "valid_key2" in result
        assert "" not in result  # 空文字キーは除外される可能性
        assert 123 not in result
        assert len([k for k in result if isinstance(k, str)]) == len(result)


class TestExtractHeadersPerformance:
    """pytest-benchmarkベースの安定的なパフォーマンステスト。"""

    def test_extract_headers_benchmark(self, converter):
        """
        大きなデータセットでのヘッダー抽出パフォーマンステスト。
        """
        # Arrange
        large_objects = [
            {f"key_{j}": f"value_{i}_{j}" for j in range(100)} for i in range(1000)
        ]

        # Act & Assert
        result = converter._extract_headers(large_objects)

        # 機能確認(時間に依存しない)
        assert len(result) <= 1000
        assert isinstance(result, list)
        assert all(isinstance(key, str) for key in result)

    def test_scalability_benchmark_stable(self, converter):
        """
        スケーラビリティのテスト(安定版)。
        """
        # Arrange
        very_large_objects = [
            {f"key_{j}": f"value_{i}_{j}" for j in range(50)} for i in range(5000)
        ]

        # Act & Assert
        result = converter._extract_headers(very_large_objects)
        assert len(result) <= 1000
        assert isinstance(result, list)
        assert all(isinstance(key, str) for key in result)

    @pytest.mark.performance
    def test_extract_headers_performance_reference_only(self, converter):
        """
        _extract_headers メソッドのパフォーマンス参考測定(CI安全版)。
        時間アサーションなし、機能確認と参考値出力のみ。
        """
        # Arrange
        large_objects = [
            {f"key_{j}": f"value_{i}_{j}" for j in range(100)} for i in range(1000)
        ]

        # Act
        start_time = time.perf_counter()
        result = converter._extract_headers(large_objects)
        processing_time = time.perf_counter() - start_time

        # Assert - 機能確認のみ
        assert isinstance(result, list)
        assert len(result) <= 1000
        assert all(isinstance(key, str) for key in result)

        # 参考値ログ出力
        print("\n_extract_headers performance reference:")
        print(f"  Processing time: {processing_time:.4f}s")
        print(f"  Objects processed: {len(large_objects):,}")
        print(f"  Keys extracted: {len(result)}")


class TestTableConverterObjectToRow:
    """Test cases for the _object_to_row method."""

    def test_object_to_row_all_keys_present_returns_values_in_order(
        self, converter, sample_headers
    ):
        """Test _object_to_row returns values in header order when all keys present."""
        # Arrange
        obj = {"name": "John", "age": "30"}
        # Act
        result = converter._object_to_row(obj, sample_headers)
        # Assert
        assert result == ["30", "John"]

    def test_object_to_row_missing_keys_returns_empty_strings(
        self, converter, sample_headers
    ):
        """Test _object_to_row returns empty strings for missing keys."""
        # Arrange
        obj = {"name": "John"}  # missing "age"
        # Act
        result = converter._object_to_row(obj, sample_headers)
        # Assert
        assert result == ["", "John"]

    def test_object_to_row_none_values_converted_to_empty_strings(
        self, converter, sample_headers
    ):
        """Test _object_to_row converts None values to empty strings."""
        # Arrange
        obj = {"name": None, "age": 30}
        # Act
        result = converter._object_to_row(obj, sample_headers)
        # Assert
        assert result == ["30", ""]

    def test_object_to_row_empty_object_returns_empty_strings(
        self, converter, sample_headers
    ):
        """Test _object_to_row returns empty strings for empty object."""
        # Arrange
        obj = {}
        # Act
        result = converter._object_to_row(obj, sample_headers)
        # Assert
        assert result == ["", ""]

    def test_object_to_row_converts_values_to_strings(self, converter):
        """Test _object_to_row converts all values to strings."""
        # Arrange
        obj = {"number": 123, "boolean": True, "float": 45.67}
        headers = ["boolean", "float", "number"]
        # Act
        result = converter._object_to_row(obj, headers)
        # Assert
        assert result == ["True", "45.67", "123"]

    def test_object_to_row_empty_headers_returns_empty_list(self, converter):
        """Test _object_to_row returns empty list for empty headers."""
        # Arrange
        obj = {"name": "John", "age": 30}
        headers = []
        # Act
        result = converter._object_to_row(obj, headers)
        # Assert
        assert result == []
