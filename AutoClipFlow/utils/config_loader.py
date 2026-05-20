"""
config_loader.py - 配置文件加载器
"""

import json
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    def __init__(self, config_path: Path):
        self.config_path = config_path

    def load(self) -> Dict[str, Any]:
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def validate(self, config: Dict[str, Any]) -> bool:
        required_keys = ['project', 'video', 'speed', 'clips', 'output']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"缺少必需配置项: {key}")
        return True