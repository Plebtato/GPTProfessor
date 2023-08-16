import streamlit as st
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from PyPDF2 import PdfReader
from docx import Document

st.title('Note Q&A')

openai_api_key = st.sidebar.text_input('OpenAI API Key', type='password')

file = st.file_uploader('Upload files', type=["pdf", "docx", "csv", "txt"], )

if file is not None:
    if file.type == "application/pdf":
        reader = PdfReader(file)
        documents = ""
        for page in reader.pages:
            documents += page.extract_text() + " "
    
    elif file.type == "text/plain":
        documents = file.read().decode()

    elif file.type == "text/csv":
        documents = file.read().decode()

    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        docx = Document(file)
        documents = ""
        for paragraph in docx.paragraphs:
            documents += paragraph.text + " "
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_text(documents)
    embeddings = OpenAIEmbeddings()
    docsearch = Chroma.from_texts(texts, embeddings)

def generate_response(query):
    llm = OpenAI(temperature=0.2, openai_api_key=openai_api_key)
    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=docsearch.as_retriever())
    st.info(qa.run(query))

with st.form('my_form'):
    text = st.text_area('Ask:', 'What are the three key pieces of advice for learning how to code?')
    submitted = st.form_submit_button('Submit')
    if not openai_api_key.startswith('sk-'):
        st.warning('Please enter your OpenAI API key!', icon='⚠')
    if submitted and openai_api_key.startswith('sk-'):
        generate_response(text)