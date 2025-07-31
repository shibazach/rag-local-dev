# src/error_handler.py
import sys, traceback
from OLD.src.utils import debug_print

# REM: エラーハンドラーを設定する関数
def install_global_exception_handler():
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        debug_print("💥 予期しないエラーが発生しました:")
        traceback.print_exception(exc_type, exc_value, exc_traceback)

    sys.excepthook = handle_exception
