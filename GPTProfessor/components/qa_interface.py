import streamlit as st
import config
import qa
import manage_collections
import components.chat_interface
from documents import DocumentCollection


def ask_form(collection: DocumentCollection):
    with st.form("ask_form"):
        st.write(
            "Ask a question and get a quick response. Works better with more specific questions."
        )
        st.markdown("######")
        question = st.text_area(
            "Question",
            placeholder="Ask me anything, as long as it is in your documents! ",
        )
        model = st.radio(
            "Select Model",
            ("DaVinci", "GPT-3.5", "GPT-4"),
            captions=[
                "Low cost language model. Good for general use, may struggle with more complex questions.",
                "More expensive to run, often provides better results.",
                "Highly capable next-generation model. Requires special OpenAI access. May hurt your wallet.",
            ],
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
                st.info(qa.generate_qa_answer(question, model, collection))


def open_chat_form(collection: DocumentCollection):
    with st.form("chat_form"):
        st.write(
            "Have a converation! Please note that the answers from here will probably be less refined than the Q&A answers."
        )
        st.markdown("######")
        model = st.radio(
            "Select Model",
            ("GPT-3.5", "GPT-4"),
            captions=[
                "This model is the basis for ChatGPT.",
                "Highly capable next-generation model. Requires special OpenAI access. May hurt your wallet.",
            ],
        )
        st.form_submit_button(
            "Launch Chat",
            use_container_width=True,
            on_click=components.chat_interface.open_popup,
            args=(model,),
        )


def quiz_form(collection: DocumentCollection):
    with st.form("quiz_form"):
        st.write("Choose a topic from your documents to create study questions for.")
        st.markdown("######")
        topic = st.text_input(
            "Topic",
            placeholder="Choose a topic!",
        )
        model = st.radio(
            "Select Model",
            ("GPT-3.5", "GPT-4"),
            captions=[
                "This model is the basis for ChatGPT.",
                "Highly capable next-generation model. Requires special OpenAI access. May hurt your wallet.",
            ],
        )
        submitted_question = st.form_submit_button("Submit", use_container_width=True)
        if not config.openai_api_key.startswith("sk-"):
            st.warning("Please enter your OpenAI API key!", icon="⚠")
        if not st.session_state["current_collection_id"]:
            st.error("Error, invalid collection.", icon="⚠")
        if (
            submitted_question
            and config.openai_api_key.startswith("sk-")
            and st.session_state["current_collection_id"]
        ):
            with st.spinner():
                st.info(qa.generate_quiz_questions(topic, model, collection))


def manual_collection_update_form(collection: DocumentCollection):
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
                collection.upload_file(file)
            st.success("Done!")

    st.markdown("######")
    st.subheader("Saved Files")
    with st.expander("List", expanded=True):
        collection.display_saved_files()


def path_collection_update_form(collection: DocumentCollection):
    current_collection_path = collection.get_path()
    if collection.type == "Sync":
        st.subheader("Change Folder") if current_collection_path else st.subheader(
            "Select Folder"
        )
        path_placeholder = "C:\\Users\\Me\\Documents\\Course Notes"
        input_label = "Path"
    elif collection.type == "Google Drive":
        st.subheader(
            "Change Google Drive Folder"
        ) if current_collection_path else st.subheader("Select Google Drive Folder")
        path_placeholder = "1yucgL9WGgWZdM1TOuKkeghlPizuzMYb5"
        input_label = "Folder ID"
    elif collection.type == "Code":
        st.subheader("Change Repository") if current_collection_path else st.subheader(
            "Select Repository"
        )
        path_placeholder = "C:\\Users\\Me\\Project_Repo"
        input_label = "Path"

    with st.form("select_form", clear_on_submit=True):
        if collection.type == "Google Drive":
            st.subheader("Requirements")
            st.write(
                """
                        1. [Create a Google Cloud project or use an existing project.](https://console.cloud.google.com/flows/enableapi?apiid=drive.googleapis.com)\n
                        2. [Enable the Google Drive API.](https://developers.google.com/drive/api/quickstart/python#authorize_credentials_for_a_desktop_application)\n
                        3. Authorize credentials for desktop app.
                        """
            )
            st.divider()
            st.subheader("Selection")
            st.write(
                """
                        You can get the ID of a Google Drive folder from the last part of the URL. For example:\n
                        URL: https://drive.google.com/drive/u/0/folders/1yucgL9WGgWZdM1TOuKkeghlPizuzMYb5\n
                        ID: 1yucgL9WGgWZdM1TOuKkeghlPizuzMYb5
                        """
            )
            st.divider()

        path = st.text_input(input_label, placeholder=path_placeholder)
        submitted_path = st.form_submit_button("Submit", use_container_width=True)

        if path and submitted_path and st.session_state["current_collection_id"]:
            with st.spinner("This could take a while..."):
                reset = True if current_collection_path else False

                if collection.type == "Sync":
                    collection.sync_folder(path, reset)
                elif collection.type == "Google Drive":
                    collection.sync_google_drive(path)
                elif collection.type == "Code":
                    collection.sync_code_repo(path, reset)

            st.success("Done!")


def path_collection_reload_form(collection: DocumentCollection):
    current_collection_path = collection.get_path()
    if current_collection_path:
        if collection.type == "Sync":
            st.subheader("Reload Folder")
            description = "Updates the collection with new changes to the files in the current folder:"
        elif collection.type == "Google Drive":
            st.subheader("Reload Folder")
            description = "Updates the collection with new changes to the files in the current folder:"
        elif collection.type == "Code":
            st.subheader("Reload Repository")
            description = "Updates the collection with new changes to the files in the current repository:"

        with st.form("reload_form", clear_on_submit=False):
            st.write(description)
            st.write(current_collection_path)
            submitted_path = st.form_submit_button("Reload", use_container_width=True)

            if submitted_path and st.session_state["current_collection_id"]:
                with st.spinner("This could take a while..."):
                    if collection.type == "Sync":
                        collection.sync_folder(
                            current_collection_path,
                        )
                    elif collection.type == "Google Drive":
                        collection.sync_google_drive(
                            current_collection_path,
                        )
                    elif collection.type == "Code":
                        collection.sync_code_repo(
                            current_collection_path,
                        )

                st.success("Done!")

        if collection.type == "Sync":
            with st.expander("View File List", expanded=False):
                collection.display_saved_files(False)


def delete_collection_button():
    st.button(
        "Delete Collection",
        type="primary",
        use_container_width=True,
        on_click=manage_collections.delete_collection,
        args=(st.session_state["current_collection_id"],),
    )
