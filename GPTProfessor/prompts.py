from langchain.prompts import PromptTemplate

# TODO: Create separate prompts for each model.
# DaVinci tends add additional unwanted info not from the sources
# GPT-3.5 tends to avoid including info that has already been found in the sources
# have stricter info requirements for davinci, looser for GPT-3.5

qa_template_davinci = """
Use the following sources to answer the question at the end.
Only include info that is found in the listed sources and is relevant to the question.
Do not include info from the sources that is obviously incorrect, as it is likely an error.
Make sure to incude all relevant info from the sources, but keep your answer concise.
If you find a variety of info, please order them from most relevant to least.
If you cannot find relevant info, just say sorry and that you couldn't find any info about it, don't try to make up an answer.
You do not need to summarize your answer.

Sources:
{summaries}
Question: {question}
"""
QA_PROMPT_DAVINCI = PromptTemplate(
    template=qa_template_davinci, input_variables=["summaries", "question"]
)


qa_template_gpt_35 = """
Use the following sources to answer the question at the end.
Only include info that is found in the listed sources and is relevant to the question.
Do not include info from the sources that is obviously incorrect, as it is likely an error.
Make sure to incude all relevant info from the sources, but keep your answer concise.
If you find a variety of info, please order them from most relevant to least.
If you cannot find relevant info, just say sorry and that you couldn't find any info about it, don't try to make up an answer.
You do not need to summarize your answer.

Sources:
{summaries}
Question: {question}
"""
QA_PROMPT_GPT_35 = PromptTemplate(
    template=qa_template_gpt_35, input_variables=["summaries", "question"]
)


doc_prompt_template = "Input: {page_content}\Question: {source}"
DOC_PROMPT = PromptTemplate(
    template=doc_prompt_template, input_variables=["page_content", "source"]
)


quiz_template_gpt_35 = """
Use the following sources to create up to 10 study questions for the topic at the end.
You must include an answer for each question.
Only create questions that have solutions contained in the listed sources and is relevant to the topic.
Do not include info from the sources that is obviously incorrect, as it is likely an error.
If the sources do not contain relevant info on the topic, just say sorry and that you couldn't create questions for this topic.

Keep your output in this format:

Questions:
1.
2.
3.


Answers:
1.
2.
3.

Sources:
{summaries}
Topic: {question}
"""
QUIZ_PROMPT_GPT_35 = PromptTemplate(
    template=quiz_template_gpt_35, input_variables=["summaries", "question"]
)