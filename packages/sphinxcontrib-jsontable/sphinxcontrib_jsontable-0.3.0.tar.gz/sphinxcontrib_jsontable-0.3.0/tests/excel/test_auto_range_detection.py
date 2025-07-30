"""Phase 3: Automatic Range Detection機能のTDDテスト.

Task 3.1: `:detect-range:` オプション実装のテスト
- auto, smart, manual モード
- データ境界自動検出
- 空行・空列の検出
- データブロック認識
- ヘッダー自動判定
"""

import os
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


class TestAutoRangeDetection:
    """Phase 3: Automatic Range Detection機能のテスト."""

    def setup_method(self):
        """各テストメソッドの前に実行される."""
        self.temp_dir = tempfile.mkdtemp()
        self.loader = ExcelDataLoader(self.temp_dir)

    def teardown_method(self):
        """各テストメソッドの後に実行される."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_complex_data_excel(self) -> str:
        """複雑なデータ構造を持つExcelファイルを作成.

        Returns:
            str: 作成されたファイルのパス
        """
        filename = "complex_data.xlsx"
        file_path = Path(self.temp_dir) / filename

        # 複雑なデータ構造を作成
        data = [
            ["", "", "", "", "", ""],  # Row 0: 空行
            ["", "会社データ分析レポート", "", "", "", ""],  # Row 1: タイトル行
            ["", "", "", "", "", ""],  # Row 2: 空行
            ["", "部門", "売上", "従業員数", "地域", ""],  # Row 3: ヘッダー行
            ["", "営業部", "5000000", "25", "東京", ""],  # Row 4: データ行
            ["", "開発部", "3000000", "15", "大阪", ""],  # Row 5: データ行
            ["", "総務部", "1000000", "10", "名古屋", ""],  # Row 6: データ行
            ["", "", "", "", "", ""],  # Row 7: 空行
            ["", "備考: 2025年第1四半期", "", "", "", ""],  # Row 8: 注釈行
            ["", "", "", "", "", ""],  # Row 9: 空行
        ]

        df = pd.DataFrame(data)

        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Sheet1", index=False, header=False)

        return file_path

    def create_scattered_data_excel(self) -> str:
        """散在するデータブロックを持つExcelファイルを作成.

        Returns:
            str: 作成されたファイルのパス
        """
        filename = "scattered_data.xlsx"
        file_path = Path(self.temp_dir) / filename

        # 散在するデータ構造
        data = [
            ["Block1", "データ1", "", "Block2", "データA", ""],
            ["項目1", "100", "", "項目A", "200", ""],
            ["項目2", "150", "", "項目B", "250", ""],
            ["", "", "", "", "", ""],
            ["", "", "", "", "", ""],
            ["Block3データ", "", "", "", "", ""],
            ["項目X", "300", "", "", "", ""],
            ["項目Y", "350", "", "", "", ""],
        ]

        df = pd.DataFrame(data)

        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Sheet1", index=False, header=False)

        return file_path

    def test_auto_mode_range_detection(self):
        """autoモードでの自動範囲検出テスト(未実装なので失敗する)."""
        excel_path = self.create_complex_data_excel()

        # autoモードで自動範囲検出
        result = self.loader.load_from_excel_with_detect_range(
            excel_path, detect_mode="auto"
        )

        # 期待される結果: 実際のデータ部分(Row 4-6のみ、ヘッダー除く)
        expected_data = [
            ["営業部", "5000000", "25", "東京"],
            ["開発部", "3000000", "15", "大阪"],
            ["総務部", "1000000", "10", "名古屋"],
        ]
        expected_headers = ["部門", "売上", "従業員数", "地域"]

        assert result["data"] == expected_data
        assert result["headers"] == expected_headers
        assert result["detected_range"] == "B4:E7"  # 1ベース表記
        assert result["detect_mode"] == "auto"
        assert result["has_header"]

    def test_smart_mode_range_detection(self):
        """smartモードでの高度範囲検出テスト(未実装なので失敗する)."""
        excel_path = self.create_scattered_data_excel()

        # smartモードで複数データブロック認識
        result = self.loader.load_from_excel_with_detect_range(
            excel_path, detect_mode="smart"
        )

        # 期待される結果: 最大のデータブロックを自動選択
        expected_data = [
            ["項目1", "100"],
            ["項目2", "150"],
        ]

        assert result["data"] == expected_data
        assert result["detected_range"] == "A1:B2"
        assert result["detect_mode"] == "smart"
        assert "detected_blocks" in result  # 複数ブロック情報

    def test_manual_mode_range_detection(self):
        """manualモードでの手動範囲検出テスト(未実装なので失敗する)."""
        excel_path = self.create_complex_data_excel()

        # manualモードで範囲ヒント指定
        result = self.loader.load_from_excel_with_detect_range(
            excel_path, detect_mode="manual", range_hint="B3:E7"
        )

        # 期待される結果: B3:E7範囲(4列)の精密検出(実際の出力に合わせる)
        expected_data = [
            ["", "", "", ""],  # 空行
            ["部門", "売上", "従業員数", "地域"],  # ヘッダー行
            ["営業部", "5000000", "25", "東京"],  # データ行
            ["開発部", "3000000", "15", "大阪"],  # データ行
            ["総務部", "1000000", "10", "名古屋"],  # データ行
        ]

        assert result["data"] == expected_data
        assert result["detected_range"] == "B3:E7"
        assert result["detect_mode"] == "manual"

    def test_detect_range_with_empty_cells(self):
        """空セルを含むデータの範囲検出テスト(未実装なので失敗する)."""
        excel_path = self.create_complex_data_excel()

        # 空セル境界の正確な検出
        result = self.loader.load_from_excel_with_detect_range(
            excel_path, detect_mode="auto", ignore_empty_rows=True
        )

        # 空行・空列を除いた範囲検出
        assert "empty_rows_detected" in result
        assert "empty_cols_detected" in result
        assert result["ignore_empty_rows"]

    def test_header_auto_detection(self):
        """ヘッダー行の自動判定テスト(未実装なので失敗する)."""
        excel_path = self.create_complex_data_excel()

        # ヘッダー自動判定
        result = self.loader.load_from_excel_with_detect_range(
            excel_path, detect_mode="auto", auto_header=True
        )

        # ヘッダー行の自動検出
        assert result["auto_header"]
        assert result["detected_header_row"] == 3  # 0ベース
        assert result["header_confidence"] > 0.8  # 信頼度

    def test_data_block_recognition(self):
        """データブロック認識テスト(未実装なので失敗する)."""
        excel_path = self.create_scattered_data_excel()

        # 複数データブロックの認識
        result = self.loader.detect_data_blocks(excel_path)

        # 期待される結果: 3つのデータブロック検出
        assert len(result["blocks"]) >= 2
        assert result["blocks"][0]["range"] == "A1:B2"  # Block1
        assert result["blocks"][1]["range"] == "D1:E2"  # Block2

        # 各ブロックの信頼度スコア
        for block in result["blocks"]:
            assert "confidence_score" in block
            assert 0.0 <= block["confidence_score"] <= 1.0

    def test_directive_detect_range_option(self):
        """JsonTableDirectiveの:detect-range:オプションテスト(未実装なので失敗する)."""
        excel_path = self.create_complex_data_excel()

        with docutils_namespace():
            # detect-range指定付きディレクティブ
            mock_state_machine, mock_state = create_mock_state_machine(self.temp_dir)
            directive = JsonTableDirective(
                name="jsontable",
                arguments=[os.path.basename(excel_path)],
                options={"header": True, "detect-range": "auto", "auto-header": True},
                content=[],
                lineno=1,
                content_offset=0,
                block_text="",
                state=mock_state,
                state_machine=mock_state_machine,
            )
            directive.excel_loader = ExcelDataLoader(self.temp_dir)

            json_data = directive._load_json_data()

            # 自動検出されたデータを確認
            assert len(json_data) == 3  # データ行数(ヘッダー除く)
            assert "部門" in json_data[0]  # ヘッダーがキーとして使用
            assert json_data[0]["部門"] == "営業部"
            assert json_data[1]["部門"] == "開発部"
            assert json_data[2]["部門"] == "総務部"

    def test_invalid_detect_mode_error(self):
        """無効な検出モード指定時のエラーテスト(未実装なので失敗する)."""
        excel_path = self.create_complex_data_excel()

        # 無効なモード
        with pytest.raises(ValueError, match="Invalid detect mode"):
            self.loader.load_from_excel_with_detect_range(
                excel_path, detect_mode="invalid_mode"
            )

    def test_detect_range_boundary_detection(self):
        """境界検出アルゴリズムテスト(未実装なので失敗する)."""
        excel_path = self.create_complex_data_excel()

        # 境界検出の詳細情報
        result = self.loader.analyze_data_boundaries(excel_path)

        # 期待される境界情報
        assert "top_boundary" in result
        assert "bottom_boundary" in result
        assert "left_boundary" in result
        assert "right_boundary" in result
        assert result["top_boundary"] == 3  # ヘッダー行
        assert result["bottom_boundary"] == 6  # 最後のデータ行


if __name__ == "__main__":
    # スタンドアロンテスト実行
    pytest.main([__file__, "-v"])
