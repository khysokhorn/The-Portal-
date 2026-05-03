import uvicorn
from fastapi import FastAPI, Request, Response
import httpx
import json
import os
from dotenv import load_dotenv

app = FastAPI()

# Load environment variables from .env
load_dotenv()

# Your local OpenAI-compatible server
LOCAL_SERVER_URL = os.getenv("LOCAL_SERVER_URL", "http://host.docker.internal:8045/v1/chat/completions")
LOCAL_API_KEY = os.getenv("LOCAL_API_KEY", "sk-local-key")
PREFERRED_MODEL = os.getenv("PREFERRED_MODEL")

# Cache for failed models
FAILED_MODELS = set()

def translate_anthropic_to_openai_messages(anthropic_messages):
    openai_messages = []
    for msg in anthropic_messages:
        role = msg.get("role")
        content = msg.get("content")
        
        if isinstance(content, str):
            openai_messages.append({"role": role, "content": content})
        elif isinstance(content, list):
            # Handle mixed content blocks (text, tool_use, tool_result)
            tool_calls = []
            text_parts = []
            
            for block in content:
                block_type = block.get("type")
                if block_type == "text":
                    text_parts.append(block.get("text", ""))
                elif block_type == "tool_use":
                    tool_calls.append({
                        "id": block.get("id"),
                        "type": "function",
                        "function": {
                            "name": block.get("name"),
                            "arguments": json.dumps(block.get("input", {}))
                        }
                    })
                elif block_type == "tool_result":
                    # Anthropic tool results become a separate message in OpenAI
                    openai_messages.append({
                        "role": "tool",
                        "tool_call_id": block.get("tool_use_id"),
                        "content": str(block.get("content", ""))
                    })
            
            if text_parts or tool_calls:
                msg_obj = {"role": role, "content": " ".join(text_parts) if text_parts else None}
                if tool_calls:
                    msg_obj["tool_calls"] = tool_calls
                openai_messages.append(msg_obj)
    
    return openai_messages

def translate_anthropic_tools_to_openai(anthropic_tools):
    if not anthropic_tools:
        return None
    
    openai_tools = []
    for tool in anthropic_tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.get("name"),
                "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", {"type": "object", "properties": {}})
            }
        })
    return openai_tools

async def get_prioritized_models():
    """Fetch models from the local server and prioritize them"""
    try:
        models_url = LOCAL_SERVER_URL.replace("/chat/completions", "/models")
        headers = {"Authorization": f"Bearer {LOCAL_API_KEY}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(models_url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                data = response.json().get("data", [])
                # Filter out image, gpt models and failed models
                model_ids = [
                    m["id"] for m in data 
                    if m["id"] not in FAILED_MODELS and "image" not in m["id"].lower() and "gpt" not in m["id"].lower()
                ]
                
                # If everything is filtered out, try again without FAILED_MODELS (still ignoring images/gpt)
                if not model_ids and data:
                    FAILED_MODELS.clear()
                    model_ids = [
                        m["id"] for m in data 
                        if "image" not in m["id"].lower() and "gpt" not in m["id"].lower()
                    ]

                if PREFERRED_MODEL and PREFERRED_MODEL in model_ids:
                    model_ids.remove(PREFERRED_MODEL)
                    model_ids.insert(0, PREFERRED_MODEL)
                    return model_ids

                # Default sorting logic
                def get_priority_tuple(model_id):
                    m = model_id.lower()
                    cat = 0 if "claude" in m else (1 if "flash" in m else (2 if "pro" in m else 3))
                    thinking = 0 if ("thinking" in m or "reasoning" in m) else 1
                    return (cat, thinking)

                model_ids.sort(reverse=True)
                return sorted(model_ids, key=get_priority_tuple)
    except Exception as e:
        print(f"Error fetching models: {e}")
    
    return [PREFERRED_MODEL] if PREFERRED_MODEL else ["claude-3-5-sonnet-20241022"]

@app.get("/v1/models")
async def list_models():
    models = await get_prioritized_models()
    return {"data": [{"id": m, "object": "model", "created": 1677610602, "owned_by": "local"} for m in models]}

@app.post("/v1/messages")
async def proxy_anthropic_to_openai(request: Request):
    try:
        anthropic_body = await request.json()
        print(f"--- Incoming Claude Request ---")
        
        openai_messages = []
        if "system" in anthropic_body:
            # Handle system prompt which can be a string or list of blocks
            system_content = anthropic_body["system"]
            if isinstance(system_content, list):
                system_content = " ".join([b.get("text", "") for b in system_content if b.get("type") == "text"])
            openai_messages.append({"role": "system", "content": system_content})
            
        openai_messages.extend(translate_anthropic_to_openai_messages(anthropic_body.get("messages", [])))
        openai_tools = translate_anthropic_tools_to_openai(anthropic_body.get("tools"))

        # Clean headers
        auth_header = request.headers.get("Authorization", "").replace("sk-ant-api03-", "")
        if not auth_header:
            auth_header = f"Bearer {LOCAL_API_KEY}"

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
                if openai_tools:
                    openai_body["tools"] = openai_tools
                
                print(f"Sending to OpenAI: {json.dumps(openai_body)}")

                try:
                    response = await client.post(
                        LOCAL_SERVER_URL,
                        json=openai_body,
                        headers={"Authorization": auth_header, "Content-Type": "application/json"},
                        timeout=180.0
                    )

                    if response.status_code == 200:
                        print(f"Success with model: {model_name}")
                        openai_res = response.json()
                        choice = openai_res.get("choices", [{}])[0]
                        message = choice.get("message", {})
                        
                        anthropic_content = []
                        if message.get("content"):
                            anthropic_content.append({"type": "text", "text": message["content"]})
                        
                        # Translate OpenAI tool_calls back to Anthropic tool_use
                        tool_calls = message.get("tool_calls", [])
                        for tc in tool_calls:
                            try:
                                args = json.loads(tc["function"]["arguments"])
                            except:
                                args = tc["function"]["arguments"]
                            
                            anthropic_content.append({
                                "type": "tool_use",
                                "id": tc["id"],
                                "name": tc["function"]["name"],
                                "input": args
                            })

                        stop_reason = "end_turn"
                        if tool_calls:
                            stop_reason = "tool_use"
                        elif choice.get("finish_reason") == "length":
                            stop_reason = "max_tokens"

                        return {
                            "id": openai_res.get("id", "msg_local"),
                            "type": "message",
                            "role": "assistant",
                            "content": anthropic_content,
                            "model": anthropic_body.get("model", "claude-3-5-sonnet-20241022"),
                            "stop_reason": stop_reason,
                            "stop_sequence": None,
                            "usage": {
                                "input_tokens": openai_res.get("usage", {}).get("prompt_tokens", 0),
                                "output_tokens": openai_res.get("usage", {}).get("completion_tokens", 0)
                            }
                        }
                    elif response.status_code == 404:
                        print(f"Model {model_name} not found (404). Blacklisting.")
                        FAILED_MODELS.add(model_name)
                    elif response.status_code == 503:
                        print(f"Model {model_name} temporarily unhealthy (503).")
                    else:
                        print(f"Model {model_name} error {response.status_code}: {response.text}")
                    last_error = response
                except Exception as e:
                    print(f"Exception for {model_name}: {e}")
                    last_error = e
            
            return Response(content=str(last_error), status_code=500)
    except Exception as e:
        print(f"Proxy Error: {e}")
        return Response(content=str(e), status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000)

