"""
浏览器操作模块
"""

from typing import Dict, Any, Optional, List

from orion_browser_mcp.config import config
from orion_browser_mcp.browser_interface import BrowserServiceInterface
from orion_browser_mcp.local_browser_service import LocalBrowserService
from orion_browser_mcp.remote_browser_service import RemoteBrowserService


class BrowserController:
    """浏览器控制器类，封装浏览器操作，支持本地和远程两种模式"""

    def __init__(self):
        """初始化浏览器控制器"""
        self._service: BrowserServiceInterface = None
        self._initialized = False

    def _get_service(self) -> BrowserServiceInterface:
        """根据配置获取浏览器服务实例
        
        Returns:
            BrowserServiceInterface: 浏览器服务实例
        """
        if self._service is None:
            if config.browser_mode == "remote":
                print(f"使用远程浏览器服务: {config.remote_service_url}")
                self._service = RemoteBrowserService()
            else:
                print("使用本地浏览器服务")
                self._service = LocalBrowserService()
        return self._service

    async def close(self) -> Dict[str, Any]:
        """关闭浏览器
        
        Returns:
            Dict: 包含操作结果的字典
        """
        service = self._get_service()
        result = await service.close()
        
        # 重置服务实例，下次使用时重新创建
        self._service = None
        self._initialized = False
        
        return result

    async def go_to_url(self, url: str) -> Dict[str, Any]:
        """导航到指定URL
        
        Args:
            url: 要访问的URL
            
        Returns:
            Dict: 包含操作结果的字典
        """
        service = self._get_service()
        return await service.go_to_url(url)

    async def open_tab(self, url: str) -> Dict[str, Any]:
        """打开新标签页
        
        Args:
            url: 要在新标签页中打开的URL
            
        Returns:
            Dict: 包含操作结果的字典
        """
        service = self._get_service()
        return await service.open_tab(url)

    async def input_text(self, text: str, index: int) -> Dict[str, Any]:
        """在输入框中输入文本
        
        Args:
            text: 要输入的文本
            index: 输入框索引
            
        Returns:
            Dict: 包含操作结果的字典
        """
        service = self._get_service()
        return await service.input_text(text, index)

    async def click_element(self, index: int) -> Dict[str, Any]:
        """点击元素
        
        Args:
            index: 要点击的元素索引
            
        Returns:
            Dict: 包含操作结果的字典
        """
        service = self._get_service()
        return await service.click_element(index)

    async def switch_tab(self, page_id: int) -> Dict[str, Any]:
        """切换标签页
        
        Args:
            page_id: 要切换到的标签页ID
            
        Returns:
            Dict: 包含操作结果的字典
        """
        service = self._get_service()
        return await service.switch_tab(page_id)
        
    async def get_all_tabs(self) -> Dict[str, Any]:
        """获取所有浏览器标签页
        
        Returns:
            Dict: 包含操作结果的字典
        """
        service = self._get_service()
        return await service.get_all_tabs()

    async def send_keys(self, keys: str) -> Dict[str, Any]:
        """发送键盘输入
        
        Args:
            keys: 要发送的键，如Escape、Backspace、Insert、PageDown、Delete、Enter等，
                  也支持组合键如Control+o、Control+Shift+T
                  
        Returns:
            Dict: 包含操作结果的字典
        """
        service = self._get_service()
        return await service.send_keys(keys)

    async def scroll_down(self, amount: int) -> Dict[str, Any]:
        """向下滚动页面
        
        Args:
            amount: 滚动的像素数量
            
        Returns:
            Dict: 包含操作结果的字典
        """
        service = self._get_service()
        return await service.scroll_down(amount)
        
    async def scroll_element_to_bottom_by_index(self, index: int) -> Dict[str, Any]:
        """滚动指定索引的element元素到页面底部
        
        Args:
            index: 要滚动的element元素的索引
        """
        service = self._get_service()
        return await service.scroll_element_to_bottom_by_index(index)
    
    async def go_back(self) -> Dict[str, Any]:
        """返回上一页
        
        Returns:
            Dict: 包含操作结果的字典
        """
        service = self._get_service()
        return await service.go_back()

    async def scroll_up(self, amount: int) -> Dict[str, Any]:
        """向上滚动页面
        
        Args:
            amount: 滚动的像素数量
            
        Returns:
            Dict: 包含操作结果的字典
        """
        service = self._get_service()
        return await service.scroll_up(amount)

    async def scroll_to_text(self, text: str) -> Dict[str, Any]:
        """滚动到包含特定文本的元素
        
        Args:
            text: 要查找的文本
            
        Returns:
            Dict: 包含操作结果的字典
        """
        service = self._get_service()
        return await service.scroll_to_text(text)

    async def extract_content(self) -> Dict[str, Any]:
        """提取页面内容以从页面中检索特定信息，例如所有公司名称、特定描述、有关的所有信息、结构化格式的公司链接或简单链接
        """
        service = self._get_service()
        return await service.extract_content()
        
    async def web_search(self, query: str) -> Dict[str, Any]:
        """在浏览器中搜索指定内容
        
        Args:
            query: 要搜索的内容
        """
        service = self._get_service()
        return await service.web_search(query)

    async def do_date_picker(self, index: int, date: Optional[str] = None, date_range: Optional[List[str]] = None):
        """操作日期选择器组件
        
        Args:
            index: 要操作的日期选择器元素的索引
            date: 单个日期字符串，格式如 "2024-01-15"
            date_range: 日期范围列表，包含开始和结束日期，如 ["2024-01-15", "2024-01-20"]
        """
        service = self._get_service()
        return await service.do_date_picker(index, date, date_range)
# 创建全局浏览器控制器实例
browser_controller = BrowserController() 