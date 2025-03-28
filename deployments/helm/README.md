
# Helm deployments

This directory contains full stack kubernetes deployments of 
various projects using helm charts.

Currently:

- `ask-aithena-chart` rag app
- `arxiv-ingestion-job-chart` arxiv ingestion
- `ai-review-chart` ai assisted literature review app

If you would rather deploy only an app and reuse the underlying services and agents,
please deploy the individual app helm charts.

For any helm chart:

* Configure your deployment
- rename `values-sample.yaml` to `values.yaml`
- update all values to match your deployment.

* Deploy
```shell 
microk8s helm install ${RELEASE_NAME} ${CHART_DIR}
```

* Update
```shell 
microk8s helm upgrade ${RELEASE_NAME} ${CHART_DIR}
```

* Delete
```shell 
microk8s helm uninstall ${RELEASE_NAME}
```

## templates

Template are resuable charts that other components will use to create their resources.