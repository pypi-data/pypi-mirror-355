"""Phase 2: Range Specification機能の簡略化されたテスト.

Task 2.2: `:range:` オプション実装の基本確認テスト
"""

import pytest


def test_range_functionality_implemented():
    """Range機能が実装済みであることを確認するテスト。"""

    # ExcelDataLoaderをインポートして実装済みメソッドをチェック
    try:
        from sphinxcontrib.jsontable.excel_data_loader import ExcelDataLoader

        loader = ExcelDataLoader()

        # load_from_excel_with_range メソッドが存在することを確認
        assert hasattr(loader, "load_from_excel_with_range"), (
            "load_from_excel_with_range method should exist (implemented)"
        )

        # _parse_range_specification メソッドが存在することを確認
        assert hasattr(loader, "_parse_range_specification"), (
            "_parse_range_specification method should exist (implemented)"
        )

        print("✅ Range Specification機能は実装済み")

    except ImportError as e:
        pytest.fail(f"Excel support should be available: {e}")


def test_directive_range_option_implemented():
    """JsonTableDirectiveで:range:オプションが実装済みであることを確認。"""

    try:
        from sphinxcontrib.jsontable.directives import JsonTableDirective

        # option_specに'range'が存在することを確認
        assert "range" in JsonTableDirective.option_spec, (
            "Range option should exist (implemented)"
        )

        print("✅ :range:オプションは実装済み")

    except ImportError as e:
        pytest.fail(f"Excel support should be available: {e}")


if __name__ == "__main__":
    test_range_functionality_implemented()
    test_directive_range_option_implemented()
    print("✅ Range Specification機能実装確認完了")
