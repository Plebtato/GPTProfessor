from langchain.prompts import PromptTemplate


qa_chain_template = """
Use the following sources to answer the question at the end.
Only include info that is found in the listed sources, but if something is obviously wrong, don't include it.
Make sure to incude all relevant info, but keep your answer concise.
If you don't know the answer, just say sorry and that you couldn't find any info about it, don't try to make up an answer.
You do not need to summarize your answer.

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
