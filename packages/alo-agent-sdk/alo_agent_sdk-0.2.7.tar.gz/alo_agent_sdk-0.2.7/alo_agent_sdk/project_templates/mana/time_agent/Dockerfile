# ALO Agent SDK - Agent Dockerfile
# This Dockerfile is for the 'time_agent' component of the 'mana' template.

# Specify the Python version you want to use
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Argument for the agent's specific requirements file
ARG AGENT_REQUIREMENTS_FILE=requirements.txt

# 1. Copy requirements.sdk.txt (which should list alo-agent-sdk==0.1.12)
#    This file will be copied from the generated project's time_agent directory.
COPY requirements.sdk.txt .

# 2. Install alo-agent-sdk and its dependencies from PyPI.
#    This also installs other dependencies listed in requirements.sdk.txt.
RUN pip install --no-cache-dir -r requirements.sdk.txt

# 3. Copy the agent's specific requirements file (e.g., requirements.txt for time_agent),
#    if it exists, and install them.
#    These are additional dependencies for the specific agent.
COPY ${AGENT_REQUIREMENTS_FILE}* .
RUN if [ -f "${AGENT_REQUIREMENTS_FILE}" ]; then pip install --no-cache-dir -r ${AGENT_REQUIREMENTS_FILE}; fi

# Copy the rest of the agent's application code (e.g., main.py)
COPY . .

# Google Cloud Run expects the application to listen on the port specified by $PORT
# Default port for this agent.
ENV PORT 8080
EXPOSE $PORT

# Command to run the Uvicorn server for your FastAPI application
# Assumes your agent's main file is main.py and the FastAPI instance is 'app'.
CMD python -c "import sys; print('--- sys.path (time_agent) ---'); [print(p) for p in sys.path]; print('--- alo_agent_sdk location (time_agent) ---'); import alo_agent_sdk; print(alo_agent_sdk.__path__); print('--- Trying to import AgentBuilder (time_agent) ---'); from alo_agent_sdk.core import AgentBuilder; print('AgentBuilder imported successfully from time_agent!')" && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
