# Chapter 17: Wireless Android ADB Integration

## Overview
The Device Subsystem (`backend/devices/core.py` and `auto_connect.py`) extends ADA's reach from the desktop to Android smartphones and tablets over the local Wi-Fi network.

## Key Capabilities
- **Zero-Config Auto-ADB**: Automatically discovers and pairs with Android devices broadcasting Wireless Debugging (mDNS / Zeroconf) on the local subnet.
- **Remote App Launching**: Launches WhatsApp, Spotify, Settings, or custom Android packages via `am start`.
- **Text & Message Injection**: Types messages directly into mobile apps using `input text` and `input tap`.
- **Battery & Telemetry Monitoring**: Pulls device battery level, network state, and screen status for the HUD.
