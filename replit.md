# Overview

This is a Jira-GitHub integration automation system that streamlines development workflows by automatically processing Jira tickets and generating code, tests, and documentation. The system receives Jira webhook events, analyzes tickets using AI, creates GitHub branches and pull requests, and maintains a complete audit trail of automated actions.

The core application includes a simple Todo App (`todo_app.py`) that serves as the base application being enhanced through automated Jira ticket processing. The system intelligently handles different issue types (Bug, Story, Task, New Feature) with context-aware AI analysis and generates appropriate implementation scaffolding, test cases, and API specifications.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Webhook Processing Architecture
The system uses Flask-based webhook endpoints to process incoming events from both Jira and GitHub. The `unified_automation.py` serves as the main orchestrator, handling webhook verification, event routing, and coordinating automated responses. Webhook security is implemented through HMAC signature verification for both Jira and GitHub webhooks.

## AI-Powered Analysis Engine
The system leverages OpenAI's API for intelligent ticket analysis through the `JiraAutomationAgent` class. The AI engine analyzes Jira ticket content, determines appropriate actions based on issue type, and generates context-aware recommendations for implementation. This includes automatic labeling, priority assessment, and effort estimation.

## Git Integration and Automation
Automated Git operations are handled through multiple components:
- `auto_git_sync.py` provides continuous synchronization with remote repositories
- `github_sync_webhook.py` manages GitHub webhook events for bidirectional sync
- `git_sync_service.py` runs background Git operations as a service

The system can automatically create branches, commit changes, and create pull requests based on Jira ticket analysis.

## Code Generation Pipeline
The system generates implementation scaffolding in the `src/` directory, with each Jira ticket resulting in a dedicated Python module following a consistent naming convention. Generated code includes:
- Implementation classes with standardized structure
- Logging and error handling
- Placeholder methods for actual functionality
- Feature documentation in the `features/` directory

## Testing Framework
Automated test generation creates:
- Test specifications in the `tests/` directory
- API specifications in JSON format
- Unit test scaffolding aligned with implementation classes
- Testing checklists and manual testing guidelines

## File Organization Strategy
The system maintains a clean separation of concerns:
- Root level: Main automation scripts and configuration
- `src/`: Generated implementation code
- `features/`: Feature documentation and specifications
- `tests/`: Test specifications and scaffolding
- Configuration files for Git sync and webhook management

# External Dependencies

## Jira Integration
- **Jira REST API**: Used for reading ticket details and posting updates back to issues
- **Jira Webhooks**: Receives real-time notifications when tickets are created or updated
- **Authentication**: Requires Jira API tokens for secure communication

## GitHub Integration
- **GitHub REST API**: Manages repository operations including branch creation, file updates, and pull request creation
- **GitHub Webhooks**: Enables bidirectional sync for push and pull request events
- **Authentication**: Uses GitHub Personal Access Tokens with repository permissions

## AI Services
- **OpenAI API**: Powers the intelligent analysis of Jira tickets and generates context-aware recommendations
- **Authentication**: Requires OpenAI API key for AI-powered features

## Python Libraries
- **Flask**: Web framework for webhook endpoints and API handling
- **Requests**: HTTP client for external API communication
- **LangChain**: Framework for AI agent orchestration and prompt engineering
- **Gradio**: Provides web interface capabilities for user interaction
- **Python-dotenv**: Environment variable management for configuration

## Development Platform
- **Replit**: Cloud-based development environment that hosts the automation system
- **Environment Variables**: Secure storage of API keys and configuration through Replit Secrets