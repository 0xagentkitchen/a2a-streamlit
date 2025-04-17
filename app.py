import streamlit as st
from common.client.card_resolver import A2ACardResolver
from common.types import AgentCard, A2AClientJSONError

st.title("A2A Client - Agent Discovery")

st.header("Agent Card Resolver")
url_input = st.text_input("Enter root URL:")
use_wellknown = st.checkbox("Add .well-known folder", value=True)

if url_input:
    try:
        if use_wellknown:
            resolver = A2ACardResolver(base_url=url_input)
        else:
            resolver = A2ACardResolver(base_url=url_input, agent_card_path="agent.json")
        
        agent_card:AgentCard = resolver.get_agent_card()
        st.subheader("Agent Card")
        st.json(agent_card.model_dump())
    except ValueError as e:
        st.error(f"Invalid input: {str(e)}")
    except A2AClientJSONError as e:
        st.error(f"Failed to fetch or parse agent card: {str(e)}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
else:
    st.info("Please enter a URL.")