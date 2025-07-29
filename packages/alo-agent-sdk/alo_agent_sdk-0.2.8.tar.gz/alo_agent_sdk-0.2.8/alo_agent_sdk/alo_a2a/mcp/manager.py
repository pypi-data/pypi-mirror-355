"""
Manages configurations and provides access to MCPClient instances
for configured MCP servers. Also handles starting/stopping local MCP servers,
including those managed by Docker Compose.
"""
import json
import os
import logging
import asyncio
import subprocess 
from pathlib import Path
from typing import Dict, Optional, Any, List, Tuple

from pydantic import ValidationError
from dotenv import dotenv_values

from .client import MCPClient, MCPConnectionError
from .exceptions import (
    MCPConfigError,
    MCPAuthEnvError,
    MCPManagerError
)
from .config_models import MCPConfigurationFile, MCPServerConfigLocal, AnyMCPServerConfig, MCPBasicAuthConfig, MCPBearerAuthConfig, MCPAPIKeyAuthConfig

logger = logging.getLogger(__name__)

class MCPManager:
    DEFAULT_CONFIG_SUBDIR = ".alo_project"
    DEFAULT_LOG_SUBDIR = "logs" # New for log files
    DEFAULT_CONFIG_FILENAME = "mcp_servers.json"
    PROJECT_ROOT_INDICATORS = [".git", "pyproject.toml", "setup.py", ".alo_project_marker"]
    MAX_CONFIG_SEARCH_DEPTH = 10
    HEALTHCHECK_TIMEOUT = 10 
    HEALTHCHECK_RETRIES = 3 
    HEALTHCHECK_RETRY_DELAY = 2 

    _parsed_config: Optional[MCPConfigurationFile] = None
    _local_server_processes: Dict[str, asyncio.subprocess.Process] 
    _config_file_mtime: Optional[float] = None 
    _log_file_handles: Dict[str, Tuple[Any, Any]] # To store (stdout_fh, stderr_fh)

    def __init__(self, config_path: Optional[Path] = None, project_root_or_start_path: Optional[Path] = None):
        base_path = Path(project_root_or_start_path).resolve() if project_root_or_start_path else Path.cwd().resolve()
        if config_path:
            resolved_config_path = Path(config_path)
            if not resolved_config_path.is_absolute():
                self._config_path = (base_path / resolved_config_path).resolve()
            else:
                self._config_path = resolved_config_path
        else:
            self._config_path = self.get_default_config_filepath(base_path)
        
        self._clients_cache: Dict[str, MCPClient] = {}
        self._local_server_processes = {}
        self._log_file_handles = {} # Initialize log file handles dict
        self._load_config()

    @classmethod
    def _find_project_root(cls, start_path: Path) -> Path:
        current_path = start_path.resolve()
        for _ in range(cls.MAX_CONFIG_SEARCH_DEPTH):
            for indicator in cls.PROJECT_ROOT_INDICATORS:
                if (current_path / indicator).exists():
                    logger.debug(f"Project root found at {current_path} due to indicator '{indicator}'")
                    return current_path
            if current_path.parent == current_path: break
            current_path = current_path.parent
        logger.debug(f"No project root indicator found from {start_path}. Using {start_path} as effective root.")
        return start_path

    @classmethod
    def get_default_config_filepath(cls, start_dir: Optional[Path] = None) -> Path:
        search_start_path = Path(start_dir).resolve() if start_dir else Path.cwd().resolve()
        project_root = cls._find_project_root(search_start_path)
        config_dir = project_root / cls.DEFAULT_CONFIG_SUBDIR
        return (config_dir / cls.DEFAULT_CONFIG_FILENAME).resolve()

    def _get_log_paths(self, server_name: str) -> Tuple[Path, Path]:
        """Gets the paths for stdout and stderr log files for a server."""
        # Logs will be stored in <project_root>/.alo_project/logs/<server_name>.stdxxx.log
        # This assumes self._config_path.parent is <project_root>/.alo_project
        log_dir = self._config_path.parent / self.DEFAULT_LOG_SUBDIR
        log_dir.mkdir(parents=True, exist_ok=True)
        stdout_log = log_dir / f"{server_name}.stdout.log"
        stderr_log = log_dir / f"{server_name}.stderr.log"
        return stdout_log, stderr_log

    def _load_config(self):
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning(f"Could not create parent directory for MCP config {self._config_path.parent}: {e}.")

        if not self._config_path.exists():
            logger.info(f"MCP config file not found at {self._config_path}. Initializing empty config.")
            self._parsed_config = MCPConfigurationFile()
            self._config_file_mtime = None 
            return
        try:
            current_mtime = self._config_path.stat().st_mtime
            with open(self._config_path, 'r') as f: raw_data = json.load(f)
            self._parsed_config = MCPConfigurationFile.model_validate(raw_data)
            self._config_file_mtime = current_mtime 
            logger.info(f"Loaded and validated MCP config from {self._config_path} (mtime: {current_mtime})")
        except json.JSONDecodeError as e:
            self._config_file_mtime = None 
            raise MCPConfigError(f"Error decoding JSON from {self._config_path}: {e}")
        except ValidationError as e:
            self._config_file_mtime = None 
            errors = "; ".join([f"Field '{' -> '.join(map(str, err['loc']))}': {err['msg']}" for err in e.errors()])
            raise MCPConfigError(f"Invalid MCP config in {self._config_path}: {errors}")
        except FileNotFoundError:
             logger.warning(f"MCP config file {self._config_path} not found during load attempt.")
             self._parsed_config = MCPConfigurationFile()
             self._config_file_mtime = None
        except Exception as e:
            self._config_file_mtime = None 
            raise MCPConfigError(f"Unexpected error loading MCP config from {self._config_path}: {e}")

    def _get_server_conf_model(self, server_name: str) -> AnyMCPServerConfig:
        if not self._parsed_config or server_name not in self._parsed_config.mcp_servers:
            raise MCPConfigError(f"MCP server '{server_name}' not found in config at {self._config_path}.")
        return self._parsed_config.mcp_servers[server_name]

    def _read_secret_from_file(self, file_path: Path, secret_name: str, server_name: str) -> str:
        try:
            secret = file_path.read_text().strip()
            if not secret:
                raise MCPAuthEnvError(f"Secret file '{file_path}' for '{secret_name}' on server '{server_name}' is empty.")
            return secret
        except FileNotFoundError:
            raise MCPAuthEnvError(f"Secret file '{file_path}' for '{secret_name}' on server '{server_name}' not found.")
        except Exception as e:
            raise MCPAuthEnvError(f"Error reading secret file '{file_path}' for '{secret_name}' on server '{server_name}': {e}")

    async def _run_shell_command(self, cmd: str, cwd: Optional[Path] = None, env: Optional[Dict[str,str]] = None) -> Tuple[bool, str, str]:
        logger.debug(f"Running command: {cmd} in {cwd or os.getcwd()}")
        process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=cwd, env=env)
        stdout, stderr = await process.communicate()
        success = process.returncode == 0
        stdout_str = stdout.decode().strip(); stderr_str = stderr.decode().strip()
        if not success: logger.error(f"Command '{cmd}' failed (code {process.returncode}). Stderr: {stderr_str}. Stdout: {stdout_str}")
        return success, stdout_str, stderr_str

    async def _perform_health_check(self, server_name: str, url: str, healthcheck_path: str) -> bool:
        if not healthcheck_path.startswith("/"): healthcheck_path = "/" + healthcheck_path
        logger.info(f"Performing health check for '{server_name}' at {url}{healthcheck_path}...")
        temp_hc_client = MCPClient(server_url=url, timeout=self.HEALTHCHECK_TIMEOUT)
        try:
            for attempt in range(self.HEALTHCHECK_RETRIES):
                try:
                    response = await temp_hc_client.client.get(healthcheck_path) 
                    response.raise_for_status() 
                    logger.info(f"Health check for '{server_name}' successful on attempt {attempt + 1}.")
                    return True
                except Exception as e: 
                    logger.warning(f"Health check attempt {attempt + 1} for '{server_name}' failed: {e}")
                    if attempt < self.HEALTHCHECK_RETRIES - 1: await asyncio.sleep(self.HEALTHCHECK_RETRY_DELAY)
                    else: logger.error(f"All {self.HEALTHCHECK_RETRIES} health check attempts for '{server_name}' failed."); return False
        finally: await temp_hc_client.close()
        return False

    async def start_local_server(self, server_name: str) -> bool:
        server_conf_model = self._get_server_conf_model(server_name)
        if not isinstance(server_conf_model, MCPServerConfigLocal): raise MCPManagerError(f"'{server_name}' not local.")
        if self.is_local_server_running(server_name): logger.info(f"'{server_name}' already running."); return True

        env_vars = os.environ.copy()
        if server_conf_model.env_file_path and server_conf_model.env_file_path.exists():
            logger.info(f"Loading .env from {server_conf_model.env_file_path} for '{server_name}'")
            env_vars.update(dotenv_values(server_conf_model.env_file_path))

        if server_conf_model.compose_managed and server_conf_model.project_compose_file_path and server_conf_model.compose_service_name:
            compose_file = Path(server_conf_model.project_compose_file_path)
            if not compose_file.exists(): raise MCPConfigError(f"Compose file {compose_file} not found for '{server_name}'.")
            cmd = f"docker-compose -f \"{compose_file.resolve()}\" up -d --build {server_conf_model.compose_service_name}"
            logger.info(f"Starting '{server_name}' via Docker Compose: {cmd}")
            success, _, stderr_str = await self._run_shell_command(cmd, cwd=compose_file.parent)
            if not success: logger.error(f"Failed to start '{server_name}' with Docker Compose: {stderr_str}"); return False
            self._local_server_processes[server_name] = None 
        else:
            logger.info(f"Starting '{server_name}' with command: {server_conf_model.run_command}")
            stdout_log_path, stderr_log_path = self._get_log_paths(server_name)
            try:
                # Open log files in append mode
                stdout_fh = open(stdout_log_path, 'ab') # Use 'ab' for binary append to avoid encoding issues from subprocess
                stderr_fh = open(stderr_log_path, 'ab')
                self._log_file_handles[server_name] = (stdout_fh, stderr_fh)

                process = await asyncio.create_subprocess_shell(
                    server_conf_model.run_command, 
                    stdout=stdout_fh, # Redirect to file
                    stderr=stderr_fh, # Redirect to file
                    cwd=server_conf_model.project_path, env=env_vars
                )
                self._local_server_processes[server_name] = process
                logger.info(f"'{server_name}' process started (PID: {process.pid}). Logs: {stdout_log_path}, {stderr_log_path}")
            except Exception as e: 
                logger.error(f"Failed to start process '{server_name}': {e}")
                if server_name in self._log_file_handles: # Close handles if opened
                    self._log_file_handles[server_name][0].close()
                    self._log_file_handles[server_name][1].close()
                    del self._log_file_handles[server_name]
                return False

        if server_conf_model.healthcheck_path:
            server_url = f"http://localhost:{server_conf_model.port}"
            if not await self._perform_health_check(server_name, server_url, server_conf_model.healthcheck_path):
                logger.error(f"Health check failed for '{server_name}'. Stopping."); await self.stop_local_server(server_name); return False
        else: 
            await asyncio.sleep(2) 
            if not self.is_local_server_running(server_name): logger.error(f"'{server_name}' exited prematurely."); return False
            logger.info(f"'{server_name}' assumed started (no health check).")
        return True

    async def stop_local_server(self, server_name: str) -> bool:
        server_conf_model = self._get_server_conf_model(server_name)
        if not isinstance(server_conf_model, MCPServerConfigLocal): logger.warning(f"Stop called on non-local '{server_name}'."); return False

        if server_conf_model.compose_managed and server_conf_model.project_compose_file_path and server_conf_model.compose_service_name:
            compose_file = Path(server_conf_model.project_compose_file_path)
            if not compose_file.exists(): logger.error(f"Compose file {compose_file} not found for stopping '{server_name}'."); return False
            cmd = f"docker-compose -f \"{compose_file.resolve()}\" stop {server_conf_model.compose_service_name}"
            logger.info(f"Stopping '{server_name}' via Docker Compose: {cmd}")
            success, _, stderr_str = await self._run_shell_command(cmd, cwd=compose_file.parent)
            if not success: logger.error(f"Failed to stop '{server_name}' with Docker Compose: {stderr_str}")
            if server_name in self._local_server_processes and self._local_server_processes[server_name] is None: del self._local_server_processes[server_name]
            return success

        process = self._local_server_processes.get(server_name)
        if not process: logger.info(f"'{server_name}' not managed or already stopped."); return True
        if process.returncode is not None: logger.info(f"'{server_name}' (PID: {process.pid}) already terminated."); del self._local_server_processes[server_name]; return True
        logger.info(f"Stopping '{server_name}' (PID: {process.pid})...")
        try:
            process.terminate(); await asyncio.wait_for(process.wait(), timeout=10.0)
            logger.info(f"'{server_name}' (PID: {process.pid}) terminated.")
        except asyncio.TimeoutError:
            logger.warning(f"'{server_name}' (PID: {process.pid}) did not terminate. Killing..."); process.kill(); await process.wait()
            logger.info(f"'{server_name}' (PID: {process.pid}) killed.")
        except Exception as e:
            logger.error(f"Error stopping '{server_name}' (PID: {process.pid}): {e}")
            if process.returncode is None: process.kill(); await process.wait()
            del self._local_server_processes[server_name]; return False
        
        if server_name in self._log_file_handles: # Close log file handles
            try:
                self._log_file_handles[server_name][0].close()
                self._log_file_handles[server_name][1].close()
            except Exception as e_close:
                logger.error(f"Error closing log files for '{server_name}': {e_close}")
            del self._log_file_handles[server_name]
        
        del self._local_server_processes[server_name]; return True

    async def get_client(self, server_name: str) -> MCPClient:
        try:
            if self._config_path.exists():
                if self._config_file_mtime is None or self._config_path.stat().st_mtime != self._config_file_mtime:
                    logger.info(f"Config {self._config_path} changed. Reloading."); await self.reload_config() 
            elif self._config_file_mtime is not None: 
                 logger.info(f"Config {self._config_path} removed. Reloading."); await self.reload_config()
        except Exception as e: logger.warning(f"Could not check config mtime for {self._config_path}: {e}.")

        if server_name in self._clients_cache: return self._clients_cache[server_name]
        server_conf_model = self._get_server_conf_model(server_name)
        
        if isinstance(server_conf_model, MCPServerConfigLocal) and server_conf_model.auto_start:
            if not await self.start_local_server(server_name): raise MCPManagerError(f"Failed to auto-start '{server_name}'.")

        server_url: str
        if server_conf_model.type == "local": server_url = f"http://localhost:{server_conf_model.port}"
        elif server_conf_model.type == "remote": server_url = str(server_conf_model.url)
        else: raise MCPConfigError(f"Unknown server type '{server_conf_model.type}' for '{server_name}'.")

        auth_dict: Optional[Dict[str, Any]] = None
        if server_conf_model.authentication:
            auth_model = server_conf_model.authentication
            auth_dict = {"type": auth_model.type}
            
            if auth_model.type == "basic":
                if auth_model.auth_source == "env":
                    auth_dict["username"] = os.getenv(auth_model.username_env_var)
                    auth_dict["password"] = os.getenv(auth_model.password_env_var)
                    if auth_dict["username"] is None: raise MCPAuthEnvError(f"Env var '{auth_model.username_env_var}' for basic auth not set for '{server_name}'.")
                    if auth_dict["password"] is None: raise MCPAuthEnvError(f"Env var '{auth_model.password_env_var}' for basic auth not set for '{server_name}'.")
                elif auth_model.auth_source == "file":
                    auth_dict["username"] = self._read_secret_from_file(auth_model.username_file_path, "username", server_name)
                    auth_dict["password"] = self._read_secret_from_file(auth_model.password_file_path, "password", server_name)
            elif auth_model.type in ["bearer", "api_key"]:
                token_val = None
                if auth_model.auth_source == "env":
                    token_val = os.getenv(auth_model.token_env_var)
                    if token_val is None: raise MCPAuthEnvError(f"Env var '{auth_model.token_env_var}' for {auth_model.type} auth not set for '{server_name}'.")
                elif auth_model.auth_source == "file":
                    token_val = self._read_secret_from_file(auth_model.token_file_path, "token/key", server_name)
                
                if auth_model.type == "bearer": auth_dict["token"] = token_val
                elif auth_model.type == "api_key":
                    auth_dict["key"] = token_val
                    auth_dict["key_name"] = auth_model.key_name
                    auth_dict["location"] = auth_model.location
        try:
            client = MCPClient(server_url=server_url, auth=auth_dict)
            self._clients_cache[server_name] = client
            return client
        except Exception as e:
            raise MCPManagerError(f"Could not create MCPClient for '{server_name}': {e}")

    async def close_all_clients(self):
        logger.info("Closing clients and stopping managed local servers...")
        for name in list(self._local_server_processes.keys()): 
            try: await self.stop_local_server(name) # This will also close log handles
            except Exception as e: logger.error(f"Error stopping local server '{name}' during shutdown: {e}")
        for name in list(self._clients_cache.keys()): 
            client = self._clients_cache.pop(name)
            try: await client.close()
            except Exception as e: logger.error(f"Error closing client for '{name}': {e}")
        
        # Ensure any remaining log handles are closed (e.g., if stop_local_server failed before closing them)
        for name in list(self._log_file_handles.keys()):
            try:
                self._log_file_handles[name][0].close()
                self._log_file_handles[name][1].close()
            except Exception as e_close:
                logger.error(f"Error closing lingering log files for '{name}': {e_close}")
            del self._log_file_handles[name]

        logger.info("Finished closing clients and stopping servers.")

    def list_server_names(self) -> List[str]:
        if self._parsed_config: return list(self._parsed_config.mcp_servers.keys())
        return []

    def get_server_config(self, server_name: str) -> Optional[Dict[str, Any]]:
        try: 
            if self._config_path.exists():
                if self._config_file_mtime is None or self._config_path.stat().st_mtime != self._config_file_mtime:
                    logger.info(f"Config {self._config_path} changed. Forcing sync reload."); self.reload_config_sync() 
            elif self._config_file_mtime is not None:
                 logger.info(f"Config {self._config_path} removed. Forcing sync reload."); self.reload_config_sync()
        except Exception as e: logger.warning(f"Could not check config mtime for {self._config_path}: {e}.")
        if self._parsed_config and server_name in self._parsed_config.mcp_servers:
            return self._parsed_config.mcp_servers[server_name].model_dump(exclude_none=True)
        return None
        
    async def reload_config(self):
        logger.info("Async reloading: stopping servers, closing clients, reloading config...")
        await self.close_all_clients() 
        self._parsed_config = None 
        self._load_config() 
        logger.info("Async reload complete.")

    def reload_config_sync(self):
        logger.info("Sync reloading config (does not stop servers/close clients)...")
        if self._clients_cache: logger.warning("Cached clients cleared by sync reload.")
        self._parsed_config = None; self._clients_cache.clear()
        # Note: This sync reload does not stop running processes or close their log files.
        # Active processes in _local_server_processes and _log_file_handles remain.
        # This could lead to issues if server configs change drastically.
        # A full async reload is preferred if possible.
        self._load_config() 
        logger.info("Sync reload complete.")

    def get_config_path(self) -> Path: return self._config_path

    def is_local_server_running(self, server_name: str) -> bool:
        server_conf_model = self._get_server_conf_model(server_name)
        if not isinstance(server_conf_model, MCPServerConfigLocal): return False
        if server_conf_model.compose_managed and server_conf_model.project_compose_file_path and server_conf_model.compose_service_name:
            compose_file = Path(server_conf_model.project_compose_file_path)
            if not compose_file.exists(): return False
            cmd = f"docker-compose -f \"{compose_file.resolve()}\" ps -q {server_conf_model.compose_service_name}"
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=compose_file.parent, check=False)
                if result.returncode == 0 and result.stdout.strip():
                    container_id = result.stdout.strip()
                    if container_id:
                        inspect_cmd = f"docker inspect {container_id} --format='{{{{.State.Status}}}}'"
                        inspect_result = subprocess.run(inspect_cmd, shell=True, capture_output=True, text=True, check=False)
                        return inspect_result.returncode == 0 and inspect_result.stdout.strip() == "running"
                return False
            except Exception as e:
                logger.error(f"Error checking docker-compose status for '{server_name}': {e}")
                return False
        else: 
            process = self._local_server_processes.get(server_name)
            return process is not None and process.returncode is None
