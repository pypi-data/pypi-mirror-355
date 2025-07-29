from __future__ import annotations
from typing import (
    Literal,
    Any,
    Callable,
    Union,
)  # Removed Optional if not used elsewhere
from pydantic import BaseModel, Field
from datetime import datetime

# PageSize related types
PredefinedPageSize = Literal[
    "4A0",
    "2A0",
    "A0",
    "A1",
    "A2",
    "A3",
    "A4",
    "A5",
    "A6",
    "A7",
    "A8",
    "A9",
    "A10",
    "B0",
    "B1",
    "B2",
    "B3",
    "B4",
    "B5",
    "B6",
    "B7",
    "B8",
    "B9",
    "B10",
    "C0",
    "C1",
    "C2",
    "C3",
    "C4",
    "C5",
    "C6",
    "C7",
    "C8",
    "C9",
    "C10",
    "RA0",
    "RA1",
    "RA2",
    "RA3",
    "RA4",
    "SRA0",
    "SRA1",
    "SRA2",
    "SRA3",
    "SRA4",
    "EXECUTIVE",
    "FOLIO",
    "LEGAL",
    "LETTER",
    "TABLOID",
]
"""Standard predefined page sizes for PDF documents."""


class CustomPageSize(BaseModel):
    """Defines a custom page size with specific width and height."""

    width: float = Field(description="The width of the page in points.")
    height: float = Field(description="The height of the page in points.")


PageSize = PredefinedPageSize | CustomPageSize
"""Represents the size of a page, either a predefined string (e.g., 'A4') or a CustomPageSize object."""


class Position(BaseModel):
    """Represents a 2D position with x and y coordinates."""

    x: float = Field(description="The x-coordinate in points.")
    y: float = Field(description="The y-coordinate in points.")


PageOrientation = Literal["portrait", "landscape"]
"""Defines the orientation of a page: 'portrait' or 'landscape'."""

PageBreak = Literal[
    "before", "beforeEven", "beforeOdd", "after", "afterEven", "afterOdd"
]
"""Specifies how a page break should occur relative to content (e.g., 'before' an element, 'afterOdd' page)."""

Size = float | Literal["auto", "*"] | str
"""
Represents a size value.
Can be:
- A number (in points).
- 'auto' (content-dependent size).
- '*' (star sizing, for proportional distribution of space, e.g., in table columns).
- A string percentage (e.g., "50%").
"""

PatternFill = tuple[str, str]
"""Defines a pattern fill with foreground and background colors: `[<foregroundColor>, <backgroundColor>]`."""

Margins = float | list[float]
"""
Represents margins.
Can be:
- A single number for all sides (e.g., `40`).
- A list of two numbers `[horizontal, vertical]` (e.g., `[20, 40]`).
- A list of four numbers `[left, top, right, bottom]` (e.g., `[10, 20, 10, 20]`).
"""

Decoration = Literal["underline", "strike", "overline"]
"""Text decoration type."""

DecorationStyle = Literal["dashed", "dotted", "double", "wavy"]
"""Style of the text decoration (e.g., 'dashed' underline)."""

Alignment = Literal["left", "right", "justify", "center"]
"""Text alignment options."""


class Dash(BaseModel):
    """Defines a dash pattern for lines, used in canvas or borders."""

    length: float = Field(description="Length of the dash in points.")
    space: float | None = Field(
        default=None,
        description="Length of the space after the dash in points. Defaults to `length` if not provided.",
    )


class LineStyle(BaseModel):
    """Defines the style of a line, currently supporting dash patterns. (Primarily for table cell borders in some contexts)."""

    dash: Dash | None = Field(default=None, description="Dash pattern for the line.")


class ContextPageSize(BaseModel):
    """Represents the current page size context, typically passed to dynamic content functions."""

    width: float = Field(description="The width of the current page in points.")
    height: float = Field(description="The height of the current page in points.")


class TFontFamilyTypes(BaseModel):
    """Defines font files for different styles (normal, bold, italics, bolditalics) within a font family."""

    normal: str | None = Field(
        default=None,
        description="Path or reference to the normal (roman) font file/stream.",
    )
    bold: str | None = Field(
        default=None, description="Path or reference to the bold font file/stream."
    )
    italics: str | None = Field(
        default=None, description="Path or reference to the italics font file/stream."
    )
    bolditalics: str | None = Field(
        default=None,
        description="Path or reference to the bold-italics font file/stream.",
    )


TFontDictionary = dict[str, TFontFamilyTypes]
"""A dictionary mapping font family names (e.g., 'Roboto') to their TFontFamilyTypes definitions."""


class TDocumentInformation(BaseModel):
    """Metadata for the PDF document (e.g., title, author, subject)."""

    title: str | None = Field(default=None, description="The title of the document.")
    author: str | None = Field(default=None, description="The author of the document.")
    subject: str | None = Field(
        default=None, description="The subject of the document."
    )
    keywords: str | None = Field(
        default=None,
        description="Keywords associated with the document, comma-separated.",
    )
    producer: str | None = Field(
        default=None,
        description="The producer of the PDF. pdfmake sets its own default.",
    )
    creator: str | None = Field(
        default=None, description="The creator of the PDF. pypdfmake sets a default."
    )
    creationDate: datetime = Field(
        default_factory=datetime.now,
        description="The creation date of the document. Defaults to current time.",
    )
    modDate: datetime = Field(
        default_factory=datetime.now,
        description="The modification date of the document. Defaults to current time.",
    )
    trapped: str | None = Field(
        default=None,
        description="Trapping information for the document (e.g., 'True', 'False', 'Unknown').",
    )


PDFSubset = Literal["PDF/A-1B", "PDF/A-2B", "PDF/A-3B", "PDF/X-3"]
"""Specifies a PDF subset standard for archival or print purposes (e.g., 'PDF/A-1B')."""


class Style(BaseModel):
    """Defines a style that can be applied to content elements, affecting their appearance and layout."""

    font: str | None = Field(
        default=None,
        description="Name of the font family (must be defined in `fonts` dictionary).",
    )
    fontSize: float | None = Field(default=None, description="Font size in points.")
    fontFeatures: list[str] | None = Field(
        default=None, description="OpenType font features (e.g., ['smcp', 'liga=0'])."
    )
    bold: bool | None = Field(default=None, description="Apply bold style.")
    italics: bool | None = Field(default=None, description="Apply italic style.")
    characterSpacing: float | None = Field(
        default=None, description="Space between characters in points."
    )
    lineHeight: float | None = Field(
        default=None,
        description="Line height as a multiplier of font size (e.g., 1.5) or absolute points.",
    )
    color: str | None = Field(
        default=None, description="Text color (e.g., 'blue', '#00ff00')."
    )
    background: str | None = Field(
        default=None, description="Background color of the text block."
    )
    markerColor: str | None = Field(
        default=None, description="Color of list markers (bullets/numbers)."
    )
    decoration: Decoration | None = Field(
        default=None, description="Text decoration ('underline', 'strike', 'overline')."
    )
    decorationStyle: DecorationStyle | None = Field(
        default=None,
        description="Style of the decoration ('dashed', 'dotted', 'double', 'wavy').",
    )
    decorationColor: str | None = Field(
        default=None, description="Color of the decoration."
    )
    alignment: Alignment | None = Field(
        default=None,
        description="Text alignment ('left', 'right', 'center', 'justify').",
    )
    margin: Margins | None = Field(
        default=None, description="Margins around the element."
    )
    width: Size | None = Field(default=None, description="Width of the element.")
    height: Size | None = Field(default=None, description="Height of the element.")
    opacity: float | None = Field(
        default=None, description="Opacity of the element (0.0 to 1.0)."
    )
    leadingIndent: float | None = Field(
        default=None, description="Indentation for the first line of a paragraph."
    )
    preserveLeadingSpaces: bool | None = Field(
        default=None, description="If true, preserve leading spaces in text."
    )
    preserveTrailingSpaces: bool | None = Field(
        default=None, description="If true, preserve trailing spaces in text."
    )
    noWrap: bool | None = Field(
        default=None, description="If true, prevent text from wrapping."
    )
    pageBreak: PageBreak | None = Field(
        default=None, description="Page break behavior before or after the element."
    )
    pageOrientation: PageOrientation | None = Field(
        default=None,
        description="Specific page orientation for the page this element starts on.",
    )
    headlineLevel: int | None = Field(
        default=None, description="Headline level for accessibility and TOC generation."
    )
    # Table cell specific properties
    fillColor: str | None = Field(
        default=None, description="Background color for table cells or canvas shapes."
    )
    rowSpan: int | None = Field(
        default=None, description="Number of rows this table cell should span."
    )
    colSpan: int | None = Field(
        default=None, description="Number of columns this table cell should span."
    )
    border: list[bool] | None = Field(
        default=None,
        description="Border for table cells: `[left, top, right, bottom]`. True for default line, False for no line.",
    )
    borderColor: str | list[str] | None = Field(
        default=None,
        description="Border color for table cells. Single color or `[left, top, right, bottom]`.",
    )
    verticalAlignment: Literal["top", "center", "bottom"] | None = Field(
        default=None, description="Vertical alignment within a table cell."
    )
    # Style inheritance
    style: str | list[str] | None = Field(
        default=None,
        description="Name of a style or list of style names to inherit from.",
    )
    model_config = {
        "extra": "allow"
    }  # Allow other properties for pdfmake compatibility


StyleReference = str | Style | list[str | Style]
"""A reference to a style: can be a style name (string), a Style object, or a list of these for cascading styles."""

StyleDictionary = dict[str, Style]
"""A dictionary mapping style names (e.g., 'headerStyle') to Style objects."""


class ContentBase(Style):
    """Base class for content elements, providing common styling capabilities and Table of Contents (TOC) properties."""

    id: str | None = Field(
        default=None,
        description="An optional identifier for the content element. Used for page references, text references, or as a link target.",
    )
    tocItem: bool | StyleReference | None = Field(
        default=None,
        description="If true or a StyleReference, this item will be included in the Table of Contents. The StyleReference can style the TOC entry.",
    )
    tocStyle: StyleReference | None = Field(
        default=None,
        description="Style to be applied specifically to this item's entry in the Table of Contents.",
    )
    tocMargin: Margins | None = Field(
        default=None,
        description="Margins for this item's entry in the Table of Contents.",
    )


class ContentLink(BaseModel):
    """Properties for creating hyperlinks within content elements like text or images."""

    link: str | None = Field(
        default=None,
        description="An external URLOrderedListElement to link to (e.g., 'https://example.com').",
    )
    linkToPage: int | None = Field(
        default=None,
        description="A 1-based page number to link to within the current document.",
    )
    linkToDestination: str | None = Field(
        default=None,
        description="The `id` of a content element to link to within the current document.",
    )


class ContentText(ContentBase, ContentLink):
    """
    Represents a text block. Can be a simple string or a list of mixed string and styled text objects
    for complex inline styling.
    """

    text: str | int | list[str | int | ContentText] = Field(
        description="The text content. Can be a string, number, or a list of strings, numbers, or other `ContentText` objects for complex inline styling and mixed formatting."
    )


class ContentColumns(ContentBase):
    """Defines a layout with multiple columns. Content flows from one column to the next."""

    columns: list["AnyContent"] = Field(
        description="A list of content elements, each representing a column. Content can be simple text or complex structures."
    )
    columnGap: float | None = Field(
        default=None, description="The space between columns in points."
    )


class ContentStack(ContentBase):
    """Stacks content elements vertically. Each element in the stack is placed below the previous one."""

    stack: list["AnyContent"] = Field(
        description="A list of content elements to be stacked vertically."
    )


OrderedListType = Literal[
    "none",  # No marker
    "decimal",  # 1, 2, 3,...
    "lower-alpha",  # a, b, c,...
    "upper-alpha",  # A, B, C,...
    "lower-roman",  # i, ii, iii,...
    "upper-roman",  # I, II, III,...
]
"""Marker types for ordered lists (e.g., '1.', 'a.', 'A.', 'i.', 'I.'). Defaults to 'decimal'."""


class OrderedListElementProperties(BaseModel):
    """Properties that can be applied to items in an ordered list."""

    counter: int | None = Field(
        default=None,
        description="Overrides the counter for this list item. Does not influence counters for other list items.",
    )
    type: OrderedListType | None = Field(
        default=None,
        description="Overrides the list marker type for this list item.",
    )


class OrderedListElement(ContentBase, OrderedListElementProperties):
    """
    Represents an item in an ordered list, combining content and list-specific properties.
    """

    text: str | int | list[str | int | ContentText] = Field(
        description="The text content of the list item. Can be a string, number, or a list of mixed content."
    )


class ContentOrderedList(ContentBase):
    """Represents an ordered list (e.g., numbered or lettered)."""

    ol: list[AnyContent | str | OrderedListElement] = Field(
        description="A list of content elements, each representing a list item."
    )
    type: OrderedListType | None = Field(
        default=None,
        description="The type of marker for the list items (e.g., 'lower-alpha', 'upper-roman'). Defaults to decimal numbers.",
    )
    reversed: bool | None = Field(
        default=None,
        description="If true, the list numbering will be in reverse order.",
    )
    start: int | None = Field(
        default=None, description="The starting number for the list (e.g., start at 5)."
    )
    separator: str | list[str] | None = Field(
        default=None,
        description="Custom separator for list items. Can be a single string (e.g., ')') or a [before, after] list (e.g., ['(', ')']).",
    )


class UnorderedListElementProperties(BaseModel):
    """Properties that can be applied to items in an unordered list."""

    type: UnorderedListType | None = Field(
        default=None,
        description="Overrides the list marker type for this list item.",
    )


UnorderedListType = Literal[
    "disc",  # Default, filled circle
    "circle",  # Hollow circle
    "square",  # Filled square
    "none",  # No marker
]
"""Marker types for unordered lists (bullet styles, e.g., 'disc', 'circle', 'square'). Defaults to 'disc' (bullet)."""


class UnorderedListElement(ContentBase, UnorderedListElementProperties):
    """
    Represents an item in an unordered list, combining content and list-specific properties.
    """

    text: str | int | list[str | int | ContentText] = Field(
        description="The text content of the list item. Can be a string, number, or a list of mixed content."
    )


class ContentUnorderedList(ContentBase):
    """Represents an unordered list (e.g., bulleted)."""

    ul: list[AnyContent | str | UnorderedListElement] = Field(
        description="A list of content elements, each representing a list item."
    )
    type: UnorderedListType | None = Field(
        default=None,
        description="The type of marker for the list items (e.g., 'square', 'circle'). Defaults to 'bullet'.",
    )


Point = tuple[float, float]
"""Represents a 2D point as a tuple (x, y) in points, used in canvas elements."""

CanvasLineCap = Literal["butt", "round", "square"]
"""Defines the style for the end caps of a line in a canvas: 'butt', 'round', or 'square'."""

CanvasLineJoin = Literal["miter", "round", "bevel"]
"""Defines the style for the joins between two lines in a canvas: 'miter', 'round', or 'bevel'."""


class CanvasElementProperties(BaseModel):
    """Base properties for canvas elements, including line, fill, and general styling."""

    lineColor: str | None = Field(
        default=None,
        description="Color of the line for vector shapes (e.g., 'red', '#0000FF'). Default is 'black' if a line is drawn.",
    )
    lineWidth: float = Field(default=1, description="Width of the line in points.")
    lineCap: CanvasLineCap | None = Field(
        default=None, description="Style of line end caps."
    )
    lineJoin: CanvasLineJoin | None = Field(
        default=None,
        description="Style of line joins when multiple line segments meet.",
    )
    dash: Dash | None = Field(
        default=None,
        description="Dash pattern for lines (e.g., `{ length: 4, space: 2 }`).",
    )
    miterLimit: float | None = Field(
        default=None,
        description="Miter limit for line joins when `lineJoin` is 'miter'.",
    )
    fillColor: str | None = Field(
        default=None, description="Color to fill the shape (e.g., 'yellow', '#FFFF00')."
    )
    fillOpacity: float | None = Field(
        default=None, description="Opacity of the fill (0.0 to 1.0)."
    )
    color: str | None = Field(
        default=None,
        description="General color property. Can act as a shorthand for `lineColor` or `fillColor` depending on the element, or for text color if the canvas element is text (not standard in pdfmake vector canvas).",
    )
    opacity: float | None = Field(
        default=None,
        description="General opacity for the entire canvas element (0.0 to 1.0).",
    )


class CanvasRect(CanvasElementProperties):
    """A rectangle canvas element."""

    type: Literal["rect"] = Field(
        default="rect", description="Type of canvas element, must be 'rect'."
    )
    x: float = Field(
        description="X-coordinate of the top-left corner of the rectangle."
    )
    y: float = Field(
        description="Y-coordinate of the top-left corner of the rectangle."
    )
    w: float = Field(description="Width of the rectangle.")
    h: float = Field(description="Height of the rectangle.")
    r: float | None = Field(
        default=None,
        description="Radius for rounded corners. If 0 or undefined, corners are square.",
    )


class CanvasLine(CanvasElementProperties):
    """A line canvas element, connecting two points."""

    type: Literal["line"] = Field(
        default="line", description="Type of canvas element, must be 'line'."
    )
    x1: float = Field(description="X-coordinate of the starting point of the line.")
    y1: float = Field(description="Y-coordinate of the starting point of the line.")
    x2: float = Field(description="X-coordinate of the ending point of the line.")
    y2: float = Field(description="Y-coordinate of the ending point of the line.")


class CanvasPolyline(CanvasElementProperties):
    """A polyline (series of connected lines) or polygon canvas element."""

    type: Literal["polyline"] = Field(
        default="polyline", description="Type of canvas element, must be 'polyline'."
    )
    points: list[Point] = Field(
        description="List of points `[(x, y), ...]` defining the vertices of the polyline."
    )
    closePath: bool | None = Field(
        default=None,
        description="If true, connects the last point to the first, effectively creating a polygon that can be filled.",
    )


class CanvasEllipse(CanvasElementProperties):
    """An ellipse or circle canvas element."""

    type: Literal["ellipse"] = Field(
        default="ellipse", description="Type of canvas element, must be 'ellipse'."
    )
    x: float = Field(description="X-coordinate of the center of the ellipse.")
    y: float = Field(description="Y-coordinate of the center of the ellipse.")
    r1: float = Field(description="Horizontal radius of the ellipse.")
    r2: float | None = Field(
        default=None,
        description="Vertical radius of the ellipse. If not provided, defaults to `r1` (creating a circle).",
    )


CanvasElement = CanvasRect | CanvasPolyline | CanvasLine | CanvasEllipse
"""Union type for all supported canvas vector elements."""


class ContentCanvas(ContentBase):
    """Allows drawing vector graphics using a canvas-like API within the document."""

    canvas: list[CanvasElement] = Field(
        description="A list of canvas elements (rectangles, lines, polylines, ellipses) to draw."
    )


ImageAlignment = Literal["left", "right", "center"]
"""Horizontal alignment for images within their bounding box if `cover` is used or if the image has fixed dimensions smaller than available space."""

ImageVerticalAlignment = Literal["top", "bottom", "center"]
"""Vertical alignment for images, similar to `ImageAlignment` but for the vertical axis."""


class ImageCover(BaseModel):
    """
    Defines how an image should cover its container, similar to CSS `background-size: cover`.
    The image is scaled to maintain its aspect ratio while filling the element's entire content box.
    If the image's aspect ratio does not match the aspect ratio of its box, then the image will be clipped to fit.
    """

    width: float | None = Field(
        default=None,
        description="Target width for the cover area. Image will be scaled to cover this width.",
    )
    height: float | None = Field(
        default=None,
        description="Target height for the cover area. Image will be scaled to cover this height.",
    )
    align: ImageAlignment | None = Field(
        default=None,
        description="Horizontal alignment of the image within the covered area if aspect ratios differ.",
    )
    valign: ImageVerticalAlignment | None = Field(
        default=None,
        description="Vertical alignment of the image within the covered area if aspect ratios differ.",
    )


class ContentImage(ContentBase, ContentLink):
    """Represents an image to be embedded in the document."""

    image: str = Field(
        description="The key of the image in the `images` dictionary (defined at the document root) or a base64 encoded image string (e.g., 'data:image/jpeg;base64,...')."
    )
    width: Size | None = Field(
        default=None,
        description="Width of the image in points. If undefined, uses natural image width.",
    )
    height: Size | None = Field(
        default=None,
        description="Height of the image in points. If undefined, uses natural image height.",
    )
    fit: tuple[float, float] | None = Field(
        default=None,
        description="Tuple `[maxWidth, maxHeight]` to scale the image to fit within these dimensions while maintaining aspect ratio.",
    )
    cover: ImageCover | None = Field(
        default=None,
        description="Cover options for the image, allowing it to fill a specified area, potentially being cropped.",
    )
    pageBreak: PageBreak | None = Field(
        default=None, description="Page break behavior before or after the image."
    )
    absolutePosition: Position | None = Field(
        default=None,
        description="Position the image absolutely on the page at `(x, y)` coordinates.",
    )
    relativePosition: Position | None = Field(
        default=None,
        description="Position the image relative to its normal flow position by `(x, y)` offset.",
    )
    opacity: float | None = Field(
        default=None, description="Opacity of the image (0.0 to 1.0)."
    )


class ContentSvg(ContentBase, ContentLink):
    """Represents an SVG image to be embedded in the document."""

    svg: str = Field(
        description="The SVG content as a string (e.g., '<svg>...</svg>')."
    )
    width: Size | None = Field(
        default=None,
        description="Width to render the SVG in points. If undefined, may use SVG's native width.",
    )
    height: Size | None = Field(
        default=None,
        description="Height to render the SVG in points. If undefined, may use SVG's native height.",
    )
    fit: tuple[float, float] | None = Field(
        default=None,
        description="Tuple `[maxWidth, maxHeight]` to scale the SVG to fit within these dimensions while maintaining aspect ratio.",
    )
    # font: str | None = Field(default=None, description="Default font for text within the SVG, if not specified in the SVG itself.") # pdfmake supports this


ContentTableRef = "ContentTable"  # Internal type alias, not for direct user use.

DynamicRowSizeCallable = Callable[[int], float | Literal["auto"]]
"""
A callable that dynamically determines row height in a table.
It receives:
- `rowIndex`: The 0-based index of the row.
Should return a height in points or 'auto'.
"""

DynamicLayoutCallable = Callable[[int, ContentTableRef], "Any | None"]
"""
A callable for dynamically determining horizontal table layout properties (lines, padding).
It receives:
- `index`: The 0-based index of the line or column.
- `node`: The `ContentTable` node itself.
Should return a value appropriate for the property (e.g., line width, padding value).
"""

VerticalDynamicLayoutCallable = Callable[[int, ContentTableRef], "Any | None"]
"""
A callable for dynamically determining vertical table layout properties (lines, padding).
It receives:
- `index`: The 0-based index of the line or row.
- `node`: The `ContentTable` node itself.
Should return a value appropriate for the property (e.g., line width, padding value).
"""

DynamicCellLayoutCallable = Callable[[int, ContentTableRef, int], "Any | None"]
"""
A callable for dynamically determining table cell layout properties (padding, fill color) for horizontal context.
It receives:
- `rowIndex`: The 0-based index of the row.
- `node`: The `ContentTable` node itself.
- `columnIndex`: The 0-based index of the column.
Should return a value appropriate for the property (e.g., padding value, color string).
"""

VerticalDynamicCellLayoutCallable = Callable[[int, ContentTableRef, int], "Any | None"]
"""
A callable for dynamically determining table cell layout properties (padding, fill color) for vertical context.
It receives:
- `columnIndex`: The 0-based index of the column.
- `node`: The `ContentTable` node itself.
- `rowIndex`: The 0-based index of the row.
Should return a value appropriate for the property (e.g., padding value, color string).
"""


DynamicContentCallable = Callable[
    [int, int, ContextPageSize], Union["AnyContent", list["AnyContent"], None]
]
"""
A callable that dynamically generates content for elements like header, footer, or the main document body.
It receives:
- `currentPage`: The current page number (1-based).
- `pageCount`: The total number of pages in the document.
- `pageSize`: A `ContextPageSize` object with `width` and `height` of the current page.
Should return a single content element, a list of content elements, a string, or None.
"""

DynamicBackgroundCallable = Callable[
    [int, ContextPageSize], Union["AnyContent", list["AnyContent"], None]
]
"""
A callable that dynamically generates background content for each page.
It receives:
- `currentPage`: The current page number (1-based).
- `pageSize`: A `ContextPageSize` object with `width` and `height` of the current page.
Should return a single content element, a list of content elements, a string, or None for the background.
"""


class CustomTableLayout(BaseModel):
    """
    Defines a custom layout for tables, allowing dynamic control over line widths, colors, styles,
    cell padding, and fill colors.
    """

    hLineWidth: DynamicLayoutCallable | None = Field(
        default=None,
        description="Callable to determine horizontal line width. Receives `(i, node)`, returns line width. `i` is line index.",
    )
    vLineWidth: VerticalDynamicLayoutCallable | None = Field(
        default=None,
        description="Callable to determine vertical line width. Receives `(i, node)`, returns line width. `i` is line index.",
    )
    hLineColor: DynamicLayoutCallable | None = Field(
        default=None,
        description="Callable to determine horizontal line color. Receives `(i, node)`, returns color string.",
    )
    vLineColor: VerticalDynamicLayoutCallable | None = Field(
        default=None,
        description="Callable to determine vertical line color. Receives `(i, node)`, returns color string.",
    )
    hLineStyle: DynamicLayoutCallable | None = Field(
        default=None,
        description="Callable to determine horizontal line style (e.g., dash pattern). Receives `(i, node)`. ",
    )
    vLineStyle: VerticalDynamicLayoutCallable | None = Field(
        default=None,
        description="Callable to determine vertical line style. Receives `(i, node)`. ",
    )
    paddingLeft: DynamicLayoutCallable | None = Field(
        default=None,
        description="Callable to determine left padding of cells in a column. Receives `(i, node)`, `i` is column index.",
    )
    paddingRight: DynamicLayoutCallable | None = Field(
        default=None,
        description="Callable to determine right padding of cells in a column. Receives `(i, node)`, `i` is column index.",
    )
    paddingTop: DynamicCellLayoutCallable | None = Field(
        default=None,
        description="Callable to determine top padding of a cell. Receives `(i, node, j)`, `i` is row index, `j` is col index.",
    )
    paddingBottom: DynamicCellLayoutCallable | None = Field(
        default=None,
        description="Callable to determine bottom padding of a cell. Receives `(i, node, j)`, `i` is row index, `j` is col index.",
    )
    fillColor: DynamicCellLayoutCallable | None = Field(
        default=None,
        description="Callable to determine background fill color of a cell. Receives `(i, node, j)`, `i` is row index, `j` is col index.",
    )
    defaultBorder: bool | None = Field(
        default=None,
        description="If true, draws default borders for cells unless overridden by cell's `border` property. Default is true.",
    )


PredefinedTableLayout = Literal["noBorders", "headerLineOnly", "lightHorizontalLines"]
"""Standard predefined table layouts: 'noBorders', 'headerLineOnly', 'lightHorizontalLines'."""

TableLayout = str | PredefinedTableLayout | CustomTableLayout
"""
Represents a table layout.
Can be:
- A predefined layout name string (e.g., 'noBorders').
- A `CustomTableLayout` object for full control.
- A string referring to a custom layout defined in the `tableLayouts` dictionary at the document root (not directly modeled here, but a string value implies this).
"""


class ContentTable(ContentBase):
    """Represents a table with rows, columns, and an optional layout."""

    table: "Table" = Field(
        description="The `Table` object containing the body (rows and cells), column widths, row heights, and header definitions."
    )
    layout: TableLayout | None = Field(
        default=None,
        description="The layout to apply to the table. Can be a predefined string (e.g., 'lightHorizontalLines'), a custom layout object, or a string key for a layout defined in `documentDefinition.tableLayouts`.",
    )


class ContentAnchor(
    ContentBase
):  # In pdfmake, any element with an `id` can be an anchor. This specific type might be for creating a visible text that is also a target.
    """
    Represents a text element that can also serve as a named destination (anchor) if an `id` is provided.
    Primarily, link destinations are created by assigning an `id` to any content element.
    """

    text: str | int | list[str | int | ContentText] = Field(
        description="The visible text content of this element. If an `id` is set (from `ContentBase`), this element can be a link target."
    )


class ContentPageReference(ContentBase):
    """Displays the page number where a referenced element (identified by its `id`) appears."""

    pageReference: str = Field(
        description="The `id` of the content element whose page number is to be displayed."
    )
    text: str | int | ContentText | None = Field(
        default=None,
        description="Optional text to display alongside the page number. Can be a simple string or a styled `ContentText` object. The page number is typically inserted where a special placeholder might be used or appended/prepended.",
    )


class ContentTextReference(ContentBase):
    """Displays the text content of another element (identified by its `id`)."""

    textReference: str = Field(
        description="The `id` of the content element whose text content is to be displayed."
    )
    text: str | int | ContentText | None = Field(
        default=None,
        description="Optional text to display alongside the referenced text. Can be a simple string or a styled `ContentText` object.",
    )


class TableOfContent(BaseModel):  # Corresponds to 'toc' property in ContentToc
    """Defines the properties for a Table of Contents (TOC)."""

    title: "AnyContent | None" = Field(
        default=None,
        description="Optional title for the Table of Contents (e.g., a `ContentText` object).",
    )
    textMargin: Margins | None = Field(
        default=None, description="Margins for individual TOC entries."
    )
    textStyle: StyleReference | None = Field(
        default=None, description="Style to be applied to TOC entries (text part)."
    )
    id: str | None = Field(
        default=None,
        description="Optional `id` for the Table of Contents block itself, making it a linkable target.",
    )
    # numberStyle: StyleReference | None = Field(default=None, description="Style for the page numbers in the TOC.") # pdfmake supports this
    # style: StyleReference | None = Field(default=None, description="Overall style for the TOC block.") # pdfmake supports this


class ContentToc(ContentBase):
    """Generates a Table of Contents based on elements marked with `tocItem` or `headlineLevel`."""

    toc: TableOfContent = Field(
        description="The `TableOfContent` definition object specifying the appearance and behavior of the TOC."
    )


class ContentTocItem(
    ContentBase
):  # This is less common; usually tocItem on other elements is used.
    """
    Represents an explicit item to be included in the Table of Contents.
    More commonly, items are added to the TOC by setting the `tocItem` property on other content elements.
    """

    text: str | int | list[str | int | ContentText] = Field(
        description="The text of the TOC item as it should appear in the TOC."
    )
    # tocLink: str | None = Field(default=None, description="If this TOC item should link to a specific `id` different from its own implied target.") # Not standard pdfmake, but a thought.


class ContentQr(ContentBase):
    """Generates a QR code image."""

    qr: str = Field(description="The text content to encode in the QR code.")
    foreground: str | None = Field(
        default=None,
        description="Color of the QR code modules (dots). Default: 'black'.",
    )
    background: str | None = Field(
        default=None, description="Color of the QR code background. Default: 'white'."
    )
    version: int | None = Field(
        default=None,
        description="QR code version (1-40). Determines data capacity. Auto-selected if None.",
    )
    eccLevel: Literal["L", "M", "Q", "H"] | None = Field(
        default=None,
        description="Error correction capability level (Low, Medium, Quartile, High). Default: 'M'.",
    )
    fit: float | None = Field(
        default=None,
        description="Size (width and height) of the QR code in points. Default: 100.",
    )
    padding: float | None = Field(
        default=None,
        description="Padding around the QR code in modules (QR code 'pixels'). Default: 0.",
    )
    mode: Literal["numeric", "alphanumeric", "byte", "kanji"] | None = Field(
        default=None, description="Encoding mode. Auto-selected if None."
    )
    maskPattern: Literal[0, 1, 2, 3, 4, 5, 6, 7] | None = Field(
        default=None,
        description="Mask pattern for the QR code. Auto-selected if None (0-7).",
    )


PDFVersion = Literal["1.3", "1.4", "1.5", "1.6", "1.7", "1.7ext3"]
"""Specifies the PDF version for the output document (e.g., '1.7')."""


class Watermark(BaseModel):
    """Defines a watermark (text or image) to be displayed on pages, typically in the background."""

    text: str = Field(description="The text content of the watermark.")
    font: str | None = Field(
        default=None,
        description="Font for the watermark text. Must be defined in `fonts` dictionary.",
    )
    fontSize: float | None = Field(
        default=None, description="Font size for the watermark text in points."
    )
    color: str | None = Field(
        default=None, description="Color of the watermark text. Default: 'black'."
    )
    opacity: float | None = Field(
        default=None, description="Opacity of the watermark (0.0 to 1.0). Default: 0.5."
    )
    bold: bool | None = Field(
        default=None, description="Whether the watermark text is bold."
    )
    italics: bool | None = Field(
        default=None, description="Whether the watermark text is italic."
    )
    angle: float | None = Field(
        default=None,
        description="Rotation angle of the watermark text in degrees. Default: 0.",
    )
    # image: str | None = Field(default=None, description="Image key for an image watermark.") # pdfmake also supports image watermarks


class Pattern(BaseModel):
    """Defines a repeating pattern for backgrounds or fills, using vector graphics (canvas) or SVG."""

    boundingBox: list[float] = Field(
        description="The bounding box `[x1, y1, x2, y2]` of one instance of the pattern cell in points."
    )
    xStep: float = Field(
        description="Horizontal step size in points for repeating the pattern."
    )
    yStep: float = Field(
        description="Vertical step size in points for repeating the pattern."
    )
    canvas: list[CanvasElement] | None = Field(
        default=None, description="Canvas elements to draw one instance of the pattern."
    )
    svg: str | None = Field(
        default=None,
        description="SVG content string to use as one instance of the pattern.",
    )


PatternDictionary = dict[str, Pattern]
"""A dictionary mapping pattern names to Pattern objects, for use in `background` or `fillColor` properties."""


class ImageDefinition(BaseModel):
    """Defines an image by its URL, typically for remote images to be fetched by pdfmake if not provided as base64."""

    url: str = Field(
        description="URL of the image (e.g., 'https://example.com/image.png')."
    )
    # headers: dict[str, str] | None = Field(default=None, description="Optional HTTP headers for fetching the image.") # pdfmake supports this


ImageDictionary = dict[str, str | ImageDefinition]
"""
A dictionary mapping image names (keys) to image data.
Values can be:
- A base64 encoded image string (e.g., 'data:image/jpeg;base64,...').
- A URL string (if pdfmake is configured to fetch remote images).
- An `ImageDefinition` object (primarily for specifying URLs, potentially with headers).
"""


class Table(BaseModel):
    """Defines the structure and content of a table, including its body, column widths, row heights, and header behavior."""

    body: list[list["TableCell"]] = Field(
        description="A 2D array representing the table rows and cells. Each cell is `TableCell` content."
    )
    widths: list[Size] | None = Field(
        default=None,
        description="List of column widths. Can be fixed numbers (points), '*', or 'auto'. If undefined, columns are equally sized.",
    )
    heights: float | list[float | Literal["auto"]] | DynamicRowSizeCallable | None = (
        Field(
            default=None,
            description="List of row heights (points or 'auto'), or a callable `(rowIndex) => height` for dynamic row heights.",
        )
    )
    headerRows: int | None = Field(
        default=None,
        description="Number of rows from the beginning of `body` to repeat as a header on subsequent pages if the table spans multiple pages.",
    )
    keepWithHeaderRows: int | None = Field(
        default=None,
        description="Number of body rows (after headerRows) to keep with the header rows when a page break occurs within the table.",
    )
    layout: TableLayout | None = Field(
        default=None,
        description="Overrides the layout defined in `ContentTable.layout` specifically for this table's internal structure. Not commonly used here, `ContentTable.layout` is primary.",
    )


# Define basic content types directly - from __future__ import annotations makes this work
ContentTypes = Union[
    "ContentText",
    "ContentColumns",
    "ContentStack",
    "ContentOrderedList",
    "ContentUnorderedList",
    "ContentCanvas",
    "ContentImage",
    "ContentSvg",
    "ContentTable",
    "ContentPageReference",
    "ContentTextReference",
    "ContentToc",
    "ContentQr",
    str,
]

# Define AnyContent to include both basic types and lists of those types
AnyContent = Union[ContentTypes, list[ContentTypes]]
"""
A union of all possible content element types that can be part of the document body
or complex structures like columns, stacks, lists, etc.
Forward references (strings) are used here for each Pydantic model and should be
resolved by appropriate `Model.model_rebuild()` calls at the end of the module
for all involved models.
"""

# Now define TableCell type alias, using the now-defined AnyContent
TableCell = Union[
    AnyContent, dict[str, Any]
]  # dict[str, Any] is a fallback, ideally cells are specific content types.
"""
Represents the content of a table cell.
Can be:
- Any `AnyContent` type (e.g., a string, `ContentText`, `ContentImage`).
- A dictionary, which pdfmake often interprets as a `ContentText`-like object if it has a `text` key, or other content types if structured accordingly.
  It's generally recommended to use explicit Pydantic models for cell content for better type safety.
"""


class TDocumentDefinitions(BaseModel):
    """The root object for a pdfmake document definition, containing all content, styles, metadata, and document-level settings."""

    content: Union[AnyContent, list[AnyContent | str]] = Field(
        description="The main content of the document. Can be a single content element or an array of elements."
    )
    styles: StyleDictionary | None = Field(
        default=None,
        description="A dictionary of named styles that can be referenced by content elements.",
    )
    defaultStyle: Style | None = Field(
        default=None,
        description="The default style applied to all text elements unless overridden.",
    )
    pageSize: PageSize | None = Field(
        default=None,
        description="Page size of the document (e.g., 'A4', or a custom `{width, height}`). Default: 'A4'.",
    )
    pageOrientation: PageOrientation | None = Field(
        default=None,
        description="Page orientation ('portrait' or 'landscape'). Default: 'portrait'.",
    )
    pageMargins: Margins | None = Field(
        default=None,
        description="Margins for pages `[left, top, right, bottom]` or a single value. Default: `[40, 60, 40, 60]` (approx).",
    )
    header: Union[AnyContent, DynamicContentCallable, None] = Field(
        default=None,
        description="Content for the page header. Can be static content or a function `(currentPage, pageCount, pageSize) => content`.",
    )
    footer: Union[AnyContent, DynamicContentCallable, None] = Field(
        default=None,
        description="Content for the page footer. Can be static content or a function `(currentPage, pageCount, pageSize) => content`.",
    )
    background: Union[AnyContent, DynamicBackgroundCallable, None] = Field(
        default=None,
        description="Background content for all pages. Can be static or a function `(currentPage, pageSize) => content`.",
    )
    images: ImageDictionary | None = Field(
        default=None,
        description="A dictionary of images, where keys are names used in `ContentImage.image` and values are image data (base64 or URL).",
    )
    fonts: TFontDictionary | None = Field(
        default=None,
        description="A dictionary defining custom fonts and their font family types.",
    )
    patterns: PatternDictionary | None = Field(
        default=None,
        description="A dictionary of named patterns that can be used for backgrounds or fills.",
    )
    watermark: str | Watermark | None = Field(
        default=None,
        description="A watermark to be displayed on pages. Can be a simple string or a `Watermark` object for more options.",
    )
    info: TDocumentInformation | None = Field(
        default=None, description="Metadata for the PDF document (title, author, etc.)."
    )
    compress: bool = Field(
        default=True, description="Whether to compress the PDF content. Default: true."
    )
    userPassword: str | None = Field(
        default=None, description="Password required to open the PDF (user password)."
    )
    ownerPassword: str | None = Field(
        default=None,
        description="Password required to change permissions or the user password (owner password).",
    )
    permissions: dict[str, bool] | None = Field(
        default=None,
        description="Permissions for the PDF (e.g., `{ printing: 'highResolution', modifying: false }`).",
    )
    defaultFont: str | None = Field(
        default=None,
        description="Sets the default font for the document if not specified in defaultStyle. Overrides VFS fonts like Roboto.",
    )
    version: PDFVersion | None = Field(
        default=None, description="PDF version for the output document."
    )
    subset: PDFSubset | None = Field(
        default=None, description="Specifies a PDF subset standard (e.g., PDF/A)."
    )
    author: str | None = Field(
        default=None, description="Shortcut for `info.author`."
    )  # This is a common pdfmake pattern, though not in official docs for top level.
    creator: str = Field(
        default="pypdfmake",
        description="Shortcut for `info.creator`. Defaults to 'pypdfmake'.",
    )  # Same as above.
    model_config = {"extra": "allow"}


_all_pydantic_models_ = [
    cls
    for _, cls in locals().copy().items()
    if isinstance(cls, type) and issubclass(cls, BaseModel) and cls is not BaseModel
]

for model_cls in _all_pydantic_models_:
    if hasattr(model_cls, "model_rebuild"):
        model_cls.model_rebuild(force=True)
