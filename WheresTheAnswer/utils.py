import os

def get_doc_index_path(collection_id: int):
    return os.path.join("data", "doc_index", str(collection_id) + ".json")