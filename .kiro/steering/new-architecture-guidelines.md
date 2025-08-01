---
inclusion: always
---

# 新アーキテクチャ開発ガイドライン

## 概要
new/フォルダ以下で構築された新RAGシステムの開発・運用ガイドライン。
旧システム（OLD/）からの移行を完了し、モダンなFastAPI + Pydantic v2アーキテクチャを採用。

## 🏗️ アーキテクチャ原則

### レイヤー分離
- **API層** (`new/api/`): エンドポイント定義、リクエスト/レスポンス処理
- **サービス層** (`new/services/`): ビジネスロジック、外部サービス統合
- **データ層** (`new/database/`): データベース操作、モデル定義
- **UI層** (`new/templates/`, `new/static/`): フロントエンド、静的ファイル

### 設定管理
- **統一設定**: `new/config.py` でPydantic BaseSettingsによる環境変数管理
- **型安全性**: 全設定項目に型ヒント・バリデーション適用
- **環境分離**: 開発・テスト・本番環境の設定分離

## 📊 データベース設計（3テーブル構成）

### テーブル構成
```sql
-- 主テーブル: ファイルバイナリ格納
files_blob (id UUID, checksum, blob_data, stored_at)

-- メタ情報: ファイル属性
files_meta (blob_id UUID, file_name, mime_type, size, status, ...)

-- テキスト情報: 処理結果
files_text (blob_id UUID, raw_text, refined_text, quality_score, ...)
```

### 設計原則
- **正規化**: 重複排除、整合性確保
- **パフォーマンス**: 適切なインデックス設計
- **拡張性**: 新機能追加に対応可能な構造
- **保守性**: 明確な責務分離

## 🔄 処理パイプライン

### ファイル処理フロー
1. **アップロード**: ファイル受信、チェックサム計算、重複チェック
2. **メタデータ抽出**: ファイル情報、ページ数等の基本情報取得
3. **OCR処理**: 複数エンジン対応、テキスト抽出
4. **LLM整形**: Ollama統合、日本語テキスト品質向上
5. **ベクトル化**: 埋め込みモデルによるベクトル生成
6. **インデックス化**: 検索用インデックス構築

### 非同期処理
- **SSE**: Server-Sent Eventsによるリアルタイム進捗表示
- **キャンセル対応**: 処理中断・復旧機能
- **エラーハンドリング**: 段階的フォールバック処理

## 🔐 セキュリティ設計

### 認証・認可
```python
# 統一認証パターン
@router.post("/api/endpoint")
async def endpoint(
    request_data: RequestSchema,
    current_user = Depends(get_current_user)  # 全APIで統一
):
    # 処理ロジック
    pass
```

### セキュリティヘッダー
- **CSP**: Content Security Policy設定
- **CORS**: 適切なオリジン制限
- **セッション**: セキュアクッキー設定

## 🧪 テスト戦略

### テストファイル構成
- `new/simple_integration_test.py`: 基本統合テスト
- `new/system_integration_test.py`: システム全体テスト
- `new/test_db_connection.py`: データベース接続テスト

### テスト原則
- **単体テスト**: サービス層の個別機能テスト
- **統合テスト**: API エンドポイントのE2Eテスト
- **モック活用**: 外部依存の分離テスト

## 📝 開発ワークフロー

### コード品質
```python
# 標準的なサービス実装パターン
class ExampleService:
    """サービスクラスの標準実装"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def process_async(self, data: InputSchema) -> OutputSchema:
        """非同期処理の標準パターン"""
        try:
            # 入力検証
            validated_data = self._validate_input(data)
            
            # ビジネスロジック実行
            result = await self._execute_business_logic(validated_data)
            
            # 結果返却
            return OutputSchema(**result)
            
        except Exception as e:
            self.logger.error(f"処理エラー: {e}")
            raise ProcessingError(f"処理失敗: {str(e)}")
```

### エラーハンドリング
- **段階的処理**: 各段階での適切なエラー処理
- **ログ出力**: 構造化ログによる問題追跡
- **ユーザー通知**: 分かりやすいエラーメッセージ

## 🚀 デプロイメント

### Docker構成
- **開発環境**: `.devcontainer/` による統一開発環境
- **本番環境**: `docker-compose.yml` による本番デプロイ
- **依存関係**: `requirements.txt` による明確な依存管理

### 監視・運用
- **ヘルスチェック**: `/health` エンドポイントによる死活監視
- **メトリクス**: 処理時間、エラー率等の監視
- **ログ管理**: 構造化ログによる運用支援

## 🔧 開発ツール

### 推奨拡張機能
- **Python**: pylint, black, mypy
- **FastAPI**: FastAPI拡張
- **データベース**: PostgreSQL拡張

### デバッグ支援
- `new/debug.py`: デバッグ用ユーティリティ
- 環境変数 `DEBUG_MODE=true` でデバッグ出力有効化
- SQLAlchemy echo設定による SQL ログ出力

## 📚 参考資料

### 公式ドキュメント
- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic v2](https://docs.pydantic.dev/latest/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)

### プロジェクト固有
- `NEW_SYSTEM_README.md`: システム概要・セットアップ手順
- `.kiro/steering/`: 開発ガイドライン集
- `new/config.py`: 設定項目一覧・説明