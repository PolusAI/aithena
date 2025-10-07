#!/bin/bash
# daily-update.sh - Script to run OpenAlex daily updates
# Usage: ./daily-update.sh [from_date]
# If from_date is not provided, it will use the last successful update date

set -e

# Configuration
API_URL="http://localhost:8000/update"
JOB_TYPE="WORKS_UPDATE"
FROM_DATE="$1"

# Function to format the request body
build_request() {
    if [ -z "$FROM_DATE" ]; then
        # No date provided, use automatic date detection
        echo '{"job_type": "'"$JOB_TYPE"'"}'
    else
        # Use the provided date
        echo '{"job_type": "'"$JOB_TYPE"'", "from_date": "'"$FROM_DATE"'"}'
    fi
}

# Function to check if API is available
check_api() {
    echo "Checking if API is available..."
    if curl -s "http://localhost:8000/health" | grep -q "ok"; then
        echo "API is available"
        return 0
    else
        echo "Error: API is not available at $API_URL"
        return 1
    fi
}

# Main execution
echo "Starting OpenAlex daily update at $(date)"

# Build the request body
REQUEST_BODY=$(build_request)
echo "Request body: $REQUEST_BODY"

# Check if API is available
if ! check_api; then
    if [ -n "$(command -v docker)" ]; then
        echo "API not responding. Checking container status..."
        
        # Check if container exists
        if docker container inspect openalex-api &>/dev/null; then
            # Container exists, check status
            CONTAINER_STATUS=$(docker container inspect --format='{{.State.Status}}' openalex-api)
            echo "Container status: $CONTAINER_STATUS"
            
            if [ "$CONTAINER_STATUS" != "running" ]; then
                echo "Attempting to start API container..."
                docker start openalex-api
                sleep 10  # Wait for container to start
                
                # Check again if API is available
                if ! check_api; then
                    echo "API still not available after starting container. Check logs:"
                    docker logs --tail 50 openalex-api
                    exit 1
                fi
            else
                echo "Container is running but API is not responding. Check logs:"
                docker logs --tail 50 openalex-api
                exit 1
            fi
        else
            # Container doesn't exist, try to start docker compose
            if [ -f "docker-compose.yml" ]; then
                echo "Container doesn't exist. Attempting to start services with docker compose..."
                docker compose up -d
                sleep 15  # Wait for services to initialize
                
                # Check again if API is available
                if ! check_api; then
                    echo "API still not available after starting services. Check logs:"
                    docker compose logs --tail 50 openalex-api
                    exit 1
                fi
            else
                echo "Container doesn't exist and no docker-compose.yml found."
                echo "Please start the API service first."
                exit 1
            fi
        fi
    else
        echo "Docker not available. Please ensure the API service is running."
        exit 1
    fi
fi

# Send update request
echo "Sending update request to $API_URL..."
RESPONSE=$(curl -s -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d "$REQUEST_BODY")

# Check response
JOB_ID=$(echo $RESPONSE | grep -o '"id":[0-9]*' | cut -d':' -f2)

if [ -n "$JOB_ID" ]; then
    echo "Update job started successfully with ID: $JOB_ID"
    echo "Monitor progress with: curl http://localhost:8000/jobs/$JOB_ID"
    exit 0
else
    echo "Error starting update job. Response:"
    echo "$RESPONSE"
    exit 1
fi 