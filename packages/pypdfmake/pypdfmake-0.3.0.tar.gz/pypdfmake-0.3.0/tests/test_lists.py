from pypdfmake import (
    ContentText,
    TDocumentDefinitions,
    ContentUnorderedList,
    ContentOrderedList,
    ContentColumns,
    OrderedListElement,
    ContentStack,
    Style,
    UnorderedListElement,
)
from tests.utils import load_expected_json

from rich import traceback

traceback.install()


def test_lists_document_output():
    lorem_ipsum = "Lorem ipsum dolor"

    # Load the expected JSON data
    expected_data_dict = load_expected_json("expected_lists.json")

    # First build the content list to allow using raw dictionaries
    doc_definition = TDocumentDefinitions(
        content=[
            #
            # Basic unordered list
            ContentText(text="Unordered list", style="header"),
            ContentUnorderedList(ul=["item 1", "item 2", "item 3"]),
            #
            # Unordered list with longer lines
            ContentText(text="\n\nUnordered list with longer lines", style="header"),
            ContentUnorderedList(ul=["item 1", lorem_ipsum, "item 3"]),
            #
            # Basic ordered list
            ContentText(text="\n\nOrdered list", style="header"),
            ContentOrderedList(ol=["item 1", "item 2", "item 3"]),
            #
            # Ordered list with longer lines
            ContentText(text="\n\nOrdered list with longer lines", style="header"),
            ContentOrderedList(ol=["item 1", lorem_ipsum, "item 3"]),
            #
            # Descending ordered list
            ContentText(text="\n\nOrdered list should be descending", style="header"),
            ContentOrderedList(reversed=True, ol=["item 1", "item 2", "item 3"]),
            #
            # Ordered list with start value
            ContentText(text="\n\nOrdered list with start value", style="header"),
            ContentOrderedList(start=50, ol=["item 1", "item 2", "item 3"]),
            #
            # Ordered list with own values
            ContentText(text="\n\nOrdered list with own values", style="header"),
            ContentOrderedList(
                ol=[
                    OrderedListElement(text="item 1", counter=10),
                    OrderedListElement(text="item 2", counter=20),
                    OrderedListElement(text="item 3", counter=30),
                    OrderedListElement(text="item 4 without own value", counter=None),
                ]
            ),
            # Nested lists (ordered)
            ContentText(text="\n\nNested lists (ordered)", style="header"),
            ContentOrderedList(
                ol=[
                    "item 1",
                    [
                        lorem_ipsum,
                        ContentOrderedList(
                            ol=[
                                "subitem 1",
                                "subitem 2",
                                "subitem 3 - " + lorem_ipsum,
                                "subitem 3 - " + lorem_ipsum,
                                "subitem 3 - " + lorem_ipsum,
                                ContentText(
                                    text=[
                                        "subitem 3 - " + lorem_ipsum,
                                        "subitem 3 - " + lorem_ipsum,
                                        "subitem 3 - " + lorem_ipsum,
                                        "subitem 3 - " + lorem_ipsum,
                                        "subitem 3 - " + lorem_ipsum,
                                        "subitem 3 - " + lorem_ipsum,
                                        "subitem 3 - " + lorem_ipsum,
                                        "subitem 3 - " + lorem_ipsum,
                                    ]
                                ),
                                "subitem 3 - " + lorem_ipsum,
                                "subitem 3 - " + lorem_ipsum,
                                "subitem 3 - " + lorem_ipsum,
                                "subitem 3 - " + lorem_ipsum,
                                "subitem 4",
                                "subitem 5",
                            ]
                        ),
                    ],
                    "item 3\nsecond line of item3",
                ]
            ),
            # Nested lists (unordered)
            ContentText(text="\n\nNested lists (unordered)", style="header"),
            ContentOrderedList(
                ol=[
                    "item 1",
                    lorem_ipsum,
                    ContentUnorderedList(
                        ul=[
                            "subitem 1",
                            "subitem 2",
                            "subitem 3 - " + lorem_ipsum,
                            "subitem 3 - " + lorem_ipsum,
                            "subitem 3 - " + lorem_ipsum,
                            ContentText(
                                text=[
                                    "subitem 3 - " + lorem_ipsum,
                                    "subitem 3 - " + lorem_ipsum,
                                    "subitem 3 - " + lorem_ipsum,
                                    "subitem 3 - " + lorem_ipsum,
                                    "subitem 3 - " + lorem_ipsum,
                                    "subitem 3 - " + lorem_ipsum,
                                    "subitem 3 - " + lorem_ipsum,
                                    "subitem 3 - " + lorem_ipsum,
                                ]
                            ),
                            "subitem 3 - " + lorem_ipsum,
                            "subitem 3 - " + lorem_ipsum,
                            "subitem 3 - " + lorem_ipsum,
                            "subitem 3 - " + lorem_ipsum,
                            "subitem 4",
                            "subitem 5",
                        ]
                    ),
                    "item 3\nsecond line of item3",
                ]
            ),
            # Unordered lists inside columns
            ContentText(text="\n\nUnordered lists inside columns", style="header"),
            ContentColumns(
                columns=[
                    ContentUnorderedList(ul=["item 1", lorem_ipsum]),
                    ContentUnorderedList(ul=["item 1", lorem_ipsum]),
                ]
            ),
            # Ordered lists inside columns
            ContentText(text="\n\nOrdered lists inside columns", style="header"),
            ContentColumns(
                columns=[
                    ContentOrderedList(ol=["item 1", lorem_ipsum]),
                    ContentOrderedList(ol=["item 1", lorem_ipsum]),
                ]
            ),
            # Nested lists with columns
            ContentText(text="\n\nNested lists width columns", style="header"),
            ContentUnorderedList(
                ul=[
                    "item 1",
                    lorem_ipsum,
                    ContentOrderedList(
                        ol=[
                            [
                                ContentColumns(
                                    columns=[
                                        "column 1",
                                        ContentStack(
                                            stack=[
                                                "column 2",
                                                ContentUnorderedList(
                                                    ul=[
                                                        "item 1",
                                                        "item 2",
                                                        ContentUnorderedList(
                                                            ul=["item", "item", "item"]
                                                        ),
                                                        "item 4",
                                                    ]
                                                ),
                                            ]
                                        ),
                                        "column 3",
                                        "column 4",
                                    ]
                                ),
                                "subitem 1 in a vertical container",
                                "subitem 2 in a vertical container",
                            ],
                            "subitem 2",
                            "subitem 3 - " + lorem_ipsum,
                            "subitem 3 - " + lorem_ipsum,
                            "subitem 3 - " + lorem_ipsum,
                            ContentText(
                                text=[
                                    "subitem 3 - " + lorem_ipsum,
                                    "subitem 3 - " + lorem_ipsum,
                                    "subitem 3 - " + lorem_ipsum,
                                    "subitem 3 - " + lorem_ipsum,
                                    "subitem 3 - " + lorem_ipsum,
                                    "subitem 3 - " + lorem_ipsum,
                                    "subitem 3 - " + lorem_ipsum,
                                    "subitem 3 - " + lorem_ipsum,
                                ]
                            ),
                            "subitem 3 - " + lorem_ipsum,
                            "subitem 3 - " + lorem_ipsum,
                            "subitem 3 - " + lorem_ipsum,
                            "subitem 3 - " + lorem_ipsum,
                            "subitem 4",
                            "subitem 5",
                        ]
                    ),
                    "item 3\nsecond line of item3",
                ]
            ),
            # Unordered list with square marker type
            ContentText(
                text="\n\nUnordered list with square marker type", style="header"
            ),
            ContentUnorderedList(type="square", ul=["item 1", "item 2", "item 3"]),
            # Unordered list with circle marker type
            ContentText(
                text="\n\nUnordered list with circle marker type", style="header"
            ),
            ContentUnorderedList(type="circle", ul=["item 1", "item 2", "item 3"]),
            # Colored unordered list
            ContentText(text="\n\nColored unordered list", style="header"),
            ContentUnorderedList(color="blue", ul=["item 1", "item 2", "item 3"]),
            # Colored unordered list with own marker color
            ContentText(
                text="\n\nColored unordered list with own marker color", style="header"
            ),
            ContentUnorderedList(
                color="blue", markerColor="red", ul=["item 1", "item 2", "item 3"]
            ),
            # Colored ordered list
            ContentText(text="\n\nColored ordered list", style="header"),
            ContentOrderedList(color="blue", ol=["item 1", "item 2", "item 3"]),
            # Colored ordered list with own marker color
            ContentText(
                text="\n\nColored ordered list with own marker color", style="header"
            ),
            ContentOrderedList(
                color="blue", markerColor="red", ol=["item 1", "item 2", "item 3"]
            ),
            # Ordered list - type: lower-alpha
            ContentText(text="\n\nOrdered list - type: lower-alpha", style="header"),
            ContentOrderedList(type="lower-alpha", ol=["item 1", "item 2", "item 3"]),
            # Ordered list - type: upper-alpha
            ContentText(text="\n\nOrdered list - type: upper-alpha", style="header"),
            ContentOrderedList(type="upper-alpha", ol=["item 1", "item 2", "item 3"]),
            # Ordered list - type: upper-roman
            ContentText(text="\n\nOrdered list - type: upper-roman", style="header"),
            ContentOrderedList(
                type="upper-roman",
                ol=["item 1", "item 2", "item 3", "item 4", "item 5"],
            ),
            # Ordered list - type: lower-roman
            ContentText(text="\n\nOrdered list - type: lower-roman", style="header"),
            ContentOrderedList(
                type="lower-roman",
                ol=["item 1", "item 2", "item 3", "item 4", "item 5"],
            ),
            # Ordered list - type: none
            ContentText(text="\n\nOrdered list - type: none", style="header"),
            ContentOrderedList(type="none", ol=["item 1", "item 2", "item 3"]),
            # Unordered list - type: none
            ContentText(text="\n\nUnordered list - type: none", style="header"),
            ContentUnorderedList(type="none", ul=["item 1", "item 2", "item 3"]),
            # Ordered list with own separator
            ContentText(text="\n\nOrdered list with own separator", style="header"),
            ContentOrderedList(separator=")", ol=["item 1", "item 2", "item 3"]),
            # Ordered list with own complex separator
            ContentText(
                text="\n\nOrdered list with own complex separator", style="header"
            ),
            ContentOrderedList(
                separator=(["(", ")"]), ol=["item 1", "item 2", "item 3"]
            ),
            ContentText(text="\n\nOrdered list with own items type", style="header"),
            ContentOrderedList(
                ol=[
                    "item 1",
                    OrderedListElement(text="item 2", type="none"),
                    OrderedListElement(text="item 3", type="upper-roman"),
                ],
            ),
            ContentText(text="\n\nUnordered list with own items type", style="header"),
            ContentUnorderedList(
                ul=[
                    "item 1",
                    UnorderedListElement(text="item 2", type="none"),
                    UnorderedListElement(text="item 3", type="circle"),
                ],
            ),
        ],
        styles={
            "header": Style(fontSize=15, bold=True),
        },
        defaultStyle=Style(fontSize=12),
    )

    # Generate a Python dictionary from the TDocumentDefinitions object.
    # exclude_none=True omits fields that are None, simplifying comparison.
    # by_alias=True to handle field aliases correctly
    generated_data_dict = doc_definition.model_dump(exclude_none=True, by_alias=True)

    # Compare the relevant fields
    assert generated_data_dict.get("content") == expected_data_dict.get("content", [])
    assert generated_data_dict.get("styles") == expected_data_dict.get("styles", {})
    assert generated_data_dict.get("defaultStyle") == expected_data_dict.get(
        "defaultStyle", {}
    )
