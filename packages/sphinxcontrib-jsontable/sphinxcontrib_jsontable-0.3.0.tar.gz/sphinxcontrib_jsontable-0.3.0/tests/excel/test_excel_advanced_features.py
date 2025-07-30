"""
Excel Data Loader 高度機能完全テストスイート

未カバーの高度機能をテストして80%カバレッジ達成を目指す
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from sphinxcontrib.jsontable.excel_data_loader import ExcelDataLoader


class TestAdvancedExcelFeatures:
    """高度なExcel機能のテスト."""

    def setup_method(self):
        """テスト前の準備."""
        self.base_path = Path("/tmp")
        self.loader = ExcelDataLoader(self.base_path)

    def create_mock_excel_data(self, rows=10, cols=5):
        """モックExcelデータを作成."""
        data = []
        for i in range(rows):
            row = []
            for j in range(cols):
                if i == 0:  # ヘッダー行
                    row.append(f"Header{j + 1}")
                else:
                    row.append(f"R{i}C{j + 1}")
            data.append(row)
        return data


class TestSkipRowsAndHeaderCombination:
    """スキップ行とヘッダー組み合わせ機能のテスト."""

    def setup_method(self):
        """テスト前の準備."""
        self.base_path = Path("/tmp")
        self.loader = ExcelDataLoader(self.base_path)

    def test_load_from_excel_with_skip_rows_and_header_basic(self):
        """基本的なスキップ行+ヘッダー読み込みテスト."""
        with (
            patch.object(self.loader, "_validate_excel_file"),
            patch.object(self.loader, "load_from_excel_with_range") as mock_load,
        ):
            # モックデータ: 5行のデータ
            mock_data = [
                ["Skip1", "Skip1"],  # 行0 - スキップ対象
                ["Header1", "Header2"],  # 行1 - ヘッダー
                ["Data1", "Data2"],  # 行2 - データ
                ["Skip2", "Skip2"],  # 行3 - スキップ対象
                ["Data3", "Data4"],  # 行4 - データ
            ]

            mock_load.return_value = {"data": mock_data, "sheet_name": "Sheet1"}

            # テスト実行: 行0,3をスキップ、行1をヘッダーとして使用
            result = self.loader.load_from_excel_with_skip_rows_and_header(
                "test.xlsx", "A1:B5", "0,3", 1
            )

            # 結果検証
            assert result["has_header"] is True
            assert result["headers"] == ["header1", "header2"]
            assert len(result["data"]) == 2  # データ行2つ
            assert result["data"][0] == ["Data1", "Data2"]
            assert result["data"][1] == ["Data3", "Data4"]
            assert result["skip_rows"] == "0,3"
            assert result["header_row"] == 1
            assert result["skipped_row_count"] == 2

    def test_skip_rows_and_header_with_adjusted_header_row(self):
        """スキップ後のヘッダー行調整テスト."""
        with (
            patch.object(self.loader, "_validate_excel_file"),
            patch.object(self.loader, "load_from_excel_with_range") as mock_load,
        ):
            mock_data = [
                ["Skip1", "Skip2"],  # 行0 - スキップ
                ["Skip2", "Skip2"],  # 行1 - スキップ
                ["Header1", "Header2"],  # 行2 - ヘッダー(調整後は行0)
                ["Data1", "Data2"],  # 行3 - データ
            ]

            mock_load.return_value = {"data": mock_data, "sheet_name": "Sheet1"}

            # 行0,1をスキップ、行2をヘッダーとして使用
            result = self.loader.load_from_excel_with_skip_rows_and_header(
                "test.xlsx", "A1:B4", "0,1", 2
            )

            assert result["adjusted_header_row"] == 0  # スキップ後は先頭行
            assert result["headers"] == ["header1", "header2"]
            assert len(result["data"]) == 1

    def test_skip_rows_and_header_invalid_header_after_skip(self):
        """スキップ後にヘッダー行が無効になる場合のテスト."""
        with (
            patch.object(self.loader, "_validate_excel_file"),
            patch.object(self.loader, "load_from_excel_with_range") as mock_load,
        ):
            mock_data = [
                ["Data1", "Data2"],  # 行0 - スキップ
                ["Data3", "Data4"],  # 行1 - スキップ
            ]

            mock_load.return_value = {"data": mock_data, "sheet_name": "Sheet1"}

            # 行0,1をスキップ、行1をヘッダーとして使用すると調整後に無効
            with pytest.raises(
                ValueError, match="Header row .* is specified to be skipped"
            ):
                self.loader.load_from_excel_with_skip_rows_and_header(
                    "test.xlsx", "A1:B2", "0,1", 1
                )

    def test_skip_rows_and_header_no_header_mode(self):
        """ヘッダーなしモードでのスキップ行処理テスト."""
        with (
            patch.object(self.loader, "_validate_excel_file"),
            patch.object(self.loader, "load_from_excel_with_range") as mock_load,
        ):
            mock_data = [
                ["Skip", "Skip"],  # 行0 - スキップ
                ["Data1", "Data2"],  # 行1 - データ
                ["Data3", "Data4"],  # 行2 - データ
            ]

            mock_load.return_value = {"data": mock_data, "sheet_name": "Sheet1"}

            # ヘッダー行を-1に設定(ヘッダーなし)
            result = self.loader.load_from_excel_with_skip_rows_and_header(
                "test.xlsx", "A1:B3", "0", -1
            )

            assert result["has_header"] is False
            assert result["headers"] == []
            assert len(result["data"]) == 2
            assert result["adjusted_header_row"] == -1


class TestDetectRangeFeatures:
    """自動範囲検出機能のテスト."""

    def setup_method(self):
        """テスト前の準備."""
        self.base_path = Path("/tmp")
        self.loader = ExcelDataLoader(self.base_path)

    def test_load_from_excel_with_detect_range_auto_mode(self):
        """autoモードでの範囲自動検出テスト."""
        with (
            patch.object(self.loader, "_validate_excel_file"),
            patch.object(self.loader, "load_from_excel") as mock_load,
            patch.object(self.loader, "_detect_auto_range") as mock_detect,
            patch.object(self.loader, "_extract_detected_range") as mock_extract,
        ):
            # モックデータの設定
            mock_load.return_value = {
                "data": [["H1", "H2"], ["D1", "D2"]],
                "sheet_name": "Sheet1",
            }
            mock_detect.return_value = "A1:B2"
            mock_extract.return_value = [["H1", "H2"], ["D1", "D2"]]

            result = self.loader.load_from_excel_with_detect_range(
                "test.xlsx", detect_mode="auto"
            )

            assert result["detected_range"] == "A1:B2"
            assert result["detect_mode"] == "auto"
            mock_detect.assert_called_once()
            mock_extract.assert_called_once()

    def test_load_from_excel_with_detect_range_smart_mode(self):
        """smartモードでの範囲自動検出テスト."""
        with (
            patch.object(self.loader, "_validate_excel_file"),
            patch.object(self.loader, "load_from_excel") as mock_load,
            patch.object(self.loader, "_detect_multiple_data_blocks") as mock_blocks,
            patch.object(self.loader, "_extract_detected_range") as mock_extract,
        ):
            # モックデータの設定
            mock_load.return_value = {
                "data": [["H1", "H2"], ["D1", "D2"]],
                "sheet_name": "Sheet1",
            }

            # 複数ブロックを模擬
            mock_blocks.return_value = [
                {
                    "min_row": 0,
                    "max_row": 1,
                    "min_col": 0,
                    "max_col": 1,
                    "total_cells": 4,
                },
                {
                    "min_row": 3,
                    "max_row": 4,
                    "min_col": 0,
                    "max_col": 1,
                    "total_cells": 2,
                },
            ]
            mock_extract.return_value = [["H1", "H2"], ["D1", "D2"]]

            result = self.loader.load_from_excel_with_detect_range(
                "test.xlsx", detect_mode="smart"
            )

            assert result["detect_mode"] == "smart"
            assert "detected_range" in result
            mock_blocks.assert_called_once()

    def test_load_from_excel_with_detect_range_smart_mode_fallback(self):
        """smartモードで検出失敗時のフォールバックテスト."""
        with (
            patch.object(self.loader, "_validate_excel_file"),
            patch.object(self.loader, "load_from_excel") as mock_load,
            patch.object(self.loader, "_detect_multiple_data_blocks") as mock_blocks,
            patch.object(self.loader, "_detect_auto_range") as mock_auto,
            patch.object(self.loader, "_extract_detected_range") as mock_extract,
        ):
            mock_load.return_value = {
                "data": [["H1", "H2"], ["D1", "D2"]],
                "sheet_name": "Sheet1",
            }

            # ブロック検出失敗を模擬
            mock_blocks.return_value = []
            mock_auto.return_value = "A1:B2"
            mock_extract.return_value = [["H1", "H2"], ["D1", "D2"]]

            result = self.loader.load_from_excel_with_detect_range(
                "test.xlsx", detect_mode="smart"
            )

            # フォールバックが動作することを確認
            mock_auto.assert_called_once()
            assert result["detected_range"] == "A1:B2"

    def test_load_from_excel_with_detect_range_manual_mode(self):
        """manualモードでの範囲検出テスト."""
        with (
            patch.object(self.loader, "_validate_excel_file"),
            patch.object(self.loader, "load_from_excel") as mock_load,
            patch.object(self.loader, "_detect_manual_range") as mock_manual,
            patch.object(self.loader, "_extract_detected_range") as mock_extract,
        ):
            mock_load.return_value = {
                "data": [["H1", "H2"], ["D1", "D2"]],
                "sheet_name": "Sheet1",
            }
            mock_manual.return_value = "A1:B2"
            mock_extract.return_value = [["H1", "H2"], ["D1", "D2"]]

            result = self.loader.load_from_excel_with_detect_range(
                "test.xlsx", detect_mode="manual", range_hint="A1:B2"
            )

            assert result["detect_mode"] == "manual"
            # manual modeではrange_hintを直接使用するため、_detect_manual_rangeは呼び出されない
            # mock_manual.assert_called_once()

    def test_load_from_excel_with_detect_range_invalid_mode(self):
        """無効な検出モードでのエラーテスト."""
        with patch.object(self.loader, "_validate_excel_file"):
            with pytest.raises(ValueError, match="Invalid detect mode"):
                self.loader.load_from_excel_with_detect_range(
                    "test.xlsx", detect_mode="invalid_mode"
                )


class TestMergedCellsWithRange:
    """結合セル処理と範囲指定の組み合わせテスト."""

    def setup_method(self):
        """テスト前の準備."""
        self.base_path = Path("/tmp")
        self.loader = ExcelDataLoader(self.base_path)

    def test_load_from_excel_with_merge_cells_and_range_expand_mode(self):
        """expandモードでの結合セル処理テスト."""
        with (
            patch.object(self.loader, "_validate_excel_file"),
            patch.object(self.loader, "load_from_excel_with_range") as mock_load,
            patch.object(self.loader, "detect_merged_cells") as mock_detect,
            patch.object(self.loader, "_filter_merged_cells_in_range") as mock_filter,
            patch.object(self.loader, "_apply_merge_cell_processing") as mock_process,
        ):
            # モックデータの設定
            mock_load.return_value = {
                "data": [["A1", ""], ["A2", "B2"]],
                "sheet_name": "Sheet1",
                "has_header": False,
                "headers": [],
            }

            mock_detect.return_value = {
                "has_merged_cells": True,
                "merged_ranges": [{"range": "A1:B1"}],
            }
            mock_filter.return_value = [{"range": "A1:B1"}]
            mock_process.return_value = [["A1", "A1"], ["A2", "B2"]]

            result = self.loader.load_from_excel_with_merge_cells_and_range(
                "test.xlsx", "A1:B2", merge_mode="expand"
            )

            assert result["merge_mode"] == "expand"
            assert "merged_cells_info" in result
            mock_process.assert_called_once()

    def test_load_from_excel_with_merged_cells_invalid_mode(self):
        """無効なマージモードでのエラーテスト."""
        with patch.object(self.loader, "_validate_excel_file"):
            with pytest.raises((Exception, ValueError)):  # MergedCellsError
                self.loader.load_from_excel_with_merge_cells_and_range(
                    "test.xlsx", "A1:B2", merge_mode="invalid_mode"
                )

    def test_merged_cells_with_header_row_processing(self):
        """ヘッダー行付きでの結合セル処理テスト."""
        with (
            patch.object(self.loader, "_validate_excel_file"),
            patch.object(self.loader, "load_from_excel_with_range") as mock_load,
            patch.object(self.loader, "detect_merged_cells") as mock_detect,
            patch.object(self.loader, "_filter_merged_cells_in_range") as mock_filter,
            patch.object(self.loader, "_apply_merge_cell_processing") as mock_process,
        ):
            mock_load.return_value = {
                "data": [["Header1", "Header2"], ["Data1", ""]],
                "sheet_name": "Sheet1",
                "has_header": True,
                "headers": ["Header1", "Header2"],
            }

            mock_detect.return_value = {"has_merged_cells": False, "merged_ranges": []}
            mock_filter.return_value = []
            mock_process.return_value = [["Header1", "Header2"], ["Data1", ""]]

            result = self.loader.load_from_excel_with_merge_cells_and_range(
                "test.xlsx", "A1:B2", merge_mode="expand", header_row=0
            )

            assert result["has_header"] is True
            assert result["headers"] == ["Header1", "Header2"]
