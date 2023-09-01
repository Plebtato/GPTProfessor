import config
import documents
import document_collections
import qa
import streamlit as st


# STATE AND GLOBAL MANAGEMENT

if "create_popup" not in st.session_state:
    st.session_state["create_popup"] = True

if "current_collection_id" not in st.session_state:
    st.session_state["current_collection_id"] = ""

if (
    st.session_state["create_popup"] == False
    and not st.session_state["current_collection_id"]
):
    if document_collections.get_collections():
        st.session_state[
            "current_collection_id"
        ] = document_collections.get_collections()[0]["id"]
    else:
        st.session_state["create_popup"] = True


# SIDEBAR

st.sidebar.title(":page_facing_up: Where's the Answer?")
st.sidebar.divider()

st.sidebar.header("Document Collections")
document_collections.display_collections()
st.sidebar.button(
    ":heavy_plus_sign: New",
    type="primary",
    use_container_width=True,
    on_click=document_collections.open_popup,
)

st.sidebar.divider()
config.openai_api_key = st.sidebar.text_input(
    "OpenAI API Key", value=config.openai_api_key, type="password"
)


# CREATE INTERFACE

if st.session_state["create_popup"]:
    st.title("Create A New Collection")

    # with st.form('create_form'):
    show_name_in_use_err = False
    show_missing_name_err = False
    new_collection_name = st.text_input("Name")
    new_collection_type = st.radio(
        "Type",
        ["Manual", "Sync", "Google Drive", "Code"],
        captions=[
            "Add and remove your documents manually. Supports PDF, DOCX, CSV, and TXT.",
            "Select a folder on your device to automatically upload and sync. Supports PDF, DOCX, CSV, and TXT.",
            "Select a Google Drive folder to automatically upload and sync Google Docs and Google Sheets.",
            "Select a local code repository to automatically upload and sync. Supports C++ and C# source code. WIP!"
        ],
    )
    col1, col2 = st.columns(2)

    if document_collections.get_collections():
        with col1:
            if st.button(
                "Create",
                type="primary",
                use_container_width=True,
                on_click=document_collections.create_collection,
                args=(new_collection_name, new_collection_type),
            ):
                if not new_collection_name:
                    show_missing_name_err = True
                elif document_collections.validate_collection_name(new_collection_name):
                    show_name_in_use_err = False
                    show_missing_name_err = False
                else:
                    show_name_in_use_err = True
        with col2:
            st.button(
                "Cancel",
                use_container_width=True,
                on_click=document_collections.close_popup,
            )
    else:
        if st.button(
            "Create",
            type="primary",
            use_container_width=True,
            on_click=document_collections.create_collection,
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


# Q&A INTERFACE

if not st.session_state["create_popup"]:
    
    # Load collection info
    collection_title = ""
    collection_type = ""
    collection_path = ""
    for collection in document_collections.get_collections():
        if collection["id"] == st.session_state["current_collection_id"]:
            collection_title = collection["name"]
            collection_type = collection["type"]
            break
    if collection_type != "Manual":
        collection_path = documents.get_path(st.session_state["current_collection_id"])
    
    st.title(collection_title)

    with st.form("ask_form"):
        text = st.text_area(
            "Question", placeholder="Ask me anything about your documents!"
        )
        model = st.radio(
            "Select Model",
            ("DaVinci", "GPT-3.5", "GPT-4"),
            captions=[
            "Low cost language model. Good for general use.",
            "More expensive to run, but may provide better results.",
            "Highly capable next-generation model. Requires special OpenAI access. Also hurts your wallet."
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

    st.markdown("######")
    
    if collection_type == "Manual":
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

        st.markdown("######")
        st.subheader("Saved Files")
        with st.expander("List", expanded=True):
            documents.display_saved_files(st.session_state["current_collection_id"])
    
    elif collection_type == "Sync":
        st.subheader("Select Folder")
        with st.form("code_select_form", clear_on_submit=False):
            code_path = st.text_input("Folder Path", placeholder="C:\\Users\\Me\\Documents\\Course Notes", value=collection_path)
            submitted_code_path = st.form_submit_button("Submit", use_container_width=True)

    elif collection_type == "Google Drive":
        st.subheader("Select Google Drive Folder")
        with st.form("code_select_form", clear_on_submit=False):
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
            drive_path = st.text_input("Google Drive Folder ID", placeholder="1yucgL9WGgWZdM1TOuKkeghlPizuzMYb5", value=collection_path)
            submitted_drive_path = st.form_submit_button("Submit", use_container_width=True)
            if drive_path and submitted_drive_path and st.session_state["current_collection_id"]:
                with st.spinner("This could take a while..."):
                    documents.sync_google_drive(drive_path, st.session_state["current_collection_id"])
    
    elif collection_type == "Code":
        st.subheader("Select Project")
        with st.form("code_select_form", clear_on_submit=False):
            code_path = st.text_input("Directory Path", placeholder="C:\\Users\\Me\\Project_Repo", value=collection_path)
            submitted_code_path = st.form_submit_button("Submit", use_container_width=True)
            if code_path and submitted_code_path and st.session_state["current_collection_id"]:
                with st.spinner("This could take a while..."):
                    documents.sync_code_repo(code_path, st.session_state["current_collection_id"])


    st.markdown("######")
    st.divider()
    st.button(
        "Delete Collection",
        type="primary",
        use_container_width=True,
        on_click=document_collections.delete_collection,
        args=(st.session_state["current_collection_id"],),
    )
