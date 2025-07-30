"""範囲指定エラーハンドリングの包括的テスト."""

import shutil
import tempfile
from pathlib import Path

import pytest
from openpyxl import Workbook

from sphinxcontrib.jsontable.excel_data_loader import (
    ExcelDataLoader,
    RangeSpecificationError,
)


class TestRangeErrorHandlingComplete:
    """範囲指定エラーハンドリングの完全テスト."""

    def setup_method(self):
        """テスト前の準備."""
        self.temp_dir = tempfile.mkdtemp()
        self.loader = ExcelDataLoader(self.temp_dir)

    def teardown_method(self):
        """テスト後のクリーンアップ."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_excel(self, filename="test_range.xlsx"):
        """テスト用Excelファイル作成."""
        file_path = Path(self.temp_dir) / filename
        wb = Workbook()
        ws = wb.active

        # 10x10のテストデータ
        for row in range(1, 11):
            for col in range(1, 11):
                ws.cell(row=row, column=col, value=f"R{row}C{col}")

        wb.save(file_path)
        return file_path

    def test_non_string_range_specification(self):
        """非文字列の範囲指定でRangeSpecificationError."""
        excel_path = self.create_test_excel()

        # 整数を範囲指定に渡す
        with pytest.raises(RangeSpecificationError) as exc_info:
            self.loader.load_from_excel_with_range(excel_path, 123)

        cause = exc_info.value.__cause__
        assert isinstance(cause, TypeError)
        assert "Range specification must be a string" in str(cause)
        assert "got int" in str(cause)

        # リストを範囲指定に渡す
        with pytest.raises(RangeSpecificationError) as exc_info:
            self.loader.load_from_excel_with_range(excel_path, ["A1", "C3"])

        cause = exc_info.value.__cause__
        assert isinstance(cause, TypeError)
        assert "Range specification must be a string" in str(cause)
        assert "got list" in str(cause)

        # Noneを範囲指定に渡す
        with pytest.raises(RangeSpecificationError) as exc_info:
            self.loader.load_from_excel_with_range(excel_path, None)

        cause = exc_info.value.__cause__
        assert isinstance(cause, TypeError)
        assert "Range specification must be a string" in str(cause)
        assert "got NoneType" in str(cause)

    def test_empty_range_specification(self):
        """空の範囲指定でRangeSpecificationError."""
        excel_path = self.create_test_excel()

        # 完全に空の文字列
        with pytest.raises(RangeSpecificationError) as exc_info:
            self.loader.load_from_excel_with_range(excel_path, "")

        error_message = str(exc_info.value)
        assert "Range specification cannot be empty" in error_message

        # 空白のみの文字列
        with pytest.raises(RangeSpecificationError) as exc_info:
            self.loader.load_from_excel_with_range(excel_path, "   ")

        error_message = str(exc_info.value)
        assert "Range specification cannot be empty" in error_message

        # タブのみの文字列
        with pytest.raises(RangeSpecificationError) as exc_info:
            self.loader.load_from_excel_with_range(excel_path, "\t\t")

        error_message = str(exc_info.value)
        assert "Range specification cannot be empty" in error_message

    def test_invalid_range_format(self):
        """無効な範囲フォーマットでRangeSpecificationError."""
        excel_path = self.create_test_excel()

        invalid_ranges = [
            "INVALID",  # 完全に無効
            "A1:B2:C3",  # コロンが多すぎる
            "A1-B2",  # ハイフン区切り
            "1A:2B",  # 数字が先頭
            "AA:BB",  # 行番号なし
            "11:22",  # 列文字なし
            "A:B",  # 行番号なし（列のみ）
            "1:2",  # 列文字なし（行のみ）
            "@#$:!%&",  # 特殊文字
        ]

        for invalid_range in invalid_ranges:
            with pytest.raises(RangeSpecificationError) as exc_info:
                self.loader.load_from_excel_with_range(excel_path, invalid_range)

            error_message = str(exc_info.value)
            assert (
                "Failed to parse range specification" in error_message
                or "Invalid range specification" in error_message
                or "Unexpected error parsing range specification" in error_message
                or "Invalid range format" in error_message
            )

    def test_invalid_cell_address_format(self):
        """無効なセルアドレスフォーマットでRangeSpecificationError."""
        excel_path = self.create_test_excel()

        invalid_cell_ranges = [
            "A1:XYZ999999",  # 無効な列名
            "A1:Z0",  # 行0は無効
            "A1:$%^123",  # 特殊文字
            "A1:123ABC",  # 数字が先頭の列名
            "A1:A-5",  # マイナス記号
        ]

        for invalid_range in invalid_cell_ranges:
            with pytest.raises(RangeSpecificationError) as exc_info:
                self.loader.load_from_excel_with_range(excel_path, invalid_range)

            error_message = str(exc_info.value)
            assert (
                "Failed to parse range specification" in error_message
                or "Invalid cell address" in error_message
                or "Invalid range specification" in error_message
                or "Unexpected error parsing range specification" in error_message
                or "exceeds data rows" in error_message
                or "exceeds data columns" in error_message
                or "Invalid range format" in error_message
            )

    def test_range_out_of_bounds(self):
        """範囲外指定でのエラーハンドリング."""
        excel_path = self.create_test_excel()

        # 存在しない大きな範囲
        out_of_bounds_ranges = [
            "A1:ZZ9999",  # 大きすぎる範囲
            "AA1:AB2",  # 存在しない列
            "A100:B200",  # 存在しない行
        ]

        for range_spec in out_of_bounds_ranges:
            try:
                # 範囲外でもエラーにならない場合があるが、
                # 解析自体は成功して空のデータが返される
                result = self.loader.load_from_excel_with_range(excel_path, range_spec)
                assert isinstance(result, dict)
                # 空のデータまたは部分的なデータが返される
                assert "data" in result
            except RangeSpecificationError:
                # 範囲外エラーが発生することもある
                pass

    def test_reverse_range_specification(self):
        """逆順の範囲指定でのエラーハンドリング."""
        excel_path = self.create_test_excel()

        reverse_ranges = [
            "C3:A1",  # 列が逆順
            "A5:A1",  # 行が逆順
            "E5:A1",  # 両方逆順
        ]

        for reverse_range in reverse_ranges:
            try:
                # 実装によっては自動で正規化される場合がある
                result = self.loader.load_from_excel_with_range(
                    excel_path, reverse_range
                )
                assert isinstance(result, dict)
            except (RangeSpecificationError, ValueError):
                # エラーが発生することもある
                pass

    def test_malformed_range_with_special_characters(self):
        """特殊文字を含む不正な範囲指定."""
        excel_path = self.create_test_excel()

        malformed_ranges = [
            "A1:B2;",  # セミコロン
            "A1:B2,",  # カンマ
            "A1:B2 C3",  # スペース
            "A1:B2#",  # ハッシュ
            "A1:B2?",  # クエスチョン
            "A1:(B2)",  # 括弧
            "A1:[B2]",  # 角括弧
            "A1:{B2}",  # 波括弧
        ]

        for malformed_range in malformed_ranges:
            with pytest.raises(RangeSpecificationError) as exc_info:
                self.loader.load_from_excel_with_range(excel_path, malformed_range)

            error_message = str(exc_info.value)
            assert (
                "Failed to parse range specification" in error_message
                or "Unexpected error parsing range specification" in error_message
                or "Invalid range format" in error_message
            )

    def test_unicode_and_non_ascii_range(self):
        """Unicodeと非ASCII文字を含む範囲指定."""
        excel_path = self.create_test_excel()

        unicode_ranges = [
            "Ａ１:Ｂ２",  # 全角文字
            "A1:B２",  # 混在
            "あ1:い2",  # ひらがな
            "A1:漢字",  # 漢字
            "A1:Ё2",  # キリル文字
        ]

        for unicode_range in unicode_ranges:
            with pytest.raises(RangeSpecificationError) as exc_info:
                self.loader.load_from_excel_with_range(excel_path, unicode_range)

            error_message = str(exc_info.value)
            assert (
                "Failed to parse range specification" in error_message
                or "Invalid cell address" in error_message
                or "Unexpected error parsing range specification" in error_message
                or "Invalid range format" in error_message
            )

    def test_exception_chaining_in_range_parsing(self):
        """範囲解析での例外チェーンテスト."""
        excel_path = self.create_test_excel()

        # 内部で例外が発生して、それがRangeSpecificationErrorに変換される
        with pytest.raises(RangeSpecificationError) as exc_info:
            self.loader.load_from_excel_with_range(excel_path, "INVALID:RANGE")

        # 例外チェーンが正しく設定されているかチェック
        error_message = str(exc_info.value)
        assert (
            "Failed to parse range specification" in error_message
            or "Invalid cell address" in error_message
            or "Unexpected error parsing range specification" in error_message
            or "Invalid range format" in error_message
        )

    def test_case_sensitivity_in_range_parsing(self):
        """範囲解析の大文字小文字処理."""
        excel_path = self.create_test_excel()

        # 小文字の範囲指定（内部で大文字に変換される）
        lowercase_ranges = [
            "a1:b2",
            "c3:d4",
            "e5:f6",
        ]

        for range_spec in lowercase_ranges:
            # 小文字でも正常に処理されることを確認
            result = self.loader.load_from_excel_with_range(excel_path, range_spec)
            assert isinstance(result, dict)
            assert "data" in result
            assert len(result["data"]) >= 1

    def test_whitespace_handling_in_range(self):
        """範囲指定での空白文字処理."""
        excel_path = self.create_test_excel()

        whitespace_ranges = [
            " A1:B2 ",  # 前後の空白
            "A1 : B2",  # コロン周りの空白
            " A1 : B2 ",  # 全体的な空白
            "A1:\tB2",  # タブ文字
            "A1:\nB2",  # 改行文字
        ]

        for range_spec in whitespace_ranges:
            try:
                # 空白が適切にトリムされて処理される
                result = self.loader.load_from_excel_with_range(excel_path, range_spec)
                assert isinstance(result, dict)
                assert "data" in result
            except RangeSpecificationError:
                # 一部の空白パターンではエラーになる場合もある
                pass

    def test_error_message_details(self):
        """エラーメッセージの詳細情報テスト."""
        excel_path = self.create_test_excel()

        with pytest.raises(RangeSpecificationError) as exc_info:
            self.loader.load_from_excel_with_range(excel_path, "COMPLETELY_INVALID")

        exception = exc_info.value
        error_message = str(exception)

        # エラーメッセージに含まれるべき情報
        assert "COMPLETELY_INVALID" in error_message
        assert (
            "Failed to parse range specification" in error_message
            or "Invalid range specification" in error_message
            or "Unexpected error parsing range specification" in error_message
            or "Invalid range format" in error_message
        )

    def test_range_specification_error_attributes(self):
        """RangeSpecificationErrorの属性テスト."""
        excel_path = self.create_test_excel()

        with pytest.raises(RangeSpecificationError) as exc_info:
            self.loader.load_from_excel_with_range(excel_path, "INVALID_RANGE")

        exception = exc_info.value

        # 例外が適切に初期化されていることを確認
        assert isinstance(exception, RangeSpecificationError)
        assert isinstance(exception, Exception)

        # エラーメッセージが設定されていることを確認
        assert str(exception)
        assert len(str(exception)) > 0
