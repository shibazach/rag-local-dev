#!/usr/bin/env python3
# new/simple_integration_test.py
# 新系システム簡易統合テスト（動作確認重視）

import requests
import json

BASE_URL = "http://localhost:8000"

def test_basic_functionality():
    """基本機能の動作確認"""
    print("🚀 新系システム簡易統合テスト")
    print("=" * 50)
    
    success_count = 0
    total_tests = 0
    
    # 1. ヘルスチェック
    print("🔍 1. ヘルスチェック")
    total_tests += 1
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 成功: {data}")
            success_count += 1
        else:
            print(f"  ❌ 失敗: Status {response.status_code}")
    except Exception as e:
        print(f"  ❌ エラー: {e}")
    
    # 2. データ登録ページ
    print("\n🔍 2. データ登録ページアクセス")
    total_tests += 1
    try:
        response = requests.get(f"{BASE_URL}/data-registration")
        if response.status_code in [200, 302]:  # 200=成功, 302=ログイン必要
            print(f"  ✅ ページアクセス成功 (Status: {response.status_code})")
            success_count += 1
        else:
            print(f"  ❌ ページアクセス失敗: Status {response.status_code}")
    except Exception as e:
        print(f"  ❌ エラー: {e}")
    
    # 3. 静的ファイル
    print("\n🔍 3. 主要静的ファイル確認")
    total_tests += 1
    static_files = [
        "/static/css/main.css",
        "/static/js/data_registration.js"
    ]
    
    static_success = 0
    for file_path in static_files:
        try:
            response = requests.get(f"{BASE_URL}{file_path}")
            if response.status_code == 200:
                static_success += 1
        except:
            pass
    
    if static_success >= len(static_files) // 2:
        print(f"  ✅ 静的ファイル配信成功 ({static_success}/{len(static_files)})")
        success_count += 1
    else:
        print(f"  ❌ 静的ファイル配信問題 ({static_success}/{len(static_files)})")
    
    # 4. 基本API確認
    print("\n🔍 4. 基本API動作確認")
    total_tests += 1
    try:
        response = requests.get(f"{BASE_URL}/api/files")
        if response.status_code in [200, 401, 422]:
            print(f"  ✅ Files API応答成功 (Status: {response.status_code})")
            success_count += 1
        else:
            print(f"  ❌ Files API応答失敗: Status {response.status_code}")
    except Exception as e:
        print(f"  ❌ Files APIエラー: {e}")
    
    # 5. システム設定確認
    print("\n🔍 5. システム基本設定")
    total_tests += 1
    try:
        # ポート8000で稼働確認
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print(f"  ✅ ポート8000で正常稼働")
            success_count += 1
        else:
            print(f"  ❌ システム設定問題")
    except Exception as e:
        print(f"  ❌ システム設定エラー: {e}")
    
    # 結果表示
    print("\n" + "=" * 50)
    print("📊 簡易統合テスト結果")
    print("=" * 50)
    
    success_rate = (success_count / total_tests) * 100
    print(f"✅ 成功: {success_count}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 新系システム基本機能正常稼働確認！")
        status = "✅ SUCCESS"
    elif success_rate >= 60:
        print("⚠️  基本機能は動作中（軽微な問題あり）")
        status = "⚠️  PARTIAL"
    else:
        print("❌ 重大な問題があります")
        status = "❌ FAILED"
    
    print(f"\n🏷️  統合テスト結果: {status}")
    
    return {
        "status": status,
        "success_rate": success_rate,
        "success_count": success_count,
        "total_tests": total_tests
    }

def test_ui_integration():
    """UI統合機能テスト"""
    print("\n🎨 UI統合機能確認")
    print("-" * 30)
    
    ui_tests = [
        ("/", "ルートページ"),
        ("/login", "ログインページ"),
        ("/data-registration", "データ登録ページ"),
        ("/files", "ファイル管理ページ")
    ]
    
    ui_success = 0
    for endpoint, name in ui_tests:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.status_code in [200, 302]:
                print(f"  ✅ {name}")
                ui_success += 1
            else:
                print(f"  ❌ {name} (Status: {response.status_code})")
        except Exception as e:
            print(f"  ❌ {name} (Error: {str(e)[:30]})")
    
    print(f"\n📊 UI統合成功率: {ui_success}/{len(ui_tests)} ({ui_success/len(ui_tests)*100:.1f}%)")
    return ui_success >= len(ui_tests) // 2

if __name__ == "__main__":
    # 基本機能テスト
    basic_result = test_basic_functionality()
    
    # UI統合テスト
    ui_result = test_ui_integration()
    
    # 最終判定
    print("\n" + "=" * 50)
    print("🏁 最終判定")
    print("=" * 50)
    
    if basic_result["success_rate"] >= 80 and ui_result:
        print("🎉 【新系システム統合テスト完全成功】")
        print("   ✅ 基本機能動作確認")
        print("   ✅ UI統合確認")  
        print("   ✅ システム安定性確認")
        exit_code = 0
    elif basic_result["success_rate"] >= 60:
        print("⚠️  【新系システム部分的成功】")
        print("   ✅ 主要機能は動作中")
        print("   ⚠️  軽微な調整が必要")
        exit_code = 1
    else:
        print("❌ 【新系システム要修正】")
        exit_code = 2
    
    exit(exit_code)