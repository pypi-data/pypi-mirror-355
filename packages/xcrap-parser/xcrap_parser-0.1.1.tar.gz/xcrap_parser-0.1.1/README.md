# Xcrap Parser

Xcrap Parser is a declarative, model-driven parser for extracting data from HTML and JSON files, with the ability to interleave both to extract even more information.

It is inspired by the parser embedded in the Xcrap Framework available for Node.js. It was built using **Parsel** for HTML parsing and **JMESPath** for JSON parsing.

## Installation

```cmd
pip install xcrap-parser
```

## Simple Usage

```python
from xcrap_parser import HtmlParsingModel

html = "<html><title>Title</title><body><h1>Heading</h1></body></html>"

root_parsing_model = HtmlParsingModel({
    "title": {
        "query": "title::text"
    },
    "heading": {
        "query": "h1::text"
    }
})

data = root_parsing_model.parse(html)

print(data)
```