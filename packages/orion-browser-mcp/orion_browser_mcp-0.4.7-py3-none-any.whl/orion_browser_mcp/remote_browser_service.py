"""
远程浏览器服务实现
"""

import json
import aiohttp
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin

from orion_browser_mcp.config import config
from orion_browser_mcp.browser_interface import BrowserServiceInterface


class RemoteBrowserService(BrowserServiceInterface):
    """远程浏览器服务实现"""

    def __init__(self):
        """初始化远程浏览器服务"""
        self.base_url = config.remote_service_url
        self.timeout = config.remote_timeout
        self.session = None
        self.initialized = False

    async def initialize(self) -> None:
        """初始化HTTP会话"""
        if not self.initialized:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
            self.initialized = True

    async def close(self) -> Dict[str, Any]:
        """关闭HTTP会话和远程浏览器
        
        Returns:
            Dict: 包含操作结果的字典
        """
        try:
            if self.initialized and self.session:
                # 先尝试关闭远程浏览器
                action_data = {
                    "action": {
                        "close": {}
                    }
                }
                result = await self._make_action_request(action_data)
                
                # 关闭HTTP会话
                await self.session.close()
                self.initialized = False
                
                return result or {"status": "success", "message": "远程浏览器和会话已关闭"}
        except Exception as e:
            if self.session:
                await self.session.close()
                self.initialized = False
            return {"status": "error", "message": f"关闭远程服务时出错: {str(e)}"}

    async def _make_action_request(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """发送浏览器动作请求到远程服务
        
        Args:
            action_data: 包含action结构的请求数据
            
        Returns:
            Dict: 服务器响应
        """
        try:
            await self.initialize()
            
            url = urljoin(self.base_url, "/browser/action")
            headers = {"Content-Type": "application/json"}
            json_data = json.dumps(action_data)
            
            async with self.session.post(url, data=json_data, headers=headers) as response:
                return await self._handle_response(response)
                
        except aiohttp.ClientTimeout:
            return {"status": "error", "message": "请求超时"}
        except aiohttp.ClientError as e:
            return {"status": "error", "message": f"网络错误: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"远程服务调用失败: {str(e)}"}

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """处理HTTP响应
        
        Args:
            response: HTTP响应对象
            
        Returns:
            Dict: 处理后的响应数据
        """
        try:
            if response.content_type == "application/json":
                data = await response.json()
            else:
                text = await response.text()
                data = {"status": "success", "message": text}
            
            if response.status >= 400:
                data["status"] = "error"
                if "message" not in data:
                    data["message"] = f"HTTP {response.status}: {response.reason}"
            
            return data
        except Exception as e:
            return {"status": "error", "message": f"解析响应失败: {str(e)}"}

    async def go_to_url(self, url: str) -> Dict[str, Any]:
        """导航到指定URL
        
        Args:
            url: 要访问的URL
            
        Returns:
            Dict: 包含操作结果的字典
        """
        action_data = {
            "action": {
                "go_to_url": {
                    "url": url
                }
            }
        }
        return await self._make_action_request(action_data)

    async def open_tab(self, url: str) -> Dict[str, Any]:
        """打开新标签页
        
        Args:
            url: 要在新标签页中打开的URL
            
        Returns:
            Dict: 包含操作结果的字典
        """
        action_data = {
            "action": {
                "open_tab": {
                    "url": url
                }
            }
        }
        return await self._make_action_request(action_data)

    async def input_text(self, text: str, index: int) -> Dict[str, Any]:
        """在输入框中输入文本
        
        Args:
            text: 要输入的文本
            index: 输入框索引
            
        Returns:
            Dict: 包含操作结果的字典
        """
        action_data = {
            "action": {
                "input_text": {
                    "text": text,
                    "index": index
                }
            }
        }
        return await self._make_action_request(action_data)

    async def click_element(self, index: int) -> Dict[str, Any]:
        """点击元素
        
        Args:
            index: 要点击的元素索引
            
        Returns:
            Dict: 包含操作结果的字典
        """
        action_data = {
            "action": {
                "click_element": {
                    "index": index
                }
            }
        }
        return await self._make_action_request(action_data)

    async def switch_tab(self, page_id: int) -> Dict[str, Any]:
        """切换标签页
        
        Args:
            page_id: 要切换到的标签页ID
            
        Returns:
            Dict: 包含操作结果的字典
        """
        action_data = {
            "action": {
                "switch_tab": {
                    "page_id": page_id
                }
            }
        }
        return await self._make_action_request(action_data)

    async def get_all_tabs(self) -> Dict[str, Any]:
        """获取所有浏览器标签页
        
        Returns:
            Dict: 包含操作结果的字典
        """
        action_data = {
            "action": {
                "get_all_tabs": {}
            }
        }
        return await self._make_action_request(action_data)

    async def send_keys(self, keys: str) -> Dict[str, Any]:
        """发送键盘输入
        
        Args:
            keys: 要发送的键，如Escape、Backspace、Insert、PageDown、Delete、Enter等，
                  也支持组合键如Control+o、Control+Shift+T
                  
        Returns:
            Dict: 包含操作结果的字典
        """
        action_data = {
            "action": {
                "send_keys": {
                    "keys": keys
                }
            }
        }
        return await self._make_action_request(action_data)

    async def scroll_down(self, amount: int) -> Dict[str, Any]:
        """向下滚动页面
        
        Args:
            amount: 滚动的像素数量
            
        Returns:
            Dict: 包含操作结果的字典
        """
        action_data = {
            "action": {
                "scroll_down": {
                    "amount": amount
                }
            }
        }
        return await self._make_action_request(action_data)

    async def scroll_element_to_bottom_by_index(self, index: int) -> Dict[str, Any]:
        """滚动指定索引的element元素到页面底部
        
        Args:
            index: 要滚动的element元素的索引
        """
        action_data = {
            "action": {
                "scroll_element_to_bottom_by_index": {
                    "index": index
                }
            }
        }
        return await self._make_action_request(action_data)

    async def go_back(self) -> Dict[str, Any]:
        """返回上一页
        
        Returns:
            Dict: 包含操作结果的字典
        """
        action_data = {
            "action": {
                "go_back": {}
            }
        }
        return await self._make_action_request(action_data)

    async def scroll_up(self, amount: int) -> Dict[str, Any]:
        """向上滚动页面
        
        Args:
            amount: 滚动的像素数量
            
        Returns:
            Dict: 包含操作结果的字典
        """
        action_data = {
            "action": {
                "scroll_up": {
                    "amount": amount
                }
            }
        }
        return await self._make_action_request(action_data)

    async def scroll_to_text(self, text: str) -> Dict[str, Any]:
        """滚动到包含特定文本的元素
        
        Args:
            text: 要查找的文本
            
        Returns:
            Dict: 包含操作结果的字典
        """
        action_data = {
            "action": {
                "scroll_to_text": {
                    "text": text
                }
            }
        }
        return await self._make_action_request(action_data)

    async def extract_content(self) -> Dict[str, Any]:
        """提取页面内容以从页面中检索特定信息，例如所有公司名称、特定描述、有关的所有信息、结构化格式的公司链接或简单链接
        """
        action_data = {
            "action": {
                "extract_content": {}
            }
        }
        return await self._make_action_request(action_data)
    
    async def do_date_picker(self, index: int, date: Optional[str] = None, date_range: Optional[List[str]] = None):
        """操作日期选择器组件
        
        Args:
            index: 要操作的日期选择器元素的索引
            date: 单个日期字符串，格式如 "2024-01-15"
            date_range: 日期范围列表，包含开始和结束日期，如 ["2024-01-15", "2024-01-20"]
        """
        action_data = {
            "action": {
                "do_date_picker": {
                    "index": index,
                    "date": date,
                    "date_range": date_range
                }
            }
        }
        return await self._make_action_request(action_data)

    async def web_search(self, query: str) -> Dict[str, Any]:
        """在浏览器中搜索指定内容
        
        Args:
            query: 要搜索的内容
        """
        # web_search 通过 go_to_url 实现
        search_url = f"https://cn.bing.com/search?q={query}"
        action_data = {
            "action": {
                "go_to_url": {
                    "url": search_url
                }
            }
        }
        return await self._make_action_request(action_data) 