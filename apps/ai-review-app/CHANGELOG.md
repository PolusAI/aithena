## v0.2.0-dev1

- due to discrepancies in llm backends behaviors,
previous versions only supported azure models. This restriction has
been lifting and the app now works with ollama-backed llms. 
- removed aithena-services direct dependency and now requires an running
aithena service instance.

## v0.2.0-dev0

- migration to aithena repository
- provide docker container
- only support azure/openai endpoints

Missing features:
- similarity is removed as previous embedding service used nvembed
and we are now relying and ollama deployed nomic-text-embed


## 0.1.0 

- original implementation.