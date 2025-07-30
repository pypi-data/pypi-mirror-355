from typing import Optional, Any
from parsel import Selector

from .parsing_model import ParsingModel
from .parser import Parser

class HtmlParser(Parser):
    root: Selector
    
    def __init__(self, source) -> None:
        super().__init__(source)
        
        self.root = Selector(source)
        
    def parse_first(
        self,
        query: str,
        default: Optional[Any] = None
    ) -> Optional[str]:
        selector_list = self.root.css(query)
        
        if len(selector_list) == 0:
            return default
        
        data = selector_list.get()
        
        return data or default
    
    def parse_many(
        self,
        query: str,
        limit: Optional[int] = None
    ) -> list[str]:
        selector_list = self.root.css(query)
        items = []
        
        for selector in selector_list:
            if not limit is None and len(items) >= limit: break
            data = selector.get()
            items.append(data)
            
        return items
    
    def extract_first(
        self,
        model: ParsingModel,
        query: Optional[str] = None,
    ) -> dict[str, Any]:
        selector = self.root.css(query) if not query is None else self.root
        source = selector.get()
        return model.parse(source)
    
    def extract_many(
        self,
        model: ParsingModel,
        query: str,
        limit: Optional[int] = None
    ) -> list[dict[str, Any]]:
        selector_list = self.root.css(query)
        items = []
        
        for selector in selector_list:
            if not limit is None and len(items) >= limit: break
            source = selector.get()
            data = model.parse(source)
            items.append(data)
            
        return data
    