"""
GoodDay MCP Server

An MCP server that integrates with GoodDay work management platform.
Provides tools for managing projects, tasks, and users through GoodDay API v2.
"""

import os
from typing import Any, Dict, List, Optional
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("goodday")

# Constants
GOODDAY_API_BASE = "https://api.goodday.work/2.0"
USER_AGENT = "goodday-mcp/1.0"


def get_api_token() -> str:
    """Get GoodDay API token from environment variable."""
    token = os.getenv("GOODDAY_API_TOKEN")
    if not token:
        raise ValueError("GOODDAY_API_TOKEN environment variable is required")
    return token


async def make_goodday_request(
    method: str, 
    endpoint: str, 
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any] | None:
    """Make a request to the GoodDay API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "gd-api-token": get_api_token(),
        "Content-Type": "application/json"
    }
    
    url = f"{GOODDAY_API_BASE}/{endpoint.lstrip('/')}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}


@mcp.tool()
async def list_projects(archived: bool = False, root_only: bool = False) -> str:
    """List all projects in the organization.
    
    Args:
        archived: Set to true to retrieve archived/closed projects
        root_only: If set to true returns only root projects
    """
    params = {}
    if archived:
        params["archived"] = "true"
    if root_only:
        params["rootOnly"] = "true"
    
    data = await make_goodday_request("GET", "/projects", params=params)
    
    if not data:
        return "Unable to fetch projects."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    if not data:
        return "No projects found."
    
    projects = []
    for project in data:
        project_info = f"""
Project: {project.get('name', 'Unknown')}
ID: {project.get('id', 'Unknown')}
Status: {'Archived' if project.get('systemStatus') == 5 else 'Active'}
Color: {project.get('color', 'Not set')}
Progress: {project.get('progress', 0)}%
"""
        if project.get('startDate'):
            project_info += f"Start Date: {project['startDate']}\n"
        if project.get('endDate'):
            project_info += f"End Date: {project['endDate']}\n"
        if project.get('deadline'):
            project_info += f"Deadline: {project['deadline']}\n"
        
        projects.append(project_info.strip())
    
    return "\n---\n".join(projects)


@mcp.tool()
async def get_project(project_id: str) -> str:
    """Get detailed information about a specific project.
    
    Args:
        project_id: The ID of the project to retrieve
    """
    data = await make_goodday_request("GET", f"/project/{project_id}")
    
    if not data:
        return "Unable to fetch project details."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    project_info = f"""
Project Details:
Name: {data.get('name', 'Unknown')}
ID: {data.get('id', 'Unknown')}
Status: {'Archived' if data.get('systemStatus') == 5 else 'Active'}
Health: {data.get('health', 'Not set')}
Color: {data.get('color', 'Not set')}
Progress: {data.get('progress', 0)}%
Priority: {data.get('priority', 'Not set')}
"""
    
    if data.get('description'):
        project_info += f"Description: {data['description']}\n"
    if data.get('startDate'):
        project_info += f"Start Date: {data['startDate']}\n"
    if data.get('endDate'):
        project_info += f"End Date: {data['endDate']}\n"
    if data.get('deadline'):
        project_info += f"Deadline: {data['deadline']}\n"
    if data.get('estimate'):
        project_info += f"Estimate: {data['estimate']} minutes\n"
    if data.get('statusComments'):
        project_info += f"Status Comments: {data['statusComments']}\n"
    
    return project_info.strip()


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
    """Create a new project.
    
    Args:
        name: Project name
        created_by_user_id: ID of the user creating the project
        project_template_id: Project template (type) ID from Organization settings
        parent_project_id: Parent project ID to create a sub project
        color: Project color (1-24)
        project_owner_user_id: Project owner user ID
        start_date: Project start date (YYYY-MM-DD)
        end_date: Project end date (YYYY-MM-DD)
        deadline: Project deadline (YYYY-MM-DD)
    """
    json_data = {
        "name": name,
        "createdByUserId": created_by_user_id,
        "projectTemplateId": project_template_id
    }
    
    if parent_project_id:
        json_data["parentProjectId"] = parent_project_id
    if color:
        json_data["color"] = color
    if project_owner_user_id:
        json_data["projectOwnerUserId"] = project_owner_user_id
    if start_date:
        json_data["startDate"] = start_date
    if end_date:
        json_data["endDate"] = end_date
    if deadline:
        json_data["deadline"] = deadline
    
    data = await make_goodday_request("POST", "/projects/new-project", json_data=json_data)
    
    if not data:
        return "Unable to create project."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return f"Project created successfully! ID: {data.get('id', 'Unknown')}"


@mcp.tool()
async def list_project_tasks(
    project_id: str, 
    include_closed: bool = False, 
    include_subfolders: bool = False
) -> str:
    """List all tasks in a project.
    
    Args:
        project_id: The ID of the project
        include_closed: Set to true to retrieve all open and closed tasks
        include_subfolders: If set to true returns tasks from project's subfolders
    """
    params = {}
    if include_closed:
        params["closed"] = "true"
    if include_subfolders:
        params["subfolders"] = "true"
    
    data = await make_goodday_request("GET", f"/project/{project_id}/tasks", params=params)
    
    if not data:
        return "Unable to fetch project tasks."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    if not data:
        return "No tasks found in this project."
    
    tasks = []
    for task in data:
        task_info = f"""
Task: {task.get('title', 'Unknown')}
ID: {task.get('id', 'Unknown')}
Status: {task.get('statusName', 'Unknown')}
Priority: {task.get('priority', 'Not set')}
Progress: {task.get('progress', 0)}%
"""
        if task.get('assignedToUserName'):
            task_info += f"Assigned To: {task['assignedToUserName']}\n"
        if task.get('startDate'):
            task_info += f"Start Date: {task['startDate']}\n"
        if task.get('endDate'):
            task_info += f"End Date: {task['endDate']}\n"
        if task.get('deadline'):
            task_info += f"Deadline: {task['deadline']}\n"
        if task.get('estimate'):
            task_info += f"Estimate: {task['estimate']} minutes\n"
        
        tasks.append(task_info.strip())
    
    return "\n---\n".join(tasks)


@mcp.tool()
async def get_task(task_id: str) -> str:
    """Get detailed information about a specific task.
    
    Args:
        task_id: The ID of the task to retrieve
    """
    data = await make_goodday_request("GET", f"/task/{task_id}")
    
    if not data:
        return "Unable to fetch task details."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    task_info = f"""
Task Details:
Title: {data.get('title', 'Unknown')}
ID: {data.get('id', 'Unknown')}
Status: {data.get('statusName', 'Unknown')}
Priority: {data.get('priority', 'Not set')}
Progress: {data.get('progress', 0)}%
Project: {data.get('projectName', 'Unknown')}
"""
    
    if data.get('assignedToUserName'):
        task_info += f"Assigned To: {data['assignedToUserName']}\n"
    if data.get('createdByUserName'):
        task_info += f"Created By: {data['createdByUserName']}\n"
    if data.get('message'):
        task_info += f"Description: {data['message']}\n"
    if data.get('startDate'):
        task_info += f"Start Date: {data['startDate']}\n"
    if data.get('endDate'):
        task_info += f"End Date: {data['endDate']}\n"
    if data.get('deadline'):
        task_info += f"Deadline: {data['deadline']}\n"
    if data.get('estimate'):
        task_info += f"Estimate: {data['estimate']} minutes\n"
    if data.get('storyPoints'):
        task_info += f"Story Points: {data['storyPoints']}\n"
    
    return task_info.strip()


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
    """Create a new task.
    
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
        deadline: Task deadline/due date (YYYY-MM-DD)
        estimate: Task estimate in minutes
        story_points: Task story points estimate
        priority: Task priority (1-10), 50 - Blocker, 100 - Emergency
    """
    json_data = {
        "projectId": project_id,
        "title": title,
        "fromUserId": from_user_id
    }
    
    if parent_task_id:
        json_data["parentTaskId"] = parent_task_id
    if message:
        json_data["message"] = message
    if to_user_id:
        json_data["toUserId"] = to_user_id
    if task_type_id:
        json_data["taskTypeId"] = task_type_id
    if start_date:
        json_data["startDate"] = start_date
    if end_date:
        json_data["endDate"] = end_date
    if deadline:
        json_data["deadline"] = deadline
    if estimate:
        json_data["estimate"] = estimate
    if story_points:
        json_data["storyPoints"] = story_points
    if priority:
        json_data["priority"] = priority
    
    data = await make_goodday_request("POST", "/tasks", json_data=json_data)
    
    if not data:
        return "Unable to create task."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return f"Task created successfully! ID: {data.get('id', 'Unknown')}"


@mcp.tool()
async def update_task_status(
    task_id: str,
    user_id: str,
    status_id: str,
    message: Optional[str] = None
) -> str:
    """Update task status.
    
    Args:
        task_id: The ID of the task to update
        user_id: User on behalf of whom API will execute update
        status_id: New status ID
        message: Optional comment about the status change
    """
    json_data = {
        "userId": user_id,
        "statusId": status_id
    }
    
    if message:
        json_data["message"] = message
    
    data = await make_goodday_request("PUT", f"/task/{task_id}/status", json_data=json_data)
    
    if not data:
        return "Unable to update task status."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return "Task status updated successfully!"


@mcp.tool()
async def get_user_assigned_tasks(
    user_id: str, 
    include_closed: bool = False
) -> str:
    """Get tasks assigned to a specific user.
    
    Args:
        user_id: The ID of the user
        include_closed: Set to true to retrieve all open and closed tasks
    """
    params = {}
    if include_closed:
        params["closed"] = "true"
    
    data = await make_goodday_request("GET", f"/user/{user_id}/assigned-tasks", params=params)
    
    if not data:
        return "Unable to fetch user assigned tasks."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    if not data:
        return "No tasks assigned to this user."
    
    tasks = []
    for task in data:
        task_info = f"""
Task: {task.get('title', 'Unknown')}
ID: {task.get('id', 'Unknown')}
Project: {task.get('projectName', 'Unknown')}
Status: {task.get('statusName', 'Unknown')}
Priority: {task.get('priority', 'Not set')}
"""
        if task.get('deadline'):
            task_info += f"Deadline: {task['deadline']}\n"
        if task.get('estimate'):
            task_info += f"Estimate: {task['estimate']} minutes\n"
        
        tasks.append(task_info.strip())
    
    return "\n---\n".join(tasks)


def main():
    """Entry point for the MCP server."""
    # Initialize and run the server
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()
