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

def get_principles():
    return {'offensive': ConstitutionalPrinciple(
        critique_request='Discuss whether the assistant said anything that may be interpreted as offensive or harmful. If possible, also point out any harmful assumptions in the human’s dialogue.',
        revision_request='Please write a new version of the assistant’s response that removes offensive and harmful content, and politely addresses any problematic assumptions from the human.',
        name='offensive'),
            'harmful6': ConstitutionalPrinciple(
                critique_request='Discuss whether the human is deliberately trying to bait the assistant into generating harmful content, and whether they succeeded in doing so.',
                revision_request='Write a revision of the assistant’s response that refrains from saying anything harmful.',
                name='harmful6'),
            'criminal': ConstitutionalPrinciple(
                critique_request='Read the assistant’s last response carefully and identify anything it said that provides advice or assistance in potentially criminal activities, such as violence, theft, hacking, robbery, or any other illegal activity. Consider the strongest argument you could give that the assistant response might encourage crime.',
                revision_request='Rewrite the assistant response to avoid assisting the human with criminal plans or activities, such as violence, theft, hacking, robbery, or anything illegal.',
                name='criminal'),
            'harmful7': ConstitutionalPrinciple(
                critique_request='Critique the assistant’s last response and identify anything it said that was harmful, unethical, dangerous, or illegal.',
                revision_request='Please rewrite the assistant response to remove any and all harmful, unethical, dangerous, or illegal content.',
                name='harmful7'),
            'ethical_principle': ConstitutionalPrinciple(
                critique_request="The model should only talk about ethical and legal and fair things.",
                revision_request="Rewrite the model's output to be ethical, legal and fair and should not be harmfull to any living creature.",
                name="Ethical Principle")}
