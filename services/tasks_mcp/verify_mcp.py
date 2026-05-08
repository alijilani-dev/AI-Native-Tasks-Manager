import requests
import json
import time

# Use the canonical URL with a trailing slash to avoid 307 redirects
URL = "http://localhost:8000/mcp/"
HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json"
}

print("🔄 Step 1: Initializing Session Handshake...")
init_payload = {
    "jsonrpc": "2.0", 
    "id": 1, 
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05", 
        "capabilities": {}, 
        "clientInfo": {"name": "manual-tester", "version": "1.0"}
    }
}

try:
    # Send initialization request and capture the response
    r1 = requests.post(URL, json=init_payload, headers=HEADERS, allow_redirects=True)
    
    if r1.status_code != 200:
        print(f"❌ Initialization Failed with status code: {r1.status_code}")
        sys.exit(1)
        
    sid = r1.headers.get("mcp-session-id")
    if not sid:
        print("❌ Server responded but did not return an 'mcp-session-id' header.")
        exit(1)
        
    print(f"✅ Handshake Stable! Captured Session ID: {sid}")
    print("📋 Initialization Metadata:")
    print(r1.text)
    print("-" * 50)

    # Attach the session ID to the request headers for subsequent calls
    HEADERS["mcp-session-id"] = sid

    print("🔄 Step 2: Sending Mandatory Initialized Notification...")
    # MCP spec requires an initialized notification before executing tools
    notification_payload = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }
    r_msg = requests.post(URL, json=notification_payload, headers=HEADERS, allow_redirects=True)
    print(f"👉 Notification Status: {r_msg.status_code} (Expected 200 or 202/204)\n")

    print("🔄 Step 3: Triggering Health Check Tool...")
    health_payload = {
        "jsonrpc": "2.0", 
        "id": 2, 
        "method": "tools/call", 
        "params": {"name": "health", "arguments": {}}
    }
    r2 = requests.post(URL, json=health_payload, headers=HEADERS, allow_redirects=True)
    print("📋 Health Response Payload:")
    print(r2.text)
    print("-" * 50)

    print("🔄 Step 4: Triggering Task Capture Tool...")
    capture_payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "tasks_capture", "arguments": {"title": "Verified Task", "type": "task"}}
    }
    r3 = requests.post(URL, json=capture_payload, headers=HEADERS, allow_redirects=True)
    print("📋 Task Capture Response Payload:")
    print(r3.text)

except Exception as e:
    print(f"❌ Connection error: {str(e)}")
