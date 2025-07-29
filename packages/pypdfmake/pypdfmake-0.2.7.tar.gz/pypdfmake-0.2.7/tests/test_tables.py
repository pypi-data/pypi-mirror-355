from pypdfmake import (
    TDocumentDefinitions,
    ContentText,
    ContentTable,
    Table,
    Style,
    ContentStack,
    ContentUnorderedList,
    CustomTableLayout,
)
from .utils import load_expected_json


def test_tables_document_output():
    lorem_ipsum = "Lorem ipsum dolor sit amet"
    doc_definition = TDocumentDefinitions(
        content=[
            ContentText(text="Tables", style="header"),
            "Official documentation is in progress, this document is just a glimpse of what is possible with pdfmake and its layout engine.",
            ContentText(
                text="A simple table (no headers, no width specified, no spans, no styling)",
                style="subheader",
            ),
            "The following table has nothing more than a body array",
            ContentTable(
                style="tableExample",
                table=Table(
                    body=[
                        ["Column 1", "Column 2", "Column 3"],
                        ["One value goes here", "Another one here", "OK?"],
                    ]
                ),
            ),
            ContentText(text="A simple table with nested elements", style="subheader"),
            "It is of course possible to nest any other type of nodes available in pdfmake inside table cells",
            ContentTable(
                style="tableExample",
                table=Table(
                    body=[
                        ["Column 1", "Column 2", "Column 3"],
                        [
                            ContentStack(
                                stack=[
                                    "Let's try an unordered list",
                                    ContentUnorderedList(ul=["item 1", "item 2"]),
                                ]
                            ),
                            [
                                "or a nested table",
                                ContentTable(
                                    table=Table(
                                        body=[
                                            ["Col1", "Col2", "Col3"],
                                            ["1", "2", "3"],
                                            ["1", "2", "3"],
                                        ]
                                    )
                                ),
                            ],
                            ContentText(
                                text=[
                                    "Inlines can be ",
                                    ContentText(text="styled\n", italics=True),
                                    ContentText(
                                        text="easily as everywhere else",
                                        fontSize=10.0,
                                    ),
                                ]
                            ),
                        ],
                    ]
                ),
            ),
            ContentText(text="Defining column widths", style="subheader"),
            "Tables support the same width definitions as standard columns:",
            ContentUnorderedList(bold=True, ul=["auto", "star", "fixed value"]),
            ContentTable(
                style="tableExample",
                table=Table(
                    widths=[100, 200, "*"],
                    body=[
                        ["width=100", "star-sized", "width=200", "star-sized"],
                        [
                            "fixed-width cells have exactly the specified width",
                            ContentText(
                                text="nothing interesting here",
                                italics=True,
                                color="gray",
                            ),
                            ContentText(
                                text="nothing interesting here",
                                italics=True,
                                color="gray",
                            ),
                            ContentText(
                                text="nothing interesting here",
                                italics=True,
                                color="gray",
                            ),
                        ],
                    ],
                ),
            ),
            ContentTable(
                style="tableExample",
                table=Table(
                    widths=["*", "auto"],
                    body=[
                        [
                            "This is a star-sized column. The next column over, an auto-sized column, will wrap to accommodate all the text in this cell.",
                            "I am auto sized.",
                        ]
                    ],
                ),
            ),
            ContentTable(
                style="tableExample",
                table=Table(
                    widths=["*", "auto"],
                    body=[
                        [
                            "This is a star-sized column. The next column over, an auto-sized column, will not wrap to accommodate all the text in this cell, because it has been given the noWrap style.",
                            ContentText(text="I am auto sized.", noWrap=True),
                        ]
                    ],
                ),
            ),
            ContentText(text="Defining row heights", style="subheader"),
            ContentTable(
                style="tableExample",
                table=Table(
                    heights=[20, 50, 70],
                    body=[
                        ["row 1 with height 20", "column B"],
                        ["row 2 with height 50", "column B"],
                        ["row 3 with height 70", "column B"],
                    ],
                ),
            ),
            "With same height:",
            ContentTable(
                style="tableExample",
                table=Table(
                    heights=40.0,
                    body=[
                        ["row 1", "column B"],
                        ["row 2", "column B"],
                        ["row 3", "column B"],
                    ],
                ),
            ),
            "With height from function:",
            ContentTable(
                style="tableExample",
                table=Table(
                    body=[
                        ["row 1", "column B"],
                        ["row 2", "column B"],
                        ["row 3", "column B"],
                    ]
                ),
            ),
            ContentText(text="Column/row spans", pageBreak="before", style="subheader"),
            "Each cell-element can set a rowSpan or colSpan",
            ContentTable(
                style="tableExample",
                color="#444",
                table=Table(
                    widths=[200, "auto", "auto"],
                    headerRows=2,
                    body=[
                        [
                            ContentText(
                                text="Header with Colspan = 2",
                                style="tableHeader",
                                colSpan=2,
                                alignment="center",
                            ),
                            {},
                            ContentText(
                                text="Header 3",
                                style="tableHeader",
                                alignment="center",
                            ),
                        ],
                        [
                            ContentText(
                                text="Header 1",
                                style="tableHeader",
                                alignment="center",
                            ),
                            ContentText(
                                text="Header 2",
                                style="tableHeader",
                                alignment="center",
                            ),
                            ContentText(
                                text="Header 3",
                                style="tableHeader",
                                alignment="center",
                            ),
                        ],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        [
                            ContentText(
                                rowSpan=3,
                                text="rowSpan set to 3\nLorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor",
                            ),
                            "Sample value 2",
                            "Sample value 3",
                        ],
                        ["", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        [
                            "Sample value 1",
                            ContentText(
                                colSpan=2,
                                rowSpan=2,
                                text="Both:\nrowSpan and colSpan\ncan be defined at the same time",
                            ),
                            "",
                        ],
                        ["Sample value 1", "", ""],
                    ],
                ),
            ),
            ContentText(text="Headers", pageBreak="before", style="subheader"),
            "You can declare how many rows should be treated as a header. Headers are automatically repeated on the following pages",
            ContentText(
                text=[
                    "It is also possible to set keepWithHeaderRows to make sure there will be no page-break between the header and these rows. Take a look at the document-definition and play with it. If you set it to one, the following table will automatically start on the next page, since there's not enough space for the first row to be rendered here"
                ],
                color="gray",
                italics=True,
            ),
            ContentTable(
                style="tableExample",
                table=Table(
                    headerRows=1,
                    body=[
                        [
                            ContentText(text="Header 1", style="tableHeader"),
                            ContentText(text="Header 2", style="tableHeader"),
                            ContentText(text="Header 3", style="tableHeader"),
                        ],
                        [
                            lorem_ipsum,
                            lorem_ipsum,
                            lorem_ipsum,
                        ],
                    ],
                ),
            ),
            ContentText(text="Styling tables", style="subheader"),
            "You can provide a custom styler for the table. Currently it supports:",
            ContentUnorderedList(ul=["line widths", "line colors", "cell paddings"]),
            "with more options coming soon...\n\npdfmake currently has a few predefined styles (see them on the next page)",
            ContentText(
                text="noBorders:",
                fontSize=14,
                bold=True,
                pageBreak="before",
                margin=[0, 0, 0, 8],
            ),
            ContentTable(
                style="tableExample",
                table=Table(
                    headerRows=1,
                    body=[
                        [
                            ContentText(text="Header 1", style="tableHeader"),
                            ContentText(text="Header 2", style="tableHeader"),
                            ContentText(text="Header 3", style="tableHeader"),
                        ],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                    ],
                ),
                layout="noBorders",
            ),
            ContentText(
                text="headerLineOnly:",
                fontSize=14,
                bold=True,
                margin=[0, 20, 0, 8],
            ),
            ContentTable(
                style="tableExample",
                table=Table(
                    headerRows=1,
                    body=[
                        [
                            ContentText(text="Header 1", style="tableHeader"),
                            ContentText(text="Header 2", style="tableHeader"),
                            ContentText(text="Header 3", style="tableHeader"),
                        ],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                    ],
                ),
                layout="headerLineOnly",
            ),
            ContentText(
                text="lightHorizontalLines:",
                fontSize=14,
                bold=True,
                margin=[0, 20, 0, 8],
            ),
            ContentTable(
                style="tableExample",
                table=Table(
                    headerRows=1,
                    body=[
                        [
                            ContentText(text="Header 1", style="tableHeader"),
                            ContentText(text="Header 2", style="tableHeader"),
                            ContentText(text="Header 3", style="tableHeader"),
                        ],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                    ],
                ),
                layout="lightHorizontalLines",
            ),
            ContentText(
                text="but you can provide a custom styler as well",
                margin=[0, 20, 0, 8],
            ),
            ContentTable(
                style="tableExample",
                table=Table(
                    headerRows=1,
                    body=[
                        [
                            ContentText(text="Header 1", style="tableHeader"),
                            ContentText(text="Header 2", style="tableHeader"),
                            ContentText(text="Header 3", style="tableHeader"),
                        ],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                    ],
                ),
                layout=CustomTableLayout(),
            ),
            ContentText(text="zebra style", margin=[0, 20, 0, 8]),
            ContentTable(
                style="tableExample",
                table=Table(
                    body=[
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                    ]
                ),
                layout=CustomTableLayout(),
            ),
            ContentText(text="and can be used dash border", margin=[0, 20, 0, 8]),
            ContentTable(
                style="tableExample",
                table=Table(
                    headerRows=1,
                    body=[
                        [
                            ContentText(text="Header 1", style="tableHeader"),
                            ContentText(text="Header 2", style="tableHeader"),
                            ContentText(text="Header 3", style="tableHeader"),
                        ],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                        ["Sample value 1", "Sample value 2", "Sample value 3"],
                    ],
                ),
                layout=CustomTableLayout(),
            ),
            ContentText(
                text="Optional border",
                fontSize=14,
                bold=True,
                pageBreak="before",
                margin=[0, 0, 0, 8],
            ),
            "Each cell contains an optional border property: an array of 4 booleans for left border, top border, right border, bottom border.",
            ContentTable(
                style="tableExample",
                table=Table(
                    body=[
                        [
                            ContentText(
                                border=[False, True, False, False],
                                fillColor="#eeeeee",
                                text="border:\n[false, true, false, false]",
                            ),
                            ContentText(
                                border=[False, False, False, False],
                                fillColor="#dddddd",
                                text="border:\n[false, false, false, false]",
                            ),
                            ContentText(
                                border=[True, True, True, True],
                                fillColor="#eeeeee",
                                text="border:\n[true, true, true, true]",
                            ),
                        ],
                        [
                            ContentText(
                                rowSpan=3,
                                border=[True, True, True, True],
                                fillColor="#eeeeff",
                                text="rowSpan: 3\n\nborder:\n[true, true, true, true]",
                            ),
                            ContentText(fillColor="#eeeeee", text="border:\nundefined"),
                            ContentText(
                                border=[True, False, False, False],
                                fillColor="#dddddd",
                                text="border:\n[true, false, false, false]",
                            ),
                        ],
                        [
                            "",
                            ContentText(
                                colSpan=2,
                                border=[True, True, True, True],
                                fillColor="#eeffee",
                                text="colSpan: 2\n\nborder:\n[true, true, true, true]",
                            ),
                            "",
                        ],
                        [
                            "",
                            ContentText(fillColor="#eeeeee", text="border:\nundefined"),
                            ContentText(
                                border=[False, False, True, True],
                                fillColor="#dddddd",
                                text="border:\n[false, false, true, true]",
                            ),
                        ],
                    ]
                ),
                layout=CustomTableLayout(defaultBorder=False),
            ),
            "For every cell without a border property, whether it has all borders or not is determined by layout.defaultBorder, which is false in the table above and true (by default) in the table below.",
            ContentTable(
                style="tableExample",
                table=Table(
                    body=[
                        [
                            ContentText(
                                border=[False, False, False, False],
                                fillColor="#eeeeee",
                                text="border:\n[false, false, false, false]",
                            ),
                            ContentText(fillColor="#dddddd", text="border:\nundefined"),
                            ContentText(fillColor="#eeeeee", text="border:\nundefined"),
                        ],
                        [
                            ContentText(fillColor="#dddddd", text="border:\nundefined"),
                            ContentText(fillColor="#eeeeee", text="border:\nundefined"),
                            ContentText(
                                border=[True, True, False, False],
                                fillColor="#dddddd",
                                text="border:\n[true, true, false, false]",
                            ),
                        ],
                    ]
                ),
            ),
            "And some other examples with rowSpan/colSpan...",
            ContentTable(
                style="tableExample",
                table=Table(
                    body=[
                        ["", "column 1", "column 2", "column 3"],
                        [
                            "row 1",
                            ContentText(
                                rowSpan=3,
                                colSpan=3,
                                border=[True, True, True, True],
                                fillColor="#cccccc",
                                text="rowSpan: 3\ncolSpan: 3\n\nborder:\n[true, true, true, true]",
                            ),
                            "",
                            "",
                        ],
                        ["row 2", "", "", ""],
                        ["row 3", "", "", ""],
                    ]
                ),
                layout=CustomTableLayout(defaultBorder=False),
            ),
            ContentTable(
                style="tableExample",
                table=Table(
                    body=[
                        [
                            ContentText(
                                colSpan=3,
                                text="colSpan: 3\n\nborder:\n[false, false, false, false]",
                                fillColor="#eeeeee",
                                border=[False, False, False, False],
                            ),
                            "",
                            "",
                        ],
                        [
                            "border:\nundefined",
                            "border:\nundefined",
                            "border:\nundefined",
                        ],
                    ]
                ),
            ),
            ContentTable(
                style="tableExample",
                table=Table(
                    body=[
                        [
                            ContentText(
                                rowSpan=3,
                                text="rowSpan: 3\n\nborder:\n[false, false, false, false]",
                                fillColor="#eeeeee",
                                border=[False, False, False, False],
                            ),
                            "border:\nundefined",
                            "border:\nundefined",
                        ],
                        ["", "border:\nundefined", "border:\nundefined"],
                        ["", "border:\nundefined", "border:\nundefined"],
                    ]
                ),
            ),
        ],
        styles={
            "header": Style(fontSize=18, bold=True, margin=[0, 0, 0, 10]),
            "subheader": Style(fontSize=16, bold=True, margin=[0, 10, 0, 5]),
            "tableExample": Style(margin=[0, 5, 0, 15]),
            "tableHeader": Style(bold=True, fontSize=13, color="black"),
        },
        defaultStyle=Style(),
    )

    generated_data_dict = doc_definition.model_dump(mode="json", exclude_none=True)
    expected_data_dict = load_expected_json("expected_tables.json")

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
