# Cloud Build & GCP Configuration Guide

## 🔧 Cloud Build Trigger Substitution Variables

Configure these in your **Cloud Build Trigger** settings:

### Required Substitution Variables

| Variable | Default Value | Description | Required? |
|----------|--------------|-------------|-----------|
| `_REGION` | `us-central1` | GCP region for Artifact Registry and Cloud Run | ✅ Yes |
| `_REPO_NAME` | `test-agent` | Artifact Registry repository name | ✅ Yes |
| `_IMAGE_NAME` | `koozie-agent` | Docker image name | ✅ Yes |
| `_SERVICE_NAME` | `koozie-agent-service` | Cloud Run service name | ✅ Yes |

### Built-in Cloud Build Variables (Auto-provided)

These are automatically available - **no configuration needed**:

- `$PROJECT_ID` - Your GCP project ID (e.g., `heyai-backend`)
- `$BUILD_ID` - Unique build ID
- `$SHORT_SHA` - Git commit SHA (if using git trigger)

---

## 🔐 GCP Project Setup

### 1. Artifact Registry Repository

**Create the repository** (if it doesn't exist):

```bash
gcloud artifacts repositories create test-agent \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker repository for Koozie Agent"
```

**Required IAM Permissions:**
- Cloud Build service account needs: `Artifact Registry Writer`
- (Automatically granted if using Cloud Build)

### 2. Cloud Run Service Account

**Create or use a service account** for Cloud Run:

```bash
# Create service account (if needed)
gcloud iam service-accounts create koozie-agent-sa \
  --display-name="Koozie Agent Service Account"

# Grant Vertex AI User role
gcloud projects add-iam-policy-binding heyai-backend \
  --member="serviceAccount:koozie-agent-sa@heyai-backend.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

**Required Roles:**
- `roles/aiplatform.user` - To call Vertex AI Gemini API
- (Default Cloud Run service account can be used if it has this role)

**Update Cloud Run deployment** to use the service account:

```bash
gcloud run services update koozie-agent-service \
  --service-account=koozie-agent-sa@heyai-backend.iam.gserviceaccount.com \
  --region=us-central1
```

### 3. Cloud Build Service Account Permissions

The Cloud Build service account (`PROJECT_NUMBER@cloudbuild.gserviceaccount.com`) needs:

**Required Roles:**
- `roles/run.admin` - To deploy to Cloud Run
- `roles/iam.serviceAccountUser` - To use the Cloud Run service account
- `roles/storage.admin` - To push to Artifact Registry (usually auto-granted)

**Grant permissions:**

```bash
PROJECT_NUMBER=$(gcloud projects describe heyai-backend --format="value(projectNumber)")

gcloud projects add-iam-policy-binding heyai-backend \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding heyai-backend \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

---

## 🚫 Secrets Required: **NONE**

**No Secret Manager secrets are needed** for this deployment because:

1. ✅ Vertex AI authentication uses the Cloud Run service account (via Application Default Credentials)
2. ✅ Environment variables are set directly in Cloud Run (no sensitive data)
3. ✅ No API keys or tokens need to be stored in Secret Manager

---

## 📋 Cloud Build Trigger Configuration

### Trigger Settings:

1. **Name:** `test-agent-trigger` (or your preferred name)
2. **Event:** Push to branch (e.g., `main`)
3. **Source:** Connect your repository
4. **Configuration:** Cloud Build configuration file
5. **Location:** `test-agent/cloudbuild.yaml`

### Substitution Variables (in Trigger UI):

```
_REGION = us-central1
_REPO_NAME = test-agent
_IMAGE_NAME = koozie-agent
_SERVICE_NAME = koozie-agent-service
```

---

## ✅ Pre-Deployment Checklist

Before your first deployment, ensure:

- [ ] Artifact Registry repository `test-agent` exists in `us-central1`
- [ ] Cloud Build service account has `roles/run.admin` and `roles/iam.serviceAccountUser`
- [ ] Cloud Run service account has `roles/aiplatform.user` (or use default with this role)
- [ ] Vertex AI API is enabled in your project
- [ ] Cloud Run API is enabled in your project
- [ ] Artifact Registry API is enabled in your project

---

## 🧪 Test Deployment

After configuring, test the trigger:

```bash
# Trigger a build manually
gcloud builds submit --config=cloudbuild.yaml

# Or push to your repository to trigger automatically
git push origin main
```

---

## 📝 Environment Variables in Cloud Run

These are automatically set by the Cloud Build script:

- `GCP_PROJECT_ID` = `$PROJECT_ID` (your GCP project)
- `VERTEX_AI_LOCATION` = `us-central1` (from `_REGION`)
- `VERTEX_AI_MODEL` = `gemini-2.5-flash` (hardcoded)

**No manual configuration needed** - they're set during deployment!

---

## 🔍 Troubleshooting

### If deployment fails:

1. **Check Cloud Build logs** in GCP Console
2. **Verify service account permissions**:
   ```bash
   gcloud projects get-iam-policy heyai-backend \
     --flatten="bindings[].members" \
     --filter="bindings.members:*cloudbuild*"
   ```

3. **Verify Artifact Registry exists**:
   ```bash
   gcloud artifacts repositories list --location=us-central1
   ```

4. **Check Cloud Run service account**:
   ```bash
   gcloud run services describe koozie-agent-service \
     --region=us-central1 \
     --format="value(spec.template.spec.serviceAccountName)"
   ```

