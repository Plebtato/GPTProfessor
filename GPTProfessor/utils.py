import os

def get_doc_index_path(collection_id: int):
    return os.path.join("data", "doc_index", str(collection_id) + ".json")

def chunks(lst, n):
    # https://stackoverflow.com/a/312464/18903720
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def get_model(model):
    if model == "GPT-4":
        model_name = "gpt-4"
        max_tokens_limit = 6750
    elif model == "GPT-3.5":
        model_name = "gpt-3.5-turbo"
        max_tokens_limit = 3375
    elif model == "DaVinci":
        model_name = "text-davinci-003"
        max_tokens_limit = 3375
    return model_name, max_tokens_limit