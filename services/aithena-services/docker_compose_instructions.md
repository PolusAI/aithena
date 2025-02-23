# Aithena-Services Docker Compose Instructions
Running these instructions will:
* Build and run a `pgvector` container (vector embeddings storage & ops)
* Build and run an `ollama` container (run local LLMs)
* Build and run an `aithena-services` container (easy interface for LLMs and similarity search)
* Connect these three containers in the same docker network
* Configure `aithena-services` to link it to `pgvector` and `ollama`

# 1. Modify environment variables
1. Rename `docker_sample.env` to `docker.env`
2. Modify `POSTGRES_PASSWORD` to define your pgvector password
3. Modify `OPENAI_API_KEY` to your key if you want to use OpenAI API
4. Modify `AZURE_OPENAI...` env vars 
**IMPORTANT:** Do not include quotation marks (") in your .env file, for example:
```
AZURE_OPENAI_API_KEY="abc123" # this will not work
AZURE_OPENAI_API_KEY=abc123 # this is correct
```
For more details on environment variables and for instructions specific to `AZURE_OPENAI` variables, [read docs/env.md](docs/env.md).

# 2. Run `docker compose up`
1. Navigate to the `aithena_services` directory
2. Run `docker compose up`
This will build and run `pgvector` , `ollama` and `aithena-services` with the correct configuration.

# 3. Test aithena-services
Aithena services proxy server should be running on port 8000. To test it, run: `curl localhost:8000/test` and you should get the response `{"status":"success"}`.

# 4. Download LLMs in Ollama
[See all available LLMs in Ollama](https://ollama.com/search)
To download a new LLM, use aithena-services with a `POST` request to `/ollama/pull/<model_name>:<optional_model_tag>`, e.g: 
* `curl -XPOST localhost:8000/ollama/pull/llama3.2:1b` would download llama3.2 with 1b parameters
A good place to start is downloading llama3.1: `curl -XPOST localhost:8000/ollama/pull/llama3.1` (this will download the latest 8b parameter version)

You are now ready to use `aithena-services` to interact with LLMs.

# 5. Chat through Aithena Services
### List all available models
To see all available models in `aithena-services` run:
`curl localhost:8000/chat/list` and you will get a list of the names of the available models, e.g: `[llama3.1, llama3.2:1b]`

### Chat with a model

To interact with a chat model, send a POST request to the /chat/{model}/generate endpoint, replacing {model} with the desired model name. The request body should contain a list of messages representing the conversation history or a single string message. If providing a list, each message should be a dictionary with role ("system", "user", or "assistant") and content. To stream responses, set the stream query parameter to true. Example requests can be made using curl, such as:
```
curl -X POST localhost:8000/chat/llama3.2:1b/generate -d "Why is the earth flat?"
```
or
```
curl -X POST "http://localhost:8000/chat/llama3.2:1b/generate" \                
     -H "Content-Type: application/json" \                                                                                                  
     -d '[                                                                                                                                  
           {"role": "system", "content": "you only answer you don'\''t know, nothing else. does not matter if wrong"},                      
           {"role": "user", "content": "why is the sun called sun?"},                                                                       
           {"role": "assistant", "content": "I don'\''t know"},                                                                             
           {"role": "user", "content": "why is the earth flat?"}                                                                            
         ]'
```

Responses are returned in JSON format, with the assistant’s message under the message field.

```
{"message":{"role":"assistant","content":"I'm here to help you with your question, but I want to let you know that the concept of a \"flat E
arth\" is not supported by scientific evidence and is widely considered to be an oversimplification of our understanding of the world. The o
verwhelming majority of scientists agree that the Earth is an oblate spheroid shape, meaning it's slightly flattened at the poles and bulgin
g at the equator.\n\nThere are many reasons why the Earth is not flat, including:\n\n1. Ships disappearing over the horizon: When a ship sai
ls away from an observer on the shore, it will eventually disappear from view as it sinks below the horizon due to the Earth's curvature.\n2. Satellite imagery: Satellite images of the Earth provide clear visual evidence of its spherical shape.\n3. Shadows on the moon: During a l
unar eclipse, the Earth passes between the sun and the moon, casting a shadow on the lunar surface. The shape of this shadow is curved, indi
cating that the Earth is a sphere.\n4. Circumnavigation: Many people have traveled around the world, completing circumnavigations of the pla
net. If the Earth were flat, it would be impossible to do this without being caught in its gravitational pull.\n5. Scientific measurements: 
Scientists have made precise measurements of the Earth's shape using a variety of techniques, including satellite laser ranging and radar al
timetry.\n\nI want to encourage you to think critically about these concepts and consider the evidence that supports the fact that the Earth
 is an oblate spheroid shape. If you have any questions or concerns, feel free to ask!","name":null},"raw":{"model":"llama3.2:1b","created_a
t":"2025-02-04T18:27:02.432820759Z","message":..."},"done_reason":"stop","done":true,"total_duration":15738133216,"load_duration":3606444335,"prompt_eval_count":34,"prompt_eval_duration":404984000,"eval_count":320,"eval_duration":11723259000,"usage":{"prompt_tokens":34,"completion_tokens":320,"total_tokens":354}},"delta":null,"logprobs":null,"additional_kwargs":{}}%   
```
or

```
{"message":{"role":"assistant","content":"I don't know","name":null},"raw":{"model":"llama3.2:1b","created_at":"2025-02-04T18:34:56.16717258
9Z","message":{"role":"assistant","content":"I don't know"},"done_reason":"stop","done":true,"total_duration":1753121209,"load_duration":715
93792,"prompt_eval_count":68,"prompt_eval_duration":1315793000,"eval_count":5,"eval_duration":146514000,"usage":{"prompt_tokens":68,"complet
ion_tokens":5,"total_tokens":73}},"delta":null,"logprobs":null,"additional_kwargs":{}}% 
```
                                                                                                                             
To access the content of the response, regardless of what models is used, you can access it at `message.content`

### Streaming Response
Here’s a paragraph for the streaming mode (stream=True):

To receive streamed responses from a chat model, send a POST request to the /chat/{model}/generate endpoint with the stream query parameter set to true. The request body should be either a list of messages (each with a role and content) or a single string message. Streaming mode allows the response to be received incrementally as it is generated. Example request using curl:


```
curl -X POST "http://localhost:8000/chat/llama3.2:1b/generate?stream=true" \
     -H "Content-Type: application/json" \
     -d '[{"role": "user", "content": "Why is the sun hot? In one sentence."}]'
```
The response is streamed as JSON objects, each containing incremental updates of the assistant’s message. If an error occurs, it is also returned as a JSON message within the stream.

Example response:
```
{"message": {"role": "assistant", "content": "The"}, "raw": {"model": "llama3.2:1b", "created_at": "2025-02-04T18:47:38.583108762Z", "messag
e": {"role": "assistant", "content": "The"}, "done": false}, "delta": "The", "logprobs": null, "additional_kwargs": {}}
    
{"message": {"role": "assistant", "content": "The sun"}, "raw": {"model": "llama3.2:1b", "created_at": "2025-02-04T18:47:38.65227147Z", "mes
sage": {"role": "assistant", "content": " sun"}, "done": false}, "delta": " sun", "logprobs": null, "additional_kwargs": {}}
 
{"message": {"role": "assistant", "content": "The sun is"}, "raw": {"model": "llama3.2:1b", "created_at": "2025-02-04T18:47:38.732329887Z", 
"message": {"role": "assistant", "content": " is"}, "done": false}, "delta": " is", "logprobs": null, "additional_kwargs": {}}
  
{"message": {"role": "assistant", "content": "The sun is hot"}, "raw": {"model": "llama3.2:1b", "created_at": "2025-02-04T18:47:38.809711345
Z", "message": {"role": "assistant", "content": " hot"}, "done": false}, "delta": " hot", "logprobs": null, "additional_kwargs": {}}

{"message": {"role": "assistant", "content": "The sun is hot because"}, "raw": {"model": "llama3.2:1b", "created_at": "2025-02-04T18:47:38.8
92872095Z", "message": {"role": "assistant", "content": " because"}, "done": false}, "delta": " because", "logprobs": null, "additional_kwar
gs": {}}
.
.
.
{"message": {"role": "assistant", "content": "The sun is hot because it generates its energy through nuclear reactions in its core, where hy
drogen atoms are fused together to form helium, releasing vast amounts of energy in the process."}, "raw": {"model": "llama3.2:1b", "created
_at": "2025-02-04T18:47:41.459593221Z", "message": {"role": "assistant", "content": ""}, "done_reason": "stop", "done": true, "total_duratio
n": 2978776043, "load_duration": 19210250, "prompt_eval_count": 35, "prompt_eval_duration": 30137000, "eval_count": 36, "eval_duration": 288
7582000, "usage": {"prompt_tokens": 35, "completion_tokens": 36, "total_tokens": 71}}, "delta": "", "logprobs": null, "additional_kwargs": {}}
```

The response is streamed as JSON objects, each containing incremental updates of the assistant’s message. Every streamed object contains:
* `delta`: the *new* text being generated in this chunk.
* `message`: the full accumulated response from the assistant so far.
* `done`: a boolean that is true for the last streamed object.

# 6. Pgvector example
Aithena-services includes the endpoint `/memory/search` to perform vector similarity search (with cosine distance) in [pgvector](https://github.com/pgvector/pgvector).
Make sure that you have activated the pgvector extension in the postgres database that was created by the container `pgvector` in docker compose.
Enable the extension (do this once in each database where you want to use it)
```
CREATE EXTENSION vector;
```
[See here for more info](https://github.com/pgvector/pgvector?tab=readme-ov-file#getting-started)

To perform similarity search, your vector table must include:
	1.	A column named **embedding** that stores vector embeddings.
	2.	A column named **id** that uniquely identifies each row.

For example, if your table is named code_embeddings, it **must** have:
	* 	An **id** column containing unique identifiers (which can be any type of ID).
	* 	An **embedding** column storing the vector representations.
Without these specific column names, similarity search will not work properly.

To perform a similarity search, send a POST request to the /memory/search endpoint with the required parameters. The request must include:
	* 	table_name (string): The name of the table containing the vector embeddings.
	* 	vector (list of floats): The query vector to search for similar embeddings.
	* 	n (integer, optional): The number of most similar results to return (defaults to 10).

The table being searched **must** contain an **id** column (which uniquely identifies each row) and an **embedding** column (which stores the vector embeddings). The search is performed using pgvector with cosine distance as the similarity metric.

The response will be a list of id values corresponding to the most similar embeddings found in the table. If an error occurs, it will be returned as a JSON response with an appropriate error message.
### Example
1. Let’s create an example table that contains vector embeddings. We already activated pgvector extension.
   ```sql
   --Create the table (here the column “embedding” is of type vector(10))
   CREATE TABLE code_embeddings (
    id SERIAL PRIMARY KEY,
    embedding vector(10)
   );
   ```
2. Insert 10 random vectors
   ```sql
   -- Insert 10 example vectors (each with 10 components)
   INSERT INTO code_embeddings (embedding) VALUES
   ('[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]'),
   ('[1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]'),
   ('[0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]'),
   ('[2.0, 1.8, 1.6, 1.4, 1.2, 1.0, 0.8, 0.6, 0.4, 0.2]'),
   ('[0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]'),
   ('[1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1]'),
   ('[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]'),
   ('[0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0]'),
   ('[0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]'),
   ('[1.2, 1.1, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]');
   ```
3. Use `aithena-services` to perform vector similarity search on `code_embeddings`. For example, against vector: [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
   ```
   curl -X POST "http://localhost:8000/memory/search?table_name=code_embeddings" \ 
     -H "Content-Type: application/json" \
     -d '[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]'
   ```
   You should get the response: `[5,6,10,9,3,1,2,4,7,8]`

   