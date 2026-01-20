from bson import ObjectId

def serialize_ids_only(doc: dict) -> dict:
    if not doc:
        return None

    doc["id"] = str(doc.pop("_id"))

    for key, value in doc.items():
        if isinstance(value, ObjectId):
            doc[key] = str(value)

    return doc
