import json
import os
import re
import shutil
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

import httpx
import pytest


def _find_project_root():
    return str(Path(__file__).resolve().parent.parent.parent)


def _port_open(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def _parse_sse_response(text: str) -> dict:
    data_match = re.search(r'^data: (.+)$', text, re.MULTILINE)
    if data_match:
        return json.loads(data_match.group(1))
    return json.loads(text)


@pytest.fixture(scope="session")
def server_port():
    return 18567


@pytest.fixture(scope="session")
def server_url(server_port):
    return f"http://localhost:{server_port}"


@pytest.fixture(scope="session")
def e2e_server(server_port, server_url):
    root = _find_project_root()
    env = {**os.environ, "TASKS_MCP_PORT": str(server_port)}
    process = subprocess.Popen(
        [shutil.which("uv"), "run", "python", "-m", "tasks_mcp.server"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        time.sleep(0.5)
        if _port_open("127.0.0.1", server_port):
            time.sleep(1)
            break
    else:
        process.terminate()
        process.wait(3)
        out, err = process.communicate()
        raise RuntimeError(
            f"Server did not start on port {server_port}\n"
            f"stdout:\n{out.decode(errors='replace')}\n"
            f"stderr:\n{err.decode(errors='replace')}"
        )

    yield server_url

    process.terminate()
    process.wait(5)


@pytest.fixture(scope="session")
def session_id(e2e_server):
    body = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "pytest-e2e", "version": "1.0"},
        },
    }).encode()
    req = urllib.request.Request(
        f"{e2e_server}/mcp",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        text = resp.read().decode()
    data = _parse_sse_response(text)
    sid = resp.headers.get("Mcp-Session-Id") or data.get("meta", {}).get("sessionId")
    return sid


@pytest.fixture
async def e2e_client(e2e_server):
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(base_url=e2e_server, timeout=15, headers=headers) as client:
        yield client


@pytest.fixture(autouse=True)
def reset_storage():
    import tasks_mcp.storage as storage
    storage.clear()
    yield


async def call_tool(client, session_id, name: str, args: dict) -> dict:
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": args},
    }
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "Mcp-Session-Id": session_id,
    } if session_id else {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    response = await client.post("/mcp", json=body, headers=headers)
    return _parse_sse_response(response.text)
