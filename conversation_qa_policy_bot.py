import logging
import requests
from streamlit_chat import message
from trubrics.integrations.streamlit import FeedbackCollector
import streamlit as st

FAST_API_SERVING_URL = st.secrets["FAST_API_SERVING_URL"]

def ask_question(input):
    url = f'{FAST_API_SERVING_URL}/conversation_qa_bot_with_guardrails/?input_string={input}'
    logging.info(f"URL: {url}")
    response = requests.request(method='GET', url=url)
    if response.status_code != 200:
        raise Exception(f'Request failed with status {response.status_code}, {response.text}')
    return response.json()


# Setting page title and header
st.set_page_config(page_title="LLM-Chatbot", page_icon=":robot_face:")
st.markdown("<h1 style='text-align: center;'>LLM based Government Policy Bot</h1>", unsafe_allow_html=True)

# Initialise session state variables
if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
if 'model_name' not in st.session_state:
    st.session_state['model_name'] = []

# Sidebar - let user choose model, show total cost of current conversation, and let user clear the current conversation
st.sidebar.title("Sidebar")
counter_placeholder = st.sidebar.empty()
clear_button = st.sidebar.button("Clear Conversation", key="clear")

# reset everything
if clear_button:
    st.session_state['generated'] = []
    st.session_state['past'] = []
    st.session_state['messages'] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
    st.session_state['model_name'] = []
    counter_placeholder.write(f"Total cost of this conversation: ${st.session_state['total_cost']:.5f}")


# generate a response
def generate_response(prompt):
    st.session_state['messages'].append({"role": "user", "content": prompt})
    with st.spinner('Generating...'):
        completion = ask_question(prompt)
        response = completion["processed_string"][0]["answer"]
        st.session_state['messages'].append({"role": "assistant", "content": response})
    return response


# container for chat history
response_container = st.container()
# container for text box
container = st.container()

collector = FeedbackCollector(
    project="default",
    email=st.secrets["TRUBRICS_EMAIL"],  # Store your Trubrics credentials in st.secrets:
    password=st.secrets["TRUBRICS_PASSWORD"],  # https://blog.streamlit.io/secrets-in-sharing-apps/
)

with container:
    with st.form(key='my_form', clear_on_submit=True):
        user_input = st.text_area("User:", key='input', height=100)
        submit_button = st.form_submit_button(label='Submit')

    if submit_button and user_input:
        output = generate_response(user_input)
        st.session_state['past'].append(user_input)
        st.session_state['generated'].append(output)
        st.session_state['model_name'].append("llm-qa-government-policy-bot")


def post_feedback_data(feedback: dict, question: str, answer: str):
    # Define the URL of the FastAPI endpoint
    url = f"{FAST_API_SERVING_URL}/process_feedback"  # Replace with your actual endpoint URL

    # Define the request data
    metadata = {}
    metadata.update(feedback["metadata"])
    metadata.update({'component_name': feedback["component"]})
    request_data = {
        "model_name": feedback["model"],
        "response_type": feedback["user_response"]["type"],
        "response_score": str(feedback["user_response"]["score"]),
        "response_text": feedback["user_response"]["text"],
        "user_id": "streamlit_app_test_1",
        "metadata": str(metadata),
        "question": str(question),
        "answer": str(answer)
    }
    # Send a POST request to the API
    response = requests.post(url, json=request_data)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # logging.info the response JSON
        logging.info(response.json())
    else:
        # logging.info an error message if the request was not successful
        logging.info(f"Error: {response.status_code}")
        logging.info(response.text)


if st.session_state['generated']:
    with response_container:
        for i in range(len(st.session_state['generated'])):
            message(st.session_state["past"][i], is_user=True, key=str(i) + '_user')
            message(st.session_state["generated"][i], key=str(i))
            feedback = collector.st_feedback(
                component="LLM Feedback Demo",
                feedback_type="thumbs",
                model="llm-qa-government-policy-bot",
                open_feedback_label="[Optional] Provide additional feedback",
                key=f"feedback-{i}"  # each key should have a unique id
            )
            if feedback != None:
                logging.info(f"Feedback received: {str(feedback)}")
                post_feedback_data(feedback, st.session_state['messages'][-2], st.session_state['messages'][-1])
