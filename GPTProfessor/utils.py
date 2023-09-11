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
        token_limit_before_response = 6750
        token_limit_max = 8192
    elif model == "GPT-3.5":
        model_name = "gpt-3.5-turbo"
        token_limit_before_response = 3375
        token_limit_max = 4097
    elif model == "DaVinci":
        model_name = "text-davinci-003"
        token_limit_before_response = 3375
        token_limit_max = 4097
    return model_name, token_limit_before_response, token_limit_max