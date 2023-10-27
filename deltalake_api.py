import requests

url = "https://dbc-3696807f-276e.cloud.databricks.com/api/2.0/sql/statements/"

headers = {
    "Authorization": "Bearer dapia869ec03adeb862eeff62c70d9a43965",
    "Content-Type": "application/json"
}

data = {
    "warehouse_id": "597bd5e07eaec370",
    "catalog": "hive_metastore",
    "schema": "langchain_policy_bot",
    "statement": "INSERT INTO response_table (model, response_type, response_score, response_text, user_id, metadata) VALUES (:model_name, :response_type, :response_score, :response_text, :user_id, :metadata);",
    "parameters": [
        { "name": "model_name", "value": "llm-qa-government-policy-bot", "type": "STRING" },
        { "name": "response_type", "value": "thumbs", "type": "STRING" },
        { "name": "response_score", "value": "up", "type": "STRING" },
        { "name": "response_text", "value": "Good response", "type": "STRING" },
        { "name": "user_id", "value": "streamlit_app_test_1", "type": "STRING" },
        { "name": "metadata", "value": "{}", "type": "STRING" }
    ]
}

response = requests.post(url, headers=headers, json=data)

# Print response
print(response.text)
