# Chapter 31: Packaging Native Desktop App with Tauri

## Overview
ADA includes a native Rust Tauri v2 desktop shell (`frontend/src-tauri/`) that packages the React frontend into an ultra-compact Windows desktop executable (.exe / .msi).

## Building the Desktop App
```bash
cd frontend
npm run tauri build
```

## Binary Artifacts
- Location: `frontend/src-tauri/target/release/`
- Executable: `ADA.exe` (~15 MB lightweight executable)
- Auto-updates and system tray integration enabled out of the box.
