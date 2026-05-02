import uvicorn
from fastapi import FastAPI, Request, Response
import httpx
import json

app = FastAPI()

import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Your local OpenAI-compatible server (can be overridden by environment variable)
LOCAL_SERVER_URL = os.getenv("LOCAL_SERVER_URL", "http://host.docker.internal:8045/v1/chat/completions")
LOCAL_API_KEY = os.getenv("LOCAL_API_KEY", "sk-local-key")



# Cache for failed models to avoid retrying them in the same session
FAILED_MODELS = set()
PREFERRED_MODEL = os.getenv("PREFERRED_MODEL")

async def get_prioritized_models():
    """Fetch models from the local server and prioritize them: claude > flash > pro"""
    try:
        # Derive models endpoint from chat completions URL
        models_url = LOCAL_SERVER_URL.replace("/chat/completions", "/models")
        headers = {"Authorization": f"Bearer {LOCAL_API_KEY}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(models_url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                data = response.json().get("data", [])
                model_ids = [m["id"] for m in data if m["id"] not in FAILED_MODELS]
                
                # If everything is filtered out, clear the cache and try again
                if not model_ids and data:
                    print("All models previously failed. Clearing failure cache.")
                    FAILED_MODELS.clear()
                    model_ids = [m["id"] for m in data]

                if PREFERRED_MODEL and PREFERRED_MODEL in model_ids:
                    # Move preferred model to the front
                    model_ids.remove(PREFERRED_MODEL)
                    model_ids.insert(0, PREFERRED_MODEL)
                    return model_ids

                # Prioritize based on keywords and version
                def get_priority_tuple(model_id):
                    m = model_id.lower()
                    
                    # Category Priority
                    if "claude" in m:
                        cat = 0
                    elif "flash" in m:
                        cat = 1
                    elif "pro" in m:
                        cat = 2
                    else:
                        cat = 3
                    
                    # Thinking/Reasoning Priority
                    thinking = 0 if ("thinking" in m or "reasoning" in m) else 1
                    
                    return (cat, thinking)

                # Step 1: Sort everything by name descending to put newer versions first
                model_ids.sort(reverse=True)
                
                # Step 2: Perform a stable sort using our category and thinking priorities
                sorted_models = sorted(model_ids, key=get_priority_tuple)
                
                return sorted_models
            else:
                print(f"Failed to fetch models: {response.status_code}")
    except Exception as e:
        print(f"Error fetching models: {e}")
    
    # Fallback if fetching fails
    return [PREFERRED_MODEL] if PREFERRED_MODEL else ["claude-3-5-sonnet-20241022", "gemini-1.5-flash", "gemini-1.5-pro"]

@app.get("/v1/models")
async def list_models():
    models = await get_prioritized_models()
    return {
        "data": [
            {"id": model, "object": "model", "created": 1677610602, "owned_by": "local"}
            for model in models
        ]
    }

@app.post("/v1/messages")
async def proxy_anthropic_to_openai(request: Request):
    try:
        anthropic_body = await request.json()
        print(f"--- Incoming Claude Request ---")
        
        openai_messages = []
        # Convert Anthropic system prompt if present
        if "system" in anthropic_body:
            openai_messages.append({"role": "system", "content": anthropic_body["system"]})
            
        for msg in anthropic_body.get("messages", []):
            role = msg.get("role")
            content = msg.get("content")
            if isinstance(content, list):
                text_content = "".join([block.get("text", "") for block in content if block.get("type") == "text"])
                openai_messages.append({"role": role, "content": text_content})
            else:
                openai_messages.append({"role": role, "content": content})

        # Filter and clean headers
        headers = {k: v for k, v in request.headers.items() if v is not None}
        auth_header = headers.get("Authorization", "")
        
        # Strip the Claude "login trick" prefix before sending to local server
        if "sk-ant-api03-" in auth_header:
            auth_header = auth_header.replace("sk-ant-api03-", "")
        
        if not auth_header:
            auth_header = f"Bearer {LOCAL_API_KEY}" # Use the key from .env

        async with httpx.AsyncClient() as client:
            last_error = None
            models = await get_prioritized_models()
            for model_name in models:
                print(f"Attempting with model: {model_name}")
                openai_body = {
                    "model": model_name,
                    "messages": openai_messages,
                    "max_tokens": anthropic_body.get("max_tokens", 4096),
                    "stream": False
                }

                try:
                    response = await client.post(
                        LOCAL_SERVER_URL,
                        json=openai_body,
                        headers={"Authorization": auth_header, "Content-Type": "application/json"},
                        timeout=120.0 # Increased timeout for pro models
                    )

                    if response.status_code == 200:
                        print(f"Success with model: {model_name}")
                        openai_res = response.json()
                        choice = openai_res.get("choices", [{}])[0]
                        content_text = choice.get("message", {}).get("content", "No response from local model.")
                        
                        return {
                            "id": openai_res.get("id", "msg_local"),
                            "type": "message",
                            "role": "assistant",
                            "content": [{"type": "text", "text": content_text}],
                            "model": "claude-3-5-sonnet-20241022", # Always tell Claude it was Claude
                            "usage": {
                                "input_tokens": openai_res.get("usage", {}).get("prompt_tokens", 0),
                                "output_tokens": openai_res.get("usage", {}).get("completion_tokens", 0)
                            }
                        }
                    elif response.status_code == 503 or response.status_code == 404:
                        print(f"Model {model_name} failed with status {response.status_code}. Blacklisting.")
                        FAILED_MODELS.add(model_name)
                        last_error = response
                    else:
                        print(f"Model {model_name} failed with status {response.status_code}: {response.text}")
                        last_error = response
                except Exception as e:
                    print(f"Error calling {model_name}: {e}")
                    last_error = e
            
            # If we get here, all models failed
            if isinstance(last_error, Response):
                return Response(content=last_error.text, status_code=last_error.status_code)
            else:
                return Response(content=str(last_error), status_code=500)

    except Exception as e:
        print(f"Proxy Error: {e}")
        return Response(content=str(e), status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000)

