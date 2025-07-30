"""Phase 2: Sheet Selection機能のTDDテスト.

Task 2.1: `:sheet:` オプション実装のテスト
- シート名指定機能
- シートインデックス指定機能
- デフォルトシート設定
- エラーハンドリング(存在しないシート、日本語対応)
"""

import shutil
import tempfile
from pathlib import Path

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


class TestSheetSelection:
    """Phase 2: Sheet Selection機能のテスト."""

    def setup_method(self):
        """各テストメソッドの前に実行される。"""
        self.temp_dir = tempfile.mkdtemp()
        self.loader = ExcelDataLoader(self.temp_dir)

    def teardown_method(self):
        """各テストメソッドの後に実行される。"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_multi_sheet_excel(self) -> str:
        """複数シートを持つテスト用Excelファイルを作成。

        Returns:
            str: 作成されたファイルのパス
        """
        file_path = Path(self.temp_dir) / "multi_sheet_test.xlsx"

        # 複数のシートを作成
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            # Sheet1: 基本データ
            df1 = pd.DataFrame(
                [
                    ["Name", "Age", "City"],
                    ["Alice", "25", "Tokyo"],
                    ["Bob", "30", "Osaka"],
                ]
            )
            df1.to_excel(writer, sheet_name="Sheet1", index=False, header=False)

            # 営業データ: 日本語シート名
            df2 = pd.DataFrame(
                [
                    ["商品", "売上", "担当者"],
                    ["商品A", "100000", "田中"],
                    ["商品B", "150000", "佐藤"],
                ]
            )
            df2.to_excel(writer, sheet_name="営業データ", index=False, header=False)

            # Data Sheet: 英語シート名
            df3 = pd.DataFrame(
                [
                    ["Product", "Price", "Stock"],
                    ["Widget", "500", "100"],
                    ["Gadget", "750", "50"],
                ]
            )
            df3.to_excel(writer, sheet_name="Data Sheet", index=False, header=False)

        return file_path

    def test_sheet_selection_by_name(self):
        """シート名による指定のテスト(実装前なので失敗する)。"""
        excel_path = self.create_multi_sheet_excel()

        # Sheet1を明示的に指定
        result = self.loader.load_from_excel(excel_path, sheet_name="Sheet1")
        assert result["sheet_name"] == "Sheet1"
        assert result["data"][0] == ["Alice", "25", "Tokyo"]

        # 営業データシート(日本語名)を指定
        result = self.loader.load_from_excel(excel_path, sheet_name="営業データ")
        assert result["sheet_name"] == "営業データ"
        assert result["data"][0] == ["商品A", "100000", "田中"]

        # Data Sheetを指定
        result = self.loader.load_from_excel(excel_path, sheet_name="Data Sheet")
        assert result["sheet_name"] == "Data Sheet"
        assert result["data"][0] == ["Widget", "500", "100"]

    def test_sheet_selection_by_index(self):
        """シートインデックスによる指定のテスト(未実装機能なので失敗する)。"""
        excel_path = self.create_multi_sheet_excel()

        # インデックス0(最初のシート)
        result = self.loader.load_from_excel_by_index(excel_path, sheet_index=0)
        assert result["sheet_name"] == "Sheet1"
        assert result["data"][0] == ["Alice", "25", "Tokyo"]

        # インデックス1(2番目のシート)
        result = self.loader.load_from_excel_by_index(excel_path, sheet_index=1)
        assert result["sheet_name"] == "営業データ"
        assert result["data"][0] == ["商品A", "100000", "田中"]

        # インデックス2(3番目のシート)
        result = self.loader.load_from_excel_by_index(excel_path, sheet_index=2)
        assert result["sheet_name"] == "Data Sheet"
        assert result["data"][0] == ["Widget", "500", "100"]

    def test_nonexistent_sheet_name_error(self):
        """存在しないシート名指定時のエラーテスト(未実装なので失敗する)。"""
        excel_path = self.create_multi_sheet_excel()

        with pytest.raises(ValueError, match="Sheet 'NonExistentSheet' not found"):
            self.loader.load_from_excel(excel_path, sheet_name="NonExistentSheet")

    def test_invalid_sheet_index_error(self):
        """無効なシートインデックス指定時のエラーテスト(未実装なので失敗する)。"""
        excel_path = self.create_multi_sheet_excel()

        # 範囲外のインデックス
        with pytest.raises(ValueError, match="Sheet index 10 is out of range"):
            self.loader.load_from_excel_by_index(excel_path, sheet_index=10)

        # 負のインデックス
        with pytest.raises(ValueError, match="Sheet index must be non-negative"):
            self.loader.load_from_excel_by_index(excel_path, sheet_index=-1)

    def test_directive_sheet_option(self):
        """JsonTableDirectiveの:sheet:オプションテスト(未実装なので失敗する)。"""
        excel_path = self.create_multi_sheet_excel()

        # モックSphinx環境
        class MockConfig:
            jsontable_max_rows = 10000

        class MockEnv:
            def __init__(self, srcdir):
                self.srcdir = srcdir
                self.config = MockConfig()

        MockEnv(self.temp_dir)

        with docutils_namespace():
            # シート名指定
            mock_state_machine, mock_state = create_mock_state_machine(self.temp_dir)

            directive = JsonTableDirective(
                name="jsontable",
                arguments=[Path(excel_path).name],
                options={"header": True, "sheet": "営業データ"},
                content=[],
                lineno=1,
                content_offset=0,
                block_text="",
                state=mock_state,
                state_machine=mock_state_machine,
            )
            directive.excel_loader = ExcelDataLoader(self.temp_dir)

            json_data = directive._load_json_data()

            # 営業データシートのデータが取得されることを確認
            assert len(json_data) == 2
            assert json_data[0]["商品"] == "商品A"
            assert json_data[1]["商品"] == "商品B"

    def test_directive_sheet_index_option(self):
        """JsonTableDirectiveのsheet-indexオプションテスト(未実装なので失敗する)。"""
        excel_path = self.create_multi_sheet_excel()

        class MockConfig:
            jsontable_max_rows = 10000

        class MockEnv:
            def __init__(self, srcdir):
                self.srcdir = srcdir
                self.config = MockConfig()

        MockEnv(self.temp_dir)

        with docutils_namespace():
            # シートインデックス指定
            mock_state_machine, mock_state = create_mock_state_machine(self.temp_dir)

            directive = JsonTableDirective(
                name="jsontable",
                arguments=[Path(excel_path).name],
                options={"header": True, "sheet-index": 2},
                content=[],
                lineno=1,
                content_offset=0,
                block_text="",
                state=mock_state,
                state_machine=mock_state_machine,
            )
            directive.excel_loader = ExcelDataLoader(self.temp_dir)

            json_data = directive._load_json_data()

            # Data Sheetのデータが取得されることを確認
            assert len(json_data) == 2
            assert json_data[0]["Product"] == "Widget"
            assert json_data[1]["Product"] == "Gadget"

    def test_directive_sheet_option_priority(self):
        """sheet名とsheet-indexの両方が指定された場合の優先度テスト(未実装なので失敗する)。"""
        excel_path = self.create_multi_sheet_excel()

        class MockConfig:
            jsontable_max_rows = 10000

        class MockEnv:
            def __init__(self, srcdir):
                self.srcdir = srcdir
                self.config = MockConfig()

        MockEnv(self.temp_dir)

        with docutils_namespace():
            # sheet名とsheet-indexの両方を指定(sheet名が優先されるべき)
            mock_state_machine, mock_state = create_mock_state_machine(self.temp_dir)

            directive = JsonTableDirective(
                name="jsontable",
                arguments=[Path(excel_path).name],
                options={"header": True, "sheet": "営業データ", "sheet-index": 2},
                content=[],
                lineno=1,
                content_offset=0,
                block_text="",
                state=mock_state,
                state_machine=mock_state_machine,
            )
            directive.excel_loader = ExcelDataLoader(self.temp_dir)

            json_data = directive._load_json_data()

            # sheet名(営業データ)が優先されることを確認
            assert len(json_data) == 2
            assert json_data[0]["商品"] == "商品A"


if __name__ == "__main__":
    # スタンドアロンテスト実行
    pytest.main([__file__, "-v"])
