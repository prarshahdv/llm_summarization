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

from langchain import PromptTemplate, LLMChain
from langchain.chains import ConstitutionalChain
from langchain.chains.constitutional_ai.models import ConstitutionalPrinciple
from nemoguardrails import LLMRails
from nemoguardrails.server.api import register_logger

def get_principles() -> object:
    return {'offensive': ConstitutionalPrinciple(critique_request='Discuss whether the assistant said anything that may be interpreted as offensive or harmful. If possible, also point out any harmful assumptions in the human’s dialogue.', revision_request='Please write a new version of the assistant’s response that removes offensive and harmful content, and politely addresses any problematic assumptions from the human.', name='offensive'),
     'harmful6': ConstitutionalPrinciple(critique_request='Discuss whether the human is deliberately trying to bait the assistant into generating harmful content, and whether they succeeded in doing so.', revision_request='Write a revision of the assistant’s response that refrains from saying anything harmful.', name='harmful6'),
     'criminal': ConstitutionalPrinciple(critique_request='Read the assistant’s last response carefully and identify anything it said that provides advice or assistance in potentially criminal activities, such as violence, theft, hacking, robbery, or any other illegal activity. Consider the strongest argument you could give that the assistant response might encourage crime.', revision_request='Rewrite the assistant response to avoid assisting the human with criminal plans or activities, such as violence, theft, hacking, robbery, or anything illegal.', name='criminal'),
     'harmful7': ConstitutionalPrinciple(critique_request='Critique the assistant’s last response and identify anything it said that was harmful, unethical, dangerous, or illegal.', revision_request='Please rewrite the assistant response to remove any and all harmful, unethical, dangerous, or illegal content.', name='harmful7'),
     'ethical_principle': ConstitutionalPrinciple(critique_request="The model should only talk about ethical and legal and fair things.", revision_request="Rewrite the model's output to be ethical, legal and fair and should not be harmfull to any living creature.", name="Ethical Principle")}



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


def set_LLM_data(rails):
    # prompt
    system_template = """
            You are an intelligent and excellent at answering questions about government policies.
            I will ask questions from the documents and you'll help me try finding the answers from it.
            Give the answer using best of your knowledge, say you don't know if unable able to answer.
            ---------------
            {context}
            """
    qa_prompt = PromptTemplate.from_template(system_template)
    principles = get_principles()
    constitutional_chain = ConstitutionalChain.from_llm(
        llm=rails.llm,
        constitutional_principles=list(principles.values()),
        chain=LLMChain(llm=rails.llm, prompt=qa_prompt),
    )
    rails.register_action(constitutional_chain, name="qa_chain")


def init(llm_rails: LLMRails):
    # We register the additional prompt context for the current date.
    set_LLM_data(llm_rails)

register_logger(custom_logger)
