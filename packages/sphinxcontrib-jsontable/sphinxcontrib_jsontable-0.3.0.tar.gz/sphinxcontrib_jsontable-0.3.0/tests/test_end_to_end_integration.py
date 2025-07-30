"""Task 4.4: End-to-End Integration Testing.

実際のSphinx環境を使用した包括的な統合テスト
- 実際のドキュメントビルド
- Excel/JSON機能の統合動作確認
- 互換性テスト
"""

import shutil
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from sphinx.application import Sphinx
from sphinx.util.docutils import docutils_namespace


class TestEndToEndIntegration:
    """End-to-End統合テスト."""

    def setup_method(self):
        """各テストメソッドの前に実行される."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.src_dir = self.temp_dir / "source"
        self.build_dir = self.temp_dir / "build"
        self.doctree_dir = self.temp_dir / "doctrees"

        # ディレクトリ作成
        self.src_dir.mkdir(parents=True)
        self.build_dir.mkdir(parents=True)
        self.doctree_dir.mkdir(parents=True)

        # データディレクトリ作成
        self.data_dir = self.src_dir / "data"
        self.data_dir.mkdir()

    def teardown_method(self):
        """各テストメソッドの後に実行される."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_conf_py(self) -> Path:
        """conf.pyファイルを作成."""
        conf_content = """
extensions = ['sphinxcontrib.jsontable']

master_doc = 'index'
source_suffix = '.rst'

# HTML出力設定
html_theme = 'default'
html_static_path = []

# jsontable設定
jsontable_max_rows = 10000
"""
        conf_path = self.src_dir / "conf.py"
        conf_path.write_text(conf_content, encoding="utf-8")
        return conf_path

    def create_test_json(self, filename: str, data: dict) -> Path:
        """テスト用JSONファイルを作成."""
        import json

        json_path = self.data_dir / filename
        json_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return json_path

    def create_test_excel(
        self, filename: str, data: list, sheet_name: str = "Sheet1"
    ) -> Path:
        """テスト用Excelファイルを作成."""
        excel_path = self.data_dir / filename

        # DataFrameを作成してExcelに保存
        if data and isinstance(data[0], list):
            # 2D array形式
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
            else:
                df = pd.DataFrame(data)
        else:
            # dict形式
            df = pd.DataFrame(data)

        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        return excel_path

    def build_docs(self, rst_content: str) -> tuple[bool, str]:
        """ドキュメントをビルドして結果を返す."""
        # index.rstファイル作成
        index_path = self.src_dir / "index.rst"
        index_path.write_text(rst_content, encoding="utf-8")

        # conf.py作成
        self.create_conf_py()

        try:
            with docutils_namespace():
                app = Sphinx(
                    srcdir=str(self.src_dir),
                    confdir=str(self.src_dir),
                    outdir=str(self.build_dir),
                    doctreedir=str(self.doctree_dir),
                    buildername="html",
                )
                app.build()

            # ビルド成功の確認
            index_html = self.build_dir / "index.html"
            if index_html.exists():
                return True, index_html.read_text(encoding="utf-8")
            else:
                return False, "HTML file not generated"

        except Exception as e:
            return False, str(e)

    def test_json_basic_integration(self):
        """JSON基本機能の統合テスト."""
        # テストデータ作成
        test_data = [
            {"name": "Alice", "age": 25, "city": "Tokyo"},
            {"name": "Bob", "age": 30, "city": "Osaka"},
            {"name": "Charlie", "age": 35, "city": "Kyoto"},
        ]
        self.create_test_json("users.json", test_data)

        # RSTコンテンツ作成
        rst_content = """
Test JSON Integration
====================

.. jsontable:: data/users.json
   :header:
"""

        # ビルド実行
        success, content = self.build_docs(rst_content)

        # 検証
        assert success, f"Build failed: {content}"
        assert "Alice" in content, "JSON data not rendered"
        assert "Tokyo" in content, "JSON data not rendered"
        assert "<table" in content, "Table not generated"
        assert "<th" in content, "Header not generated"

    def test_excel_basic_integration(self):
        """Excel基本機能の統合テスト."""
        # テストデータ作成
        test_data = [
            ["Name", "Age", "City"],
            ["Alice", 25, "Tokyo"],
            ["Bob", 30, "Osaka"],
            ["Charlie", 35, "Kyoto"],
        ]
        excel_file = self.create_test_excel("employees.xlsx", test_data)

        # デバッグ: ファイルが実際に作成されたか確認
        assert excel_file.exists(), f"Excel file not created at: {excel_file}"
        print(f"DEBUG: Excel file created at: {excel_file}")
        print(f"DEBUG: Data directory: {self.data_dir}")
        print(f"DEBUG: Source directory: {self.src_dir}")

        # RSTコンテンツ作成
        rst_content = """
Test Excel Integration
======================

.. jsontable:: data/employees.xlsx
   :header:
"""

        # ビルド実行
        success, content = self.build_docs(rst_content)

        # デバッグ情報出力
        print(f"DEBUG: Build success: {success}")
        if not success:
            print(f"DEBUG: Error content: {content}")

        # 検証
        assert success, f"Build failed: {content}"
        assert "Alice" in content, "Excel data not rendered"
        assert "Tokyo" in content, "Excel data not rendered"
        assert "<table" in content, "Table not generated"
        assert "<th" in content, "Header not generated"

    def test_excel_sheet_selection_integration(self):
        """Excelシート選択機能の統合テスト."""
        # 複数シートのExcelファイル作成
        excel_path = self.data_dir / "multi_sheet.xlsx"

        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            # Sheet1
            df1 = pd.DataFrame([["Product", "Price"], ["Apple", 100], ["Banana", 80]])
            df1.to_excel(writer, sheet_name="Products", index=False, header=False)

            # Sheet2
            df2 = pd.DataFrame(
                [["Employee", "Department"], ["Alice", "Engineering"], ["Bob", "Sales"]]
            )
            df2.to_excel(writer, sheet_name="Employees", index=False, header=False)

        # RSTコンテンツ作成
        rst_content = """
Test Excel Sheet Selection
==========================

Products Sheet:

.. jsontable:: data/multi_sheet.xlsx
   :header:
   :sheet: Products

Employees Sheet:

.. jsontable:: data/multi_sheet.xlsx
   :header:
   :sheet: Employees
"""

        # ビルド実行
        success, content = self.build_docs(rst_content)

        # 検証
        assert success, f"Build failed: {content}"
        assert "Apple" in content, "Products sheet data not rendered"
        assert "Alice" in content, "Employees sheet data not rendered"
        assert "Engineering" in content, "Department data not rendered"

    def test_excel_range_specification_integration(self):
        """Excel範囲指定機能の統合テスト."""
        # 大きなデータセットを含むExcelファイル作成
        data = []
        for i in range(20):
            data.append([f"Item{i}", f"Value{i}", f"Category{i % 3}"])

        # ヘッダー付きでExcel作成
        df = pd.DataFrame(data, columns=["Item", "Value", "Category"])
        excel_path = self.data_dir / "large_data.xlsx"
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)

        # RSTコンテンツ作成(範囲指定)
        rst_content = """
Test Excel Range Specification
==============================

First 5 rows only:

.. jsontable:: data/large_data.xlsx
   :header:
   :range: A1:C6
"""

        # ビルド実行
        success, content = self.build_docs(rst_content)

        # 検証
        assert success, f"Build failed: {content}"
        assert "Item0" in content, "First row not included"
        assert "Item4" in content, "Fifth row not included"
        assert "Item10" not in content, "Range specification not working"

    def test_backward_compatibility_integration(self):
        """後方互換性の統合テスト."""
        # JSON機能(既存)
        test_data = [{"id": 1, "name": "Test User"}, {"id": 2, "name": "Another User"}]
        self.create_test_json("legacy.json", test_data)

        # RSTコンテンツ(従来の記法)
        rst_content = """
Test Backward Compatibility
===========================

Legacy JSON directive:

.. jsontable:: data/legacy.json
   :header:
   :limit: 10
"""

        # ビルド実行
        success, content = self.build_docs(rst_content)

        # 検証
        assert success, f"Build failed: {content}"
        assert "Test User" in content, "Legacy JSON not working"
        assert "<table" in content, "Table not generated"

    def test_error_handling_integration(self):
        """エラーハンドリングの統合テスト."""
        # 存在しないファイルを指定
        rst_content = """
Test Error Handling
==================

Non-existent file:

.. jsontable:: data/nonexistent.json
   :header:
"""

        # ビルド実行
        success, content = self.build_docs(rst_content)

        # エラーが適切に処理されることを確認
        # (ビルドは失敗してもよいが、クラッシュしてはいけない)
        if not success:
            assert "not found" in content.lower() or "error" in content.lower()
        else:
            # ビルドが成功した場合、エラーメッセージが含まれているはず
            assert "error" in content.lower() or "not found" in content.lower()

    def test_performance_integration(self):
        """パフォーマンス統合テスト."""
        # 大きなデータセットを作成
        large_data = []
        for i in range(1000):  # 1000行のデータ
            large_data.append(
                {
                    "id": i,
                    "name": f"User{i}",
                    "email": f"user{i}@example.com",
                    "department": f"Dept{i % 10}",
                }
            )

        self.create_test_json("large.json", large_data)

        # RSTコンテンツ(制限付き)
        rst_content = """
Test Performance
===============

Large dataset with limit:

.. jsontable:: data/large.json
   :header:
   :limit: 50
"""

        # ビルド実行(時間測定)
        import time

        start_time = time.time()
        success, content = self.build_docs(rst_content)
        build_time = time.time() - start_time

        # 検証
        assert success, f"Build failed: {content}"
        assert "User0" in content, "Data not rendered"
        assert build_time < 30, f"Build too slow: {build_time}s"  # 30秒以内

        # 制限が適用されていることを確認
        user_count = content.count("User")
        assert user_count <= 60, f"Too many rows rendered: {user_count}"


@pytest.mark.integration
class TestSphinxCompatibility:
    """Sphinx互換性テスト."""

    def test_sphinx_version_compatibility(self):
        """Sphinx バージョン互換性テスト."""
        # 現在のSphinxバージョンを確認
        import sphinx

        sphinx_version = sphinx.__version__

        # メジャーバージョンが3.0以上であることを確認
        major_version = int(sphinx_version.split(".")[0])
        assert major_version >= 3, f"Unsupported Sphinx version: {sphinx_version}"

    def test_python_version_compatibility(self):
        """Python バージョン互換性テスト."""
        import sys

        python_version = sys.version_info

        # Python 3.10以上であることを確認
        assert python_version >= (3, 10), (
            f"Unsupported Python version: {python_version}"
        )

    def test_required_dependencies(self):
        """必要な依存関係のテスト."""
        # 必須依存関係をインポートテスト
        import importlib.util

        required_modules = ["docutils", "openpyxl", "pandas", "sphinx"]
        for module_name in required_modules:
            if importlib.util.find_spec(module_name) is None:
                pytest.fail(f"Required dependency missing: {module_name}")
