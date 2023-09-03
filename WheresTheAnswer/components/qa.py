import streamlit as st
import documents
import config
import qa
import document_collections


def ask_form():
    with st.form("ask_form"):
        text = st.text_area(
            "Question", placeholder="Ask me anything about your documents!"
        )
        model = st.radio(
            "Select Model",
            ("DaVinci", "GPT-3.5", "GPT-4"),
            captions=[
            "Low cost language model. Good for general use, may struggle with more complex questions.",
            "More expensive to run, often provides better results.",
            "Highly capable next-generation model. Requires special OpenAI access. May hurt your wallet."
            ]
        )
        submitted_ask = st.form_submit_button("Submit", use_container_width=True)
        if not config.openai_api_key.startswith("sk-"):
            st.warning("Please enter your OpenAI API key!", icon="⚠")
        if not st.session_state["current_collection_id"]:
            st.error("Error, invalid collection.", icon="⚠")
        if (
            submitted_ask
            and config.openai_api_key.startswith("sk-")
            and st.session_state["current_collection_id"]
        ):
            with st.spinner():
                qa.generate_response(
                    text, model, st.session_state["current_collection_id"]
                )


def manual_collection_update_form():
    st.subheader("Upload")
    with st.form("upload_form", clear_on_submit=False):
        file = st.file_uploader(
            "Upload files:",
            type=["pdf", "docx", "csv", "txt"],
            label_visibility="collapsed",
        )
        submitted_doc = st.form_submit_button("Submit", use_container_width=True)
        if not st.session_state["current_collection_id"]:
            st.error("Error, invalid collection.", icon="⚠")
        if submitted_doc and file and st.session_state["current_collection_id"]:
            with st.spinner("This could take a while..."):
                documents.upload_file(file, st.session_state["current_collection_id"])
            st.success('Done!')

    st.markdown("######")
    st.subheader("Saved Files")
    with st.expander("List", expanded=True):
        documents.display_saved_files(st.session_state["current_collection_id"])


def path_collection_update_form(type):
    current_collection_path = documents.get_path(st.session_state["current_collection_id"])
    if type == "Sync":
        st.subheader("Change Folder") if current_collection_path else st.subheader("Select Folder")
        path_placeholder = "C:\\Users\\Me\\Documents\\Course Notes"
        input_label = "Path"
    elif type == "Google Drive":
        st.subheader("Change Google Drive Folder") if current_collection_path else st.subheader("Select Google Drive Folder")
        path_placeholder = "1yucgL9WGgWZdM1TOuKkeghlPizuzMYb5"
        input_label = "Folder ID"
    elif type == "Code":
        st.subheader("Change Repository") if current_collection_path else st.subheader("Select Repository")
        path_placeholder = "C:\\Users\\Me\\Project_Repo"
        input_label = "Path"

    with st.form("select_form", clear_on_submit=True):
        if type == "Google Drive":
            st.subheader("Requirements")
            st.write("""
                        1. [Create a Google Cloud project or use an existing project.](https://console.cloud.google.com/flows/enableapi?apiid=drive.googleapis.com)\n
                        2. [Enable the Google Drive API.](https://developers.google.com/drive/api/quickstart/python#authorize_credentials_for_a_desktop_application)\n
                        3. Authorize credentials for desktop app.
                        """)
            st.divider()
            st.subheader("Selection")
            st.write("""
                        You can get the ID of a Google Drive folder from the last part of the URL. For example:\n
                        URL: https://drive.google.com/drive/u/0/folders/1yucgL9WGgWZdM1TOuKkeghlPizuzMYb5\n
                        ID: 1yucgL9WGgWZdM1TOuKkeghlPizuzMYb5
                        """)
            st.divider()

        path = st.text_input(input_label, placeholder=path_placeholder)
        submitted_path = st.form_submit_button("Submit", use_container_width=True)
        
        if path and submitted_path and st.session_state["current_collection_id"]:
            with st.spinner("This could take a while..."):
                reset = True if current_collection_path else False

                if type == "Sync":
                    documents.sync_folder(path, st.session_state["current_collection_id"], reset)
                elif type == "Google Drive":
                    documents.sync_google_drive(path, st.session_state["current_collection_id"])
                elif type == "Code":
                    documents.sync_code_repo(path, st.session_state["current_collection_id"], reset)
                
            st.success('Done!')


def path_collection_reload_form(type):
    current_collection_path = documents.get_path(st.session_state["current_collection_id"])
    if current_collection_path:
        if type == "Sync":
            st.subheader("Reload Folder")
            description = "Updates the collection with the new changes to the current folder:"
        elif type == "Google Drive":
            st.subheader("Reload Folder")
            description = "Updates the collection with the new changes to the current folder:"
        elif type == "Code":
            st.subheader("Reload Repository") 
            description = "Updates the collection with new changes to the current repository:"
        
        with st.form("reload_form", clear_on_submit=False):
            st.write(description)
            st.write(current_collection_path)
            submitted_path = st.form_submit_button("Reload", use_container_width=True)
            
            if submitted_path and st.session_state["current_collection_id"]:
                with st.spinner("This could take a while..."):
                    if type == "Sync":
                        documents.sync_folder(current_collection_path, st.session_state["current_collection_id"])
                    elif type == "Google Drive":
                        documents.sync_google_drive(current_collection_path, st.session_state["current_collection_id"])
                    elif type == "Code":
                        documents.sync_code_repo(current_collection_path, st.session_state["current_collection_id"])
                    
                st.success('Done!')
        
        if type == "Sync":
            with st.expander("View File List", expanded=False):
                documents.display_saved_files(st.session_state["current_collection_id"], False)


def delete_collection_button():
    st.button(
        "Delete Collection",
        type="primary",
        use_container_width=True,
        on_click=document_collections.delete_collection,
        args=(st.session_state["current_collection_id"],),
    )