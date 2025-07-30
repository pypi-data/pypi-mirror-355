"""
デバッグユーティリティモジュール
コマンドライン引数 -d または --debug が指定されている場合のみデバッグメッセージを出力します
"""

import sys

# グローバル変数としてデバッグモードのフラグを定義
# 初期設定ではコマンドライン引数をチェックして設定
debug_mode = any(arg in ['-d', '--debug'] for arg in sys.argv)

def set_debug_mode(enabled=True):
    """
    デバッグモードを明示的に設定します
    """
    global debug_mode
    debug_mode = enabled
    if debug_mode:
        debug_print("[debug] デバッグモードを有効化しました")

def debug_print(*args, **kwargs):
    """
    デバッグモードが有効な場合のみメッセージを出力します
    """
    if debug_mode:
        print(*args, **kwargs)

def error_print(*args, **kwargs):
    """
    エラーメッセージは常に出力します
    """
    print(*args, **kwargs)
