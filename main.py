import dotenv
dotenv.load_dotenv()

from openai import OpenAI
import asyncio
import streamlit as st
from agents import Runner, SQLiteSession, InputGuardrailTripwireTriggered,OutputGuardrailTripwireTriggered
from models import UserAccountContext
from my_agent.triage_agent import triage_agent

client = OpenAI()

user_account_context = UserAccountContext(
    user_id="1",
    name="Hong Gil Dong",
    phone_number="010-1234-5678",
    email="hgd@gmail.com",
    dietary_restrictions="Vegetarian",
    food_preferences="Korean, Italian",
    cravings="Spicy food")

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "chat-history",
        "customer-support-memory.db",
    )

session = st.session_state["session"]

if "agent" not in st.session_state:
    st.session_state["agent"] = triage_agent

async def paint_history():
    messages = await session.get_items()
    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    if message["type"] =="message":
                        st.write(message["content"][0]["text"].replace("$", "\\$"))

asyncio.run(paint_history())

async def run_agent(message):
    with st.chat_message("ai"):
        text_placeholder  = st.empty()
        response = ""

        st.session_state["text_placeholder"] = text_placeholder

        try:
            stream = Runner.run_streamed(
                st.session_state["agent"],
                message,
                session=session,
                context=user_account_context,
            )

            async for event in stream.stream_events():
                if event.type == "raw_response_event":

                    if event.data.type == "response.output_text.delta":
                        response += event.data.delta
                        text_placeholder.write(response.replace("$", "\\$"))
                
                elif event.type == "agent_updated_stream_event":

                    if st.session_state["agent"].name != event.new_agent.name:
                        st.write(f"🤖 transfered from {st.session_state["agent"].name} to {event.new_agent.name}")
                        st.session_state["agent"] = event.new_agent
                        text_placeholder = st.empty()
                        st.session_state["text_placeholder"] = text_placeholder
                        response = ""
        
        except InputGuardrailTripwireTriggered:
            st.write("I can't answer that question. I'm here to help with restaurant recommendations, orders, and reservations. Please ask me something related to those topics!")

        except OutputGuardrailTripwireTriggered:
            st.write("Sorry, I generated a response that violated my guidelines. Let's try again!")
            st.session_state["text_placeholder"].empty()

message = st.chat_input("What would you like to eat today?")

if message:

    if message:
        with st.chat_message("human"):
            st.write(message)

with st.sidebar:
    reset = st.button("reset Memory")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))
    