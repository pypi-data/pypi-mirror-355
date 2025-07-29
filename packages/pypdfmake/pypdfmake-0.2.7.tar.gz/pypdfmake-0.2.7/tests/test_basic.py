from pypdfmake import TDocumentDefinitions
from tests.utils import load_expected_json


def test_basic_document_output():
    doc_definition = TDocumentDefinitions(
        content=[
            "First paragraph",
            "Another paragraph, this time a little bit longer to make sure, this line will be divided into at least two lines",
        ]
    )

    # Generate a Python dictionary from the TDocumentDefinitions object.
    # exclude_none=True omits fields that are None, simplifying comparison if expected_basic.json is minimal.
    generated_data_dict = doc_definition.model_dump(exclude_none=True)

    # Load the expected JSON data
    expected_data_dict = load_expected_json("expected_basic.json")

    # Extract the 'content' field from both generated and expected data for comparison.
    generated_content = generated_data_dict.get("content")
    expected_content = expected_data_dict.get("content")

    assert generated_content == expected_content
