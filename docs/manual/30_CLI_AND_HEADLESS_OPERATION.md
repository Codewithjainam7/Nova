# Chapter 30: CLI & Headless Daemon Operation

## Overview
ADA can be operated completely headless from the command line or as a background Windows service without opening the 3D web interface.

## CLI Execution
```bash
python -m backend.cli --query "Check for Windows updates"
```

## Running as Background Daemon
To run ADA as a persistent background daemon listening for voice hotwords or network webhooks:
```bash
python -m backend.main --daemon --port 8000
```
