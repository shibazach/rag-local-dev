"""
認証ページ - ログイン/ログアウト処理
"""
from nicegui import ui

class LoginPage:
    """ログインページクラス"""
    
    def render(self):
        """ページレンダリング"""
        # 全面背景グラデーション・完全センタリング
        with ui.element('div').style('''
            position: fixed; 
            top: 0; left: 0; right: 0; bottom: 0; 
            width: 100vw; height: 100vh; 
            background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
            display: flex; 
            justify-content: center; 
            align-items: center;
            margin: 0; 
            padding: 0;
            z-index: 1000;
        '''):
            with ui.element('div').style('''
                background: rgba(255,255,255,0.95); 
                padding: 48px; 
                border-radius: 16px; 
                box-shadow: 0 20px 40px rgba(0,0,0,0.1); 
                min-width: 360px; 
                max-width: 400px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.3);
            '''):
                # タイトル部分
                ui.label('R&D RAGシステム').style('''
                    font-size: 28px; 
                    font-weight: bold; 
                    text-align: center; 
                    margin: 0 0 12px 0; 
                    color: #334155;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ''')
                
                ui.label('ログイン').style('''
                    font-size: 18px; 
                    text-align: center; 
                    margin: 0 0 32px 0; 
                    color: #64748b;
                ''')
                
                # 入力フォーム
                username_input = ui.input(
                    label='ユーザー名',
                    placeholder='admin'
                ).style('''
                    width: 100%; 
                    margin-bottom: 20px;
                ''').props('outlined dense')
                
                password_input = ui.input(
                    label='パスワード',
                    placeholder='password',
                    password=True
                ).style('''
                    width: 100%; 
                    margin-bottom: 32px;
                ''').props('outlined dense')
                
                # ログインボタン
                ui.button(
                    'ログイン',
                    on_click=lambda: self._handle_login(username_input.value, password_input.value)
                ).style('''
                    width: 100%; 
                    background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%); 
                    color: white; 
                    padding: 16px; 
                    font-size: 16px; 
                    font-weight: 600;
                    border: none; 
                    border-radius: 8px; 
                    cursor: pointer;
                    box-shadow: 0 4px 12px rgba(107, 114, 128, 0.4);
                    transition: all 0.3s ease;
                ''').props('no-caps')
                
                # ヒント表示
                ui.label('ヒント: admin / password').style('''
                    font-size: 12px; 
                    text-align: center; 
                    margin: 16px 0 0 0; 
                    color: #94a3b8;
                ''')
    
    def _handle_login(self, username: str, password: str):
        """ログイン処理（シンプルセッション管理 + リダイレクト対応）"""
        if username == "admin" and password == "password":
            from app.auth.session_simple import SimpleSessionManager
            
            # ユーザーデータ準備
            user_data = {
                "id": 1,
                "username": username,
                "email": f"{username}@example.com",
                "is_admin": True
            }
            
            # シンプルセッション作成
            session_id = SimpleSessionManager.create_session(user_data)
            
            if session_id:
                ui.notify('ログインしました', color='positive')
                
                # 非同期リダイレクト処理をコールバック式に変更
                self._perform_redirect()
            else:
                ui.notify('ログイン処理に失敗しました', color='negative')
        else:
            ui.notify('ユーザー名またはパスワードが正しくありません', type='negative')
    
    def _perform_redirect(self):
        """非同期リダイレクト処理"""
        # JavaScriptでリダイレクトURLを取得して直接遷移
        ui.run_javascript('''
            // URLパラメータからリダイレクト先を取得
            const urlParams = new URLSearchParams(window.location.search);
            const redirectUrl = urlParams.get('redirect') || '/';
            
            // ページ遷移を実行
            console.log('リダイレクト先:', redirectUrl);
            window.location.href = redirectUrl;
        ''')
    
    def _get_redirect_url_sync(self) -> str:
        """同期版リダイレクトURL取得（フォールバック用）"""
        # シンプルなフォールバック: ホームページにリダイレクト
        return '/'