from pypdfmake import (
    TDocumentDefinitions,
    ContentText,
    ContentStack,
    Style,
)  # Added ContentStack and Style
from tests.utils import load_expected_json


def test_margin_document_output():
    lorem_ipsum = "Lorem ipsum dolor sit amet, consectetur adipisicing elit. Malit profecta versatur nomine ocurreret multavit, officiis viveremus aeternum superstitio suspicor alia nostram, quando nostros congressus susceperant concederetur leguntur iam, vigiliae democritea tantopere causae, atilii plerumque ipsas potitur pertineant multis rem quaeri pro, legendum didicisse credere ex maluisset per videtis. Cur discordans praetereat aliae ruinae dirigentur orestem eodem, praetermittenda divinum. Collegisti, deteriora malint loquuntur officii cotidie finitas referri doleamus ambigua acute. Adhaesiones ratione beate arbitraretur detractis perdiscere, constituant hostis polyaeno. Diu concederetur."
    doc_definition = TDocumentDefinitions(
        content=[
            ContentStack(
                stack=[
                    "This header has both top and bottom margins defined",
                    ContentText(text="This is a subheader", style="subheader"),
                ],
                style="header",
            ),
            ContentText(
                text=[
                    "Margins have slightly different behavior than other layout properties. They are not inherited, unlike anything else. They're applied only to those nodes which explicitly ",
                    "set margin or style property.\n",
                ]
            ),
            ContentText(
                text="This paragraph (consisting of a single line) directly sets top and bottom margin to 20",
                margin=[0, 20],  # Using tuple for margin
            ),
            ContentStack(
                stack=[
                    ContentText(
                        text=[
                            "This line begins a stack of paragraphs. The whole stack uses a ",
                            ContentText(text="superMargin", italics=True),
                            " style (with margin and fontSize properties).",
                        ]
                    ),
                    ContentText(
                        text=[
                            "When you look at the",
                            ContentText(text=" document definition", italics=True),
                            ", you will notice that fontSize is inherited by all paragraphs inside the stack.",
                        ]
                    ),
                    "Margin however is only applied once (to the whole stack).",
                ],
                style="superMargin",
            ),
            ContentStack(
                stack=[
                    "I'm not sure yet if this is the desired behavior. I find it a better approach however. One thing to be considered in the future is an explicit layout property called inheritMargin which could opt-in the inheritance.\n\n",
                    ContentText(
                        fontSize=15,
                        text=[
                            "Currently margins for ",
                            ContentText(
                                text="inlines", margin=20
                            ),  # Margin on inline text, as per expected
                            " are ignored\n\n",
                        ],
                    ),
                    lorem_ipsum + "\n",
                    lorem_ipsum + "\n",
                    lorem_ipsum + "\n",
                    lorem_ipsum + "\n",
                    lorem_ipsum + "\n",
                    lorem_ipsum + "\n",
                    lorem_ipsum + "\n",
                ],
                margin=[0, 20, 0, 0],  # Using tuple for margin
                alignment="justify",
            ),
        ],
        styles={
            "header": Style(
                fontSize=18, bold=True, alignment="right", margin=[0, 190, 0, 80]
            ),
            "subheader": Style(fontSize=14),
            "superMargin": Style(margin=[20, 0, 40, 0], fontSize=15),
        },
        # pageMargins is not in expected_margin.json, so removing it or ensuring it matches if intended.
        # For now, let's stick to what's in expected_margin.json.
    )

    generated_data_dict = doc_definition.model_dump(exclude_none=True)
    expected_data_dict = load_expected_json("expected_margin.json")

    assert generated_data_dict.get("content") == expected_data_dict.get("content")
    assert generated_data_dict.get("styles") == expected_data_dict.get("styles")
    # If pageMargins were intended, an assert for it would go here.
