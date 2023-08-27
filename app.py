import streamlit as st
import json
import os
import copy
from langchain.llms import OpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.vectorstores import Chroma
from PyPDF2 import PdfReader
from docx import Document
from prompts import QA_CHAIN_PROMPT, DOC_PROMPT

openai_api_key = ""
if 'create_popup' not in st.session_state:
    st.session_state['create_popup'] = True

if 'current_collection' not in st.session_state:
    st.session_state['current_collection'] = ""

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
            #TODO: OCR support
        
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
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=0
        )
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


def generate_response(query, model):
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
        temperature=0.2, 
        openai_api_key=openai_api_key,
        model_name=model_name
    )
    llm_retriever = MultiQueryRetriever.from_llm(
        retriever=vectordb.as_retriever(search_kwargs = {'k':8}), 
        llm=llm
    )
    load_chain = load_qa_with_sources_chain(
        llm=llm, 
        chain_type="stuff",
        prompt=QA_CHAIN_PROMPT,
        document_prompt=DOC_PROMPT
    ) 
    qa_chain = RetrievalQAWithSourcesChain(
        combine_documents_chain=load_chain,
        retriever=llm_retriever,
        reduce_k_below_max_tokens=True,
        max_tokens_limit=max_tokens_limit,
        return_source_documents=True
    )

    if (query[-1] != "?"):
        # err when no question mark?
        query += "?"

    result = qa_chain({"question": query}, return_only_outputs=True)
    
    sources = []
    for doc in result["source_documents"]:
        if doc.metadata["source"] not in sources:
            sources.append(doc.metadata["source"])
    
    source_output = "\n\nSources: "
    for source in sources:
        source_output += "\n\n" + source 

    st.info(result["answer"] + source_output)
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


def get_collections():
    path = "data"
    if os.path.isdir(path):
        return [ item for item in os.listdir(path) if os.path.isdir(os.path.join(path, item)) ]
    else:
        return []


def open_popup(open = True):
    if open:
        st.session_state['create_popup'] = True


def close_popup(close = True):
    if close:
        st.session_state['create_popup'] = False


def create_collection(collection_name, collection_type):
    print("Creating")
    


def main():
    # SIDEBAR
    
    st.sidebar.title(':question::page_facing_up: Note Q&A')
    st.sidebar.divider()
    st.sidebar.header('Document Collections')

    st.sidebar.button("ECE 350", use_container_width=True)
    st.sidebar.button("pentagon leaked documents", use_container_width=True)
    st.sidebar.button("pentagon leaked documents 2", use_container_width=True)
    st.sidebar.button(":heavy_plus_sign: New", type ="primary", use_container_width=True, on_click=open_popup)

    st.sidebar.divider()
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    openai_api_key = st.sidebar.text_input('OpenAI API Key', value=openai_api_key, type='password')
    
    # CREATE PAGE

    if st.session_state['create_popup']:
        st.title('Create New Collection')

        with st.form('create_form'):
            show_name_error = False
            new_collection_name = st.text_input('Name')
            new_collection_type = st.radio(
                "Type",
                ["Manual", "Sync"],
                captions = ["Add and remove your documents manually.", "Select a folder and automatically upload and sync."])
            col1, col2 = st.columns(2) 

            if len(get_collections()) != 0:
                with col1:
                    is_name_valid = new_collection_name not in get_collections()
                    if st.form_submit_button("Create", type ="primary", use_container_width=True, on_click=open_popup, args=(is_name_valid,)):
                        if is_name_valid:
                            show_name_error = False
                            create_collection(new_collection_name, new_collection_type)
                        else:
                            show_name_error = True
                with col2:
                    st.form_submit_button("Cancel", use_container_width=True, on_click=close_popup)
            else:
                if st.form_submit_button("Create", type ="primary", use_container_width=True):
                    show_name_error = False
                    create_collection(new_collection_name, new_collection_type)

            if show_name_error:
                st.error('A collection with this name already exists. Please choose a different name.', icon="🚨")
    # COLLECTION PAGE

    if not st.session_state['create_popup']:
        st.title('Title')
        st.subheader('Ask')
        with st.form('ask_form'):
            text = st.text_area('Ask:', 'What are the three key pieces of advice for learning how to code?', label_visibility='collapsed')
            model = st.radio(
                "Select Model",
                ('DaVinci', 'GPT-3.5', 'GPT-4'),
                help="Choose the language model to answer the question with.\n1. DaVinci: Low cost, least capable. Still good for general use.\n2. GPT-3.5: Moderate cost, moderate capability.\n3. GPT-4: Expensive, highly capable, requires special OpenAI access."
            )
            submitted_ask = st.form_submit_button('Submit')
            if not openai_api_key.startswith('sk-'):
                st.warning('Please enter your OpenAI API key!', icon='⚠')
            if submitted_ask and openai_api_key.startswith('sk-'):
                generate_response(text, model)

        st.markdown('######')
        st.subheader('Upload')
        with st.form("upload_form", clear_on_submit=True):
            file = st.file_uploader('Upload files:', type=["pdf", "docx", "csv", "txt"], label_visibility='collapsed')
            submitted_doc = st.form_submit_button("Submit")
            if submitted_doc and file:
                upload_file(file)

        st.markdown('######')
        st.subheader('Saved Files')
        list_saved_files()


if __name__ == '__main__':
    main()