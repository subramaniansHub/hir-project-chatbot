import streamlit as st
import random
import time
from logic import ExperimentManager, ScriptManager
import json

# Page Config
st.set_page_config(
    page_title="Glow & Co. Support",
    page_icon="✨",
    layout="centered"
)

# Load CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

# Initialize Logic
if 'experiment' not in st.session_state:
    st.session_state.experiment = ExperimentManager()
    st.session_state.script = ScriptManager()
    st.session_state.current_step = 0 # Track script index
    
    # Assign Condition
    if 'condition' not in st.session_state:
        st.session_state.condition = random.choice(['High_Empathy', 'High_Expertise'])
        st.session_state.experiment.log_assignment(st.session_state.condition)

if 'messages' not in st.session_state:
    st.session_state.messages = []
    # Kick off the conversation automatically
    # We might have multiple initial messages (non-questions) to show at start
    while True:
        step_data = st.session_state.script.get_step(st.session_state.current_step, st.session_state.condition)
        if not step_data:
            break
            
        if step_data["type"] in ["message", "section_header"]:
            # It's a statement, so we act immediately
            st.session_state.messages.append({
                "role": "assistant", 
                "content": step_data["text"],
                "image": step_data["image"],
                "type": step_data["type"]
            })
            st.session_state.current_step += 1
        else:
            # It is a question, so we wait for user input
            # Add the question to history so it renders
            st.session_state.messages.append({
                "role": "assistant", 
                "content": step_data["text"],
                "image": step_data["image"],
                "type": step_data["type"]
            })
            st.session_state.current_step += 1 # Advance past the question so next loop we wait for answer
            break


# Header with Avatar
col1, col2 = st.columns([1, 4])
with col1:
    st.image("assets/avatar.png", use_container_width=True)
with col2:
    st.title("Glow & Co. Support")
    st.caption("Your personal skincare assistant")

# Display Chat History
for message in st.session_state.messages:
    if message.get("type") == "section_header":
         st.divider()
         st.caption(message["content"])
    else:
        with st.chat_message(message["role"], avatar="assets/avatar.png" if message["role"] == "assistant" else None):
            st.markdown(message["content"])
            if message.get("image"):
                st.image(message["image"], width=300)

# Chat Input logic
# Only show input if we are NOT finished
total_steps = st.session_state.script.get_total_steps()
is_finished = st.session_state.current_step >= total_steps

if not is_finished:
    if prompt := st.chat_input("Type your response..."):
        # 1. User speaks
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Force a rerun to update the UI immediately with user message
        st.rerun()

else:
    # If finished, maybe show survey
    st.session_state.show_survey = True

# Logic to Process Next Bot Response (runs after rerun)
# If the last message was from User, we need to fetch the NEXT bot step(s)
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    
    with st.chat_message("assistant", avatar="assets/avatar.png"):
        message_placeholder = st.empty()
        
        # Loop through potentially multiple consecutive bot messages (e.g. statement -> statement -> question)
        while True:
            step_data = st.session_state.script.get_step(st.session_state.current_step, st.session_state.condition)
            
            if not step_data:
                break
                
            # Simulate typing for text
            full_response = ""
            with st.spinner("Typing..."):
                time.sleep(0.8) # Small delay
                
            # Render content
            if step_data["type"] == "section_header":
                 st.divider()
                 st.caption(step_data["text"])
            else:
                st.markdown(step_data["text"])
                if step_data["image"]:
                    st.image(step_data["image"], width=300)
            
            # Append to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": step_data["text"],
                "image": step_data["image"],
                "type": step_data["type"]
            })
            
            st.session_state.current_step += 1
            
            # If this was a question, we stop and wait for user (break loop)
            # If it was a message/header, effectively we just printed it, and now we loop to the next item immediately
            if step_data["type"] == "question":
                st.rerun() # Rerun to remove spinner and ready input
                break 
    st.subheader("Feedback Survey")
    with st.form("feedback_form"):
        st.write("How was your experience?")
        
        q1 = st.slider("How knowledgeable was the assistant?", 1, 5, 3)
        q2 = st.slider("How empathetic was the assistant?", 1, 5, 3)
        q3 = st.text_area("Any other comments?")
        
        submitted = st.form_submit_button("Submit Feedback")
        if submitted:
            # Here we will send data to GSheets
            from data_handler import DataHandler
            
            # Prepare data pakcage
            session_data = {
                "session_id": st.session_state.experiment.session_id,
                "condition": st.session_state.condition,
                "chat_history": st.session_state.messages,
                "survey_knowledge": q1,
                "survey_empathy": q2,
                "survey_comments": q3
            }
            
            logger = DataHandler()
            success = logger.log_data(session_data)
            
            if success:
                st.success("Thank you for your feedback! Your session is complete.")
            else:
                st.error("There was an error saving your response. Please contact the administrator.")
            # st.stop()
