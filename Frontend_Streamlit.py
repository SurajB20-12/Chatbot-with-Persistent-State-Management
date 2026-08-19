import streamlit as st
from Backend_LangGrapth import chatbot, retrieve_thread_ids, delete_thread
from langchain.messages import HumanMessage, AIMessage, ToolMessage
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
    st.session_state["message_history"] = []


def add_threads(thread_id):
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)


def remove_thread(thread_id):

    delete_thread(thread_id)

    if thread_id in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].remove(thread_id)

    if st.session_state["thread_id"] == thread_id:

        st.session_state["thread_id"] = generate_thread_id()
        st.session_state["message_history"] = []

    st.rerun()

    # below function accept a thread_id and return messages(HumanMessage and AIMessages)
    # that stored in thread with that thread_id.
    # This is used to display the chat history when user clicks on a thread in the sidebar.


def load_conversation(thread_id):
    state = chatbot.get_state(config={"configurable": {"thread_id": thread_id}})
    return state.values.get("messages", [])


# -----------------------------------Session State Initialization-----------------------

# Initialize session state for message history and hero section visibility
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

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
    col1, col2 = st.sidebar.columns([5, 1])

    with col1:
        if st.button(str(thread), key=f"chat_{thread}"):

            st.session_state["thread_id"] = thread

            messages = load_conversation(thread)

            temp_messages = []

            for msg in messages:
                role = "user" if isinstance(msg, HumanMessage) else "assistant"

                temp_messages.append(
                    {
                        "role": role,
                        "content": msg.content,
                    }
                )

            st.session_state["message_history"] = temp_messages

    with col2:
        if st.button("❌", key=f"delete_{thread}"):

            remove_thread(thread)


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
for message in st.session_state["message_history"]:
    with st.chat_message(message["role"]):
        st.text(message["content"])

# Chat input section
user_input = st.chat_input("Type Here")

if user_input:
    # Hide the hero section after the first input
    st.session_state["show_hero"] = False

    # Append user input to message history
    st.session_state["message_history"].append({"role": "user", "content": user_input})
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
    # with st.chat_message("assistant"):
    #     # ai_message = st.write_stream(
    #     #     message_chunk.content
    #     #     for message_chunk, metadata in chatbot.stream(
    #     #         {"messages": [HumanMessage(content=user_input)]},
    #     #         config=CONFIG,
    #     #         stream_mode="messages",
    #     #     )
    #     # )
    #     def ai_only_stream():
    #         for message_chunk, metadata in chatbot.stream(
    #             {"messages": [HumanMessage(content=user_input)]},
    #             config=CONFIG,
    #             stream_mode="messages",
    #         ):
    #             if isinstance(message_chunk, AIMessage):
    #                 yield message_chunk.content

    #     ai_message = st.write_stream(ai_only_stream())
    # st.session_state["message_history"].append(
    #     {"role": "assistant", "content": ai_message}
    # )
    with st.chat_message("assistant"):
        # Use a mutable holder so the generator can set/modify it
        status_holder = {"box": None}

        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages",
            ):
                # Lazily create & update the SAME status container when any tool runs
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )

                # Stream ONLY assistant tokens
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content

        ai_message = st.write_stream(ai_only_stream())

        # Finalize only if a tool was actually used
        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool finished", state="complete", expanded=False
            )

    # Save assistant message
    st.session_state["message_history"].append(
        {"role": "assistant", "content": ai_message}
    )
