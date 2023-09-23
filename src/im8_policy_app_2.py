import sys
import sqlite3

__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
connection = sqlite3.connect('../cache.db', timeout=1000)
connection = sqlite3.connect('../table', timeout=1000)
connection = sqlite3.connect('../main', timeout=1000)

import logging
import streamlit as st
import os
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.embeddings import OpenAIEmbeddings
from langchain import PromptTemplate
import asyncio
from utils.constitutional_chain import ConstitutionalChain
from utils.functions import read_pdf_to_string, get_principles, get_rails

logging.basicConfig(level=logging.INFO)

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
st.set_page_config(page_title='Government Policy Docs')
st.title('🦜🔗 Government Policy Bot')

# client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory="db/"))
# collection = client.create_collection(name="policies")

# initialize default variables
st.session_state.QA = []
LLM_DATA = {}


class PolicyQABot:

    def __int__(self):
        # guardrails
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.rails = loop.run_until_complete(get_rails())
        self.pdf_dir_path = "resources/policies"
        st.session_state.QA = []

    def set_llm_data(self):
        # read pdf
        text_content = read_pdf_to_string(self.pdf_dir_path)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=6000, chunk_overlap=1000, length_function=len)
        embeddings = OpenAIEmbeddings()
        documents = text_splitter.create_documents(text_content)
        output_dir = "../db_metadata_v5"
        db = Chroma.from_documents(documents, embeddings, persist_directory=output_dir)

        # prompt
        prompt_template = """
                You are an intelligent and excellent at answering questions about government policies.
                I will ask questions from the documents and you'll help me try finding the answers from it.
                Give the answer using best of your knowledge, say you dont know unable able to answer.
                ---------------
                {context}
                """
        qa_prompt = PromptTemplate.from_template(prompt_template)
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        qa_chain = ConversationalRetrievalChain.from_llm(self.rails.llm, db.as_retriever(),
                                                         memory=memory, condense_question_prompt=qa_prompt)

        # constitutional ai
        principles = get_principles()
        constitutional_chain = ConstitutionalChain.from_llm(
            llm=self.rails.llm,
            chain=qa_chain,
            constitutional_principles=list(principles.values()),
        )
        self.rails.register_action(constitutional_chain, name="qa_chain")
        return

    def generate_response(self, query_text):
        loop = asyncio.get_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self.rails.generate_async(
            messages=[{"role": "user", "content": query_text}]))
        dict = {"question": query_text, "answer": result["content"]}
        st.session_state.QA.append(dict)
        return

    def run(self):
        self.set_llm_data()
        with st.form('myform'):
            query_text = st.text_input('Enter your question:', placeholder='Enter your question here')
            submitted = st.form_submit_button('Submit', disabled=(query_text == ""))
            if submitted:
                with st.spinner('Generating...'):
                    self.generate_response(query_text)
                    for i in st.session_state.QA:
                        st.write("Question : " + i["question"])
                        st.write("Answer : " + i["answer"])
                        st.write("\n\n")


if __name__ == "__main__":
    # guardrails
    PolicyQABot().run()