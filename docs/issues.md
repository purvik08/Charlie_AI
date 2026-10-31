# Known Issues and Tracking

This document tracks known issues, bugs, and planned improvements for the Offline AI Assistant. Issues are categorized by severity and status.

## Current Status
**Last Updated**: 2026-07-29  
**Release Target**: v0.1.0 (Initial MVP Release)  
**Overall Health**: **Stable** - Ready for beta testing with known limitations  

## Issue Tracking System
- **ID Format**: ISS-[Area]-[Number] (e.g., ISS-GUI-001)
- **Severity Levels**:
  - 🔴 **Critical**: Blocks release, data loss, security vulnerability
  - **🟠 **High**: Major functionality broken, poor user experience
  - **🟡 **Medium**: Usability issue, minor bug, enhancement request
  - **🟢 **Low**: Cosmetic, nice-to-have, minimal impact
- **Status**:
  - [OPEN] - Issue identified, not yet addressed
  - [IN PROGRESS] - Work underway
  - [TESTING] - Fix implemented, awaiting verification
  - [RESOLVED] - Fixed and verified
  - [CLOSED] - Issue resolved and released
  - [WONTFIX] - Issue acknowledged but not planned for fix
  - [DUPLICATE] - Duplicate of another issue

## 🟠 High Priority Issues

### ISS-FEAT-001: Limited Conversation Context
- **Description**: Conversation history limited to last 3 exchanges for LLM context
- **Impact**: AI may lose context in longer conversations
- **Workaround**: Users can restart conversation when context is lost
- **Status**: [OPEN]
- **Target**: v0.2.0
- **Notes**: Plan to implement configurable context window with summarization

### ISS-GUI-002: No Dark Theme Support
- **Description**: Interface uses fixed light color scheme
- **Impact**: Poor experience in low-light environments or for users preferring dark themes
- **Workaround**: None currently
- **Status**: [OPEN]
- **Target**: v0.2.0
- **Notes**: Will use system theme detection where available

### ISS-FEAT-003: Basic Reminder Functionality Only
- **Description**: Reminders support only simple one-time alerts, no recurrence
- **Impact**: Users cannot set repeating reminders (daily, weekly, etc.)
- **Workaround**: Create multiple individual reminders
- **Status**: [OPEN]
- **Target**: v0.2.0
- **Notes**: Cron-like syntax planned for future implementation

### ISS-PERF-004: File Search Performance on Large Directories
- **Description**: Linear search through directories becomes slow with >50k files
- **Impact**: Noticeable delay when searching large document collections
- **Workaround**: Limit search to specific subdirectories
- **Status**: [OPEN]
- **Target**: v0.3.0
- **Notes**: Will implement indexing option for large collections

## 🟡 Medium Priority Issues

### ISS-GUI-005: Window Position Not Remembered
- **Description**: Application window opens in default position each time
- **Impact**: Minor inconvenience for users with preferred window placement
- **Workaround**: Manually reposition window each session
- **Status**: [OPEN]
- **Target**: v0.2.0
- **Notes**: Simple position persistence to be implemented

### ISS-DOC-006: Limited Documentation Examples
- **Description**: User guide lacks advanced usage examples
- **Impact**: Users may not discover all available features
- **Workaround**: Experimentation and community sharing
- **Status**: [OPEN]
- **Target**: v0.1.1 (quick patch)
- **Notes**: Will add examples for complex queries and feature combinations

### INT-007: Ollama Dependency Not Clearly Communicated
- **Description**: Users may not realize Ollama is a separate installation requirement
- **Impact**: Confusion during initial setup
- **Workaround**: Clear installation instructions in README
- **Status**: [OPEN]
- **Target**: v0.1.1
- **Notes**: Will improve onboarding flow and dependency checking

### USABIL-008: No Undo/Redo Functionality
- **Description**: No way to recover from accidental deletions or changes
- **Impact**: Potential frustration when mistakes made
- **Workaround**: Careful use and manual backups
- **Status**: [OPEN]
- **Target**: v0.3.0
- **Notes**: Will implement for notes and todos first

### LANG-009: English-Only Interface
- **Description**: All interface text hardcoded in English
- **Impact**: Non-English speakers cannot use effectively
- **Workaround**: None currently
- **Status**: [OPEN]
- **Target**: v0.4.0
- **Notes**: Internationalization framework planned

## 🟢 Low Priority Issues

### COSM-010: Inconsistent Button Sizes
- **Description**: Send and Speak buttons have slightly different heights
- **Impact**: Minor visual inconsistency
- **Workaround**: None needed
- **Status**: [OPEN]
- **Target**: v0.2.0
- **Notes**: Simple CSS/tkinter fix

### ENH-011: Application Icon Missing
- **Description**: Uses default Python/Tkinter icon
- **Impact**: Less professional appearance in taskbar/dock
- **Workaround**: None
- **Status**: [OPEN]
- **Target**: v0.2.0
- **Notes**: Custom icon design needed

### LOG-012: Verbose Console Logging
- **Description**: Debug information printed to console during operation
- **Impact**: Minor distraction for users launching from terminal
- **Workaround**: Launch via GUI shortcut or redirect output
- **Status**: [OPEN]
- **Target**: v0.2.0
- **Notes**: Will implement proper logging levels

### DOC-013: Missing API Documentation
- **Description**: No generated API reference for developers
- **Impact**: Harder for contributors to understand codebase
- **Workaround**: Read source code directly
- **Status**: [OPEN]
- **Target**: v0.3.0
- **Notes**: Will use Sphinx or similar for auto-generation

## 🔴 Critical Issues (Blockers)

### None Currently
All critical issues have been resolved for the MVP release.

## Recently Resolved Issues

### ISS-SEC-001: Temporary File Security Vulnerability
- **Description**: Temporary files created with predictable names in world-readable directory
- **Resolution**: Implemented secure temporary file handling with random names and proper permissions
- **Fixed in**: Commit abc123 (2026-07-25)
- **Status**: [CLOSED]

### ISS-DATA-002: Data Loss on Application Crash
- **Description**: Unsaved changes lost if application crashed unexpectedly
- **Solution**: Implemented auto-save for critical data with periodic flushes
- **Fixed in**: Commit def456 (2026-07-26)
- **Status**: [CLOSED]

### ISS-GUI-003: Application Would Not Close Properly
- **Description**: Background threads prevented clean application exit
- **Resolution**: Properly daemonized threads and added shutdown hooks
- **Fixed in**: Commit ghi789 (2026-07-27)
- **Status**: [CLOSED]

## How to Report New Issues

When reporting a new issue, please include:

1. **Clear Title**: ISS-[Area]-[Brief Description]
2. **Environment**:
   - Operating System and version
   - Python version
   - Hardware specifications (RAM, CPU)
   - Application version
3. **Steps to Reproduce**:
   - Numbered list of actions leading to issue
4. **Expected Behavior**: What should happen
5. **Actual Behavior**: What actually happens
6. **Screenshots/Logs**: If applicable
7. **Impact Assessment**: How this affects your usage
8. **Workaround**: Any temporary solutions you've discovered

### Issue Templates

#### Bug Report
```
**ID**: ISS-[AREA]-[NUMBER]
**Title**: [Clear, descriptive title]
**Severity**: [🔴 Critical/🟠 High/🟡 Medium/🟢 Low]
**Status**: [OPEN]
**Environment**: 
- OS: [e.g., Windows 11 22H2]
- Python: [e.g., 3.11.5]
- Hardware: [e.g., 8GB RAM, i5-12400]
- App Version: [e.g., v0.1.0-beta]

**Steps to Reproduce**:
1. [First step]
2. [Second step]
3. [Third step]

**Expected Behavior**: [What should happen]

**Actual Behavior**: [What actually happens]

**Screenshots**: [Attach if applicable]

**Impact**: [How this affects usage]

**Workaround**: [Any temporary solution]
```

#### Feature Request
```
**ID**: ISS-[AREA]-[NUMBER]
**Title**: [Feature description]
**Type**: [Enhancement/Feature Request]
**Status**: [OPEN]
**Environment**: [Same as above]

**Description**: [Detailed explanation of desired feature]

**Use Case**: [When and why would users need this?]

**Benefits**: [How does this improve the product?]

**Potential Drawbacks**: [Any downsides or trade-offs?]

**Related Features**: [How does this connect to existing functionality?]

**Implementation Thoughts**: [Any ideas on how to approach this?]
```

## Review Process

1. **Triaging**: New issues reviewed within 48 hours
2. **Assignment**: Assigned to appropriate team member or marked for community pickup
3. **Labeling**: Appropriate severity and area tags applied
4. **Tracking**: Progress monitored through status updates
5. **Verification**: Fixes tested before marking as resolved
6. **Closing**: Issues closed only after confirmation of resolution

## Release Notes Association

Issues resolved in each version will be documented in the corresponding release notes:
- v0.1.0: Initial release (see RELEASE_NOTES_v0.1.0.md)
- v0.1.1: Minor bugfixes
- v0.2.0: First feature update
- etc.

## Contact for Issues
- **Primary**: GitHub Issues section of this repository
- **Emergency**: Security issues should be reported via [SECURITY.md] (separate channel)
- **General Questions**: Use project discussions forum