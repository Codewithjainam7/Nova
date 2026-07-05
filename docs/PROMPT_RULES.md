# PROMPT RULES

Project: NOVA

Document Type: AI Prompt Engineering Rules

Version: 1.0.0

Status: Final

Priority: Critical

Depends On:

PROJECT_CONSTITUTION.md

SYSTEM_ARCHITECTURE.md

AGENT_RULES.md

---

# Purpose

This document defines how every AI prompt inside NOVA should be designed, executed, validated, and maintained.

Every AI interaction must follow these standards.

---

# Prompt Philosophy

The AI should:

Understand before answering.

Plan before executing.

Verify before responding.

Never guess.

Never hallucinate.

Never assume success.

---

# Prompt Lifecycle

Receive User Request

↓

Understand Intent

↓

Collect Context

↓

Retrieve Memory

↓

Select Prompt Template

↓

Inject Context

↓

Generate Plan

↓

Execute

↓

Verify

↓

Generate Response

↓

Store Relevant Memory

---

# Prompt Structure

Every prompt shall contain:

Role

Objective

Context

Memory

Constraints

Available Tools

Expected Output

Verification Rules

Failure Rules

---

# Role Definition

Every prompt must explicitly define the AI role.

Examples:

Planner

Memory Manager

Desktop Agent

Browser Agent

Vision Agent

Coding Agent

Search Agent

Email Agent

---

# Context Injection

The prompt shall include:

Current Conversation

Relevant Memory

User Preferences

Running Tasks

Current Screen

Open Applications

Recent History

Time

Operating System

Available Tools

---

# Memory Rules

Only relevant memories shall be injected.

Avoid unrelated information.

Limit context size.

Prioritize recent memories.

---

# Planning Rules

The AI shall:

Understand the request.

Break large tasks into smaller tasks.

Estimate dependencies.

Choose tools.

Verify completion.

---

# Tool Rules

The AI shall only use available tools.

Never invent tools.

Never assume tool capabilities.

Verify every tool result.

---

# Verification Rules

Every action shall be verified.

Examples:

Browser opened

↓

Verify tab exists.

File moved

↓

Verify destination.

Email sent

↓

Verify success.

---

# Retry Rules

Retry only recoverable failures.

Maximum retries configurable.

Never retry indefinitely.

Use alternative strategies.

---

# Clarification Rules

If user intent is ambiguous:

Ask clarifying questions.

Never guess critical information.

---

# Safety Rules

Always confirm before:

Deleting files

Formatting drives

Sending emails

Making purchases

Installing software

Changing system settings

Accessing sensitive information

---

# Response Rules

Responses shall be:

Accurate

Concise

Actionable

Honest

Structured

Never fabricate results.

Clearly communicate uncertainty.

---

# Output Format

Every agent response should include:

Status

Summary

Result

Verification

Errors (if any)

Suggested Next Steps

---

# Prompt Templates

Planner Prompt

Desktop Prompt

Browser Prompt

Memory Prompt

Vision Prompt

Search Prompt

Coding Prompt

Email Prompt

Plugin Prompt

System Prompt

---

# Context Window Rules

Prioritize:

Current Task

↓

Relevant Memory

↓

Recent Conversation

↓

User Preferences

↓

Long-term Context

Discard irrelevant context.

---

# Prompt Versioning

Every prompt must include:

Prompt ID

Version

Owner

Last Updated

Purpose

Dependencies

---

# Forbidden Behaviors

Do not hallucinate APIs.

Do not fabricate files.

Do not invent browser states.

Do not claim task completion without verification.

Do not ignore errors.

Do not bypass Planner.

Do not bypass Execution Engine.

---

# AI Quality Checklist

✓ Intent Understood

✓ Context Loaded

✓ Memory Retrieved

✓ Plan Generated

✓ Tools Selected

✓ Execution Verified

✓ Errors Handled

✓ Response Structured

✓ Memory Updated (if required)

---

# Future Prompt Categories

System Prompts

Agent Prompts

Tool Prompts

Developer Prompts

User Prompts

Plugin Prompts

Debug Prompts

Testing Prompts

Learning Prompts

---

# Definition of Prompt Success

A prompt is successful only when:

The user's intent is correctly understood.

The correct tools are selected.

The requested task is completed.

The result is verified.

The response is truthful.

The experience feels natural.

---

End of PROMPT_RULES.md