"""
Custom exceptions for the Model Context Protocol (MCP) client and manager.
"""

class MCPError(Exception):
    """Base class for all MCP-related errors."""
    pass

# --- MCP Client Errors ---
class MCPClientError(MCPError):
    """Base class for errors originating from MCPClient operations."""
    pass

class MCPConnectionError(MCPClientError):
    """Error connecting to an MCP server or network-related issues."""
    pass

class MCPTimeoutError(MCPClientError):
    """Timeout during an MCP request."""
    pass

class MCPToolError(MCPClientError):
    """Error reported by the MCP server during tool execution or an issue with the tool itself."""
    pass

class MCPAuthenticationError(MCPClientError):
    """Authentication failed when trying to communicate with the MCP server (e.g., 401, 403)."""
    pass

class MCPResponseParseError(MCPClientError):
    """Error parsing the response from an MCP server (e.g., malformed JSON)."""
    pass

# --- MCP Manager Errors ---
class MCPManagerError(MCPError):
    """Base class for errors originating from MCPManager operations."""
    pass

class MCPConfigError(MCPManagerError):
    """Error related to the MCP server configuration (e.g., mcp_servers.json)."""
    pass

class MCPAuthEnvError(MCPManagerError):
    """Error due to a missing or invalid environment variable required for authentication."""
    pass
