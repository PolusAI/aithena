#!/bin/bash

# Define the StatefulSet name and namespace
STATEFULSET_NAME="ollama-ss-set"
NAMESPACE="default"

# Define the number of replicas
REPLICAS=2

# Delete the StatefulSet
microk8s kubectl delete statefulset ${STATEFULSET_NAME} --namespace=${NAMESPACE}

# Delete the Headless Service
microk8s kubectl delete service ollama-ss-headless --namespace=${NAMESPACE}

# Delete NodePort services for each replica
for i in $(seq 0 $((REPLICAS - 1)))
do
  SERVICE_NAME="ollama-ss-${STATEFULSET_NAME}-${i}"
  microk8s kubectl delete service ${SERVICE_NAME} --namespace=${NAMESPACE}
done

# Delete PVCs for each replica
for i in $(seq 0 $((REPLICAS - 1)))
do
  PVC_NAME="pvc-ollama-ss-${STATEFULSET_NAME}-${i}"
  kubectl delete pvc ${PVC_NAME} --namespace=${NAMESPACE}
done

# Delete PVs for each replica
for i in $(seq 0 $((REPLICAS - 1)))
do
  PV_NAME="pv-ollama-ss-${STATEFULSET_NAME}-${i}"
  kubectl delete pv ${PV_NAME}
done