from typing import Any
import jmespath
import json

from .parser import Parser

class JsonParser(Parser):
    root: Any
    
    def __init__(self, source) -> None:
        super().__init__(source)
        
        self.root = json.loads(source)
        
    def extract(self, query: str) -> Any:
        return jmespath.search(query, self.root)