#!/usr/bin/env bash
# Cloud Run deploy script.
# Run from the project root: ./deploy/deploy.sh
#
# Required environment (set these in your shell or .env before running):
#   GCP_PROJECT_ID  — your Google Cloud project id
#   GCP_REGION      — e.g. us-central1
#
# Assumes you've already run `gcloud auth login` and created the secrets
# in Secret Manager (see deploy/setup-once.sh below).

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:?GCP_PROJECT_ID not set}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="axyloid-bots"

echo "→ Project: $PROJECT_ID"
echo "→ Region:  $REGION"
echo "→ Service: $SERVICE_NAME"
echo ""

echo "→ Building and deploying via gcloud (one command, no manual Docker push)"
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 60 \
    --concurrency 80 \
    --max-instances 5 \
    --min-instances 0 \
    --set-secrets "GITHUB_APP_ID=github-app-id:latest,GITHUB_WEBHOOK_SECRET=github-webhook-secret:latest" \
    --set-secrets "GITHUB_PRIVATE_KEY_PATH=/secrets/github-private-key:latest" \
    --update-env-vars "LOG_LEVEL=INFO"

echo ""
echo "→ Deployment complete"
gcloud run services describe "$SERVICE_NAME" \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --format="value(status.url)"