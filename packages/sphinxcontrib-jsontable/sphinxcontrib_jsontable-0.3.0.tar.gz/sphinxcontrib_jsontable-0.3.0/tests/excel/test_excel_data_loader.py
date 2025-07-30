"""Excel Data Loader関連のテスト."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Excel対応がある場合のみテストを実行
try:
    from sphinxcontrib.jsontable.excel_data_loader import ExcelDataLoader

    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


class TestExcelDataLoader:
    """ExcelDataLoaderクラスのテスト."""

    def setup_method(self):
        """各テストメソッドの前に実行される。"""
        self.temp_dir = tempfile.mkdtemp()
        self.loader = ExcelDataLoader(self.temp_dir)

    def teardown_method(self):
        """各テストメソッドの後に実行される。"""
        # 一時ディレクトリのクリーンアップ
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_excel(
        self, filename: str, data: list, has_header: bool = True
    ) -> str:
        """テスト用Excelファイルを作成。

        Args:
            filename: ファイル名(.xlsxを含む)
            data: 書き込むデータ(2D list)
            has_header: ヘッダー行があるかどうか

        Returns:
            str: 作成されたファイルのパス
        """
        file_path = str(Path(self.temp_dir) / filename)

        if has_header:
            df = pd.DataFrame(data[1:], columns=data[0])
        else:
            df = pd.DataFrame(data)

        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, header=has_header)
        return file_path

    def test_init(self):
        """初期化のテスト。"""
        loader = ExcelDataLoader("/test/path")
        assert loader.base_path == Path("/test/path")

        loader = ExcelDataLoader()
        assert loader.base_path == Path.cwd()

    def test_is_safe_path(self):
        """パス安全性チェックのテスト。"""
        # 安全なパス
        safe_path = str(Path(self.temp_dir) / "test.xlsx")
        assert self.loader.is_safe_path(safe_path) is True

        # 危険なパス (パストラバーサル)
        dangerous_path = str(Path(self.temp_dir) / "../../../etc/passwd")
        assert self.loader.is_safe_path(dangerous_path) is False

    def test_validate_excel_file(self):
        """Excelファイル検証のテスト。"""
        # 存在しないファイル
        with pytest.raises(FileNotFoundError):
            self.loader.validate_excel_file("nonexistent.xlsx")

        # 正常なExcelファイル
        test_data = [["Name", "Age"], ["Alice", "25"], ["Bob", "30"]]
        excel_path = self.create_test_excel("test_valid.xlsx", test_data)
        assert self.loader.validate_excel_file(excel_path) is True

        # 不正な拡張子
        txt_path = str(Path(self.temp_dir) / "test.txt")
        with open(txt_path, "w") as f:
            f.write("test")

        with pytest.raises(ValueError, match="Unsupported file format"):
            self.loader.validate_excel_file(txt_path)

    def test_basic_sheet_detection(self):
        """基本シート検出のテスト。"""
        test_data = [["Name", "Age"], ["Alice", "25"], ["Bob", "30"]]
        excel_path = self.create_test_excel("test_sheet.xlsx", test_data)

        sheet_name = self.loader.basic_sheet_detection(excel_path)
        assert sheet_name == "Sheet1"  # デフォルトシート名

    def test_header_detection(self):
        """ヘッダー検出のテスト。"""
        # ヘッダーありのデータ
        df_with_header = pd.DataFrame(
            [["Name", "Age", "City"], ["Alice", 25, "Tokyo"], ["Bob", 30, "Osaka"]]
        )
        assert self.loader.header_detection(df_with_header) is True

        # ヘッダーなしのデータ(全て数値)
        df_no_header = pd.DataFrame([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        assert self.loader.header_detection(df_no_header) is False

        # 空のDataFrame
        df_empty = pd.DataFrame()
        assert self.loader.header_detection(df_empty) is False

    def test_data_type_conversion(self):
        """データ型変換のテスト。"""
        # 混合データ型のDataFrame
        df = pd.DataFrame(
            [["Alice", 25, 175.5], ["Bob", 30, 180.0], ["Charlie", None, 165.8]]
        )

        result = self.loader.data_type_conversion(df)

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == ["Alice", "25", "175.5"]
        assert result[1] == ["Bob", "30", "180"]  # 180.0 → "180"
        assert result[2] == ["Charlie", "", "165.8"]  # None → ""

    def test_load_from_excel_with_header(self):
        """ヘッダーありExcelファイル読み込みのテスト。"""
        test_data = [
            ["Name", "Age", "City"],
            ["Alice", "25", "Tokyo"],
            ["Bob", "30", "Osaka"],
        ]
        excel_path = self.create_test_excel("test_with_header.xlsx", test_data, True)

        result = self.loader.load_from_excel(excel_path)

        assert result["has_header"] is True
        assert result["headers"] == ["Name", "Age", "City"]
        assert result["rows"] == 2
        assert result["columns"] == 3
        assert len(result["data"]) == 2
        assert result["data"][0] == ["Alice", "25", "Tokyo"]

    def test_load_from_excel_without_header(self):
        """ヘッダーなしExcelファイル読み込みのテスト。"""
        test_data = [["Alice", "25", "Tokyo"], ["Bob", "30", "Osaka"]]
        excel_path = self.create_test_excel("test_no_header.xlsx", test_data, False)

        result = self.loader.load_from_excel(excel_path)

        assert result["has_header"] is False
        assert result["headers"] == []
        assert result["rows"] == 2
        assert result["columns"] == 3
        assert len(result["data"]) == 2
        assert result["data"][0] == ["Alice", "25", "Tokyo"]

    def test_load_from_excel_with_explicit_header_row(self):
        """明示的なヘッダー行指定のテスト。"""
        test_data = [
            ["Name", "Age", "City"],
            ["Alice", "25", "Tokyo"],
            ["Bob", "30", "Osaka"],
        ]
        excel_path = self.create_test_excel(
            "test_explicit_header.xlsx", test_data, True
        )

        # ヘッダー行を明示的に指定
        result = self.loader.load_from_excel(excel_path, header_row=0)

        assert result["has_header"] is True
        assert result["headers"] == ["Name", "Age", "City"]
        assert len(result["data"]) == 2

    def test_load_from_excel_errors(self):
        """Excelファイル読み込みエラーのテスト。"""
        # 安全でないパス
        with pytest.raises(ValueError, match="Unsafe file path"):
            self.loader.load_from_excel("../../../etc/passwd")

        # 存在しないファイル(絶対パスを使用)
        from pathlib import Path

        nonexistent_path = str(Path(self.temp_dir) / "nonexistent.xlsx")
        with pytest.raises(FileNotFoundError):
            self.loader.load_from_excel(nonexistent_path)

    def test_load_from_excel_empty_file(self):
        """空のExcelファイルのテスト。"""
        # 空のDataFrameを作成
        df_empty = pd.DataFrame()
        from pathlib import Path

        empty_path = str(Path(self.temp_dir) / "empty.xlsx")
        with pd.ExcelWriter(empty_path, engine="openpyxl") as writer:
            df_empty.to_excel(writer, index=False)

        with pytest.raises(ValueError, match="Empty data"):
            self.loader.load_from_excel(empty_path)


@pytest.mark.skipif(EXCEL_AVAILABLE, reason="Test Excel import error handling")
def test_excel_import_error():
    """Excel機能が無効な場合のテスト。"""
    # この場合、ExcelDataLoaderのインポート自体が失敗するため、
    # ここではEXCEL_AVAILABLEフラグのテストのみ行う
    assert EXCEL_AVAILABLE is False
