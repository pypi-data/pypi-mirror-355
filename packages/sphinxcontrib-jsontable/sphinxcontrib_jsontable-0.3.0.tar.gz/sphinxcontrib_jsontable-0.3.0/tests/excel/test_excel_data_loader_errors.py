"""Excel Data Loader エラーハンドリング機能のテスト."""

import os
import tempfile
from datetime import datetime

import pandas as pd
import pytest

# Excel対応がある場合のみテストを実行
try:
    from sphinxcontrib.jsontable.excel_data_loader import (
        EnhancedExcelError,
        ExcelDataLoader,
        RangeSpecificationError,
        SkipRowsError,
    )

    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


class TestExcelDataLoaderErrors:
    """ExcelDataLoaderのエラーハンドリング機能のテスト."""

    def setup_method(self):
        """各テストメソッドの前に実行される。"""
        self.temp_dir = tempfile.mkdtemp()
        self.loader = ExcelDataLoader(self.temp_dir)

    def teardown_method(self):
        """各テストメソッドの後に実行される。"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_enhanced_excel_error_creation(self):
        """EnhancedExcelError基本機能のテスト。"""
        # 基本的なエラー作成
        error = EnhancedExcelError("Test error message")
        assert str(error) == "Test error message"
        assert error.error_code == "GENERIC_ERROR"
        assert error.user_message == "Test error message"
        assert error.technical_message == "Test error message"
        assert error.recovery_suggestions == []
        assert error.error_context == {}
        assert error.debug_info == {}
        assert isinstance(error.timestamp, datetime)

    def test_enhanced_excel_error_with_details(self):
        """詳細情報付きEnhancedExcelErrorのテスト。"""
        recovery_suggestions = ["Check file path", "Verify permissions"]
        error_context = {"file_path": "/test/path.xlsx", "operation": "read"}
        debug_info = {"line_number": 123, "method": "load_excel"}

        error = EnhancedExcelError(
            message="Detailed error message",
            error_code="FILE_READ_ERROR",
            user_message="ファイルの読み込みに失敗しました",
            technical_message="Permission denied when accessing file",
            recovery_suggestions=recovery_suggestions,
            error_context=error_context,
            debug_info=debug_info,
        )

        assert error.error_code == "FILE_READ_ERROR"
        assert error.user_message == "ファイルの読み込みに失敗しました"
        assert error.technical_message == "Permission denied when accessing file"
        assert error.recovery_suggestions == recovery_suggestions
        assert error.error_context == error_context
        assert error.debug_info == debug_info

        # error_details確認
        details = error.error_details
        assert details["error_type"] == "EnhancedExcelError"
        assert details["error_code"] == "FILE_READ_ERROR"
        assert details["user_friendly_message"] == "ファイルの読み込みに失敗しました"
        assert details["technical_details"] == "Permission denied when accessing file"
        assert details["recovery_suggestions"] == recovery_suggestions
        assert details["debug_info"] == debug_info

    def test_enhanced_excel_error_localized_messages(self):
        """多言語対応メッセージのテスト。"""
        error = EnhancedExcelError(
            message="English error message",
            user_message="日本語エラーメッセージ",
        )

        # 日本語メッセージ
        assert error.get_message("ja") == "日本語エラーメッセージ"
        assert error.localized_message == "日本語エラーメッセージ"

        # 英語メッセージ
        assert error.get_message("en") == "English error message"

        # 存在しない言語の場合は英語にフォールバック
        assert error.get_message("fr") == "English error message"

    def test_range_specification_error(self):
        """RangeSpecificationErrorのテスト。"""
        range_spec = "A1:Z100"
        error = RangeSpecificationError("Invalid range", range_spec)

        assert str(error) == "Invalid range"
        assert error.invalid_spec == range_spec
        assert isinstance(error, ValueError)

    def test_skip_rows_error(self):
        """SkipRowsErrorのテスト。"""
        skip_rows_spec = "0,1,invalid"
        error = SkipRowsError("Invalid skip rows format", skip_rows_spec)

        assert str(error) == "Invalid skip rows format"
        assert error.invalid_spec == skip_rows_spec
        assert isinstance(error, ValueError)

    def test_excel_data_loader_initialization_errors(self):
        """ExcelDataLoader初期化時のエラーテスト。"""
        # 存在しないディレクトリでの初期化
        nonexistent_dir = "/nonexistent/directory/path"
        loader = ExcelDataLoader(nonexistent_dir)
        # 初期化は成功するが、パスは設定される
        from pathlib import Path

        assert loader.base_path == Path(nonexistent_dir)

    def test_path_validation_methods(self):
        """パス検証メソッドのテスト。"""
        # 正常なパス
        from pathlib import Path

        safe_path = str(Path(self.temp_dir) / "test.xlsx")
        assert self.loader.is_safe_path(safe_path) is True

        # パストラバーサル攻撃のテスト
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
        ]

        for dangerous_path in dangerous_paths:
            assert self.loader.is_safe_path(dangerous_path) is False

    def test_file_validation_errors(self):
        """ファイル検証エラーのテスト。"""
        # 存在しないファイル
        from pathlib import Path

        nonexistent_file = str(Path(self.temp_dir) / "nonexistent.xlsx")
        with pytest.raises(FileNotFoundError):
            self.loader.validate_excel_file(nonexistent_file)

        # 不正な拡張子
        invalid_extensions = [".txt", ".csv", ".json", ".pdf", ".exe"]
        for ext in invalid_extensions:
            from pathlib import Path

            invalid_file = str(Path(self.temp_dir) / f"test{ext}")
            with open(invalid_file, "w") as f:
                f.write("test content")

            with pytest.raises(ValueError, match="Unsupported file format"):
                self.loader.validate_excel_file(invalid_file)

    def test_sheet_detection_edge_cases(self):
        """シート検出のエッジケースのテスト。"""
        # 空のExcelファイルを作成
        empty_file = os.path.join(self.temp_dir, "empty.xlsx")
        with pd.ExcelWriter(empty_file, engine="openpyxl") as writer:
            pd.DataFrame().to_excel(writer, index=False)

        # 空ファイルでのシート検出
        sheet_name = self.loader.basic_sheet_detection(empty_file)
        assert sheet_name == "Sheet1"  # デフォルトシート名

    def test_header_detection_edge_cases(self):
        """ヘッダー検出のエッジケースのテスト。"""
        # 完全に空のDataFrame
        empty_df = pd.DataFrame()
        assert self.loader.header_detection(empty_df) is False

        # 1行のみのDataFrame
        single_row_df = pd.DataFrame([["Name", "Age", "City"]])
        # 単一行の場合、ヘッダー検出結果は実装に依存
        result = self.loader.header_detection(single_row_df)
        assert isinstance(result, bool)

        # 全て同じ型のDataFrame
        numeric_df = pd.DataFrame([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        assert self.loader.header_detection(numeric_df) is False

        # 混合型だがヘッダーらしくないDataFrame
        mixed_df = pd.DataFrame([[1, "text", 3.14], [2, "more", 2.71]])
        result = self.loader.header_detection(mixed_df)
        # 型の多様性があるため、ヘッダーの可能性がある
        assert isinstance(result, bool)

    def test_data_type_conversion_edge_cases(self):
        """データ型変換のエッジケースのテスト。"""
        # None値を含むDataFrame
        df_with_none = pd.DataFrame(
            [["Alice", None, 25.5], [None, "Bob", None], ["Charlie", "Engineer", 30]]
        )

        result = self.loader.data_type_conversion(df_with_none)
        assert result[0] == ["Alice", "", "25.5"]
        assert result[1] == ["", "Bob", ""]
        assert result[2] == ["Charlie", "Engineer", "30"]

        # 異なる数値型を含むDataFrame
        df_numeric = pd.DataFrame([[1, 2.0, 3.14159, True], [100, 200.5, 0.0, False]])

        result = self.loader.data_type_conversion(df_numeric)
        assert result[0] == ["1", "2", "3.14159", "True"]
        assert result[1] == ["100", "200.5", "0", "False"]

    def test_range_specification_validation(self):
        """範囲指定バリデーションのテスト。"""
        # 無効な範囲指定でのエラー発生テスト
        invalid_ranges = [
            "invalid",
            "A1:Z",
            "1:A1",
            "",
            "A1:A0",  # 逆順
            "Z1:A1",  # 逆順
        ]

        test_data = [["Name", "Age"], ["Alice", "25"]]
        df = pd.DataFrame(test_data)
        excel_path = os.path.join(self.temp_dir, "test_range.xlsx")
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)

        for invalid_range in invalid_ranges:
            with pytest.raises((ValueError, RangeSpecificationError)):
                try:
                    self.loader.load_from_excel_with_range(excel_path, invalid_range)
                except Exception as e:
                    # デバッグ情報
                    print(f"Range: {invalid_range}, Error: {type(e).__name__}: {e}")
                    raise

    def test_skip_rows_validation(self):
        """Skip Rows指定バリデーションのテスト。"""
        # 無効なSkip Rows指定でのエラー発生テスト
        invalid_skip_specs = [
            "invalid",
            "a,b,c",
            "-1",
            "1,2,,3",  # 空の要素
            "1-",  # 不完全な範囲
            "-5",  # 不完全な範囲
            "1--5",  # 無効な範囲記法
        ]

        test_data = [["Name", "Age"], ["Alice", "25"], ["Bob", "30"]]
        df = pd.DataFrame(test_data)
        excel_path = os.path.join(self.temp_dir, "test_skip.xlsx")
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)

        for invalid_skip in invalid_skip_specs:
            with pytest.raises((ValueError, SkipRowsError)):
                try:
                    self.loader.load_from_excel_with_skip_rows(excel_path, invalid_skip)
                except Exception as e:
                    # デバッグ情報
                    print(f"Skip spec: {invalid_skip}, Error: {type(e).__name__}: {e}")
                    raise
