from pypdfmake import TDocumentDefinitions, ContentImage
from tests.utils import load_expected_json


def test_images_document_output():
    # Placeholder for base64 data URLs
    sample_data_url = "data:image/jpeg;base64,/9j/4RC5RXhp"

    doc_definition = TDocumentDefinitions(
        content=[
            "pdfmake (since it's based on pdfkit) supports JPEG and PNG format",
            "If no width/height/fit is provided, image original size will be used",
            ContentImage(image="sampleImage.jpg"),
            "If you specify width, image will scale proportionally",
            ContentImage(image="sampleImage.jpg", width=150),
            "If you specify both width and height - image will be stretched",
            ContentImage(image="sampleImage.jpg", width=150, height=150),
            "You can also fit the image inside a rectangle",
            ContentImage(
                image="sampleImage.jpg", fit=(100.0, 100.0), pageBreak="after"
            ),
            "Images can be also provided in dataURL format...",
            ContentImage(image=sample_data_url, width=200.0),
            'or be declared in an "images" dictionary and referenced by name',
            ContentImage(image="building", width=200.0),
            "and opacity is supported:",
            ContentImage(image="sampleImage.jpg", width=150.0, opacity=0.5),
        ],
        images={
            "building": sample_data_url  # Using placeholder for the "building" image data
        },
    )

    generated_data_dict = doc_definition.model_dump(mode="json", exclude_none=True)
    expected_data_dict = load_expected_json("expected_images.json")

    # Compare relevant parts, like the content array structure and image properties
    assert generated_data_dict.get("content") == expected_data_dict.get("content")
    assert generated_data_dict.get("images") == expected_data_dict.get("images")
