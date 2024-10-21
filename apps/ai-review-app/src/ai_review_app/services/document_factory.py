from ai_review_app.models.context import Document
from qdrant_client.http.models.models import Record

def convert_records_to_docs(records: list[Record]) -> list[Document]:
    return [convert_record_to_doc(record) for record in records]

def convert_record_to_doc(record : Record) -> Document:
    if not record.payload:
        raise Exception("no metadata...")
    if record.payload.get("type") == "section":
        headings = f" - {(' > ').join(record.payload['headings'])}" if record.payload['headings'] else ""
        doc = Document(
            id=str(record.id),
            # title=f"{record.payload['title']}",
            title=f"{record.payload['title']} {headings}",
            text=record.payload["text"] if record.payload is not None else "")
    elif record.payload.get("type") == "abstract":
        doc = Document(
            id=str(record.id),
            title=record.payload["title"][0],
            text=record.payload["abstract"][0] if record.payload is not None else "")
    else:
        #TODO eventually remove. Added to support the old dbs with broken spec for now
        title = record.payload.get("title", "")
        if isinstance(title, list):
            title = title[0]
        if title is None:
            title = ""
        abstract = record.payload.get("abstract", "")
        if isinstance(abstract, list):
            abstract = abstract[0]  
        if abstract is None:
            abstract = ""
        doc = Document(
            id=str(record.id),
            title=title,
            text=abstract)
    return doc