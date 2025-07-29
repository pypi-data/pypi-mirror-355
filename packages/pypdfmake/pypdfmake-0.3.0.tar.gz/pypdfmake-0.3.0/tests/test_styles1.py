from pypdfmake import TDocumentDefinitions, ContentText, Style
from tests.utils import load_expected_json


def test_styles1_document_output():
    lorem_ipsum_short = "Lorem ipsum dolor sit amet, consectetur adipisicing elit. Confectum ponit legam, perferendis nomine miserum, animi. Moveat nesciunt triari naturam.\n\n"
    lorem_ipsum_long = "Lorem ipsum dolor sit amet, consectetur adipisicing elit. Confectum ponit legam, perferendis nomine miserum, animi. Moveat nesciunt triari naturam posset, eveniunt specie deorsus efficiat sermone instituendarum fuisse veniat, eademque mutat debeo. Delectet plerique protervi diogenem dixerit logikh levius probabo adipiscuntur afficitur, factis magistra inprobitatem aliquo andriam obiecta, religionis, imitarentur studiis quam, clamat intereant vulgo admonitionem operis iudex stabilitas vacillare scriptum nixam, reperiri inveniri maestitiam istius eaque dissentias idcirco gravis, refert suscipiet recte sapiens oportet ipsam terentianus, perpauca sedatio aliena video."

    doc_definition = TDocumentDefinitions(
        content=[
            ContentText(text="This is a header, using header style", style="header"),
            lorem_ipsum_short,
            ContentText(text="Subheader 1 - using subheader style", style="subheader"),
            lorem_ipsum_long,
            lorem_ipsum_long,  # Repeated as per expected output
            lorem_ipsum_long + "\n\n",  # Repeated with newlines
            ContentText(text="Subheader 2 - using subheader style", style="subheader"),
            lorem_ipsum_long,
            lorem_ipsum_long + "\n\n",
            ContentText(
                text="It is possible to apply multiple styles, by passing an array. This paragraph uses two styles: quote and small. When multiple styles are provided, they are evaluated in the specified order which is important in case they define the same properties",
                style=["quote", "small"],
            ),
        ],
        styles={
            "header": Style(fontSize=18, bold=True),
            "subheader": Style(fontSize=15, bold=True),
            "quote": Style(italics=True),
            "small": Style(fontSize=8),
        },
    )

    generated_data_dict = doc_definition.model_dump(exclude_none=True)
    expected_data_dict = load_expected_json("expected_styles1.json")

    assert generated_data_dict.get("content") == expected_data_dict.get("content")
    assert generated_data_dict.get("styles") == expected_data_dict.get("styles")
