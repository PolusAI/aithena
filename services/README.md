# aithena-services (v0.1.0-dev1)

For information on how to set up your environment, [see here](/docs/env.md).

## Launch the test chat dashboard

1. Save `.env-sample` as `.env`
2. Modify `.env` to use your API keys and point to ollama. If you will not use one of the services, comment it out.
3. If running locally, modify `SOLARA_ROOT_PATH` by replacing `${JUPYTERHUB_SERVICE_PREFIX}/proxy/8000/` with the local URL (including port). It is important to keep the `dashboards/chat/` path in the URL.
4. Install uvicorn: `pip install uvicorn`
5. Launch the API: `uvicorn api.main:app`
6. Go to the location where the API is launched, and add `dashboards/chat/` to the path (make sure to include the trailing `/`)