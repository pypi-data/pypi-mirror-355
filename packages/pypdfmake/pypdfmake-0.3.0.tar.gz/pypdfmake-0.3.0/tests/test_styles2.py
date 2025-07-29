from pypdfmake import TDocumentDefinitions, ContentText, Style
from tests.utils import load_expected_json


def test_styles2_document_output():
    doc_definition = TDocumentDefinitions(
        content=[
            ContentText(
                text="This is a header (whole paragraph uses the same header style)\n\n",
                style="header",
            ),
            ContentText(
                text=[
                    "It is however possible to provide an array of texts ",
                    "to the paragraph (instead of a single string) and have ",
                    ContentText(text="a better ", fontSize=15, bold=True),
                    "control over it. \nEach inline can be ",
                    ContentText(text="styled ", fontSize=20),
                    ContentText(text="independently ", italics=True, fontSize=40),
                    "then.\n\n",
                ]
            ),
            ContentText(text="Mixing named styles and style-overrides", style="header"),
            ContentText(
                style="bigger",
                italics=False,  # Overriding italics from 'bigger' style
                text=[
                    "We can also mix named-styles and style-overrides at both paragraph and inline level. ",
                    'For example, this paragraph uses the "bigger" style, which changes fontSize to 15 and sets italics to true. ',
                    "Texts are not italics though. It's because we've overridden italics back to false at ",
                    "the paragraph level. \n\n",
                    "We can also change the style of a single inline. Let's use a named style called header: ",
                    ContentText(text="like here.\n", style="header"),
                    "It got bigger and bold.\n\n",
                    "OK, now we're going to mix named styles and style-overrides at the inline level. ",
                    "We'll use header style (it makes texts bigger and bold), but we'll override ",
                    "bold back to false: ",
                    ContentText(text="wow! it works!", style="header", bold=False),
                    "\n\nMake sure to take a look into the sources to understand what's going on here.",
                ],
            ),
        ],
        styles={
            "header": Style(fontSize=18, bold=True),
            "bigger": Style(fontSize=15, italics=True),
        },
    )

    generated_data_dict = doc_definition.model_dump(exclude_none=True)
    expected_data_dict = load_expected_json("expected_styles2.json")

    assert generated_data_dict.get("content") == expected_data_dict.get("content")
    assert generated_data_dict.get("styles") == expected_data_dict.get("styles")
