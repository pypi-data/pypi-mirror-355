"""
浏览器服务使用示例
"""

import asyncio
import os
from orion_browser_mcp.browser_actions import browser_controller


async def example_usage():
    """浏览器服务使用示例"""
    
    print("=== 浏览器服务使用示例 ===")
    
    # 显示当前配置
    from orion_browser_mcp.config import config
    print(f"当前浏览器模式: {config.browser_mode}")
    if config.browser_mode == "remote":
        print(f"远程服务地址: {config.remote_service_url}")
        print(f"超时时间: {config.remote_timeout}秒")
    
    try:
        # 示例操作：访问网页
        print("\n1. 访问百度首页...")
        result = await browser_controller.go_to_url("https://www.baidu.com")
        print(f"结果: {result}")
        
        # 示例操作：提取页面内容
        print("\n2. 提取页面内容...")
        result = await browser_controller.extract_content()
        print(f"结果: {result}")
        
        # 示例操作：搜索
        print("\n3. 搜索'Python'...")
        result = await browser_controller.web_search("Python")
        print(f"结果: {result}")
        
        # 示例操作：获取所有标签页
        print("\n4. 获取所有标签页...")
        result = await browser_controller.get_all_tabs()
        print(f"结果: {result}")
        
    except Exception as e:
        print(f"操作失败: {str(e)}")
    
    finally:
        # 关闭浏览器
        print("\n5. 关闭浏览器...")
        result = await browser_controller.close()
        print(f"结果: {result}")


async def test_local_mode():
    """测试本地模式"""
    print("=== 测试本地模式 ===")
    
    # 设置为本地模式
    os.environ["BROWSER_MODE"] = "local"
    
    # 重新加载配置
    from orion_browser_mcp.config import config
    config.__post_init__()
    
    await example_usage()


async def test_remote_mode():
    """测试远程模式"""
    print("=== 测试远程模式 ===")
    
    # 设置为远程模式
    os.environ["BROWSER_MODE"] = "remote"
    os.environ["REMOTE_SERVICE_URL"] = "http://localhost:8080"
    os.environ["REMOTE_TIMEOUT"] = "30"
    
    # 重新加载配置
    from orion_browser_mcp.config import config
    config.__post_init__()
    
    await example_usage()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "local":
            asyncio.run(test_local_mode())
        elif mode == "remote":
            asyncio.run(test_remote_mode())
        else:
            print("使用方法: python example_usage.py [local|remote]")
    else:
        # 默认测试本地模式
        asyncio.run(test_local_mode()) 