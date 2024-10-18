# Ask Aithena Deployment

This is a multinodes deployment of ask-aithena.
It aims to run the AI models on a gpu node,
and the rest of the stack on a regular cpu node.

## How to run

`run-ask-aithena.sh -g $GPUS` 

with $GPUS the number of gpus to run ollama on.

## services deployed

This script run to sbatch jobs : `ollama.sh` and `ask-aithena.sh`

We deploy 5 long running services:
- ollama
- qdrant
- aithena-services
- ask-aithena-agent
- ask-aithena-app

## data

All data needed are found in `.data`:

`.data/ollama-data` contains all the model files
`.data/qdrant` contains all the db files

## container images

Singularity images can all be found in `/vast/projects/aithena/multinodes/.containers`

## Port-forwarding the dashboard

The log should tell you were the dashboard has been deployed:

`aithena app available at : http://node15.dali.hpc.ncats.nih.gov:8765`

Just port forward from your local machine:

`ssh -L 8765:node15.dali.hpc.ncats.nih.gov:8765 username@dali.ncats.nih.gov`

Ask aithena!