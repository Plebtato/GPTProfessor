import os

def get_doc_index_path(collection_id: int):
    return os.path.join("data", "doc_index", str(collection_id) + ".json")

def chunks(lst, n):
    # https://stackoverflow.com/a/312464/18903720
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]