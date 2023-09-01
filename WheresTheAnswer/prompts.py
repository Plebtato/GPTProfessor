from langchain.prompts import PromptTemplate


qa_chain_template = """Use the following sources to answer the question at the end. Only include info that is found in the listed sources.
If you don't know the answer, just say sorry and that you couldn't find any info about it, don't try to make up an answer. Don't mention the sources itself, just state the info.

Sources:
{summaries}
Question: {question}
"""

QA_CHAIN_PROMPT = PromptTemplate(
    template=qa_chain_template, input_variables=["summaries", "question"]
)

doc_prompt_template = "Input: {page_content}\Question: {source}"

DOC_PROMPT = PromptTemplate(
    template=doc_prompt_template, input_variables=["page_content", "source"]
)
