from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QFormLayout, QDialogButtonBox, QFileDialog, QLineEdit
from PyQt5.QtCore import Qt
from pathlib import Path

class ShellSettingsDialog(QDialog):
    def __init__(self, parent=None, current_program="", current_dir=""):
        super().__init__(parent)
        self.setWindowTitle("シェルランチャ設定")
        self.program_line = QLineEdit(current_program)
        self.dir_path_label = QLabel(current_dir)
        dir_button = QPushButton("ディレクトリ選択")
        dir_button.clicked.connect(self.select_dir)
        layout = QFormLayout()
        layout.addRow("コマンドライン（引数含む）", self.program_line)
        layout.addRow(dir_button, self.dir_path_label)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def select_dir(self):
        path = QFileDialog.getExistingDirectory(self, "作業ディレクトリを選択")
        if path:
            self.dir_path_label.setText(path)

    def get_values(self):
        return (
            self.program_line.text(),
            self.dir_path_label.text()
        )
