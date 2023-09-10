import streamlit as st
import config
from documents import DocumentCollection


def chat(collection: DocumentCollection):
    if not st.session_state["chat_model"]:
        st.session_state["chat_model"] = "GPT-3.5"

    for message in st.session_state["messages_" + str(collection.id)]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Say something!"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state["messages_" + str(collection.id)].append({"role": "user", "content": prompt})

        response = f"Echo: {prompt}"
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response)
        # Add assistant response to chat history
        st.session_state["messages_" + str(collection.id)].append({"role": "assistant", "content": response})

    st.button(
        ":arrow_backward: Return to Main Page",
        on_click=close_popup,
    )


def open_popup(model, open=True):
    if open:
        st.session_state["chat_model"] = model
        st.session_state["chat_popup"] = True


def close_popup(close=True):
    if close:
        st.session_state["chat_popup"] = False
