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
    st.title("Create New Collection")

    # with st.form('create_form'):
    show_name_in_use_err = False
    show_missing_name_err = False
    new_collection_name = st.text_input("Name")
    new_collection_type = st.radio(
        "Type",
        ["Manual", "Sync"],
        captions=[
            "Add and remove your documents manually.",
            "Select a folder and automatically upload and sync.",
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


# COLLECTION INTERFACE

if not st.session_state["create_popup"]:
    title = ""
    for collection in document_collections.get_collections():
        if collection["id"] == st.session_state["current_collection_id"]:
            title = collection["name"]
            break
    st.title(title)

    with st.form("ask_form"):
        text = st.text_area(
            "Question:", placeholder="Ask me anything about your documents!"
        )
        model = st.radio(
            "Select Model",
            ("DaVinci", "GPT-3.5", "GPT-4"),
            help="Choose the language model to answer the question with.\n1. DaVinci: Low cost, least capable. Still good for general use.\n2. GPT-3.5: Moderate cost, moderate capability.\n3. GPT-4: Expensive, highly capable, requires special OpenAI access.",
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
    st.subheader("Upload")
    with st.form("upload_form", clear_on_submit=True):
        file = st.file_uploader(
            "Upload files:",
            type=["pdf", "docx", "csv", "txt"],
            label_visibility="collapsed",
        )
        submitted_doc = st.form_submit_button("Submit", use_container_width=True)
        if not st.session_state["current_collection_id"]:
            st.error("Error, invalid collection.", icon="⚠")
        if submitted_doc and file and st.session_state["current_collection_id"]:
            with st.spinner():
                documents.upload_file(file, st.session_state["current_collection_id"])

    st.markdown("######")
    st.subheader("Saved Files")
    with st.expander("", expanded=True):
        documents.display_saved_files(st.session_state["current_collection_id"])

    st.markdown("######")
    st.divider()
    st.button(
        "Delete Collection",
        type="primary",
        use_container_width=True,
        on_click=document_collections.delete_collection,
        args=(st.session_state["current_collection_id"],),
    )
