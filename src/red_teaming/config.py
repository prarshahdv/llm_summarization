# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import csv
import json
import os

from langchain import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.embeddings import OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from nemoguardrails import LLMRails
from nemoguardrails.server.api import register_logger
import streamlit as st


os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

async def custom_logger(item):
    print(item)
    """Custom logger that writes the ratings to a CSV file in the current directory."""
    data = json.loads(item["body"])
    config_id = data["config_id"]
    messages = data["messages"]

    # We only track on rating events
    if messages[-1]["role"] != "event" or messages[-1]["event"].get("type") != "rating":
        print("Skipping")
        return

    # Extract the data from the event
    str_messages = ""
    for message in messages:
        if message["role"] == "user":
            str_messages += f"User: {message['content']}\n"
        if message["role"] == "assistant":
            str_messages += f"Assistant: {message['content']}\n"

    event_data = messages[-1]["event"]["data"]

    row = [
        config_id,
        event_data["challenge"]["id"],
        event_data["challenge"]["name"],
        event_data["challenge"]["description"],
        event_data["success"],
        event_data["effort"],
        event_data["comment"],
        str_messages.strip(),
    ]

    with open("ratings.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)

def _get_qa_chain(rails):
    # read pdf
    from utils.functions import read_pdf_to_string, get_principles
    from utils.constitutional_chain import ConstitutionalChain

    pdf_dir_path= "resources/policies"
    text_content = read_pdf_to_string(pdf_dir_path)
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

    principles = get_principles()
    qa_chain = ConversationalRetrievalChain.from_llm(rails.llm, db.as_retriever(),
                                                     memory=memory, condense_question_prompt=qa_prompt)
    constitutional_chain = ConstitutionalChain.from_llm(
        llm=rails.llm,
        chain=qa_chain,
        constitutional_principles=list(principles.values()),
    )
    return constitutional_chain

# def init(llm_rails: LLMRails):
#     # We register the additional prompt context for the current date.
#     # from src.im8_policy_app_2 import PolicyQABot
#     # bot = PolicyQABot(llm_rails)
#     # bot.set_llm_data()
#     # llm_rails = bot.rails
#     qa_chain = _get_qa_chain(llm_rails)
#     llm_rails.register_action(qa_chain, name="qa_chain")

register_logger(custom_logger)
