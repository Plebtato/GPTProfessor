import streamlit as st
import json
import os
import copy
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.vectorstores import Chroma
from langchain.vectorstores import FAISS
from PyPDF2 import PdfReader
from docx import Document


openai_api_key = ""

db_path = os.path.join("data", "chroma_db")
doc_index_path = os.path.join("data", "doc_index.json")

embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
vectordb = Chroma(persist_directory=db_path, embedding_function=embeddings)


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
        
        if (os.path.isfile(doc_index_path)):
            with open(doc_index_path, "r") as openfile:
                json_obj = json.load(openfile)

            last_id = json_obj["last_id"]
            ids = [str(i) for i in range(last_id, last_id + len(texts))]
            metadata = []

            for text in texts:
                metadata.append({ "source": file.name })

            vectordb.add_texts(texts, metadatas=metadata, ids=ids)
            print("Embedding query done")

            saved_docs = json_obj["saved_docs"]
            saved_docs.append({
                "source": file.name,
                "ids": ids
            })
            dictionary = {
                "last_id": last_id + len(texts),
                "saved_docs": saved_docs
            }

            with open(doc_index_path, "w") as outfile:
                json.dump(dictionary, outfile)
        
        else:
            last_id = 0
            ids = [str(i) for i in range(last_id, last_id + len(texts))]
            metadata = []

            for text in texts:
                metadata.append({ "source": file.name })

            vectordb.add_texts(texts, metadatas=metadata, ids=ids)
            print("Embedding query done")

            dictionary = {
                "last_id": last_id + len(texts),
                "saved_docs": [{
                    "source": file.name,
                    "ids": ids
                }]
            }

            with open(doc_index_path, "w") as outfile:
                json.dump(dictionary, outfile)


def generate_response(query):
    # TODO: add model options (davinci, chatgpt3 and 4)
    llm = OpenAI(temperature=0.2, openai_api_key=openai_api_key)
    llm_retriever = MultiQueryRetriever.from_llm(retriever=vectordb.as_retriever(), llm=llm)
    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=llm_retriever)

    if (query[-1] != "?"):
        # err when no question mark?
        query += "?"

    st.info(qa.run(query))
    print("LLM query done")


def list_saved_files():
    if (os.path.isfile(doc_index_path)):
        with open(doc_index_path, "r") as openfile:
            json_obj = json.load(openfile)

        saved_docs = json_obj["saved_docs"]
        
        for index, doc in enumerate(saved_docs):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("######")
                st.text(doc["source"])
            
            with col2:

                def delete_doc():
                    print("delete ids " + str(doc["ids"]))
                    vectordb._collection.delete(ids=doc["ids"])
                    print(vectordb._collection.count())
                    copy_json = copy.deepcopy(json_obj)
                    for x in saved_docs:
                        if x["ids"] == doc["ids"]:
                            copy_json["saved_docs"].remove(x)
                            break
                    with open(doc_index_path, "w") as outfile:
                        json.dump(copy_json, outfile)
                
                st.button("Delete", key=index, on_click=delete_doc)


def main():
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    openai_api_key = st.sidebar.text_input('OpenAI API Key', value=openai_api_key, type='password')
    
    st.title('Note Q&A')

    st.markdown('#')
    st.subheader('Ask')
    with st.form('ask_form'):
        text = st.text_area('Ask:', 'What are the three key pieces of advice for learning how to code?', label_visibility='collapsed')
        submitted = st.form_submit_button('Submit')
        if not openai_api_key.startswith('sk-'):
            st.warning('Please enter your OpenAI API key!', icon='⚠')
        if submitted and openai_api_key.startswith('sk-'):
            generate_response(text)

    st.markdown('#')
    st.subheader('Upload')
    with st.form("upload_form", clear_on_submit=True):
        file = st.file_uploader('Upload files:', type=["pdf", "docx", "csv", "txt"], label_visibility='collapsed')
        submitted = st.form_submit_button("Submit")
        if submitted and file:
            upload_file(file)

    st.markdown('#')
    st.subheader('Saved Files')
    list_saved_files()


if __name__ == '__main__':
    main()