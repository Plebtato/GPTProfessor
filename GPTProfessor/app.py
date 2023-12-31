import manage_collections
import streamlit as st
import components.sidebar
import components.collections_interface
import components.qa_interface
import components.chat_interface
from documents import DocumentCollection


# STATE MANAGEMENT

if "create_popup" not in st.session_state:
    st.session_state["create_popup"] = True

if "chat_popup" not in st.session_state:
    st.session_state["chat_popup"] = False

if "current_collection_id" not in st.session_state:
    st.session_state["current_collection_id"] = ""

if (
    st.session_state["create_popup"] == False
    and not st.session_state["current_collection_id"]
):
    if manage_collections.get_collections():
        st.session_state[
            "current_collection_id"
        ] = manage_collections.get_collections()[0]["id"]
    else:
        st.session_state["create_popup"] = True

# UI

components.sidebar.sidebar()

if st.session_state["create_popup"]:
    components.collections_interface.create_collection_form()
else:
    # Load collection info
    # use st.cache resource?
    collection = DocumentCollection(st.session_state["current_collection_id"])
    st.title(collection.title)

    if st.session_state["chat_popup"]:
        st.markdown("######")
        components.chat_interface.chat(collection)

    else:
        tab1, tab2, tab3 = st.tabs(["Q&A", "Chat", "Quiz"])

        with tab1:
            components.qa_interface.ask_form(collection)
        with tab2:
            components.qa_interface.open_chat_form(collection)
        with tab3:
            components.qa_interface.quiz_form(collection)

        st.markdown("######")

        if collection.type == "Manual":
            components.qa_interface.manual_collection_update_form(collection)
        else:
            components.qa_interface.path_collection_update_form(collection)
            components.qa_interface.path_collection_reload_form(collection)

        st.markdown("######")

        st.divider()
        components.qa_interface.delete_collection_button()
