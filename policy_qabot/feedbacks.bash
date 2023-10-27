export OPENAI_API_KEY=""
export DATABRICKS_HOST=""
export DATABRICKS_TOKEN=""
export DATABRICKS_SQL_WAREHOUSE_ID=""

curl --request POST \
<DATABRICKS_HOST>/api/2.0/sql/statements/ \
--header "Authorization: Bearer <DATABRICKS_TOKEN>" \
--header "Content-Type: application/json" \
--data '{
  "warehouse_id": "<DATABRICKS_SQL_WAREHOUSE_ID>",
  "catalog": "hive_metastore",
  "schema": "langchain_policy_bot",
  "statement": "INSERT INTO response_table (model, response_type, response_score, response_text, user_id, metadata) VALUES (:model_name, :response_type, :response_score, :response_text, :user_id, :metadata);",
  "parameters": [
    { "name": "model_name", "value": "llm-qa-government-policy-bot", "type": "STRING" },
    { "name": "response_type", "value": "thumbs", "type": "STRING" },
    { "name": "response_score", "value": "up", "type": "STRING" },
    { "name": "response_text", "value": "Good response", "type": "STRING" },
    { "name": "user_id", "value": "streamlit_app_test_1", "type": "STRING" },
    { "name": "metadata", "value": "{}", "type": "STRING" }]}'