"""Phase 2: Range Specification機能のTDDテスト.

Task 2.2: `:range:` オプション実装のテスト
- A1:C10形式の範囲指定機能
- 範囲検証ロジック
- 範囲外アクセス防止
- 指定範囲のデータ抽出
- 空セルの処理
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


class TestRangeSpecification:
    """Phase 2: Range Specification機能のテスト."""

    def setup_method(self):
        """各テストメソッドの前に実行される。"""
        self.temp_dir = tempfile.mkdtemp()
        self.loader = ExcelDataLoader(self.temp_dir)

    def teardown_method(self):
        """各テストメソッドの後に実行される。"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_range_test_excel(self) -> str:
        """範囲指定テスト用の構造化Excelファイルを作成。

        Returns:
            str: 作成されたファイルのパス
        """
        file_path = os.path.join(self.temp_dir, "range_test.xlsx")

        # 6x6のデータグリッドを作成
        data = [
            ["A", "B", "C", "D", "E", "F"],  # Row 1
            ["1", "2", "3", "4", "5", "6"],  # Row 2
            ["X", "Y", "Z", "P", "Q", "R"],  # Row 3
            ["7", "8", "9", "10", "11", "12"],  # Row 4
            ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"],  # Row 5
            ["100", "200", "300", "400", "500", "600"],  # Row 6
        ]

        df = pd.DataFrame(data)

        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Sheet1", index=False, header=False)

        return file_path

    def test_basic_range_specification(self):
        """基本的な範囲指定のテスト(未実装機能なので失敗する)。"""
        excel_path = self.create_range_test_excel()

        # A1:C3の範囲を指定
        result = self.loader.load_from_excel_with_range(excel_path, range_spec="A1:C3")

        # 期待される3x3のデータ
        expected_data = [["A", "B", "C"], ["1", "2", "3"], ["X", "Y", "Z"]]

        assert result["data"] == expected_data
        assert result["range"] == "A1:C3"
        assert result["rows"] == 3
        assert result["columns"] == 3

    def test_single_cell_range(self):
        """単一セル範囲指定のテスト(未実装機能なので失敗する)。"""
        excel_path = self.create_range_test_excel()

        # 単一セルB2を指定
        result = self.loader.load_from_excel_with_range(excel_path, range_spec="B2")

        expected_data = [["2"]]

        assert result["data"] == expected_data
        assert result["range"] == "B2"
        assert result["rows"] == 1
        assert result["columns"] == 1

    def test_full_row_range(self):
        """行全体の範囲指定のテスト(未実装機能なので失敗する)。"""
        excel_path = self.create_range_test_excel()

        # 2行目全体を指定(A2:F2)
        result = self.loader.load_from_excel_with_range(excel_path, range_spec="A2:F2")

        expected_data = [["1", "2", "3", "4", "5", "6"]]

        assert result["data"] == expected_data
        assert result["range"] == "A2:F2"
        assert result["rows"] == 1
        assert result["columns"] == 6

    def test_full_column_range(self):
        """列全体の範囲指定のテスト(未実装機能なので失敗する)。"""
        excel_path = self.create_range_test_excel()

        # B列全体を指定(B1:B6)
        result = self.loader.load_from_excel_with_range(excel_path, range_spec="B1:B6")

        expected_data = [["B"], ["2"], ["Y"], ["8"], ["Beta"], ["200"]]

        assert result["data"] == expected_data
        assert result["range"] == "B1:B6"
        assert result["rows"] == 6
        assert result["columns"] == 1

    def test_invalid_range_format_error(self):
        """無効な範囲形式指定時のエラーテスト(未実装なので失敗する)。"""
        excel_path = self.create_range_test_excel()

        # 無効な範囲形式
        invalid_format_ranges = [
            "A1-C3",  # ハイフン形式(コロンが正しい)
            "1A:3C",  # 逆順
            "A:C3",  # 不完全な形式
            "A1:C",  # 不完全な形式
        ]

        for invalid_range in invalid_format_ranges:
            with pytest.raises(
                Exception,
                match="Invalid.*format|Invalid.*address|Invalid.*cell|Unexpected.*error",
            ):
                self.loader.load_from_excel_with_range(
                    excel_path, range_spec=invalid_range
                )

        # 範囲外のセルアドレス(有効な形式だが存在しない列)
        out_of_bounds_ranges = [
            "Z1:AA1",  # 存在しない列
        ]

        for out_of_bounds_range in out_of_bounds_ranges:
            with pytest.raises(Exception, match="exceeds.*columns|out of bounds"):
                self.loader.load_from_excel_with_range(
                    excel_path, range_spec=out_of_bounds_range
                )

    def test_out_of_bounds_range_error(self):
        """範囲外指定時のエラーテスト(未実装なので失敗する)。"""
        excel_path = self.create_range_test_excel()

        # 範囲外の指定(6x6のデータなので、G列やRow7は存在しない)
        with pytest.raises(
            Exception, match="exceeds.*rows|exceeds.*columns|out of bounds"
        ):
            self.loader.load_from_excel_with_range(excel_path, range_spec="A1:G10")

    def test_inverted_range_error(self):
        """逆転範囲指定時のエラーテスト(未実装なので失敗する)。"""
        excel_path = self.create_range_test_excel()

        # 逆転した範囲(C3:A1は無効)
        with pytest.raises(
            Exception,
            match="Invalid range.*start.*end|start.*must.*before|Start.*greater.*end|Unexpected.*error",
        ):
            self.loader.load_from_excel_with_range(excel_path, range_spec="C3:A1")

    def test_directive_range_option(self):
        """JsonTableDirectiveの:range:オプションテスト(未実装なので失敗する)。"""
        excel_path = self.create_range_test_excel()

        # モックSphinx環境
        class MockConfig:
            jsontable_max_rows = 10000

        class MockEnv:
            def __init__(self, srcdir):
                self.srcdir = srcdir
                self.config = MockConfig()

        MockEnv(self.temp_dir)

        with docutils_namespace():
            # 範囲指定付きディレクティブ
            mock_state_machine, mock_state = create_mock_state_machine(self.temp_dir)

            directive = JsonTableDirective(
                name="jsontable",
                arguments=[os.path.basename(excel_path)],
                options={"header": True, "range": "A1:C4"},
                content=[],
                lineno=1,
                content_offset=0,
                block_text="",
                state=mock_state,
                state_machine=mock_state_machine,
            )
            directive.excel_loader = ExcelDataLoader(self.temp_dir)

            json_data = directive._load_json_data()

            # A1:C4範囲のデータが取得されることを確認
            # 範囲指定時はlist[list[str]]形式で生データが返される
            assert len(json_data) == 4  # A1:C4の4行分
            assert json_data[0] == ["A", "B", "C"]  # 1行目(ヘッダー)
            assert json_data[1] == ["1", "2", "3"]  # 2行目
            assert json_data[2] == ["X", "Y", "Z"]  # 3行目
            assert json_data[3] == ["7", "8", "9"]  # 4行目

    def test_range_with_sheet_option(self):
        """範囲指定とシート指定の組み合わせテスト(未実装なので失敗する)。"""
        excel_path = self.create_range_test_excel()

        # シートと範囲の両方を指定
        result = self.loader.load_from_excel_with_range(
            excel_path, sheet_name="Sheet1", range_spec="B2:D4"
        )

        expected_data = [["2", "3", "4"], ["Y", "Z", "P"], ["8", "9", "10"]]

        assert result["data"] == expected_data
        assert result["sheet_name"] == "Sheet1"
        assert result["range"] == "B2:D4"

    def test_range_specification_validation(self):
        """範囲指定の検証ロジックテスト(未実装なので失敗する)。"""
        # range_specが文字列でない場合
        with pytest.raises(TypeError, match="Range specification must be a string"):
            self.loader._parse_range_specification(123)

        # 空文字列の場合
        with pytest.raises(ValueError, match="Range specification cannot be empty"):
            self.loader._parse_range_specification("")

        # None の場合
        with pytest.raises(TypeError, match="Range specification must be a string"):
            self.loader._parse_range_specification(None)


if __name__ == "__main__":
    # スタンドアロンテスト実行
    pytest.main([__file__, "-v"])
