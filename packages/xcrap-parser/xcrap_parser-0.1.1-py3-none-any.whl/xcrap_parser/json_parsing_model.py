from typing import Any, TypedDict, Optional
import jmespath
import json

from .parsing_model import ParsingModel

class JsonParsingModelShapeValue(TypedDict):
    __required__ = ["query"]
    __optional__ = ["default"]
    
    query: str
    default: Optional[Any]

class JsonParsingModelShape(TypedDict):
    __required__ = ["query"]
    __optional__ = ["default"]
    
    query: str
    default: Optional[Any]

class JsonParsingModel(ParsingModel):
    shape: JsonParsingModelShape
    
    def __init__(self, shape: JsonParsingModelShape) -> None:
        self.shape = shape
    
    def parse(self, source: str) -> Any:
        root = json.loads(source)
        data: dict[str, Any] = {}
        
        for key, value in self.shape.items():
            data[key] = self._parse_value(value, root)

        return data
        
    def _parse_value(self, value: JsonParsingModelShapeValue, root: Any) -> Any:
        extracted_data = jmespath.search(value["query"], root)
        
        if extracted_data is None and "default" in value:
            return value["default"]

        return extracted_data