# ALO Agent SDK - Agent Dockerfile
# This Dockerfile is for the 'slack_agent' component of the 'mana' template.

# Specify the Python version you want to use
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Argument for the agent's specific requirements file
ARG AGENT_REQUIREMENTS_FILE=requirements.txt

# 1. Copy requirements.sdk.txt (which should list the alo-agent-sdk version)
#    This file will be copied from the generated project's slack_agent directory.
COPY requirements.sdk.txt .

# 2. Install alo-agent-sdk and its dependencies.
#    This also installs other dependencies listed in requirements.sdk.txt.
#    Using --no-cache-dir to reduce image size.
RUN pip install --no-cache-dir -r requirements.sdk.txt

# 3. Copy the agent's specific requirements file (e.g., requirements.txt for slack_agent),
#    if it exists, and install them.
#    These are additional dependencies for the specific agent (e.g., python-dotenv for local .env).
COPY ${AGENT_REQUIREMENTS_FILE}* .
RUN if [ -f "${AGENT_REQUIREMENTS_FILE}" ]; then pip install --no-cache-dir -r ${AGENT_REQUIREMENTS_FILE}; fi

# Copy the rest of the agent's application code (e.g., main.py)
COPY . .

# AGENT_PORT will be set by docker-compose or Cloud Run.
# Default port for this agent if AGENT_PORT is not set.
ENV AGENT_PORT 8003 
ENV PORT ${AGENT_PORT} # Google Cloud Run expects PORT
EXPOSE ${PORT}

# Command to run the Python application
# main.py in slack_agent calls run_fastapi_server internally.
CMD python main.py
