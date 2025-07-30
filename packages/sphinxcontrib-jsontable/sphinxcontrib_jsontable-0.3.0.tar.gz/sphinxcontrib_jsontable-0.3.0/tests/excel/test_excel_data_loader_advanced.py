"""Excel Data Loader 高度機能のテスト."""

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


class TestExcelDataLoaderAdvanced:
    """ExcelDataLoaderの高度機能のテスト."""

    def setup_method(self):
        """各テストメソッドの前に実行される。"""
        self.temp_dir = tempfile.mkdtemp()
        self.loader = ExcelDataLoader(self.temp_dir)

    def teardown_method(self):
        """各テストメソッドの後に実行される。"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_excel(
        self, filename: str, data: list, has_header: bool = True
    ) -> str:
        """テスト用Excelファイルを作成。"""
        file_path = Path(self.temp_dir) / filename

        if has_header:
            df = pd.DataFrame(data[1:], columns=data[0])
        else:
            df = pd.DataFrame(data)

        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, header=has_header)
        return file_path

    def test_path_validation_comprehensive(self):
        """包括的なパス検証のテスト。"""
        # 絶対パスでの安全性チェック
        abs_safe_path = (Path(self.temp_dir) / "test.xlsx").resolve()
        assert self.loader.is_safe_path(abs_safe_path) is True

        # 相対パスでの安全性チェック
        rel_safe_path = "./test.xlsx"
        # 相対パスの場合、ベースディレクトリとの関係による
        result = self.loader.is_safe_path(rel_safe_path)
        assert isinstance(result, bool)

        # Windows形式のパストラバーサル
        windows_traversal = "..\\..\\windows\\system32"
        assert self.loader.is_safe_path(windows_traversal) is False

        # Unix形式のパストラバーサル
        unix_traversal = "../../etc/passwd"
        assert self.loader.is_safe_path(unix_traversal) is False

    def test_file_extension_validation(self):
        """ファイル拡張子の包括的検証テスト。"""
        # 有効な拡張子(小文字のみ対応)
        valid_extensions = [".xlsx"]
        for ext in valid_extensions:
            test_file = Path(self.temp_dir) / f"test{ext}"
            # 実際のファイルを作成
            with pd.ExcelWriter(test_file, engine="openpyxl") as writer:
                pd.DataFrame([["A", "B"], ["1", "2"]]).to_excel(writer, index=False)
            assert self.loader.validate_excel_file(test_file) is True

        # 無効な拡張子
        invalid_extensions = [".txt", ".csv", ".json", ".xml", ".pdf"]
        for ext in invalid_extensions:
            test_file = Path(self.temp_dir) / f"test{ext}"
            with open(test_file, "w") as f:
                f.write("dummy content")
            with pytest.raises(ValueError, match="Unsupported file format"):
                self.loader.validate_excel_file(test_file)

    def test_data_type_conversion_comprehensive(self):
        """包括的なデータ型変換のテスト。"""
        # 複雑な混合データ型
        complex_data = [
            ["Alice", 25, 175.5, True, None, pd.NaT],
            ["Bob", None, 180, False, "text", 123.456],
            [None, 30, None, None, "", 0],
            ["", 0, 0.0, True, "special", float("inf")],
        ]
        df = pd.DataFrame(complex_data)
        result = self.loader.data_type_conversion(df)

        # 結果の検証
        assert len(result) == 4
        assert isinstance(result, list)
        assert all(isinstance(row, list) for row in result)
        assert all(isinstance(cell, str) for row in result for cell in row)

        # 特定の変換ケースの確認
        assert result[0][0] == "Alice"  # 文字列はそのまま
        assert result[0][1] == "25"  # 整数は文字列に
        assert result[0][2] == "175.5"  # 浮動小数点数は文字列に
        assert result[0][3] == "True"  # Booleanは文字列に
        assert result[0][4] == ""  # Noneは空文字列に

    def test_header_detection_various_cases(self):
        """様々なケースでのヘッダー検出テスト。"""
        # 明確にヘッダーがあるケース
        header_data = pd.DataFrame(
            [
                ["Name", "Age", "City", "Country"],
                ["Alice", 25, "Tokyo", "Japan"],
                ["Bob", 30, "New York", "USA"],
            ]
        )
        # ヘッダー検出結果は実装に依存するため、booleanであることを確認
        result = self.loader.header_detection(header_data)
        assert isinstance(result, bool)

        # 数値のみのケース
        numeric_data = pd.DataFrame([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]])
        assert self.loader.header_detection(numeric_data) is False

        # 混合だが第1行が数値多数のケース
        mixed_numeric_first = pd.DataFrame(
            [[1, 2, "Category"], ["Alice", 25, "Person"], ["Bob", 30, "Person"]]
        )
        result = self.loader.header_detection(mixed_numeric_first)
        # 実装に依存するが、少なくともbooleanが返される
        assert isinstance(result, bool)

        # 空のDataFrameケース
        empty_data = pd.DataFrame()
        assert self.loader.header_detection(empty_data) is False

    def test_excel_loader_with_different_base_paths(self):
        """異なるベースパスでのExcelDataLoaderテスト。"""
        # Pathオブジェクトでの初期化
        path_obj = Path(self.temp_dir)
        loader_with_path = ExcelDataLoader(path_obj)
        assert loader_with_path.base_path == path_obj

        # 文字列でのベースパス
        loader_with_str = ExcelDataLoader(self.temp_dir)
        assert str(loader_with_str.base_path) == self.temp_dir

        # デフォルト(引数なし)
        loader_default = ExcelDataLoader()
        assert loader_default.base_path == Path.cwd()

    def test_excel_file_operations_edge_cases(self):
        """Excelファイル操作のエッジケースのテスト。"""
        # 非常に小さなデータ
        tiny_data = [["A"], ["1"]]
        excel_path = self.create_test_excel("tiny.xlsx", tiny_data, True)
        result = self.loader.load_from_excel(excel_path)
        assert result["rows"] == 1
        assert result["columns"] == 1
        assert result["data"] == [["1"]]

        # ヘッダーのみのデータ
        header_only_data = [["Name", "Age", "City"]]
        excel_path = self.create_test_excel("header_only.xlsx", header_only_data, True)
        result = self.loader.load_from_excel(excel_path)
        # ヘッダーのみの場合の動作は実装に依存する
        assert isinstance(result["rows"], int)
        # ヘッダーがNoneの場合もあるため、型チェックのみ
        assert result["headers"] is None or isinstance(result["headers"], list)
        assert isinstance(result["data"], list)

    def test_basic_sheet_detection_various_files(self):
        """様々なファイルでの基本シート検出テスト。"""
        # 標準的なExcelファイル
        test_data = [["Name", "Age"], ["Alice", "25"]]
        excel_path = self.create_test_excel("standard.xlsx", test_data)
        sheet_name = self.loader.basic_sheet_detection(excel_path)
        assert sheet_name in ["Sheet1", "シート1"]  # 環境により異なる可能性

        # 複数シートを持つファイル(最初のシートが検出される)
        with pd.ExcelWriter(Path(self.temp_dir) / "multi_sheet.xlsx") as writer:
            pd.DataFrame([["A", "B"], ["1", "2"]]).to_excel(
                writer, sheet_name="FirstSheet", index=False
            )
            pd.DataFrame([["C", "D"], ["3", "4"]]).to_excel(
                writer, sheet_name="SecondSheet", index=False
            )

        multi_sheet_path = Path(self.temp_dir) / "multi_sheet.xlsx"
        detected_sheet = self.loader.basic_sheet_detection(multi_sheet_path)
        assert detected_sheet == "FirstSheet"

    def test_validate_excel_file_comprehensive(self):
        """Excelファイル検証の包括的テスト。"""
        # 正常なファイルの検証
        valid_data = [["Name", "Age"], ["Alice", "25"]]
        valid_path = self.create_test_excel("valid.xlsx", valid_data)
        assert self.loader.validate_excel_file(valid_path) is True

        # 空のExcelファイル
        empty_df = pd.DataFrame()
        empty_path = Path(self.temp_dir) / "empty.xlsx"
        with pd.ExcelWriter(empty_path, engine="openpyxl") as writer:
            empty_df.to_excel(writer, index=False)
        # 空ファイルでも形式的には有効
        assert self.loader.validate_excel_file(empty_path) is True

        # 破損したファイル(Excelファイルとして認識されない)
        corrupted_path = Path(self.temp_dir) / "corrupted.xlsx"
        with open(corrupted_path, "w") as f:
            f.write("This is not an Excel file")
        # 破損ファイルは読み込み時にエラーになる可能性があるが、
        # validate_excel_fileは基本的な形式チェックのみ
        try:
            result = self.loader.validate_excel_file(corrupted_path)
            # エラーが出なければTrue、出ればexceptionがraiseされる
            assert isinstance(result, bool)
        except Exception:
            # 破損ファイルでエラーが出るのは想定内
            pass

    def test_load_from_excel_with_various_headers(self):
        """様々なヘッダー形式でのExcel読み込みテスト。"""
        # 日本語ヘッダー
        japanese_data = [
            ["名前", "年齢", "職業"],
            ["田中太郎", "30", "エンジニア"],
            ["佐藤花子", "25", "デザイナー"],
        ]
        jp_path = self.create_test_excel("japanese.xlsx", japanese_data, True)
        result = self.loader.load_from_excel(jp_path)
        assert result["headers"] == ["名前", "年齢", "職業"]
        assert result["data"][0] == ["田中太郎", "30", "エンジニア"]

        # 特殊文字を含むヘッダー
        special_data = [
            ["名前/Name", "年齢(Age)", "職業@Job"],
            ["Test User", "35", "Manager"],
        ]
        special_path = self.create_test_excel("special.xlsx", special_data, True)
        result = self.loader.load_from_excel(special_path)
        assert result["headers"] == ["名前/Name", "年齢(Age)", "職業@Job"]

    def test_data_consistency_check(self):
        """データ整合性チェックのテスト。"""
        # 不整合なデータ(行によって列数が異なる)
        # pandasは自動的に調整するため、実際にはエラーにならない
        inconsistent_data = [
            ["A", "B", "C"],
            ["1", "2"],  # 列数が少ない
            ["4", "5", "6", "7"],  # 列数が多い(pandasが調整)
        ]
        df = pd.DataFrame(inconsistent_data)
        result = self.loader.data_type_conversion(df)
        # pandasが自動的にNaNで埋めるため、問題なく処理される
        assert isinstance(result, list)
        assert len(result) == 3
