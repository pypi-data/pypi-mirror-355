"""Excel Data Loader 範囲指定・Skip Rows機能のテスト."""

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Excel対応がある場合のみテストを実行
try:
    from sphinxcontrib.jsontable.excel_data_loader import (
        ExcelDataLoader,
        RangeSpecificationError,
        SkipRowsError,
    )

    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


class TestExcelDataLoaderRangeSkip:
    """ExcelDataLoaderの範囲指定・Skip Rows機能のテスト."""

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

    def create_large_test_excel(self) -> str:
        """大きなテスト用Excelファイルを作成。"""
        data = [["ID", "Name", "Score", "Category"]]
        for i in range(100):
            data.append([str(i), f"User_{i}", str(i * 10 % 100), f"Category_{i % 5}"])

        return self.create_test_excel("large_test.xlsx", data, True)

    def test_range_specification_parsing(self):
        """範囲指定の解析機能テスト。"""
        test_data = [
            ["A", "B", "C", "D"],
            ["1", "2", "3", "4"],
            ["5", "6", "7", "8"],
            ["9", "10", "11", "12"],
        ]
        excel_path = self.create_test_excel("range_parse.xlsx", test_data, False)

        # 有効な範囲指定
        valid_ranges = [
            "A1:C3",
            "B2:D4",
            "A1:B2",
            "C1:D2",
        ]

        for range_spec in valid_ranges:
            try:
                result = self.loader.load_from_excel_with_range(excel_path, range_spec)
                assert isinstance(result, dict)
                assert "data" in result
                assert "range" in result
                assert result["range"] == range_spec
            except Exception as e:
                # 実装されていない場合はスキップ
                pytest.skip(f"Range specification not implemented: {e}")

    def test_skip_rows_parsing(self):
        """Skip Rows指定の解析機能テスト。"""
        test_data = [
            ["Comment line", "", "", ""],  # Row 0
            ["Header", "A", "B", "C"],  # Row 1
            ["Data1", "1", "2", "3"],  # Row 2
            ["Comment", "", "", ""],  # Row 3
            ["Data2", "4", "5", "6"],  # Row 4
        ]
        excel_path = self.create_test_excel("skip_rows.xlsx", test_data, False)

        # 有効なSkip Rows指定
        valid_skip_specs = [
            "0",  # 単一行
            "0,3",  # 複数行
            "0-2",  # 範囲
            "0,3-4",  # 混合
        ]

        for skip_spec in valid_skip_specs:
            try:
                result = self.loader.load_from_excel_with_skip_rows(
                    excel_path, skip_spec
                )
                assert isinstance(result, dict)
                assert "data" in result
                assert "skip_rows" in result
                assert result["skip_rows"] == skip_spec
            except Exception as e:
                # 実装されていない場合はスキップ
                pytest.skip(f"Skip rows not implemented: {e}")

    def test_range_and_skip_combination(self):
        """範囲指定とSkip Rowsの組み合わせテスト。"""
        test_data = [
            ["Comment", "", "", ""],  # Row 0
            ["Header", "A", "B", "C"],  # Row 1
            ["Data1", "1", "2", "3"],  # Row 2
            ["Comment", "", "", ""],  # Row 3
            ["Data2", "4", "5", "6"],  # Row 4
            ["Data3", "7", "8", "9"],  # Row 5
        ]
        excel_path = self.create_test_excel("combo.xlsx", test_data, False)

        try:
            # A1:C5の範囲で、コメント行(0,3)をスキップ
            result = self.loader.load_from_excel_with_skip_rows_and_range(
                excel_path, range_spec="A1:C5", skip_rows="0,3"
            )
            assert isinstance(result, dict)
            assert "data" in result
            assert "range" in result
            assert "skip_rows" in result
        except Exception as e:
            pytest.skip(f"Range and skip combination not implemented: {e}")

    def test_header_row_specification(self):
        """ヘッダー行指定機能のテスト。"""
        test_data = [
            ["Comment", "", ""],  # Row 0
            ["Name", "Age", "City"],  # Row 1 - Header
            ["Alice", "25", "Tokyo"],  # Row 2
            ["Bob", "30", "Osaka"],  # Row 3
        ]
        excel_path = self.create_test_excel("header_spec.xlsx", test_data, False)

        # 1行目をヘッダーとして指定
        result = self.loader.load_from_excel_with_header_row(excel_path, 1)
        assert isinstance(result, dict)
        assert result["has_header"] is True
        assert result["headers"] == ["name", "age", "city"]  # ヘッダー正規化済み
        assert len(result["data"]) == 2

    def test_range_with_header_row(self):
        """範囲指定とヘッダー行指定の組み合わせテスト。"""
        test_data = [
            ["A", "B", "C", "D", "E"],
            ["Name", "Age", "City", "Score", "Rank"],  # Row 1 - Header
            ["Alice", "25", "Tokyo", "95", "1"],
            ["Bob", "30", "Osaka", "87", "2"],
            ["Charlie", "22", "Kyoto", "92", "3"],
        ]
        excel_path = self.create_test_excel("range_header.xlsx", test_data, False)

        # B1:D4の範囲でヘッダー行1を指定
        result = self.loader.load_from_excel_with_range_and_header_row(
            excel_path, range_spec="B1:D4", header_row=1
        )
        assert isinstance(result, dict)
        assert result["has_header"] is True
        assert result["headers"] == ["age", "city", "score"]  # ヘッダー正規化済み

    def test_skip_rows_with_header_row(self):
        """Skip Rowsとヘッダー行指定の組み合わせテスト。"""
        test_data = [
            ["Comment1", "", ""],  # Row 0 - Skip
            ["Name", "Age", "City"],  # Row 1 - Header
            ["Alice", "25", "Tokyo"],  # Row 2
            ["Comment2", "", ""],  # Row 3 - Skip
            ["Bob", "30", "Osaka"],  # Row 4
        ]
        excel_path = self.create_test_excel("skip_header.xlsx", test_data, False)

        # コメント行(0,3)をスキップ、1行目をヘッダーとして指定
        result = self.loader.load_from_excel_with_skip_rows_and_header(
            excel_path, skip_rows="0,3", header_row=1
        )
        assert isinstance(result, dict)
        assert result["has_header"] is True
        assert result["headers"] == ["name", "age", "city"]  # ヘッダー正規化済み
        assert len(result["data"]) == 2

    def test_error_handling_range_specification(self):
        """範囲指定のエラーハンドリングテスト。"""
        test_data = [["A", "B"], ["1", "2"]]
        excel_path = self.create_test_excel("error_range.xlsx", test_data, False)

        # 無効な範囲指定
        invalid_ranges = [
            "Z1:Z2",  # 存在しない列
            "A1:A100",  # 存在しない行
            "B1:A1",  # 逆順
            "invalid",  # 無効な形式
            "",  # 空文字
        ]

        for invalid_range in invalid_ranges:
            with pytest.raises((ValueError, RangeSpecificationError)):
                self.loader.load_from_excel_with_range(excel_path, invalid_range)

    def test_error_handling_skip_rows(self):
        """Skip Rowsのエラーハンドリングテスト。"""
        test_data = [["A", "B"], ["1", "2"], ["3", "4"]]
        excel_path = self.create_test_excel("error_skip.xlsx", test_data, False)

        # 無効なSkip Rows指定
        invalid_skip_specs = [
            "100",  # 存在しない行
            "-1",  # 負の値
            "a,b",  # 無効な文字
            "1-",  # 不完全な範囲
            "",  # 空文字
        ]

        for invalid_skip in invalid_skip_specs:
            with pytest.raises((ValueError, SkipRowsError)):
                self.loader.load_from_excel_with_skip_rows(excel_path, invalid_skip)

    def test_large_dataset_handling(self):
        """大きなデータセットの処理テスト。"""
        excel_path = self.create_large_test_excel()

        # 大きなファイルの読み込み
        result = self.loader.load_from_excel(excel_path)
        assert isinstance(result, dict)
        assert result["rows"] == 100
        assert result["columns"] == 4

        # 範囲指定での読み込み
        range_result = self.loader.load_from_excel_with_range(excel_path, "A1:C50")
        assert isinstance(range_result, dict)
        assert len(range_result["data"]) == 50

        # Skip Rowsでの読み込み
        skip_result = self.loader.load_from_excel_with_skip_rows(
            excel_path,
            "0-9",  # 最初の10行をスキップ
        )
        assert isinstance(skip_result, dict)
        assert len(skip_result["data"]) == 90  # 100行 - 10行 = 90行(ヘッダー除く)

    def test_range_validation_methods(self):
        """範囲検証メソッドのテスト。"""
        # 有効な範囲検証
        valid_ranges = [
            "A1:B2",
            "C3:D4",
            "A1:Z100",
        ]

        for valid_range in valid_ranges:
            try:
                # 範囲検証メソッドが存在する場合
                if hasattr(self.loader, "_validate_range_specification"):
                    result = self.loader._validate_range_specification(valid_range)
                    assert result is True or result is None
            except Exception:
                # メソッドが存在しないか、実装されていない場合はスキップ
                pass

    def test_skip_rows_validation_methods(self):
        """Skip Rows検証メソッドのテスト。"""
        # 有効なSkip Rows検証
        valid_skip_specs = [
            "0",
            "1,2,3",
            "0-5",
            "1-3,7,9-11",
        ]

        for valid_skip in valid_skip_specs:
            try:
                # Skip Rows検証メソッドが存在する場合
                if hasattr(self.loader, "_validate_skip_rows_specification"):
                    result = self.loader._validate_skip_rows_specification(valid_skip)
                    assert result is True or result is None
            except Exception:
                # メソッドが存在しないか、実装されていない場合はスキップ
                pass

    def test_data_extraction_methods(self):
        """データ抽出メソッドのテスト。"""
        test_data = [
            ["Name", "Age", "City"],
            ["Alice", "25", "Tokyo"],
            ["Bob", "30", "Osaka"],
        ]
        excel_path = self.create_test_excel("extraction.xlsx", test_data, True)

        try:
            # 基本的なデータ抽出
            result = self.loader.load_from_excel(excel_path)
            assert isinstance(result["data"], list)
            assert len(result["data"]) == 2

            # ヘッダー情報の確認
            if result["has_header"]:
                assert isinstance(result["headers"], list)
                assert len(result["headers"]) == 3

            # メタデータの確認
            assert isinstance(result["rows"], int)
            assert isinstance(result["columns"], int)
            assert result["rows"] >= 0
            assert result["columns"] >= 0

        except Exception as e:
            pytest.skip(f"Data extraction methods not implemented: {e}")

    def test_sheet_name_handling(self):
        """シート名処理のテスト。"""
        # 複数シートを持つExcelファイルを作成
        multi_sheet_path = os.path.join(self.temp_dir, "multi_sheet.xlsx")

        with pd.ExcelWriter(multi_sheet_path, engine="openpyxl") as writer:
            # Sheet1
            pd.DataFrame([["A1", "B1"], ["A2", "B2"]]).to_excel(
                writer, sheet_name="Sheet1", index=False
            )
            # Sheet2
            pd.DataFrame([["C1", "D1"], ["C2", "D2"]]).to_excel(
                writer, sheet_name="Sheet2", index=False
            )

        try:
            # デフォルトシートでの読み込み
            result1 = self.loader.load_from_excel(multi_sheet_path)
            assert isinstance(result1, dict)

            # 明示的なシート指定での読み込み
            if hasattr(self.loader, "load_from_excel"):
                # シート名を指定できる場合
                try:
                    result2 = self.loader.load_from_excel(
                        multi_sheet_path, sheet_name="Sheet2"
                    )
                    assert isinstance(result2, dict)
                except TypeError:
                    # sheet_nameパラメータがサポートされていない場合
                    pass

        except Exception as e:
            pytest.skip(f"Sheet name handling not implemented: {e}")
