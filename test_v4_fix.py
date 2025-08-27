#!/usr/bin/env python3
"""
V4修正版動作確認テスト

修正項目:
1. ft.Image src=None 初期化 (真っ赤エラー修正)
2. asyncio.create_task() → page.run_task() (event loop エラー修正)  
3. 画像visibility制御改善
"""

import sys
import asyncio
import tempfile
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

def test_v4_ui_initialization():
    """V4 UI初期化テスト"""
    print("🎨 V4 UI初期化テスト...")
    
    try:
        from app.flet_ui.shared.pdf_large_preview_v4 import create_large_pdf_preview_v4
        
        # UI作成
        ui = create_large_pdf_preview_v4()
        print("✅ V4 UIインスタンス作成成功")
        
        # 画像コンポーネント確認
        assert ui._image_display.src is None, f"Expected None, got {ui._image_display.src}"
        assert ui._image_display.visible is False, f"Expected False, got {ui._image_display.visible}"
        print("✅ 画像コンポーネント初期化確認")
        
        # 状態確認  
        state = ui.get_current_state()
        assert state['state'] == 'empty', f"Expected 'empty', got {state['state']}"
        print("✅ 初期状態確認")
        
        return True
        
    except Exception as e:
        print(f"❌ V4 UI初期化エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_v4_server_image():
    """V4サーバー画像生成テスト"""
    print("\n🌐 V4サーバー画像生成テスト...")
    
    try:
        from app.flet_ui.shared.pdf_stream_server_v4 import PDFStreamServerV4
        
        # テスト用PDF
        test_pdf = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj  
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj
%%EOF"""
        
        # サーバー起動
        server = PDFStreamServerV4(port=0)
        await server.start()
        print(f"✅ サーバー起動: http://127.0.0.1:{server.actual_port}")
        
        # PDF登録
        pdf_url = await server.register_pdf_async("test", test_pdf)
        print(f"✅ PDF登録: {pdf_url}")
        
        # 画像URL生成
        image_url = server.get_image_url("test", 0, width=800, dpr=1.0, fmt="png")
        print(f"✅ 画像URL: {image_url}")
        
        # HTTP確認
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                    print(f"✅ 画像取得成功: {len(image_data)} bytes")
                else:
                    raise RuntimeError(f"HTTP {resp.status}")
        
        # サーバー停止
        await server.stop()
        print("✅ サーバー停止完了")
        
        return True
        
    except Exception as e:
        print(f"❌ V4サーバーテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """メインテスト"""
    print("=" * 50)
    print("🔧 V4修正版動作確認テスト")
    print("=" * 50)
    
    tests = []
    
    # UI初期化テスト
    result1 = test_v4_ui_initialization()
    tests.append(("UI初期化", result1))
    
    # サーバーテスト
    result2 = await test_v4_server_image()
    tests.append(("サーバー画像生成", result2))
    
    # 結果
    print("\n" + "=" * 50)
    print("📊 テスト結果")
    print("=" * 50)
    
    success_count = 0
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            success_count += 1
    
    print(f"\n🎯 成功: {success_count}/{len(tests)} テスト")
    
    if success_count == len(tests):
        print("🎉 V4修正版テスト成功！")
        print("🚀 真っ赤エラー・event loop エラー修正完了")
    else:
        print("⚠️ 一部テスト失敗")
        
    return success_count == len(tests)

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

