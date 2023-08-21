from langchain.prompts import PromptTemplate


template = """Use the following pieces of context to answer the question at the end. 
If you don't know the answer, just say that you don't know, don't try to make up an answer. 
Keep the answer as concise as possible. 
{context}
Question: {question}
"""

QA_CHAIN_PROMPT = PromptTemplate.from_template(template)