# REM: app/fastapi_main.py @2025-07-18 00:00 UTC +9
# REM: FastAPI 起動エントリ。ここではアプリ生成 & ルーター登録だけを行う。
import os
import uvicorn
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# REM: 共有設定
BASE_DIR      = os.path.dirname(__file__)         # /workspace/app
STATIC_DIR    = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app = FastAPI()

# REM: metricsエンドポイントのアクセスログを無効化するミドルウェア
@app.middleware("http")
async def filter_metrics_logs(request: Request, call_next):
    response = await call_next(request)
    
    # metricsエンドポイントのアクセスログを抑制
    if request.url.path == "/metrics":
        # エラーの場合のみログ出力
        if response.status_code >= 400:
            logging.getLogger("uvicorn.access").info(
                f'{request.client.host}:{request.client.port} - '
                f'"{request.method} {request.url.path} HTTP/1.1" {response.status_code}'
            )
        # 正常時はログを抑制（何もしない）
    
    return response

# REM: テンプレートディレクトリ設定
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# REM: staticファイル配信設定
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# REM: 既存ルーター一括登録
from app.routes import router as api_router
app.include_router(api_router)

# REM: プロンプト配信用エンドポイント登録
from app.routes.ingest_api import router as ingest_api_router
from app.routes.metrics import router as metrics_router
from app.routes.try_ocr import router as try_ocr_router
from app.routes.dict_editor import router as dict_editor_router
app.include_router(metrics_router)
app.include_router(try_ocr_router)
app.include_router(dict_editor_router)

# prefix="/api" の下に "/refine_prompt" をマウント
app.include_router(ingest_api_router, prefix="/api")

# REM: カスタムログフィルター（metricsの正常アクセスを除外）
class MetricsLogFilter(logging.Filter):
    def filter(self, record):
        # ログメッセージにmetricsが含まれ、かつ200 OKの場合は除外
        if hasattr(record, 'getMessage'):
            message = record.getMessage()
            if '/metrics' in message and '200 OK' in message:
                return False
        return True

# REM: uvicornのアクセスログにフィルターを適用
def setup_logging():
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.addFilter(MetricsLogFilter())

# REM: 開発用スタンドアロン実行
if __name__ == "__main__":
    setup_logging()
    uvicorn.run(
        "app.fastapi_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
