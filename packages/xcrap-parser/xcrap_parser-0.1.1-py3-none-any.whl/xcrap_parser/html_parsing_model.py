from typing import Optional, Union, TypedDict, Any
from parsel import Selector

from .parsing_model import ParsingModel

class HtmlParsingModelShapeBaseValue(TypedDict, total = False):
    __required__ = ["query"]
    __optional__ = ["default", "multiple", "limit"]
    
    query: str
    default: Optional[Union[str, list[str]]]
    multiple: Optional[bool]
    limit: Optional[int]

class HtmlParsingModelShapeNestedValue(TypedDict, total = False):
    __required__ = ["query", "model"]
    __optional__ = ["default", "multiple", "limit"]
    
    query: str
    limit: Optional[int]
    multiple: Optional[bool]
    model: ParsingModel

HtmlParsingModelShape = dict[str, HtmlParsingModelShapeNestedValue | HtmlParsingModelShapeBaseValue]

class HtmlParsingModel(ParsingModel):
    shape: HtmlParsingModelShape
    
    def __init__(self, shape: HtmlParsingModelShape):
        self.shape = shape
    
    def parse(self, source: str) -> dict[str, Any]:
        root = Selector(source)
        data: dict[str, Any] = {}
        
        for key, value in self.shape.items():
            is_nested_value = "model" in value
            
            if is_nested_value:
                data[key] = self._parse_nested_value(value, root)
            else:
                data[key] = self._parse_base_value(value, root)
                
        return data
    
    def _parse_base_value(self, value: HtmlParsingModelShapeBaseValue, root: Selector) -> Optional[str | list[str]]:
        if "multiple" in value and value["multiple"]:
            selector_list = root.css(value["query"])
            
            if "limit" in value:
                selector_list = selector_list[value["limit"]:]
            
            return selector_list.getall()
    
        else:
            selector_list = root.css(value["query"])
            result = selector_list.get()
            
            if result is None and "default" in value:
                return value["default"]
            
            return result
            
    def _parse_nested_value(self, value: HtmlParsingModelShapeNestedValue, root: Selector) -> list[dict] | dict:
        if "multiple" in value and value["multiple"]:
            selector_list = root.css(value["query"])
            
            if "limit" in value:
                selector_list = selector_list[value["limit"]:]
                
            return [value["model"].parse(selector) for selector in selector_list]
        
        else:
            selector_list = root.css(value["query"])
            nested_source = selector_list.get()
            data = value["model"].parse(nested_source)
            
            return data