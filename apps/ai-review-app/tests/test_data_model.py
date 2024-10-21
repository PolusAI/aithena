from ai_review_app.models.context import DocType, Document
from polus.aithena.common.logger import get_logger

logger = get_logger(__file__)


def test_create_document():
    doc = Document(id="doc1", text="content of doc1", type=DocType.DOCUMENT)
    print(doc)

def test_create_summary():
    doc1 = Document(id="doc1", text="content of doc1", type=DocType.DOCUMENT)
    doc2 = Document(id="doc2", text="content of doc2", type=DocType.DOCUMENT)
    sum1 = Document(id="sum1", text="summary of doc1 and doc2", type=DocType.SUMMARY, derived_from=[doc1, doc2])
    print(sum1)