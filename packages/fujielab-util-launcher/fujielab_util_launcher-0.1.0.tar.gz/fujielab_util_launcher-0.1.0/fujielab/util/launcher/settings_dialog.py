from PyQt5.QtWidgets import QDialog, QComboBox, QLabel, QPushButton, QFormLayout, QDialogButtonBox, QFileDialog, QFrame
from PyQt5.QtCore import Qt
from pathlib import Path

class PythonSettingsDialog(QDialog):
    def __init__(self, parent=None, envs=None, current_env="", current_script="", current_dir="", get_interpreters_func=None):
        super().__init__(parent)
        self.setWindowTitle("Pythonランチャ設定")
        self.env_combo = QComboBox()
        self.env_combo.addItems(envs or [])
        if current_env in (envs or []):
            self.env_combo.setCurrentText(current_env)
        self.script_path_label = QLabel(current_script)
        self.dir_path_label = QLabel(current_dir)
        script_button = QPushButton("スクリプト選択")
        dir_button = QPushButton("ディレクトリ選択")
        script_button.clicked.connect(self.select_script)
        dir_button.clicked.connect(self.select_dir)
        layout = QFormLayout()
        layout.addRow("Pythonインタプリタ", self.env_combo)
        layout.addRow(dir_button, self.dir_path_label)
        layout.addRow(script_button, self.script_path_label)
        refresh_button = QPushButton("インタプリタリストの更新")
        refresh_button.clicked.connect(self.refresh_interpreters)
        layout.addRow("", refresh_button)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.get_interpreters_func = get_interpreters_func

    def refresh_interpreters(self):
        # 現在選択されているテキストを保存
        current_text = self.env_combo.currentText()
        
        # コンボボックスをクリア
        self.env_combo.clear()
        
        if self.get_interpreters_func:
            new_list = self.get_interpreters_func(force_refresh=True)
            self.env_combo.addItems(new_list.keys())
            
            # 元々選択していたインタプリタが新しいリストにも存在するなら、それを選択
            if current_text in new_list:
                self.env_combo.setCurrentText(current_text)

    def select_script(self):
        # デフォルトディレクトリを作業ディレクトリに、なければカレントディレクトリに
        default_dir = self.dir_path_label.text() or str(Path.cwd())
        path, _ = QFileDialog.getOpenFileName(self, "スクリプトを選択", directory=default_dir, filter="Python Scripts (*.py)")
        if path:
            self.script_path_label.setText(path)

    def select_dir(self):
        path = QFileDialog.getExistingDirectory(self, "作業ディレクトリを選択")
        if path:
            self.dir_path_label.setText(path)

    def get_values(self):
        return (
            self.env_combo.currentText(),
            self.script_path_label.text(),
            self.dir_path_label.text()
        )


class GlobalSettingsDialog(QDialog):
    """
    グローバル設定ダイアログ
    スクリプト設定は不要で、インタプリタとディレクトリのみを扱います
    """
    def __init__(self, parent=None, envs=None, current_env="", current_dir="", get_interpreters_func=None):
        super().__init__(parent)
        self.setWindowTitle("グローバル設定")
        self.env_combo = QComboBox()
        self.env_combo.addItems(envs or [])
        if current_env in (envs or []):
            self.env_combo.setCurrentText(current_env)
        self.dir_path_label = QLabel(current_dir)
        
        dir_button = QPushButton("ディレクトリ選択")
        dir_button.clicked.connect(self.select_dir)
        
        layout = QFormLayout()
        # インタプリタセクションのフレームを作成
        # Create frames with consistent width
        interpreter_frame = QFrame()
        interpreter_frame.setFrameShape(QFrame.StyledPanel)
        interpreter_frame.setFrameShadow(QFrame.Raised)
        interpreter_frame.setMinimumWidth(400)  # Set minimum width
        interpreter_layout = QFormLayout(interpreter_frame)
        interpreter_layout.addRow("デフォルトPythonインタプリタ", self.env_combo)
        refresh_button = QPushButton("インタプリタリストの更新")
        refresh_button.clicked.connect(self.refresh_interpreters)
        interpreter_layout.addRow("", refresh_button)
        layout.addRow("", interpreter_frame)

        workdir_frame = QFrame()
        workdir_frame.setFrameShape(QFrame.StyledPanel)
        workdir_frame.setFrameShadow(QFrame.Raised)
        workdir_frame.setMinimumWidth(400)  # Same minimum width
        workdir_layout = QFormLayout(workdir_frame)
        workdir_layout.addRow("デフォルト作業ディレクトリ", self.dir_path_label)
        workdir_layout.addRow("", dir_button)
        layout.addRow("", workdir_frame)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.get_interpreters_func = get_interpreters_func

    def refresh_interpreters(self):
        # 現在選択されているテキストを保存
        current_text = self.env_combo.currentText()
        
        # コンボボックスをクリア
        self.env_combo.clear()
        
        if self.get_interpreters_func:
            new_list = self.get_interpreters_func(force_refresh=True)
            self.env_combo.addItems(new_list.keys())
            
            # 元々選択していたインタプリタが新しいリストにも存在するなら、それを選択
            if current_text in new_list:
                self.env_combo.setCurrentText(current_text)

    def select_dir(self):
        path = QFileDialog.getExistingDirectory(self, "デフォルト作業ディレクトリを選択")
        if path:
            self.dir_path_label.setText(path)

    def get_values(self):
        return (
            self.env_combo.currentText(),
            self.dir_path_label.text()
        )
