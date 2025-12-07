import streamlit as st
from router import rl
from faq import ingest_faq_data,faq_chain
from sql import sql_chain
from pathlib import Path

st.title("E Commerce Chatbot")

faqs_path = Path(__file__).parent / "resources/faq_data.csv"
ingest_faq_data(faqs_path)
db_path = Path(__file__).parent / "db.sqlite"

def ask(query):
    route = rl(query, limit=1)
    if route.name == "faq":
        return faq_chain(query)
    elif route.name == "sql":
        return sql_chain(query)
    else:
        print(route.name)
        return "I'm sorry, I don't have an answer for that."

query = st.chat_input("Ask a question about our products or services:")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

if query:
    with st.chat_message("user"):
        st.markdown(query, unsafe_allow_html=True)
        st.session_state["messages"].append({"role": "user", "content": query})

    response = ask(query)
    with st.chat_message("assistant"):
        st.markdown(response, unsafe_allow_html=True)
        st.session_state["messages"].append({"role": "assistant", "content": response})