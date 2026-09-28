import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="My Local AI", page_icon="🤖")
st.title("Local Fine-Tuned Qwen 2.5")

client = OpenAI(base_url="http://127.0.0.1:8080/v1", api_key="empty")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a coding question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="default_model",
            messages=st.session_state.messages,
            stream=True,
            max_tokens=800
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
