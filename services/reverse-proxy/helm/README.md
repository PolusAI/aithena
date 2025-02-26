## Reverse-Proxy Service (nginx)

### Configure 

Rename `vars-sample` to `.vars` and update values then `source .vars`
with the values for your service deployment.

To configure nginx, rename `nginx.conf-sample` to `nginx.conf`
edit value with variables creating previously.

Also rename `values-sample.md` to `values.md`


### Install

```shell
microk8s helm install nginxbox . -n box
```

### Test

```shell
curl -X POST http://localhost:80/ais/chat/llama3.1/generate\?stream\=False -d '[{"role": "user", "content": "What is the capital of France?"
```

