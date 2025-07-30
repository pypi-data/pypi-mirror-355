"""Phase 2: Skip Rows機能のTDDテスト.

Task 2.4: `:skip-rows:` オプション実装のテスト
- 行番号リスト指定機能(例: "0,1,2")
- 範囲指定対応(例: "0-2,5,7-9")
- 指定行の除外処理
- データ整合性確保
- 他オプションとの組み合わせ
"""

import os
import shutil
import tempfile

import pandas as pd
import pytest
from sphinx.util.docutils import docutils_namespace

# Excel対応がある場合のみテストを実行
try:
    from sphinxcontrib.jsontable.directives import JsonTableDirective
    from sphinxcontrib.jsontable.excel_data_loader import ExcelDataLoader

    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


def create_mock_state_machine(srcdir="/tmp"):
    """Create a mock state machine for testing JsonTableDirective."""

    class MockReporter:
        def warning(self, msg, *args, **kwargs):
            pass

        def error(self, msg, *args, **kwargs):
            pass

        def info(self, msg, *args, **kwargs):
            pass

    class MockConfig:
        def __init__(self):
            self.jsontable_max_rows = 1000

    class MockEnv:
        def __init__(self, srcdir):
            self.config = MockConfig()
            self.srcdir = srcdir

    class MockSettings:
        def __init__(self, srcdir):
            self.env = MockEnv(srcdir)

    class MockDocument:
        def __init__(self, srcdir):
            self.settings = MockSettings(srcdir)

    class MockState:
        def __init__(self, srcdir):
            self.document = MockDocument(srcdir)

    class MockStateMachine:
        def __init__(self):
            self.reporter = MockReporter()

    return MockStateMachine(), MockState(srcdir)


class TestSkipRows:
    """Phase 2: Skip Rows機能のテスト."""

    def setup_method(self):
        """各テストメソッドの前に実行される。"""
        self.temp_dir = tempfile.mkdtemp()
        self.loader = ExcelDataLoader(self.temp_dir)

    def teardown_method(self):
        """各テストメソッドの後に実行される。"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_skip_rows_test_excel(self) -> str:
        """Skip Rows機能テスト用のExcelファイルを作成。

        Returns:
            str: 作成されたファイルのパス
        """
        file_path = os.path.join(self.temp_dir, "skip_rows_test.xlsx")

        # スキップ対象の行を含むデータを作成
        data = [
            ["# コメント行(スキップ対象)", "", "", ""],  # Row 0
            ["メタデータ: 作成日 2025-06-13", "", "", ""],  # Row 1
            ["", "", "", ""],  # Row 2: 空行
            ["商品名", "価格", "在庫", "カテゴリ"],  # Row 3: ヘッダー行
            ["商品A", "1000", "50", "電子機器"],  # Row 4: データ行
            ["商品B", "2000", "30", "家具"],  # Row 5: データ行
            ["# 中間コメント", "", "", ""],  # Row 6: スキップ対象
            ["商品C", "1500", "20", "文具"],  # Row 7: データ行
            ["商品D", "3000", "10", "電子機器"],  # Row 8: データ行
            ["", "", "", ""],  # Row 9: 空行
            ["合計", "7500", "110", ""],  # Row 10: 集計行(スキップ対象)
        ]

        df = pd.DataFrame(data)

        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Sheet1", index=False, header=False)

        return file_path

    def test_skip_rows_by_list(self):
        """行番号リスト指定でのスキップテスト(未実装機能なので失敗する)。"""
        excel_path = self.create_skip_rows_test_excel()

        # 0,1,2行目をスキップ(コメント、メタデータ、空行をスキップ)
        result = self.loader.load_from_excel_with_skip_rows(
            excel_path, skip_rows="0,1,2"
        )

        # 期待されるデータ(3行目以降、スキップした行は除外)
        expected_data = [
            ["商品名", "価格", "在庫", "カテゴリ"],  # Row 3
            ["商品A", "1000", "50", "電子機器"],  # Row 4
            ["商品B", "2000", "30", "家具"],  # Row 5
            ["# 中間コメント", "", "", ""],  # Row 6
            ["商品C", "1500", "20", "文具"],  # Row 7
            ["商品D", "3000", "10", "電子機器"],  # Row 8
            ["", "", "", ""],  # Row 9
            ["合計", "7500", "110", ""],  # Row 10
        ]

        assert result["data"] == expected_data
        assert result["skip_rows"] == "0,1,2"
        assert result["skipped_row_count"] == 3

    def test_skip_rows_by_range(self):
        """範囲指定でのスキップテスト(未実装機能なので失敗する)。"""
        excel_path = self.create_skip_rows_test_excel()

        # 0-2行目と6行目と9-10行目をスキップ
        result = self.loader.load_from_excel_with_skip_rows(
            excel_path, skip_rows="0-2,6,9-10"
        )

        # 期待されるデータ(スキップされた行を除く)
        expected_data = [
            ["商品名", "価格", "在庫", "カテゴリ"],  # Row 3
            ["商品A", "1000", "50", "電子機器"],  # Row 4
            ["商品B", "2000", "30", "家具"],  # Row 5
            ["商品C", "1500", "20", "文具"],  # Row 7
            ["商品D", "3000", "10", "電子機器"],  # Row 8
        ]

        assert result["data"] == expected_data
        assert result["skip_rows"] == "0-2,6,9-10"
        assert result["skipped_row_count"] == 6  # 0,1,2,6,9,10の6行

    def test_skip_rows_with_header_row(self):
        """Skip Rowsとヘッダー行指定の組み合わせテスト(未実装なので失敗する)。"""
        excel_path = self.create_skip_rows_test_excel()

        # 0-2行目をスキップし、3行目をヘッダーとして使用
        result = self.loader.load_from_excel_with_skip_rows_and_header(
            excel_path, "0-2,6,9-10", 3
        )

        # スキップ後のデータでヘッダー処理
        expected_headers = ["商品名", "価格", "在庫", "カテゴリ"]
        assert result["headers"] == expected_headers
        assert result["has_header"]

        # データ部分(ヘッダー行以降、スキップ行は除外)
        expected_data = [
            ["商品A", "1000", "50", "電子機器"],  # Row 4
            ["商品B", "2000", "30", "家具"],  # Row 5
            ["商品C", "1500", "20", "文具"],  # Row 7
            ["商品D", "3000", "10", "電子機器"],  # Row 8
        ]
        assert result["data"] == expected_data

    def test_skip_rows_with_range(self):
        """Skip Rowsと範囲指定の組み合わせテスト。"""
        excel_path = self.create_skip_rows_test_excel()

        # A3:C8の範囲で、範囲内index 3をスキップ(元のExcel行6に相当)
        result = self.loader.load_from_excel_with_skip_rows_and_range(
            excel_path, range_spec="A3:C8", skip_rows="3"
        )

        # 範囲内でスキップ処理された結果
        expected_data = [
            ["", "", ""],  # Row 3 (range index 0)
            ["商品名", "価格", "在庫"],  # Row 4 (range index 1)
            ["商品A", "1000", "50"],  # Row 5 (range index 2)
            # Range index 3 (["商品B", "2000", "30"]) はスキップ
            ["# 中間コメント", "", ""],  # Row 7 (元のrange index 4)
            ["商品C", "1500", "20"],  # Row 8 (元のrange index 5)
        ]

        assert result["data"] == expected_data
        assert result["range"] == "A3:C8"
        assert result["skip_rows"] == "3"

    def test_invalid_skip_rows_format_error(self):
        """無効なスキップ行形式指定時のエラーテスト(未実装なので失敗する)。"""
        excel_path = self.create_skip_rows_test_excel()

        # 無効な形式
        invalid_formats = [
            "a,b,c",  # 文字列
            "1-",  # 不完全な範囲
            "-5",  # 不完全な範囲
            "1--5",  # 無効な範囲記法
            "1,2,,3",  # 空の要素
        ]

        for invalid_format in invalid_formats:
            with pytest.raises(
                Exception,
                match="Invalid.*format|Negative.*not.*allowed|Invalid.*specification",
            ):
                self.loader.load_from_excel_with_skip_rows(
                    excel_path, skip_rows=invalid_format
                )

    def test_skip_rows_out_of_range_error(self):
        """範囲外のスキップ行指定時のエラーテスト(未実装なので失敗する)。"""
        excel_path = self.create_skip_rows_test_excel()

        # 範囲外の行番号(データが11行なので11以上は無効)
        with pytest.raises(ValueError, match="Skip row 15 is out of range"):
            self.loader.load_from_excel_with_skip_rows(excel_path, skip_rows="0,1,15")

    def test_directive_skip_rows_option(self):
        """JsonTableDirectiveの:skip-rows:オプションテスト(未実装なので失敗する)。"""
        excel_path = self.create_skip_rows_test_excel()

        # モックSphinx環境
        class MockConfig:
            jsontable_max_rows = 10000

        class MockEnv:
            def __init__(self, srcdir):
                self.srcdir = srcdir
                self.config = MockConfig()

        MockEnv(self.temp_dir)

        with docutils_namespace():
            # Skip Rows指定付きディレクティブ
            mock_state_machine, mock_state = create_mock_state_machine(self.temp_dir)

            directive = JsonTableDirective(
                name="jsontable",
                arguments=[os.path.basename(excel_path)],
                options={"header": True, "header-row": 3, "skip-rows": "0-2,6,9-10"},
                content=[],
                lineno=1,
                content_offset=0,
                block_text="",
                state=mock_state,
                state_machine=mock_state_machine,
            )
            directive.excel_loader = ExcelDataLoader(self.temp_dir)

            json_data = directive._load_json_data()

            # スキップ処理された結果を確認
            assert len(json_data) == 4  # データ行数(ヘッダー除く)
            assert json_data[0]["商品名"] == "商品A"
            assert json_data[1]["商品名"] == "商品B"
            assert (
                json_data[2]["商品名"] == "商品C"
            )  # Row 6がスキップされているためRow 7
            assert json_data[3]["商品名"] == "商品D"

    def test_skip_rows_parsing(self):
        """Skip Rows指定文字列の解析テスト(未実装なので失敗する)。"""
        # 正常な形式のテスト
        result = self.loader._parse_skip_rows_specification("0,1,2")
        assert result == [0, 1, 2]

        result = self.loader._parse_skip_rows_specification("0-2,5,7-9")
        assert result == [0, 1, 2, 5, 7, 8, 9]

        result = self.loader._parse_skip_rows_specification("10")
        assert result == [10]

        # 重複の排除
        result = self.loader._parse_skip_rows_specification("1,2,1,3,2")
        assert result == [1, 2, 3]

        # ソート
        result = self.loader._parse_skip_rows_specification("5,1,3")
        assert result == [1, 3, 5]

    def test_skip_rows_validation(self):
        """Skip Rows指定の検証テスト(未実装なので失敗する)。"""
        # 無効な型
        with pytest.raises(TypeError, match="Skip rows must be a string"):
            self.loader._validate_skip_rows_specification(123)

        # 空文字列
        with pytest.raises(ValueError, match="Skip rows specification cannot be empty"):
            self.loader._validate_skip_rows_specification("")

        # None
        assert (
            self.loader._validate_skip_rows_specification(None) is None
        )  # スキップなしモード


if __name__ == "__main__":
    # スタンドアロンテスト実行
    pytest.main([__file__, "-v"])
