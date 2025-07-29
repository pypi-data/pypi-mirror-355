# Jira CLI MCP

A Model Context Protocol (MCP) server that wraps the [Jira CLI](https://github.com/ankitpokhrel/jira-cli) tool, exposing Jira commands through MCP resources, tools, and prompts for AI assistant integration.

## Features

- **MCP Resources**: Access Jira data through standardized URL endpoints
- **MCP Tools**: Execute Jira commands (create issues, edit, assign, etc.)
- **MCP Prompts**: Use templates for common Jira workflows
- **Authentication**: Uses existing Jira CLI authentication
- **Project Configuration**: Customize default project and config

## Prerequisites

- Python 3.11+
- [Jira CLI](https://github.com/ankitpokhrel/jira-cli) installed and configured
- Access to a Jira instance

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/yourusername/jira-cli-mcp.git
   cd jira-cli-mcp
   ```

2. Install dependencies with uv:

   ```bash
   uv sync
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

## Configuration

The server can be configured via environment variables:

- `JIRA_CONFIG_FILE`: Path to a custom Jira CLI config file
- `JIRA_PROJECT`: Default Jira project to use

Example:

```bash
export JIRA_PROJECT="PROJ"
export JIRA_CONFIG_FILE="/path/to/config.yml"
```

## Usage

### Starting the Server

```bash
python main.py
```

By default, the server will start on port 8080.

### Available Resources

- `jira://issues` - List recent issues
- `jira://issue/{issue_key}` - View issue details
- `jira://epics` - List epics
- `jira://sprints` - List sprints
- `jira://projects` - List projects
- `jira://boards` - List boards
- `jira://search/{jql}` - Search issues with JQL

### Available Tools

- `create_issue` - Create a new Jira issue
- `edit_issue` - Edit an existing Jira issue
- `assign_issue` - Assign issue to a user
- `move_issue` - Move/transition issue to new status
- `add_comment` - Add comment to issue
- `search_issues_tool` - Search issues with flexible criteria
- `clone_issue` - Clone an existing issue
- `link_issues` - Link two issues
- `create_epic` - Create a new epic
- `add_to_sprint` - Add issues to sprint

### Available Prompts

- `create_bug_report` - Template for creating a bug report
- `create_feature_request` - Template for creating a feature request
- `daily_standup_search` - Search for issues relevant to daily standup
- `issue_triage_workflow` - Workflow for triaging new issues

## Integrating with AI Assistants

This MCP server can be integrated with AI assistants that support the Model Context Protocol. Example integration:

```python
from mcp.client import MCPClient

# Connect to the MCP server
client = MCPClient("http://localhost:8080")

# Use resources
issues = client.fetch_resource("jira://issues")

# Execute tools
result = client.execute_tool("create_issue", {
    "summary": "Fix login bug",
    "issue_type": "Bug",
    "priority": "High"
})

# Get prompts
template = client.get_prompt("create_bug_report", {
    "component": "Authentication", 
    "severity": "High"
})
```

## License

[MIT](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

