import os
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import BaseMessage
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from typing import TypedDict, Annotated
from dotenv import load_dotenv
import sqlite3

load_dotenv()

API_KEY = os.getenv("API_KEY")
llm = ChatGroq(model_name="llama-3.3-70b-versatile", api_key=API_KEY)


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def chat_node(state: ChatState):
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


conn = sqlite3.connect(database="chatbot.db", check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)
graph = StateGraph(ChatState)

graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)

# Example of invoking the chatbot and streaming responses

# for message_chunk, metadata in chatbot.stream(
#     {"messages": [HumanMessage(content="What is recipe for pasta?")]},
#     config={"configurable": {"thread_id": "thread-001"}},
#     stream_mode="messages",
# ):
#     if message_chunk.content:
#         print(message_chunk.content, end=" ", flush=True)

# CONFIG = {"configurable": {"thread_id": "thread-001"}}
# response = chatbot.invoke(
#     {"messages": [HumanMessage(content="What is my name?")]}, config=CONFIG
# )

# print(response)


# retrive the all unique thread ids from the database
def retrieve_thread_ids():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    return list(all_threads)
