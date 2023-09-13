import config
import utils
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationSummaryBufferMemory
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from documents import DocumentCollection
from prompts import CHAT_AGENT_PROMPT
from langchain.agents.agent_toolkits import create_retriever_tool
from langchain.agents import AgentExecutor
from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent


def generate_chat_response(
    text,
    collection: DocumentCollection,
    message_history: StreamlitChatMessageHistory,
    model,
):
    model_name, token_limit_source, token_limit_max = utils.get_model(model)

    llm = ChatOpenAI(
        temperature=0.8, openai_api_key=config.openai_api_key, model_name=model_name
    )

    memory = ConversationSummaryBufferMemory(
        chat_memory=message_history,
        llm=llm,
        max_token_limit=token_limit_max,
        return_messages=True
        # memory_key="chat_history",
    )

    retriever = collection.vector_db.as_retriever(search_kwargs={"k": 3})
    tool = create_retriever_tool(
        retriever,
        "search_collection",
        "Searches and returns documents regarding the user's questions.",
    )
    tools = [tool]
    agent = OpenAIFunctionsAgent(llm=llm, tools=tools, prompt=CHAT_AGENT_PROMPT)
    agent_executor = AgentExecutor(
        agent=agent, tools=tools, memory=memory, verbose=True
    )
    return agent_executor({"input": text})["output"]
