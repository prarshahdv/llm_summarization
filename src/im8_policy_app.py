import sys
import sqlite3

from nemoguardrails.rails.llm.context_var_chain import ContextVarChain

__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
connection = sqlite3.connect('../cache.db', timeout=1000)
connection = sqlite3.connect('../table', timeout=1000)
connection = sqlite3.connect('../main', timeout=1000)

import logging
import streamlit as st
import os
import fitz  # PyMuPDF
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.embeddings import OpenAIEmbeddings
from langchain import PromptTemplate
import asyncio
from langchain.chains.constitutional_ai.models import ConstitutionalPrinciple
from utils.constitutional_chain import ConstitutionalChain

logging.basicConfig(level=logging.INFO)

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
st.set_page_config(page_title='Government Policy Docs')
st.title('🦜🔗 Government Policy Bot')

# client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory="db/"))
# collection = client.create_collection(name="policies")

# initialize default variables
st.session_state.QA = []
LLM_DATA = {}


def read_pdf_to_string(dir_path):
    pdf_to_str = []
    for file_path in os.listdir(dir_path):
        doc = fitz.open(os.path.join(dir_path, file_path))
        text = ""
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text += page.get_text()
        pdf_to_str.append(text)
    return pdf_to_str


async def get_rails():
    import nemoguardrails
    config = nemoguardrails.RailsConfig.from_path("../config/")
    return nemoguardrails.LLMRails(config)


def get_principles():
    return {'offensive': ConstitutionalPrinciple(critique_request='Discuss whether the assistant said anything that may be interpreted as offensive or harmful. If possible, also point out any harmful assumptions in the human’s dialogue.', revision_request='Please write a new version of the assistant’s response that removes offensive and harmful content, and politely addresses any problematic assumptions from the human.', name='offensive'),
     'harmful6': ConstitutionalPrinciple(critique_request='Discuss whether the human is deliberately trying to bait the assistant into generating harmful content, and whether they succeeded in doing so.', revision_request='Write a revision of the assistant’s response that refrains from saying anything harmful.', name='harmful6'),
     'criminal': ConstitutionalPrinciple(critique_request='Read the assistant’s last response carefully and identify anything it said that provides advice or assistance in potentially criminal activities, such as violence, theft, hacking, robbery, or any other illegal activity. Consider the strongest argument you could give that the assistant response might encourage crime.', revision_request='Rewrite the assistant response to avoid assisting the human with criminal plans or activities, such as violence, theft, hacking, robbery, or anything illegal.', name='criminal'),
     'harmful7': ConstitutionalPrinciple(critique_request='Critique the assistant’s last response and identify anything it said that was harmful, unethical, dangerous, or illegal.', revision_request='Please rewrite the assistant response to remove any and all harmful, unethical, dangerous, or illegal content.', name='harmful7'),
     'ethical_principle': ConstitutionalPrinciple(critique_request="The model should only talk about ethical and legal and fair things.", revision_request="Rewrite the model's output to be ethical, legal and fair and should not be harmfull to any living creature.", name="Ethical Principle")}


def set_LLM_data():
    global LLM_DATA

    # guardrails
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    rails = loop.run_until_complete(get_rails())

    # read pdf
    pdf_dir_path = "resources/policies"
    text_content = read_pdf_to_string(pdf_dir_path)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=6000, chunk_overlap=1000, length_function=len)
    embeddings = OpenAIEmbeddings()
    documents = text_splitter.create_documents(text_content)
    output_dir = "../db_metadata_v5"
    db = Chroma.from_documents(documents, embeddings, persist_directory=output_dir)

    # prompt
    system_template = """
            You are an intelligent and excellent at answering questions about government policies.
            I will ask questions from the documents and you'll help me try finding the answers from it.
            Give the answer using best of your knowledge, say you dont know unable able to answer.
            ---------------
            {context}
            """
    qa_prompt = PromptTemplate.from_template(system_template)
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    principles = get_principles()
    qa_chain = ConversationalRetrievalChain.from_llm(rails.llm, db.as_retriever(),
                                                     memory=memory, condense_question_prompt=qa_prompt)
    constitutional_chain = ConstitutionalChain.from_llm(
        llm=rails.llm,
        chain=qa_chain,
        constitutional_principles=list(principles.values()),
    )
    rails.register_action(constitutional_chain, name="qa_chain")
    LLM_DATA = {"rails": rails}


def generate_response(query_text):
    global LLM_DATA
    rails = LLM_DATA["rails"]
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(rails.generate_async(
        messages=[{"role": "user", "content": query_text}]))
    dict = {"question": query_text, "answer": result["content"]}
    st.session_state.QA.append(dict)
    return


set_LLM_data()
with st.form('myform'):
    query_text = st.text_input('Enter your question:', placeholder='Enter your question here')
    submitted = st.form_submit_button('Submit', disabled=(query_text == ""))
    if submitted:
        with st.spinner('Generating...'):
            generate_response(query_text)
            for i in st.session_state.QA:
                st.write("Question : " + i["question"])
                st.write("Answer : " + i["answer"])
                st.write("\n\n")
