
# DEBUG HELM DEPLOYMENT

Visualize the resources :

```shell
microk8s get <all|resource-type>
```

List deployed charts:

```shell
microk8s helm list
```

it is sometimes useful to bash into existing containers:

```microk8s exec -it ${pod-name} -- bash```