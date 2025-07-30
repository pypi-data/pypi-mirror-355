import os
import sys
import json
import time
import argparse
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QPropertyAnimation, QTimer, QEasingCurve, pyqtProperty
from .debug_util import debug_print, set_debug_mode
from .main_window import MainWindow

class FadingSplashScreen(QSplashScreen):
    def __init__(self, pixmap):
        super().__init__(pixmap, Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(1.0)
        self._opacity = 1.0

    def get_opacity(self):
        return self._opacity

    def set_opacity(self, opacity):
        self._opacity = opacity
        self.setWindowOpacity(opacity)

    opacity = pyqtProperty(float, get_opacity, set_opacity)

    def fadeOut(self, duration=500, callback=None):
        # アニメーションのパフォーマンスを最適化
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(duration)  # ミリ秒
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.setEasingCurve(QEasingCurve.Linear)  # よりスムーズなアニメーション
        
        # コールバック前に事前準備を行う
        if callback:
            self.animation.valueChanged.connect(lambda v: QApplication.processEvents())  # アニメーション中もUIを更新
            
            # アニメーション完了前（80%まで進んだ時点）で事前にコールバックを実行
            def early_callback(v):
                if v <= 0.2 and not hasattr(self, '_callback_executed'):
                    self._callback_executed = True
                    callback()
            
            self.animation.valueChanged.connect(early_callback)
        
        self.animation.start(QPropertyAnimation.DeleteWhenStopped)  # 使い終わったらメモリを解放
        debug_print("[debug] スプラッシュスクリーンのフェードアウトを開始")

def get_default_config_path():
    # XDG_CONFIG_HOME or ~/.config/fujielab_launcher/config.json など
    config_dir = os.environ.get("XDG_CONFIG_HOME")
    if not config_dir:
        config_dir = os.path.join(str(Path.home()), ".config")
    config_dir = os.path.join(config_dir, "fujielab_launcher")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "config.json")

def create_default_config(config_path):
    # システムPython
    import platform
    try:
        if platform.system() == "Windows":
            import subprocess
            sys_path = subprocess.check_output(["where", "python"], universal_newlines=True).strip().split("\n")[0]
        else:
            import subprocess
            sys_path = subprocess.check_output(["which", "python3"], universal_newlines=True).strip()
    except Exception:
        sys_path = sys.executable
    config = {
        "interpreter": sys_path,
        "workdir": os.getcwd()
    }
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def ensure_config(reset=False, ask_dialog=None):
    config_path = get_default_config_path()
    if reset and os.path.exists(config_path):
        if ask_dialog:
            res = ask_dialog()
            if res == QMessageBox.No:
                return config_path
        create_default_config(config_path)
    elif not os.path.exists(config_path):
        create_default_config(config_path)
    return config_path

def ask_reset_dialog():
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Question)
    msg.setWindowTitle("設定ファイルの再作成確認")
    msg.setText("コマンドラインオプションにより設定ファイルを新規作成します。よろしいですか？\n(既存の設定は上書きされます)")
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    return msg.exec_()

def parse_arguments():
    """コマンドライン引数を解析します"""
    parser = argparse.ArgumentParser(description='Fujielab Utility Launcher')
    parser.add_argument('-d', '--debug', action='store_true', 
                        help='デバッグモードを有効にします。詳細なログメッセージが表示されます。')
    parser.add_argument('--reset-config', action='store_true',
                        help='設定ファイルを初期化します。既存の設定は上書きされます。')
    parser.add_argument('--version', action='store_true',
                        help='バージョン情報を表示して終了します。')
    
    return parser.parse_args()

def main():
    # コマンドライン引数の解析
    args = parse_arguments()
    
    # デバッグモードの設定
    set_debug_mode(args.debug)
    if args.debug:
        debug_print("[debug] デバッグモードで起動しました")
    
    # バージョン情報表示
    if args.version:
        print("Fujielab Utility Launcher v0.1.0")
        return 0
    
    # 設定ファイルのリセットフラグ
    reset_config = args.reset_config
    
    app = QApplication(sys.argv)
    
    # スプラッシュスクリーン表示開始時間を記録
    splash_start_time = time.time()
    
    # スプラッシュスクリーンの表示
    splash_pix = QPixmap(os.path.join(os.path.dirname(__file__), 'resources', 'splash.png'))
    splash = FadingSplashScreen(splash_pix)
    splash.setAutoFillBackground(True)
    splash.show()
    app.processEvents()
    
    # アプリケーションアイコンを設定 - すぐに開始して並行処理
    try:
        # まず.icoファイルを優先して試す（Windowsでより適切）
        ico_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon.ico')
        png_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon.png')
        
        if os.path.exists(ico_path):
            app.setWindowIcon(QIcon(ico_path))
            debug_print(f"[debug] アイコンを設定しました: {ico_path}")
        elif os.path.exists(png_path):
            app.setWindowIcon(QIcon(png_path))
            debug_print(f"[debug] アイコンを設定しました: {png_path}")
        else:
            debug_print("[debug] アイコンファイルが見つかりません")
    except Exception as e:
        debug_print(f"[debug] アイコン設定エラー: {e}")
    
    # 1秒間スプラッシュスクリーンを表示中にメインウィンドウの初期化を行う
    config_path = ensure_config(reset=reset_config, ask_dialog=ask_reset_dialog if reset_config else None)
    debug_print("[debug] メインウィンドウの事前初期化を開始")
    win = MainWindow()
    # メインウィンドウを非表示で準備する（初期化処理やリソース読み込みを完了させる）
    win.hide()
    app.processEvents()  # UIイベントを処理してレスポンシブさを維持
    debug_print("[debug] メインウィンドウの初期化完了")
    
    # 残りのスプラッシュスクリーン表示時間を計算（最低1秒間は表示）
    elapsed_time = time.time() - splash_start_time
    remaining_time = max(0, 1.0 - elapsed_time)
    debug_print(f"[debug] 経過時間: {elapsed_time:.2f}秒、残り時間: {remaining_time:.2f}秒")
    if remaining_time > 0:
        time.sleep(remaining_time)
    
    # スプラッシュスクリーンをフェードアウトさせてから、メインウィンドウを表示する
    def show_main_window():
        win.show()
        splash.hide()  # finish()より高速
        debug_print("[debug] スプラッシュスクリーン終了後にメインウィンドウを表示")
    
    # フェードアウト開始（短くして200ミリ秒に）
    splash.fadeOut(200, show_main_window)
    
    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())
