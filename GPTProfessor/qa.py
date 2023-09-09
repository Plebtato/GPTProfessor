import config
import streamlit as st
from langchain.llms import OpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainFilter
from langchain.vectorstores import Chroma
import prompts
from documents import DocumentCollection


def generate_response(query, model, collection : DocumentCollection):
    if model == "GPT-4":
        model_name = "gpt-4"
        max_tokens_limit = 6750
    elif model == "GPT-3.5":
        model_name = "gpt-3.5-turbo"
        max_tokens_limit = 3375
    else:
        model_name = "text-davinci-003"
        max_tokens_limit = 3375

    llm = OpenAI(
        temperature=0.3, openai_api_key=config.openai_api_key, model_name=model_name
    )
    compressor = LLMChainFilter.from_llm(llm)
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=collection.vector_db.as_retriever(search_kwargs={"k": 16}),
    )
    # llm_retriever = MultiQueryRetriever.from_llm(
    #     retriever=vectordb.as_retriever(search_kwargs={"k": 16}), llm=llm
    # )
    load_chain = load_qa_with_sources_chain(
        llm=llm,
        chain_type="stuff",
        prompt=prompts.QA_CHAIN_PROMPT,
        document_prompt=prompts.DOC_PROMPT,
    )
    qa_chain = RetrievalQAWithSourcesChain(
        combine_documents_chain=load_chain,
        retriever=compression_retriever,
        reduce_k_below_max_tokens=True,
        max_tokens_limit=max_tokens_limit,
        return_source_documents=True,
    )

    if query[-1] != "?":
        # err when no question mark?
        query += "?"

    result = qa_chain({"question": query}, return_only_outputs=True)
    sources = []
    for doc in result["source_documents"]:
        print("\n\n" + str(doc))
        if doc.metadata["source"] not in sources:
            sources.append(doc.metadata["source"])

    source_output = "\n\nSources: "
    if sources:
        # sometimes still returns sources when answer is not found, only occurs when Chroma collection is specified (???)
        if result["answer"][0:5] != "Sorry" and result["answer"][0:6] != "\nSorry":
            for source in sources:
                source_output += "\n\n" + source
        else:
            source_output = ""
    else:
        source_output = ""

    st.info(result["answer"] + source_output)
    print("\nLLM query done")
