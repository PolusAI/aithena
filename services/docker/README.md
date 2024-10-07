# AIthena Services - Docker
These are instructions to set up and serve AIthena Services in a docker container.

## Environment Variables
### **Check [docs/env.md](../docs/env.md) for more details**
1. Rename `variables_sample.env` to `variables.env`
2. Replace the values of the environment variables with the correct values

*IMPORTANT:* Do not include quotation marks (") in your .env file, for example:
```
AZURE_OPENAI_API_KEY="abc123" # this will not work
AZURE_OPENAI_API_KEY=abc123 # this is correct
```

## Docker Run
Use a command similar to:
```
docker run -itd --name "ais0" -p 8001:80 \
--env-file docker/variables.env \
--network=name=ais0 \
aithena-services:0.0.1
```

Args:
* `-p` X:80, X is your host machine port where the FastAPI (running inside the container's port 80) will be mapped
* `--env-file` leave as `docker/variables.env` - assuming you have already correctly followed the steps in the previous section
* `--network` is optional, in case you are running the container inside a docker network

## Test API
Run a GET request to `/test` and you should get `{"status": "success"}`:
```bash
~ $ curl http://localhost:8001/test     
{"status":"success"}% 
```

## Examples
### Embeddings
```bash
~ $ curl -X POST http://localhost:8001/embed/nomic-embed-text:latest/generate -d \
> "This is a test embedding"
[0.6514015793800354,1.2047090530395508,-3.8498952388763428,...
```

### Chat
```bash
~ $ curl -X POST http://localhost:8001/chat/llama3.1:latest/generate\?stream\=False \
-d '[{"role": "user", "content": "Is the Earth flat?"}]'
{"message":{"role":"assistant","content":"No, the Earth is not flat. It is an oblate spheroid, meaning it is shaped like a sphere that has been slightly flattened at the poles and bulging at the equator.","name":null},"raw":{"model":"llama3.1:latest","created_at":"2024-09-10T04:17:34.464453429Z","message":{"role":"assistant","content":"No, the Earth is not flat. It is an oblate spheroid, meaning it is shaped like a sphere that has been slightly flattened at the poles and bulging at the equator."},"done_reason":"stop","done":true,"total_duration":16802824342,"load_duration":30122375,"prompt_eval_count":31,"prompt_eval_duration":4395003000,"eval_count":41,"eval_duration":12333513000,"usage":{"prompt_tokens":31,"completion_tokens":41,"total_tokens":72}},"delta":null,"logprobs":null,"additional_kwargs":{}}%
```