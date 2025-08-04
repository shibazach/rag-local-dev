#!/usr/bin/env python3
"""
完全分離テスト: 最小構成FastAPI + NiceGUI
DOM構造確認用の実験ファイル（本プロジェクトから完全独立）
"""

from fastapi import FastAPI
from nicegui import ui, app
import uvicorn

# FastAPIアプリケーション作成
fastapi_app = FastAPI(title="最小構成テスト")

# ===== 完全まっさらなページ =====
@ui.page('/')
def home():
    """完全まっさらなNiceGUIページ"""
    ui.label('🔬 最小構成DOM構造テスト')
    ui.label('これは完全まっさらなNiceGUIページです')

# ===== 基本パネルのみのページ =====
@ui.page('/panel')
def panel_test():
    """基本パネル1つだけのページ"""
    with ui.element('div').style('border:1px solid #ccc;padding:16px;margin:16px;'):
        ui.label('📋 基本パネルテスト')
        ui.button('ボタン')
        ui.input('入力フィールド')

# ===== Quasarタブのみのページ =====
@ui.page('/tabs')
def tabs_test():
    """Quasarタブのみのページ（最小構成）"""
    with ui.tabs() as tabs:
        tab1 = ui.tab('タブA')
        tab2 = ui.tab('タブB')
    
    with ui.tab_panels(tabs, value=tab1):
        with ui.tab_panel(tab1):
            ui.label('タブAの内容')
        with ui.tab_panel(tab2):
            ui.label('タブBの内容')

# ===== position:fixedヘッダーのみのページ =====
@ui.page('/header')
def header_test():
    """position:fixedヘッダーのみのページ"""
    # position:fixedヘッダー
    with ui.element('div').style('position:fixed;top:0;left:0;width:100%;height:48px;background:#334155;color:white;z-index:1000;display:flex;align-items:center;padding:0 16px;'):
        ui.label('🏠 固定ヘッダー')
    
    # メインコンテンツ（margin-top:48px）
    with ui.element('div').style('margin-top:48px;padding:16px;'):
        ui.label('メインコンテンツエリア')
        ui.label('ヘッダーの下に配置されています')

# ===== ヘッダー+フッター+メインのページ =====
@ui.page('/layout')
def layout_test():
    """ヘッダー+フッター+メインコンテンツのページ"""
    # ヘッダー
    with ui.element('div').style('position:fixed;top:0;left:0;width:100%;height:48px;background:#334155;color:white;z-index:1000;display:flex;align-items:center;padding:0 16px;'):
        ui.label('🏠 ヘッダー')
    
    # メインコンテンツ
    with ui.element('div').style('margin-top:48px;margin-bottom:24px;padding:16px;min-height:calc(100vh - 72px);'):
        ui.label('📄 メインコンテンツ')
        ui.label('ヘッダーとフッターの間に配置')
        for i in range(50):
            ui.label(f'コンテンツ行 {i+1}')
    
    # フッター
    with ui.element('div').style('position:fixed;bottom:0;left:0;width:100%;height:24px;background:#374151;color:white;z-index:999;display:flex;align-items:center;padding:0 16px;'):
        ui.label('📊 フッター')

# ===== FastAPIエンドポイント =====
@fastapi_app.get("/api/test")
def api_test():
    return {"message": "最小構成API", "status": "OK"}

# ===== ルートインデックス（ナビゲーション） =====
@ui.page('/nav')
def navigation():
    """全テストページへのナビゲーション"""
    ui.markdown("""
    # 🔬 DOM構造テスト - ナビゲーション
    
    各ページでブラウザ開発者ツールを開いてDOM構造を確認してください。
    """)
    
    ui.link('1. 完全まっさら', '/')
    ui.link('2. 基本パネルのみ', '/panel')
    ui.link('3. Quasarタブのみ', '/tabs')
    ui.link('4. position:fixedヘッダーのみ', '/header')
    ui.link('5. ヘッダー+フッター+メイン', '/layout')

if __name__ == "__main__":
    print("🔬 最小構成DOM構造テスト開始")
    print("📍 ナビゲーション: http://localhost:8081/nav")
    print("📍 完全まっさら: http://localhost:8081/")
    print("📍 基本パネル: http://localhost:8081/panel")
    print("📍 Quasarタブ: http://localhost:8081/tabs")
    print("📍 固定ヘッダー: http://localhost:8081/header")
    print("📍 フルレイアウト: http://localhost:8081/layout")
    
    # ポート8081で起動（本プロジェクトと完全分離）
    ui.run(
        host='0.0.0.0', 
        port=8081,
        title='最小構成DOM構造テスト',
        show=False
    )