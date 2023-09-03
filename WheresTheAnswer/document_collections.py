import config
import streamlit as st
import json
import os
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from pathlib import Path


def get_collections():
    if os.path.isfile(config.collections_path):
        with open(config.collections_path, "r") as openfile:
            json_obj = json.load(openfile)
        return json_obj["collections"]
    else:
        return []


def display_collections():
    collections_list = get_collections()

    for index, collection in enumerate(collections_list):

        def click(collection=collection):
            st.session_state["current_collection_id"] = collection["id"]
            st.session_state["create_popup"] = False

        st.sidebar.button(
            collection["name"],
            key=index,
            use_container_width=True,
            on_click=click,
            args=(collection,),
        )


def open_popup(open=True):
    if open:
        st.session_state["create_popup"] = True


def close_popup(close=True):
    if close:
        st.session_state["create_popup"] = False


def validate_collection_name(collection_name):
    collections = get_collections()
    for collection in collections:
        if collection_name == collection["name"]:
            return False
    return True


def create_collection(collection_name, collection_type):
    if not get_collections():
        Path(os.path.join("data", "doc_index")).mkdir(parents=True, exist_ok=True)
        create_collection_dict = {"collections": []}

        with open(config.collections_path, "w") as outfile:
            json.dump(create_collection_dict, outfile)

    if collection_name and validate_collection_name(collection_name):
        collections_list = get_collections()

        if collections_list:
            id = collections_list[-1]["id"] + 1
        else:
            id = 1

        print("Create collection: " + collection_name)
        doc_index_path = os.path.join("data", "doc_index", str(id) + ".json")

        collection_dict = {"path": "", "last_id": 0, "saved_docs": []}

        with open(doc_index_path, "w") as outfile:
            json.dump(collection_dict, outfile)

        collections_list.append({"name": collection_name, "id": id, "type": collection_type})
        add_collection_dict = {"collections": collections_list}

        with open(config.collections_path, "w") as outfile:
            json.dump(add_collection_dict, outfile)

        st.session_state["current_collection_id"] = id
        close_popup()


def delete_collection(collection):
    doc_index_path = os.path.join("data", "doc_index", str(collection) + ".json")

    if os.path.exists(doc_index_path):
        embeddings = OpenAIEmbeddings(openai_api_key=config.openai_api_key)
        vectordb = Chroma(
            "db" + str(collection),
            persist_directory=config.db_path,
            embedding_function=embeddings,
        )
        vectordb.delete_collection()

        os.remove(doc_index_path)
        collections_list = get_collections()
        for collection_data in collections_list:
            if collection_data["id"] == collection:
                collections_list.remove(collection_data)
                break

        add_collection_dict = {"collections": collections_list}

        with open(config.collections_path, "w") as outfile:
            json.dump(add_collection_dict, outfile)

        print("deleted collection")

    st.session_state["current_collection_id"] = ""
    st.session_state["create_popup"] = True
