"""
配置管理模块
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AppConfig:
    """应用配置类"""
    
    # 服务器配置
    server_name: str = "Browser"
    host: str = "127.0.0.1"
    port: int = 8000
    
    # 浏览器配置
    headless: bool = False
    highlight_elements: bool = True
    
    # 浏览器模式配置：local 或 remote
    browser_mode: str = "local"  # 默认为本地模式
    
    # 远程服务配置
    remote_service_url: str = "http://localhost:8080"  # 远程服务地址
    remote_timeout: int = 30  # 远程服务超时时间（秒）
    
    # 视觉模式配置
    vision_enabled: bool = False
    
    json_format: bool = False
    
    # 图片处理配置
    image_quality: int = 100
    max_image_width: int = 800
    max_image_height: int = 600
    
    def __post_init__(self):
        """初始化后检查环境变量"""
        # 从环境变量加载配置
        self.vision_enabled = self.vision_enabled or os.environ.get("VISION_ENABLED", "").lower() in ("1", "true", "yes", "on")
        
        # 浏览器模式配置
        browser_mode = os.environ.get("BROWSER_MODE", "local").lower()
        if browser_mode in ("local", "remote"):
            self.browser_mode = browser_mode
        
        # 远程服务配置
        if os.environ.get("REMOTE_SERVICE_URL"):
            self.remote_service_url = os.environ.get("REMOTE_SERVICE_URL")
            
        if os.environ.get("REMOTE_TIMEOUT"):
            try:
                self.remote_timeout = int(os.environ.get("REMOTE_TIMEOUT"))
            except ValueError:
                pass  # 使用默认值


# 创建默认配置实例
config = AppConfig()


def update_config_from_args(args):
    """从命令行参数更新配置
    
    Args:
        args: 命令行参数
    """
    if (hasattr(args, "vision") and args.vision) or os.environ.get("VISION_ENABLED", "").lower() in ("1", "true", "yes", "on"):
        config.vision_enabled = True
        
    if os.environ.get("JSON_FORMAT", "").lower() in ("1", "true", "yes", "on"):
        config.json_format = True
        
    if os.environ.get("IMAGE_QUALITY", "").lower() in ("1", "true", "yes", "on"):
        config.image_quality = int(os.environ.get("IMAGE_QUALITY", "100"))
        
    if hasattr(args, "headless") and args.headless:
        config.headless = True
        
    if hasattr(args, "host") and args.host:
        config.host = args.host
        
    if hasattr(args, "port") and args.port:
        config.port = args.port 