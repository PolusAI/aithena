# Ask-Aithena Helm Chart Instructions

This document provides instructions on how to deploy the Ask-Aithena application stack using the parent Helm chart.

## Introduction

The `ask-aithena-chart` is a Helm chart that simplifies the deployment of the entire Ask-Aithena application stack. It manages the following components as sub-charts:

- `aithena-services-chart`
- `ask-aithena-agent-chart`
- `ask-aithena-app-chart`
- `litellm-chart`
- `litellm-db-chart`
- `ollama-chart`
- `rabbitmq-chart`
- `postgres-chart`
- `arctic-chart`

This chart provides a centralized location to configure all the services, which are deployed into the `askaithena` namespace.

## Prerequisites

Before you begin, ensure you have the following installed and configured:

- A running Kubernetes cluster.
- `kubectl` configured to communicate with your cluster.
- Helm 3 installed.

### Arctic Embedding Model

The `arctic-chart` requires the Snowflake Arctic embedding model to be available on the host machine. Before installing the chart, you must download the model from Hugging Face Hub and ensure the path in `values.yaml` matches the location of the downloaded model.

1.  **Install Hugging Face Hub CLI**:
    If you don't have it installed, you can install it with pip:
    ```sh
    pip install huggingface_hub[cli]
    ```
    Or use `uvx` to install it:
    ```sh
    uvx --from 'huggingface_hub[cli]' pip install huggingface_hub[cli]
    ```

2.  **Download the Model**:
    Use the following command to download the model. This will download it to the default Hugging Face cache directory (usually `~/.cache/huggingface/hub`).
    ```sh
    huggingface-cli download Snowflake/snowflake-arctic-embed-l-v2.0
    ```

3.  **Verify the Path**:
    Make sure the `hostPath` in the `arctic-chart` section of the `values.yaml` file points to your Hugging Face cache directory. The default is `/polus2/velezramirezc2/.cache/huggingface`.

## Configuration

All configuration for the sub-charts can be managed from the `values.yaml` file located in the `ask-aithena-chart` directory.

### Centralized `values.yaml`

The `values.yaml` file is structured to allow you to override the default values for each sub-chart. Each sub-chart has its own section, named after the chart itself.

For example, to change the number of replicas for the `ask-aithena-app-chart`, you would modify its section in the `values.yaml` file like this:

```yaml
# ask-aithena-chart/values.yaml

...

ask-aithena-app-chart:
  replicaCount: 2

...
```

### Namespace Configuration

The namespace for the deployment is configured at the top of the `values.yaml` file:

```yaml
# ask-aithena-chart/values.yaml

namespace: "askaithena"
```

## Installation Steps

Follow these steps to deploy the Ask-Aithena stack:

1.  **Navigate to the Chart Directory**:
    Open your terminal and change to the `ask-aithena-chart` directory:
    ```sh
    cd deployments/helm/ask-aithena-chart
    ```

2.  **Build Helm Dependencies**:
    Build the required Helm dependencies:
    ```sh
    helm dependency build
    ```

3.  **Configure Values**:
    Copy the sample values file and modify it to your needs:
    ```sh
    cp values.sample.yaml values.yaml
    ```
    Then, edit `values.yaml` to set up your specific configuration.

4.  **Install or Upgrade the Chart**:
    Run the following command to install or upgrade the chart. This command is idempotent: it will install the release if it doesn't exist, or upgrade it if it does.
    ```sh
    helm upgrade --install ask-aithena . --namespace askaithena --create-namespace
    ```
    **Note**: The `--create-namespace` flag ensures the namespace is created if it doesn't already exist.

## Verifying the Deployment

Once the installation is complete, you can verify that all the components are running correctly.

-   **Check the Pods**:
    List all the pods in the `askaithena` namespace to ensure they are in the `Running` state:
    ```sh
    mkk get pods -n askaithena
    ```

-   **Check the Services**:
    List all the services to see their cluster IPs and ports:
    ```sh
    mkk get services -n askaithena
    ```

## Uninstalling the Deployment

To remove the Ask-Aithena application stack from your cluster, use the `helm uninstall` command:

```sh
helm uninstall ask-aithena -n askaithena
```

This will delete all the resources associated with the `ask-aithena` release.
