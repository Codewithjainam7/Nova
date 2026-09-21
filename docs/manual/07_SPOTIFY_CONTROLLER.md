# Chapter 07: Native Spotify Desktop Controller

## Overview
The Spotify Controller (`backend/desktop/controllers/spotify_controller.py`) enables full desktop Spotify playback and navigation without requiring Spotify Developer API tokens or premium OAuth authentication.

## Supported Operations
- `play_media`: Searches for a song or artist and initiates playback.
- `pause` / `resume`: Toggles global media playback via virtual media keys.
- `next_track` / `previous_track`: Advances or rewinds playlist tracks.
- `open_app`: Focuses or launches the Spotify desktop client.

## Implementation Details
```python
# Launching or focusing Spotify via Windows URI protocol
os.startfile("spotify:")

# Searching and playing a track via keyboard sequence
pyautogui.hotkey('ctrl', 'l')       # Focus search bar
pyautogui.write(song_name, 0.04)    # Type track title
pyautogui.press('enter')            # Search
pyautogui.press('enter')            # Play top result
```
