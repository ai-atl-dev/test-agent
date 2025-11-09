import os
import json
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Content

app = FastAPI()

# Load environment variables
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "heyai-backend")
VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
VERTEX_AI_MODEL = os.getenv("VERTEX_AI_MODEL", "gemini-2.5-flash")

# Set up Application Default Credentials if path is provided
ADC_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/Users/varunahlawat/Work/AI_ATL_25/application_default_credentials.json")
if os.path.exists(ADC_PATH):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ADC_PATH

# Load Koozie context
KOOZIE_CONTEXT = ""
try:
    with open("context.txt", "r", encoding="utf-8") as f:
        KOOZIE_CONTEXT = f.read()
except FileNotFoundError:
    print("Warning: context.txt not found. Running without context.")

# Initialize Vertex AI
model = None
try:
    vertexai.init(project=GCP_PROJECT_ID, location=VERTEX_AI_LOCATION)
    # Create system instruction with Koozie context
    system_instruction = f"""You are a helpful customer service assistant for Koozie Group, a leading supplier in the promotional products industry.

Your role is to provide accurate, friendly, and helpful support to customers regarding Koozie Group's products, services, ordering, and general inquiries.

Here is comprehensive information about Koozie Group:

{KOOZIE_CONTEXT}

When answering questions:
1. Be concise, conversational, friendly, professional, and helpful
2. Use the provided context to answer questions accurately
3. If you don't know something specific (like exact current pricing or inventory), direct customers to check the distributor portal at kooziegroup.com or call customer service
4. Always verify current pricing and availability when possible
5. Be concise but thorough
6. Keep responses natural and conversational, as if you are talking to your best friend on a phone call after a couple of weeks!

Don't talk for way too long. Keep your responses concise and to the point.
"""
    
    model = GenerativeModel(
        VERTEX_AI_MODEL,
        system_instruction=system_instruction
    )
except Exception as e:
    print(f"Warning: Failed to initialize Vertex AI: {e}")
    model = None


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[list] = None


class ChatResponse(BaseModel):
    status: str
    message: Optional[str] = None


def build_contents(message: str, conversation_history: Optional[List] = None) -> List[Content]:
    """Build contents list for Vertex AI API."""
    contents = []
    
    # Add conversation history if provided
    if conversation_history:
        for msg in conversation_history:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                role = msg["role"]
                text = msg["content"]
                if role == "user":
                    contents.append(Content(role="user", parts=[Part.from_text(text)]))
                elif role == "model" or role == "assistant":
                    contents.append(Content(role="model", parts=[Part.from_text(text)]))
    
    # Add current user message
    contents.append(Content(role="user", parts=[Part.from_text(message)]))
    
    return contents


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "project_id": GCP_PROJECT_ID,
        "location": VERTEX_AI_LOCATION,
        "model": VERTEX_AI_MODEL,
        "context_loaded": len(KOOZIE_CONTEXT) > 0,
        "vertex_ai_initialized": model is not None
    }


@app.post("/chat", response_class=StreamingResponse)
async def chat_stream(request: ChatRequest):
    """
    Chat endpoint with streaming response.
    Returns tokens as they are generated for minimal latency.
    """
    if model is None:
        raise HTTPException(
            status_code=500,
            detail="Vertex AI model not initialized. Check your GCP credentials and configuration."
        )

    try:
        # Build contents for the API
        contents = build_contents(request.message, request.conversation_history)

        # Stream response
        def generate():
            try:
                response = model.generate_content(
                    contents,
                    generation_config={
                        "temperature": 0.7,
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 2048,
                    },
                    stream=True
                )
                
                for chunk in response:
                    # Extract text from chunk (handle different response formats)
                    chunk_text = None
                    if hasattr(chunk, 'text') and chunk.text:
                        chunk_text = chunk.text
                    elif hasattr(chunk, 'candidates') and chunk.candidates:
                        if hasattr(chunk.candidates[0], 'content') and chunk.candidates[0].content:
                            if hasattr(chunk.candidates[0].content, 'parts') and chunk.candidates[0].content.parts:
                                if hasattr(chunk.candidates[0].content.parts[0], 'text'):
                                    chunk_text = chunk.candidates[0].content.parts[0].text
                    
                    if chunk_text:
                        # Send each chunk as Server-Sent Events format
                        yield f"data: {json.dumps({'text': chunk_text, 'done': False})}\n\n"
                
                # Send completion signal
                yield f"data: {json.dumps({'text': '', 'done': True})}\n\n"
                
            except Exception as e:
                error_msg = json.dumps({"error": str(e), "done": True})
                yield f"data: {error_msg}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")


@app.post("/chat/sync", response_model=ChatResponse)
async def chat_sync(request: ChatRequest):
    """
    Synchronous chat endpoint (non-streaming).
    Useful for testing or when streaming is not needed.
    """
    if model is None:
        raise HTTPException(
            status_code=500,
            detail="Vertex AI model not initialized. Check your GCP credentials and configuration."
        )

    try:
        # Build contents for the API
        contents = build_contents(request.message, request.conversation_history)

        # Generate response
        response = model.generate_content(
            contents,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
        )

        return ChatResponse(
            status="success",
            message=response.text if hasattr(response, 'text') and response.text else "No response generated"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)

