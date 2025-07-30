from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QMenuBar, QAction, QSizePolicy, QMdiArea, QFileDialog, QMessageBox
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt, QPoint, QRect
from .sticky_mdi import StickyMdiSubWindow
from .script_runner import ScriptRunnerWidget
from .shell_runner import ShellRunnerWidget
from .config_manager import LauncherConfigManager
from .debug_util import debug_print, error_print
import platform
from PyQt5.QtWidgets import QApplication
from pathlib import Path
import math

class CustomMdiArea(QMdiArea):
    """
    カスタムMDIエリアクラス
    ウィンドウの元の位置に基づいて、最も近い適切なタイル位置に配置する機能を提供
    """
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def tileSubWindows(self):
        """
        サブウィンドウをタイル状に配置する
        各ウィンドウの元の位置から最も近いタイル位置に配置
        """
        if not self.subWindowList():
            return
            
        # アクティブなサブウィンドウ数
        windows = self.subWindowList()
        windows_count = len(windows)
        
        # ウィンドウ無しまたは1つだけなら最大化
        if windows_count == 0:
            return
        if windows_count == 1:
            windows[0].showMaximized()
            return
        
        # タイルレイアウトのグリッドサイズを決定
        # できるだけ正方形に近くなるように列数と行数を計算
        cols = math.ceil(math.sqrt(windows_count))
        rows = math.ceil(windows_count / cols)
        
        # タイルのセルサイズを計算
        area_width = self.width()
        area_height = self.height()
        cell_width = area_width / cols
        cell_height = area_height / rows
        
        debug_print(f"[debug] タイル配置: {windows_count}ウィンドウ, {cols}列 x {rows}行, セルサイズ: {cell_width}x{cell_height}")
        
        # 各グリッドセル位置を計算
        grid_cells = []
        for row in range(rows):
            for col in range(cols):
                if len(grid_cells) < windows_count:
                    cell_rect = QRect(
                        int(col * cell_width),
                        int(row * cell_height),
                        int(cell_width),
                        int(cell_height)
                    )
                    # セルの中心点を計算
                    cell_center = QPoint(
                        int(cell_rect.left() + cell_rect.width() / 2),
                        int(cell_rect.top() + cell_rect.height() / 2)
                    )
                    grid_cells.append((cell_rect, cell_center))
        
        # 各ウィンドウの現在の位置を記憶
        window_positions = []
        for window in windows:
            # ウィンドウの中心点を計算
            window_rect = window.geometry()
            window_center = QPoint(
                int(window_rect.left() + window_rect.width() / 2),
                int(window_rect.top() + window_rect.height() / 2)
            )
            window_positions.append((window, window_center))
        
        # 各グリッドセルに最も近いウィンドウを割り当てる
        assigned_windows = set()
        assignments = []  # (window, cell_rect) のリスト
        
        # 各グリッドセルについて、最も近いまだ割り当てられていないウィンドウを見つける
        for cell_rect, cell_center in grid_cells:
            best_window = None
            min_distance = float('inf')
            
            for window, window_center in window_positions:
                if window in assigned_windows:
                    continue
                
                # 中心点間の距離を計算
                distance = math.sqrt(
                    (cell_center.x() - window_center.x()) ** 2 +
                    (cell_center.y() - window_center.y()) ** 2
                )
                
                if distance < min_distance:
                    min_distance = distance
                    best_window = window
            
            if best_window:
                assigned_windows.add(best_window)
                assignments.append((best_window, cell_rect))
        
        # 残っているウィンドウがあれば、残りのセルに割り当て
        remaining_windows = [w for w, _ in window_positions if w not in assigned_windows]
        remaining_cells = [cell for cell, _ in grid_cells[len(assignments):]]
        
        for window, cell_rect in zip(remaining_windows, remaining_cells):
            assignments.append((window, cell_rect))
        
        # ウィンドウを新しい位置に移動
        for window, cell_rect in assignments:
            window.setGeometry(cell_rect)
            
        debug_print(f"[debug] タイル配置完了: {len(assignments)}ウィンドウを配置しました")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        debug_print("[debug] ======== MainWindow初期化開始 ========")
        self.setWindowTitle('FUJIE Lab. Program Launcher')
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.menu_bar = QMenuBar(self)
        self.menu_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.menu_bar, stretch=0)
        self.mdi = CustomMdiArea()
        layout.addWidget(self.mdi, stretch=1)
        self.initMenu()

        self.global_config = {}
        # サブウィンドウの設定キャッシュ
        self.launcher_cache = []
        # 終了処理中フラグの初期化
        self.in_closing = False

        # MDIエリアのサブウィンドウアクティブ化時に設定を保存
        self.mdi.subWindowActivated.connect(self.saveAllLaunchers)

        # 設定マネージャの初期化
        self.config_manager = LauncherConfigManager()
        self._geometry_restored = False
        self._suppress_save = True

        # 前回の設定を復元
        debug_print("[debug] 前回の設定を復元します")
        self.restoreAllLaunchers()
        debug_print("[debug] ======== MainWindow初期化完了 ========")

    def initMenu(self):
        menubar = self.menu_bar
        menubar.clear()
        fileMenu = menubar.addMenu('ファイル')
        newPythonLauncherAct = QAction('新規Pythonランチャー', self)
        newPythonLauncherAct.setShortcut(QKeySequence('Ctrl+N'))
        newPythonLauncherAct.triggered.connect(lambda: self.createPythonLauncherWindow())
        fileMenu.addAction(newPythonLauncherAct)
        newShellLauncherAct = QAction('新規シェルランチャー', self)
        newShellLauncherAct.setShortcut(QKeySequence('Shift+Ctrl+N'))
        newShellLauncherAct.triggered.connect(lambda: self.createShellLauncherWindow())
        fileMenu.addAction(newShellLauncherAct)
        fileMenu.addSeparator()
        importAct = QAction('設定のインポート', self)
        importAct.setShortcut(QKeySequence('Ctrl+I'))
        importAct.triggered.connect(self.importConfig)
        fileMenu.addAction(importAct)
        exportAct = QAction('設定のエクスポート', self)
        exportAct.setShortcut(QKeySequence('Shift+Ctrl+S'))
        exportAct.triggered.connect(self.exportConfig)
        fileMenu.addAction(exportAct)
        fileMenu.addSeparator()
        exitAct = QAction('終了', self)
        exitAct.setShortcut(QKeySequence.Quit)
        exitAct.triggered.connect(self.close)
        fileMenu.addAction(exitAct)
        arrangeMenu = menubar.addMenu('整列')
        tileAct = QAction('タイル', self)
        tileAct.triggered.connect(self.mdi.tileSubWindows)
        arrangeMenu.addAction(tileAct)
        cascadeAct = QAction('カスケード', self)
        cascadeAct.triggered.connect(self.mdi.cascadeSubWindows)
        arrangeMenu.addAction(cascadeAct)

        # 設定メニュー追加
        settingsMenu = menubar.addMenu('設定')
        settingsAct = QAction('グローバル設定', self)
        settingsAct.setShortcut(QKeySequence('Ctrl+,'))
        settingsAct.triggered.connect(self.openSettingsDialog)
        settingsMenu.addAction(settingsAct)

        menu_style = """
        QMenuBar {
            background: #ffffff;
            border-bottom: 1px solid #b0b0b0;
            font-size: 14px;
            font-weight: bold;
            padding: 0 2px;
            height: 28px;
        }
        QMenuBar::item {
            background: transparent;
            color: #222;
            padding: 4px 8px 4px 8px;
            border-radius: 4px 4px 0 0;
            margin: 0 1px;
        }
        QMenuBar::item:selected {
            background: #e6e6e6;
            color: #1565c0;
        }
        QMenu {
            background: #ffffff;
            border: 1px solid #b0b0b0;
            font-size: 13px;
        }
        QMenu::item {
            padding: 6px 24px 6px 16px;
            border-radius: 4px;
        }
        QMenu::item:selected {
            background: #e6e6e6;
            color: #1565c0;
        }
        """
        menubar.setStyleSheet(menu_style)

    def createPythonLauncherWindow(self, config=None, geometry=None):
        sub = StickyMdiSubWindow()
        # グローバル設定を反映したconfigを生成
        if config is None:
            config = {}
            config_manager = self.config_manager
            config['interpreter'] = config_manager.get_default_interpreter_path()
            config['workdir'] = config_manager.get_default_workdir()
        # print(config)
        # import ipdb; ipdb.set_trace()
        widget = ScriptRunnerWidget(config=config)
        sub.setWidget(widget)
        sub.setAttribute(Qt.WA_DeleteOnClose)
        sub.resize(500, 300)
        self.mdi.addSubWindow(sub)
        if geometry:
            sub.setGeometry(*geometry)
        sub.show()
        sub.installEventFilter(self)
        widget.config_changed_callback = self.saveAllLaunchers
        self.saveAllLaunchers()

    def createShellLauncherWindow(self, config=None, geometry=None):
        sub = StickyMdiSubWindow()
        from .shell_runner import ShellRunnerWidget
        # グローバル設定を反映したconfigを生成
        if config is None:
            config = {}
            config_manager = self.config_manager
            config['workdir'] = config_manager.get_default_workdir()
        widget = ShellRunnerWidget()
        widget.apply_config(config)
        sub.setWidget(widget)
        sub.setAttribute(Qt.WA_DeleteOnClose)
        sub.resize(500, 300)
        self.mdi.addSubWindow(sub)
        if geometry:
            sub.setGeometry(*geometry)
        sub.show()
        sub.installEventFilter(self)
        widget.config_changed_callback = self.saveAllLaunchers
        self.saveAllLaunchers()

    def eventFilter(self, obj, event):
        # ウィンドウ移動・リサイズ・クローズ時に保存
        from PyQt5.QtCore import QEvent
        if event.type() in (QEvent.Move, QEvent.Resize, QEvent.Close):
            self.saveAllLaunchers()
        return super().eventFilter(obj, event)

    def importConfig(self):
        path, _ = QFileDialog.getOpenFileName(self, "設定ファイルのインポート", filter="YAML Files (*.yaml *.yml)")
        if path:
            self.config_manager.import_config(path)
            reply = QMessageBox.question(self, "再起動確認", "設定ファイルをインポートしました。再起動しますか？", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                import sys, os
                os.execv(sys.executable, [sys.executable] + sys.argv)

    def exportConfig(self):
        path, _ = QFileDialog.getSaveFileName(self, "設定ファイルのエクスポート", filter="YAML Files (*.yaml *.yml)")
        if path:
            self.config_manager.export(path)
            QMessageBox.information(self, "エクスポート完了", "設定ファイルをエクスポートしました。")

    def saveAllLaunchers(self):
        if getattr(self, '_suppress_save', False):
            debug_print("[debug] saveAllLaunchers: 保存抑制中のため処理をスキップします")
            return

        launchers = []
        subwindow_count = len(self.mdi.subWindowList())
        in_closing = hasattr(self, 'in_closing') and self.in_closing
        debug_print(f"[debug] saveAllLaunchers: サブウィンドウ数 {subwindow_count}, 終了処理中={in_closing}")

        # 終了処理中はキャッシュを使用（closeEventで更新済み）
        if in_closing and hasattr(self, 'launcher_cache') and self.launcher_cache:
            debug_print(f"[debug] 終了処理中: キャッシュからランチャー設定を使用 ({len(self.launcher_cache)}個)")
            launchers = self.launcher_cache

            # キャッシュ内容のデバッグ出力
            for idx, launcher in enumerate(self.launcher_cache):
                ltype = launcher.get('type')
                config = launcher.get('config', {})
                if ltype == 'python':
                    script = config.get('script', '(未設定)')
                    debug_print(f"[debug] キャッシュ[{idx}] Python設定: script={Path(script).name if script else '(未設定)'}")
                else:
                    cmdline = config.get('cmdline', '(未設定)')
                    debug_print(f"[debug] キャッシュ[{idx}] Shell設定: cmdline={cmdline[:20] + '...' if len(cmdline) > 20 else cmdline}")

        # サブウィンドウが存在する場合、現在の状態からキャッシュを更新
        elif subwindow_count > 0:
            debug_print("[debug] 現在のサブウィンドウから設定を取得してキャッシュ更新")

            # 終了処理中でなければキャッシュをクリア
            if not in_closing:
                self.launcher_cache = []

            for sub in self.mdi.subWindowList():
                widget = sub.widget()
                if isinstance(widget, ScriptRunnerWidget):
                    ltype = 'python'
                elif isinstance(widget, ShellRunnerWidget):
                    ltype = 'shell'
                else:
                    continue

                geo = sub.geometry()
                try:
                    config = widget.get_config()

                    # 設定内容のデバッグ出力
                    if ltype == 'python':
                        script = config.get('script', '(未設定)')
                        interpreter = config.get('interpreter', '(未設定)')
                        workdir = config.get('workdir', '(未設定)')
                        debug_print(f"[debug] Python設定: script={Path(script).name if script else '(未設定)'}, "
                            f"interpreter={Path(interpreter).name if interpreter else '(未設定)'}, "
                            f"workdir={Path(workdir).name if workdir else '(未設定)'}")
                    else:
                        cmdline = config.get('cmdline', '(未設定)')
                        workdir = config.get('workdir', '(未設定)')
                        debug_print(f"[debug] Shell設定: cmdline={cmdline[:20] + '...' if len(cmdline) > 20 else cmdline}, "
                            f"workdir={Path(workdir).name if workdir else '(未設定)'}")

                    launcher_info = {
                        'type': ltype,
                        'geometry': [geo.x(), geo.y(), geo.width(), geo.height()],
                        'config': config
                    }

                    launchers.append(launcher_info)

                    # 終了処理中でなければキャッシュも更新
                    if not in_closing:
                        self.launcher_cache.append(launcher_info)

                except Exception as e:
                    error_print(f"[error] ウィジェットからの設定取得エラー: {e}")
        # サブウィンドウが0の場合でも、終了処理でなければキャッシュが破棄されないようにする
        elif not in_closing and hasattr(self, 'launcher_cache') and self.launcher_cache:
            debug_print(f"[debug] サブウィンドウ無し＆終了処理でない: キャッシュからランチャー設定を使用 ({len(self.launcher_cache)}個)")
            launchers = self.launcher_cache

        main_geo = self.geometry()
        self.config_manager.set_launchers(launchers)
        self.config_manager.set_mainwindow_geometry([main_geo.x(), main_geo.y(), main_geo.width(), main_geo.height()])
        self.config_manager.set_mainwindow_state(self.isMaximized())
        debug_print(f"[debug] 設定を保存しました: ランチャー数={len(launchers)}")

    def restoreWindowGeometry(self):
        geo = self.config_manager.get_mainwindow_geometry()
        maximized = self.config_manager.get_mainwindow_state()
        if geo and len(geo) == 4:
            self.setGeometry(*geo)
        if maximized:
            self.showMaximized()

    def restoreAllLaunchers(self):
        launchers = self.config_manager.get_launchers()
        debug_print(f"[debug] 設定ファイルから{len(launchers)}個のランチャー設定を読み込みました")

        # キャッシュも復元
        self.launcher_cache = launchers.copy() if launchers else []

        for idx, l in enumerate(launchers):
            ltype = l.get('type')
            geometry = l.get('geometry')
            config = l.get('config', {})

            if ltype == 'python':
                script = config.get('script', '(未設定)')
                debug_print(f"[debug] {idx+1}番目: Python設定を復元 script={script}")
                self.createPythonLauncherWindow(config=config, geometry=geometry)
            elif ltype == 'shell':
                cmdline = config.get('cmdline', '(未設定)')
                debug_print(f"[debug] {idx+1}番目: Shell設定を復元 cmdline={cmdline[:20]+'...' if len(cmdline) > 20 else cmdline}")
                self.createShellLauncherWindow(config=config, geometry=geometry)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.menu_bar.setMinimumWidth(self.width())
        self.saveAllLaunchers()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.saveAllLaunchers()

    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, '_geometry_restored', False):
            geo = self.config_manager.get_mainwindow_geometry()
            maximized = self.config_manager.get_mainwindow_state()
            if maximized:
                if platform.system() == "Darwin":
                    screen = QApplication.primaryScreen().availableGeometry()
                    self.move(screen.x(), screen.y())
                    self.resize(screen.width(), screen.height())
                else:
                    self.showMaximized()
            elif geo and len(geo) == 4:
                self.setGeometry(*geo)
            self._geometry_restored = True
            self._suppress_save = False  # 復元後に保存許可

    def changeEvent(self, event):
        from PyQt5.QtCore import QEvent
        if event.type() == QEvent.WindowStateChange:
            self.saveAllLaunchers()
        super().changeEvent(event)

    def openSettingsDialog(self):
        from .settings_dialog import GlobalSettingsDialog
        from .script_runner import ScriptRunnerWidget
        interp_map = ScriptRunnerWidget().get_interpreters()
        current_label = self.config_manager.get_default_interpreter_label()
        current_dir = self.config_manager.get_default_workdir()
        dialog = GlobalSettingsDialog(self, envs=list(interp_map.keys()), current_env=current_label, current_dir=current_dir, get_interpreters_func=lambda force_refresh=False: ScriptRunnerWidget().get_interpreters(force_refresh))
        if dialog.exec_() == dialog.Accepted:
            label, workdir = dialog.get_values()
            path = interp_map.get(label, "python")
            self.config_manager.set_default_interpreter(label, path)
            self.config_manager.set_default_workdir(workdir)

    def closeEvent(self, event):
        """メインウィンドウが閉じられるときに設定を保存し、全てのサブウィンドウを明示的に閉じる"""
        debug_print("[debug] ======== MainWindow closeEvent: 終了処理開始 ========")

        # 終了処理中フラグをセット(先にセットして、サブウィンドウの個別保存を防止)
        self.in_closing = True
        self._suppress_save = False  # 強制的に保存を有効化

        # キャッシュ更新のために全サブウィンドウ設定を取得
        debug_print("[debug] サブウィンドウの設定をキャッシュ（終了前の最終状態）")
        subwindow_count = len(self.mdi.subWindowList())
        debug_print(f"[debug] 現在のサブウィンドウ数: {subwindow_count}")

        # キャッシュをクリアして最新状態を反映
        self.launcher_cache = []

        for sub in self.mdi.subWindowList():
            widget = sub.widget()
            if not widget:
                continue

            if isinstance(widget, ScriptRunnerWidget):
                ltype = 'python'
            elif isinstance(widget, ShellRunnerWidget):
                ltype = 'shell'
            else:
                continue

            geo = sub.geometry()
            try:
                config = widget.get_config()
                launcher_info = {
                    'type': ltype,
                    'geometry': [geo.x(), geo.y(), geo.width(), geo.height()],
                    'config': config
                }
                self.launcher_cache.append(launcher_info)

                # 設定内容のデバッグ出力
                if ltype == 'python':
                    script = config.get('script', '(未設定)')
                    interpreter = config.get('interpreter', '(未設定)')
                    workdir = config.get('workdir', '(未設定)')
                    debug_print(f"[debug] キャッシュしたPython設定: script={script}, interpreter={interpreter}")
                else:
                    cmdline = config.get('cmdline', '(未設定)')
                    workdir = config.get('workdir', '(未設定)')
                    debug_print(f"[debug] キャッシュしたShell設定: cmdline={cmdline[:30]}...")

            except Exception as e:
                error_print(f"[error] クローズ時のウィジェット設定取得エラー: {e}")

        debug_print(f"[debug] {len(self.launcher_cache)}個のランチャー設定をキャッシュしました")

        # 設定を保存（キャッシュから保存される）
        self.saveAllLaunchers()
        debug_print("[debug] 設定ファイルに保存しました")

        # サブウィンドウを閉じる
        debug_print("[debug] サブウィンドウを閉じます")
        for window in self.mdi.subWindowList():
            window.close()

        debug_print("[debug] ======== MainWindow closeEvent: 終了処理完了 ========")
        event.accept()
