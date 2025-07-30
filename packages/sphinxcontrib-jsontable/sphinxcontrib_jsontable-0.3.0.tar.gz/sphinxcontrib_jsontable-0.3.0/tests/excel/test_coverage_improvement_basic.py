"""
Coverage Improvement Basic Tests

実際に動作する基本的なテストでカバレッジ80%達成を目指す
"""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from sphinxcontrib.jsontable.excel_data_loader import ExcelDataLoader


class TestBasicExcelDataLoader:
    """基本的なExcelDataLoader機能のテスト."""

    def setup_method(self):
        """テスト前の準備."""
        # 一時ディレクトリを作成
        self.temp_dir = Path(tempfile.mkdtemp())
        self.loader = ExcelDataLoader(self.temp_dir)

    def teardown_method(self):
        """テスト後のクリーンアップ."""
        # 一時ディレクトリを削除
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_excel_file(self, filename: str, data: list[list]) -> Path:
        """テスト用Excelファイルを作成."""
        file_path = self.temp_dir / filename
        df = pd.DataFrame(data)
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, header=False)
        return file_path

    def test_basic_excel_loading(self):
        """基本的なExcel読み込みテスト."""
        # テストデータ作成
        test_data = [
            ["Name", "Age", "City"],
            ["Alice", 25, "Tokyo"],
            ["Bob", 30, "Osaka"],
        ]
        excel_file = self.create_test_excel_file("test_basic.xlsx", test_data)

        # 読み込みテスト
        result = self.loader.load_from_excel(str(excel_file))

        # 結果検証
        assert "data" in result
        assert "sheet_name" in result
        assert len(result["data"]) == 2  # データ行のみ

    def test_excel_file_validation(self):
        """Excelファイル検証のテスト."""
        # 存在するファイル
        test_data = [["A", "B"], ["1", "2"]]
        excel_file = self.create_test_excel_file("test_validation.xlsx", test_data)

        # 検証テスト(例外が発生しないことを確認)
        self.loader.validate_excel_file(str(excel_file))

    def test_excel_file_validation_non_existent(self):
        """存在しないファイルの検証テスト."""
        non_existent = self.temp_dir / "non_existent.xlsx"

        with pytest.raises(FileNotFoundError):
            self.loader.validate_excel_file(str(non_existent))

    def test_is_safe_path_valid(self):
        """セーフパス判定(有効パス)のテスト."""
        safe_file = self.temp_dir / "safe_file.xlsx"
        result = self.loader.is_safe_path(str(safe_file))
        assert result is True

    def test_is_safe_path_invalid(self):
        """セーフパス判定(無効パス)のテスト."""
        unsafe_path = "/etc/passwd"
        result = self.loader.is_safe_path(unsafe_path)
        assert result is False

    def test_excel_with_sheet_name(self):
        """シート名指定でのExcel読み込みテスト."""
        test_data = [["Col1", "Col2"], ["Val1", "Val2"]]
        excel_file = self.create_test_excel_file("test_sheet.xlsx", test_data)

        result = self.loader.load_from_excel(str(excel_file), sheet_name="Sheet1")

        assert result["sheet_name"] == "Sheet1"
        assert len(result["data"]) == 2

    def test_parse_range_specification_basic(self):
        """基本的な範囲指定パースのテスト."""
        range_spec = "A1:C3"
        result = self.loader._parse_range_specification(range_spec)

        assert result["start_row"] == 0  # 0ベース
        assert result["end_row"] == 2
        assert result["start_col"] == 0
        assert result["end_col"] == 2

    def test_parse_range_specification_single_cell(self):
        """単一セル範囲指定のテスト."""
        range_spec = "B2"
        result = self.loader._parse_range_specification(range_spec)

        assert result["start_row"] == 1
        assert result["end_row"] == 1
        assert result["start_col"] == 1
        assert result["end_col"] == 1

    def test_column_letter_to_number(self):
        """列文字から番号への変換テスト."""
        assert self.loader._column_letter_to_number("A") == 0
        assert self.loader._column_letter_to_number("B") == 1
        assert self.loader._column_letter_to_number("Z") == 25
        assert self.loader._column_letter_to_number("AA") == 26

    def test_number_to_column_letter(self):
        """番号から列文字への変換テスト."""
        assert self.loader._number_to_column_letter(0) == "A"
        assert self.loader._number_to_column_letter(1) == "B"
        assert self.loader._number_to_column_letter(25) == "Z"
        assert self.loader._number_to_column_letter(26) == "AA"

    def test_validate_range_bounds(self):
        """範囲境界の検証テスト."""
        # 有効な範囲
        self.loader._validate_range_bounds(0, 2, 0, 2)  # A1:C3

        # 無効な範囲(例外が発生することを確認)
        with pytest.raises(ValueError):
            self.loader._validate_range_bounds(2, 0, 0, 2)  # 逆順

    def test_extract_range_basic(self):
        """基本的な範囲抽出テスト."""
        test_data = [["A1", "B1", "C1"], ["A2", "B2", "C2"], ["A3", "B3", "C3"]]

        range_info = {"start_row": 0, "end_row": 1, "start_col": 1, "end_col": 2}

        result = self.loader._extract_range(test_data, range_info)

        assert result == [["B1", "C1"], ["B2", "C2"]]

    def test_normalize_header_names(self):
        """ヘッダー名正規化のテスト."""
        headers = ["Column 1", "column_2", "COLUMN-3", ""]
        result = self.loader._normalize_header_names(headers)

        assert "column_1" in result
        assert "column_2" in result
        assert "column_3" in result
        assert "column_4" in result  # 空の場合のデフォルト

    def test_is_likely_header_statistical(self):
        """統計的ヘッダー判定のテスト."""
        # ヘッダーらしい行
        header_row = ["Name", "Age", "City", "Country"]
        assert self.loader._is_likely_header_statistical(header_row) is True

        # データらしい行
        data_row = ["Alice", "25", "Tokyo", "Japan"]
        assert self.loader._is_likely_header_statistical(data_row) is False

    def test_contains_header_keywords(self):
        """ヘッダーキーワード判定のテスト."""
        # 英語キーワード
        header_en = ["ID", "Name", "Date", "Count"]
        assert self.loader._contains_header_keywords(header_en) is True

        # 日本語キーワード
        header_jp = ["番号", "名前", "日付", "件数"]
        assert self.loader._contains_header_keywords(header_jp) is True

        # キーワードなし
        no_keywords = ["Apple", "Banana", "Cherry", "Date"]
        assert self.loader._contains_header_keywords(no_keywords) is False

    def test_calculate_text_ratio(self):
        """テキスト比率計算のテスト."""
        mixed_row = ["Text", "123", "45.6", ""]
        ratio = self.loader._calculate_text_ratio(mixed_row)
        assert 0.0 <= ratio <= 1.0

    def test_calculate_numeric_ratio(self):
        """数値比率計算のテスト."""
        numeric_row = ["123", "45.6", "0", "-7.8"]
        ratio = self.loader._calculate_numeric_ratio(numeric_row)
        assert ratio == 1.0  # 全て数値

    def test_detect_header_row_basic(self):
        """基本的なヘッダー行検出のテスト."""
        test_data = [
            ["Name", "Age", "City"],  # ヘッダー
            ["Alice", "25", "Tokyo"],
            ["Bob", "30", "Osaka"],
        ]

        header_row = self.loader._detect_header_row(test_data)
        assert header_row == 0  # 最初の行がヘッダー

    def test_extract_headers_from_data(self):
        """データからのヘッダー抽出テスト."""
        test_data = [["Name", "Age", "City"], ["Alice", "25", "Tokyo"]]

        headers = self.loader._extract_headers_from_data(test_data, 0)
        assert headers == ["name", "age", "city"]  # 正規化されたヘッダー

    def test_parse_skip_rows_specification_list(self):
        """スキップ行指定(リスト)のパースのテスト."""
        skip_spec = "1,3,5"
        result = self.loader._parse_skip_rows_specification(skip_spec)
        assert result == [1, 3, 5]

    def test_parse_skip_rows_specification_range(self):
        """スキップ行指定(範囲)のパースのテスト."""
        skip_spec = "2-4"
        result = self.loader._parse_skip_rows_specification(skip_spec)
        assert result == [2, 3, 4]

    def test_apply_skip_rows(self):
        """スキップ行適用のテスト."""
        test_data = [["Row0"], ["Row1"], ["Row2"], ["Row3"], ["Row4"]]

        skip_rows = [1, 3]
        result = self.loader._apply_skip_rows(test_data, skip_rows)

        expected = [["Row0"], ["Row2"], ["Row4"]]
        assert result == expected
