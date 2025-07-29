"""
浏览器服务抽象接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BrowserServiceInterface(ABC):
    """浏览器服务抽象接口"""

    @abstractmethod
    async def initialize(self) -> None:
        """初始化浏览器服务"""
        pass

    @abstractmethod
    async def close(self) -> Dict[str, Any]:
        """关闭浏览器"""
        pass

    @abstractmethod
    async def go_to_url(self, url: str) -> Dict[str, Any]:
        """导航到指定URL"""
        pass

    @abstractmethod
    async def open_tab(self, url: str) -> Dict[str, Any]:
        """打开新标签页"""
        pass

    @abstractmethod
    async def input_text(self, text: str, index: int) -> Dict[str, Any]:
        """在输入框中输入文本"""
        pass

    @abstractmethod
    async def click_element(self, index: int) -> Dict[str, Any]:
        """点击元素"""
        pass

    @abstractmethod
    async def switch_tab(self, page_id: int) -> Dict[str, Any]:
        """切换标签页"""
        pass

    @abstractmethod
    async def get_all_tabs(self) -> Dict[str, Any]:
        """获取所有浏览器标签页"""
        pass

    @abstractmethod
    async def send_keys(self, keys: str) -> Dict[str, Any]:
        """发送键盘输入"""
        pass

    @abstractmethod
    async def scroll_down(self, amount: int) -> Dict[str, Any]:
        """向下滚动页面"""
        pass

    @abstractmethod
    async def scroll_element_to_bottom_by_index(self, index: int) -> Dict[str, Any]:
        """滚动指定索引的element元素到页面底部"""
        pass

    @abstractmethod
    async def go_back(self) -> Dict[str, Any]:
        """返回上一页"""
        pass

    @abstractmethod
    async def scroll_up(self, amount: int) -> Dict[str, Any]:
        """向上滚动页面"""
        pass

    @abstractmethod
    async def scroll_to_text(self, text: str) -> Dict[str, Any]:
        """滚动到包含特定文本的元素"""
        pass

    @abstractmethod
    async def extract_content(self) -> Dict[str, Any]:
        """提取页面内容"""
        pass

    @abstractmethod
    async def web_search(self, query: str) -> Dict[str, Any]:
        """在浏览器中搜索指定内容"""
        pass 