import streamlit as st
from common.client import A2AClient, A2ACardResolver
from common.types import AgentCard, A2AClientJSONError, TaskState, Message, TextPart, FilePart, FileContent
import uuid
import asyncio
from typing import List

st.set_page_config(layout="wide")
st.title("A2A Client")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "client" not in st.session_state:
    st.session_state.client = None
if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex
if "agent_card" not in st.session_state:
    st.session_state.agent_card = None

# Sidebar - Agent Card Resolution
st.sidebar.header("Agent Card Resolution")
card_url_input = st.sidebar.text_input("Enter Agent Card URL:")
use_wellknown = st.sidebar.checkbox("Add .well-known folder", value=True)
resolve_button = st.sidebar.button("Resolve Agent Card")

if resolve_button and card_url_input:
    try:
        if use_wellknown:
            resolver = A2ACardResolver(base_url=card_url_input)
        else:
            resolver = A2ACardResolver(base_url=card_url_input, agent_card_path="agent.json")
        
        agent_card:AgentCard = resolver.get_agent_card()
        st.session_state.agent_card = agent_card
        st.sidebar.success("Successfully resolved agent card!")
        
        # Display agent card information
        st.sidebar.subheader("Agent Card")
        st.sidebar.json({
            "name": agent_card.name,
            "version": agent_card.version,
            "description": agent_card.description,
            "url": agent_card.url,
            "capabilities": {
                "streaming": agent_card.capabilities.streaming,
                "pushNotifications": agent_card.capabilities.pushNotifications
            }
        })
        
        # Add copy button for the agent URL
        st.sidebar.text("Agent URL (click to copy):")
        st.sidebar.code(agent_card.url, language=None)
        
    except ValueError as e:
        st.sidebar.error(f"Invalid input: {str(e)}")
    except A2AClientJSONError as e:
        st.sidebar.error(f"Failed to fetch or parse agent card: {str(e)}")
    except Exception as e:
        st.sidebar.error(f"An unexpected error occurred: {str(e)}")

# Main frame - Agent Connection and Chat
st.header("Agent Connection")
col1, col2 = st.columns([3, 1])
with col1:
    agent_url = st.text_input("Enter Agent URL:")
with col2:
    connect_button = st.button("Connect to Agent")

if connect_button and agent_url:
    try:
        st.session_state.client = A2AClient(url=agent_url)
        st.success("Successfully connected to agent!")
    except Exception as e:
        st.error(f"Failed to connect to agent: {str(e)}")

# Chat interface
if st.session_state.client:
    st.header("Chat")
    
    # Create a container for the chat history
    chat_container = st.container()
    
    # Display chat history in the container
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                with st.chat_message("user", avatar="👤"):
                    st.write(message["content"])
            else:
                with st.chat_message("agent", avatar="🤖"):
                    st.write(message["content"])

    # Chat input
    user_input = st.chat_input("Type your message here...")

    if user_input:
        # Add user message to chat
        user_message = {"role": "user", "content": user_input}
        st.session_state.messages.append(user_message)

        # Show user message immediately
        with st.chat_message("user", avatar="👤"):
            st.write(user_input)

        # Prepare message parts for the API
        parts: List[TextPart | FilePart] = []
        if user_input:
            parts.append(TextPart(text=user_input))

        # Create task payload
        task_id = uuid.uuid4().hex
        payload = {
            "id": task_id,
            "sessionId": st.session_state.session_id,
            "message": {
                "role": "user",
                "parts": parts
            },
            "acceptedOutputModes": ["text"]
        }

        try:
            # Send message to agent
            with st.chat_message("agent", avatar="🤖"):
                message_placeholder = st.empty()
                full_response = ""

                # Check if we have streaming capability from the agent card
                is_streaming = (st.session_state.agent_card and 
                              st.session_state.agent_card.capabilities.streaming)
                
                is_streaming = False # Disable streaming for now
                if is_streaming:
                    # Handle streaming response
                    async def process_stream(message_placeholder):
                        response_stream = await st.session_state.client.send_task_streaming(payload)
                        full_response = ""
                        async for result in response_stream:
                            if result.result and result.result.artifacts:
                                for artifact in result.result.artifacts:
                                    for part in artifact.parts:
                                        if part.type == "text":
                                            full_response += part.text
                                            message_placeholder.write(full_response)
                        return full_response

                    full_response = asyncio.run(process_stream(message_placeholder))
                else:
                    # Handle non-streaming response
                    response = asyncio.run(st.session_state.client.send_task(payload))
                    print("---------------- Response ----------------")
                    print("Result:", response.result)
                    print(response)
                    print("---------------- /Response ----------------")
                    if response.result and response.result.artifacts:
                        for artifact in response.result.artifacts:
                            for part in artifact.parts:
                                if part.type == "text":
                                    full_response += part.text
                        message_placeholder.write(full_response)

                # Add agent response to chat history
                if full_response:
                    st.session_state.messages.append({
                        "role": "agent",
                        "content": full_response
                    })

        except Exception as e:
            st.error(f"Error communicating with agent: {str(e)}")

elif not agent_url:
    st.info("Enter an Agent URL and connect to start chatting.")