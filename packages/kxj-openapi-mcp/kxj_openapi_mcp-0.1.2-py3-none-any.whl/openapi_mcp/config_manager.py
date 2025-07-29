#!/usr/bin/env python3
"""
MCP 配置管理模块
用于从环境变量读取 MCP Key 和其他配置信息
符合标准 MCP 配置方式
"""

import os
from typing import Optional, Dict, Any

class ConfigManager:
    """配置管理器 - 从环境变量读取配置"""
    
    def __init__(self):
        """初始化配置管理器"""
        pass
    
    def get_mcp_key(self) -> Optional[str]:
        """
        从环境变量获取 MCP Key
        
        支持多种环境变量名称:
        - MCP_API_KEY (推荐)
        - OPENAPI_MCP_KEY
        - MCP_KEY
        
        Returns:
            MCP Key 或 None
        """
        # 按优先级顺序检查环境变量
        key_vars = [
            "MCP_API_KEY",      # 标准MCP配置
            "OPENAPI_MCP_KEY",  # 项目特定配置
            "MCP_KEY"           # 简化配置
        ]
        
        for var_name in key_vars:
            key = os.getenv(var_name)
            if key and key.strip():
                return key.strip()
        
        return None
    
    def is_configured(self) -> bool:
        """
        检查是否已配置 MCP Key
        
        Returns:
            是否已配置
        """
        return bool(self.get_mcp_key())
    
    def get_all_config(self) -> Dict[str, Any]:
        """
        获取所有MCP相关的环境变量配置
        
        Returns:
            所有配置的字典（隐藏敏感信息）
        """
        config = {}
        
        # 检查所有可能的MCP key环境变量
        key_vars = ["MCP_API_KEY", "OPENAPI_MCP_KEY", "MCP_KEY"]
        
        for var_name in key_vars:
            value = os.getenv(var_name)
            if value:
                # 隐藏敏感信息
                if len(value) > 16:
                    config[var_name] = f"{value[:8]}...{value[-8:]}"
                else:
                    config[var_name] = "***"
            else:
                config[var_name] = None
        
        # 添加其他相关环境变量
        other_vars = [
            "MCP_SERVER_NAME",
            "MCP_SERVER_URL", 
            "MCP_DEBUG",
            "OPENAPI_BASE_URL"
        ]
        
        for var_name in other_vars:
            config[var_name] = os.getenv(var_name)
        
        return config
    
    def debug_key_info(self) -> Dict[str, Any]:
        """
        调试信息：获取key相关的详细信息
        
        Returns:
            调试信息字典
        """
        key = self.get_mcp_key()
        
        return {
            "key_configured": bool(key),
            "key_length": len(key) if key else 0,
            "key_preview": f"{key[:8]}...{key[-8:]}" if key and len(key) > 16 else "***" if key else None,
            "environment_variables": {
                "MCP_API_KEY": "SET" if os.getenv("MCP_API_KEY") else "NOT_SET",
                "OPENAPI_MCP_KEY": "SET" if os.getenv("OPENAPI_MCP_KEY") else "NOT_SET", 
                "MCP_KEY": "SET" if os.getenv("MCP_KEY") else "NOT_SET"
            }
        }

# 全局配置管理器实例
config_manager = ConfigManager() 