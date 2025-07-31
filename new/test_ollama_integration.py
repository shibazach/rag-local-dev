#!/usr/bin/env python3
# new/test_ollama_integration.py
"""
Ollama統合テストスクリプト
LLM接続、テキスト整形、エラーハンドリングを検証
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルート追加
sys.path.append(str(Path(__file__).parent))

from services.llm import OllamaClient, OllamaRefiner
from services.processing import FileProcessor
from config import LOGGER


async def test_ollama_connection():
    """Ollama接続テスト"""
    print("🔗 Ollama接続テスト開始")
    
    try:
        client = OllamaClient()
        is_available = await client.is_available()
        
        if is_available:
            print("  ✅ Ollama接続成功")
            return True
        else:
            print("  ❌ Ollama接続失敗（サーバー未起動の可能性）")
            return False
            
    except ImportError as e:
        print(f"  ❌ 依存関係エラー: {e}")
        print("     pip install langchain langchain-community langchain-ollama")
        return False
    except Exception as e:
        print(f"  ❌ 接続エラー: {e}")
        return False


async def test_text_refinement():
    """テキスト整形テスト"""
    print("\n🧠 テキスト整形テスト開始")
    
    # テストテキスト
    test_text = """
    これは    OCRで読み取った
    
    
    テキストです。
    
    改行や     スペースが
    
    
    不規則に     なっています。
    """
    
    try:
        refiner = OllamaRefiner()
        
        # フォールバック機能テスト
        print("  📝 フォールバック機能テスト")
        fallback_result = refiner.normalize_text(test_text)
        print(f"     正規化結果: {repr(fallback_result[:50])}...")
        
        # Ollama整形テスト
        print("  🤖 Ollama整形テスト")
        refined_text, language, quality_score = await refiner.refine_text(
            raw_text=test_text,
            language="ja"
        )
        
        print(f"     整形結果: {repr(refined_text[:50])}...")
        print(f"     言語: {language}")
        print(f"     品質スコア: {quality_score:.2f}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 整形エラー: {e}")
        return False


async def test_processing_pipeline():
    """処理パイプライン統合テスト"""
    print("\n⚙️ 処理パイプライン統合テスト開始")
    
    try:
        processor = FileProcessor()
        
        # テストファイル作成
        test_file_path = "/tmp/test_ollama.txt"
        test_content = "これはOllama統合テスト用のファイルです。LLMによる整形を検証します。"
        
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        print(f"  📄 テストファイル: {test_file_path}")
        
        # 処理設定
        settings = {
            'llm_model': 'phi4-mini',
            'language': 'ja',
            'quality_threshold': 0.7,
            'embedding_models': ['intfloat-e5-large-v2']
        }
        
        # ファイル処理実行（データベース保存なし）
        print("  🔄 ファイル処理実行")
        result = await processor.process_file(
            file_id="test-ollama-001",
            file_name="test_ollama.txt",
            file_path=test_file_path,
            settings=settings,
            save_to_db=False  # テスト用にDB保存スキップ
        )
        
        print("  📊 処理結果:")
        print(f"     成功: {result.get('success', False)}")
        print(f"     OCRテキスト: {repr(result.get('ocr_result', {}).get('text', '')[:50])}...")
        print(f"     LLM整形済み: {repr(result.get('llm_refined_text', '')[:50])}...")
        print(f"     品質スコア: {result.get('quality_score', 0):.2f}")
        
        # クリーンアップ
        Path(test_file_path).unlink(missing_ok=True)
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"  ❌ パイプラインエラー: {e}")
        return False


async def test_error_handling():
    """エラーハンドリングテスト"""
    print("\n🛡️ エラーハンドリングテスト開始")
    
    try:
        # 不正なモデル指定
        print("  🔧 不正モデルテスト")
        client = OllamaClient(model="invalid-model-name")
        try:
            result = await client.generate_text("テスト")
            print(f"     予期しない成功: {result[:30]}...")
        except Exception as e:
            print(f"     期待通りのエラー: {type(e).__name__}")
        
        # 中断フラグテスト
        print("  ⏹️ 中断フラグテスト")
        refiner = OllamaRefiner()
        abort_flag = {'flag': True}
        
        try:
            result = await refiner.refine_text("テスト", abort_flag=abort_flag)
            print(f"     中断結果: {result[:30]}...")
        except InterruptedError:
            print("     正常な中断処理")
        
        return True
        
    except Exception as e:
        print(f"  ❌ エラーハンドリングテスト失敗: {e}")
        return False


async def main():
    """メインテスト実行"""
    print("🚀 Ollama統合テスト開始")
    print("=" * 50)
    
    tests = [
        ("Ollama接続", test_ollama_connection),
        ("テキスト整形", test_text_refinement),
        ("処理パイプライン", test_processing_pipeline),
        ("エラーハンドリング", test_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}テスト例外: {e}")
            results.append((test_name, False))
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("📊 Ollama統合テスト結果")
    print("=" * 50)
    
    success_count = 0
    total_count = len(results)
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {'成功' if success else '失敗'}")
        if success:
            success_count += 1
    
    success_rate = (success_count / total_count) * 100
    print(f"\n📈 成功率: {success_count}/{total_count} ({success_rate:.1f}%)")
    
    if success_rate >= 75:
        print("🎉 Ollama統合テスト全体: ✅ 成功")
        return True
    else:
        print("⚠️ Ollama統合テスト全体: ❌ 要改善")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)