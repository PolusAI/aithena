echo "DB_PORT: $DB_PORT"
echo "DOC_COLLECTION: $DOC_COLLECTION"
echo "EMBED_MODEL: $EMBED_MODEL"
echo "CHAT_MODEL: $CHAT_MODEL"

# qdrant
srun --ntasks=1 --nodes=1 singularity run --writable-tmpfs --bind ${QDRANT_DATA_PATH}:/qdrant/storage --bind ${QDRANT_SNAPSHOTS_PATH}:/qdrant/snapshots ${QDRANT_IMAGE} &
echo "Running qdrant on ${SECOND_NODE}"

# aithena services
srun --ntasks=1 --nodes=1 singularity run --pwd /aithena_services_src/ ${AITHENA_SERVICES_IMAGE} uvicorn --host 0.0.0.0 --port 9000 api.main:app &
echo "Running ollama on ${SECOND_NODE}"

# ask aithena agent
srun --ntasks=1 --nodes=1 singularity run ${ASK_AITHENA_AGENT_IMAGE} &
echo "Running ask agent on ${SECOND_NODE}"

# ask aithena apps
srun --ntasks=1 --nodes=1 singularity run --pwd /ask_aithena_dashboard/ --writable-tmpfs ${ASK_AITHENA_DASHBOARD_IMAGE} &
echo "Running ask app on ${SECOND_NODE}"

wait  # Wait for all child jobs to finish