# core.py
"""
核心模块
"""

import json
from typing import Dict, List, Optional, Union, Any

from .app_config import config

# 测试管理
engine = None

def helloworld():
    """测试"""
    return {
            "text": "hello",
            "code": "0000"
        }