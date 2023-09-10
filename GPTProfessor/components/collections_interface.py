import streamlit as st
import manage_collections


def create_collection_form():
    st.title("Create A New Collection")

    # with st.form('create_form'):
    show_name_in_use_err = False
    show_missing_name_err = False
    new_collection_name = st.text_input("Name")
    new_collection_type = st.radio(
        "Type",
        ["Manual", "Sync", "Google Drive", "Code"],
        # ["Manual","Sync", "Google Drive", "Code", "Confluence"],
        captions=[
            "Add and remove your documents manually. Supports PDF, DOCX, CSV, and TXT.",
            "Select a folder on your device to automatically upload and sync. Supports PDF, DOCX, CSV, and TXT.",
            "Select a Google Drive folder to automatically upload and sync Google Docs and Google Sheets. WIP!",
            "Select a local code repository to automatically upload and sync. Supports C++ and C# source code. WIP!",
            # "Load Confluence pages.",
        ],
    )
    col1, col2 = st.columns(2)

    if manage_collections.get_collections():
        with col1:
            if st.button(
                "Create",
                type="primary",
                use_container_width=True,
                on_click=manage_collections.create_collection,
                args=(new_collection_name, new_collection_type),
            ):
                if not new_collection_name:
                    show_missing_name_err = True
                elif manage_collections.validate_collection_name(new_collection_name):
                    show_name_in_use_err = False
                    show_missing_name_err = False
                else:
                    show_name_in_use_err = True
        with col2:
            st.button(
                "Cancel",
                use_container_width=True,
                on_click=close_popup,
            )
    else:
        if st.button(
            "Create",
            type="primary",
            use_container_width=True,
            on_click=manage_collections.create_collection,
            args=(new_collection_name, new_collection_type),
        ):
            if not new_collection_name:
                show_missing_name_err = True

    if show_name_in_use_err:
        st.error(
            "A collection with this name already exists. Please choose a different name.",
            icon="🚨",
        )

    if show_missing_name_err:
        st.error("Please enter a name for your collection.", icon="🚨")


def open_popup(open=True):
    if open:
        st.session_state["create_popup"] = True
        st.session_state["chat_popup"] = False


def close_popup(close=True):
    if close:
        st.session_state["create_popup"] = False
