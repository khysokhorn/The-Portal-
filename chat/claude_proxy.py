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



@app.get("/v1/models")
async def list_models():
    # Return a dummy model list so Claude is happy
    return {
        "data": [
            {"id": "gemini-3-flash", "object": "model", "created": 1677610602, "owned_by": "local"}
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

        openai_body = {
            "model": "gemini-3-flash", # Force use your local model
            "messages": openai_messages,
            "max_tokens": anthropic_body.get("max_tokens", 4096),
            "stream": False # TUI usually prefers non-streaming for the first handshake
        }

        # Filter and clean headers
        headers = {k: v for k, v in request.headers.items() if v is not None}
        auth_header = headers.get("Authorization", "")
        
        # Strip the Claude "login trick" prefix before sending to local server
        if "sk-ant-api03-" in auth_header:
            auth_header = auth_header.replace("sk-ant-api03-", "")
        
        if not auth_header:
            auth_header = f"Bearer {LOCAL_API_KEY}" # Use the key from .env


        async with httpx.AsyncClient() as client:
            response = await client.post(
                LOCAL_SERVER_URL,
                json=openai_body,
                headers={"Authorization": auth_header, "Content-Type": "application/json"},
                timeout=60.0
            )

            
            if response.status_code == 200:
                openai_res = response.json()
                choice = openai_res.get("choices", [{}])[0]
                content_text = choice.get("message", {}).get("content", "No response from local model.")
                
                return {
                    "id": openai_res.get("id", "msg_local"),
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "text", "text": content_text}],
                    "model": "claude-3-5-sonnet-20241022", # Tell Claude what it wants to hear
                    "usage": {
                        "input_tokens": openai_res.get("usage", {}).get("prompt_tokens", 0),
                        "output_tokens": openai_res.get("usage", {}).get("completion_tokens", 0)
                    }
                }
            else:
                print(f"Error from local server: {response.status_code} - {response.text}")
                return Response(content=response.text, status_code=response.status_code)
    except Exception as e:
        print(f"Proxy Error: {e}")
        return Response(content=str(e), status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=4000)
