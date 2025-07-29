#!/usr/bin/env python3
"""
Jira CLI MCP Server

A Model Context Protocol server that wraps the jira CLI tool.
Exposes jira commands through MCP resources, tools, and prompts.
"""

import asyncio
import json
import os
from typing import cast
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP


@dataclass
class JiraCliConfig:
    """Jira CLI configuration"""

    config_file: str | None = None
    project: str | None = None


@dataclass
class AppContext:
    """Application context"""

    config: JiraCliConfig


async def run_jira_command(
    *args: str, input_data: str | None = None
) -> tuple[str, str, int]:
    """Execute jira CLI command and return stdout, stderr, returncode"""
    cmd = ["jira"] + list(args)

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE if input_data else None,
        )

        stdout, stderr = await process.communicate(
            input=input_data.encode() if input_data else None
        )

        return stdout.decode(), stderr.decode(), process.returncode or 0
    except FileNotFoundError:
        return (
            "",
            "jira CLI not found. Please install: https://github.com/ankitpokhrel/jira-cli",
            1,
        )
    except Exception as e:
        return "", f"Error running jira command: {e}", 1


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle"""
    config_file = os.getenv("JIRA_CONFIG_FILE")
    project = os.getenv("JIRA_PROJECT")

    config = JiraCliConfig(config_file=config_file, project=project)

    # Test jira CLI is available (but don't fail startup if it's not)
    try:
        stdout, stderr, code = await run_jira_command("--version")
        if code != 0:
            print(f"Warning: jira CLI not working properly: {stderr}")
        else:
            print(f"jira CLI is available: {stdout.strip()}")

            # Check authentication by trying to get current user
            auth_stdout, auth_stderr, auth_code = await run_jira_command("me")
            if auth_code != 0:
                print(
                    f"Warning: jira CLI not authenticated. Run 'jira init' or check API credentials: {auth_stderr}"
                )
            else:
                print(f"jira CLI authenticated successfully: {auth_stdout.strip()}")

    except FileNotFoundError:
        print(
            "Warning: jira CLI not found. Please install: https://github.com/ankitpokhrel/jira-cli"
        )
    except Exception as e:
        print(f"Warning: Could not test jira CLI: {e}")

    yield AppContext(config=config)


# Create MCP server
mcp = FastMCP("Jira CLI MCP", lifespan=app_lifespan)


def build_jira_args(ctx: AppContext, *args: str) -> list[str]:
    """Build jira command args with config"""
    cmd_args = []

    if ctx.config.config_file:
        cmd_args.extend(["--config", ctx.config.config_file])

    if ctx.config.project:
        cmd_args.extend(["--project", ctx.config.project])

    cmd_args.extend(args)
    return cmd_args


# Resources (for providing context to LLMs)


@mcp.resource("jira://issues")
async def list_issues() -> str:
    """List recent issues"""
    ctx = cast(AppContext, mcp.get_context().request_context.lifespan_context)

    args = build_jira_args(ctx, "issue", "list", "--plain", "--no-headers", "--raw")
    stdout, stderr, code = await run_jira_command(*args)

    if code != 0:
        return f"Error: {stderr}"

    try:
        # Try to parse as JSON if --raw flag worked
        issues = json.loads(stdout)
        return json.dumps(issues, indent=2)
    except json.JSONDecodeError:
        # Fall back to plain text
        return stdout


@mcp.resource("jira://issue/{issue_key}")
async def view_issue(issue_key: str) -> str:
    """View issue details"""
    ctx = cast(AppContext, mcp.get_context().request_context.lifespan_context)

    args = build_jira_args(ctx, "issue", "view", issue_key, "--plain")
    stdout, stderr, code = await run_jira_command(*args)

    if code != 0:
        return f"Error: {stderr}"

    return stdout


@mcp.resource("jira://epics")
async def list_epics() -> str:
    """List epics"""
    ctx = cast(AppContext, mcp.get_context().request_context.lifespan_context)

    args = build_jira_args(ctx, "epic", "list", "--plain", "--no-headers")
    stdout, stderr, code = await run_jira_command(*args)

    if code != 0:
        return f"Error: {stderr}"

    return stdout


@mcp.resource("jira://sprints")
async def list_sprints() -> str:
    """List sprints"""
    ctx = cast(AppContext, mcp.get_context().request_context.lifespan_context)

    args = build_jira_args(ctx, "sprint", "list", "--plain", "--no-headers")
    stdout, stderr, code = await run_jira_command(*args)

    if code != 0:
        return f"Error: {stderr}"

    return stdout


@mcp.resource("jira://projects")
async def list_projects() -> str:
    """List projects"""
    ctx = cast(AppContext, mcp.get_context().request_context.lifespan_context)

    args = build_jira_args(ctx, "project", "list")
    stdout, stderr, code = await run_jira_command(*args)

    if code != 0:
        return f"Error: {stderr}"

    return stdout


@mcp.resource("jira://boards")
async def list_boards() -> str:
    """List boards"""
    ctx = cast(AppContext, mcp.get_context().request_context.lifespan_context)

    args = build_jira_args(ctx, "board", "list")
    stdout, stderr, code = await run_jira_command(*args)

    if code != 0:
        return f"Error: {stderr}"

    return stdout


@mcp.resource("jira://search/{jql}")
async def search_issues(jql: str) -> str:
    """Search issues with JQL"""
    ctx = cast(AppContext, mcp.get_context().request_context.lifespan_context)

    args = build_jira_args(ctx, "issue", "list", "--jql", jql, "--plain")
    stdout, stderr, code = await run_jira_command(*args)

    if code != 0:
        return f"Error: {stderr}"

    return stdout


# Tools (for taking actions)


@mcp.tool()
async def create_issue(
    summary: str,
    issue_type: str = "Task",
    body: str = "",
    priority: str = "",
    assignee: str = "",
    labels: str = "",
    component: str = "",
    no_input: bool = True,
) -> str:
    """Create a new Jira issue"""
    ctx = cast(AppContext, mcp.get_context().request_context.lifespan_context)

    args = build_jira_args(
        ctx, "issue", "create", "--type", issue_type, "--summary", summary
    )

    if body:
        args.extend(["--body", body])
    if priority:
        args.extend(["--priority", priority])
    if assignee:
        args.extend(["--assignee", assignee])
    if labels:
        args.extend(["--label", labels])
    if component:
        args.extend(["--component", component])
    if no_input:
        args.append("--no-input")

    stdout, stderr, code = await run_jira_command(*args)

    if code != 0:
        return f"Error creating issue: {stderr}"

    return f"Issue created successfully:\n{stdout}"


@mcp.tool()
async def edit_issue(
    issue_key: str,
    summary: str = "",
    body: str = "",
    priority: str = "",
    assignee: str = "",
    labels: str = "",
    component: str = "",
    no_input: bool = True,
) -> str:
    """Edit an existing Jira issue"""
    ctx = cast(AppContext, mcp.get_context().request_context.lifespan_context)

    args = build_jira_args(ctx, "issue", "edit", issue_key)

    if summary:
        args.extend(["--summary", summary])
    if body:
        args.extend(["--body", body])
    if priority:
        args.extend(["--priority", priority])
    if assignee:
        args.extend(["--assignee", assignee])
    if labels:
        args.extend(["--label", labels])
    if component:
        args.extend(["--component", component])
    if no_input:
        args.append("--no-input")

    stdout, stderr, code = await run_jira_command(*args)

    if code != 0:
        return f"Error editing issue: {stderr}"

    return f"Issue updated successfully:\n{stdout}"


@mcp.tool()
async def assign_issue(issue_key: str, assignee: str) -> str:
    """Assign issue to a user"""
    ctx = cast(AppContext, mcp.get_context().request_context.lifespan_context)

    args = build_jira_args(ctx, "issue", "assign", issue_key, assignee)
    stdout, stderr, code = await run_jira_command(*args)

    if code != 0:
        return f"Error assigning issue: {stderr}"

    return f"Issue assigned successfully:\n{stdout}"


@mcp.tool()
async def move_issue(issue_key: str, status: str, comment: str = "") -> str:
    """Move/transition issue to new status"""
    ctx = cast(AppContext, mcp.get_context().request_context.lifespan_context)

    args = build_jira_args(ctx, "issue", "move", issue_key, status)

    if comment:
        args.extend(["--comment", comment])

    stdout, stderr, code = await run_jira_command(*args)

    if code != 0:
        return f"Error moving issue: {stderr}"

    return f"Issue moved successfully:\n{stdout}"


@mcp.tool()
async def add_comment(issue_key: str, comment: str) -> str:
    """Add comment to issue"""
    ctx = cast(AppContext, mcp.get_context().request_context.lifespan_context)

    args = build_jira_args(ctx, "issue", "comment", "add", issue_key, comment)
    stdout, stderr, code = await run_jira_command(*args)

    if code != 0:
        return f"Error adding comment: {stderr}"

    return f"Comment added successfully:\n{stdout}"


@mcp.tool()
async def search_issues_tool(
    jql: str = "",
    issue_type: str = "",
    status: str = "",
    assignee: str = "",
    priority: str = "",
    reporter: str = "",
    created: str = "",
    updated: str = "",
    labels: str = "",
    limit: int = 25,
) -> str:
    """Search issues with flexible criteria"""
    ctx = cast(AppContext, mcp.get_context().request_context.lifespan_context)

    args = build_jira_args(ctx, "issue", "list", "--plain")

    if jql:
        args.extend(["--jql", jql])
    else:
        # Build query from individual parameters
        if issue_type:
            args.extend(["--type", issue_type])
        if status:
            args.extend(["--status", status])
        if assignee:
            args.extend(["--assignee", assignee])
        if priority:
            args.extend(["--priority", priority])
        if reporter:
            args.extend(["--reporter", reporter])
        if created:
            args.extend(["--created", created])
        if updated:
            args.extend(["--updated", updated])
        if labels:
            args.extend(["--label", labels])

    args.extend(["--paginate", f"0:{limit}"])

    stdout, stderr, code = await run_jira_command(*args)

    if code != 0:
        return f"Error searching issues: {stderr}"

    return stdout


@mcp.tool()
async def clone_issue(issue_key: str, summary: str = "", assignee: str = "") -> str:
    """Clone an existing issue"""
    ctx = cast(AppContext, mcp.get_context().request_context.lifespan_context)

    args = build_jira_args(ctx, "issue", "clone", issue_key)

    if summary:
        args.extend(["--summary", summary])
    if assignee:
        args.extend(["--assignee", assignee])

    stdout, stderr, code = await run_jira_command(*args)

    if code != 0:
        return f"Error cloning issue: {stderr}"

    return f"Issue cloned successfully:\n{stdout}"


@mcp.tool()
async def link_issues(inward_issue: str, outward_issue: str, link_type: str) -> str:
    """Link two issues"""
    ctx = cast(AppContext, mcp.get_context().request_context.lifespan_context)

    args = build_jira_args(ctx, "issue", "link", inward_issue, outward_issue, link_type)
    stdout, stderr, code = await run_jira_command(*args)

    if code != 0:
        return f"Error linking issues: {stderr}"

    return f"Issues linked successfully:\n{stdout}"


@mcp.tool()
async def create_epic(
    name: str, summary: str, body: str = "", priority: str = ""
) -> str:
    """Create a new epic"""
    ctx = cast(AppContext, mcp.get_context().request_context.lifespan_context)

    args = build_jira_args(
        ctx, "epic", "create", "--name", name, "--summary", summary, "--no-input"
    )

    if body:
        args.extend(["--body", body])
    if priority:
        args.extend(["--priority", priority])

    stdout, stderr, code = await run_jira_command(*args)

    if code != 0:
        return f"Error creating epic: {stderr}"

    return f"Epic created successfully:\n{stdout}"


@mcp.tool()
async def add_to_sprint(sprint_id: str, *issue_keys: str) -> str:
    """Add issues to sprint"""
    ctx = cast(AppContext, mcp.get_context().request_context.lifespan_context)

    args = build_jira_args(ctx, "sprint", "add", sprint_id, *issue_keys)
    stdout, stderr, code = await run_jira_command(*args)

    if code != 0:
        return f"Error adding to sprint: {stderr}"

    return f"Issues added to sprint successfully:\n{stdout}"


# Prompts (for structured interactions)


@mcp.prompt()
def create_bug_report(component: str = "", severity: str = "Medium") -> str:
    """Template for creating a bug report"""
    return f"""Create a bug report with these details:

**Summary:** [Brief description of the bug]

**Component:** {component or "[Affected component/module]"}

**Priority:** {severity}

**Steps to Reproduce:**
1. [First step]
2. [Second step]  
3. [Third step]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Environment:**
- OS: [Operating system]
- Browser: [If applicable]
- Version: [Application/product version]

**Additional Information:**
[Screenshots, logs, or other relevant details]

Use: `create_issue` tool with type "Bug" and the above information."""


@mcp.prompt()
def create_feature_request(area: str = "") -> str:
    """Template for creating a feature request"""
    return f"""Create a feature request with these details:

**Summary:** [Brief title of the feature]

**Component:** {area or "[Area/module for the feature]"}

**Priority:** Medium

**User Story:**
As a [type of user], I want [goal] so that [benefit].

**Acceptance Criteria:**
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

**Description:**
[Detailed description of the feature]

**Benefits:**
[Why this feature is valuable]

**Technical Notes:**
[Any technical considerations or constraints]

Use: `create_issue` tool with type "Story" and the above information."""


@mcp.prompt()
def daily_standup_search() -> str:
    """Search for issues relevant to daily standup"""
    return """Search for your current work items:

**Your Open Issues:**
Use: `search_issues_tool` with assignee="$(jira me)" and status not "Done"

**Recently Updated Issues:**
Use: `search_issues_tool` with updated="week" and assignee="$(jira me)"

**Current Sprint Issues:**
Use: `search_issues_tool` with jql="assignee = currentUser() AND sprint in openSprints()"

**Yesterday's Work:**
Use: `search_issues_tool` with updated="1d" and assignee="$(jira me)"

Review these results to prepare your standup update."""


@mcp.prompt()
def issue_triage_workflow() -> str:
    """Workflow for triaging new issues"""
    return """Issue Triage Workflow:

**Step 1: Review New Issues**
Use: `search_issues_tool` with status="Open" and created="today"

**Step 2: For Each Issue, Check:**
- Is the summary clear and descriptive?
- Are reproduction steps provided (for bugs)?
- Is the priority appropriate?
- Is the component/area identified?
- Is there enough information to work on it?

**Step 3: Actions to Take:**
- Use `edit_issue` to improve summary/description
- Use `assign_issue` to assign to appropriate team member
- Use `move_issue` to change status (e.g., "In Review" → "Ready for Development")
- Use `add_comment` to ask for clarification if needed

**Step 4: Prioritize**
- Use `edit_issue` to set appropriate priority
- Use `link_issues` to connect related issues
- Use `add_to_sprint` for ready issues"""


if __name__ == "__main__":
    mcp.run()

