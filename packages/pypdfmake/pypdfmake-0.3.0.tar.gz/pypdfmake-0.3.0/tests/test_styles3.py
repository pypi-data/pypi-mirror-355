from pypdfmake import TDocumentDefinitions, ContentText, Style
from .utils import load_expected_json


def test_styles3_document_output():
    lorem_ipsum_long = "Lorem ipsum dolor sit amet, consectetur adipisicing elit. Malit profecta versatur nomine ocurreret multavit, officiis viveremus aeternum superstitio suspicor alia nostram, quando nostros congressus susceperant concederetur leguntur iam, vigiliae democritea tantopere causae, atilii plerumque ipsas potitur pertineant multis rem quaeri pro, legendum didicisse credere ex maluisset per videtis. Cur discordans praetereat aliae ruinae dirigentur orestem eodem, praetermittenda divinum. Collegisti, deteriora malint loquuntur officii cotidie finitas referri doleamus ambigua acute. Adhaesiones ratione beate arbitraretur detractis perdiscere, constituant hostis polyaeno. Diu concederetur."

    doc_definition = TDocumentDefinitions(
        content=[
            ContentText(
                text="This paragraph uses header style and extends the alignment property",
                style="header",
                alignment="center",
            ),
            ContentText(
                text=[
                    "This paragraph uses header style and overrides bold value setting it back to false.\n",
                    "Header style in this example sets alignment to justify, so this paragraph should be rendered \n",
                    lorem_ipsum_long,
                ],
                style="header",
                bold=False,
            ),
        ],
        styles={
            "header": Style(fontSize=18, bold=True, alignment="justify"),
        },
        # defaultStyle is not in expected_styles3.json, so removing it.
    )

    generated_data_dict = doc_definition.model_dump(mode="json", exclude_none=True)
    expected_data_dict = load_expected_json("expected_styles3.json")

    assert generated_data_dict.get("content") == expected_data_dict.get("content")
    assert generated_data_dict.get("styles") == expected_data_dict.get("styles")
