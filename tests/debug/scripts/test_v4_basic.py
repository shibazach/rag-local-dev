#!/usr/bin/env python3
"""
V4システム基本動作テスト

テスト項目:
1. PyMuPDFレンダラー基本動作
2. V4サーバー起動・PDF登録・画像生成
3. V4 UI基本機能
4. パフォーマンス測定

実行: python test_v4_basic.py
"""

import sys
import time
import asyncio
import tempfile
from pathlib import Path

# プロジェクトルート追加
sys.path.append(str(Path(__file__).parent))

def create_test_pdf() -> bytes:
    """テスト用PDF生成"""
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
4 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
%%EOF"""

def test_pdf_renderer():
    """PDFレンダラー基本テスト"""
    print("🔍 V4 PDFレンダラー テスト開始...")
    
    try:
        from app.flet_ui.shared.pdf_page_renderer import (
            render_page_image, get_pdf_page_count, prefetch_pages
        )
        
        # テストPDF作成
        test_pdf_data = create_test_pdf()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(test_pdf_data)
            tmp_path = tmp.name
        
        print(f"📄 テストPDF作成: {tmp_path}")
        
        # ページ数確認
        page_count = get_pdf_page_count(tmp_path)
        print(f"📊 ページ数: {page_count}")
        assert page_count == 2, f"Expected 2 pages, got {page_count}"
        
        # ページレンダリングテスト
        print("🖼️ ページ0レンダリング...")
        start_time = time.time()
        image_data = render_page_image(tmp_path, 0, width=1200, dpr=1.0, format_type="png")
        render_time = time.time() - start_time
        
        print(f"✅ レンダリング完了: {len(image_data)} bytes in {render_time:.3f}s")
        assert len(image_data) > 1000, "Image data too small"
        
        # キャッシュテスト
        print("⚡ キャッシュテスト...")
        start_time = time.time()
        image_data2 = render_page_image(tmp_path, 0, width=1200, dpr=1.0, format_type="png")
        cache_time = time.time() - start_time
        
        speedup = render_time / cache_time if cache_time > 0 else float('inf')
        print(f"🚀 キャッシュ高速化: {speedup:.1f}x ({cache_time:.3f}s)")
        
        # 先読みテスト
        print("📖 先読みテスト...")
        prefetch_pages(tmp_path, 0, width=1200, dpr=1.0, range_size=1)
        time.sleep(1)  # 先読み完了待ち
        print("✅ 先読み完了")
        
        # クリーンアップ
        import os
        os.unlink(tmp_path)
        
        print("✅ PDFレンダラーテスト完了")
        return True
        
    except Exception as e:
        print(f"❌ PDFレンダラーテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_v4_server():
    """V4サーバーテスト"""
    print("\n🌐 V4サーバー テスト開始...")
    
    try:
        from app.flet_ui.shared.pdf_stream_server_v4 import PDFStreamServerV4
        
        # サーバー作成・起動
        server = PDFStreamServerV4(host="127.0.0.1", port=0)
        await server.start()
        
        print(f"🚀 サーバー起動: http://{server.host}:{server.actual_port}")
        
        # PDF登録
        test_pdf_data = create_test_pdf()
        pdf_url = await server.register_pdf_async("test_pdf", test_pdf_data)
        print(f"📄 PDF登録完了: {pdf_url}")
        
        # 画像URL生成
        image_url = server.get_image_url("test_pdf", 0, width=800, dpr=1.0, fmt="png")
        print(f"🖼️ 画像URL: {image_url}")
        
        # 情報URL生成
        info_url = server.get_info_url("test_pdf")
        print(f"📊 情報URL: {info_url}")
        
        # HTTP クライアントテスト
        import aiohttp
        async with aiohttp.ClientSession() as session:
            # ヘルスチェック
            health_url = f"http://{server.host}:{server.actual_port}/health"
            async with session.get(health_url) as resp:
                health_data = await resp.json()
                print(f"💚 ヘルス: {health_data['status']} (v{health_data['version']})")
            
            # PDF情報取得
            async with session.get(info_url) as resp:
                info_data = await resp.json()
                print(f"📋 PDF情報: {info_data['page_count']}ページ, {info_data['file_size']}bytes")
            
            # 画像取得テスト
            print("🖼️ 画像取得テスト...")
            start_time = time.time()
            async with session.get(image_url) as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                    load_time = time.time() - start_time
                    print(f"✅ 画像取得完了: {len(image_data)} bytes in {load_time:.3f}s")
                    assert len(image_data) > 1000, "Image data too small"
                else:
                    raise RuntimeError(f"Image request failed: {resp.status}")
        
        # サーバー停止
        await server.stop()
        print("🛑 サーバー停止完了")
        
        print("✅ V4サーバーテスト完了")
        return True
        
    except Exception as e:
        print(f"❌ V4サーバーテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_v4_ui():
    """V4 UI基本テスト（インスタンス作成のみ）"""
    print("\n🎨 V4 UI テスト開始...")
    
    try:
        from app.flet_ui.shared.pdf_large_preview_v4 import create_large_pdf_preview_v4
        
        # UI インスタンス作成
        ui_component = create_large_pdf_preview_v4()
        print("🎯 V4 UI インスタンス作成完了")
        
        # 状態確認
        state = ui_component.get_current_state()
        print(f"📊 初期状態: {state['state']} (ページ: {state['current_page']}/{state['total_pages']})")
        assert state['state'] == 'empty', f"Expected 'empty' state, got {state['state']}"
        
        print("✅ V4 UI テスト完了")
        return True
        
    except Exception as e:
        print(f"❌ V4 UI テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """メインテスト"""
    print("=" * 60)
    print("🚀 V4システム 統合テスト開始")
    print("=" * 60)
    
    test_results = []
    
    # 1. PDFレンダラーテスト
    result1 = test_pdf_renderer()
    test_results.append(("PDFレンダラー", result1))
    
    # 2. V4サーバーテスト
    result2 = await test_v4_server()
    test_results.append(("V4サーバー", result2))
    
    # 3. V4 UIテスト
    result3 = test_v4_ui()
    test_results.append(("V4 UI", result3))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    
    success_count = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            success_count += 1
    
    total_tests = len(test_results)
    print(f"\n🎯 成功: {success_count}/{total_tests} テスト")
    
    if success_count == total_tests:
        print("🎉 すべてのテストが成功しました！")
        print("🔥 V4画像変換システムは動作可能です")
    else:
        print("⚠️  一部のテストが失敗しました")
        print("🔧 エラーログを確認してください")
    
    return success_count == total_tests

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

