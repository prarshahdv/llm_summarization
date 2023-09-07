import sys
import sqlite3
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
connection = sqlite3.connect('cache.db', timeout=1000)
connection = sqlite3.connect('table', timeout=1000)
connection = sqlite3.connect('main', timeout=1000)


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

logging.basicConfig(level=logging.INFO)

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
st.set_page_config(page_title='LLM Summarization Docs')
st.title('🦜🔗 LLM Summarization')

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
    config = nemoguardrails.RailsConfig.from_path("config/")
    return nemoguardrails.LLMRails(config)


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
            output_dir = "./db_metadata_v5"
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
            qa_chain = ConversationalRetrievalChain.from_llm(rails.llm, db.as_retriever(),
                                                       memory=memory, condense_question_prompt=qa_prompt)

            rails.register_action(qa_chain, name="qa_chain")
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
