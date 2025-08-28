#!/usr/bin/env python3
"""
FletのWebViewでpostMessage機能が使用可能か確認するテスト
"""

import flet as ft
import asyncio
import time

def test_webview_message():
    """WebViewのメッセージ機能テスト"""
    
    def main(page: ft.Page):
        page.title = "WebViewメッセージテスト"
        
        # HTMLテスト用コンテンツ
        test_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Message Test</title></head>
        <body>
            <h1>WebViewメッセージテスト</h1>
            <button onclick="sendMessage()">メッセージ送信</button>
            <div id="status">待機中...</div>
            
            <script>
                function sendMessage() {
                    document.getElementById('status').textContent = 'メッセージ送信中...';
                    
                    // 複数の方法でメッセージ送信を試行
                    try {
                        // 方法1: window.parent.postMessage
                        if (window.parent) {
                            window.parent.postMessage('TEST_MESSAGE_FROM_WEBVIEW', '*');
                        }
                        
                        // 方法2: window.webkit (iOS)
                        if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.flet) {
                            window.webkit.messageHandlers.flet.postMessage('TEST_MESSAGE_WEBKIT');
                        }
                        
                        // 方法3: window.flet (デスクトップ)
                        if (window.flet) {
                            window.flet.postMessage('TEST_MESSAGE_FLET');
                        }
                        
                        document.getElementById('status').textContent = 'メッセージ送信完了';
                        
                    } catch (e) {
                        document.getElementById('status').textContent = 'エラー: ' + e.message;
                    }
                }
                
                // ページ読み込み完了を通知
                setTimeout(() => {
                    sendMessage();
                }, 1000);
            </script>
        </body>
        </html>
        """
        
        def on_message(e):
            """メッセージ受信ハンドラ"""
            message = e.data if hasattr(e, 'data') else str(e)
            timestamp = time.strftime("%H:%M:%S")
            
            print(f"[{timestamp}] ✅ WebViewメッセージ受信成功: {message}")
            print(f"[{timestamp}] 📋 イベント詳細: type={type(e)}, attributes={dir(e)}")
            
            with open("webview_message_test.log", "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] SUCCESS: {message}\n")
                f.write(f"[{timestamp}] EVENT_DETAIL: {type(e)} - {dir(e)}\n")
            
            status_text.value = f"✅受信成功: {message}"
            status_text.update()
            
            # 成功時は5秒後に終了
            page.run_task(auto_close)
        
        # WebViewの様々なメッセージイベントを試行
        try:
            webview = ft.WebView(
                data=test_html,  # HTMLを直接設定
                expand=True,
                on_page_started=lambda e: print("[WebView] ページ開始"),
                on_page_ended=lambda e: print("[WebView] ページ終了"),
            )
            
            # メッセージハンドラーが存在するかチェック
            message_handlers = []
            for attr in ['on_message', 'on_web_message', 'on_message_received']:
                if hasattr(webview, attr):
                    message_handlers.append(attr)
                    setattr(webview, attr, on_message)
                    
        except Exception as e:
            print(f"WebView作成エラー: {e}")
            webview = ft.Text(f"WebView作成失敗: {e}")
            message_handlers = []
        
        status_text = ft.Text("待機中...", size=14)
        
        async def auto_close():
            """自動終了機能"""
            await asyncio.sleep(5)
            print("[INFO] テスト完了 - 自動終了")
            page.window.close()
        
        async def timeout_close():
            """タイムアウト終了"""
            await asyncio.sleep(10)  # 10秒後にタイムアウト
            print("[WARNING] ❌ タイムアウト - postMessage機能は利用不可と判定")
            with open("webview_message_test.log", "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] TIMEOUT: No message received\n")
            status_text.value = "❌ タイムアウト: postMessage未対応"
            status_text.update()
            await asyncio.sleep(2)
            page.window.close()
        
        # 初期化完了ログ
        print(f"[{time.strftime('%H:%M:%S')}] 🧪 WebViewメッセージテスト開始")
        print(f"[{time.strftime('%H:%M:%S')}] 🔍 検出メッセージハンドラー: {', '.join(message_handlers) if message_handlers else 'なし'}")
        
        with open("webview_message_test.log", "w", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] TEST_START: WebView Message Test\n")
            f.write(f"[{time.strftime('%H:%M:%S')}] HANDLERS: {', '.join(message_handlers) if message_handlers else 'None'}\n")
        
        # タイムアウト監視開始
        page.run_task(timeout_close)
        
        page.add(
            ft.Text("WebViewメッセージ機能テスト", size=20, weight=ft.FontWeight.BOLD),
            ft.Text(f"検出されたメッセージハンドラー: {', '.join(message_handlers) if message_handlers else 'なし'}"),
            status_text,
            ft.Container(content=webview, expand=True, height=400)
        )
    
    ft.app(target=main)

if __name__ == "__main__":
    test_webview_message()
