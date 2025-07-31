# 🚫 インポートエラー再発防止ガイド

## 📋 **根本問題と解決策**

### 🚨 **発生していた問題**
```
ModuleNotFoundError: No module named 'config'
ModuleNotFoundError: No module named 'api'
ModuleNotFoundError: No module named 'services'
```

### ✅ **解決方法**
1. **相対インポート全廃**: `from config import` → `from new.config import`
2. **絶対パス統一**: 全モジュールで `new.` プレフィックス必須
3. **パッケージ構造整合**: ディレクトリパスとインポートパスの一致

## 🎯 **絶対インポート原則**

### **✅ 正しいインポート書き方**
```python
# 設定・ログ
from new.config import LOGGER, DB_ENGINE, STATIC_DIR

# データベース
from new.database.connection import get_db_connection
from new.database.models import files_blob

# 認証
from new.auth import get_optional_user
from new.auth_utils import require_admin

# API
from new.api.files import router as files_router

# サービス
from new.services.ocr.factory import OCREngineFactory
from new.services.processing.pipeline import ProcessingPipeline

# ルート
from new.routes.ui import router as ui_router
```

### **❌ 絶対に使用禁止**
```python
# 相対インポート（エラーの原因）
from config import LOGGER          # ❌
from database import init_db       # ❌
from api import files_router       # ❌
from services.ocr import Factory   # ❌
from auth import get_user          # ❌
```

## 📂 **パッケージ構造対応表**

| ディレクトリ | 正しいインポート |
|-------------|----------------|
| `new/config.py` | `from new.config import` |
| `new/auth.py` | `from new.auth import` |
| `new/database/` | `from new.database.connection import` |
| `new/api/files.py` | `from new.api.files import` |
| `new/services/ocr/` | `from new.services.ocr.factory import` |
| `new/routes/ui.py` | `from new.routes.ui import` |
| `new/templates/` | `TEMPLATES_DIR = BASE_DIR / "templates"` |
| `new/static/` | `STATIC_DIR = BASE_DIR / "static"` |

## 🔧 **ディレクトリパス設定**

### **config.py での正しい設定**
```python
from pathlib import Path

# ベースディレクトリ設定
BASE_DIR = Path(__file__).parent

# 静的ファイル・テンプレート
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# 入出力ディレクトリ
INPUT_DIR = Path("ignored/input_files")
OUTPUT_DIR = Path("ignored/output_files")
```

## 🚨 **よくある間違いパターン**

### **Pattern 1: 混在インポート**
```python
# ❌ 混在（一貫性なし）
from new.config import LOGGER
from database import get_connection    # 相対！
from new.api.files import router
```

### **Pattern 2: 部分的絶対パス**
```python
# ❌ 中途半端
from new.services.processing import Pipeline
from services.ocr import Factory       # 相対！
```

### **Pattern 3: パス解決ミス**
```python
# ❌ パス不整合
STATIC_DIR = "static"                  # 相対パス
templates = Jinja2Templates(directory=str(STATIC_DIR))  # エラー発生
```

## 📝 **新規ファイル作成時チェックリスト**

### **必須確認事項**
- [ ] 全インポートが `new.` で始まっている
- [ ] 相対インポート（`from config`, `from api` など）が存在しない
- [ ] パスは `BASE_DIR` を基準とした絶対パス
- [ ] `__init__.py` ファイルが必要な場所に存在

### **テストコマンド**
```bash
# インポートエラーチェック
cd /workspace && python -c "
import sys
sys.path.insert(0, '/workspace')
from new.main import app
print('✅ インポート成功')
"

# 相対インポート検出
grep -r "^from config import" new/
grep -r "^from database import" new/
grep -r "^from api import" new/
grep -r "^from services import" new/
```

## 🔄 **修正プロセス**

### **段階1: 相対インポート特定**
```bash
grep -r "^from config\|^from database\|^from api\|^from services" new/
```

### **段階2: 一括置換**
```bash
# 手動で各ファイルを修正
# 例: from config import → from new.config import
```

### **段階3: 動作確認**
```bash
cd /workspace && python -c "from new.main import app"
```

### **段階4: サーバー起動テスト**
```bash
cd /workspace && python run_app.py --app new
```

## 📊 **修正実績**

**修正対象ファイル一覧:**
- `new/main.py` - 全インポート
- `new/api/*.py` - 6ファイル
- `new/database/*.py` - 2ファイル  
- `new/services/**/*.py` - 4ファイル
- `new/routes/ui.py` - 認証関連
- `new/config.py` - パス設定

**修正パターン統計:**
- `from config import` → `from new.config import`: 15箇所
- `from database import` → `from new.database import`: 3箇所
- `from api import` → `from new.api import`: 5箇所
- `from services import` → `from new.services import`: 4箇所

## 🎯 **今後の運用方針**

1. **新規ファイル作成時**: 必ず絶対インポートで開始
2. **コードレビュー**: インポート文を最優先チェック
3. **CI/CD**: インポートエラー検出の自動化
4. **ドキュメント**: このガイドを定期的に更新

---
**このガイドに従うことで、インポートエラーの再発を完全に防止できます。**