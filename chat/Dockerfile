FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn httpx python-dotenv


# Copy the proxy script
COPY claude_proxy.py .

# Expose the proxy port
EXPOSE 4000

# Run the proxy
CMD ["python", "claude_proxy.py"]
