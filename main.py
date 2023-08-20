import streamlit as st
import json
from os import environ
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.vectorstores import Chroma
from PyPDF2 import PdfReader
from docx import Document


openai_api_key = ""
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
vectordb = Chroma(persist_directory="./data/chroma_db", embedding_function=embeddings)


def upload_file(file):
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

        #TODO: PPT
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_text(input_docs)
        
        vectordb.add_texts(texts)


def generate_response(query):
    llm = OpenAI(temperature=0.2, openai_api_key=openai_api_key)
    llm_retriever = MultiQueryRetriever.from_llm(retriever=vectordb.as_retriever(), llm=llm)
    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=llm_retriever)
    st.info(qa.run(query))


def main():
    openai_api_key = environ.get('OPENAI_API_KEY')
    openai_api_key = st.sidebar.text_input('OpenAI API Key', value=openai_api_key, type='password')
    
    st.title('Note Q&A')

    st.markdown('#')
    st.subheader('Ask')
    with st.form('my_form'):
        text = st.text_area('Ask:', 'What are the three key pieces of advice for learning how to code?', label_visibility='collapsed')
        submitted = st.form_submit_button('Submit')
        if not openai_api_key.startswith('sk-'):
            st.warning('Please enter your OpenAI API key!', icon='⚠')
        if submitted and openai_api_key.startswith('sk-'):
            generate_response(text)

    st.markdown('#')
    st.subheader('Upload')
    file = st.file_uploader('Upload files:', type=["pdf", "docx", "csv", "txt"], label_visibility='collapsed')
    upload_file(file)

    st.markdown('#')
    st.subheader('Saved Files')


if __name__ == '__main__':
    main()