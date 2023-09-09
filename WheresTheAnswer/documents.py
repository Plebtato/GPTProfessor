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
import manage_collections
import tqdm
import datetime


class DocumentCollection:
    def __init__(self, collection_id) -> None:
        for collection in manage_collections.get_collections():
            if collection["id"] == collection_id:
                collection_title = collection["name"]
                collection_type = collection["type"]
                break

        if collection_title == None or collection_title == None:
            raise ValueError("Cannot find id in collection list")

        self.id = collection_id
        self.title = collection_title
        self.type = collection_type
        self.doc_index_path = utils.get_doc_index_path(collection_id)
        self.embeddings = OpenAIEmbeddings(openai_api_key=config.openai_api_key)
        self.vector_db = Chroma(
            "db" + str(collection_id),
            persist_directory=config.db_path,
            embedding_function=self.embeddings,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.character_splitter_chunk_size,
            chunk_overlap=config.character_splitter_chunk_overlap,
        )

    def upload_file(self, file):
        """
        Uploads a file to the db collection for manual collection type
        Needs to be separate as Langchain loaders are not compatible with Streamlit file input
        """
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

            # TODO: PPT support

            texts = self.text_splitter.split_text(input_docs)

            with open(self.doc_index_path, "r") as openfile:
                json_obj = json.load(openfile)

            last_id = json_obj["last_id"]
            ids = [str(i) for i in range(last_id, last_id + len(texts))]
            metadata = []

            for text in texts:
                metadata.append({"source": file.name})

            text_chunks = utils.chunks(texts, config.embedding_api_chunk_limit)
            chunk_ids = utils.chunks(ids, config.embedding_api_chunk_limit)
            chunk_metadatas = utils.chunks(metadata, config.embedding_api_chunk_limit)

            # Load vector db
            for index, (chunk, chunk_id, chunk_metadata) in tqdm.tqdm(
                enumerate(zip(text_chunks, chunk_ids, chunk_metadatas))
            ):
                self.vector_db.add_texts(chunk, metadatas=chunk_metadata, ids=chunk_id)

            saved_docs = json_obj["saved_docs"]
            saved_docs.append({"source": file.name, "ids": ids})
            dictionary = {"last_id": last_id + len(texts), "saved_docs": saved_docs}

            with open(self.doc_index_path, "w") as outfile:
                json.dump(dictionary, outfile)

    def create_and_load_collection(self, docs, reset=False):
        """
        Loads files into a collection based on path or folder id
        """
        time = datetime.datetime.now().isoformat()

        # reset db if needed
        if reset:
            self.vector_db.delete_collection()

            collection_dict = {"path": "", "last_id": 0, "saved_docs": []}
            with open(self.doc_index_path, "w") as outfile:
                json.dump(collection_dict, outfile)

        # Get available db ids
        with open(self.doc_index_path, "r") as openfile:
            json_obj = json.load(openfile)

        saved_docs = json_obj["saved_docs"]
        last_id = json_obj["last_id"]
        ids = [str(i) for i in range(last_id, last_id + len(docs))]

        # Split by chunks to avoid token limit
        doc_chunks = utils.chunks(docs, config.embedding_api_chunk_limit)
        chunk_ids = utils.chunks(ids, config.embedding_api_chunk_limit)

        # Load vector db
        for index, (chunk, chunk_id) in tqdm.tqdm(
            enumerate(zip(doc_chunks, chunk_ids))
        ):
            if index == 0:
                self.vector_db = Chroma.from_documents(
                    chunk,
                    collection_name="db" + str(self.id),
                    persist_directory=config.db_path,
                    embedding=self.embeddings,
                    ids=chunk_id,
                )
            else:
                self.vector_db.add_documents(chunk, ids=chunk_id)

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

            saved_docs.append(
                {"source": source, "ids": source_ids, "last_updated": time}
            )

        dictionary = {"last_id": last_id + len(docs), "saved_docs": saved_docs}
        with open(self.doc_index_path, "w") as outfile:
            json.dump(dictionary, outfile)

    def update_path(self, path):
        """
        Updates the path in the doc index
        """
        with open(self.doc_index_path, "r") as openfile:
            json_obj = json.load(openfile)

        json_obj["path"] = path

        with open(self.doc_index_path, "w") as outfile:
            json.dump(json_obj, outfile)

    # use attribute instead
    def get_path(self):
        with open(self.doc_index_path, "r") as openfile:
            json_obj = json.load(openfile)
        return json_obj["path"]

    def should_update_source(self, source_path):
        """
        Checks if source is not in collection or has been modified
        """
        with open(self.doc_index_path, "r") as openfile:
            json_obj = json.load(openfile)

        for doc in json_obj["saved_docs"]:
            if source_path == doc["source"]:
                if datetime.datetime.fromtimestamp(
                    os.path.getmtime(source_path)
                ) < datetime.datetime.fromisoformat(doc["last_updated"]):
                    return False
        return True

    def delete_source_if_existing(self, source_path):
        """
        Deletes the source if it is in the collection already
        """
        with open(self.doc_index_path, "r") as openfile:
            json_obj = json.load(openfile)

        for source in json_obj["saved_docs"]:
            if source_path == source["source"]:
                print("delete ids " + str(source["ids"]))
                self.vector_db._collection.delete(ids=source["ids"])
                print(self.vector_db._collection.count())
                copy_json = deepcopy(json_obj)
                copy_json["saved_docs"].remove(source)

                with open(self.doc_index_path, "w") as outfile:
                    json.dump(copy_json, outfile)

    def clear_removed_sources(self):
        """
        Clears sources that no longer exist in the directory
        """
        with open(self.doc_index_path, "r") as openfile:
            json_obj = json.load(openfile)
        for source in json_obj["saved_docs"]:
            if not os.path.isfile(source["source"]):
                print("delete ids " + str(source["ids"]))
                self.vector_db._collection.delete(ids=source["ids"])
                print(self.vector_db._collection.count())
                copy_json = deepcopy(json_obj)
                copy_json["saved_docs"].remove(source)

                with open(self.doc_index_path, "w") as outfile:
                    json.dump(copy_json, outfile)

    def sync_folder(self, path, reset=False):
        if os.path.isdir(path):
            self.clear_removed_sources()
            split_docs = []

            for dirpath, dirs, files in os.walk(path):
                for filename in files:
                    filename_with_path = os.path.join(dirpath, filename)
                    if self.should_update_source(filename_with_path):
                        if filename_with_path.endswith(".pdf"):
                            loader = PyPDFLoader(filename_with_path)
                        elif filename_with_path.endswith(".txt"):
                            loader = TextLoader(filename_with_path, encoding="utf8")
                        elif filename_with_path.endswith(".csv"):
                            loader = CSVLoader(filename_with_path, encoding="utf8")
                        elif filename_with_path.endswith(".docx"):
                            loader = Docx2txtLoader(filename_with_path)

                        if filename_with_path.endswith(
                            (".pdf", ".txt", ".csv", ".docx")
                        ):
                            self.delete_source_if_existing(filename_with_path)
                            documents = loader.load()
                            text_splitter = RecursiveCharacterTextSplitter(
                                chunk_size=config.character_splitter_chunk_size,
                                chunk_overlap=config.character_splitter_chunk_overlap,
                            )
                            split_docs.extend(text_splitter.split_documents(documents))

            self.create_and_load_collection(split_docs, reset)
            self.update_path(path)
        else:
            st.error("Path not found!")

    def sync_google_drive(self, folder_id):
        loader = GoogleDriveLoader(
            folder_id=folder_id,
            recursive=True,
        )
        documents = loader.load()

        if documents:
            split_docs = self.text_splitter.split_documents(documents)
            self.create_and_load_collection(split_docs)
            self.update_path(folder_id)
        else:
            st.error("Google Drive folder not found!")

    def sync_code_repo(self, path, reset=False):
        if os.path.isdir(path):
            self.clear_removed_sources()
            split_docs = []

            for dirpath, dirs, files in os.walk(path):
                for filename in files:
                    filename_with_path = os.path.join(dirpath, filename)
                    if self.should_update_source(filename_with_path):
                        if filename_with_path.endswith((".cpp", ".hpp", ".h", ".md")):
                            self.delete_source_if_existing(filename_with_path)
                            loader = TextLoader(filename_with_path, encoding="utf8")
                            documents = loader.load()
                            text_splitter = RecursiveCharacterTextSplitter(
                                chunk_size=config.character_splitter_chunk_size,
                                chunk_overlap=config.character_splitter_chunk_overlap,
                            )
                            split_docs.extend(text_splitter.split_documents(documents))

            self.create_and_load_collection(split_docs, reset)
            self.update_path(path)
        else:
            st.error("Path not found!")

    def display_saved_files(self, show_delete=True):
        # Renders the saved files as a list with control buttons
        with open(self.doc_index_path, "r") as openfile:
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
                            self.vector_db._collection.delete(ids=source["ids"])
                            print(self.vector_db._collection.count())
                            copy_json = deepcopy(json_obj)
                            for doc_data in saved_docs:
                                if doc_data["ids"] == source["ids"]:
                                    copy_json["saved_docs"].remove(doc_data)
                                    break
                            with open(self.doc_index_path, "w") as outfile:
                                json.dump(copy_json, outfile)

                        st.button(
                            "Delete",
                            key=str(self.id) + "_" + str(index),
                            on_click=delete_source,
                            use_container_width=True,
                        )
                else:
                    st.markdown("######")
                    st.write(source["source"])
