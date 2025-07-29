import typer
import shutil
import pathlib
import importlib.resources
import importlib.util
import os
import json
import asyncio 
import subprocess 
from typing import Optional, List, Dict, Any 
from pathlib import Path
from ruamel.yaml import YAML 

from alo_agent_sdk.alo_a2a.mcp.manager import MCPManager, MCPConfigError, MCPAuthEnvError, MCPManagerError
from alo_agent_sdk.alo_a2a.mcp.exceptions import MCPError
from alo_agent_sdk.alo_a2a.mcp.config_models import MCPServerConfigLocal

app = typer.Typer(help="ALO Agent SDK Command Line Interface")
mcp_app = typer.Typer(name="mcp", help="Manage Model Context Protocol (MCP) server configurations for your project.")
app.add_typer(mcp_app)


# --- Helper function for CLI to get config path ---
def _get_mcp_config_file_path() -> Path:
    return MCPManager.get_default_config_filepath()

def _tail_file(filepath: Path, lines: int) -> List[str]:
    if not filepath.exists():
        return [f"Log file not found: {filepath}"]
    if lines <= 0:
        try:
            return filepath.read_text(encoding='utf-8', errors='replace').splitlines()
        except Exception as e:
            return [f"Error reading log file {filepath}: {e}"]
    try:
        with open(filepath, 'rb') as f:
            f.seek(0, os.SEEK_END)
            fsize = f.tell()
            if fsize == 0: return []
            num_lines_found = 0
            buffer_size = 4096 
            buffer = bytearray()
            while num_lines_found < lines and f.tell() > 0:
                seek_pos = max(0, f.tell() - buffer_size)
                f.seek(seek_pos)
                chunk = f.read(min(fsize, buffer_size if f.tell() > buffer_size else f.tell())) 
                buffer = chunk + buffer
                f.seek(seek_pos)
                num_lines_found = buffer.count(b'\n')
                if f.tell() == 0: break 
            try: decoded_buffer = buffer.decode('utf-8', errors='replace')
            except UnicodeDecodeError: decoded_buffer = buffer.decode('latin-1', errors='replace')
            all_lines = decoded_buffer.splitlines()
            return all_lines[-lines:]
    except Exception as e:
        return [f"Error reading log file {filepath}: {e}"]

async def _follow_file_async(filepath: Path, stream_name: str):
    typer.echo(f"Following {stream_name} from {filepath} (Ctrl+C to stop)...")
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            f.seek(0, 2)
            while True:
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.1)
                    continue
                typer.echo(f"[{stream_name}] {line.strip()}")
    except FileNotFoundError: typer.secho(f"Log file {filepath} not found.", fg=typer.colors.RED)
    except KeyboardInterrupt: typer.echo(f"\nStopped following {stream_name}.")
    except Exception as e: typer.secho(f"Error following log file {filepath}: {e}", fg=typer.colors.RED)

# --- MCP CLI Commands ---
@mcp_app.command("configure")
def configure_mcp_server(
    server_name: str = typer.Argument(..., help="A unique name for this MCP server configuration."),
    type_str: str = typer.Option(..., "--type", "-t", help="Type of the server: 'remote' or 'local'.", case_sensitive=False, metavar="TYPE"),
    url: Optional[str] = typer.Option(None, "--url", help="[Remote] URL of the remote MCP server."),
    auth_type_str: Optional[str] = typer.Option(None, "--auth-type", help="Authentication type: 'none', 'basic', 'bearer', 'api_key'.", case_sensitive=False, metavar="AUTH_TYPE"),
    auth_source_str: Optional[str] = typer.Option(None, "--auth-source", help="Source for auth credentials: 'env' or 'file'.", case_sensitive=False, metavar="SOURCE"),
    auth_username_env: Optional[str] = typer.Option(None, "--auth-username-env", help="[env source] Env var for basic auth username."),
    auth_password_env: Optional[str] = typer.Option(None, "--auth-password-env", help="[env source] Env var for basic auth password."),
    auth_token_env: Optional[str] = typer.Option(None, "--auth-token-env", help="[env source] Env var for the token/API key."),
    auth_username_file: Optional[str] = typer.Option(None, "--auth-username-file", help="[file source] Path to file containing basic auth username."),
    auth_password_file: Optional[str] = typer.Option(None, "--auth-password-file", help="[file source] Path to file containing basic auth password."),
    auth_token_file: Optional[str] = typer.Option(None, "--auth-token-file", help="[file source] Path to file containing the token/API key."),
    auth_apikey_name: Optional[str] = typer.Option(None, "--auth-apikey-name", help="[API Key Auth] Header or query name for API key."),
    auth_apikey_location: Optional[str] = typer.Option(None, "--auth-apikey-location", help="[API Key Auth] Location: 'header' or 'query'.", case_sensitive=False, metavar="LOCATION"),
    project_path_str: Optional[str] = typer.Option(None, "--project-path", help="[Local] Path to the local MCP server project directory."),
    run_command: Optional[str] = typer.Option(None, "--run-command", help="[Local] Command to run the local MCP server."),
    port: Optional[int] = typer.Option(None, "--port", help="[Local] Port number the local server will listen on."),
    env_file_str: Optional[str] = typer.Option(None, "--env-file", help="[Local] Path to the .env file for the local server (optional)."),
    healthcheck_path: Optional[str] = typer.Option(None, "--healthcheck-path", help="[Local] Healthcheck path (e.g., '/health', optional)."),
    auto_start: Optional[bool] = typer.Option(None, "--auto-start/--no-auto-start", help="[Local] Auto-start this server when client is requested."),
    dockerfile_str: Optional[str] = typer.Option(None, "--dockerfile", help="[Local Docker] Relative path to Dockerfile within project-path."),
    docker_image_name: Optional[str] = typer.Option(None, "--docker-image", help="[Local Docker] Custom Docker image name."),
    compose_service_name_str: Optional[str] = typer.Option(None, "--compose-service-name", help="[Local Docker] Name for service in Docker Compose."),
    compose_generate_snippet: bool = typer.Option(False, "--compose-generate-snippet", help="[Local Docker] Generate Docker Compose snippet."),
    compose_managed: Optional[bool] = typer.Option(None, "--compose-managed/--no-compose-managed", help="[Local Docker] SDK manages this via project's docker-compose.yml."),
    project_compose_file_str: Optional[str] = typer.Option(None, "--project-compose-file", help="[Local Docker, if compose-managed] Path to project's docker-compose.yml.")
):
    config_file_path = _get_mcp_config_file_path()
    config_data: Dict[str, Any] = {}
    if config_file_path.exists():
        try:
            with open(config_file_path, 'r') as f: config_data = json.load(f)
            if not isinstance(config_data, dict) or "mcp_servers" not in config_data or not isinstance(config_data.get("mcp_servers"), dict):
                config_data = {"mcp_servers": {}, "version": "1.0"}
        except json.JSONDecodeError: config_data = {"mcp_servers": {}, "version": "1.0"}
    else: config_data = {"mcp_servers": {}, "version": "1.0"}

    final_type_str = type_str.lower()
    server_entry: Dict[str, Any] = {"type": final_type_str}

    if final_type_str == "remote":
        final_url = url or typer.prompt("URL of the remote MCP server")
        if not final_url: typer.secho("URL is required.", fg=typer.colors.RED); raise typer.Exit(1)
        server_entry["url"] = final_url
    elif final_type_str == "local":
        final_project_path_str = project_path_str or typer.prompt("Path to local MCP server project", default=".")
        project_path_abs = Path(final_project_path_str).resolve()
        server_entry["project_path"] = str(project_path_abs)
        final_run_command = run_command or typer.prompt("Run command for local server")
        if not final_run_command: typer.secho("Run command required.", fg=typer.colors.RED); raise typer.Exit(1)
        server_entry["run_command"] = final_run_command
        final_port = port if port is not None else typer.prompt("Port", type=int, default=8000)
        server_entry["port"] = final_port
        final_env_file_str = env_file_str if env_file_str is not None else typer.prompt(".env file path (optional)", default="", show_default=False)
        if final_env_file_str: server_entry["env_file_path"] = str(Path(final_env_file_str).resolve())
        final_healthcheck_path = healthcheck_path if healthcheck_path is not None else typer.prompt("Healthcheck path (optional)", default="", show_default=False)
        if final_healthcheck_path: server_entry["healthcheck_path"] = final_healthcheck_path
        final_auto_start = auto_start if auto_start is not None else typer.confirm("Auto-start server?", default=False)
        server_entry["auto_start"] = final_auto_start
        if typer.confirm("Configure Docker options?", default=False):
            final_dockerfile_str = dockerfile_str or typer.prompt("Dockerfile path", default="Dockerfile")
            if final_dockerfile_str: server_entry["dockerfile_path"] = final_dockerfile_str
            final_docker_image_name = docker_image_name or typer.prompt("Docker image name (optional)", default="", show_default=False)
            if final_docker_image_name: server_entry["docker_image_name"] = final_docker_image_name
            final_compose_service_name_str = compose_service_name_str or typer.prompt("Docker Compose service name", default=server_name)
            server_entry["compose_service_name"] = final_compose_service_name_str
            final_compose_managed = compose_managed if compose_managed is not None else typer.confirm("SDK manage via Docker Compose?", default=False)
            server_entry["compose_managed"] = final_compose_managed
            if final_compose_managed:
                final_project_compose_file_str = project_compose_file_str or typer.prompt("Path to project's docker-compose.yml", default="docker-compose.yml")
                if final_project_compose_file_str: server_entry["project_compose_file_path"] = str(Path(final_project_compose_file_str).resolve())
                else: typer.secho("Project Docker Compose file path needed.", fg=typer.colors.YELLOW)
    else: typer.secho(f"Error: Invalid type '{final_type_str}'.", fg=typer.colors.RED); raise typer.Exit(1)

    final_auth_type_str_val = auth_type_str
    if final_auth_type_str_val is None: final_auth_type_str_val = typer.prompt("Auth type", default="none", show_choices=["none", "basic", "bearer", "api_key"],show_default=True, case_sensitive=False)
    final_auth_type_str_val = final_auth_type_str_val.lower()

    if final_auth_type_str_val != "none":
        auth_config: Dict[str, Any] = {"type": final_auth_type_str_val}
        final_auth_source_str = auth_source_str or typer.prompt("Auth credentials source", default="env", show_choices=["env", "file"], case_sensitive=False)
        auth_config["auth_source"] = final_auth_source_str.lower()

        if final_auth_type_str_val == "basic":
            if auth_config["auth_source"] == "env":
                final_auth_username_env = auth_username_env or typer.prompt("Env var for username")
                final_auth_password_env = auth_password_env or typer.prompt("Env var for password")
                if not final_auth_username_env or not final_auth_password_env: typer.secho("Username/password env vars required.", fg=typer.colors.RED); raise typer.Exit(1)
                auth_config["username_env_var"] = final_auth_username_env; auth_config["password_env_var"] = final_auth_password_env
            elif auth_config["auth_source"] == "file":
                final_auth_username_file = auth_username_file or typer.prompt("Path to username file")
                final_auth_password_file = auth_password_file or typer.prompt("Path to password file")
                if not final_auth_username_file or not final_auth_password_file: typer.secho("Username/password file paths required.", fg=typer.colors.RED); raise typer.Exit(1)
                auth_config["username_file_path"] = str(Path(final_auth_username_file).resolve()); auth_config["password_file_path"] = str(Path(final_auth_password_file).resolve())
        elif final_auth_type_str_val in ["bearer", "api_key"]:
            if auth_config["auth_source"] == "env":
                final_auth_token_env = auth_token_env or typer.prompt(f"Env var for {final_auth_type_str_val} token/key")
                if not final_auth_token_env: typer.secho(f"Token env var required.", fg=typer.colors.RED); raise typer.Exit(1)
                auth_config["token_env_var"] = final_auth_token_env
            elif auth_config["auth_source"] == "file":
                final_auth_token_file = auth_token_file or typer.prompt(f"Path to file for {final_auth_type_str_val} token/key")
                if not final_auth_token_file: typer.secho(f"Token file path required.", fg=typer.colors.RED); raise typer.Exit(1)
                auth_config["token_file_path"] = str(Path(final_auth_token_file).resolve())
            if final_auth_type_str_val == "api_key":
                final_auth_apikey_name = auth_apikey_name or typer.prompt("API key name", default="X-API-Key")
                auth_config["key_name"] = final_auth_apikey_name
                final_auth_apikey_location = auth_apikey_location or typer.prompt("API key location", default="header", show_choices=["header", "query"], case_sensitive=False)
                auth_config["location"] = final_auth_apikey_location.lower()
                if auth_config["location"] not in ["header", "query"]: typer.secho("API key location: 'header' or 'query'.", fg=typer.colors.RED); raise typer.Exit(1)
        else: typer.secho(f"Warning: Unknown auth type '{final_auth_type_str_val}'.", fg=typer.colors.YELLOW); auth_config = {}
        if auth_config and auth_config.get("type") != "none": server_entry["authentication"] = auth_config
    
    config_data.setdefault("mcp_servers", {})[server_name] = server_entry
    config_data.setdefault("version", "1.0")
    try:
        config_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file_path, 'w') as f: json.dump(config_data, f, indent=2)
        typer.secho(f"MCP server '{server_name}' configured in {config_file_path}", fg=typer.colors.GREEN)
        if server_entry["type"] == "local" and compose_generate_snippet:
            typer.echo("\n--- Docker Compose Snippet ---")
            project_root_for_compose = MCPManager._find_project_root(Path.cwd())
            context_path_str = str(server_entry["project_path"]) 
            try: context_path_rel = os.path.relpath(context_path_str, project_root_for_compose)
            except ValueError: context_path_rel = context_path_str 
            snippet_service_name = server_entry.get("compose_service_name", server_name)
            service_def = { "build": { "context": f"./{context_path_rel}", "dockerfile": server_entry.get("dockerfile_path", "Dockerfile") }, "ports": [f"{server_entry['port']}:{server_entry['port']}"], }
            if server_entry.get("env_file_path"):
                env_file_abs = Path(server_entry["env_file_path"])
                try: env_file_rel = os.path.relpath(env_file_abs, project_root_for_compose); service_def["env_file"] = [f"./{env_file_rel}"]
                except ValueError: service_def["env_file"] = [str(env_file_abs)]
            if server_entry.get("docker_image_name"): service_def["image"] = server_entry["docker_image_name"]
            compose_snippet = {snippet_service_name: service_def}
            yaml = YAML(); yaml.indent(mapping=2, sequence=4, offset=2)
            import io; string_stream = io.StringIO()
            yaml.dump(compose_snippet, string_stream)
            typer.echo("# Add to your project's docker-compose.yml services section:")
            typer.echo(f"# Ensure paths are correct relative to your docker-compose.yml.")
            typer.echo(string_stream.getvalue())
    except Exception as e:
        typer.secho(f"Error writing config or snippet: {e}", fg=typer.colors.RED); raise typer.Exit(1)

@mcp_app.command("list")
def list_mcp_servers():
    config_file_path = _get_mcp_config_file_path()
    if not config_file_path.exists(): typer.echo(f"Config file {config_file_path} not found."); return
    try:
        manager = MCPManager(config_path=config_file_path)
        names = manager.list_server_names()
        if not names: typer.echo(f"No MCP servers in {config_file_path}."); return
        typer.secho("Configured MCP Servers:", bold=True)
        for name in names:
            conf = manager.get_server_config(name)
            typer.echo(f"- {name} (type: {conf.get('type', 'N/A') if conf else 'N/A'})")
    except Exception as e: typer.secho(f"Error loading config: {e}", fg=typer.colors.RED); raise typer.Exit(1)

@mcp_app.command("describe")
def describe_mcp_server(server_name: str = typer.Argument(..., help="Name of the MCP server.")):
    config_file_path = _get_mcp_config_file_path()
    if not config_file_path.exists(): typer.echo(f"Config file not found."); return
    try:
        manager = MCPManager(config_path=config_file_path)
        conf = manager.get_server_config(server_name)
        if not conf: typer.secho(f"Server '{server_name}' not found.", fg=typer.colors.RED); raise typer.Exit(1)
        typer.secho(f"Config for '{server_name}':", bold=True); typer.echo(json.dumps(conf, indent=2))
    except Exception as e: typer.secho(f"Error loading config: {e}", fg=typer.colors.RED); raise typer.Exit(1)

@mcp_app.command("remove")
def remove_mcp_server(server_name: str = typer.Argument(..., help="Name of the MCP server.")):
    config_file_path = _get_mcp_config_file_path()
    if not config_file_path.exists(): typer.secho(f"Config file not found.", fg=typer.colors.RED); raise typer.Exit(1)
    try:
        with open(config_file_path, 'r') as f: config_data = json.load(f)
        if server_name not in config_data.get("mcp_servers", {}):
            typer.secho(f"Server '{server_name}' not found.", fg=typer.colors.YELLOW); raise typer.Exit(0)
        if not typer.confirm(f"Remove MCP server '{server_name}'?"): typer.echo("Removal cancelled."); raise typer.Exit(0)
        del config_data["mcp_servers"][server_name]
        with open(config_file_path, 'w') as f: json.dump(config_data, f, indent=2)
        typer.secho(f"Server '{server_name}' removed.", fg=typer.colors.GREEN)
    except Exception as e: typer.secho(f"Error processing config: {e}", fg=typer.colors.RED); raise typer.Exit(1)

@mcp_app.command("start")
def start_mcp_server(server_name: str = typer.Argument(..., help="Name of the local MCP server to start.")):
    manager = MCPManager() 
    try:
        if asyncio.run(manager.start_local_server(server_name)):
            typer.secho(f"Local MCP server '{server_name}' starting...", fg=typer.colors.GREEN)
        else:
            typer.secho(f"Failed to start '{server_name}'. Check logs.", fg=typer.colors.RED)
    except (MCPConfigError, MCPManagerError) as e: typer.secho(f"Error starting '{server_name}': {e}", fg=typer.colors.RED)
    except Exception as e: typer.secho(f"Unexpected error starting '{server_name}': {e}", fg=typer.colors.RED)

@mcp_app.command("stop")
def stop_mcp_server(server_name: str = typer.Argument(..., help="Name of the local MCP server to stop.")):
    manager = MCPManager()
    try:
        if asyncio.run(manager.stop_local_server(server_name)):
            typer.secho(f"Local MCP server '{server_name}' stopped.", fg=typer.colors.GREEN)
        else:
            typer.secho(f"Failed to stop '{server_name}'.", fg=typer.colors.YELLOW)
    except (MCPConfigError, MCPManagerError) as e: typer.secho(f"Error stopping '{server_name}': {e}", fg=typer.colors.RED)
    except Exception as e: typer.secho(f"Unexpected error stopping '{server_name}': {e}", fg=typer.colors.RED)

@mcp_app.command("status")
def status_mcp_server(server_name: Optional[str] = typer.Argument(None, help="Name of a local MCP server. If omitted, shows all.")):
    manager = MCPManager()
    servers_to_check = []
    if server_name:
        s_conf = manager.get_server_config(server_name)
        if not s_conf: typer.secho(f"Server '{server_name}' not configured.", fg=typer.colors.RED); raise typer.Exit(1)
        if s_conf.get("type") != "local": typer.secho(f"'{server_name}' is not local.", fg=typer.colors.YELLOW); raise typer.Exit(0)
        servers_to_check.append(server_name)
    else:
        for name in manager.list_server_names():
            s_conf = manager.get_server_config(name)
            if s_conf and s_conf.get("type") == "local": servers_to_check.append(name)
    if not servers_to_check: typer.echo("No local MCP servers configured."); return
    typer.secho("Local MCP Server Status:", bold=True)
    for name in servers_to_check:
        is_running = manager.is_local_server_running(name)
        status_color = typer.colors.GREEN if is_running else typer.colors.RED
        status_text = "Running" if is_running else "Not Running / Stopped"
        process_info = manager._local_server_processes.get(name)
        pid_info = ""
        if process_info is None and manager._get_server_conf_model(name).compose_managed: # type: ignore
            pid_info = "(managed by Docker Compose)"
        elif process_info and hasattr(process_info, 'pid') and process_info.pid is not None:
            pid_info = f"(PID: {process_info.pid})"
        typer.secho(f"- {name}: {status_text} {pid_info}", fg=status_color)

@mcp_app.command("logs")
def logs_mcp_server(
    server_name: str = typer.Argument(..., help="Name of the local MCP server to view logs for."),
    lines: Optional[int] = typer.Option(100, "--lines", "-n", help="Number of lines to show from the end of the logs. Use 0 for all."),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output.")
):
    manager = MCPManager()
    try:
        server_conf_model = manager._get_server_conf_model(server_name) 
        if not isinstance(server_conf_model, MCPServerConfigLocal):
            typer.secho(f"Server '{server_name}' is not a local server.", fg=typer.colors.YELLOW); raise typer.Exit(0)

        if server_conf_model.compose_managed and server_conf_model.project_compose_file_path and server_conf_model.compose_service_name:
            compose_file = Path(server_conf_model.project_compose_file_path)
            if not compose_file.exists():
                typer.secho(f"Docker Compose file {compose_file} not found for '{server_name}'.", fg=typer.colors.RED); raise typer.Exit(1)
            cmd_parts = ["docker-compose", "-f", str(compose_file.resolve()), "logs"]
            if follow: cmd_parts.append("--follow")
            if lines is not None and lines > 0 : cmd_parts.extend(["--tail", str(lines)])
            cmd_parts.append(server_conf_model.compose_service_name)
            typer.echo(f"Showing logs for '{server_name}' via Docker Compose (Cmd: {' '.join(cmd_parts)}) ...")
            subprocess.run(cmd_parts, cwd=compose_file.parent, check=False)
        else:
            stdout_log, stderr_log = manager._get_log_paths(server_name) 
            typer.echo(f"Showing logs for '{server_name}' (from files):")
            if stdout_log.exists():
                typer.secho(f"--- STDOUT ({stdout_log}) ---", bold=True)
                for line in _tail_file(stdout_log, lines if lines is not None else 0): typer.echo(line)
            else: typer.echo(f"Stdout log file not found: {stdout_log}")
            if stderr_log.exists():
                typer.secho(f"\n--- STDERR ({stderr_log}) ---", bold=True)
                for line in _tail_file(stderr_log, lines if lines is not None else 0): typer.echo(line, err=True)
            else: typer.echo(f"Stderr log file not found: {stderr_log}")
            if follow:
                async def _follow_both():
                    tasks = []
                    if stdout_log.exists(): tasks.append(_follow_file_async(stdout_log, "stdout"))
                    if stderr_log.exists(): tasks.append(_follow_file_async(stderr_log, "stderr"))
                    if not tasks: typer.echo("No log files found to follow."); return
                    await asyncio.gather(*tasks)
                try: asyncio.run(_follow_both())
                except KeyboardInterrupt: typer.echo("\nStopped following logs.")
    except (MCPConfigError, MCPManagerError) as e:
        typer.secho(f"Error accessing logs for '{server_name}': {e}", fg=typer.colors.RED)
    except Exception as e:
        typer.secho(f"Unexpected error accessing logs for '{server_name}': {e}", fg=typer.colors.RED)

@app.command()
def hello():
    typer.echo("Hello from ALO SDK CLI!")

@app.command()
def create_app(template_name: str, output_dir_str: str):
    typer.echo(f"Creating new application from template '{template_name}' in '{output_dir_str}'...")
    output_dir = pathlib.Path(output_dir_str)
    if output_dir.exists():
        typer.echo(f"Warning: Output directory '{output_dir}' already exists. Removing for test.")
        try: shutil.rmtree(output_dir)
        except Exception as e: typer.secho(f"Could not remove existing directory {output_dir}: {e}", fg=typer.colors.RED)
    try:
        source_template_dir_traversable = importlib.resources.files("alo_agent_sdk").joinpath("project_templates", template_name)
        if not source_template_dir_traversable.is_dir():
            typer.secho(f"Error: Template source '{template_name}' not found at {source_template_dir_traversable}", fg=typer.colors.RED); raise typer.Exit(1)
        with importlib.resources.as_file(source_template_dir_traversable) as source_path_concrete:
            if output_dir.exists() and list(output_dir.iterdir()):
                typer.secho(f"Error: Output directory '{output_dir}' exists and is not empty.", fg=typer.colors.RED); raise typer.Exit(1)
            output_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source_path_concrete, output_dir, dirs_exist_ok=True)
        typer.secho(f"Successfully created project '{output_dir.name}' from template '{template_name}'.", fg=typer.colors.GREEN)
        typer.echo("\nNext steps:"); typer.echo(f"  1. Navigate to the project: cd {output_dir}")
        if template_name == "mana":
            typer.echo("  2. Review README.md for setup."); typer.echo("  3. Edit requirements.sdk.txt for local SDK if needed.")
            typer.echo("  4. Run with Docker: docker-compose up --build"); typer.echo("  5. Deploy with deploy_all.sh.")
    except Exception as e:
        typer.secho(f"An unexpected error occurred: {e}", fg=typer.colors.RED); raise typer.Exit(1)

if __name__ == "__main__":
    app()
