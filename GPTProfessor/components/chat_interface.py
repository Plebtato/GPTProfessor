import streamlit as st
import config
import chatbot
from documents import DocumentCollection
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory


def chat(collection: DocumentCollection):
    message_history = StreamlitChatMessageHistory(
        key="message_history_" + str(collection.id)
    )

    if not st.session_state["chat_model"]:
        st.session_state["chat_model"] = "GPT-3.5"

    st.chat_message("assistant").markdown(
        "Hello there! Feel free to ask questions and discuss!"
    )

    for message in message_history.messages:
        st.chat_message(message.type).write(message.content)

    if prompt := st.chat_input("Say something!"):
        st.chat_message("user").markdown(prompt)

        response = chatbot.generate_chat_response(
            text=prompt,
            collection=collection,
            message_history=message_history,
            model=st.session_state["chat_model"],
        )

        st.chat_message("assistant").markdown(response)

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
