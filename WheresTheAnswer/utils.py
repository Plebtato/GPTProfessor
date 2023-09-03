import os

def get_doc_index_path(collection):
    return os.path.join("data", "doc_index", str(collection) + ".json")