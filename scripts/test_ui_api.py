import urllib.request
import json
import sys

base_url = "http://localhost:8080"

endpoints = [
    ("/api/health", "GET"),
    ("/api/setup/status", "GET"),
    ("/api/setup/progress", "GET"),
    ("/api/triggers/rules", "GET"),
    ("/api/triggers/events", "GET"),
    ("/api/agents", "GET"),
    ("/api/models/profiles", "GET"),
    ("/api/sources", "GET"),
]

print("=== TESTING HTTP UI/API ENDPOINTS ON CONTAINER (http://localhost:8080) ===")

for path, method in endpoints:
    url = f"{base_url}{path}"
    try:
        req = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req) as resp:
            data = resp.read().decode()
            status = resp.status
            print(f"[OK {status}] {method} {path} -> Length: {len(data)} bytes")
    except Exception as e:
        print(f"[ERROR] {method} {path} -> {e}")

print("=== ENDPOINTS TEST COMPLETE ===")
