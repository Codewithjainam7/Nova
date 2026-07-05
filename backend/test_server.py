import subprocess
import time
import urllib.request
import sys

print("Starting backend server...")
proc = subprocess.Popen([".venv\\Scripts\\python.exe", "main.py"])
time.sleep(3) # Wait for server to start

try:
    print("Testing /health endpoint...")
    req = urllib.request.Request("http://127.0.0.1:8000/health")
    with urllib.request.urlopen(req) as response:
        if response.status == 200:
            print("API Health Endpoint OK!")
        else:
            print(f"Failed with status: {response.status}")
            sys.exit(1)
except Exception as e:
    print(f"Failed to connect to server: {e}")
    proc.kill()
    sys.exit(1)

proc.kill()
print("Backend verification complete.")
