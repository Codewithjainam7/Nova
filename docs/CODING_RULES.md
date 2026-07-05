# CODING RULES

Project: NOVA

Document Type: Engineering Coding Standards

Version: 1.0.0

Status: Final

Priority: Critical

Depends On:

PROJECT_CONSTITUTION.md

SYSTEM_ARCHITECTURE.md

TECH_STACK.md

---

# Purpose

This document defines mandatory coding standards for the entire NOVA project.

Every engineer, AI coding agent, and contributor must follow these rules.

These rules ensure consistency, maintainability, scalability, readability, and reliability.

---

# Core Principles

Readability over cleverness.

Modularity over monolithic code.

Composition over inheritance.

Explicit over implicit.

Simple over complex.

Consistency over personal preference.

---

# Folder Rules

Every module shall have its own folder.

One feature = One folder.

No unrelated files inside the same folder.

Shared code belongs only inside shared packages.

---

# File Rules

One responsibility per file.

One exported class/component when practical.

Meaningful filenames.

Avoid generic names.

Example

Good

DesktopAgent.ts

PlannerService.py

VoiceManager.ts

Bad

utils.py

helper.ts

temp.js

new.py

---

# Naming Rules

Classes

PascalCase

Functions

camelCase

Variables

camelCase

Constants

UPPER_SNAKE_CASE

Folders

kebab-case

Interfaces

PascalCase

Enums

PascalCase

Private Variables

_prefix

---

# Component Rules

Components must:

Be reusable.

Be isolated.

Contain minimal logic.

Receive typed props.

Avoid side effects.

---

# Function Rules

Maximum length

100 lines

Preferred

<50 lines

One responsibility only.

Return early.

Avoid deep nesting.

Maximum nesting

3

---

# Comment Rules

Write comments explaining "why".

Never explain obvious code.

Good

// Retry because browser navigation is unstable.

Bad

// Increment i

---

# TypeScript Rules

Strict Mode

Enabled

No "any"

Prefer interfaces

Typed APIs

Typed state

Typed events

---

# Python Rules

Type hints required.

Pydantic for validation.

Use dataclasses where appropriate.

No global mutable state.

---

# Error Handling

Never ignore exceptions.

Never swallow errors.

Return meaningful errors.

Log failures.

Support retries.

---

# Logging

Every important action shall log:

Timestamp

Module

Function

Status

Execution Time

Errors

Warnings

---

# Async Rules

Never block UI.

Use async/await.

Avoid callback chains.

Support cancellation.

---

# State Management

Single source of truth.

No duplicate state.

Predictable updates.

Immutable updates.

---

# API Rules

Validate input.

Validate output.

Use schemas.

Return structured responses.

Never expose stack traces.

---

# Security Rules

Validate all inputs.

Sanitize outputs.

Never hardcode secrets.

Use environment variables.

Encrypt sensitive data.

Least privilege principle.

---

# Performance Rules

Lazy load when possible.

Avoid unnecessary renders.

Cache expensive operations.

Release resources promptly.

Optimize startup time.

---

# Memory Rules

Avoid memory leaks.

Dispose listeners.

Close file handles.

Release browser instances.

Clear timers.

---

# Testing Rules

Every critical module requires:

Unit Tests

Integration Tests

Error Tests

Verification Tests

---

# Git Rules

Small commits.

Meaningful commit messages.

One feature per commit.

No direct commits to main.

---

# Documentation Rules

Every module requires:

README

API Documentation

Architecture Notes

Usage Examples

---

# AI Coding Rules

AI must:

Read brain.md first.

Read PROJECT_CONSTITUTION.md.

Read SYSTEM_ARCHITECTURE.md.

Never invent APIs.

Never invent folders.

Never remove existing functionality.

Never rewrite unrelated code.

Never change architecture without approval.

---

# Code Review Checklist

✓ Builds Successfully

✓ Lint Passes

✓ Tests Pass

✓ No Dead Code

✓ No Duplicate Logic

✓ Typed

✓ Documented

✓ Logged

✓ Verified

✓ Modular

---

# Definition of Done

Code is complete only when:

Requirements satisfied.

Tests passed.

Documentation updated.

Verification successful.

Architecture respected.

Code reviewed.

No known regressions.

---

End of CODING_RULES.md