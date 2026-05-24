#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:?GCP_PROJECT_ID not set}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="axyloid"
IMAGE="us-central1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/$SERVICE_NAME:latest"

echo "→ Building image: $IMAGE"
gcloud builds submit \
    --tag "$IMAGE" \
    --project "$PROJECT_ID"

echo "→ Updating service $SERVICE_NAME with new image (preserves env/secrets/volumes)"
gcloud run services update "$SERVICE_NAME" \
    --image "$IMAGE" \
    --region "$REGION" \
    --project "$PROJECT_ID"

echo ""
echo "✓ Deployment complete"
gcloud run services describe "$SERVICE_NAME" \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --format="value(status.url)"