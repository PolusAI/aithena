# Ask Aithena App (v0.1.0-dev5)

Ask aithena app is a solara dashboard communicating with the ask aithena agent.
It allows the user to ask questions and leverage existing scientific literature 
to provide accurate and sourced information.

## Env Var

`ASK_AITHENA_API_URL` *Optional*: default is "http://localhost:8080". Ask Aithena URL.
`ASK_AITHENA_STREAM` *Optional*: default is True. If True, response from Ask Aithena will be streamed. If False, the entire response will be shown once the entire response is available.

## Deployment

Ask-aithena agent needs to be deployed as it is our backend. 
See [instructions](../../agents/ask-aithena-agent/README.md)

## Test 

Create a tunnel to your host

```shell
ssh -L ${NODE_PORT}:127.0.0.1:${NODE_PORT} ${USER}@{REMOTE_HOST}
```

Browse to `http://localhost:${NODE_PORT}`

Ask Aithena!