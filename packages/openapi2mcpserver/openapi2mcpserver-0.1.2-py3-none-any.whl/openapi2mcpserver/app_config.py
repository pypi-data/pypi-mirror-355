# app_config.py
"""
配置模块，用于管理应用程序配置
"""

import os
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """配置类，用于管理应用程序配置"""
    
    # 测试配置
    BASE_URL = os.getenv("BASE_URL", "")

    
    OPEN_API_DOC_JSON_URL = os.getenv("OPEN_API_DOC_JSON_URL", "")
    
    # 服务器配置
    SERVER_NAME = os.getenv("SERVER_NAME", "OpenAPI2MCP-Server")
    
    # 路由映射配置
    ROUTE_MAPS = os.getenv("ROUTE_MAPS", "")
    
    # 连接字符串
    @property
    def CONNECTION_STRING(self):
        """Returns the base URL as a connection string."""
        """构建字符串"""
        return f"{self.BASE_URL}"
    
    def get_route_maps(self):
        """解析环境变量中的路由映射配置"""
        if not self.ROUTE_MAPS:
            return []
        
        try:
            # 解析JSON格式的路由配置
            route_configs = json.loads(self.ROUTE_MAPS)
            route_maps = []
            
            for config_item in route_configs:
                methods = config_item.get('methods', ['GET'])
                pattern = config_item.get('pattern', '')
                
                if pattern:  # 只有当pattern不为空时才添加
                    route_maps.append({
                        'methods': methods,
                        'pattern': pattern
                    })
            
            return route_maps
        except (json.JSONDecodeError, TypeError):
            return []

# 创建默认配置实例
config = Config()