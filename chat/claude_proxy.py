import uvicorn
from fastapi import FastAPI, Request, Response, BackgroundTasks
from fastapi.responses import StreamingResponse
import httpx
import json
import asyncio
import time
import os
import contextlib
from dotenv import load_dotenv

from services.db_service import DBService, log_chat_to_db
from services.account_service import AccountService

app = FastAPI()

# Load environment variables from .env
load_dotenv()

# Your local OpenAI-compatible server
LOCAL_SERVER_URL = os.getenv("LOCAL_SERVER_URL", "http://host.docker.internal:8045/v1/chat/completions")
LOCAL_API_KEY = os.getenv("LOCAL_API_KEY", "sk-local-key")
PREFERRED_MODEL = os.getenv("PREFERRED_MODEL")
# Cache for failed models
FAILED_MODELS = set()
MAX_MODEL_RETRIES = 2
RETRY_DELAY = 1.0  # seconds

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    await DBService.init_db()
    yield
    await DBService.close_db()

app.router.lifespan_context = lifespan

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
                    content = block.get("content", "")
                    if isinstance(content, list):
                        text_parts = []
                        for c in content:
                            if isinstance(c, dict) and c.get("type") == "text":
                                text_parts.append(c.get("text", ""))
                            elif isinstance(c, str):
                                text_parts.append(c)
                        content_str = "\n".join(text_parts)
                    else:
                        content_str = str(content)
                        
                    openai_messages.append({
                        "role": "tool",
                        "tool_call_id": block.get("tool_use_id"),
                        "content": content_str
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

@app.get("/api/v0/models")
async def list_models_v0():
    models = await get_prioritized_models()
    return {"data": [{"id": m, "object": "model", "created": 1677610602, "owned_by": "local"} for m in models]}

@app.post("/v1/chat/completions")
async def proxy_openai_to_openai_v1(request: Request, background_tasks: BackgroundTasks):
    return await handle_openai_proxy(request, background_tasks)

@app.post("/api/v0/chat/completions")
async def proxy_openai_to_openai_v0(request: Request, background_tasks: BackgroundTasks):
    return await handle_openai_proxy(request, background_tasks)

async def handle_openai_proxy(request: Request, background_tasks: BackgroundTasks):
    try:
        openai_body = await request.json()
        print(f"--- Incoming OpenAI Request (from Rider/LM Studio client) ---")
        
        auth_header = request.headers.get("Authorization", "")
        if not auth_header:
            auth_header = f"Bearer {LOCAL_API_KEY}"

        models = await get_prioritized_models()
        requested_model = openai_body.get("model")
        if requested_model and requested_model in models:
            models.remove(requested_model)
            models.insert(0, requested_model)
            
        # We need a long-lived client if we use stream=True and return StreamingResponse,
        # but httpx handles it if we don't close it, though it's safer to use StreamingResponse 
        # with background tasks or just a simple client initialization inside the generator.
        async def stream_generator(model_name):
            async with httpx.AsyncClient() as client:
                req = client.build_request(
                    "POST", 
                    LOCAL_SERVER_URL, 
                    json=openai_body, 
                    headers={"Authorization": auth_header, "Content-Type": "application/json"},
                    timeout=180.0
                )
                response = await client.send(req, stream=True)
                async for chunk in response.aiter_bytes():
                    yield chunk
            
            # Since tracking the full stream chunks is complex right now, we log the user's request.
            # You can expand this to buffer chunks and save the assistant's reply later!
            background_tasks.add_task(log_chat_to_db, model_name, openai_body, {"note": "streaming_response_not_logged_yet"})

        async with httpx.AsyncClient() as client:
            last_error_text = "No models attempted"
            
            for model_name in models:
                print(f"Attempting OpenAI passthrough with model: {model_name}")
                openai_body["model"] = model_name
                
                for attempt in range(MAX_MODEL_RETRIES):
                    if attempt > 0:
                        print(f"Retry attempt {attempt} for model: {model_name}")
                        await asyncio.sleep(RETRY_DELAY)
                        
                    try:
                        is_stream = openai_body.get("stream", False)
                        
                        if not is_stream:
                            response = await client.post(
                                LOCAL_SERVER_URL,
                                json=openai_body,
                                headers={"Authorization": auth_header, "Content-Type": "application/json"},
                                timeout=180.0
                            )

                            if response.status_code == 200:
                                print(f"Success with model: {model_name}")
                                background_tasks.add_task(log_chat_to_db, model_name, openai_body, response.json())
                                return Response(content=response.content, status_code=200, media_type="application/json")
                            elif response.status_code == 404:
                                print(f"Model {model_name} not found (404). Blacklisting.")
                                FAILED_MODELS.add(model_name)
                                break # Move to next model
                            
                            last_error_text = response.text
                            print(f"Attempt {attempt} failed for {model_name}: {response.status_code} - {last_error_text}")
                            
                            if response.status_code < 500: # Don't retry 4xx errors other than 404
                                break
                        else:
                            # For streaming, we test the connection first
                            req = client.build_request("POST", LOCAL_SERVER_URL, json=openai_body, headers={"Authorization": auth_header})
                            response = await client.send(req, stream=True)
                            if response.status_code == 200:
                                print(f"Success streaming with model: {model_name}")
                                return StreamingResponse(stream_generator(model_name), media_type="text/event-stream")
                            else:
                                await response.aread()
                                last_error_text = response.text
                                if response.status_code == 404:
                                    print(f"Model {model_name} not found (404). Blacklisting.")
                                    FAILED_MODELS.add(model_name)
                                    break
                                
                                print(f"Stream attempt {attempt} failed for {model_name}: {response.status_code} - {last_error_text}")
                                if response.status_code < 500:
                                    break
                    except Exception as e:
                        print(f"Exception for {model_name} (attempt {attempt}): {e}")
                        last_error_text = str(e)
            
            # CLI Hint Hack: Return a 200 response with the error as a chat message so the CLI shows it
            error_msg = f"❌ ALL ACCOUNTS UNHEALTHY\n\nReason: {last_error_text}\n\n👉 FIX: Visit http://127.0.0.1:4000/v1/accounts/logout in your browser to reset your accounts."
            return Response(
                content=json.dumps({
                    "id": "err_local",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": requested_model or "error-handler",
                    "choices": [{
                        "index": 0,
                        "message": {"role": "assistant", "content": error_msg},
                        "finish_reason": "stop"
                    }]
                }),
                status_code=200,
                media_type="application/json"
            )
    except Exception as e:
        print(f"Proxy Error: {e}")
        return Response(content=str(e), status_code=500)

@app.post("/v1/messages")
async def proxy_anthropic_to_openai(request: Request, background_tasks: BackgroundTasks):
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
            last_error_text = "No models attempted"
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

                for attempt in range(MAX_MODEL_RETRIES):
                    if attempt > 0:
                        print(f"Retry attempt {attempt} for model: {model_name}")
                        await asyncio.sleep(RETRY_DELAY)

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
                                raw_args = tc.get("function", {}).get("arguments", "")
                                args = {}
                                if raw_args:
                                    if isinstance(raw_args, str):
                                        raw_args = raw_args.strip()
                                        if raw_args.startswith("```json"):
                                            raw_args = raw_args[7:-3].strip()
                                        elif raw_args.startswith("```"):
                                            raw_args = raw_args[3:-3].strip()
                                        try:
                                            args = json.loads(raw_args)
                                        except Exception as e:
                                            print(f"Failed to parse tool arguments: {e}. Raw: {raw_args}")
                                            # Fallback to string if completely unparseable, but Anthropic expects dict
                                            args = {"error_parsing": str(raw_args)}
                                    elif isinstance(raw_args, dict):
                                        args = raw_args
                                
                                if not isinstance(args, dict):
                                    args = {}
                                
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

                            final_res = {
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
                            background_tasks.add_task(log_chat_to_db, model_name, anthropic_body, final_res)
                            return final_res
                        elif response.status_code == 404:
                            print(f"Model {model_name} not found (404). Blacklisting.")
                            FAILED_MODELS.add(model_name)
                            break
                        
                        last_error_text = response.text
                        print(f"Attempt {attempt} failed for {model_name}: {response.status_code} - {last_error_text}")
                        
                        if response.status_code < 500:
                            break
                    except Exception as e:
                        print(f"Exception for {model_name} (attempt {attempt}): {e}")
                        last_error_text = str(e)
            
            # CLI Hint Hack for Anthropic: Return a 200 response with the error as a chat message
            error_msg = f"❌ ALL ACCOUNTS UNHEALTHY\n\nReason: {last_error_text}\n\n👉 FIX: Visit http://127.0.0.1:4000/v1/accounts/logout in your browser to reset your accounts."
            return {
                "id": "err_local",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": error_msg}],
                "model": anthropic_body.get("model", "claude-3-5-sonnet-20241022"),
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 0, "output_tokens": 0}
            }
    except Exception as e:
        print(f"Proxy Error: {e}")
        return Response(content=str(e), status_code=500)

@app.get("/v1/accounts/logout")
async def logout_accounts(confirm: bool = False, type: str = "current"):
    if not confirm:
        return Response(
            content=f"""
            <html>
                <body style='font-family: sans-serif; text-align: center; padding: 50px;'>
                    <h1>⚠️ Reset Antigravity Accounts?</h1>
                    <p>Choose which action you want to perform:</p>
                    <br/>
                    <div style='display: flex; gap: 20px; justify-content: center;'>
                        <a href='/v1/accounts/logout?confirm=true&type=current' 
                           style='background: #ff8800; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;'>
                           LOGOUT CURRENT ACCOUNT ONLY
                        </a>
                        <a href='/v1/accounts/logout?confirm=true&type=all' 
                           style='background: #ff4444; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;'>
                           LOGOUT ALL ACCOUNTS
                        </a>
                    </div>
                    <br/><br/>
                    <p style='color: #666;'>Your chat history will be backed up and kept safe.</p>
                </body>
            </html>
            """,
            media_type="text/html"
        )
    
    if type == "all":
        success, message = AccountService.logout_all_accounts()
    else:
        success, message = AccountService.logout_current_account()

    if success:
        return Response(
            content=f"""
            <html>
                <body style='font-family: sans-serif; text-align: center; padding: 50px;'>
                    <h1>✅ Logout Successful</h1>
                    <p>{message}</p>
                    <hr/>
                    <h3>Next Steps:</h3>
                    <p>1. Restart your Docker containers (docker-compose restart).</p>
                    <p>2. Go to <a href='http://127.0.0.1:8045'>Antigravity Manager</a> and log in via OAuth again.</p>
                </body>
            </html>
            """,
            media_type="text/html"
        )
    else:
        return Response(content=f"Error: {message}", status_code=400)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000)

