"""
Excel Data Loader エラーハンドリング完全テストスイート

未カバーのエラーハンドリング機能をテストして80%カバレッジ達成を目指す
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sphinxcontrib.jsontable.excel_data_loader import (
    EnhancedExcelError,
    ExcelDataLoader,
    ExcelFileNotFoundError,
    MergedCellsError,
    RangeSpecificationError,
    SkipRowsError,
)


class TestExcelFileNotFoundError:
    """ExcelFileNotFoundErrorクラスのテスト."""

    def test_excel_file_not_found_error_creation(self):
        """ExcelFileNotFoundErrorの作成とメッセージ確認."""
        file_path = "/non/existent/file.xlsx"
        error = ExcelFileNotFoundError(file_path)

        assert error.error_code == "FILE_NOT_FOUND"
        assert file_path in error.user_message
        assert "ファイルが見つかりません" in error.user_message
        assert "ファイルパスが正しいか" in error.user_message

        # 技術的メッセージの確認
        assert file_path in error.technical_message
        assert "File not found" in error.technical_message

        # 復旧提案の確認
        assert len(error.recovery_suggestions) >= 3
        assert any(
            "ファイルパス" in suggestion for suggestion in error.recovery_suggestions
        )

    def test_excel_file_not_found_error_inheritance(self):
        """ExcelFileNotFoundErrorの継承関係確認."""
        error = ExcelFileNotFoundError("/test/path.xlsx")
        assert isinstance(error, EnhancedExcelError)
        assert isinstance(error, Exception)


class TestRangeSpecificationError:
    """RangeSpecificationErrorクラスのテスト."""

    def test_range_specification_error_creation(self):
        """RangeSpecificationErrorの作成とメッセージ確認."""
        message = "Invalid range specification: INVALID:RANGE"
        invalid_range = "INVALID:RANGE"
        error = RangeSpecificationError(message, invalid_spec=invalid_range)

        assert invalid_range in str(error)
        assert error.invalid_spec == invalid_range

    def test_range_specification_error_with_details(self):
        """詳細情報付きRangeSpecificationErrorのテスト."""
        message = "Invalid range specification: Z999:AA1000"
        invalid_range = "Z999:AA1000"
        error = RangeSpecificationError(message, invalid_spec=invalid_range)

        assert invalid_range in str(error)
        assert error.invalid_spec == invalid_range


class TestSkipRowsError:
    """SkipRowsErrorクラスのテスト."""

    def test_skip_rows_error_creation(self):
        """SkipRowsErrorの作成とメッセージ確認."""
        message = "Invalid skip rows specification: invalid-skip-spec"
        skip_spec = "invalid-skip-spec"
        error = SkipRowsError(message, invalid_spec=skip_spec)

        assert skip_spec in str(error)
        assert error.invalid_spec == skip_spec

    def test_skip_rows_error_with_multiple_issues(self):
        """複数問題を含むSkipRowsErrorのテスト."""
        message = "Invalid skip rows specification: 1,2,invalid,3"
        skip_spec = "1,2,invalid,3"
        error = SkipRowsError(message, invalid_spec=skip_spec)

        assert skip_spec in str(error)
        assert error.invalid_spec == skip_spec


class TestMergedCellsError:
    """MergedCellsErrorクラスのテスト."""

    def test_merged_cells_error_creation(self):
        """MergedCellsErrorの作成とメッセージ確認."""
        message = "Invalid merge mode: invalid_mode"
        error = MergedCellsError(message, invalid_spec="invalid_mode")

        assert "invalid_mode" in str(error)
        assert error.invalid_spec == "invalid_mode"

    def test_merged_cells_error_with_cell_info(self):
        """セル情報付きMergedCellsErrorのテスト."""
        message = "Merge processing failed for range A1:B2"
        cell_range = "A1:B2"
        error = MergedCellsError(message, invalid_spec=cell_range)

        assert "A1:B2" in str(error)
        assert error.invalid_spec == cell_range


class TestExcelDataLoaderErrorHandling:
    """ExcelDataLoaderクラスのエラーハンドリングテスト."""

    def setup_method(self):
        """テスト前の準備."""
        self.base_path = Path("/tmp")
        self.loader = ExcelDataLoader(self.base_path)

    def test_load_non_existent_file_raises_file_not_found_error(self):
        """存在しないファイルの読み込みでFileNotFoundErrorが発生することをテスト."""
        non_existent_file = self.base_path / "non_existent_file.xlsx"

        # ファイルが存在しないことを確認
        with pytest.raises(FileNotFoundError) as exc_info:
            self.loader.load_from_excel(str(non_existent_file))

        error = exc_info.value
        assert str(non_existent_file) in str(error)

    def test_invalid_range_specification_raises_range_error(self):
        """無効な範囲指定でRangeSpecificationErrorが発生することをテスト."""
        with (
            patch.object(self.loader, "validate_excel_file"),
            patch("pandas.read_excel", return_value=MagicMock()),
        ):
            invalid_ranges = [
                "INVALID:RANGE",
                "A999:Z1",  # 逆順範囲
                "ZZZ999:AAA1000",  # 無効なセル参照
            ]

            valid_file = self.base_path / "test.xlsx"
            for invalid_range in invalid_ranges:
                with pytest.raises(RangeSpecificationError):
                    self.loader.load_from_excel_with_range(
                        str(valid_file), invalid_range
                    )

    def test_invalid_skip_rows_specification_raises_skip_rows_error(self):
        """無効なスキップ行指定でSkipRowsErrorが発生することをテスト."""
        with (
            patch.object(self.loader, "validate_excel_file"),
            patch.object(self.loader, "load_from_excel_with_range") as mock_load,
        ):
            # モックデータの設定
            mock_load.return_value = {
                "data": [["H1", "H2"], ["R1C1", "R1C2"], ["R2C1", "R2C2"]],
                "sheet_name": "Sheet1",
            }

            invalid_skip_specs = [
                "invalid-format",
                "1,2,invalid,3",
                "-1,0,1",  # 負の値
                "1.5,2.5",  # 小数点
            ]

            valid_file = self.base_path / "test.xlsx"
            for invalid_spec in invalid_skip_specs:
                with pytest.raises((SkipRowsError, TypeError, ValueError)):
                    self.loader.load_from_excel_with_skip_rows_and_header(
                        str(valid_file), "A1:B3", invalid_spec, 0
                    )

    def test_invalid_merge_mode_raises_merged_cell_error(self):
        """無効なマージモードでMergedCellsErrorが発生することをテスト."""
        with (
            patch.object(self.loader, "validate_excel_file"),
            patch.object(self.loader, "load_from_excel_with_range") as mock_load,
        ):
            # モックデータの設定
            mock_load.return_value = {
                "data": [["A1", "B1"], ["A2", "B2"]],
                "sheet_name": "Sheet1",
            }

            invalid_merge_modes = [
                "invalid_mode",
                "expand_wrong",
                "merge_incorrect",
            ]

            valid_file = self.base_path / "test.xlsx"
            for invalid_mode in invalid_merge_modes:
                with pytest.raises((MergedCellsError, ValueError)):
                    self.loader.load_from_excel_with_merge_cells(
                        str(valid_file), merge_mode=invalid_mode
                    )

    def test_error_context_preservation(self):
        """エラーコンテキストが適切に保持されることをテスト."""
        file_path = self.base_path / "test_context.xlsx"

        with pytest.raises(FileNotFoundError) as exc_info:
            self.loader.load_from_excel(str(file_path))

        error = exc_info.value

        # ファイルパス情報が保持されていることを確認
        assert str(file_path) in str(error)

    def test_error_recovery_suggestions_accessibility(self):
        """エラー復旧提案が適切にアクセス可能であることをテスト."""
        error = ExcelFileNotFoundError("/test/file.xlsx")

        # 復旧提案がリストであることを確認
        assert isinstance(error.recovery_suggestions, list)
        assert len(error.recovery_suggestions) > 0

        # 各提案が文字列であることを確認
        for suggestion in error.recovery_suggestions:
            assert isinstance(suggestion, str)
            assert len(suggestion) > 0

    def test_enhanced_error_message_formatting(self):
        """拡張エラーメッセージの適切なフォーマットを確認."""
        test_path = "/test/path/file.xlsx"
        error = ExcelFileNotFoundError(test_path)

        # ユーザーメッセージの構造確認
        user_msg = error.user_message
        assert "ファイルが見つかりません" in user_msg
        assert test_path in user_msg
        assert "確認してください" in user_msg
        assert "1." in user_msg  # 箇条書きの確認
        assert "2." in user_msg
        assert "3." in user_msg
