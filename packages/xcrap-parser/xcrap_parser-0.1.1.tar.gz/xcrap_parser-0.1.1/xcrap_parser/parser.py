from typing import Self

from .parsing_model import ParsingModel

class Parser:
    source: str
    
    def __init__(self, source: str) -> None:
        self.source = source
        
    def parse_model(self, parsing_model: ParsingModel):
        return parsing_model.parse(self.source)
    
    @classmethod
    def load_file(
        cls,
        file_path: str,
        encoding: str = "utf-8",
        mode: str = "r"
    ) -> Self:
        with open(file_path, mode, encoding = encoding) as file:
            file_content = file.read()
            
        return Parser(file_content)