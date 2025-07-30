# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-06-16

### Added
- Initial release of GoodDay MCP Server
- 8 comprehensive tools for GoodDay integration:
  - `list_projects` - List organization projects with filtering
  - `get_project` - Get detailed project information
  - `create_project` - Create new projects
  - `list_project_tasks` - List tasks in a project
  - `get_task` - Get detailed task information
  - `create_task` - Create new tasks
  - `update_task_status` - Update task status
  - `get_user_assigned_tasks` - Get user's assigned tasks
- Full async/await support for efficient API calls
- Comprehensive error handling with descriptive messages
- Environment variable configuration for API token
- Type hints throughout for better development experience
- Support for Python 3.10+
- uv package manager support
- MCP 1.9.4+ compatibility

### Features
- Natural language integration with AI assistants
- Real-time project and task management
- User assignment tracking
- Status updates with comments
- Project filtering and organization
- Secure API token authentication

### Documentation
- Complete setup and configuration guide
- Claude Desktop integration instructions
- API reference documentation
- Example usage scenarios
