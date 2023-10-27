import asyncio
import os
import nemoguardrails

os.environ["OPENAI_API_KEY"] = "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"
rails_config = nemoguardrails.RailsConfig.from_path("/Users/pshah1/ps/projects/genai/gitlab/llm_summarization/config")
rails = nemoguardrails.LLMRails(rails_config)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
output = loop.run_until_complete(rails.generate_async(
    messages=[{"role": "user", "content": "Hello, what can you do?", 'context': "government policy doccuments"}]))
print(str("output"))