import streamlit as st
import config
import manage_collections
import components.collections_interface

def sidebar():
    st.sidebar.title(":page_facing_up: Where's the Answer?")
    st.sidebar.divider()

    st.sidebar.header("Document Collections")
    manage_collections.display_collections()
    st.sidebar.button(
        ":heavy_plus_sign: New",
        type="primary",
        use_container_width=True,
        on_click=components.collections_interface.open_popup,
    )

    st.sidebar.divider()
    config.openai_api_key = st.sidebar.text_input(
        "OpenAI API Key", value=config.openai_api_key, type="password"
    )
