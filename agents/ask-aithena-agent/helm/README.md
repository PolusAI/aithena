## Ask aithena agent

### Configure 

Rename `.vars-sample` to `.vars` and `source .vars`
Rename `.values-sample` to `.values` and update

### Install

```shell
mh upgrade ${RELEASE_NAME} . -n ${NAMESPACE}
``` 

### Test

curl -X POST http://localhost:${ASK_AITHENA_AGENT_NODEPORT}/ask -H "Content-Type: application/json" -d '{"query": "What is the capital of France?"}'
