import config
import streamlit as st
from langchain.llms import OpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.vectorstores import Chroma
import prompts


def generate_response(query, model, collection):
    if model == "GPT-4":
        model_name = "gpt-4"
        max_tokens_limit = 6750
    elif model == "GPT-3.5":
        model_name = "gpt-3.5-turbo"
        max_tokens_limit = 3375
    else:
        model_name = "text-davinci-003"
        max_tokens_limit = 3375

    embeddings = OpenAIEmbeddings(openai_api_key=config.openai_api_key)
    vectordb = Chroma(
        "db" + str(collection),
        persist_directory=config.db_path,
        embedding_function=embeddings,
    )

    llm = OpenAI(
        temperature=0.2, openai_api_key=config.openai_api_key, model_name=model_name
    )
    llm_retriever = MultiQueryRetriever.from_llm(
        retriever=vectordb.as_retriever(search_kwargs={"k": 8}), llm=llm
    )
    load_chain = load_qa_with_sources_chain(
        llm=llm,
        chain_type="stuff",
        prompt=prompts.QA_CHAIN_PROMPT,
        document_prompt=prompts.DOC_PROMPT,
    )
    qa_chain = RetrievalQAWithSourcesChain(
        combine_documents_chain=load_chain,
        retriever=llm_retriever,
        reduce_k_below_max_tokens=True,
        max_tokens_limit=max_tokens_limit,
        return_source_documents=True,
    )

    if query[-1] != "?":
        # err when no question mark?
        query += "?"

    result = qa_chain({"question": query}, return_only_outputs=True)
    print(result)
    sources = []
    for doc in result["source_documents"]:
        if doc.metadata["source"] not in sources:
            sources.append(doc.metadata["source"])

    source_output = "\n\nSources: "
    if sources:
        # sometimes still returns sources when answer is not found, only occurs when Chroma collection is specified (???)
        if result["answer"][0:5] != "Sorry":
            for source in sources:
                source_output += "\n\n" + source
        else:
            source_output = ""
    else:
        source_output = ""

    st.info(result["answer"] + source_output)
    print("LLM query done")
