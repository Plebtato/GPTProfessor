import streamlit as st
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.vectorstores import Chroma
from PyPDF2 import PdfReader
from docx import Document
import json

st.title('Note Q&A')

openai_api_key = st.sidebar.text_input('OpenAI API Key', type='password')

file = st.file_uploader('Upload files', type=["pdf", "docx", "csv", "txt"], )

if file is not None:
    if file.type == "application/pdf":
        reader = PdfReader(file)
        input_docs = ""
        for page in reader.pages:
            input_docs += page.extract_text() + " "
    
    elif file.type == "text/plain":
        input_docs = file.read().decode()

    elif file.type == "text/csv":
        input_docs = file.read().decode()

    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        docx = Document(file)
        input_docs = ""
        for paragraph in docx.paragraphs:
            input_docs += paragraph.text + " "
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_text(input_docs)
    embeddings = OpenAIEmbeddings()
    vectordb = Chroma(persist_directory="./data/chroma_db", embedding_function=embeddings)
    vectordb.add_texts(texts)

def generate_response(query):
    llm = OpenAI(temperature=0.2, openai_api_key=openai_api_key)
    llm_retriever = MultiQueryRetriever.from_llm(retriever=vectordb.as_retriever(), llm=llm)
    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=llm_retriever)
    st.info(qa.run(query))

with st.form('my_form'):
    text = st.text_area('Ask:', 'What are the three key pieces of advice for learning how to code?')
    submitted = st.form_submit_button('Submit')
    if not openai_api_key.startswith('sk-'):
        st.warning('Please enter your OpenAI API key!', icon='⚠')
    if submitted and openai_api_key.startswith('sk-'):
        generate_response(text)