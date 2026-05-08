# Import tool modules to register them on mcp
import tasks_mcp.tools.capture  # noqa: F401
import tasks_mcp.tools.modify  # noqa: F401
import tasks_mcp.tools.remove  # noqa: F401
import tasks_mcp.tools.resolve  # noqa: F401
import tasks_mcp.tools.review  # noqa: F401
from tasks_mcp.mcp_instance import mcp


@mcp.tool()
async def health() -> str:
    '''Health check for K8s probes. Returns ok when server is running.'''
    return '{"status": "ok"}'


def main():
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
