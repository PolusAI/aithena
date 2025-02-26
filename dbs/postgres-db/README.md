# PostGres DB

This projects provide deployments for postgres using:
    - docker compose
    - helm charts


## Configure 

Copy and rename `.env-sample` to `.env` and update values according
to your configuration.

Create a secret from this `.env` file

```shell
kubectl create secret generic aithenadb-secret --from-env-file=.env -n namespace
```

`postgresql.conf` is just a example of postgres configuration but is currenlty not used.
We could use it in our deployment by copying it in the proper location at startup but
for now we manually update values with psql's `SET` command.


## Deploy 

### Regular Deployment

```shell
helm dependency update
helm install ${RELEASE} . -n ${NAMESPACE}
```

### Large Scale Deployment

Rename `custom-depl-sample.yaml` to `custom-depl.yaml`

Update config and deply :

```shell
kubectl apply -f custom-depl.yaml
```


## Admin

```shell
docker pull dpage/pgadmin4
```

```shell
docker run -p 30980:80 \
    -e 'PGADMIN_DEFAULT_EMAIL=${ADMIN_EMAIL}' \
    -e 'PGADMIN_DEFAULT_PASSWORD=${ADMIN_PASSWORD}' \
    -d dpage/pgadmin4 
```


## Dump open alex schema


```shell 
mk exec $podname -n $namespace -- sh -c "pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -p $POSTGRES_PORT -n openalex -s -f openalex_schema.sql"

mk cp $namespace/$podname:openalex_schema.sql openalex_schema.sql
```


## Structure

`schemas` contains the original openalex schemas and updated versions.
`scripts` contains various admin scripts 
`helm` contains helm deployment files 
`docker` contains docker compose files
