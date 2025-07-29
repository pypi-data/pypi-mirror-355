# Dockerfile for the Mana Orchestrator Backend

# Specify the Python version
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies (will use main PyPI by default)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Environment variable for the port (Cloud Run compatible)
# The orchestrator's main.py uses PORT 8000 as default if not set.
ENV PORT 8000
EXPOSE $PORT

# Command to run the Uvicorn server for the FastAPI application
# Assumes the FastAPI app instance is 'app' in 'main.py'
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
