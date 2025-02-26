# Kubernetes stateful sets

This is stateful sets deployment with kubernetes.
Stateful sets are used to run exactly one ollama-server per GPU.
Each ollama-server can only schedule work on the GPU it is deployed on.

This deployment can be used to have more controlled on how the requests 
to ollama are processed.

In the current deployment, all ollama servers share the same models.
Each ollama instance can be accessed outside the cluster with an unique ip,
starting at 30000

```curl http://localhost:30000``` for instance on gpu0
```curl http://localhost:30001```for instance on gpu1
etc...


## Install 

```chmod u+x ./deploy_statefulsets.sh```
```./deploy_statefulsets.sh```

# Delete 

```chmod u+x ./delete_statefulsets.sh```
```./delete_statefulsets.sh```