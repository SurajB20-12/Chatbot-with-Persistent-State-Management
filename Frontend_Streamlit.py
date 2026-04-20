import streamlit as st
from Backend_LangGrapth import chatbot, retrieve_thread_ids
from langchain.messages import HumanMessage
import uuid  # used for creating unique thread IDs for conversations


# ----------------------------------utility functions-----------------------------------
# this function generates unique thread id for every new chat
def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

    # This is invoked when the user clicks on the "New Chat" button in the sidebar.
    # It clears the message history and generates a new thread ID for the new conversation.


def reset_chat():
    thread_id = generate_thread_id()
    st.session_state["thread_id"] = thread_id
    add_threads(thread_id)
    st.session_state["message_hitory"] = []


def add_threads(thread_id):
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)

    # below function accept a thread_id and return messages(HumanMessage and AIMessages)
    # that stored in thread with that thread_id.
    # This is used to display the chat history when user clicks on a thread in the sidebar.


def load_conversation(thread_id):
    state = chatbot.get_state(config={"configurable": {"thread_id": thread_id}})
    return state.values.get("messages", [])


# -----------------------------------Session State Initialization-----------------------

# Initialize session state for message history and hero section visibility
if "message_hitory" not in st.session_state:
    st.session_state["message_hitory"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = retrieve_thread_ids()

add_threads(st.session_state["thread_id"])

# -----------------------------------Sidebar UI-----------------------------------------
st.sidebar.title("LangGraph Chatbot")
if st.sidebar.button("New Chat"):
    reset_chat()
st.sidebar.header("My Conversations")


for thread in st.session_state["chat_threads"]:
    if st.sidebar.button(str(thread)):
        st.session_state["thread_id"] = thread
        messages = load_conversation(thread)

        # here we are format the message into a list of dict with role and content,
        # because the load_conversation return a list of HumanMessage and AIMessages objects,
        # but we want to store the message history in session state as a list of dict with role and content,
        # so we need to convert the HumanMessage and AIMessages objects into dict with role and content.
        temp_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            else:
                role = "assistant"
            temp_messages.append({"role": role, "content": msg.content})
        st.session_state["message_hitory"] = temp_messages


# -------------------------------------Main UI--------------------------------------
if "show_hero" not in st.session_state:
    st.session_state["show_hero"] = True

# Display the hero section if it's enabled
if st.session_state["show_hero"]:
    st.markdown(
        """
        <div style="text-align: center; margin-top: 20px; margin-bottom: 20px;">
            <h1>How Are You?</h1>
            <h3>How can I help you Today?</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Display chat history
for message in st.session_state["message_hitory"]:
    with st.chat_message(message["role"]):
        st.text(message["content"])

# Chat input section
user_input = st.chat_input("Type Here")

if user_input:
    # Hide the hero section after the first input
    st.session_state["show_hero"] = False

    # Append user input to message history
    st.session_state["message_hitory"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.text(user_input)

    # Get chatbot response
    # response = chatbot.invoke(
    #     {"messages": [HumanMessage(content=user_input)]}, config=CONFIG
    # )
    # ai_message = response["messages"][-1].content

    # Append AI response to message history
    # st.session_state["message_hitory"].append(
    #     {"role": "assistant", "content": ai_message}
    # )
    CONFIG = {"configurable": {"thread_id": st.session_state["thread_id"]}}
    with st.chat_message("assistant"):
        ai_message = st.write_stream(
            message_chunk.content
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages",
            )
        )

    st.session_state["message_hitory"].append(
        {"role": "assistant", "content": ai_message}
    )
