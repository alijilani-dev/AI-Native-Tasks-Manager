from mcp.server.fastmcp import FastMCP

from tasks_mcp.config import PORT

mcp = FastMCP("tasks_mcp", host="0.0.0.0", port=PORT, streamable_http_path="/mcp")
