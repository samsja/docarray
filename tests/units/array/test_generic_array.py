from docarray import DocumentArray, Document
from docarray.document import AnyDocument


def test_generic_init():
    class Text(Document):
        text: str

    da = DocumentArray[Text]([])
    da.document_type == Text

    assert isinstance(da, DocumentArray)


def test_normal_access_init():
    da = DocumentArray([])
    da.document_type == AnyDocument

    assert isinstance(da, DocumentArray)
