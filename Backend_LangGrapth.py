import os
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import BaseMessage
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq

from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool


from typing import TypedDict, Annotated
from dotenv import load_dotenv
import sqlite3, requests

load_dotenv()

API_KEY = os.getenv("API_KEY")
llm = ChatGroq(model_name="openai/gpt-oss-120b", api_key=API_KEY)


search_tool = DuckDuckGoSearchRun(region="us-en")


@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}

        return {
            "first_num": first_num,
            "second_num": second_num,
            "operation": operation,
            "result": result,
        }
    except Exception as e:
        return {"error": str(e)}


@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA')
    using Alpha Vantage with API key in the URL.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=39T31NPL91REF88I"
    r = requests.get(url)
    return r.json()


tools = [search_tool, calculator, get_stock_price]
llm_with_tools = llm.bind_tools(tools)


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def chat_node(state: ChatState):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


tool_node = ToolNode(tools)

conn = sqlite3.connect(database="chatbot.db", check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)

# graph.add_node("chat_node", chat_node)
# graph.add_edge(START, "chat_node")
# graph.add_edge("chat_node", END)

graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chat_node")
graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge("tools", "chat_node")


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


def delete_thread(thread_id: str):
    cursor = conn.cursor()

    tables = [
        "checkpoints",
        "writes",
    ]

    for table in tables:
        try:
            cursor.execute(
                f"""
                DELETE FROM {table}
                WHERE thread_id = ?
                """,
                (thread_id,),
            )
        except Exception:
            pass

    conn.commit()
