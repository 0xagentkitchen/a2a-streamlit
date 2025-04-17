import streamlit as st
from common.client.card_resolver import A2ACardResolver
from common.types import AgentCard

st.title("A2A Client - Agent Discovery")

st.header("Text Input Example")
user_text_input = st.text_input("Enter text here:")
text_submit_button = st.button("Submit")

if text_submit_button:
    st.write("You entered:")
    st.write(user_text_input)

st.header("Agent Card Resolver")
url_input = st.text_input("Enter a URL to resolve:")
url_submit_button = st.button("Resolve URL")

if url_input:
    resolver = A2ACardResolver()
    agent_card:AgentCard = resolver.resolve(url_input)
    st.subheader("Agent Card Details")
    st.write(f"Agent ID: {agent_card.agent_id}")
    st.write(f"Agent Name: {agent_card.name}")
    st.write(f"Agent Version: {agent_card.version}")

    st.divider()
    st.subheader("Raw Agent Card JSON")
    st.json(agent_card.model_dump())
else:
    st.write("Please enter a URL.")