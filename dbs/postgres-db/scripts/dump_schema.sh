#!/bin/bash

# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)

# Dump the openalex schema only (without data)
pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -p $POSTGRES_PORT -n openalex -s -f openalex_schema.sql