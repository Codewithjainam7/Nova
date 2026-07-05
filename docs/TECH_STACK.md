# TECH STACK

Project: NOVA

Document Type: Technology Stack

Version: 1.0.0

Status: Final

Priority: Critical

Depends On:

PROJECT_CONSTITUTION.md

VISION.md

SYSTEM_ARCHITECTURE.md

PRODUCT_REQUIREMENTS.md

---

# Purpose

This document defines every technology used in NOVA.

Technology choices should remain stable unless a major architectural reason exists.

---

# Overall Architecture

Frontend

↓

IPC

↓

Python Backend

↓

AI Runtime

↓

Operating System

---

# Desktop Framework

Tauri v2

Reason:

• Lightweight

• Native Performance

• Small Bundle Size

• Rust Security

• Excellent Windows Support

---

# Frontend

React 19

TypeScript

Vite

React Router

TanStack Query

Zustand

React Hook Form

---

# Styling

Tailwind CSS

Framer Motion

CSS Variables

Glassmorphism Components

---

# Icons

Lucide React

---

# Animation

Framer Motion

Motion One (Optional)

CSS Animations

---

# State Management

Zustand

Server State

TanStack Query

---

# Backend

Python 3.12+

FastAPI

Uvicorn

Pydantic

---

# AI Providers

Primary

Google Gemini

Secondary

OpenRouter

Fallback

Local Ollama Models

Future

OpenAI

Anthropic

Mistral

Groq

---

# Local Models

Ollama

Qwen

Llama

DeepSeek

Phi

Gemma

---

# Speech To Text

Primary

Whisper

Future

Faster Whisper

Cloud APIs

---

# Text To Speech

Microsoft Edge TTS

Piper

Future

ElevenLabs

---

# Wake Word

OpenWakeWord

Future

Porcupine

---

# Browser Automation

Playwright

Primary Browser

Brave

Supported

Chrome

Edge

Firefox

---

# Desktop Automation

PyWinAuto

PyAutoGUI

Windows APIs

Accessibility APIs

---

# Vision

EasyOCR

Tesseract

OpenCV

Pillow

Future

YOLO

---

# Database

SQLite

Future

PostgreSQL

---

# Vector Database

ChromaDB

Future

Qdrant

FAISS

---

# Memory Storage

SQLite

JSON

Vector Store

---

# Logging

Loguru

Python Logging

---

# Scheduling

APScheduler

---

# Background Tasks

AsyncIO

ThreadPool

Worker Queue

---

# Communication

IPC

WebSockets

REST

---

# Security

Windows Credential Manager

Environment Variables

Encrypted Local Storage

---

# File Formats

JSON

Markdown

SQLite

YAML

CSV

PDF

DOCX

TXT

---

# Package Managers

Frontend

npm

Backend

pip

---

# Testing

Pytest

Vitest

Playwright

---

# Code Quality

ESLint

Prettier

Black

Ruff

MyPy

---

# CI/CD

GitHub Actions

---

# Version Control

Git

GitHub

---

# Deployment

Desktop Installer

MSI

EXE

Auto Update

---

# Build Tools

Vite

Tauri Build

PyInstaller

---

# AI Prompt Storage

Markdown

YAML

---

# Configuration

JSON

Environment Variables

---

# Future Technologies

Plugin SDK

Rust Extensions

Mobile Companion

Cloud Sync

Multi-device Memory

---

# Technology Selection Rules

Technology must be:

Open Source Preferred

Well Maintained

Production Ready

Cross Platform

Modular

Actively Developed

---

# Forbidden Technologies

Electron

Heavy Runtime Dependencies

Unmaintained Libraries

Closed Proprietary SDKs (unless optional)

---

End of TECH_STACK.md