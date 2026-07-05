# AGENT RULES

Project: NOVA

Document Type: AI Agent Rules

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

This document defines the behavior, responsibilities, communication rules, lifecycle, and constraints for every AI agent inside NOVA.

Every agent must follow these rules.

No exceptions.

---

# Agent Philosophy

Each agent has one responsibility.

Agents never make product decisions.

Agents never bypass the Planner.

Agents never bypass the Execution Engine.

Agents never communicate directly.

Every action must be observable.

Every action must be verifiable.

---

# Agent Lifecycle

Receive Task

↓

Validate Input

↓

Load Context

↓

Execute

↓

Verify

↓

Generate Output

↓

Return Result

↓

Release Resources

---

# Agent Communication

Allowed

Planner

↓

Execution Engine

↓

Agent Manager

↓

Selected Agent

↓

Tool Registry

↓

Tool

↓

Verification

↓

Planner

---

Forbidden

Agent

↓

Agent

Direct communication

Forbidden

Agent

↓

Database

Without Planner

Forbidden

Agent

↓

UI

Direct updates

Forbidden

---

# Agent Responsibilities

Every Agent shall:

Perform one domain-specific task.

Return structured output.

Generate execution logs.

Handle recoverable failures.

Support cancellation.

Support timeouts.

Support verification.

---

# Standard Agent Input

Execution ID

Task ID

Agent ID

Task Description

Parameters

Planner Context

Memory Context

Permissions

Configuration

Timeout

Priority

---

# Standard Agent Output

Execution ID

Status

Success

Failure

Execution Time

Warnings

Errors

Logs

Verification Result

Output Data

Confidence Score

---

# Agent Status

Idle

Preparing

Waiting

Executing

Paused

Retrying

Verifying

Completed

Cancelled

Failed

Offline

---

# Execution Rules

Every Agent shall:

Validate input.

Validate permissions.

Execute task.

Verify results.

Return structured response.

Never return partial success as complete success.

---

# Logging Rules

Every execution must generate:

Timestamp

Agent Name

Task

Execution Time

Status

Verification

Errors

Warnings

Retry Count

---

# Retry Rules

Retry only recoverable failures.

Maximum retries configurable.

Never retry destructive actions automatically.

Never retry indefinitely.

---

# Timeout Rules

Every task shall have a timeout.

On timeout:

Stop safely.

Log event.

Notify Planner.

Release resources.

---

# Verification Rules

Every completed task must be verified.

Verification must occur before reporting success.

Failure to verify equals failure.

---

# Memory Rules

Agents may read memory.

Agents may not permanently write memory.

Only the Planner may approve long-term memory updates.

---

# Permission Rules

Agents shall never:

Delete user data without confirmation.

Send emails without confirmation.

Purchase items.

Transfer money.

Install software silently.

Modify system security.

Access protected resources without permission.

---

# Error Handling

Recover if possible.

Retry if appropriate.

Request user assistance if required.

Abort safely if recovery fails.

Never hide errors.

---

# Security Rules

Validate every input.

Sanitize parameters.

Protect credentials.

Never expose secrets.

Use least privilege.

---

# Performance Rules

Avoid blocking operations.

Release resources promptly.

Support concurrent execution.

Generate progress updates.

---

# Agent Registry

Planner Agent

Execution Agent

Desktop Agent

Browser Agent

Vision Agent

Voice Agent

Memory Agent

Search Agent

Email Agent

Calendar Agent

Notification Agent

Plugin Agent

Coding Agent

Future Agents

---

# Agent Development Rules

One folder per agent.

One responsibility per agent.

Independent testing.

Independent logging.

Independent documentation.

Replaceable implementation.

---

# Agent Quality Checklist

✓ Single Responsibility

✓ Structured Output

✓ Logging

✓ Verification

✓ Timeout Support

✓ Retry Support

✓ Cancellation Support

✓ Permission Validation

✓ Error Handling

✓ Unit Tests

---

# Future Rules

Future agents must implement this specification before integration.

No custom communication protocol is allowed.

Every agent must expose the standard interface.

---

End of AGENT_RULES.md