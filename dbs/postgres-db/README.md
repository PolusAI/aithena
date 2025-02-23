# PostGres DB

This projects provide deployments for postgres using:
    - docker compose
    - helm charts

## Configure 

Copy and rename `.env-sample` to `.env` and update values according
to your configuration.

## Deploy 

```shell
helm dependency update
helm install ${RELEASE} . -n ${NAMESPACE}
```

## Admin

docker pull dpage/pgadmin4

docker run -p 30980:80 \
    -e 'PGADMIN_DEFAULT_EMAIL=${ADMIN_EMAIL}' \
    -e 'PGADMIN_DEFAULT_PASSWORD=${ADMIN_PASSWORD}' \
    -d dpage/pgadmin4 

