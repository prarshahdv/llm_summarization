import os

import uvicorn
from fastapi import FastAPI
import mlflow
from dotenv import load_dotenv
import requests
import pandas as pd
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()
mlflow.set_tracking_uri("databricks")
model_name = "llm-qa-government-policy-bot"
model_stage = "Production"
# Load the model from the Model Registry
loaded_model = mlflow.pyfunc.load_model(f"models:/{model_name}/{model_stage}")

# conversation_qa_bot_with_guardrails
app = FastAPI(async_mode=True)


# Define a Pydantic model to represent the request body
class FeedbackData(BaseModel):
    model_name: str
    response_type: str
    response_score: str
    response_text: str
    user_id: str
    metadata: str
    question: str
    answer: str

# Define a Pydantic model to represent the response
class ResponseModel(BaseModel):
    message: str

@app.post("/process_feedback", response_model=ResponseModel)
async def process_feedback(request_data: FeedbackData):
    databricks_host = os.environ["DATABRICKS_HOST"]
    databricks_token = os.environ["DATABRICKS_TOKEN"]
    databricks_warehouse_id = os.environ["DATABRICKS_SQL_WAREHOUSE_ID"]
    url = f"{databricks_host}/api/2.0/sql/statements/"
    headers = {
        "Authorization": f"Bearer {databricks_token}",
        "Content-Type": "application/json"
    }
    data = {
        "warehouse_id": databricks_warehouse_id,
        "catalog": "hive_metastore",
        "schema": "langchain_policy_bot",
        "statement": "INSERT INTO response_table (model, response_type, response_score, response_text, user_id, metadata, question, answer) VALUES (:model_name, :response_type, :response_score, :response_text, :user_id, :metadata, :question, :answer);",
        "parameters": [
            {"name": "model_name", "value": request_data.model_name, "type": "STRING"},
            {"name": "response_type", "value": request_data.response_type, "type": "STRING"},
            {"name": "response_score", "value": request_data.response_score, "type": "STRING"},
            {"name": "response_text", "value": request_data.response_text, "type": "STRING"},
            {"name": "user_id", "value": request_data.user_id, "type": "STRING"},
            {"name": "metadata", "value": request_data.metadata, "type": "STRING"},
            {"name": "question", "value": request_data.question, "type": "STRING"},
            {"name": "answer", "value": request_data.answer, "type": "STRING"}
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    # Print response
    message = "Feedback processed successfully"
    return {"message": message, "response": response.text}

def create_questions_json(input):
    return {"question": [input]}

@app.get("/conversation_qa_bot_with_guardrails")
async def load_and_predict_from_databricks(input_string: str):
    global loaded_model
    queries = create_questions_json(input_string)
    queries_df = pd.DataFrame(queries)
    return {"processed_string": loaded_model.predict(queries_df)}

if __name__ == "__main__":
    uvicorn.run(app, loop="asyncio", host="0.0.0.0", port=8000)
