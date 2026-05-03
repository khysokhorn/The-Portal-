FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Copy the proxy script and services module
COPY claude_proxy.py .
COPY services/ ./services/

# Expose the proxy port
EXPOSE 4000

# Run the proxy
CMD ["python", "claude_proxy.py"]
