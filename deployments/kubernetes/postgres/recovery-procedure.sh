#!/bin/bash
# PostgreSQL Recovery Procedure
# This script helps recover from PostgreSQL initialization issues

echo "PostgreSQL Recovery Procedure"
echo "============================="
echo ""
echo "This script will help you recover your PostgreSQL deployment."
echo "Make sure you're in the postgres directory before running."
echo ""

# Step 1: Check current state
echo "Step 1: Checking current PostgreSQL deployment status..."
echo "mkk get statefulset -n box askaithena-db"
echo "mkk get pods -n box -l app=askaithena-db"
echo ""
read -p "Press Enter to continue after checking the status..."

# Step 2: Stop current deployment
echo ""
echo "Step 2: Stopping current PostgreSQL StatefulSet..."
echo "Run: mkk delete statefulset -n box askaithena-db"
echo ""
read -p "Press Enter after deleting the StatefulSet..."

# Step 3: Ensure all pods are terminated
echo ""
echo "Step 3: Ensuring all PostgreSQL pods are terminated..."
echo "Run: mkk get pods -n box -l app=askaithena-db"
echo "Wait for all pods to disappear before continuing."
echo ""
read -p "Press Enter when all pods are gone..."

# Step 4: Deploy debug pod to inspect
echo ""
echo "Step 4: Deploying debug pod to inspect current data directory..."
echo "Run: mkk apply -f postgres-debug-pod.yaml"
echo ""
echo "Then exec into the pod to check:"
echo "mkk exec -it -n box postgres-debug -- /bin/sh"
echo ""
echo "Inside the pod, run:"
echo "  ls -la /data/"
echo "  du -sh /data/*"
echo "  exit"
echo ""
read -p "Press Enter after inspecting the data directory..."

# Step 5: Clean debug pod
echo ""
echo "Step 5: Removing debug pod..."
echo "Run: mkk delete pod -n box postgres-debug"
echo ""
read -p "Press Enter after deleting the debug pod..."

# Step 6: Deep clean the data directory
echo ""
echo "Step 6: Running deep cleanup of the data directory..."
echo "Run: mkk apply -f postgres-deep-clean.yaml"
echo ""
echo "Check the logs to ensure cleanup was successful:"
echo "mkk logs -n box postgres-deep-clean -f"
echo ""
echo "Wait for 'Cleanup complete!' message."
echo ""
read -p "Press Enter after seeing 'Cleanup complete!'..."

# Step 7: Remove cleanup pod
echo ""
echo "Step 7: Removing cleanup pod..."
echo "Run: mkk delete pod -n box postgres-deep-clean"
echo ""
read -p "Press Enter after deleting the cleanup pod..."

# Step 8: Deploy fixed StatefulSet
echo ""
echo "Step 8: Deploying fixed PostgreSQL StatefulSet..."
echo "Run: mkk apply -f statefulset-fixed.yaml"
echo ""
echo "Monitor the deployment:"
echo "mkk get pods -n box -l app=askaithena-db -w"
echo ""
read -p "Press Enter after the pod shows Running status..."

# Step 9: Check initialization logs
echo ""
echo "Step 9: Checking PostgreSQL initialization logs..."
echo "Run: mkk logs -n box -l app=askaithena-db -c postgres --tail=50"
echo ""
echo "Look for these key messages:"
echo "  - 'The files belonging to this database system will be owned by user \"postgres\"'"
echo "  - 'initdb: ok'"
echo "  - 'CREATE ROLE'"
echo "  - 'CREATE DATABASE'"
echo "  - 'PostgreSQL init process complete; ready for start up'"
echo ""
read -p "Press Enter after confirming successful initialization..."

# Step 10: Test connection
echo ""
echo "Step 10: Testing PostgreSQL connection..."
echo "Try connecting with:"
echo "psql -U AithenaAdmin -h localhost -d askaithena -p 30432"
echo ""
echo "Password: polus2has8"
echo ""
echo "If successful, you should get a psql prompt without errors."
echo ""

echo "Recovery procedure complete!"
echo ""
echo "If you still have issues, check:"
echo "1. Init container logs: mkk logs -n box -l app=askaithena-db -c fix-permissions"
echo "2. Full pod logs: mkk logs -n box -l app=askaithena-db --all-containers"
echo "3. Pod events: mkk describe pod -n box -l app=askaithena-db"
