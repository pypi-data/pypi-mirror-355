# PyPDFMake

[![PyPI version](https://badge.fury.io/py/pypdfmake.svg)](https://badge.fury.io/py/pypdfmake)
[![Python Support](https://img.shields.io/pypi/pyversions/pypdfmake.svg)](https://pypi.org/project/pypdfmake/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Development Status](https://img.shields.io/pypi/status/pypdfmake.svg)](https://pypi.org/project/pypdfmake/)
[![Coverage](https://img.shields.io/badge/coverage-100.0%25-brightgreen)](#coverage)
[![Pydantic v2](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://pydantic.dev)

A Python library for generating [pdfmake](http://pdfmake.org/) document definitions using Pydantic models.

## Overview

PyPDFMake provides a type-safe way to create pdfmake document definitions in Python. It uses Pydantic for validation and type checking, making it easier to build complex PDF documents without worrying about the JSON structure expected by pdfmake.

## Features

-   Type-safe document definition creation with Pydantic models
-   Support for all pdfmake content types (text, tables, lists, images, etc.)
-   Helper functions for easier creation of common elements
-   Export to JSON for use with pdfmake
-   Python-friendly API with proper typing support

## Installation

```
pip install pypdfmake
```

Alternatively, if you are using `uv`:

```
uv add pypdfmake
```

## Usage

Here's a simple example of creating a PDF document definition:

```python
from pypdfmake import TDocumentDefinitions, ContentText, ContentColumns, Style
import json # used for testing

# Create a document definition
doc_definition = TDocumentDefinitions(
    content=[
        "First paragraph",
        "Another paragraph, this time a little bit longer to make sure, this line will be divided into at least two lines",
        ContentColumns(
            alignment="justify",
            columnGap=20.0,
            columns=[
                ContentText(text="Lorem ipsum dolor"),
                ContentText(text="Lorem ipsum dolor"),
            ],
        ),
    ],
    styles={
        "header": Style(fontSize=18, bold=True),
        "bigger": Style(fontSize=15, italics=True),
    },
    defaultStyle=Style(fontSize=10)
)

# Convert to JSON for use with pdfmake
json_data = doc_definition.model_dump_json(exclude_none=True)

assert json.loads(json_data) == {
    "content": [
        "First paragraph",
        "Another paragraph, this time a little bit longer to make sure, this line will be divided into at least two lines",
        {
            "alignment": "justify",
            "columns": [{"text": "Lorem ipsum dolor"}, {"text": "Lorem ipsum dolor"}],
            "columnGap": 20.0,
        },
    ],
    "styles": {
        "header": {"fontSize": 18.0, "bold": True},
        "bigger": {"fontSize": 15.0, "italics": True},
    },
    "defaultStyle": {"fontSize": 10.0},
    "compress": True,
    "creator": "pypdfmake",
}

# Now you can write it to a file or return it in an API response to a front-end

```

## Advanced Usage

The library supports all content types and features available in pdfmake:

-   Text with various formatting options
-   Tables with custom layouts
-   Lists (ordered and unordered)
-   Columns and stacks for layout
-   Images and SVGs
-   QR codes
-   Table of contents
-   Page and text references
-   Canvas for custom drawing
-   Headers, footers, and backgrounds
-   Document metadata

## Integration with JavaScript

Since pdfmake is a JavaScript library, you'll need to use the JSON output from PyPDFMake with pdfmake in a JavaScript environment. Here's a simple example:

```javascript
// In your JavaScript file
const fs = require('fs');
const pdfMake = require('pdfmake');

// Load the JSON created by PyPDFMake
const docDefinition = JSON.parse(fs.readFileSync('document.json', 'utf8'));

// Create the PDF
const printer = new pdfMake.Printer(fonts);
const pdfDoc = printer.createPdfKitDocument(docDefinition);

// Write to a file
pdfDoc.pipe(fs.createWriteStream('document.pdf'));
pdfDoc.end();
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
