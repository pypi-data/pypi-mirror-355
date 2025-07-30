from PyQt5.QtWidgets import QWidget, QTextEdit, QLabel, QLineEdit, QPushButton, QHBoxLayout, QFormLayout, QVBoxLayout, QSizePolicy, QDialog, QComboBox, QFileDialog, QGridLayout
from PyQt5.QtCore import QProcess, Qt
import subprocess
import json
from pathlib import Path
from .settings_dialog import PythonSettingsDialog
from .debug_util import debug_print, error_print

interpreter_cache = {}

class ScriptRunnerWidget(QWidget):
    def __init__(self, config=None):
        super().__init__()
        self.process = None
        self.interpreter_path = ""
        self.script_path = ""
        self.working_dir = ""
        self.interpreter_map = {}
        # バッファーを追加
        self.stdout_buffer = ""
        self.stderr_buffer = ""
        self.output_view = QTextEdit()
        self.output_view.setReadOnly(True)
        self.interpreter_label = QLabel("インタプリタ:")
        self.script_label = QLabel("スクリプト:")
        self.dir_label = QLabel("作業ディレクトリ:")
        # --- UI部品をComboBox/ボタン付きに変更 ---
        self.interpreter_combo = QComboBox()
        self.script_value = QLineEdit()
        self.script_value.setReadOnly(True)
        self.script_select_button = QPushButton("選択")
        self.dir_value = QLineEdit()
        self.dir_value.setReadOnly(True)
        self.dir_select_button = QPushButton("選択")
        # インタプリタリストをセット
        interp_map = self.get_interpreters()
        self.interpreter_map = interp_map
        self.interpreter_combo.addItems(list(interp_map.keys()))
        # --- レイアウト ---
        for lineedit in [self.script_value, self.dir_value]:
            lineedit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        for label in [self.interpreter_label, self.script_label, self.dir_label]:
            label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.run_button = QPushButton("実行")
        self.stop_button = QPushButton("停止")
        self.run_button.setFixedHeight(26)
        self.stop_button.setFixedHeight(26)
        self.script_select_button.setFixedSize(48, 24)
        self.dir_select_button.setFixedSize(48, 24)
        self.interpreter_combo.setFixedHeight(24)
        self.script_value.setFixedHeight(24)
        self.dir_value.setFixedHeight(24)
        control_layout = QHBoxLayout()
        control_layout.setSpacing(2)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.addWidget(self.run_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addStretch()
        form_layout = QGridLayout()
        form_layout.setSpacing(2)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.addWidget(self.interpreter_label, 0, 0)
        form_layout.addWidget(self.interpreter_combo, 0, 1, 1, 2)
        form_layout.addWidget(self.dir_label, 1, 0)
        form_layout.addWidget(self.dir_value, 1, 1)
        form_layout.addWidget(self.dir_select_button, 1, 2)
        form_layout.addWidget(self.script_label, 2, 0)
        form_layout.addWidget(self.script_value, 2, 1)
        form_layout.addWidget(self.script_select_button, 2, 2)
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addLayout(control_layout)
        layout.addLayout(form_layout)
        layout.addWidget(self.output_view)
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("標準入力をここに入力しEnterで送信")
        self.input_line.setFixedHeight(22)
        self.input_line.returnPressed.connect(self.send_stdin)
        layout.addWidget(self.input_line)
        self.setLayout(layout)

        from .config_manager import LauncherConfigManager
        self.config_manager = LauncherConfigManager()
        default_label = self.config_manager.get_default_interpreter_label()
        default_path = self.config_manager.get_default_interpreter_path()
        default_workdir = self.config_manager.get_default_workdir()
        if config:
            self.apply_config(config)
        else:
            if default_label and default_path:
                self.interpreter_combo.setCurrentText(default_label)
                self.interpreter_path = default_path
            elif interp_map:
                first_label = next(iter(interp_map.keys()))
                self.interpreter_combo.setCurrentText(first_label)
                self.interpreter_path = interp_map[first_label]
            if default_workdir:
                self.working_dir = default_workdir
                self.dir_value.setText(Path(self.working_dir).name if self.working_dir else "")
        self.config_changed_callback = None

        # イベント接続を追加
        self.run_button.clicked.connect(self.run_script)
        self.stop_button.clicked.connect(self.stop_script)
        self.interpreter_combo.currentIndexChanged.connect(self.on_interpreter_changed)
        self.script_select_button.clicked.connect(self.select_script)
        self.dir_select_button.clicked.connect(self.select_dir)

    def on_interpreter_changed(self):
        label = self.interpreter_combo.currentText()
        self.interpreter_path = self.interpreter_map.get(label, "python")

    def send_stdin(self):
        text = self.input_line.text()
        if self.process and self.process.state() != QProcess.NotRunning:
            self.process.write((text + "\n").encode("utf-8"))
            self.output_view.append(f"<span style='color:blue;'>{text}</span>")
            self.input_line.clear()
        else:
            self.output_view.append("<span style='color:red;'>プロセスが起動していません</span>")

    def get_interpreters(self, force_refresh=False):
        global interpreter_cache
        if interpreter_cache and not force_refresh:
            return interpreter_cache
        interpreters = {}
        import platform
        is_windows = platform.system() == "Windows"
        try:
            if is_windows:
                sys_version = subprocess.check_output(
                    ["python", "--version"], universal_newlines=True
                ).strip().split()[1]
                sys_path = subprocess.check_output(
                    ["where", "python"], universal_newlines=True
                ).strip().split("\n")[0]
            else:
                sys_version = subprocess.check_output(
                    ["python3", "--version"], universal_newlines=True
                ).strip().split()[1]
                sys_path = subprocess.check_output(
                    ["which", "python3"], universal_newlines=True
                ).strip()
            label = f"Python {sys_version} (system)"
            interpreters[label] = sys_path
        except Exception as e:
            error_print(f"[warn] system pythonの取得に失敗しました: {e}")
        try:
            output = subprocess.check_output(["conda", "info", "--json"], universal_newlines=True)
            info = json.loads(output)
            envs = info.get("envs", [])
            for env_path in envs:
                if is_windows:
                    python_path = str(Path(env_path) / "python.exe")
                else:
                    python_path = str(Path(env_path) / "bin" / "python")
                try:
                    version = subprocess.check_output(
                        [python_path, "--version"], universal_newlines=True
                    ).strip().split()[1]
                    env_name = Path(env_path).name
                    label = f"Python {version} (conda: {env_name})"
                    interpreters[label] = python_path
                except Exception:
                    continue
        except Exception as e:
            error_print(f"[warn] conda環境の取得に失敗しました: {e}")
        interpreter_cache = interpreters
        return interpreters

    def configure(self):
        interp_map = self.get_interpreters()
        dialog = PythonSettingsDialog(
            self,
            envs=list(interp_map.keys()),
            current_env=self.interpreter_combo.currentText(),
            current_script=self.script_path,
            current_dir=self.working_dir,
            get_interpreters_func=self.get_interpreters
        )
        if dialog.exec_() == QDialog.Accepted:
            label, script, workdir = dialog.get_values()
            self.interpreter_combo.setCurrentText(label)
            self.interpreter_path = interp_map.get(label, "python")
            self.script_path = script
            self.working_dir = workdir or (str(Path(script).parent) if script else "")
            self.script_value.setText(Path(self.script_path).name if self.script_path else "")
            self.dir_value.setText(Path(self.working_dir).name if self.working_dir else "")
            if self.parent() and self.script_path:
                self.parent().setWindowTitle(Path(script).name)
            if self.config_changed_callback:
                self.config_changed_callback()

    def get_config(self):
        return {
            'interpreter': self.interpreter_path,
            'script': self.script_path,
            'workdir': self.working_dir
        }

    def apply_config(self, config):
        self.interpreter_path = config.get('interpreter', '')
        interp_map = self.get_interpreters()
        # パスからラベルを逆引き
        label = next((k for k, v in interp_map.items() if v == self.interpreter_path), self.interpreter_path)
        self.interpreter_combo.setCurrentText(label)
        self.script_path = config.get('script', '')
        self.working_dir = config.get('workdir', '')
        self.script_value.setText(Path(self.script_path).name if self.script_path else "")
        self.dir_value.setText(Path(self.working_dir).name if self.working_dir else "")

    def run_script(self, checked=False):
        self.output_view.append(f"[debug] run_script called (checked={checked})")
        if not self.script_path:
            self.output_view.append("スクリプトが選択されていません")
            return
        self.output_view.append(f"[debug] インタプリタ: {self.interpreter_path}")
        self.output_view.append(f"[debug] スクリプト: {self.script_path}")
        self.output_view.append(f"[debug] 作業ディレクトリ: {self.working_dir}")

        # プロセス作成前に環境変数を設定
        self.process = QProcess(self)

        # システム環境変数を取得し、QProcessEnvironmentに変換
        from PyQt5.QtCore import QProcessEnvironment
        env = QProcessEnvironment.systemEnvironment()

        # Pythonのバッファリングを無効化
        env.insert("PYTHONUNBUFFERED", "1")
        env.insert("PYTHONIOENCODING", "utf-8:unbuffered")

        # 他の言語のバッファリングも制御（gccなど）
        env.insert("GCCNOBUFFERED", "1")

        # 環境変数を設定
        self.process.setProcessEnvironment(env)
        self.process.setProgram(self.interpreter_path)

        # コマンドライン引数調整 - Pythonの場合は-uオプションを追加
        args = [self.script_path]
        if self.interpreter_path.endswith("python") or self.interpreter_path.endswith("python3"):
            args = ["-u", self.script_path]

        self.process.setArguments(args)
        self.process.setWorkingDirectory(self.working_dir)

        # 標準出力と標準エラー出力を別々に処理するモードを設定
        self.process.setProcessChannelMode(QProcess.SeparateChannels)

        # シグナル接続
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)
        self.process.errorOccurred.connect(self.handle_process_error)

        # バッファをクリア
        self.stdout_buffer = ""
        self.stderr_buffer = ""
        self.output_view.clear()
        self.output_view.append("スクリプトを開始します...")
        self.process.start()

    def handle_process_error(self, error):
        self.output_view.append(f"<span style='color:red;'>QProcessエラー: {error}</span>")
        if self.process:
            self.output_view.append(f"詳細: {self.process.errorString()}")

    def stop_script(self):
        if self.process and self.process.state() != QProcess.NotRunning:
            from PyQt5.QtCore import QCoreApplication

            # 段階的なプロセス停止を試みる
            self.output_view.append("スクリプトの停止を試みています...")
            self.output_view.repaint()  # UIの更新を強制
            QCoreApplication.processEvents()  # イベントループを処理してUIを更新

            # ステップ1: SIGINT (Ctrl+C相当) で停止を促す
            self.process.terminate()  # QProcess.terminateはSIGINTを送信
            self.output_view.append("SIGINT送信 - 正常終了を2秒間待機中...")
            self.output_view.repaint()
            QCoreApplication.processEvents()

            if self.process.waitForFinished(2000):  # 2秒待機
                self.output_view.append("✓ スクリプトが正常に停止しました (SIGINT)")
                self.output_view.repaint()
                return

            # ステップ2: SIGTERM (通常のkill) で終了を要求
            self.output_view.append("<span style='color:orange;'>⚠ SIGINTでの停止に失敗しました</span>")
            self.output_view.append("SIGTERM送信 - 終了を2秒間待機中...")
            self.output_view.repaint()
            QCoreApplication.processEvents()

            self.process.kill()  # QProcess.killはSIGTERMを送信
            if self.process.waitForFinished(2000):  # 2秒待機
                self.output_view.append("✓ スクリプトが停止しました (SIGTERM)")
                self.output_view.repaint()
                return

            # ステップ3: SIGKILL (kill -9) で強制終了
            import signal
            import os
            self.output_view.append("<span style='color:red;'>❌ SIGTERMでの停止に失敗しました</span>")
            self.output_view.append("SIGKILL送信 - 強制終了を実行中...")
            self.output_view.repaint()
            QCoreApplication.processEvents()

            try:
                pid = self.process.processId()
                os.kill(pid, signal.SIGKILL)
                self.output_view.append("SIGKILL送信完了 - プロセス終了を待機中...")
                self.output_view.repaint()
                QCoreApplication.processEvents()

                self.process.waitForFinished(1000)  # 1秒待機
                self.output_view.append("✓ スクリプトを強制終了しました (SIGKILL)")
                self.output_view.repaint()
            except Exception as e:
                self.output_view.append(f"<span style='color:red;'>❌ プロセスの強制終了に失敗しました: {e}</span>")
                self.output_view.repaint()

    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode("utf-8", errors="replace")
        # バッファリング対応
        self.stdout_buffer += text
        lines = self.stdout_buffer.split('\n')

        # 空のリストの場合（分割結果なし）は処理しない
        if not lines:
            return

        # 最後の行以外をすべて処理
        for line in lines[:-1]:
            self.output_view.append(line)

        # 最後の行はバッファに残す
        self.stdout_buffer = lines[-1]

        # スクロールを最新に保つ
        scrollbar = self.output_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def handle_stderr(self):
        data = self.process.readAllStandardError()
        text = bytes(data).decode("utf-8", errors="replace")
        # バッファリング対応
        self.stderr_buffer += text
        lines = self.stderr_buffer.split('\n')

        # 空のリストの場合（分割結果なし）は処理しない
        if not lines:
            return

        # 最後の行以外をすべて処理
        for line in lines[:-1]:
            self.output_view.append(f"<span style='color:red;'>{line}</span>")

        # 最後の行はバッファに残す
        self.stderr_buffer = lines[-1]

        # スクロールを最新に保つ
        scrollbar = self.output_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def process_finished(self):
        # 残りのバッファをフラッシュ
        if self.stdout_buffer:
            self.output_view.append(self.stdout_buffer)
            self.stdout_buffer = ""

        if self.stderr_buffer:
            self.output_view.append(f"<span style='color:red;'>{self.stderr_buffer}</span>")
            self.stderr_buffer = ""

        self.output_view.append("スクリプトが終了しました")

    def select_script(self):
        default_dir = self.working_dir or str(Path.cwd())
        path, _ = QFileDialog.getOpenFileName(self, "スクリプトを選択", directory=default_dir, filter="Python Scripts (*.py)")
        if path:
            self.script_path = path  # フルパスを保持
            self.script_value.setText(Path(self.script_path).name)  # 表示はbasename
            if self.config_changed_callback:
                self.config_changed_callback()

    def select_dir(self):
        path = QFileDialog.getExistingDirectory(self, "作業ディレクトリを選択", directory=self.working_dir or str(Path.cwd()))
        if path:
            self.working_dir = path
            self.dir_value.setText(Path(self.working_dir).name if self.working_dir else "")
            if self.config_changed_callback:
                self.config_changed_callback()

    def closeEvent(self, event):
        """ウィンドウが閉じられるときにプロセスを終了させる"""
        from PyQt5.QtCore import QCoreApplication

        self.output_view.append("[debug] closeEvent: プロセス終了処理")
        self.output_view.repaint()
        QCoreApplication.processEvents()

        if self.process and self.process.state() != QProcess.NotRunning:
            # 段階的なプロセス停止を試みる（短い待機時間で）

            # ステップ1: SIGINT
            self.output_view.append("SIGINT送信中...")
            self.output_view.repaint()
            QCoreApplication.processEvents()

            self.process.terminate()
            if self.process.waitForFinished(500):  # 0.5秒待機
                self.output_view.append("プロセスが停止しました (SIGINT)")
                self.output_view.repaint()
                QCoreApplication.processEvents()
                event.accept()
                return

            # ステップ2: SIGTERM
            self.output_view.append("SIGTERM送信中...")
            self.output_view.repaint()
            QCoreApplication.processEvents()

            self.process.kill()
            if self.process.waitForFinished(500):  # 0.5秒待機
                self.output_view.append("プロセスが停止しました (SIGTERM)")
                self.output_view.repaint()
                QCoreApplication.processEvents()
                event.accept()
                return

            # ステップ3: SIGKILL
            self.output_view.append("SIGKILL送信中...")
            self.output_view.repaint()
            QCoreApplication.processEvents()

            try:
                import signal
                import os
                pid = self.process.processId()
                os.kill(pid, signal.SIGKILL)
                self.process.waitForFinished(500)  # 0.5秒待機
                self.output_view.append("プロセスが強制終了しました (SIGKILL)")
                self.output_view.repaint()
                QCoreApplication.processEvents()
            except:
                self.output_view.append("プロセス終了処理に失敗しました")
                self.output_view.repaint()
                QCoreApplication.processEvents()
        event.accept()

    def __del__(self):
        """インスタンスが破棄されるときにプロセスを終了させる"""
        if hasattr(self, 'process') and self.process and self.process.state() != QProcess.NotRunning:
            try:
                # 段階的なプロセス停止（超短い待機時間で）
                self.process.terminate()
                if self.process.waitForFinished(200):  # 0.2秒待機
                    return

                self.process.kill()
                if self.process.waitForFinished(200):  # 0.2秒待機
                    return

                import signal
                import os
                pid = self.process.processId()
                os.kill(pid, signal.SIGKILL)
            except:
                pass
