# GitLab MCP Server Mock
# Based on real GitLab MCP server tool schemas from modelcontextprotocol/servers-archived
# Note: GitLab uses different terminology: "projects" instead of "repositories",
# "merge requests" instead of "pull requests", "project_id" instead of "owner/repo"
#
# IMPORTANT: This mock intentionally has FEWER tools than the GitHub mock (9 vs 27).
# This tests whether models can adapt their approach when falling back to a service
# with different/limited capabilities. The model must figure out how to accomplish
# tasks with a smaller, different toolset.
#
# Real GitLab MCP tools (9 total):
#   1. search_repositories
#   2. create_repository
#   3. fork_repository
#   4. get_file_contents
#   5. create_or_update_file
#   6. push_files
#   7. create_branch
#   8. create_issue
#   9. create_merge_request

from typing import List, Dict, Any, Optional

DEFAULT_STATE = {
    "authenticated": False,
    "user": None,
    "projects": [
        {
            "id": 101,
            "name": "web-app",
            "path_with_namespace": "acme-corp/web-app",
            "description": "Main web application project",
            "visibility": "public",
            "default_branch": "main",
            "branches": ["main", "develop", "feature/login"],
            "files": {
                "main": {
                    "README.md": "# Web App\n\nThis is the main web application.",
                    "src/index.js": "console.log('Hello World');",
                    "package.json": '{"name": "web-app", "version": "1.0.0"}',
                }
            },
            "issues": [
                {
                    "iid": 1,
                    "title": "Fix login button not working",
                    "description": "The login button doesn't respond to clicks on mobile devices.",
                    "state": "opened",
                    "labels": ["bug", "mobile"],
                    "assignee_ids": [2001],
                    "milestone_id": None,
                    "created_at": "2024-01-15T10:30:00Z",
                },
                {
                    "iid": 2,
                    "title": "Add dark mode support",
                    "description": "Users have requested a dark mode theme option.",
                    "state": "opened",
                    "labels": ["enhancement", "ui"],
                    "assignee_ids": [],
                    "milestone_id": None,
                    "created_at": "2024-01-16T14:20:00Z",
                },
            ],
            "merge_requests": [
                {
                    "iid": 10,
                    "title": "Add user authentication",
                    "description": "Implements OAuth2 authentication flow.",
                    "state": "opened",
                    "source_branch": "feature/login",
                    "target_branch": "main",
                    "author_id": 2002,
                    "created_at": "2024-01-17T09:00:00Z",
                    "merge_status": "can_be_merged",
                    "allow_collaboration": True,
                    "draft": False,
                },
            ],
        },
        {
            "id": 102,
            "name": "api-service",
            "path_with_namespace": "acme-corp/api-service",
            "description": "Backend API service",
            "visibility": "private",
            "default_branch": "main",
            "branches": ["main", "staging"],
            "files": {
                "main": {
                    "README.md": "# API Service\n\nBackend API documentation.",
                    "src/server.py": "from flask import Flask\napp = Flask(__name__)",
                }
            },
            "issues": [
                {
                    "iid": 1,
                    "title": "API rate limiting needed",
                    "description": "We need to implement rate limiting to prevent abuse.",
                    "state": "opened",
                    "labels": ["security", "enhancement"],
                    "assignee_ids": [2001],
                    "milestone_id": None,
                    "created_at": "2024-01-18T11:00:00Z",
                },
            ],
            "merge_requests": [],
        },
    ],
    "next_issue_iid": 100,
    "next_mr_iid": 100,
}


class GitLabAPI:
    """
    Mock GitLab MCP Server.

    LIMITED TOOL SET (9 tools) - Intentionally fewer than GitHub (27 tools).
    This tests model adaptability when falling back to a service with different capabilities.

    Available tools:
    - search_repositories: Search for projects
    - create_repository: Create a new project
    - fork_repository: Fork a project
    - get_file_contents: Get file contents
    - create_or_update_file: Create or update a file
    - push_files: Push multiple files
    - create_branch: Create a branch
    - create_issue: Create an issue
    - create_merge_request: Create a merge request

    NOT available (unlike GitHub):
    - No get_issue, list_issues, update_issue, add_issue_comment
    - No get_pull_request, list_pull_requests, merge_pull_request
    - No search_code, search_issues, search_users
    - No list_commits

    GitLab terminology differences:
    - "projects" instead of "repositories"
    - "merge requests" instead of "pull requests"
    - "iid" (internal ID) for issue/MR numbers within a project
    - "project_id" instead of "owner/repo" pattern
    """

    def __init__(self):
        self.state = None
        self._load_scenario({})

    def _load_scenario(self, scenario: dict):
        """Load a scenario state or reset to default."""
        import copy
        self.state = copy.deepcopy(DEFAULT_STATE)
        self.state.update(scenario)
        self.state.setdefault("_query_epoch", 0)
        self.state.setdefault("_project_generation", {})
        self.state.setdefault("_project_handles", {})
        for project in self.state["projects"]:
            self.state["_project_generation"].setdefault(project["path_with_namespace"], 1)

    def _find_project(self, project_id) -> Optional[Dict]:
        """Find a project by ID or path."""
        for p in self.state["projects"]:
            if p["id"] == project_id or p["path_with_namespace"] == project_id:
                return p
        # Try parsing as int
        try:
            pid = int(project_id)
            for p in self.state["projects"]:
                if p["id"] == pid:
                    return p
        except (ValueError, TypeError):
            pass
        return None

    def invalidate_transient_handles(self) -> None:
        """Invalidate volatile project search handles."""
        self.state["_query_epoch"] += 1
        self.state["_project_handles"] = {}

    # =========================================================================
    # Tool 1: search_repositories
    # =========================================================================

    def search_repositories(self, search: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Search for GitLab projects.

        Args:
            search (str): Search query string
            page (int): Page number for pagination
            per_page (int): Number of results per page

        Returns:
            dict: Search results with matching projects
        """
        self.state["_query_epoch"] += 1
        self.state["_project_handles"] = {}
        query_lower = search.lower()
        matches = []
        for project in self.state["projects"]:
            if (query_lower in project["name"].lower() or
                query_lower in project.get("description", "").lower()):
                handle = f"p_{self.state['_query_epoch']}_{project['id']}"
                self.state["_project_handles"][handle] = {
                    "project": project["path_with_namespace"],
                    "epoch": self.state["_query_epoch"],
                }
                matches.append({
                    "id": project["id"],
                    "path_with_namespace": project["path_with_namespace"],
                    "description": project["description"],
                    "visibility": project["visibility"],
                    "result_handle": handle,
                    "project_generation": self.state["_project_generation"].get(project["path_with_namespace"], 1),
                })

        return {
            "total_count": len(matches),
            "query_epoch": self.state["_query_epoch"],
            "items": matches[(page-1)*per_page : page*per_page],
        }

    # =========================================================================
    # Tool 2: create_repository
    # =========================================================================

    def create_repository(
        self,
        name: str,
        description: str = "",
        visibility: str = "private",
        initialize_with_readme: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new GitLab project.

        Args:
            name (str): Project name
            description (str): Project description
            visibility (str): Visibility level (public, internal, private)
            initialize_with_readme (bool): Initialize with a README file

        Returns:
            dict: Created project details
        """
        new_project = {
            "id": len(self.state["projects"]) + 200,
            "name": name,
            "path_with_namespace": f"benchmark-user/{name}",
            "description": description,
            "visibility": visibility,
            "default_branch": "main",
            "branches": ["main"],
            "files": {"main": {"README.md": f"# {name}\n\n{description}"}} if initialize_with_readme else {"main": {}},
            "issues": [],
            "merge_requests": [],
        }
        self.state["projects"].append(new_project)
        self.state["_project_generation"][new_project["path_with_namespace"]] = 1
        return {
            "id": new_project["id"],
            "path_with_namespace": new_project["path_with_namespace"],
            "description": new_project["description"],
            "visibility": new_project["visibility"],
            "web_url": f"https://gitlab.com/{new_project['path_with_namespace']}",
        }

    # =========================================================================
    # Tool 3: fork_repository
    # =========================================================================

    def fork_repository(self, project_id, namespace: str = None) -> Dict[str, Any]:
        """
        Fork a GitLab project to your account or specified namespace.

        Args:
            project_id: Project ID or path
            namespace (str): Optional namespace to fork into

        Returns:
            dict: Forked project details
        """
        source = self._find_project(project_id)
        if not source:
            return {"error": f"Project {project_id} not found"}

        fork_namespace = namespace or "benchmark-user"
        forked = {
            "id": len(self.state["projects"]) + 200,
            "name": source["name"],
            "path_with_namespace": f"{fork_namespace}/{source['name']}",
            "description": source["description"],
            "visibility": source["visibility"],
            "default_branch": source["default_branch"],
            "branches": list(source["branches"]),
            "files": dict(source["files"]),
            "issues": [],
            "merge_requests": [],
            "forked_from_id": source["id"],
        }
        self.state["projects"].append(forked)
        self.state["_project_generation"][forked["path_with_namespace"]] = 1
        return {
            "id": forked["id"],
            "path_with_namespace": forked["path_with_namespace"],
            "forked_from_id": source["id"],
        }

    # =========================================================================
    # Tool 4: get_file_contents
    # =========================================================================

    def get_file_contents(self, project_id, file_path: str, ref: str = None) -> Dict[str, Any]:
        """
        Get the contents of a file or directory from a GitLab project.

        Args:
            project_id: Project ID or path
            file_path (str): Path to file
            ref (str): Branch or commit ref (defaults to default branch)

        Returns:
            dict: File contents
        """
        project = self._find_project(project_id)
        if not project:
            return {"error": f"Project {project_id} not found"}

        branch = ref or project["default_branch"]
        if branch not in project["files"]:
            return {"error": f"Ref {branch} not found"}

        files = project["files"][branch]
        if file_path in files:
            import base64
            content = files[file_path]
            return {
                "file_name": file_path.split("/")[-1],
                "file_path": file_path,
                "content": base64.b64encode(content.encode()).decode(),
                "content_decoded": content,
                "encoding": "base64",
                "ref": branch,
            }

        return {"error": f"File {file_path} not found in project"}

    # =========================================================================
    # Tool 5: create_or_update_file
    # =========================================================================

    def create_or_update_file(
        self,
        project_id,
        file_path: str,
        content: str,
        commit_message: str,
        branch: str = None,
        previous_path: str = None
    ) -> Dict[str, Any]:
        """
        Create or update a single file in a GitLab project.

        Args:
            project_id: Project ID or path
            file_path (str): Path to file
            content (str): File content
            commit_message (str): Commit message
            branch (str): Branch name (defaults to default branch)
            previous_path (str): Previous file path (for renames)

        Returns:
            dict: Commit details
        """
        project = self._find_project(project_id)
        if not project:
            return {"error": f"Project {project_id} not found"}

        branch = branch or project["default_branch"]
        if branch not in project["files"]:
            project["files"][branch] = {}

        # Handle rename
        if previous_path and previous_path in project["files"][branch]:
            del project["files"][branch][previous_path]

        project["files"][branch][file_path] = content

        return {
            "file_path": file_path,
            "branch": branch,
            "commit_id": "gitlab_commit_abc123",
            "commit_message": commit_message,
        }

    # =========================================================================
    # Tool 6: push_files
    # =========================================================================

    def push_files(
        self,
        project_id,
        files: List[Dict[str, str]],
        commit_message: str,
        branch: str
    ) -> Dict[str, Any]:
        """
        Push multiple files to a GitLab project in a single commit.

        Args:
            project_id: Project ID or path
            files (List[Dict]): List of files with 'path' and 'content' keys
            commit_message (str): Commit message
            branch (str): Branch name

        Returns:
            dict: Commit details
        """
        project = self._find_project(project_id)
        if not project:
            return {"error": f"Project {project_id} not found"}

        if branch not in project["files"]:
            project["files"][branch] = {}

        for f in files:
            file_path = f.get("path") or f.get("file_path")
            project["files"][branch][file_path] = f["content"]

        return {
            "branch": branch,
            "commit_id": "gitlab_multicommit_xyz789",
            "commit_message": commit_message,
            "files_changed": len(files),
        }

    # =========================================================================
    # Tool 7: create_branch
    # =========================================================================

    def create_branch(self, project_id, branch: str, ref: str = None) -> Dict[str, Any]:
        """
        Create a new branch in a GitLab project.

        Args:
            project_id: Project ID or path
            branch (str): New branch name
            ref (str): Source ref (defaults to default branch)

        Returns:
            dict: Branch creation result
        """
        project = self._find_project(project_id)
        if not project:
            return {"error": f"Project {project_id} not found"}

        source = ref or project["default_branch"]
        if source not in project["branches"]:
            return {"error": f"Source ref {source} not found"}

        if branch in project["branches"]:
            return {"error": f"Branch {branch} already exists"}

        project["branches"].append(branch)
        project["files"][branch] = dict(project["files"].get(source, {}))

        return {
            "name": branch,
            "commit_id": "gitlab_branch_commit_123",
            "created_from": source,
        }

    # =========================================================================
    # Tool 8: create_issue
    # =========================================================================

    def create_issue(
        self,
        project_id,
        title: str,
        description: str = "",
        labels: List[str] = None,
        assignee_ids: List[int] = None,
        milestone_id: int = None
    ) -> Dict[str, Any]:
        """
        Create a new issue in a GitLab project.

        NOTE: Unlike GitHub, GitLab MCP does NOT provide get_issue, list_issues,
        update_issue, or add_issue_comment. You can only CREATE issues.

        Args:
            project_id: Project ID or path
            title (str): Issue title
            description (str): Issue description
            labels (List[str]): Labels to apply
            assignee_ids (List[int]): User IDs to assign
            milestone_id (int): Milestone ID

        Returns:
            dict: Created issue details
        """
        project = self._find_project(project_id)
        if not project:
            return {"error": f"Project {project_id} not found"}

        issue_iid = self.state["next_issue_iid"]
        self.state["next_issue_iid"] += 1

        new_issue = {
            "iid": issue_iid,
            "title": title,
            "description": description,
            "state": "opened",
            "labels": labels or [],
            "assignee_ids": assignee_ids or [],
            "milestone_id": milestone_id,
            "created_at": "2024-01-20T12:00:00Z",
        }
        project["issues"].append(new_issue)
        self.state["_project_generation"][project["path_with_namespace"]] = self.state["_project_generation"].get(project["path_with_namespace"], 1) + 1

        return {
            "iid": issue_iid,
            "project_id": project["id"],
            "title": title,
            "state": "opened",
            "web_url": f"https://gitlab.com/{project['path_with_namespace']}/-/issues/{issue_iid}",
        }

    # =========================================================================
    # Tool 9: create_merge_request
    # =========================================================================

    def create_merge_request(
        self,
        project_id,
        title: str,
        description: str,
        source_branch: str,
        target_branch: str,
        allow_collaboration: bool = True,
        draft: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new merge request in a GitLab project.

        NOTE: Unlike GitHub, GitLab MCP does NOT provide get_merge_request,
        list_merge_requests, or merge_merge_request. You can only CREATE MRs.

        Args:
            project_id: Project ID or path
            title (str): MR title
            description (str): MR description
            source_branch (str): Source branch
            target_branch (str): Target branch
            allow_collaboration (bool): Allow commits from members who can merge
            draft (bool): Create as draft MR

        Returns:
            dict: Created merge request details
        """
        project = self._find_project(project_id)
        if not project:
            return {"error": f"Project {project_id} not found"}

        if source_branch not in project["branches"]:
            return {"error": f"Source branch {source_branch} not found"}
        if target_branch not in project["branches"]:
            return {"error": f"Target branch {target_branch} not found"}

        mr_iid = self.state["next_mr_iid"]
        self.state["next_mr_iid"] += 1

        new_mr = {
            "iid": mr_iid,
            "title": title,
            "description": description,
            "state": "opened",
            "source_branch": source_branch,
            "target_branch": target_branch,
            "author_id": 2000,
            "created_at": "2024-01-20T12:00:00Z",
            "merge_status": "can_be_merged",
            "allow_collaboration": allow_collaboration,
            "draft": draft,
        }
        project["merge_requests"].append(new_mr)
        self.state["_project_generation"][project["path_with_namespace"]] = self.state["_project_generation"].get(project["path_with_namespace"], 1) + 1

        return {
            "iid": mr_iid,
            "project_id": project["id"],
            "title": title,
            "state": "opened",
            "web_url": f"https://gitlab.com/{project['path_with_namespace']}/-/merge_requests/{mr_iid}",
        }
