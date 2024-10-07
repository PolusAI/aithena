from llama_index.llms.ollama import Ollama
from llama_index.core.llms import ChatMessage

user_message = {'role': 'user', 'content': 'Why is the sky blue?'}
messages = [ChatMessage(**user_message)]
llm = Ollama(model="llama3.1:latest", request_timeout=120.0, temperature=1.0, additional_kwargs={"top_k": 0.1})
resp = llm.chat(messages)
print(f"output: {resp.message.content}")
print(f"extra args: {resp.message.additional_kwargs}")
print(f"output: {resp.dict()}")
