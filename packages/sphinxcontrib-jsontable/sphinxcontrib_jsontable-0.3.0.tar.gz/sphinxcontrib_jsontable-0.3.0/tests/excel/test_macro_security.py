"""マクロセキュリティ機能のテスト."""

import shutil
import tempfile
import warnings
from pathlib import Path

import pytest
from openpyxl import Workbook

# Excel対応がある場合のみテストを実行
try:
    from sphinxcontrib.jsontable.excel_data_loader import ExcelDataLoader

    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


@pytest.mark.skipif(not EXCEL_AVAILABLE, reason="Excel support not available")
class TestMacroSecurity:
    """マクロセキュリティ機能のテスト."""

    def setup_method(self):
        """各テストメソッドの前に実行される."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """各テストメソッドの後に実行される."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_normal_excel(self, filename: str = "normal.xlsx") -> str:
        """通常のExcelファイルを作成."""
        file_path = str(Path(self.temp_dir) / filename)

        wb = Workbook()
        ws = wb.active
        ws["A1"] = "Header1"
        ws["B1"] = "Header2"
        ws["A2"] = "Data1"
        ws["B2"] = "Data2"

        wb.save(file_path)
        return file_path

    def create_macro_file_by_extension(self, filename: str = "macro.xlsm") -> str:
        """マクロ有効拡張子のファイルを作成（実際のマクロは含まない）."""
        file_path = str(Path(self.temp_dir) / filename)

        wb = Workbook()
        ws = wb.active
        ws["A1"] = "Header1"
        ws["B1"] = "Header2"
        ws["A2"] = "Data1"
        ws["B2"] = "Data2"

        wb.save(file_path)
        return file_path

    def test_strict_mode_blocks_macro_extension(self):
        """strictモードでマクロ拡張子ファイルをブロックするテスト."""
        macro_file = self.create_macro_file_by_extension("test.xlsm")
        loader = ExcelDataLoader(self.temp_dir, macro_security="strict")

        with pytest.raises(
            ValueError, match="Macro-enabled Excel file blocked for security"
        ):
            loader.validate_excel_file(macro_file)

    def test_warn_mode_generates_warning(self):
        """warnモードでマクロファイルに警告を発するテスト."""
        macro_file = self.create_macro_file_by_extension("test.xlsm")
        loader = ExcelDataLoader(self.temp_dir, macro_security="warn")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            loader.validate_excel_file(macro_file)

            assert len(w) == 1
            assert "Security Warning" in str(w[0].message)
            assert "Macro-enabled Excel file detected" in str(w[0].message)

    def test_allow_mode_permits_macro_files(self):
        """allowモードでマクロファイルを許可するテスト."""
        macro_file = self.create_macro_file_by_extension("test.xlsm")
        loader = ExcelDataLoader(self.temp_dir, macro_security="allow")

        # 例外や警告が発生しないことを確認
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # 警告を例外として扱う
            result = loader.validate_excel_file(macro_file)
            assert result is True

    def test_normal_file_not_affected(self):
        """通常のExcelファイルが影響されないテスト."""
        normal_file = self.create_normal_excel("normal.xlsx")

        # 全てのセキュリティレベルで通常ファイルは問題なし
        for security_level in ["strict", "warn", "allow"]:
            loader = ExcelDataLoader(self.temp_dir, macro_security=security_level)

            with warnings.catch_warnings():
                warnings.simplefilter("error")
                result = loader.validate_excel_file(normal_file)
                assert result is True

    def test_default_security_level_is_warn(self):
        """デフォルトのセキュリティレベルがwarnであることを確認."""
        loader = ExcelDataLoader(self.temp_dir)
        assert loader.macro_security == "warn"

    def test_macro_security_in_load_methods(self):
        """読み込みメソッドでマクロセキュリティが適用されることを確認."""
        macro_file = self.create_macro_file_by_extension("test.xlsm")
        loader = ExcelDataLoader(self.temp_dir, macro_security="strict")

        # load_from_excel でもマクロセキュリティが適用される
        with pytest.raises(
            ValueError, match="Macro-enabled Excel file blocked for security"
        ):
            loader.load_from_excel(macro_file)

    def test_invalid_security_level_handling(self):
        """無効なセキュリティレベル指定時のテスト."""
        # 無効なセキュリティレベルでも初期化は成功（実行時エラーで処理）
        loader = ExcelDataLoader(self.temp_dir, macro_security="invalid")
        assert loader.macro_security == "invalid"

        # ただし、マクロファイル処理時は警告されない（allow扱い）
        macro_file = self.create_macro_file_by_extension("test.xlsm")
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            result = loader.validate_excel_file(macro_file)
            assert result is True

    def test_macro_detection_error_handling(self):
        """マクロ検出時のエラーハンドリングテスト."""
        normal_file = self.create_normal_excel("normal.xlsx")
        loader = ExcelDataLoader(self.temp_dir, macro_security="strict")

        # 通常ファイルではマクロ検出エラーが無視される
        result = loader.validate_excel_file(normal_file)
        assert result is True

    def test_supported_macro_extensions(self):
        """サポートされるマクロ拡張子のテスト."""
        loader = ExcelDataLoader(self.temp_dir)

        # .xlsm と .xltm がマクロ有効拡張子として認識される
        assert ".xlsm" in loader.MACRO_ENABLED_EXTENSIONS
        assert ".xltm" in loader.MACRO_ENABLED_EXTENSIONS
        assert ".xlsx" not in loader.MACRO_ENABLED_EXTENSIONS
