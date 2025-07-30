# @Time  : 2025/06/16
# @Author: DriftCloud
# @File  : config.py

import json
import os

__all__ = ['Config']

class Config:
    _config_file_path = None
    _configs = None

    def __init__(self, config_file_path='config.json'):
        self._config_file_path = config_file_path
        if os.path.exists(config_file_path):
            self._configs = json.load(open(self._config_file_path, 'r', encoding='utf-8'))
        else:
            self._configs = {}

    def get(self, key, default=""):
        return self._configs.get(key, default)

    def set(self, key, value):
        self._configs[key] = value

    def close(self):
        with open(self._config_file_path, 'w', encoding='utf-8') as f:
            json.dump(self._configs, f, ensure_ascii=False, indent=4)
