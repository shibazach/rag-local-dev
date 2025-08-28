#!/usr/bin/env python3
"""
最小限のWebViewメッセージテスト
"""

import flet as ft

def main(page: ft.Page):
    page.title = "簡単WebViewテスト"
    
    # メッセージ受信状態
    received_messages = []
    
    def on_any_event(e):
        """全てのイベントをキャッチ"""
        msg = f"イベント: {type(e).__name__} - {getattr(e, 'data', str(e))}"
        print(f"[EVENT] {msg}")
        received_messages.append(msg)
        
        # 何かメッセージを受信したら5秒後に終了
        if len(received_messages) >= 1:
            page.run_task(close_after_delay)
    
    async def close_after_delay():
        import asyncio
        await asyncio.sleep(5)
        print(f"[RESULT] 受信メッセージ数: {len(received_messages)}")
        for i, msg in enumerate(received_messages):
            print(f"[MSG{i+1}] {msg}")
        page.window_close()
    
    # 簡単なHTML（自動でメッセージ送信）
    html = """
    <html><body>
    <h3>WebViewテスト</h3>
    <script>
        setTimeout(() => {
            // 複数の方法で送信
            if (window.parent) window.parent.postMessage('Test from JS', '*');
            if (window.webkit?.messageHandlers?.flet) window.webkit.messageHandlers.flet.postMessage('Test webkit');
            console.log('Messages sent');
        }, 1000);
    </script>
    </body></html>
    """
    
    # WebViewのメッセージハンドラーを全て試す
    webview_attrs = {}
    for attr in ['on_message', 'on_web_message', 'on_page_ended']:
        webview_attrs[attr] = on_any_event
    
    try:
        webview = ft.WebView(data=html, expand=True, **webview_attrs)
        print(f"[INFO] WebView作成成功 - ハンドラー: {list(webview_attrs.keys())}")
    except Exception as e:
        print(f"[ERROR] WebView作成失敗: {e}")
        return
    
    page.add(
        ft.Text("WebViewメッセージテスト（簡潔版）", size=16),
        ft.Container(content=webview, expand=True, height=300)
    )
    
    # 10秒後に強制終了
    async def timeout_exit():
        import asyncio
        await asyncio.sleep(10)
        print("[TIMEOUT] メッセージなし - postMessage非対応と判定")
        page.window_close()
    
    page.run_task(timeout_exit)

if __name__ == "__main__":
    ft.app(target=main)

