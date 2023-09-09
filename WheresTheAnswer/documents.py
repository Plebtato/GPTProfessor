import config
import utils
import json
import os
from copy import deepcopy
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from PyPDF2 import PdfReader
from docx import Document
import streamlit as st
from langchain.document_loaders import TextLoader
from langchain.document_loaders import GoogleDriveLoader
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.document_loaders import Docx2txtLoader
import tqdm
import datetime


def upload_file(file, collection):
    # Uploads a file to the db collection
    # TODO: Load multiple at once
    if file is not None:
        if file.type == "application/pdf":
            reader = PdfReader(file)
            input_docs = ""
            for page in reader.pages:
                input_docs += page.extract_text() + " "
            # TODO: OCR support

        elif file.type == "text/plain":
            input_docs = file.read().decode()

        elif file.type == "text/csv":
            input_docs = file.read().decode()

        elif (
            file.type
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            docx = Document(file)
            input_docs = ""
            for paragraph in docx.paragraphs:
                input_docs += paragraph.text + " "

        # TODO: PPT

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.character_splitter_chunk_size,
            chunk_overlap=config.character_splitter_chunk_overlap,
        )
        texts = text_splitter.split_text(input_docs)

        # TODO: Split very large documents to avoid rate limit

        doc_index_path = utils.get_doc_index_path(collection)
        embeddings = OpenAIEmbeddings(openai_api_key=config.openai_api_key)
        vectordb = Chroma(
            "db" + str(collection),
            persist_directory=config.db_path,
            embedding_function=embeddings,
        )

        if os.path.isfile(doc_index_path):
            with open(doc_index_path, "r") as openfile:
                json_obj = json.load(openfile)

            last_id = json_obj["last_id"]
            ids = [str(i) for i in range(last_id, last_id + len(texts))]
            metadata = []

            for text in texts:
                metadata.append({"source": file.name})

            vectordb.add_texts(texts, metadatas=metadata, ids=ids)

            saved_docs = json_obj["saved_docs"]
            saved_docs.append({"source": file.name, "ids": ids})
            dictionary = {"last_id": last_id + len(texts), "saved_docs": saved_docs}

            with open(doc_index_path, "w") as outfile:
                json.dump(dictionary, outfile)


def chunks(lst, n):
    # https://stackoverflow.com/a/312464/18903720
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def create_and_load_collection(docs, collection, delete_old=False):
    doc_index_path = utils.get_doc_index_path(collection)
    embeddings = OpenAIEmbeddings(openai_api_key=config.openai_api_key)
    vectordb = None
    time = datetime.datetime.now().isoformat()

    # remove old db if needed
    if delete_old:
        vectordb = Chroma(
            "db" + str(collection),
            persist_directory=config.db_path,
            embedding_function=embeddings,
        )
        vectordb.delete_collection()

        collection_dict = {"path": "", "last_id": 0, "saved_docs": []}
        with open(doc_index_path, "w") as outfile:
            json.dump(collection_dict, outfile)

    # Get available db ids
    with open(doc_index_path, "r") as openfile:
        json_obj = json.load(openfile)

    saved_docs = json_obj["saved_docs"]
    last_id = json_obj["last_id"]
    ids = [str(i) for i in range(last_id, last_id + len(docs))]

    # Split by chunks to avoid token limit
    doc_chunks = chunks(docs, config.embedding_api_chunk_limit)
    chunk_ids = chunks(ids, config.embedding_api_chunk_limit)

    # Load vector db
    for index, (chunk, chunk_id) in tqdm.tqdm(enumerate(zip(doc_chunks, chunk_ids))):
        if index == 0:
            vectordb = Chroma.from_documents(
                chunk,
                collection_name="db" + str(collection),
                persist_directory=config.db_path,
                embedding=embeddings,
                ids=chunk_id,
            )
        else:
            vectordb.add_documents(chunk, ids=chunk_id)

    # Create and load source list
    sources = []
    for doc in docs:
        if doc.metadata["source"] not in sources:
            sources.append(doc.metadata["source"])

    for source in sources:
        source_ids = []
        for index, (doc, doc_id) in enumerate(zip(docs, ids)):
            if doc.metadata["source"] == source:
                source_ids.append(doc_id)

        saved_docs.append({"source": source, "ids": source_ids, "last_updated": time})

    dictionary = {"last_id": last_id + len(docs), "saved_docs": saved_docs}
    with open(doc_index_path, "w") as outfile:
        json.dump(dictionary, outfile)


def write_path(path, collection):
    doc_index_path = utils.get_doc_index_path(collection)

    with open(doc_index_path, "r") as openfile:
        json_obj = json.load(openfile)

    json_obj["path"] = path

    with open(doc_index_path, "w") as outfile:
        json.dump(json_obj, outfile)


def get_path(collection):
    doc_index_path = utils.get_doc_index_path(collection)

    if os.path.isfile(doc_index_path):
        with open(doc_index_path, "r") as openfile:
            json_obj = json.load(openfile)
        return json_obj["path"]
    else:
        return ""


def should_update_source(source_path, collection):
    # checks if source is not in collection or has been modified
    doc_index_path = utils.get_doc_index_path(collection)

    if os.path.isfile(doc_index_path):
        with open(doc_index_path, "r") as openfile:
            json_obj = json.load(openfile)

        for doc in json_obj["saved_docs"]:
            if source_path == doc["source"]:
                if datetime.datetime.fromtimestamp(
                    os.path.getmtime(source_path)
                ) < datetime.datetime.fromisoformat(doc["last_updated"]):
                    return False
    return True


def delete_source_if_existing(source_path, collection):
    """
    Deletes the source if it is in the collection already
    """
    doc_index_path = utils.get_doc_index_path(collection)
    embeddings = OpenAIEmbeddings(openai_api_key=config.openai_api_key)
    vectordb = Chroma(
        "db" + str(collection),
        persist_directory=config.db_path,
        embedding_function=embeddings,
    )

    if os.path.isfile(doc_index_path):
        with open(doc_index_path, "r") as openfile:
            json_obj = json.load(openfile)

        for source in json_obj["saved_docs"]:
            if source_path == source["source"]:
                print("delete ids " + str(source["ids"]))
                vectordb._collection.delete(ids=source["ids"])
                print(vectordb._collection.count())
                copy_json = deepcopy(json_obj)
                copy_json["saved_docs"].remove(source)

                with open(doc_index_path, "w") as outfile:
                    json.dump(copy_json, outfile)


def clear_removed_sources(collection):
    """
    Clears sources that no longer exist in the directory
    """
    doc_index_path = utils.get_doc_index_path(collection)
    embeddings = OpenAIEmbeddings(openai_api_key=config.openai_api_key)
    vectordb = Chroma(
        "db" + str(collection),
        persist_directory=config.db_path,
        embedding_function=embeddings,
    )

    if os.path.isfile(doc_index_path):
        with open(doc_index_path, "r") as openfile:
            json_obj = json.load(openfile)
        for source in json_obj["saved_docs"]:
            if not os.path.isfile(source["source"]):
                print("delete ids " + str(source["ids"]))
                vectordb._collection.delete(ids=source["ids"])
                print(vectordb._collection.count())
                copy_json = deepcopy(json_obj)
                copy_json["saved_docs"].remove(source)

                with open(doc_index_path, "w") as outfile:
                    json.dump(copy_json, outfile)


def sync_folder(path, collection, reset=False):
    if os.path.isdir(path):
        clear_removed_sources(collection)
        split_docs = []

        for dirpath, dirs, files in os.walk(path):
            for filename in files:
                filename_with_path = os.path.join(dirpath, filename)
                if should_update_source(filename_with_path, collection):
                    if filename_with_path.endswith(".pdf"):
                        loader = PyPDFLoader(filename_with_path)
                    elif filename_with_path.endswith(".txt"):
                        loader = TextLoader(filename_with_path, encoding="utf8")
                    elif filename_with_path.endswith(".csv"):
                        loader = CSVLoader(filename_with_path, encoding="utf8")
                    elif filename_with_path.endswith(".docx"):
                        loader = Docx2txtLoader(filename_with_path)

                    if filename_with_path.endswith((".pdf", ".txt", ".csv", ".docx")):
                        delete_source_if_existing(filename_with_path, collection)
                        documents = loader.load()
                        text_splitter = RecursiveCharacterTextSplitter(
                            chunk_size=config.character_splitter_chunk_size,
                            chunk_overlap=config.character_splitter_chunk_overlap,
                        )
                        split_docs.extend(text_splitter.split_documents(documents))

        create_and_load_collection(split_docs, collection, reset)
        write_path(path, collection)


def sync_google_drive(folder_id, collection):
    loader = GoogleDriveLoader(
        folder_id=folder_id,
        recursive=True,
    )
    documents = loader.load()

    if documents:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.character_splitter_chunk_size,
            chunk_overlap=config.character_splitter_chunk_overlap,
        )
        split_docs = text_splitter.split_documents(documents)
        create_and_load_collection(split_docs, collection)
        write_path(folder_id, collection)


def sync_code_repo(path, collection, reset=False):
    if os.path.isdir(path):
        clear_removed_sources(collection)
        split_docs = []

        for dirpath, dirs, files in os.walk(path):
            for filename in files:
                filename_with_path = os.path.join(dirpath, filename)
                if should_update_source(filename_with_path, collection):
                    if filename_with_path.endswith((".cpp", ".hpp", ".h", ".md")):
                        delete_source_if_existing(filename_with_path, collection)
                        loader = TextLoader(filename_with_path, encoding="utf8")
                        documents = loader.load()
                        text_splitter = RecursiveCharacterTextSplitter(
                            chunk_size=config.character_splitter_chunk_size,
                            chunk_overlap=config.character_splitter_chunk_overlap,
                        )
                        split_docs.extend(text_splitter.split_documents(documents))

        create_and_load_collection(split_docs, collection, reset)
        write_path(path, collection)


def display_saved_files(collection, show_delete=True):
    # Renders the saved files as a list with control buttons

    doc_index_path = utils.get_doc_index_path(collection)

    if os.path.isfile(doc_index_path):
        embeddings = OpenAIEmbeddings(openai_api_key=config.openai_api_key)
        vectordb = Chroma(
            "db" + str(collection),
            persist_directory=config.db_path,
            embedding_function=embeddings,
        )

        with open(doc_index_path, "r") as openfile:
            json_obj = json.load(openfile)

        saved_docs = json_obj["saved_docs"]

        if not saved_docs:
            st.write("This collection is empty.")

        else:
            for index, source in enumerate(saved_docs):
                if show_delete:
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("######")
                        st.write(source["source"])

                    with col2:

                        def delete_source():
                            print("delete ids " + str(source["ids"]))
                            vectordb._collection.delete(ids=source["ids"])
                            print(vectordb._collection.count())
                            copy_json = deepcopy(json_obj)
                            for doc_data in saved_docs:
                                if doc_data["ids"] == source["ids"]:
                                    copy_json["saved_docs"].remove(doc_data)
                                    break
                            with open(doc_index_path, "w") as outfile:
                                json.dump(copy_json, outfile)

                        st.button(
                            "Delete",
                            key=str(collection) + "_" + str(index),
                            on_click=delete_source,
                            use_container_width=True,
                        )
                else:
                    st.markdown("######")
                    st.write(source["source"])
