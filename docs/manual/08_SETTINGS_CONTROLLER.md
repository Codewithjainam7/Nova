# Chapter 08: Windows Settings Controller & Deep Linking

## Overview
The Settings Controller (`backend/desktop/controllers/settings_controller.py`) allows ADA to manage Windows configuration, security, updates, and hardware preferences instantly.

## Supported Tab Mappings
ADA maps natural language settings requests to official Windows URI schemes:
- **Windows Update**: `ms-settings:windowsupdate`
- **Display**: `ms-settings:display`
- **Sound**: `ms-settings:sound`
- **Bluetooth & Devices**: `ms-settings:bluetooth`
- **Network & Wi-Fi**: `ms-settings:network-wifi`
- **Privacy & Security**: `ms-settings:privacy`
- **Apps & Features**: `ms-settings:appsfeatures`
- **Power & Battery**: `ms-settings:powersleep`

## Automated Update Checking
When asked *"Check for Windows updates"*, the controller:
1. Launches `ms-settings:windowsupdate`.
2. Waits for the UWP page render.
3. Automatically triggers the "Check for updates" button action.
