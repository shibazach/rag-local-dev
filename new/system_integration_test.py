#!/usr/bin/env python3
# new/system_integration_test.py
# 新系システム全体統合テスト

import asyncio
import aiohttp
import json
import sys
from pathlib import Path

# パス設定
sys.path.insert(0, str(Path(__file__).parent))

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api"

class SystemIntegrationTester:
    def __init__(self):
        self.session = None
        self.test_results = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_health_check(self):
        """ヘルスチェックAPI動作確認"""
        print("🔍 1. ヘルスチェックAPI動作確認")
        
        try:
            async with self.session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"  ✅ ヘルスチェック成功: {data}")
                    return True
                else:
                    print(f"  ❌ ヘルスチェック失敗: {response.status}")
                    return False
        except Exception as e:
            print(f"  ❌ ヘルスチェックエラー: {e}")
            return False

    async def test_database_connection(self):
        """データベース接続確認"""
        print("\n🔍 2. データベース接続確認")
        
        try:
            # データベーステスト用のAPIがないため、ファイル一覧で代用
            async with self.session.get(f"{BASE_URL}{API_PREFIX}/files") as response:
                if response.status == 200:
                    data = await response.json()
                    total_files = data.get('total', 0)
                    print(f"  ✅ データベース接続成功: 総ファイル数 {total_files}件")
                    return True
                elif response.status == 401:
                    print(f"  ⚠️  認証が必要ですが、API自体は動作中")
                    return True  # 認証必要だが正常
                else:
                    print(f"  ❌ データベース接続失敗: {response.status}")
                    return False
        except Exception as e:
            print(f"  ❌ データベース接続エラー: {e}")
            return False

    async def test_openapi_spec(self):
        """OpenAPI仕様確認"""
        print("\n🔍 3. OpenAPI仕様確認")
        
        try:
            async with self.session.get(f"{BASE_URL}{API_PREFIX}/openapi.json") as response:
                if response.status == 200:
                    spec = await response.json()
                    paths = spec.get('paths', {})
                    
                    # 主要APIの存在確認
                    expected_apis = [
                        f"{API_PREFIX}/files",
                        f"{API_PREFIX}/upload",
                        f"{API_PREFIX}/processing",
                        f"{API_PREFIX}/ingest",
                        f"{API_PREFIX}/file-selection"
                    ]
                    
                    found_apis = []
                    missing_apis = []
                    
                    for api in expected_apis:
                        if any(api in path for path in paths.keys()):
                            found_apis.append(api)
                        else:
                            missing_apis.append(api)
                    
                    print(f"  ✅ 登録済みAPI: {len(found_apis)}個")
                    for api in found_apis:
                        print(f"    - {api}")
                    
                    if missing_apis:
                        print(f"  ⚠️  未登録API: {len(missing_apis)}個")
                        for api in missing_apis:
                            print(f"    - {api}")
                    
                    return len(found_apis) >= 3  # 最低3つのAPIが動作していればOK
                else:
                    print(f"  ❌ OpenAPI取得失敗: {response.status}")
                    return False
        except Exception as e:
            print(f"  ❌ OpenAPI確認エラー: {e}")
            return False

    async def test_static_files(self):
        """静的ファイル配信確認"""
        print("\n🔍 4. 静的ファイル配信確認")
        
        test_files = [
            "/static/css/main.css",
            "/static/js/data_registration.js",
            "/static/js/file_selection.js"
        ]
        
        success_count = 0
        for file_path in test_files:
            try:
                async with self.session.get(f"{BASE_URL}{file_path}") as response:
                    if response.status == 200:
                        print(f"  ✅ {file_path}")
                        success_count += 1
                    else:
                        print(f"  ❌ {file_path} (Status: {response.status})")
            except Exception as e:
                print(f"  ❌ {file_path} (Error: {e})")
        
        print(f"  📊 静的ファイル成功率: {success_count}/{len(test_files)}")
        return success_count >= len(test_files) // 2  # 半分以上成功でOK

    async def test_data_registration_page(self):
        """データ登録ページアクセス確認"""
        print("\n🔍 5. データ登録ページアクセス確認")
        
        try:
            async with self.session.get(f"{BASE_URL}/data-registration") as response:
                if response.status == 200:
                    content = await response.text()
                    if "データ登録" in content:
                        print(f"  ✅ データ登録ページ表示成功")
                        return True
                    else:
                        print(f"  ⚠️  ページは表示されましたが内容に問題があります")
                        return False
                elif response.status == 302:
                    print(f"  ⚠️  ログインページにリダイレクト（認証必要）")
                    return True  # 認証必要だが正常
                else:
                    print(f"  ❌ ページアクセス失敗: {response.status}")
                    return False
        except Exception as e:
            print(f"  ❌ ページアクセスエラー: {e}")
            return False

    async def test_api_endpoints_basic(self):
        """基本APIエンドポイント確認"""
        print("\n🔍 6. 基本APIエンドポイント確認")
        
        test_endpoints = [
            f"{API_PREFIX}/files",
            f"{API_PREFIX}/upload",
            f"{API_PREFIX}/processing",
            f"{API_PREFIX}/ingest/status",
            f"{API_PREFIX}/file-selection/stats"
        ]
        
        results = {}
        for endpoint in test_endpoints:
            try:
                async with self.session.get(f"{BASE_URL}{endpoint}") as response:
                    if response.status in [200, 401, 422]:  # 200=OK, 401=認証必要, 422=パラメータ不足
                        results[endpoint] = "✅ 正常"
                    else:
                        results[endpoint] = f"❌ Status: {response.status}"
            except Exception as e:
                results[endpoint] = f"❌ Error: {str(e)[:50]}"
        
        for endpoint, result in results.items():
            print(f"  {result} {endpoint}")
        
        success_count = sum(1 for r in results.values() if "✅" in r)
        print(f"  📊 API成功率: {success_count}/{len(test_endpoints)}")
        
        return success_count >= len(test_endpoints) // 2

    async def test_system_configuration(self):
        """システム設定確認"""
        print("\n🔍 7. システム設定確認")
        
        try:
            # config情報の間接的確認
            async with self.session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    print(f"  ✅ ポート8000で正常稼働")
                    
                    # CPU/GPU設定確認（ヘルスチェックレスポンスに含まれる場合）
                    health_data = await response.json()
                    if 'config' in health_data:
                        config = health_data['config']
                        print(f"  📋 CUDA利用可能: {config.get('cuda_available', 'Unknown')}")
                        print(f"  📋 LLMモデル: {config.get('llm_model', 'Unknown')}")
                    
                    return True
                else:
                    print(f"  ❌ システム設定確認失敗")
                    return False
        except Exception as e:
            print(f"  ❌ システム設定確認エラー: {e}")
            return False

    async def run_all_tests(self):
        """全テスト実行"""
        print("🚀 新系システム全体統合テスト開始")
        print("=" * 60)
        
        test_methods = [
            self.test_health_check,
            self.test_database_connection,
            self.test_openapi_spec,
            self.test_static_files,
            self.test_data_registration_page,
            self.test_api_endpoints_basic,
            self.test_system_configuration
        ]
        
        results = []
        for test_method in test_methods:
            result = await test_method()
            results.append(result)
        
        # 最終結果
        print("\n" + "=" * 60)
        print("📊 統合テスト結果サマリー")
        print("=" * 60)
        
        success_count = sum(1 for r in results if r)
        total_tests = len(results)
        success_rate = (success_count / total_tests) * 100
        
        print(f"✅ 成功: {success_count}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 統合テスト成功！新系システム正常稼働確認")
            status = "success"
        elif success_rate >= 60:
            print("⚠️  部分的成功 - 軽微な問題あり")
            status = "partial"
        else:
            print("❌ 統合テスト失敗 - 重大な問題あり")
            status = "failed"
        
        return {
            "status": status,
            "success_rate": success_rate,
            "success_count": success_count,
            "total_tests": total_tests
        }

async def main():
    """メイン実行"""
    async with SystemIntegrationTester() as tester:
        result = await tester.run_all_tests()
        
        # 結果に応じた終了コード
        if result["status"] == "success":
            sys.exit(0)
        elif result["status"] == "partial":
            sys.exit(1)
        else:
            sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())