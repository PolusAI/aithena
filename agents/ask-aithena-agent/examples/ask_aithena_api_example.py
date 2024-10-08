import json
import requests
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# def ask_aithena(query: dict):
#     url = "http://127.0.0.1:8000/ask"
#     headers = {"Content-Type": "application/json"}

# response = requests.post(url, data=json.dumps(query), stream=False)
#     response.raise_for_status()  # Raise an error for bad status codes
#     resp = response.json()["response"]
#     return resp

# resp = ask_aithena({"query": "tell me SQL joins"})
# print(resp)

# def ask_aithena(query: dict):
#     url = "http://10.152.183.132:8000/ask"
#     headers = {"Content-Type": "application/json"}
#     response = requests.post(url, data=json.dumps(query), stream=False)
#     response.raise_for_status()  # Raise an error for bad status codes
#     resp = response.json()["response"]
#     return resp

# resp = ask_aithena({"query": "What is new in astronomy?"})
# print(resp)


def ask_aithena(query: dict):
    url = "http://localhost:9145/ask"
    response = requests.post(url, data=json.dumps(query), stream=False)
    response.raise_for_status()  # Raise an error for bad status codes
    resp = response.json()["response"]
    return resp


resp = ask_aithena({"query": "What is new in astronomy?"})
print(resp)


# def embed_model(model: str, text:str):
#     url = "http://localhost:30080/embed/nomic-embed-text/generate"
#     # headers = {'Content-Type': 'text/plain; charset=utf-8'}
#     print(f"##### embedding : {text} by sending to  {url}")
#     response = requests.post(url, json="fdsfd", params={"stream":True}, stream=True)
#     response.raise_for_status()  # Raise an error for bad status codes
#     result = response.json()
#     print(f"##### embedding succeed : {len(result)}")
#     return result

# embed_model("nomic-embed-text", "What is new in astronomy?")
