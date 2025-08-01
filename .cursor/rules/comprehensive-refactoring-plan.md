---
alwaysApply: false
---

# 包括的リファクタリング計画書

## 🎯 目的
- python-rule.mdcに完全準拠したコードベース構築
- 循環インポート・依存関係の根本的解決
- 関数型プログラミング原則の徹底適用
- 保守性・拡張性の大幅向上

## 📊 現状問題分析

### 重大な構造的問題
1. **循環インポート地獄**: `new.database` ↔ `new.models` ↔ `new.db_handler`
2. **クラス過多**: FastAPI推奨の関数型に反するOOP設計
3. **型定義の混乱**: `User`型と`Dict[str, Any]`の混在
4. **設定散在**: `DEBUG_PRINT_ENABLED`等の設定項目不整合
5. **複雑な依存関係**: 15層の深いインポート依存

### コーディングルール違反
- ❌ クラスベース設計（FileService, ChatService等）
- ❌ 深いネスト構造
- ❌ 型ヒント不統一
- ❌ エラーハンドリングの後処理
- ❌ 同期・非同期の混在

## 🏗️ リファクタリング戦略

### Phase 1: 基盤整理（緊急）
1. **設定統一**: `config.py`の完全整理
2. **型システム統一**: Pydanticモデル導入
3. **インポート正規化**: 絶対インポートへの統一
4. **循環依存解消**: 依存方向の一方向化

### Phase 2: 関数型変換（核心）
1. **クラス削除**: 全サービスクラス→関数変換
2. **RORO パターン**: 入力・出力の明確化
3. **Pure Function**: 副作用の分離
4. **依存性注入**: FastAPI標準パターン採用

### Phase 3: アーキテクチャ再構築（発展）
1. **レイヤー分離**: API→Business→Data
2. **エラーファースト**: Guard Clause導入
3. **非同期最適化**: I/O処理の完全非同期化
4. **パフォーマンス向上**: 遅延読み込み実装

## 🔧 実装詳細

### 1. 設定ファイル統一
```python
# new/config.py (完全版)
from pydantic import BaseSettings
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    # デバッグ設定
    DEBUG_MODE: bool = True
    DEBUG_PRINT_ENABLED: bool = True
    
    # データベース設定
    DATABASE_URL: str
    
    # LLM設定
    LLM_MODEL: str = "phi4-mini"
    LLM_TIMEOUT: int = 300
    
    # パス設定
    BASE_DIR: Path = Path(__file__).parent
    INPUT_DIR: Path = BASE_DIR / "ignored/input_files"
    OUTPUT_DIR: Path = BASE_DIR / "ignored/output_files"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 2. 型定義統一
```python
# new/schemas.py
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class UserSchema(BaseModel):
    id: int
    username: str
    role: str
    email: Optional[str] = None

class FileSchema(BaseModel):
    id: UUID
    filename: str
    status: str
    created_at: datetime
```

### 3. 関数型変換例
```python
# 変換前（クラスベース）
class FileService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_files(self, page: int) -> List[File]:
        return self.db.query(File).offset(page*10).limit(10).all()

# 変換後（関数型）
async def get_files_list(
    page: int = 0,
    db: Session = Depends(get_db)
) -> List[FileSchema]:
    """ファイル一覧取得（関数型・非同期）"""
    if page < 0:
        raise HTTPException(400, "ページ番号は0以上である必要があります")
    
    files = await db.execute(
        select(files_meta).offset(page * 10).limit(10)
    )
    return [FileSchema.from_orm(file) for file in files.fetchall()]
```

### 4. エラーファースト実装
```python
async def process_file_request(
    file_id: UUID,
    db: Session = Depends(get_db)
) -> ProcessingResult:
    """ファイル処理リクエスト（ガードクローズ採用）"""
    
    # ガードクローズ: 早期リターン
    if not file_id:
        raise HTTPException(400, "ファイルIDが必要です")
    
    file_record = await get_file_by_id(file_id, db)
    if not file_record:
        raise HTTPException(404, "ファイルが見つかりません")
    
    if file_record.status == "processing":
        raise HTTPException(409, "ファイルは既に処理中です")
    
    # ハッピーパス（最後）
    return await execute_file_processing(file_record, db)
```

## 📋 実装手順

### 即座実行（緊急修正）
1. **config.py完全書き換え**: 全設定項目の統一
2. **schemas.py作成**: Pydantic型定義導入
3. **循環インポート解消**: dependency graphの一方向化

### 段階実行（系統的変換）
1. **認証系統の関数化**: User型→UserSchema統一
2. **ファイル処理系統の関数化**: FileService→関数群変換
3. **API層の完全書き換え**: 関数型ルート定義
4. **データベース層の最適化**: 純粋関数化

## 🎯 成功指標

### 技術指標
- ✅ インポートエラー0件
- ✅ 循環依存0件
- ✅ クラス定義50%削減
- ✅ 関数pure化80%達成

### 品質指標
- ✅ 起動時間30%短縮
- ✅ API応答時間20%向上
- ✅ コードカバレッジ90%
- ✅ 静的解析エラー0件

## 🚀 実行宣言

このリファクタリング計画に基づき、段階的にコードベース全体を再構築し、
python-rule.mdcに完全準拠した高品質・高性能なFastAPIアプリケーションを実現します。