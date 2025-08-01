# new/debug.py
# デバッグ機能

import logging
import traceback
from typing import Any, Optional
from new.config import DEBUG_PRINT_ENABLED, LOGGER

def debug_print(*args, **kwargs):
    """
    デバッグプリント関数
    config.pyのDEBUG_PRINT_ENABLEDスイッチでon/off可能
    コンソールには出力せず、ログファイルのみに出力
    """
    if DEBUG_PRINT_ENABLED:
        message = " ".join(str(arg) for arg in args)
        LOGGER.debug(f"[DEBUG_PRINT] {message}")

def debug_log(*args, **kwargs):
    """
    デバッグログ関数
    コンソールには出力せず、ログファイルのみに出力
    """
    if DEBUG_PRINT_ENABLED:
        message = " ".join(str(arg) for arg in args)
        LOGGER.debug(f"[DEBUG_LOG] {message}")

def debug_error(error: Exception, context: str = ""):
    """
    エラーデバッグ関数
    エラーのみコンソールに出力
    """
    if DEBUG_PRINT_ENABLED:
        error_msg = f"[DEBUG_ERROR] {context}: {type(error).__name__}: {str(error)}"
        print(error_msg)  # エラーのみコンソールに出力
        LOGGER.error(f"[DEBUG_ERROR] {context}: {type(error).__name__}: {str(error)}")
        
        # スタックトレースも出力
        stack_trace = traceback.format_exc()
        if stack_trace and stack_trace != "NoneType: None\n":
            print(f"[DEBUG_ERROR_STACK] {context}:")
            print(stack_trace)
            LOGGER.error(f"[DEBUG_ERROR_STACK] {context}:\n{stack_trace}")

def debug_js_error(error_msg: str, context: str = ""):
    """
    JavaScriptエラーデバッグ関数
    JavaScriptエラーをコンソールに出力
    """
    if DEBUG_PRINT_ENABLED:
        error_msg_formatted = f"[DEBUG_JS_ERROR] {context}: {error_msg}"
        print(error_msg_formatted)  # JavaScriptエラーもコンソールに出力
        LOGGER.error(f"[DEBUG_JS_ERROR] {context}: {error_msg}")

def debug_function(func_name: str, **kwargs):
    """
    関数呼び出しデバッグ関数
    コンソールには出力せず、ログファイルのみに出力
    """
    if DEBUG_PRINT_ENABLED:
        args_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        message = f"[DEBUG_FUNCTION] {func_name}({args_str})"
        LOGGER.debug(message)

def debug_return(func_name: str, result: Any):
    """
    関数戻り値デバッグ関数
    コンソールには出力せず、ログファイルのみに出力
    """
    if DEBUG_PRINT_ENABLED:
        message = f"[DEBUG_RETURN] {func_name}() -> {result}"
        LOGGER.debug(message) 