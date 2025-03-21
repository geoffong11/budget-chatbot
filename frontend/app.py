import streamlit as st
import requests

# Function to handle chatbot conversation
def get_bot_response(user_message):
    # sending data to Flask API
    flask_url = 'http://backend:8080/query'
    data = {'user_input': user_message}
    try:
        response = requests.post(flask_url, json=data)
        if response.status_code == 200:
            bot_response = response.json().get('reply')
        else:
            bot_response = 'Error: Unable to connect to backend.'
    except Exception as e:
        bot_response = f'Error: {str(e)}'
    print(bot_response)
    return bot_response

# Streamlit UI Setup
st.title("Singapore Budget 2024 AI Chatbot assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    if message.startswith("You:"):
        # Display user message with a border
        st.markdown(f'<div style="border: 2px solid #4CAF50; padding: 10px; margin: 5px; border-radius: 5px;">{message}</div>', unsafe_allow_html=True)
    else:
        # Display bot's response with a border
        st.markdown(f'<div style="border: 2px solid #2196F3; padding: 10px; margin: 5px; border-radius: 5px;">{message}</div>', unsafe_allow_html=True)

# Input form to prevent rerun issues
with st.form(key="chat_form"):
    user_input = st.text_input("You:", key="user_input")
    submitted = st.form_submit_button("Send")

# Process input when user submits
if submitted and user_input:
    response = get_bot_response(user_input)
    st.session_state.messages.append(f"You: {user_input}")
    st.session_state.messages.append(f"Budget 2024 assistant: {response}")

    st.rerun()  # Refresh UI to display new messages