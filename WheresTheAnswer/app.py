import manage_collections
import streamlit as st
import components.sidebar
import components.collections_interface
import components.qa_interface


# STATE MANAGEMENT

if "create_popup" not in st.session_state:
    st.session_state["create_popup"] = True

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
    collection_title = ""
    collection_type = ""
    for collection in manage_collections.get_collections():
        if collection["id"] == st.session_state["current_collection_id"]:
            collection_title = collection["name"]
            collection_type = collection["type"]
            break
  
    st.title(collection_title)

    components.qa_interface.ask_form()
   
    st.markdown("######")
    
    if collection_type == "Manual":
        components.qa_interface.manual_collection_update_form()
    else:
        components.qa_interface.path_collection_update_form(collection_type)
        components.qa_interface.path_collection_reload_form(collection_type)

    st.markdown("######")

    st.divider()
    components.qa_interface.delete_collection_button()