#!/usr/bin/env python3
"""
V5統合システム単体テスト
個別コンポーネントの分離テスト
"""

import unittest
import sys
import os

# パス設定
sys.path.insert(0, '/workspace')

class TestV5UnifiedSystem(unittest.TestCase):
    """V5統合PDF表示システム単体テスト"""

    def setUp(self):
        """テスト前準備"""
        self.test_pdf_data = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000079 00000 n \n0000000173 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n301\n%%EOF'

    def test_v5_import(self):
        """V5インポートテスト"""
        try:
            from app.flet_ui.shared.pdf_large_preview_unified import PDFPreviewV5, create_pdf_preview_v5
            self.assertTrue(True, "V5インポート成功")
        except Exception as e:
            self.fail(f"V5インポート失敗: {e}")

    def test_v5_initialization(self):
        """V5初期化テスト"""
        try:
            from app.flet_ui.shared.pdf_large_preview_unified import PDFPreviewV5
            
            # ページなしで初期化
            preview = PDFPreviewV5(page=None)
            
            # 基本属性確認
            self.assertIsNone(preview._file_path)
            self.assertIsNone(preview._file_size)
            self.assertIsNone(preview._current_strategy)
            
            # 状態確認
            self.assertIsNone(preview._v1_component)
            self.assertIsNone(preview._v4_component)
            
        except Exception as e:
            self.fail(f"V5初期化失敗: {e}")

    def test_v5_file_info(self):
        """V5ファイル情報取得テスト"""
        try:
            from app.flet_ui.shared.pdf_large_preview_unified import PDFPreviewV5
            
            preview = PDFPreviewV5(page=None)
            info = preview.get_file_info()
            
            # 基本情報構造確認
            self.assertIn('file_path', info)
            self.assertIn('file_size', info)
            self.assertIn('strategy', info)
            self.assertIn('threshold_mb', info)
            
            # 閾値確認
            self.assertEqual(info['threshold_mb'], 1.2)
            
        except Exception as e:
            self.fail(f"V5ファイル情報取得失敗: {e}")

    def test_v5_clear_preview_safe(self):
        """V5クリア処理安全テスト（ページなし）"""
        try:
            from app.flet_ui.shared.pdf_large_preview_unified import PDFPreviewV5
            
            preview = PDFPreviewV5(page=None)
            
            # ページなしでクリア（エラーが出ないことを確認）
            preview.clear_preview()
            
            # 状態確認
            self.assertIsNone(preview._file_path)
            self.assertIsNone(preview._current_strategy)
            
        except Exception as e:
            self.fail(f"V5クリア処理失敗: {e}")

    def test_v5_size_threshold(self):
        """V5サイズ閾値テスト"""
        try:
            from app.flet_ui.shared.pdf_large_preview_unified import SIZE_THRESHOLD_BYTES
            
            # 1.2MB = 1,258,291バイト確認
            expected_bytes = int(1.2 * 1024 * 1024)
            self.assertEqual(SIZE_THRESHOLD_BYTES, expected_bytes)
            
        except Exception as e:
            self.fail(f"V5サイズ閾値テスト失敗: {e}")


class TestTabCComponent(unittest.TestCase):
    """tab_cコンポーネント単体テスト"""

    def test_tab_c_import(self):
        """tab_cインポートテスト"""
        try:
            from app.flet_ui.arrangement_test.tab_c.body import TabC
            self.assertTrue(True, "tab_cインポート成功")
        except Exception as e:
            self.fail(f"tab_cインポート失敗: {e}")

    def test_tab_c_initialization(self):
        """tab_c初期化テスト"""
        try:
            from app.flet_ui.arrangement_test.tab_c.body import TabC
            
            tab_c = TabC()
            
            # 基本属性確認
            self.assertEqual(tab_c.current_status, "待機中")
            self.assertEqual(tab_c.log_messages, [])
            
        except Exception as e:
            self.fail(f"tab_c初期化失敗: {e}")

    def test_tab_c_log_methods(self):
        """tab_cログメソッドテスト"""
        try:
            from app.flet_ui.arrangement_test.tab_c.body import TabC
            
            tab_c = TabC()
            
            # create_content呼び出し（UI初期化）
            content = tab_c.create_content(page=None)
            
            # ログ追加テスト（UI初期化後）
            tab_c._add_log("テストメッセージ")
            
            # ログ確認
            self.assertGreater(len(tab_c.log_messages), 0)
            
            # ステータス更新テスト
            tab_c._update_status("テスト状態")
            self.assertEqual(tab_c.current_status, "テスト状態")
            
        except Exception as e:
            self.fail(f"tab_cログメソッドテスト失敗: {e}")


if __name__ == '__main__':
    # テスト実行
    unittest.main(verbosity=2)
