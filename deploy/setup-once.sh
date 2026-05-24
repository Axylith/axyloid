#!/usr/bin/env bash
# One-time GCP project setup.
# Run ONCE per project to enable APIs and create secrets.
#
# After running this:
#   1. Create your GitHub App (see README)
#   2. Update the secret values via `gcloud secrets versions add`
#   3. Run deploy.sh to deploy

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:?GCP_PROJECT_ID not set}"
REGION="${GCP_REGION:-us-central1}"

echo "→ Enabling required APIs"
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    --project "$PROJECT_ID"

echo "→ Creating secrets (empty placeholders; add real values next)"
for secret in github-app-id github-webhook-secret github-private-key; do
    if gcloud secrets describe "$secret" --project "$PROJECT_ID" &>/dev/null; then
        echo "    $secret already exists, skipping"
    else
        gcloud secrets create "$secret" \
            --replication-policy=automatic \
            --project "$PROJECT_ID"
        echo "    created $secret"
    fi
done

echo "→ Granting Cloud Run service account access to secrets"
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

for secret in github-app-id github-webhook-secret github-private-key; do
    gcloud secrets add-iam-policy-binding "$secret" \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="roles/secretmanager.secretAccessor" \
        --project "$PROJECT_ID" >/dev/null
done

echo ""
echo "→ Setup complete. Next steps:"
echo "    1. Create your GitHub App at https://github.com/settings/apps/new"
echo "    2. Note the App ID and webhook secret"
echo "    3. Download the App's private key (.pem file)"
echo "    4. Add them as secret versions:"
echo "         echo -n \"YOUR_APP_ID\" | gcloud secrets versions add github-app-id --data-file=- --project $PROJECT_ID"
echo "         echo -n \"YOUR_WEBHOOK_SECRET\" | gcloud secrets versions add github-webhook-secret --data-file=- --project $PROJECT_ID"
echo "         gcloud secrets versions add github-private-key --data-file=path/to/key.pem --project $PROJECT_ID"
echo "    5. Run ./deploy/deploy.sh"