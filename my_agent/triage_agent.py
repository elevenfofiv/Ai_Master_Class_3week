import streamlit as st
from agents import (
    Agent,
    RunContextWrapper,
    input_guardrail,
    Runner,
    GuardrailFunctionOutput,
    handoff,
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.extensions import handoff_filters
from models import UserAccountContext, InputGuardRailOutput, HandoffData
from my_agent.menu_agent import menu_agent
from my_agent.order_agent import order_agent
from my_agent.reservation_agent import reservation_agent
from my_agent.complain_agent import complain_agent

input_guardrail_agent = Agent(
    name="Input Guardrail Agent",
    instructions="""
    You are an input guardrail agent that evaluates user input to determine if it is on-topic or off-topic for a restaurant recommendation system. 
    Your task is to analyze the user's input and classify it as either on-topic or off-topic based on its relevance to restaurant recommendations, menu preferences, dietary restrictions, and related topics.
    
    When evaluating the user's input, consider the following:
    - On-topic input includes queries about restaurant recommendations, menu preferences, dietary restrictions, food cravings, and related topics.
    - Off-topic input includes queries that are unrelated to restaurant recommendations, such as questions about unrelated subjects (e.g., sports, politics) or personal information that is not relevant to the restaurant context.
    - If the user's input includes swear words or inappropriate language, classify it as off-topic and provide a reason for the classification.
    
    Your response should be concise and focused on providing a clear classification of the user's input as either on-topic or off-topic.
    """,
    output_type=InputGuardRailOutput,
)

@input_guardrail
async def off_topic_guardrail(
    wapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
    input: str,    
):
    result = await Runner.run(
        input_guardrail_agent,
        input,
        context=wapper.context,
    )

    return GuardrailFunctionOutput(
        output_infor=result.final_output,
        tripwire_triggered=result.final_output.is_off_topic,
    )

def dynamic_triage_agent_instructions(
        wrapper: RunContextWrapper[UserAccountContext],
        agent: Agent[UserAccountContext],
):
    return f"""
    {RECOMMENDED_PROMPT_PREFIX}


    You are a triage agent that evaluates user input and determines the appropriate next steps for a restaurant recommendation system. 
    You will receive user input about their food preferences, dietary restrictions, and any specific cravings they have. 
    Based on this information, you will determine whether to provide a menu recommendation, create an order, make a table reservation, or hand off to a human agent for further assistance.
    
    When evaluating the user's input, consider the following:
    - If the user's input includes specific menu preferences or dietary restrictions, provide a personalized menu recommendation.
    - If the user's input indicates a desire to place an order, create a personalized order based on their preferences and restrictions.
    - If the user's input suggests they want to make a reservation, generate a personalized table reservation with relevant details.
    - If the user's input is unclear or requires human judgment, hand off to a human agent for further assistance.
    
    Your response should be concise and focused on providing clear next steps based on the user's input.
    """

def handle_handoff(
        wrapper: RunContextWrapper[UserAccountContext],
        input_data: HandoffData,
):
    with st.sidebar:
        st.write(
            f"""
            Handing off to {input_data.to_agent_name}
            Reason: {input_data.reason}
            Menu Description: {input_data.menu_description}
            Order: {input_data.order}
            Table Reservation: {input_data.table_reservation}
            """
        )

def make_handoff(agent):
    return handoff(
    agent=agent,
    input_type=HandoffData,
    input_filter=handoff_filters.remove_all_tools,
    )

triage_agent = Agent(
    name="Triage Agent",
    instructions=dynamic_triage_agent_instructions,
    input_guardrails=[off_topic_guardrail],
    handoffs=[make_handoff(menu_agent), make_handoff(order_agent), make_handoff(reservation_agent)],
)
