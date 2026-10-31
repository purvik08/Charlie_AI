# Phase 5 — Intelligence Layer Implementation Prompt

You are working on an existing project called **Charlie — Offline AI Assistant**.

Your task is to implement **Phase 5: Intelligence Layer** on top of the existing architecture.

## 1. IMPORTANT: DO NOT REWRITE THE PROJECT

First inspect the entire existing repository and understand the current implementation.

Do NOT:
- Rewrite the application from scratch
- Replace the existing GUI
- Replace the CLI
- Remove the FeatureRegistry
- Remove the EventBus
- Replace working features unnecessarily
- Introduce cloud APIs
- Introduce internet-dependent AI services
- Break existing commands
- Duplicate existing functionality

Preserve the existing architecture and extend it.

The current project already contains:

- `main.py`
- `assistant.py`
- `model.py`
- `config.py`
- `intent.py`
- `memory.py`
- `core/`
  - `events.py`
  - `registry.py`
  - `base.py`
- `features/`
  - `system_info/`
  - `notes/`
  - `todos/`
  - `reminders/`
  - `file_search/`
  - `tts/`
- `cli/`
- `ui/`
- Local configuration
- Local persistence
- Local LLM inference using GGUF / llama-cpp-python

Use the existing architecture as the foundation.

---

# 2. PHASE 5 OBJECTIVE

Transform Charlie from:

```text
User
 ↓
Basic intent/command detection
 ↓
Feature OR LLM
 ↓
Response
```

into:

```text
User
 ↓
Input Normalization
 ↓
Intent + Context Analysis
 ↓
Memory Retrieval
 ↓
Tool Selection
 ↓
Permission / Validation
 ↓
Tool Execution OR LLM
 ↓
Result Integration
 ↓
Response Generation
 ↓
Memory Update
 ↓
GUI / CLI / TTS
```

The goal is to make Charlie significantly more intelligent while remaining:

- Offline-first
- Privacy-first
- Lightweight
- Deterministic where possible
- LLM-assisted where useful
- Modular
- Testable
- Safe

---

# 3. CORE DESIGN PRINCIPLE

The LLM must NOT directly control the operating system.

Never allow the model to execute arbitrary Python, shell commands, subprocesses, or filesystem operations directly.

Instead:

```text
LLM
 ↓
Structured Tool Request
 ↓
Tool Registry
 ↓
Validation
 ↓
Permission Check
 ↓
Tool Execution
 ↓
Structured Result
 ↓
LLM
```

The LLM should request capabilities through registered tools.

---

# 4. INTELLIGENT ROUTING

Improve the existing `intent.py`.

Create a robust routing pipeline that can distinguish between:

### Deterministic requests

Examples:

```text
What time is it?
What's today's date?
Show my todos.
Show system information.
Create a note.
Set a reminder.
Search my files.
Open VS Code.
```

These should use deterministic application features.

### Conversational requests

Examples:

```text
Hello
How are you?
Explain recursion.
What is machine learning?
Help me understand this code.
```

These should go to the local LLM.

### Tool-based natural language requests

Examples:

```text
Remind me in 20 minutes to call John.

Create a note called project ideas and write down:
Build an offline AI assistant.

What tasks do I have left today?

Find my Python files.

Open my Downloads folder.
```

These should be converted into structured tool calls.

---

# 5. CREATE A TOOL SYSTEM

Do not hard-code every possible command inside `assistant.py`.

Introduce a reusable tool abstraction compatible with the existing FeatureRegistry.

For example:

```python
class Tool:
    name: str
    description: str
    parameters: dict

    def execute(self, **kwargs):
        ...
```

Use the existing architecture where possible rather than creating a competing registry.

The system should be able to discover registered tools dynamically.

Example tools:

```text
get_time
get_date
get_system_info
get_battery
search_files
open_path
create_note
search_notes
list_todos
add_todo
complete_todo
delete_todo
create_reminder
list_reminders
```

Existing feature implementations should be reused.

---

# 6. STRUCTURED TOOL CALLS

Create a structured internal representation.

Example:

```json
{
  "tool": "create_reminder",
  "arguments": {
    "text": "Call John",
    "delay_minutes": 20
  }
}
```

Another example:

```json
{
  "tool": "search_files",
  "arguments": {
    "query": "python",
    "path": "~/Projects"
  }
}
```

Do not rely exclusively on fragile natural-language string matching.

The implementation can use:
- deterministic parsing
- regex/date parsing
- local LLM structured output
- a hybrid approach

Prefer deterministic parsing when the request is simple.

---

# 7. HYBRID INTENT DETECTION

Implement a hybrid strategy.

### Layer 1 — Fast deterministic detection

Use patterns/rules for obvious commands.

Examples:

```text
"time"
"what time"
"today's date"
"show todos"
"system information"
```

### Layer 2 — Existing intent detector

Use the existing `intent.py`.

### Layer 3 — Local LLM classification

Only invoke the LLM when deterministic routing is uncertain.

The classifier should return structured data such as:

```json
{
  "type": "tool",
  "tool": "create_reminder",
  "confidence": 0.94
}
```

or:

```json
{
  "type": "conversation",
  "confidence": 0.91
}
```

Do not use the LLM for every trivial operation.

---

# 8. CONFIDENCE-BASED ROUTING

Introduce confidence handling.

Example:

```text
confidence >= 0.85
    → execute route

0.60 - 0.84
    → additional validation / clarification

< 0.60
    → conversational LLM response or clarification
```

Do not blindly execute ambiguous operations.

For destructive or sensitive actions, require stronger validation regardless of confidence.

---

# 9. MULTI-STEP REQUESTS

Support requests containing multiple operations.

Example:

```text
Create a todo to finish my project and remind me tomorrow at 10 AM.
```

The system should be able to produce:

```text
1. add_todo(...)
2. create_reminder(...)
```

The architecture should support:

```text
User Request
 ↓
Plan
 ↓
Tool 1
 ↓
Tool 2
 ↓
Results
 ↓
Final Response
```

Do not implement unrestricted autonomous agents yet.

Keep the planner bounded and deterministic.

---

# 10. CONTEXT AWARENESS

Improve conversation handling.

Example:

```text
User:
Create a todo to finish the Atlas documentation.

Charlie:
Added the todo.

User:
Make it high priority.

Charlie:
Updated the Atlas documentation todo to high priority.
```

The second request should use recent conversation context.

Another example:

```text
User:
Create a note about my Raspberry Pi project.

Charlie:
Done.

User:
Add the MQTT architecture to it.
```

Charlie should understand what "it" refers to.

Implement a lightweight context window.

Do not load the entire conversation history into every LLM request.

---

# 11. MEMORY RETRIEVAL

Improve `memory.py`.

Separate memory into:

### Short-term memory

Recent conversation turns.

### Persistent conversation history

Existing SQLite history.

### Relevant context

Information retrieved for the current request.

The pipeline should become:

```text
Current Request
 ↓
Retrieve relevant context
 ↓
Build compact prompt
 ↓
Local LLM
```

Do not blindly inject hundreds of previous messages.

---

# 12. MEMORY SCORING

Introduce a simple relevance mechanism.

Possible signals:

```text
recency
keyword overlap
conversation relevance
importance
```

A memory score could conceptually be:

```text
score =
    recency_weight
  + relevance_weight
  + importance_weight
```

Keep the first implementation lightweight.

Do NOT add a vector database in Phase 5.

Vector/RAG functionality belongs to the later document-intelligence phase.

---

# 13. MEMORY CONTROL

Add explicit memory operations.

The user should eventually be able to say:

```text
Remember that my project is called Charlie.

What do you remember about my project?

Forget that.

Clear conversation memory.

Show my stored memories.
```

Add appropriate commands/API methods without exposing raw database internals.

The user must remain in control.

---

# 14. CONTEXT COMPRESSION

If conversation history becomes large, summarize older context.

Example:

```text
Recent messages
+
Older conversation summary
+
Relevant memories
```

Instead of:

```text
Entire conversation
```

This is particularly important for small local models with limited context windows.

---

# 15. LLM PROMPT ARCHITECTURE

Separate prompts into logical roles.

For example:

```text
System Prompt
Tool Instructions
Relevant Memory
Recent Conversation
Current User Request
```

Do not construct giant prompts inside random feature functions.

Create a centralized prompt/context builder.

Possible structure:

```text
core/
    intelligence/
        router.py
        planner.py
        context.py
        tool_call.py
        prompt_builder.py
```

Adapt this to the existing project structure rather than blindly creating these exact files.

---

# 16. RESPONSE GENERATION

After a tool executes, do not always return raw tool output.

Example:

Tool:

```text
todo list → 4 tasks
```

The LLM can convert this into:

```text
You have 4 active tasks:
1. Finish Atlas documentation
2. Test the assistant
3. Prepare the presentation
4. Review the README
```

However, for simple deterministic requests, skip the LLM.

Example:

```text
What time is it?

→ 9:32 PM
```

No LLM required.

---

# 17. TOOL RESULT FORMAT

Standardize tool responses.

Example:

```python
ToolResult(
    success=True,
    data={...},
    message="Reminder created successfully",
    error=None
)
```

Failures should look like:

```python
ToolResult(
    success=False,
    data=None,
    message=None,
    error="Reminder time is invalid"
)
```

This should integrate with the existing `CommandResult`/feature abstractions where possible.

Do not create redundant result systems unless necessary.

---

# 18. SAFETY LAYER

Create a centralized validation mechanism.

Classify tools:

### SAFE

```text
get_time
get_date
get_system_info
get_battery
list_todos
search_notes
```

### MODERATE

```text
create_note
add_todo
create_reminder
open_path
```

### SENSITIVE

Future examples:

```text
delete_file
modify_file
execute_command
system_configuration
```

Phase 5 should establish the infrastructure for this classification.

Do not implement unrestricted shell execution.

---

# 19. CONFIRMATION SYSTEM

Create a reusable confirmation mechanism for operations that may cause side effects.

Example:

```text
User:
Delete all files in Downloads.

Charlie:
This will delete 124 files.
Do you want to continue?

[Cancel] [Confirm]
```

For Phase 5, implement the framework even if destructive tools are not yet available.

---

# 20. MODEL ABSTRACTION

Preserve the current local GGUF/llama-cpp architecture.

The intelligence layer should communicate through the existing model abstraction.

Do not make the intelligence system depend directly on llama-cpp-python internals.

Prefer:

```text
Intelligence Layer
       ↓
ModelManager / LLM interface
       ↓
llama-cpp-python
       ↓
GGUF
```

This keeps model backends replaceable.

---

# 21. PERFORMANCE REQUIREMENTS

Charlie is designed for low-resource systems.

Therefore:

### Do not invoke the LLM for:

```text
time
date
battery
system information
simple todo operations
simple note operations
```

unless necessary.

Target:

```text
Deterministic operations:
< 2 seconds

LLM operations:
as fast as the local model allows
```

Avoid unnecessary model reloads.

Avoid loading the model multiple times.

Reuse existing model instances.

---

# 22. OFFLINE REQUIREMENT

Phase 5 must work completely offline.

Do not introduce:

- OpenAI APIs
- Gemini APIs
- Claude APIs
- cloud embeddings
- cloud vector databases
- telemetry
- external inference servers

The core intelligence pipeline must operate using local components.

---

# 23. GUI INTEGRATION

Integrate the intelligence layer into the existing GUI without redesigning it.

The UI should show states such as:

```text
Ready
Thinking...
Using tool...
Processing...
Completed
Error
```

For multi-step operations:

```text
Planning...
→ Creating todo
→ Creating reminder
→ Done
```

Do not block the Tkinter main thread.

Continue using background execution/threading already present in the project.

---

# 24. CLI INTEGRATION

The same intelligence engine must work from CLI.

Example:

```bash
charlie chat
```

Then:

```text
You:
Remind me in 20 minutes to check the server.

Charlie:
Reminder created for 20 minutes from now.
```

GUI and CLI must use the same assistant/intelligence core.

Do not implement separate AI logic for CLI and GUI.

---

# 25. CONFIGURATION

Extend the existing configuration system.

Possible settings:

```json
{
  "intelligence": {
    "enabled": true,
    "use_llm_classifier": true,
    "confidence_threshold": 0.85,
    "max_context_messages": 10,
    "max_memories": 5,
    "enable_memory": true,
    "require_confirmation_for_sensitive_tools": true
  }
}
```

Respect the project's existing configuration precedence.

Do not break existing configuration.

---

# 26. TESTING

Create comprehensive tests for the intelligence layer.

At minimum:

### Intent tests

```text
"What time is it?"
"What is today's date?"
"Show my todos"
"Create a reminder"
"Explain recursion"
```

### Tool tests

Every registered tool should have success/failure tests.

### Context tests

Test:

```text
Create a todo.
Make it high priority.
```

### Memory tests

Test:

```text
Store memory.
Retrieve memory.
Forget memory.
```

### Routing tests

Ensure trivial commands don't unnecessarily invoke the LLM.

### Safety tests

Ensure unknown tool names cannot execute anything.

### Malformed LLM output

Test invalid JSON / missing fields / unknown tools.

The application must fail safely.

---

# 27. OBSERVABILITY

Add structured local logging for:

```text
request
intent
confidence
selected tool
tool arguments
tool result
LLM latency
tool latency
errors
```

BUT:

Do not log sensitive user content unnecessarily.

Never log passwords, secrets or arbitrary private file contents.

---

# 28. BACKWARD COMPATIBILITY

After implementation, all existing functionality must still work:

```text
charlie --help
charlie time now
charlie date today
charlie system info
charlie system battery
charlie file find ...
charlie note create ...
charlie note list
charlie todo add ...
charlie todo list
charlie remind add ...
charlie remind list
charlie app open ...
charlie chat
```

Existing GUI quick actions must also continue working.

---

# 29. DOCUMENTATION UPDATE

After implementation, update documentation to reflect the actual architecture.

Especially resolve the current documentation inconsistency between the older Ollama architecture and the newer llama-cpp-python/GGUF architecture.

The canonical architecture should reflect the actual implementation.

Update:

```text
README.md
AGENTS.md
architecture.md
PROJECT_SUMMARY.md
phases.md
memory.md
```

Do not invent features that were not implemented.

Clearly mark Phase 5 as:

```text
Phase 5 — Intelligence Layer
Status: Completed
```

only after tests pass.

---

# 30. IMPLEMENTATION ORDER

Do not implement everything simultaneously.

Work in these milestones:

## Milestone 1

Inspect the repository and produce an implementation plan.

Do not modify code yet.

Identify:

- Existing intent implementation
- Existing memory implementation
- Existing FeatureRegistry
- Existing EventBus
- Existing model abstraction
- Existing CommandResult
- Existing GUI threading
- Existing CLI routing
- Existing tests

## Milestone 2

Implement the unified Tool abstraction/registry using existing architecture.

## Milestone 3

Implement hybrid intent routing.

## Milestone 4

Implement structured tool calls.

## Milestone 5

Implement context management.

## Milestone 6

Implement improved memory retrieval.

## Milestone 7

Implement tool validation and safety.

## Milestone 8

Integrate with GUI and CLI.

## Milestone 9

Add tests.

## Milestone 10

Run the entire test suite and fix regressions.

## Milestone 11

Update documentation.

---

# 31. DEFINITION OF DONE

Phase 5 is complete only when Charlie can correctly handle conversations like:

### Example 1

```text
User:
What time is it?

Charlie:
[direct deterministic response]
```

### Example 2

```text
User:
Create a todo to finish my project.

Charlie:
Todo created.
```

### Example 3

```text
User:
Make it high priority.

Charlie:
Updated the todo to high priority.
```

### Example 4

```text
User:
Remind me in 30 minutes to check the build.

Charlie:
Reminder created for 30 minutes from now.
```

### Example 5

```text
User:
Explain what an API is.

Charlie:
[local LLM response]
```

### Example 6

```text
User:
Create a todo to test Charlie and remind me tomorrow at 10 AM.

Charlie:
Created the todo and scheduled the reminder.
```

### Example 7

```text
User:
Remember that Charlie is my offline AI assistant project.

Charlie:
I'll remember that.
```

Later:

```text
User:
What is Charlie?

Charlie:
Charlie is your offline AI assistant project.
```

---

# 32. FINAL ENGINEERING RULE

Prioritize:

```text
Reliability
   >
Correctness
   >
Safety
   >
Performance
   >
Intelligence
   >
Feature count
```

Do not make Charlie appear intelligent by adding unnecessary LLM calls.

Make it intelligent by combining:

```text
Deterministic Tools
+
Intent Detection
+
Context
+
Memory
+
Local LLM
+
Safe Tool Execution
```

The final architecture should resemble:

```text
                         CHARLIE
                            │
              ┌─────────────▼─────────────┐
              │     Interaction Layer     │
              │       GUI / CLI / TTS     │
              └─────────────┬─────────────┘
                            │
              ┌─────────────▼─────────────┐
              │    Intelligence Layer     │
              │                            │
              │ Intent → Context → Plan   │
              └───────┬───────────┬────────┘
                      │           │
              ┌───────▼───┐   ┌──▼────────┐
              │   Memory  │   │ Tool      │
              │   System  │   │ Registry  │
              └───────┬───┘   └──┬────────┘
                      │           │
                      │      ┌────▼─────┐
                      │      │ Security │
                      │      │Validation│
                      │      └────┬─────┘
                      │           │
                      │      ┌────▼─────┐
                      │      │ Features │
                      │      └────┬─────┘
                      │           │
                      └─────┬─────┘
                            │
                    ┌───────▼────────┐
                    │ Local LLM      │
                    │ llama.cpp/GGUF │
                    └────────────────┘
```

**Start by inspecting the repository. Do not immediately write code. First identify what already exists, what can be reused, and exactly where Phase 5 should integrate with the current architecture. Then implement milestone-by-milestone and run tests after each major change.**