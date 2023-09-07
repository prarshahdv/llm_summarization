from io import StringIO

from pdfminer.layout import LTTextContainer

__import__('pysqlite3')
import sys

sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import os

import fitz  # PyMuPDF
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory
from langchain.embeddings import OpenAIEmbeddings
from langchain import PromptTemplate

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
st.set_page_config(page_title='LLM Summarization Docs')
st.title('🦜🔗 LLM Summarization')

# initialize default variables
LLM_DATA = {}

def read_pdf_to_string(dir_path):
    pdf_to_str = []
    for file_path in os.listdir(dir_path):
        doc = fitz.open(file_path)
        text = ""
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text += page.get_text()
        pdf_to_str.append(text)
    return pdf_to_str

from functools import reduce

# Define a function to merge two lists
def merge_lists(list1, list2):
    return list1 + list2


def set_LLM_data():
            global LLM_DATA
            pdf_dir_path = "resources/policies"
            text_content = read_pdf_to_string(pdf_dir_path)
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=6000, chunk_overlap=1000, length_function=len)
            embeddings = OpenAIEmbeddings()
            documents = []
            for text in text_content:
                documents.append(text_splitter.create_documents(text))
            merged_documents = reduce(merge_lists, documents)
            db = Chroma.from_documents(merged_documents, embeddings)
            LLM_DATA = {
                "db": db
            }


def generate_response(query_text):
    system_template = """
    You are an intelligent and excellent at finding answers from the documents.
    I will ask questions from the documents and you'll help me try finding the answers from it.
    Give the answer using best of your knowledge, say you dont know if not able to answer.
    ---------------
    {context}
    """
    db = LLM_DATA["db"]
    qa_prompt = PromptTemplate.from_template(system_template)
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    qa = ConversationalRetrievalChain.from_llm(OpenAI(temperature=0, model_name="gpt-4"), db.as_retriever(),
                                               memory=memory, condense_question_prompt=qa_prompt)
    result = qa({"question": query_text})
    # return result["answer"]
    dict = {"question": result["question"], "answer": result["answer"]}
    st.session_state.QA.append(dict)


def query_form():
    with st.form('myform'):
        query_text = st.text_input('Enter your question:', placeholder='Enter your question here')
        submitted = st.form_submit_button('Submit', disabled=(query_text == ""))
        if submitted:
            with st.spinner('Generating...'):
                generate_response(query_text)
                for i in st.session_state.QA:
                    st.write("Question : " + i["question"])
                    st.write("Answer : " + i["answer"])


set_LLM_data()
query_form()