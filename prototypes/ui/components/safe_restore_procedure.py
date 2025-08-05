"""緊急復旧プロシージャ - 共通コンポーネント化フェイルセーフ"""

from typing import Optional
import shutil
import os

class SafeRestoreProcedure:
    """
    共通コンポーネント化における安全な復旧プロシージャ
    
    目的:
    - 共通コンポーネント化実験時の安全装置
    - 白画面エラー発生時の即座復旧
    - 段階的なコンポーネント移行支援
    
    使用方法:
    1. 新しい共通コンポーネントを作成
    2. SafeRestoreProcedure.backup_current_state() でバックアップ
    3. タブDで実験・テスト実行
    4. 問題発生時 SafeRestoreProcedure.emergency_restore() で復旧
    """
    
    BACKUP_DIR = "ui/pages/backups"
    TAB_D_PATH = "ui/pages/arrangement_test_tab_d.py"
    TEMPLATE_PATH = "ui/pages/arrangement_test_tab_template.py"
    
    @staticmethod
    def backup_current_state(experiment_name: str) -> bool:
        """
        現在の状態をバックアップ
        
        Args:
            experiment_name: 実験名（例: "common_form_elements_v2"）
            
        Returns:
            bool: バックアップ成功可否
        """
        try:
            # バックアップディレクトリ作成
            os.makedirs(SafeRestoreProcedure.BACKUP_DIR, exist_ok=True)
            
            # タイムスタンプ付きバックアップファイル名
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"arrangement_test_tab_d_backup_{experiment_name}_{timestamp}.py"
            backup_path = os.path.join(SafeRestoreProcedure.BACKUP_DIR, backup_filename)
            
            # ファイルをバックアップ
            if os.path.exists(SafeRestoreProcedure.TAB_D_PATH):
                shutil.copy2(SafeRestoreProcedure.TAB_D_PATH, backup_path)
                print(f"✅ バックアップ完了: {backup_path}")
                return True
            else:
                print(f"❌ 元ファイルが見つかりません: {SafeRestoreProcedure.TAB_D_PATH}")
                return False
                
        except Exception as e:
            print(f"❌ バックアップ失敗: {e}")
            return False
    
    @staticmethod
    def emergency_restore() -> bool:
        """
        緊急復旧: テンプレートでタブDを置き換え
        
        Returns:
            bool: 復旧成功可否
        """
        try:
            # テンプレートファイルの存在確認
            if not os.path.exists(SafeRestoreProcedure.TEMPLATE_PATH):
                print(f"❌ テンプレートファイルが見つかりません: {SafeRestoreProcedure.TEMPLATE_PATH}")
                return False
            
            # テンプレートでタブDを置き換え
            shutil.copy2(SafeRestoreProcedure.TEMPLATE_PATH, SafeRestoreProcedure.TAB_D_PATH)
            
            # クラス名を修正（ArrangementTestTabTemplate → ArrangementTestTabD）
            with open(SafeRestoreProcedure.TAB_D_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # クラス名とコメントを修正
            content = content.replace(
                'class ArrangementTestTabTemplate:',
                'class ArrangementTestTabD:'
            )
            content = content.replace(
                '"""配置テスト - タブテンプレート: 緊急時復旧用バックアップ"""',
                '"""配置テスト - タブD: 緊急復旧モード"""'
            )
            
            with open(SafeRestoreProcedure.TAB_D_PATH, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("🚨 緊急復旧完了: タブDを安全なテンプレートに置き換えました")
            print("📋 次の手順:")
            print("1. サーバーを再起動してください")
            print("2. /arrangement-test にアクセスしてタブDが復旧したことを確認")
            print("3. 共通コンポーネントのエラーを修正")
            print("4. 段階的に機能を復元")
            
            return True
            
        except Exception as e:
            print(f"❌ 緊急復旧失敗: {e}")
            return False
    
    @staticmethod
    def restore_from_backup(backup_filename: str) -> bool:
        """
        指定されたバックアップファイルから復旧
        
        Args:
            backup_filename: バックアップファイル名
            
        Returns:
            bool: 復旧成功可否
        """
        try:
            backup_path = os.path.join(SafeRestoreProcedure.BACKUP_DIR, backup_filename)
            
            if not os.path.exists(backup_path):
                print(f"❌ バックアップファイルが見つかりません: {backup_path}")
                return False
            
            # バックアップから復旧
            shutil.copy2(backup_path, SafeRestoreProcedure.TAB_D_PATH)
            print(f"✅ バックアップから復旧完了: {backup_filename}")
            
            return True
            
        except Exception as e:
            print(f"❌ バックアップからの復旧失敗: {e}")
            return False
    
    @staticmethod
    def list_backups() -> list:
        """
        利用可能なバックアップファイル一覧を取得
        
        Returns:
            list: バックアップファイル名のリスト
        """
        try:
            if not os.path.exists(SafeRestoreProcedure.BACKUP_DIR):
                return []
            
            backup_files = [
                f for f in os.listdir(SafeRestoreProcedure.BACKUP_DIR)
                if f.startswith('arrangement_test_tab_d_backup_') and f.endswith('.py')
            ]
            
            # 新しい順にソート
            backup_files.sort(reverse=True)
            
            return backup_files
            
        except Exception as e:
            print(f"❌ バックアップリスト取得失敗: {e}")
            return []

# 使用例とコマンドライン関数
def cli_backup(experiment_name: str):
    """コマンドライン用バックアップ"""
    SafeRestoreProcedure.backup_current_state(experiment_name)

def cli_emergency_restore():
    """コマンドライン用緊急復旧"""
    SafeRestoreProcedure.emergency_restore()

def cli_list_backups():
    """コマンドライン用バックアップ一覧"""
    backups = SafeRestoreProcedure.list_backups()
    if backups:
        print("📁 利用可能なバックアップ:")
        for i, backup in enumerate(backups, 1):
            print(f"  {i}. {backup}")
    else:
        print("📁 バックアップファイルが見つかりません")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("使用法:")
        print("  python safe_restore_procedure.py backup <実験名>")
        print("  python safe_restore_procedure.py emergency")
        print("  python safe_restore_procedure.py list")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "backup" and len(sys.argv) >= 3:
        cli_backup(sys.argv[2])
    elif command == "emergency":
        cli_emergency_restore()
    elif command == "list":
        cli_list_backups()
    else:
        print("❌ 無効なコマンドです")