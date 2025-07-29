"""
基于FastMCP的服务器模块
"""

import argparse
import sys
import subprocess
import time
import asyncio
from typing import Any, Dict, List, Union, Optional

from mcp.server.fastmcp import FastMCP, Image
from mcp.types import TextContent

from orion_browser_mcp.config import config, update_config_from_args
from orion_browser_mcp.browser_actions import browser_controller
from orion_browser_mcp.utils import format_result


def parse_args():
    """解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(description='浏览器MCP服务器 - FastMCP版本')
    parser.add_argument('--vision', action='store_true', help='启用视觉模式')
    parser.add_argument('--headless', action='store_true', help='以无头模式运行浏览器')
    parser.add_argument('--install-playwright', action='store_true', help='自动安装 playwright 依赖')
    
    args = parser.parse_args()
    return args


def create_server():
    """创建并配置FastMCP服务器
    
    Returns:
        FastMCP: 配置好的服务器实例
    """
    # 解析命令行参数
    args = parse_args()
    
    # 更新配置
    update_config_from_args(args)
    
    # 创建服务器
    mcp = FastMCP(config.server_name)
    
    # 注册工具
    register_tools(mcp)
    
    return mcp




def register_tools(mcp: FastMCP) -> None:
    """注册所有浏览器工具
    
    Args:
        mcp: FastMCP服务器实例
    """
    
    @mcp.tool()
    async def go_url(url: str) -> Union[TextContent, List[Union[TextContent, Image]]]:
        """获取指定网页的基本信息和 element元素内容
        
        Args:
            url: 要获取内容的网址
        """
        result = await browser_controller.go_to_url(url)
        return format_result(result)

    # @mcp.tool()
    # async def browser_install():
    #     """安装 playwright 依赖，只有遇到 playwright 依赖缺失时才会安装"""
    #     print("正在安装 playwright 依赖...")
    #     try:
    #         subprocess.run([sys.executable, "-m", "playwright", "install"], check=True)
    #         return "playwright 依赖安装成功！"
    #     except subprocess.CalledProcessError as e:
    #         return f"playwright 依赖安装失败: {e}"

    @mcp.tool()
    async def close_browser():
        """关闭浏览器"""
        result = await browser_controller.close()
        return format_result(result)
        
    @mcp.tool()
    async def open_tab(url: str):
        """打开一个新标签页
        Args:
            url: 要在新标签页中打开的网址
        """
        result = await browser_controller.open_tab(url)
        return format_result(result)
      
    @mcp.tool()
    async def input_text(text: str, index: int):
        """输入文本
        Args:
            text: 要输入的文本
            index: 要输入的element元素的索引
        """
        result = await browser_controller.input_text(text, index)
        return format_result(result)

    @mcp.tool()
    async def click_element(index: int):
        """点击指定索引的element的元素索引
            
        Args:
            index: 要点击的的element元素的索引
        """
        result = await browser_controller.click_element(index)
        return format_result(result)

    @mcp.tool()
    async def go_back():
        """返回上一页
            
        """
        result = await browser_controller.go_back()
        return format_result(result)
    
    @mcp.tool()
    async def switch_tab(page_id: int):
        """切换到指定索引的标签页
            
        Args:
            page_id: 要切换到的标签页的索引
        """
        result = await browser_controller.switch_tab(page_id)
        return format_result(result)

    @mcp.tool()
    async def get_all_tabs():
        """获取所有浏览器标签页

        """
        result = await browser_controller.get_all_tabs()
        return format_result(result)
      
    @mcp.tool()
    async def send_keys(keys: str):
        """发送特殊按键字符串，如Escape、Backspace、Insert、PageDown、Delete、Enter等
        
        还支持组合键如`Control+o`、`Control+Shift+T`等
        """
        result = await browser_controller.send_keys(keys)
        return format_result(result)

    @mcp.tool()
    async def scroll_down(amount: int):
        """向下滚动页面
        
        Args:
            amount: 滚动的像素数量
        """
        result = await browser_controller.scroll_down(amount)
        return format_result(result)
    
    @mcp.tool()
    async def scroll_down_element(index: int):
        """向下滚动指定索引的 SCROLL Element元素到页面底部
        
        Args:
            index: 要滚动的element元素的索引
        """
        result = await browser_controller.scroll_element_to_bottom_by_index(index)
        return format_result(result)
    

    @mcp.tool()
    async def scroll_up(amount: int):
        """向上滚动页面
        
        Args:
            amount: 滚动的像素数量
        """
        result = await browser_controller.scroll_up(amount)
        return format_result(result)

    @mcp.tool()
    async def scroll_to_text(text: str):
        """滚动到包含特定文本的元素
        
        Args:
            text: 要查找的文本
        """
        result = await browser_controller.scroll_to_text(text)
        return format_result(result)
        
    @mcp.tool()
    async def extract_content():
        """提取页面完整内容，包括所有文本、图片、链接等信息"""
        result = await browser_controller.extract_content()
        return format_result(result)
    
    @mcp.tool()
    async def get_screenshot():
        """获取当前页面截图"""
        result = await browser_controller.extract_content()
        return format_result(result, only_Image=True)
        
    @mcp.tool()
    async def click_by_position(x: int, y: int):
        """通过坐标点击页面
        
        Args:
            x: X坐标
            y: Y坐标
        """
        result = await browser_controller.click_by_position(x, y)
        return format_result(result)
    
    @mcp.tool()
    async def web_search(query: str):
        """在浏览器中搜索指定内容
        
        Args:
            query: 要搜索的内容
        """
        result = await browser_controller.web_search(query)
        return format_result(result)
    
    @mcp.tool()
    async def do_date_picker(index: int, date: Optional[str] = None, date_range: Optional[List[str]] = None):
        """操作日期选择器组件
        
        Args:
            index: 要操作的日期选择器元素的索引
            date: 单个日期字符串，格式如 "2024-01-15"
            date_range: 日期范围列表，包含开始和结束日期，如 ["2024-01-15", "2024-01-20"]
        """
        result = await browser_controller.do_date_picker(index, date, date_range)
        return format_result(result)
    
    @mcp.tool()
    async def list_all_tools():
        """获取所有可用工具的信息，包括名称、描述和输入参数模式
        
        Returns:
            包含所有工具信息的字典列表
        """
        tools_info = [
            {
                "name": "go_url",
                "description": "获取指定网页的基本信息和 element元素内容",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "要获取内容的网址"}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "close_browser",
                "description": "关闭浏览器",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "open_tab",
                "description": "打开一个新标签页",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "要在新标签页中打开的网址"}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "input_text",
                "description": "输入文本",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "要输入的文本"},
                        "index": {"type": "integer", "description": "要输入的element元素的索引"}
                    },
                    "required": ["text", "index"]
                }
            },
            {
                "name": "click_element",
                "description": "点击指定索引的element的元素索引",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "index": {"type": "integer", "description": "要点击的的element元素的索引"}
                    },
                    "required": ["index"]
                }
            },
            {
                "name": "go_back",
                "description": "返回上一页",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "switch_tab",
                "description": "切换到指定索引的标签页",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "page_id": {"type": "integer", "description": "要切换到的标签页的索引"}
                    },
                    "required": ["page_id"]
                }
            },
            {
                "name": "get_all_tabs",
                "description": "获取所有浏览器标签页",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "send_keys",
                "description": "发送特殊按键字符串，如Escape、Backspace、Insert、PageDown、Delete、Enter等，还支持组合键如Control+o、Control+Shift+T等",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "keys": {"type": "string", "description": "要发送的按键字符串"}
                    },
                    "required": ["keys"]
                }
            },
            {
                "name": "scroll_down",
                "description": "向下滚动页面",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "integer", "description": "滚动的像素数量"}
                    },
                    "required": ["amount"]
                }
            },
            {
                "name": "scroll_down_element",
                "description": "向下滚动指定索引的 SCROLL Element元素到页面底部",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "index": {"type": "integer", "description": "要滚动的element元素的索引"}
                    },
                    "required": ["index"]
                }
            },
            {
                "name": "scroll_up",
                "description": "向上滚动页面",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "integer", "description": "滚动的像素数量"}
                    },
                    "required": ["amount"]
                }
            },
            {
                "name": "scroll_to_text",
                "description": "滚动到包含特定文本的元素",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "要查找的文本"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "extract_content",
                "description": "提取页面完整内容，包括所有文本、图片、链接等信息",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_screenshot",
                "description": "获取当前页面截图",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "click_by_position",
                "description": "通过坐标点击页面",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "description": "X坐标"},
                        "y": {"type": "integer", "description": "Y坐标"}
                    },
                    "required": ["x", "y"]
                }
            },
            {
                "name": "web_search",
                "description": "在浏览器中搜索指定内容",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "要搜索的内容"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "do_date_picker",
                "description": "操作日期选择器组件",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "index": {"type": "integer", "description": "要操作的日期选择器元素的索引"},
                        "date": {"type": "string", "description": "单个日期字符串，格式如 '2024-01-15'"},
                        "date_range": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "日期范围列表，包含开始和结束日期，如 ['2024-01-15', '2024-01-20']"
                        }
                    },
                    "required": ["index"]
                }
            },
            {
                "name": "list_all_tools",
                "description": "获取所有可用工具的信息，包括名称、描述和输入参数模式",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
        
        return {
            "success": True,
            "total_tools": len(tools_info),
            "tools": tools_info
        }
   

def main():
    """主函数，创建并运行服务器"""
    server = create_server()
    server.run(transport='stdio')


if __name__ == "__main__":
    main() 