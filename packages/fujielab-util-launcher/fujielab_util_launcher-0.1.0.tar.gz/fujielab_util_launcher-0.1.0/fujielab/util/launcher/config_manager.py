import os
import yaml
from pathlib import Path

class LauncherConfigManager:
    def __init__(self, config_path=None):
        self.config_path = config_path or self.get_default_config_path()
        self.data = {}
        self.load()

    @staticmethod
    def get_default_config_path():
        config_dir = os.environ.get("XDG_CONFIG_HOME")
        if not config_dir:
            config_dir = str(Path.home() / ".config")
        config_dir = os.path.join(config_dir, "fujielab_launcher")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "config.yaml")

    def load(self, path=None):
        path = path or self.config_path
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self.data = yaml.safe_load(f) or {}
        else:
            self.data = {}

    def save(self, path=None):
        path = path or self.config_path
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.data, f, allow_unicode=True)

    def export(self, export_path):
        self.save(export_path)

    def import_config(self, import_path):
        self.load(import_path)
        self.save(self.config_path)

    def set_launchers(self, launchers):
        self.data['launchers'] = launchers
        self.save()

    def get_launchers(self):
        return self.data.get('launchers', [])

    def set_mainwindow_geometry(self, geometry):
        self.data['mainwindow_geometry'] = geometry
        self.save()

    def get_mainwindow_geometry(self):
        return self.data.get('mainwindow_geometry', None)

    def set_mainwindow_state(self, is_maximized):
        self.data['mainwindow_maximized'] = bool(is_maximized)
        self.save()

    def get_mainwindow_state(self):
        return self.data.get('mainwindow_maximized', False)

    def set_default_interpreter(self, label, path):
        self.data['default_interpreter_label'] = label
        self.data['default_interpreter_path'] = path
        self.save()

    def get_default_interpreter_label(self):
        return self.data.get('default_interpreter_label', "")

    def get_default_interpreter_path(self):
        return self.data.get('default_interpreter_path', "")

    def set_default_workdir(self, workdir_path):
        self.data['default_workdir'] = workdir_path
        self.save()

    def get_default_workdir(self):
        return self.data.get('default_workdir', "")
