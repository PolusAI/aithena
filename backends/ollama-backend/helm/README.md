# Ollama helm charts

This is regular deployment of ollama using helm charts.

A single service can route request to any number of replicas.
Each replica is running a single ollama-server, that can by
default see all gpus and can schedule work on any of them.

`values-sample.yaml` contains a definition for a single replica deployment.
`values-scaling.yaml` shows how to deploy multiple ollama servers with
specific configuration. 

Rename the one you want to use to `values.yaml` and use this file for deployment:

```mh install ${RELEASE} .  -n ${NAMESPACE}```

