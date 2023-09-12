import config
import utils
import streamlit as st
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainFilter
import prompts
from documents import DocumentCollection


def generate_qa_answer(query, model, collection: DocumentCollection):
    model_name, token_limit_source, token_limit_max = utils.get_model(model)

    if model == "GPT-4":
        qa_prompt = prompts.QA_PROMPT_GPT_35
    elif model == "GPT-3.5":
        qa_prompt = prompts.QA_PROMPT_GPT_35
    elif model == "DaVinci":
        qa_prompt = prompts.QA_PROMPT_DAVINCI

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
        prompt=qa_prompt,
        document_prompt=prompts.DOC_PROMPT,
    )
    qa_chain = RetrievalQAWithSourcesChain(
        combine_documents_chain=load_chain,
        retriever=compression_retriever,
        reduce_k_below_max_tokens=True,
        max_tokens_limit=token_limit_source,
        return_source_documents=True,
    )

    if query[-1] != "?":
        # err when no question mark when using MultiQueryRetriever?
        query += "?"

    result = qa_chain({"question": query}, return_only_outputs=True)
    return format_llm_result_with_source(result)


def generate_quiz_questions(topic, model, collection: DocumentCollection):
    model_name, token_limit_source, token_limit_max = utils.get_model(model)

    if model == "GPT-4":
        quiz_prompt = prompts.QUIZ_PROMPT_GPT_35
    elif model == "GPT-3.5":
        quiz_prompt = prompts.QUIZ_PROMPT_GPT_35

    llm = OpenAI(
        temperature=0.3, openai_api_key=config.openai_api_key, model_name=model_name
    )
    compressor = LLMChainFilter.from_llm(llm)
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=collection.vector_db.as_retriever(search_kwargs={"k": 16}),
    )
    load_chain = load_qa_with_sources_chain(
        llm=llm,
        chain_type="stuff",
        prompt=quiz_prompt,
        document_prompt=prompts.DOC_PROMPT,
    )
    qa_chain = RetrievalQAWithSourcesChain(
        combine_documents_chain=load_chain,
        retriever=compression_retriever,
        reduce_k_below_max_tokens=True,
        max_tokens_limit=token_limit_source,
        return_source_documents=True,
    )

    result = qa_chain({"question": topic}, return_only_outputs=True)
    return format_llm_result_with_source(result)


def format_llm_result_with_source(result):
    sources = []
    for doc in result["source_documents"]:
        # print("\n\n" + str(doc))
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

    return result["answer"] + source_output
    
