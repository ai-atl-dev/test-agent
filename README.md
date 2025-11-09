# Koozie Customer Service Agent

A FastAPI-based AI agent that provides customer service support for Koozie Group using Vertex AI's Gemini 2.5 Flash model with streaming responses for minimal latency.

## Features

- ✅ **Streaming Responses**: Token-by-token streaming for voice applications (minimizes latency)
- ✅ **Koozie Context**: Full product catalog and support information loaded into every request
- ✅ **Two Endpoints**: `/chat` (streaming) and `/chat/sync` (non-streaming)
- ✅ **Hot Reload Development**: Docker Compose setup for rapid testing
- ✅ **GCP Ready**: Cloud Build configuration for automated deployment

## Environment Variables

Create a `.env` file (see `.env.example`):

```bash
GCP_PROJECT_ID=heyai-backend
GCP_REGION=us-central1
GCP_PROJECT_NUMBER=127756525541
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-2.5-flash
```

## Quick Start (Development)

### Prerequisites
- Docker and Docker Compose installed
- GCP credentials configured (via `gcloud auth application-default login` or service account)

### Run with Hot Reload

```bash
# Start the development server with hot reload
docker-compose -f docker-compose.dev.yml up

# The server will be available at http://localhost:8080
```

### Test Endpoints

```bash
# Make test script executable
chmod +x test_endpoints.sh

# Run tests
./test_endpoints.sh
```

Or test manually:

```bash
# Health check
curl http://localhost:8080/health

# Streaming chat (for voice apps)
curl -sN -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is a Koozie?"}'

# Synchronous chat (for testing)
curl -X POST http://localhost:8080/chat/sync \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about your pens."}'
```

## API Endpoints

### `GET /health`
Health check endpoint. Returns server status and configuration.

**Response:**
```json
{
  "status": "healthy",
  "project_id": "heyai-backend",
  "location": "us-central1",
  "model": "gemini-2.5-flash",
  "context_loaded": true,
  "vertex_ai_initialized": true
}
```

### `POST /chat` (Streaming)
Streaming chat endpoint. Returns Server-Sent Events (SSE) with tokens as they're generated.

**Request:**
```json
{
  "message": "What products do you offer?",
  "conversation_history": [
    {"role": "user", "content": "Hello"},
    {"role": "model", "content": "Hi! How can I help you?"}
  ]
}
```

**Response:** Server-Sent Events stream
```
data: {"text": "We", "done": false}

data: {"text": " offer", "done": false}

data: {"text": " a wide", "done": false}

...

data: {"text": "", "done": true}
```

### `POST /chat/sync` (Non-Streaming)
Synchronous chat endpoint. Returns complete response.

**Request:** Same as `/chat`

**Response:**
```json
{
  "status": "success",
  "message": "We offer a wide range of promotional products..."
}
```

## Deployment to GCP

### Prerequisites
- GCP project with Vertex AI API enabled
- Artifact Registry repository created
- Cloud Build trigger configured

### Deploy

The `cloudbuild.yaml` is configured to:
1. Build Docker image
2. Push to Artifact Registry
3. Deploy to Cloud Run

Simply push to your repository and the Cloud Build trigger will handle deployment.

### Manual Deployment

```bash
# Build and push image
gcloud builds submit --config cloudbuild.yaml

# Or deploy directly to Cloud Run
gcloud run deploy koozie-agent-service \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=heyai-backend,VERTEX_AI_LOCATION=us-central1,VERTEX_AI_MODEL=gemini-2.5-flash"
```

## Project Structure

```
test-agent/
├── main.py                 # FastAPI server with Vertex AI integration
├── context.txt            # Koozie Group product catalog and support info
├── requirements.txt       # Python dependencies
├── Dockerfile            # Production container
├── Dockerfile.dev        # Development container
├── docker-compose.dev.yml # Hot reload development setup
├── cloudbuild.yaml       # GCP Cloud Build configuration
├── .env.example          # Environment variable template
├── .gitignore            # Git ignore rules
└── test_endpoints.sh     # Test script
```

## Notes

- The server loads `context.txt` at startup and includes it in every request via system instructions
- Streaming endpoint uses Server-Sent Events (SSE) for real-time token delivery
- GCP credentials are automatically detected via Application Default Credentials
- The service is configured for Cloud Run deployment with auto-scaling