#!/usr/bin/env bash
# One-time GCP project setup.
# Run ONCE per project to enable APIs and create secrets.
#
# After running this:
#   1. Create your GitHub App (see README)
#   2. Add the secret values via `gcloud secrets versions add`
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

echo "→ Granting Cloud Build service account permissions to deploy"
CLOUDBUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUDBUILD_SA}" \
    --role="roles/run.admin" >/dev/null
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUDBUILD_SA}" \
    --role="roles/iam.serviceAccountUser" >/dev/null

echo ""
echo "✓ Setup complete. Next steps:"
echo ""
echo "  1. Register your GitHub App at:"
echo "     https://github.com/settings/apps/new"
echo ""
echo "  2. From the App's settings page, collect:"
echo "     - App ID (6-digit number, top of page)"
echo "     - Webhook secret (the random string you set)"
echo "     - Private key (.pem file, generate at bottom of page)"
echo ""
echo "  3. Add the values as secret versions:"
echo "     echo -n \"YOUR_APP_ID\" | gcloud secrets versions add github-app-id \\"
echo "         --data-file=- --project $PROJECT_ID"
echo ""
echo "     echo -n \"YOUR_WEBHOOK_SECRET\" | gcloud secrets versions add github-webhook-secret \\"
echo "         --data-file=- --project $PROJECT_ID"
echo ""
echo "     gcloud secrets versions add github-private-key \\"
echo "         --data-file=path/to/key.pem --project $PROJECT_ID"
echo ""
echo "  4. Deploy ONCE via console (first-time only) so secrets/volumes get attached:"
echo "     - Cloud Run console → axyloid → Edit & Deploy New Revision"
echo "     - Variables & Secrets: add GITHUB_APP_ID, GITHUB_WEBHOOK_SECRET as secret env vars"
echo "     - Variables & Secrets: add GITHUB_PRIVATE_KEY_PATH=/secrets/github-private-key/app.pem as plain env"
echo "     - Volumes: mount github-private-key:latest at /secrets/github-private-key, path app.pem"
echo "     - Deploy"
echo ""
echo "  5. Subsequent deploys: ./deploy/deploy.sh (or push to trigger Cloud Build)"
echo "     These only update the image — secrets/volumes persist."