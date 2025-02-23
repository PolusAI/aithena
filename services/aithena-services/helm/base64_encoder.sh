#!/bin/bash

# Check if the input file is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <env_file>"
  exit 1
fi

ENV_FILE=$1

# Check if the input file exists
if [ ! -f "$ENV_FILE" ]; then
  echo "File not found: $ENV_FILE"
  exit 1
fi

# Read the env file and convert values to Base64
while IFS='=' read -r key value; do
  # Skip comments and empty lines
  if [[ "$key" =~ ^#.*$ ]] || [[ -z "$key" ]]; then
    continue
  fi

  # Encode the value to Base64
  encoded_value=$(echo -n "$value" | base64)

  # Print the key and encoded value
  echo "$key=$encoded_value"
done < "$ENV_FILE"