pip install -r requirements.txt

python -m fastapi_endpoint &

streamlit run conversation_qa_policy_bot.py --server.port 8561
