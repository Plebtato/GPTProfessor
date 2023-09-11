import config
import utils
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationSummaryBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from documents import DocumentCollection
from prompts import CHAT_PROMPT


def generate_chat_response(
    text,
    collection: DocumentCollection,
    message_history: StreamlitChatMessageHistory,
    model,
):
    model_name, token_limit_source, token_limit_max = utils.get_model(model)

    llm = ChatOpenAI(
        temperature=0.8, openai_api_key=config.openai_api_key, model_name=model_name
    )

    memory = ConversationSummaryBufferMemory(
        chat_memory=message_history,
        llm=llm,
        max_token_limit=token_limit_max,
        memory_key="chat_history",
    )

    qa = ConversationalRetrievalChain.from_llm(
        llm,
        retriever=collection.vector_db.as_retriever(search_kwargs={"k": 8}),
        memory=memory,
        get_chat_history=lambda h: h,
        combine_docs_chain_kwargs={"prompt": CHAT_PROMPT},
    )
    return qa({"question": text})["answer"]
