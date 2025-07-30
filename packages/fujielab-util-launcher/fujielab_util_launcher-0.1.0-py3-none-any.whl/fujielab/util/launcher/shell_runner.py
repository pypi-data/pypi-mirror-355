from PyQt5.QtWidgets import QWidget, QTextEdit, QLabel, QLineEdit, QPushButton, QHBoxLayout, QFormLayout, QVBoxLayout, QSizePolicy, QFileDialog, QGridLayout
from PyQt5.QtCore import QProcess
from pathlib import Path
from .shell_settings_dialog import ShellSettingsDialog
from .debug_util import debug_print, error_print

class ShellRunnerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.process = None
        self.program_cmdline = ""
        self.working_dir = ""
        self.output_view = QTextEdit()
        self.output_view.setReadOnly(True)
        self.program_label = QLabel("コマンドライン:")
        self.dir_label = QLabel("作業ディレクトリ:")
        self.program_value = QLineEdit()
        self.program_value.setReadOnly(False)  # 直接編集可能に
        self.dir_value = QLineEdit()
        self.dir_value.setReadOnly(True)
        self.dir_select_button = QPushButton("選択")
        self.run_button = QPushButton("実行")
        self.stop_button = QPushButton("停止")
        self.run_button.setFixedHeight(26)
        self.stop_button.setFixedHeight(26)
        self.dir_select_button.setFixedSize(48, 24)
        self.program_value.setFixedHeight(24)
        self.dir_value.setFixedHeight(24)
        self.program_value.textChanged.connect(self.on_cmdline_changed)
        self.dir_select_button.clicked.connect(self.select_dir)
        self.run_button.clicked.connect(self.run_program)
        self.stop_button.clicked.connect(self.stop_program)
        control_layout = QHBoxLayout()
        control_layout.setSpacing(2)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.addWidget(self.run_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addStretch()
        form_layout = QGridLayout()
        form_layout.setSpacing(2)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.addWidget(self.program_label, 0, 0)
        form_layout.addWidget(self.program_value, 0, 1)
        form_layout.addWidget(self.dir_label, 1, 0)
        form_layout.addWidget(self.dir_value, 1, 1)
        form_layout.addWidget(self.dir_select_button, 1, 2)
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
        self.config_changed_callback = None

    def on_cmdline_changed(self, text):
        self.program_cmdline = text
        if self.config_changed_callback:
            self.config_changed_callback()

    def select_dir(self):
        path = QFileDialog.getExistingDirectory(self, "作業ディレクトリを選択", directory=self.working_dir or str(Path.cwd()))
        if path:
            self.working_dir = path
            self.dir_value.setText(Path(self.working_dir).name if self.working_dir else "")
            if self.config_changed_callback:
                self.config_changed_callback()

    def send_stdin(self):
        text = self.input_line.text()
        if self.process and self.process.state() != QProcess.NotRunning:
            self.process.write((text + "\n").encode("utf-8"))
            self.output_view.append(f"<span style='color:blue;'>{text}</span>")
            self.input_line.clear()
        else:
            self.output_view.append("<span style='color:red;'>プロセスが起動していません</span>")

    def run_program(self):
        self.output_view.append("[debug] run_program called")
        if not self.program_cmdline:
            self.output_view.append("コマンドラインが入力されていません")
            return
        self.output_view.append(f"[debug] コマンドライン: {self.program_cmdline}")
        self.output_view.append(f"[debug] 作業ディレクトリ: {self.working_dir}")
        self.process = QProcess(self)
        # コマンドラインをシェルで実行
        self.process.setProgram("/bin/sh")
        self.process.setArguments(["-c", self.program_cmdline])
        self.process.setWorkingDirectory(self.working_dir)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)
        self.output_view.clear()
        self.process.errorOccurred.connect(self.handle_process_error)
        self.output_view.append("プログラムを開始します...")
        self.process.start()

    def handle_process_error(self, error):
        self.output_view.append(f"<span style='color:red;'>QProcessエラー: {error}</span>")
        if self.process:
            self.output_view.append(f"詳細: {self.process.errorString()}")

    # Dockerコンテナに特化した処理は削除
        
    def stop_program(self):
        if self.process and self.process.state() != QProcess.NotRunning:
            from PyQt5.QtCore import QCoreApplication
            
            # 段階的なプロセス停止を試みる
            self.output_view.append("プログラムの停止を試みています...")
            self.output_view.repaint()
            QCoreApplication.processEvents()
            
            # ステップ1: SIGINT (Ctrl+C相当) で停止を促す
            self.output_view.append("SIGINT送信 - 正常終了を2秒間待機中...")
            self.output_view.repaint()
            QCoreApplication.processEvents()
            
            self.process.terminate()  # QProcess.terminateはSIGINTを送信
            if self.process.waitForFinished(2000):  # 2秒待機
                self.output_view.append("✓ プログラムが正常に停止しました (SIGINT)")
                self.output_view.repaint()
                QCoreApplication.processEvents()
                return
            
            # ステップ2: SIGTERM (通常のkill) で終了を要求
            self.output_view.append("<span style='color:orange;'>⚠ SIGINTでの停止に失敗しました</span>")
            self.output_view.append("SIGTERM送信 - 終了を2秒間待機中...")
            self.output_view.repaint()
            QCoreApplication.processEvents()
            
            self.process.kill()  # QProcess.killはSIGTERMを送信 (SIGKILL ではない)
            if self.process.waitForFinished(2000):  # 2秒待機
                self.output_view.append("✓ プログラムが停止しました (SIGTERM)")
                self.output_view.repaint()
                QCoreApplication.processEvents()
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
                self.output_view.append("✓ プログラムを強制終了しました (SIGKILL)")
                self.output_view.repaint()
                QCoreApplication.processEvents()
            except Exception as e:
                self.output_view.append(f"<span style='color:red;'>❌ プロセスの強制終了に失敗しました: {e}</span>")
                self.output_view.repaint()
                QCoreApplication.processEvents()

    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode("utf-8")
        self.output_view.append(text)

    def handle_stderr(self):
        data = self.process.readAllStandardError()
        text = bytes(data).decode("utf-8")
        self.output_view.append(f"<span style='color:red;'>{text}</span>")

    def process_finished(self):
        self.output_view.append("プログラムが終了しました")

    def get_config(self):
        return {
            'cmdline': self.program_cmdline,
            'workdir': self.working_dir
        }

    def apply_config(self, config):
        self.program_cmdline = config.get('cmdline', '')
        self.working_dir = config.get('workdir', '')
        self.program_value.setText(self.program_cmdline)
        self.dir_value.setText(Path(self.working_dir).name if self.working_dir else "")

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
                # __del__メソッドではUI更新はできない可能性が高いため、
                # プロセスの終了処理のみを簡潔に行う
                
                # 段階的なプロセス停止（超短い待機時間で）
                # ここではログ出力や画面更新は行わない
                
                # ステップ1: SIGINT
                self.process.terminate()
                if self.process.waitForFinished(200):  # 0.2秒待機
                    return
                
                # ステップ2: SIGTERM
                self.process.kill()
                if self.process.waitForFinished(200):  # 0.2秒待機
                    return
                
                # ステップ3: SIGKILL
                import signal
                import os
                pid = self.process.processId()
                os.kill(pid, signal.SIGKILL)
            except:
                pass
