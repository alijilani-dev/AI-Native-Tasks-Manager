"""Health check for tasks_mcp Docker container.

Calls the MCP health tool via Streamable HTTP, handling session initialization.
"""
import json
import re
import sys
import urllib.request


def _parse_sse(text: str) -> dict:
    match = re.search(r'^data: (.+)$', text, re.MULTILINE)
    if match:
        return json.loads(match.group(1))
    return json.loads(text)


def main():
    base = f"http://localhost:{sys.argv[1] if len(sys.argv) > 1 else 8000}/mcp"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    # 1. Initialize session
    init_body = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "docker-healthcheck", "version": "1.0"},
        },
    }).encode()
    req = urllib.request.Request(base, data=init_body, headers=headers)
    with urllib.request.urlopen(req) as resp:
        _parse_sse(resp.read().decode())
        session_id = resp.headers.get("mcp-session-id")
        if not session_id:
            print("No session ID received")
            sys.exit(1)

    # 2. Call health tool
    health_body = json.dumps({
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": "health", "arguments": {}},
    }).encode()
    health_req = urllib.request.Request(
        base, data=health_body,
        headers={**headers, "mcp-session-id": session_id},
    )
    with urllib.request.urlopen(health_req) as resp:
        data = _parse_sse(resp.read().decode())
        text = data["result"]["content"][0]["text"]
        assert '"status": "ok"' in text, f"Unexpected response: {text}"

    sys.exit(0)


if __name__ == "__main__":
    main()
