# Project Rules and Guidelines

This document outlines the core principles, limitations, and operational guidelines that govern the development, use, and evolution of the Offline AI Assistant.

## 1. Foundational Principles

### 1.1 Privacy First Principle
**Rule**: No user data shall ever be transmitted outside the user's device without explicit, informed consent for a specific, temporary purpose.

**Implications**:
- All processing occurs locally
- No telemetry, analytics, or usage tracking
- No automatic updates that transmit data
- Clear opt-in for any optional online features
- Data remains under user's exclusive control

### 1.2 Offline-First Principle
**Rule**: Core functionality must work without any internet connection.

**Implications**:
- Essential features (time, notes, todos, etc.) functional offline
- LLM requires local Ollama installation but no external calls
- Graceful degradation when online services unavailable
- Explicit labeling of features requiring internet
- No requirement for account creation or login

### 1.3 User Sovereignty Principle
**Rule**: The user has complete control over their data, configuration, and the software's behavior.

**Implications**:
- Easy export/delete of all personal data
- Transparent data
- Configurable data retention policies
- Ability to disable any feature
- Clear documentation of data storage locations
- No dark patterns or manipulative design

### 1.4 Minimalism Principle
**Rule**: Implement only what is necessary to solve the user's problem effectively.

**Implications**:
- Avoid feature bloat
- Prioritize usefulness over novelty
- Remove unused code and dependencies
- Simple, intuitive interface
- Clear progression from novice to expert use

### 1.5 Transparency Principle
**Rule**: Users must be able to understand what the software is doing and why.

**Implications**:
- Clear status indicators (processing, ready, error)
- Explainable limitations and capabilities
- Visible data flow (where information goes)
- Accessible source code and documentation
- Honest representation of abilities (no overpromising)

## 2. Operational Rules

### 2.1 Data Handling Rules
- **R2.1.1**: All user data stored in `~/offline_assistant_data/` by default
- **R2.1.2**: Data files use standard formats (JSON, SQLite, plain text)
- **R2.1.3**: Automatic backups not performed (user responsibility)
- **R2.1.4**: Data deletion is permanent and irreversible
- **R2.1.5**: No hidden data collections or metadata tracking
- **R2.1.6**: Temporary files securely deleted after use
- **R2.1.7**: Export functionality provides complete data portability

### 2.2 Software Behavior Rules
- **R2.2.1**: Application starts in under 5 seconds on modern hardware
- **R2.2.2**: Responds to user input within 2 seconds for non-LLM tasks
- **R2.2.3**: Provides clear feedback during processing states
- **R2.2.4**: Gracefully handles missing dependencies (e.g., Ollama)
- **R2.2.5**: Never crashes silently; always provides error information
- **R2.2.6**: Respects system conventions (themes, accessibility settings)
- **R2.2.7**: Uses minimal system resources when idle
- **R2.2.8**: Supports keyboard navigation and shortcuts
- **R2.2.9**: Compatible with screen readers and assistive technologies
- **R2.2.10**: Allows user to configure data storage location

### 2.3 Development Rules
- **R2.3.1**: All code must be readable and maintainable
- **R2.3.2**: Functions should do one thing well (Single Responsibility)
- **R2.3.3**: Write tests for critical functionality
- **R2.3.4**: Document public APIs and complex algorithms
- **R2.3.5**: Follow PEP 8 style guidelines with reasonable exceptions
- **R2.3.6**: Use type hints for all public functions
- **R2.3.7**: Handle exceptions at appropriate abstraction levels
- **R2.3.8**: Avoid global state where possible
- **R2.3.9**: Prefer composition over inheritance
- **R2.3.10**: Keep dependencies minimal and justified
- **R2.3.11**: All user-facing strings externalized for localization
- **R2.3.12**: Secure handling of any future API keys or tokens

### 2.4 User Interface Rules
- **R2.4.1**: Consistent visual language across all screens
- **R2.4.2**: Clear visual hierarchy guiding user attention
- **R2.4.3**: Accessible color contrast (WCAG AA minimum)
- **R2.4.4**: Responsive layout adapting to different window sizes
- **R2.4.5**: Meaningful icons with text labels
- **R2.4.6**: Keyboard shortcuts discoverable via tooltips
- **R2.4.7**: Undo/redo functionality where applicable
- **R2.4.8**: Confirmation dialogs for destructive actions
- **R2.4.9**: Persistent window state (size, position) between sessions
- **R2.4.10**: Platform-native appearance where appropriate

### 2.5 Communication Rules
- **R2.5.1**: Error messages actionable and user-friendly
- **R2.5.2**: Success messages brief and unobtrusive
- **R2.5.3**: Loading indicators for operations >500ms
- **R2.5.4**: Progress indication for long operations
- **R2.5.5**: No misleading or fake "loading" animations
- **R2.5.6**: Honest representation of capabilities (no AI overclaim)
- **R2.5.7**: Clear indication when offline vs online features
- **R2.5.8**: Respectful, helpful tone in all communications
- **R2.5.9**: Multi-language support planned for future releases
- **R2.5.10**: Comprehensive, searchable documentation

## 3. Limitations and Constraints

### 3.1 Technical Limitations
- **L3.1.1**: LLM quality constrained by local hardware capabilities
- **L3.1.2**: Model size limited by available RAM/storage (typically 2-4GB per model)
- **L3.1.3**: No real-time internet information without explicit user configuration
- **L3.1.4**: Voice input functionality not included in this release (by design)
- **L3.1.5**: Performance varies significantly with hardware specifications
- **L3.1.6**: Initial model download may be large (2-4GB+)
- **L3.1.7**: Not suitable for high-frequency trading or real-time control systems
- **L3.1.8**: Limited to text-based interaction (no image/video processing native)

### 3.2 Scope Limitations
- **L3.2.1**: Not a general-purpose operating system assistant
- **L3.2.2**: Does not replace specialized professional software
- **L3.2.3**: Limited integration with third-party services (by design privacy choice)
- **L3.2.4**: No social media or messaging platform integration
- **L3.2.5**: Not designed for enterprise-scale deployment without modification
- **L3.2.6**: No built-in cloud synchronization (intentional limitation)
- **L3.2.7**: Limited natural language understanding compared to large cloud models
- **L3.2.8**: Cannot learn from user interactions beyond current session (by privacy design)

### 3.3 Legal and Compliance Constraints
- **L3.3.1**: Users must comply with Ollama's license terms
- **L3.3.2**: Users responsible for ensuring their use of language models complies with applicable laws
- **L3.3.3**: No warranty or liability for advice given by the AI
- **L3.3.4**: Not suitable for medical, legal, or financial decision-making without professional consultation
- **L3.3.5**: Users must not use for illegal activities or harmful content generation
- **L3.3.6**: Compliance with export controls for strong encryption (if added in future)
- **L3.3.7**: Adherence to child protection laws (COPPA, GDPR-K) - not intended for children under 13

### 3.4 Environmental Constraints
- **L3.4.1**: Requires electricity and functioning hardware
- **L3.4.2**: Performance degraded in extreme temperatures
- **L3.4.3**: Not suitable for use in explosive atmospheres (standard computer limitation)
- **L3.4.4**: Requires periodic maintenance (updates, disk space management)
- **L3.4.5**: Physical security of device remains user responsibility

## 4. Waivers and Exceptions

### 4.1 Approved Exceptions
- **E4.1.1**: Anonymous usage statistics may be collected ONLY if:
  - Explicitly opted-in by user via clear consent dialog
  - Absolutely no personal or identifiable information included
  - Stored separately from any user data
  - Easily disabled at any time
  - Used solely for improving the product
- **E4.1.2**: Crash reporting may be implemented ONLY if:
  - No personal data included in reports
  - User consent obtained before transmission
  - Option to review report before sending
  - Local storage option always available
- **E4.1.3**: Optional online features may be added ONLY if:
  - Clearly labeled as "Online Feature"
  - Default to OFF state
  - No functionality loss when disabled
  - Separate privacy policy for online components
  - User data never leaves device without explicit per-use consent

### 4.2 Prohibited Practices (Never Allowed)
- **P4.2.1**: Secret data collection of any kind
- **P4.2.2**: Selling or sharing user data with third parties
- **P4.2.3**: Using dark patterns to manipulate user behavior
- **P4.2.4**: Forcing updates without user consent
- **P4.2.5**: Creating vendor lock-in through proprietary data formats
- **P4.2.6**: Misrepresenting capabilities (e.g., claiming "AI" when it's just regex)
- **P4.2.7**: Storing passwords or sensitive credentials in plain text
- **P4.2.8**: Bypassing operating system security features
- **P4.2.9**: Installing additional software without explicit user permission
- **P4.2.10**: Modifying system files outside application directory

## 5. Enforcement and Compliance

### 5.1 Development Process
- **D5.1.1**: All pull requests checked for compliance with these rules
- **D5.1.2**: Architecture review for new features
- **D5.1.3**: Privacy impact assessment for data-handling changes
- **D5.1.4**: Regular dependency vulnerability scanning
- **D5.1.5**: Code ownership and accountability clearly defined
- **D5.1.6**: Continuous integration checks for rule violations
- **D5.1.7**: Architecture decision records for significant changes

### 5.2 Release Process
- **D5.2.1**: Release notes must mention any changes to data handling
- **D5.2.2**: Updated documentation reflecting current behavior
- **D5.2.3**: Backward compatibility maintained unless critical security issue
- **D5.2.4**: Deprecation warnings for features planned removal
- **D5.2.5**: Clear upgrade path for user data and settings
- **D5.2.6**: Release candidate testing with privacy-focused test cases

### 5.3 Community Governance
- **D5.3.1**: Community contributions subject to same rules
- **D5.3.2**: Maintainers have authority to reject non-compliant contributions
- **D5.3.3**: Transparent process for appealing decisions
- **D5.3.4**: Public changelog of rule modifications
- **D5.3.5**: Regular community review of these guidelines
- **D5.3.6**: Whistleblower protection for reporting violations

## 6. Review and Evolution

### 6.1 Regular Review
- **R6.1.1**: These rules reviewed quarterly by core maintainers
- **R6.1.2**: Updates proposed via standard contribution process
- **R6.1.3**: Community feedback solicited annually
- **R6.1.4**: Versioned with semantic versioning (major changes = breaking changes)
- **R6.1.5**: Effective date clearly marked on document

### 6.2 Amendment Process
- **R6.2.1**: Changes proposed as issues in repository
- **R6.2.2**: Discussion period minimum 14 days
- **R6.2.3**: Supermajority (2/3) approval required for changes
- **R6.2.4**: Emergency security exceptions possible with 24-hour notice
- **R6.2.5**: All changes documented with rationale
- **R6.2.6**: Previous versions archived for reference

### 6.3 Compliance Verification
- **V6.3.1**: Automated checks for obvious violations in CI
- **V6.3.2**: Manual review for complex compliance questions
- **V6.3.3**: External audit available upon request for major versions
- **V6.3.4**: Public transparency report published annually
- **V6.3.5**: Bug bounty program for security and privacy issues
- **V6.3.6**: Clear process for users to report suspected violations

## 7. Related Documents

- **PRD** (`docs/prd.md`): Feature specifications and requirements
- **Architecture** (`docs/architecture.md`): Technical design and component relationships
- **Memory** (`docs/memory.md`): Current project status and progress tracking
- **Issues** (`docs/issues.md`): Known problems and tracking
- **Phases** (`docs/phases.md`): Release planning and roadmap

## 8. Acceptance Criteria

A feature or change is considered compliant with these rules when:

1. ✅ It upholds all Foundational Principles (Sections 1.1-1.5)
2. ✅ It violates none of the Prohibited Practices (Section 4.2)
3. ✅ It adheres to all applicable Operational Rules (Sections 2.1-2.5)
4. ✅ It respects the defined Limitations (Section 3)
5. ✅ Any Exercises of Exception (Section 4.1) are properly justified and documented
6. ✅ It includes appropriate tests and documentation
7. ✅ It maintains or improves overall system security posture
8. ✅ It enhances, rather than diminishes, user autonomy and control
9. ✅ It is transparent in its operation and data handling
10. ✅ It contributes to the long-term maintainability and sustainability of the project

## 9. Effective Date and Version

**Version**: 1.0.0  
**Effective Date**: 2026-07-29  
**Last Reviewed**: 2026-07-29  
**Next Review Due**: 2026-10-29  

*These rules are a living document intended to evolve with the project while maintaining our core commitment to user privacy, autonomy, and trust.*

---  
*Adherence to these rules is a condition of contribution to this project. By submitting code, documentation, or other assets, contributors agree to follow these guidelines.*