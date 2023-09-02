import time
import config
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

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_text(input_docs)

        # TODO: Split very large documents to avoid rate limit

        doc_index_path = os.path.join("data", "doc_index", str(collection) + ".json")
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

        else:
            last_id = 0
            ids = [str(i) for i in range(last_id, last_id + len(texts))]
            metadata = []

            for text in texts:
                metadata.append({"source": file.name})

            vectordb.add_texts(texts, metadatas=metadata, ids=ids)
            print("Embedding query done")

            dictionary = {
                "last_id": last_id + len(texts),
                "saved_docs": [{"source": file.name, "ids": ids}],
            }

            with open(doc_index_path, "w") as outfile:
                json.dump(dictionary, outfile)


def chunks(lst, n):
    # https://stackoverflow.com/a/312464/18903720
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def create_and_load_collection(docs, collection, delete_old = True):
    doc_chunks = chunks(docs, 50) # adjust based on average character count per line
    embeddings = OpenAIEmbeddings(openai_api_key=config.openai_api_key)
    vectordb = None
    if delete_old:
        vectordb = Chroma(
            "db" + str(collection),
            persist_directory=config.db_path,
            embedding_function=embeddings,
        )
        vectordb.delete_collection()

    for (index, chunk) in tqdm.tqdm(enumerate(doc_chunks)):
        if index == 0:
            vectordb = Chroma.from_documents(
                chunk,
                collection_name="db" + str(collection),
                persist_directory=config.db_path,
                embedding=embeddings,
            )
        else:
            vectordb.add_documents(chunk)


def write_path(path, collection):
    doc_index_path = os.path.join("data", "doc_index", str(collection) + ".json")
    collection_dict = {"path": path}

    with open(doc_index_path, "w") as outfile:
        json.dump(collection_dict, outfile)


def get_path(collection):
    doc_index_path = os.path.join("data", "doc_index", str(collection) + ".json")
    
    if os.path.isfile(doc_index_path):
        with open(doc_index_path, "r") as openfile:
            json_obj = json.load(openfile)
        return json_obj["path"]
    else:
        return ""


def sync_folder(path, collection):
    if os.path.isdir(path):
        split_docs = []
        
        for dirpath, dirs, files in os.walk(path): 
            for filename in files:
                filename_with_path = os.path.join(dirpath, filename)
                if filename_with_path.endswith(".pdf"):
                    loader = PyPDFLoader(filename_with_path)
                elif filename_with_path.endswith(".txt"):
                    loader = TextLoader(filename_with_path, encoding="utf8")
                elif filename_with_path.endswith(".csv"):
                    loader = CSVLoader(filename_with_path, encoding="utf8")
                elif filename_with_path.endswith(".docx"):
                    loader = Docx2txtLoader(filename_with_path)

                if filename_with_path.endswith((".pdf", ".txt", ".csv", ".docx")):
                    documents = loader.load()
                    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
                    split_docs.extend(text_splitter.split_documents(documents))
        
        if split_docs:     
            create_and_load_collection(split_docs, collection)
            write_path(path, collection)


def sync_google_drive(folder_id, collection):
    loader = GoogleDriveLoader(
        folder_id=folder_id,
        recursive=True,
    )   
    documents = loader.load()

    if documents:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        split_docs = text_splitter.split_documents(documents)
        create_and_load_collection(split_docs, collection)
        write_path(folder_id, collection)


def sync_code_repo(path, collection):
    if os.path.isdir(path):
        split_docs = []
        
        for dirpath, dirs, files in os.walk(path): 
            for filename in files:
                filename_with_path = os.path.join(dirpath, filename)
                if filename_with_path.endswith((".cpp", ".hpp", ".h", ".md")):
                    loader = TextLoader(filename_with_path, encoding="utf8")
                    documents = loader.load()
                    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
                    split_docs.extend(text_splitter.split_documents(documents))
        
        if split_docs:   
            create_and_load_collection(split_docs, collection)
            write_path(path, collection)


def display_saved_files(collection):
    # Renders the saved files as a list with control buttons

    doc_index_path = os.path.join("data", "doc_index", str(collection) + ".json")

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
            for index, doc in enumerate(saved_docs):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("######")
                    st.write(doc["source"])

                with col2:

                    def delete_doc():
                        print("delete ids " + str(doc["ids"]))
                        vectordb._collection.delete(ids=doc["ids"])
                        print(vectordb._collection.count())
                        copy_json = deepcopy(json_obj)
                        for x in saved_docs:
                            if x["ids"] == doc["ids"]:
                                copy_json["saved_docs"].remove(x)
                                break
                        with open(doc_index_path, "w") as outfile:
                            json.dump(copy_json, outfile)

                    st.button(
                        "Delete",
                        key=str(collection) + "_" + str(index),
                        on_click=delete_doc,
                        use_container_width=True,
                    )