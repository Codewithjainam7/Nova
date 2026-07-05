import sys
import os

print(f"Python Version: {sys.version}")

try:
    import fastapi
    import uvicorn
    import pydantic
    import sqlalchemy
    import loguru
    import apscheduler
    import playwright
    import easyocr
    import cv2
    import PIL
    import pyautogui
    import pywinauto
    import chromadb
    import sentence_transformers
    import onnxruntime
    import openwakeword
    import whisper
    import edge_tts
    import dotenv
    print("All backend dependencies imported successfully!")
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)
