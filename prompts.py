from langchain.prompts import PromptTemplate


template = """Use the following pieces of context to answer the question at the end. 
If you don't know the answer, just say sorry and that you couldn't find any info about it, don't try to make up an answer. 

{context}
Question: {question}
"""

QA_CHAIN_PROMPT = PromptTemplate.from_template(template)