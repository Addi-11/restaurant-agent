import streamlit as st
from main import process_chat

st.set_page_config(page_title="FoodieSpot Assistant", layout="wide")

st.title("🍽️ FoodieSpot - Your Restaurant Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_message = st.chat_input("Ask me anything about restaurants...")

if user_message:
    st.session_state.messages.append({"role": "user", "content": user_message})
    with st.chat_message("user"):
        st.markdown(user_message)

    response = process_chat(user_message, st.session_state.messages)
    # formatted response to string
    assistant_response = response if isinstance(response, str) else str(response)

    st.session_state.messages.append(
        {"role": "assistant", "content": assistant_response}
    )
    with st.chat_message("assistant"):
        st.markdown(assistant_response)
