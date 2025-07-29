# ALO Agent SDK - Agent Registry Service Dockerfile
# This Dockerfile is for the 'agent_registry' component of the 'mana' template.

# Specify the Python version you want to use
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# 1. Copy requirements.sdk.txt (which should list alo-agent-sdk==0.1.12)
#    This file will be copied from the generated project's agent_registry directory.
COPY requirements.sdk.txt .

# 2. Install alo-agent-sdk and its dependencies from PyPI.
#    This also installs other dependencies listed in requirements.sdk.txt.
RUN pip install --no-cache-dir -r requirements.sdk.txt

# Google Cloud Run expects the application to listen on the port specified by $PORT
# Default port for this specific registry service.
ENV PORT 8001
EXPOSE $PORT

# Command to run the Uvicorn server for the FastAPI Registry Service application
# This should point to the FastAPI 'app' instance in alo_agent_sdk.registry_service.main
# This assumes 'alo_agent_sdk' is installed via requirements.sdk.txt and available in PYTHONPATH.
CMD python -c "import sys; print('--- sys.path (agent_registry) ---'); [print(p) for p in sys.path]; print('--- alo_agent_sdk location (agent_registry) ---'); import alo_agent_sdk; print(alo_agent_sdk.__path__); print('--- Trying to import registry_service.main (agent_registry) ---'); import alo_agent_sdk.registry_service.main; print('registry_service.main imported successfully!')" && uvicorn alo_agent_sdk.registry_service.main:app --host 0.0.0.0 --port ${PORT:-8001}
