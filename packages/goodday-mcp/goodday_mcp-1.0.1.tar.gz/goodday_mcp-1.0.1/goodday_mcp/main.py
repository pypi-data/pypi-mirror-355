from typing import Any, Optional, List
import httpx
import os
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("goodday-mcp")

# Constants
GOODDAY_API_BASE = "https://api.goodday.work/2.0"
USER_AGENT = "goodday-mcp/1.0"

async def make_goodday_request(endpoint: str, method: str = "GET", data: dict = None) -> dict[str, Any] | list[Any] | None:
    """Make a request to the Goodday API with proper error handling."""
    api_token = os.getenv("GOODDAY_API_TOKEN")
    if not api_token:
        raise ValueError("GOODDAY_API_TOKEN environment variable is required")
    
    headers = {
        "User-Agent": USER_AGENT,
        "gd-api-token": api_token,
        "Content-Type": "application/json"
    }
    
    url = f"{GOODDAY_API_BASE}/{endpoint.lstrip('/')}"
    
    async with httpx.AsyncClient() as client:
        try:
            if method.upper() == "POST":
                response = await client.post(url, headers=headers, json=data, timeout=30.0)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=headers, json=data, timeout=30.0)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers, timeout=30.0)
            else:
                response = await client.get(url, headers=headers, timeout=30.0)

            response.raise_for_status()

            try:
                return response.json()
            except ValueError:
                # JSON decoding failed, return raw text as fallback
                return {"error": "Invalid JSON", "raw_response": response.text}

        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
        except httpx.RequestError as e:
            return {"error": f"Request error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

def format_task(task: dict) -> str:
    """Format a task into a readable string with safe checks."""
    if not isinstance(task, dict):
        return f"Invalid task data: {repr(task)}"

    # Defensive defaults in case nested keys are not dicts
    status = task.get('status') if isinstance(task.get('status'), dict) else {}
    project = task.get('project') if isinstance(task.get('project'), dict) else {}
    assigned_user = task.get('assignedToUser') if isinstance(task.get('assignedToUser'), dict) else {}

    return f"""
Task ID: {task.get('id', 'N/A')}
Title: {task.get('title', 'N/A')}
Status: {status.get('name', 'N/A')}
Project: {project.get('name', 'N/A')}
Assigned To: {assigned_user.get('name', 'Unassigned')}
Priority: {task.get('priority', 'N/A')}
Start Date: {task.get('startDate', 'N/A')}
End Date: {task.get('endDate', 'N/A')}
Deadline: {task.get('deadline', 'N/A')}
Progress: {task.get('progress', 0)}%
Description: {task.get('message', 'No description')}
""".strip()

def format_project(project: dict) -> str:
    """Format a project into a readable string with safe checks."""
    if not isinstance(project, dict):
        return f"Invalid project data: {repr(project)}"

    # Defensive defaults in case nested keys are not dicts
    status = project.get('status') if isinstance(project.get('status'), dict) else {}
    owner = project.get('owner') if isinstance(project.get('owner'), dict) else {}

    return f"""
Project ID: {project.get('id', 'N/A')}
Name: {project.get('name', 'N/A')}
Health: {project.get('health', 'N/A')}
Status: {status.get('name', 'N/A')}
Start Date: {project.get('startDate', 'N/A')}
End Date: {project.get('endDate', 'N/A')}
Progress: {project.get('progress', 0)}%
Owner: {owner.get('name', 'N/A')}
""".strip()

def format_user(user: dict) -> str:
    """Format a user into a readable string with safe checks."""
    if not isinstance(user, dict):
        return f"Invalid user data: {repr(user)}"

    # Defensive defaults in case nested keys are not dicts
    role = user.get('role') if isinstance(user.get('role'), dict) else {}

    return f"""
User ID: {user.get('id', 'N/A')}
Name: {user.get('name', 'N/A')}
Email: {user.get('email', 'N/A')}
Role: {role.get('name', 'N/A')}
Status: {user.get('status', 'N/A')}
""".strip()

# Project Management Tools
@mcp.tool()
async def get_projects(archived: bool = False, root_only: bool = False) -> str:
    """Get list of projects from Goodday.

    Args:
        archived: Set to true to retrieve archived/closed projects
        root_only: Set to true to return only root projects
    """
    params = []
    if archived:
        params.append("archived=true")
    if root_only:
        params.append("rootOnly=true")
    
    endpoint = "projects"
    if params:
        endpoint += "?" + "&".join(params)
    
    data = await make_goodday_request(endpoint)
    
    if not data:
        return "No projects found."
        
    if isinstance(data, dict):
        if "error" in data:
            return f"Unable to fetch projects: {data.get('error', 'Unknown error')}"
    elif isinstance(data, str):
        return f"Unexpected string response from API: {data}"
    elif not isinstance(data, list):
        return f"Unexpected response format: {type(data).__name__} - {str(data)}"
    
    projects = [format_project(project) for project in data]
    return "\n---\n".join(projects)

@mcp.tool()
async def get_project(project_id: str) -> str:
    """Get details of a specific project.

    Args:
        project_id: The ID of the project to retrieve
    """
    data = await make_goodday_request(f"project/{project_id}")
    
    if not data:
        return "Project not found."
    
    if isinstance(data, dict) and "error" in data:
        return f"Unable to fetch project: {data.get('error', 'Unknown error')}"
    
    return format_project(data)

@mcp.tool()
async def create_project(
    name: str,
    created_by_user_id: str,
    project_template_id: str,
    parent_project_id: Optional[str] = None,
    color: Optional[int] = None,
    project_owner_user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    deadline: Optional[str] = None
) -> str:
    """Create a new project in Goodday.

    Args:
        name: Project name
        created_by_user_id: ID of user creating the project
        project_template_id: Project template ID (found in Organization settings → Project templates)
        parent_project_id: Parent project ID to create a sub project
        color: Project color (1-24)
        project_owner_user_id: Project owner user ID
        start_date: Project start date (YYYY-MM-DD)
        end_date: Project end date (YYYY-MM-DD)
        deadline: Project deadline (YYYY-MM-DD)
    """
    data = {
        "name": name,
        "createdByUserId": created_by_user_id,
        "projectTemplateId": project_template_id
    }
    
    if parent_project_id:
        data["parentProjectId"] = parent_project_id
    if color:
        data["color"] = color
    if project_owner_user_id:
        data["projectOwnerUserId"] = project_owner_user_id
    if start_date:
        data["startDate"] = start_date
    if end_date:
        data["endDate"] = end_date
    if deadline:
        data["deadline"] = deadline
    
    result = await make_goodday_request("projects/new-project", "POST", data)
    
    if not result:
        return "Unable to create project: No response received"
    
    if isinstance(result, dict) and "error" in result:
        return f"Unable to create project: {result.get('error', 'Unknown error')}"
    
    return f"Project created successfully: {format_project(result)}"

# Task Management Tools
@mcp.tool()
async def get_project_tasks(project_id: str, closed: bool = False, subfolders: bool = False) -> str:
    """Get tasks from a specific project.

    Args:
        project_id: The ID of the project
        closed: Set to true to retrieve all open and closed tasks
        subfolders: Set to true to return tasks from project subfolders
    """
    params = []
    if closed:
        params.append("closed=true")
    if subfolders:
        params.append("subfolders=true")
    
    endpoint = f"project/{project_id}/tasks"
    if params:
        endpoint += "?" + "&".join(params)
    
    data = await make_goodday_request(endpoint)
    
    if not data:
        return "No tasks found."
    
    if isinstance(data, dict) and "error" in data:
        return f"Unable to fetch tasks: {data.get('error', 'Unknown error')}"
    
    if not isinstance(data, list):
        return f"Unexpected response format: {str(data)}"
    
    tasks = [format_task(task) for task in data]
    return "\n---\n".join(tasks)

@mcp.tool()
async def get_user_assigned_tasks(user_id: str, closed: bool = False) -> str:
    """Get tasks assigned to a specific user.

    Args:
        user_id: The ID of the user
        closed: Set to true to retrieve all open and closed tasks
    """
    params = []
    if closed:
        params.append("closed=true")
    
    endpoint = f"user/{user_id}/assigned-tasks"
    if params:
        endpoint += "?" + "&".join(params)
    
    data = await make_goodday_request(endpoint)
    
    if not data:
        return "No assigned tasks found."
    
    if isinstance(data, dict) and "error" in data:
        return f"Unable to fetch assigned tasks: {data.get('error', 'Unknown error')}"
    
    if not isinstance(data, list):
        return f"Unexpected response format: {str(data)}"
    
    tasks = [format_task(task) for task in data]
    return "\n---\n".join(tasks)

@mcp.tool()
async def get_user_action_required_tasks(user_id: str) -> str:
    """Get action required tasks for a specific user.

    Args:
        user_id: The ID of the user
    """
    data = await make_goodday_request(f"user/{user_id}/action-required-tasks")
    
    if not data:
        return "No action required tasks found."
    
    if isinstance(data, dict) and "error" in data:
        return f"Unable to fetch action required tasks: {data.get('error', 'Unknown error')}"
    
    if not isinstance(data, list):
        return f"Unexpected response format: {str(data)}"
    
    tasks = [format_task(task) for task in data]
    return "\n---\n".join(tasks)

@mcp.tool()
async def get_task(task_id: str) -> str:
    """Get details of a specific task.

    Args:
        task_id: The ID of the task to retrieve
    """
    data = await make_goodday_request(f"task/{task_id}")
    
    if not data:
        return "Task not found."
    
    if isinstance(data, dict) and "error" in data:
        return f"Unable to fetch task: {data.get('error', 'Unknown error')}"
    
    return format_task(data)

@mcp.tool()
async def create_task(
    project_id: str,
    title: str,
    from_user_id: str,
    parent_task_id: Optional[str] = None,
    message: Optional[str] = None,
    to_user_id: Optional[str] = None,
    task_type_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    deadline: Optional[str] = None,
    estimate: Optional[int] = None,
    story_points: Optional[int] = None,
    priority: Optional[int] = None
) -> str:
    """Create a new task in Goodday.

    Args:
        project_id: Task project ID
        title: Task title
        from_user_id: Task created by user ID  
        parent_task_id: Parent task ID to create a subtask
        message: Task description/initial message
        to_user_id: Assigned To/Action required user ID
        task_type_id: Task type ID
        start_date: Task start date (YYYY-MM-DD)
        end_date: Task end date (YYYY-MM-DD)
        deadline: Task deadline (YYYY-MM-DD)
        estimate: Task estimate in minutes
        story_points: Task story points estimate
        priority: Task priority (1-10), 50 - Blocker, 100 - Emergency
    """
    data = {
        "projectId": project_id,
        "title": title,
        "fromUserId": from_user_id
    }
    
    if parent_task_id:
        data["parentTaskId"] = parent_task_id
    if message:
        data["message"] = message
    if to_user_id:
        data["toUserId"] = to_user_id
    if task_type_id:
        data["taskTypeId"] = task_type_id
    if start_date:
        data["startDate"] = start_date
    if end_date:
        data["endDate"] = end_date
    if deadline:
        data["deadline"] = deadline
    if estimate:
        data["estimate"] = estimate
    if story_points:
        data["storyPoints"] = story_points
    if priority:
        data["priority"] = priority
    
    result = await make_goodday_request("tasks", "POST", data)
    
    if not result:
        return "Unable to create task: No response received"
    
    if isinstance(result, dict) and "error" in result:
        return f"Unable to create task: {result.get('error', 'Unknown error')}"
    
    return f"Task created successfully: {format_task(result)}"

@mcp.tool()
async def update_task_status(task_id: str, user_id: str, status_id: str, message: Optional[str] = None) -> str:
    """Update the status of a task.

    Args:
        task_id: The ID of the task to update
        user_id: User on behalf of whom API will execute update
        status_id: New status ID
        message: Optional comment
    """
    data = {
        "userId": user_id,
        "statusId": status_id
    }
    
    if message:
        data["message"] = message
    
    result = await make_goodday_request(f"task/{task_id}/status", "PUT", data)
    
    if not result:
        return "Unable to update task status: No response received"
    
    if isinstance(result, dict) and "error" in result:
        return f"Unable to update task status: {result.get('error', 'Unknown error')}"
    
    return "Task status updated successfully"

@mcp.tool()
async def add_task_comment(task_id: str, user_id: str, message: str) -> str:
    """Add a comment to a task.

    Args:
        task_id: The ID of the task
        user_id: User on behalf of whom API will execute update
        message: Comment text
    """
    data = {
        "userId": user_id,
        "message": message
    }
    
    result = await make_goodday_request(f"task/{task_id}/comment", "POST", data)
    
    if not result:
        return "Unable to add comment: No response received"
    
    if isinstance(result, dict) and "error" in result:
        return f"Unable to add comment: {result.get('error', 'Unknown error')}"
    
    return "Comment added successfully"

# User Management Tools
@mcp.tool()
async def get_users() -> str:
    """Get list of organization users."""
    data = await make_goodday_request("users")
    
    if not data:
        return "No users found."
    
    if isinstance(data, dict) and "error" in data:
        return f"Unable to fetch users: {data.get('error', 'Unknown error')}"
    
    if not isinstance(data, list):
        return f"Unexpected response format: {str(data)}"
    
    users = [format_user(user) for user in data]
    return "\n---\n".join(users)

@mcp.tool()
async def get_user(user_id: str) -> str:
    """Get details of a specific user.

    Args:
        user_id: The ID of the user to retrieve
    """
    data = await make_goodday_request(f"user/{user_id}")
    
    if not data:
        return "User not found."
    
    if isinstance(data, dict) and "error" in data:
        return f"Unable to fetch user: {data.get('error', 'Unknown error')}"
    
    return format_user(data)

@mcp.tool()
async def get_project_users(project_id: str) -> str:
    """Get users associated with a specific project.

    Args:
        project_id: The ID of the project
    """
    data = await make_goodday_request(f"project/{project_id}/users")
    
    if not data:
        return "No users found for this project."
    
    if isinstance(data, dict) and "error" in data:
        return f"Unable to fetch project users: {data.get('error', 'Unknown error')}"
    
    if not isinstance(data, list):
        return f"Unexpected response format: {str(data)}"
    
    users = [format_user(user) for user in data]
    return "\n---\n".join(users)

def run_cli():
    """CLI entry point for the goodday-mcp server."""
    mcp.run(transport='stdio')

if __name__ == "__main__":
    run_cli()
