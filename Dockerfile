# Doctor+ Backend Dockerfile for Render
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Render provides PORT env var)
EXPOSE 8000

# Run uvicorn
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
