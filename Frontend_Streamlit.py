import streamlit as st
from Backend_LangGrapth import chatbot
from langchain.messages import HumanMessage

CONFIG = {"configurable": {"thread_id": "thread-001"}}

# Initialize session state for message history and hero section visibility
if "message_hitory" not in st.session_state:
    st.session_state["message_hitory"] = []
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
    response = chatbot.invoke(
        {"messages": [HumanMessage(content=user_input)]}, config=CONFIG
    )
    ai_message = response["messages"][-1].content

    # Append AI response to message history
    st.session_state["message_hitory"].append(
        {"role": "assistant", "content": ai_message}
    )
    with st.chat_message("assistant"):
        st.text(ai_message)
