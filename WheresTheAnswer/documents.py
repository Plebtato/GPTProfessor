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


def upload_file(file, collection):
    # Uploads a file to the db collection

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
            print("Embedding query done")

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

        for index, doc in enumerate(saved_docs):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("######")
                st.text(doc["source"])

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
