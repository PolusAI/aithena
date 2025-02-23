#!/bin/bash

# Define the StatefulSet name and namespace
STATEFULSET_NAME="ollama-ss-set"
NAMESPACE="default"

# Define the number of replicas
REPLICAS=2

# Define the storage path and size
STORAGE_PATH="/polus2/gerardinad/projects/aithena/.data/ollama"
STORAGE_SIZE="50Gi"
STORAGE_CLASS="microk8s-hostpath"

# Create PVs and PVCs for each replica
for i in $(seq 0 $((REPLICAS - 1)))
do
  PV_NAME="pv-ollama-ss-${STATEFULSET_NAME}-${i}"
  PVC_NAME="pvc-ollama-ss-${STATEFULSET_NAME}-${i}"
  SERVICE_NAME="ollama-ss-${STATEFULSET_NAME}-${i}"
  POD_NAME="${STATEFULSET_NAME}-${i}"

  cat <<EOF | microk8s kubectl apply -f -
apiVersion: v1
kind: PersistentVolume
metadata:
  name: ${PV_NAME}
  labels:
    type: local
spec:
  storageClassName: ${STORAGE_CLASS}
  capacity:
    storage: ${STORAGE_SIZE}
  accessModes:
    - ReadWriteOnce
  hostPath:
    # path: "${STORAGE_PATH}/${i}"
    path: "${STORAGE_PATH}"
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ${PVC_NAME}
  namespace: ${NAMESPACE}
spec:
  storageClassName: ${STORAGE_CLASS}
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: ${STORAGE_SIZE}
---
apiVersion: v1
kind: Service
metadata:
  name: ${SERVICE_NAME}
  namespace: ${NAMESPACE}
spec:
  type: NodePort
  selector:
    statefulset.kubernetes.io/pod-name: ${POD_NAME}
  ports:
  - port: 11434
    targetPort: 11434
    nodePort: $((30000 + i))
EOF
done

# Apply the StatefulSet
microk8s kubectl apply -f sset.yaml