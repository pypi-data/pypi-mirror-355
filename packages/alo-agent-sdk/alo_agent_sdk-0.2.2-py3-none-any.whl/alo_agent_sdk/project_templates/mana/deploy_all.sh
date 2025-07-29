#!/bin/bash
set -e

# Placeholder deployment script for the 'mana' application.
# This script would be responsible for deploying all components:
# 1. Agent Registry Service
# 2. Time Agent
# 3. Orchestrator Backend
# It would typically use the alo_agent_sdk/scripts/gcp/cloud_run/deploy_cloud_run.sh script
# or similar deployment mechanisms for your chosen cloud provider.

echo "--- Mana Application Deployment ---"

# --- Configuration (User needs to set these) ---
GCP_PROJECT_ID="your-gcp-project-id"
GCP_REGION="us-central1" # Or your preferred region
# Path to the ALO Agent SDK deploy script (if not in PATH)
# Example: ALO_SDK_DEPLOY_SCRIPT="../alo_agent_sdk/scripts/gcp/cloud_run/deploy_cloud_run.sh"
ALO_SDK_DEPLOY_SCRIPT="path/to/alo_agent_sdk/scripts/gcp/cloud_run/deploy_cloud_run.sh"

# --- 1. Deploy Agent Registry Service ---
echo "Deploying Agent Registry Service..."
# Ensure the build context (-c) is correct for the agent_registry
# bash "$ALO_SDK_DEPLOY_SCRIPT" \
#   -s mana-agent-registry \
#   -p "$GCP_PROJECT_ID" \
#   -r "$GCP_REGION" \
#   -c "./agent_registry"
# After deployment, capture the REGISTRY_SERVICE_URL
# REGISTRY_SERVICE_URL=$(gcloud run services describe mana-agent-registry --platform managed --region "$GCP_REGION" --project "$GCP_PROJECT_ID" --format 'value(status.url)')
# if [ -z "$REGISTRY_SERVICE_URL" ]; then
#   echo "Error: Failed to get Agent Registry Service URL."
#   exit 1
# fi
# echo "Agent Registry Service URL: $REGISTRY_SERVICE_URL"
echo "Agent Registry deployment placeholder. REGISTRY_SERVICE_URL will be needed."
REGISTRY_SERVICE_URL="https_your_registry_url_here_a_run_app" # Replace with actual after deploy

# --- 2. Deploy Time Agent ---
echo "Deploying Time Agent..."
# The Time Agent needs the ALO_REGISTRY_URL and its own ALO_AGENT_SERVICE_URL
# Cloud Run provides K_SERVICE and PORT, which can be used to construct ALO_AGENT_SERVICE_URL
# Alternatively, the agent can try to auto-detect or be configured.
# The deploy_cloud_run.sh script can pass environment variables.
# The agent's own service URL is often derived by Cloud Run itself.
# The time_agent/main.py uses ALO_AGENT_SERVICE_URL if set.
# bash "$ALO_SDK_DEPLOY_SCRIPT" \
#   -s mana-time-agent \
#   -p "$GCP_PROJECT_ID" \
#   -r "$GCP_REGION" \
#   -c "./time_agent" \
#   -e "ALO_REGISTRY_URL=$REGISTRY_SERVICE_URL,PORT=8080" # PORT is for uvicorn, Cloud Run handles external mapping
# TIME_AGENT_URL=$(gcloud run services describe mana-time-agent --platform managed --region "$GCP_REGION" --project "$GCP_PROJECT_ID" --format 'value(status.url)')
# echo "Time Agent URL: $TIME_AGENT_URL"
echo "Time Agent deployment placeholder."

# --- 3. Deploy Orchestrator Backend ---
echo "Deploying Orchestrator Backend..."
# The Orchestrator needs the ALO_REGISTRY_URL
# bash "$ALO_SDK_DEPLOY_SCRIPT" \
#   -s mana-orchestrator-backend \
#   -p "$GCP_PROJECT_ID" \
#   -r "$GCP_REGION" \
#   -c "./orchestrator_backend" \
#   -e "ALO_REGISTRY_URL=$REGISTRY_SERVICE_URL,PORT=8000"
# ORCHESTRATOR_URL=$(gcloud run services describe mana-orchestrator-backend --platform managed --region "$GCP_REGION" --project "$GCP_PROJECT_ID" --format 'value(status.url)')
# echo "Orchestrator Backend URL: $ORCHESTRATOR_URL"
# echo "API endpoint for time: $ORCHESTRATOR_URL/api/get_current_time"
echo "Orchestrator Backend deployment placeholder."


echo "------------------------------------------------------------------"
echo "Mana Application deployment script (placeholder) finished."
echo "Please fill in your GCP_PROJECT_ID, GCP_REGION, and ALO_SDK_DEPLOY_SCRIPT path."
echo "Then, uncomment and adapt the deployment commands for each service."
echo "Ensure each service's Dockerfile and requirements are correctly configured."
echo "The Agent Registry must be deployed first to get its URL for other services."
echo "------------------------------------------------------------------"

exit 0
