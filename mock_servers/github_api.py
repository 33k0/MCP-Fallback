# GitHub MCP Server Mock
# Based on real GitHub MCP server tool schemas from modelcontextprotocol/servers-archived

from typing import List, Dict, Any, Optional

DEFAULT_STATE = {
    "authenticated": False,
    "user": None,
    "repositories": [
        {
            "id": 1,
            "owner": "acme-corp",
            "name": "web-app",
            "full_name": "acme-corp/web-app",
            "description": "Main web application repository",
            "private": False,
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
                    "number": 1,
                    "title": "Fix login button not working",
                    "body": "The login button doesn't respond to clicks on mobile devices.",
                    "state": "open",
                    "labels": ["bug", "mobile"],
                    "assignees": ["john-dev"],
                    "created_at": "2024-01-15T10:30:00Z",
                },
                {
                    "number": 2,
                    "title": "Add dark mode support",
                    "body": "Users have requested a dark mode theme option.",
                    "state": "open",
                    "labels": ["enhancement", "ui"],
                    "assignees": [],
                    "created_at": "2024-01-16T14:20:00Z",
                },
            ],
            "pull_requests": [
                {
                    "number": 10,
                    "title": "Add user authentication",
                    "body": "Implements OAuth2 authentication flow.",
                    "state": "open",
                    "head": "feature/login",
                    "base": "main",
                    "author": "jane-dev",
                    "created_at": "2024-01-17T09:00:00Z",
                    "mergeable": True,
                    "files_changed": ["src/auth.js", "src/login.js"],
                    "reviews": [],
                    "comments": [],
                },
            ],
        },
        {
            "id": 2,
            "owner": "acme-corp",
            "name": "api-service",
            "full_name": "acme-corp/api-service",
            "description": "Backend API service",
            "private": True,
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
                    "number": 1,
                    "title": "API rate limiting needed",
                    "body": "We need to implement rate limiting to prevent abuse.",
                    "state": "open",
                    "labels": ["security", "enhancement"],
                    "assignees": ["john-dev"],
                    "created_at": "2024-01-18T11:00:00Z",
                },
            ],
            "pull_requests": [],
        },
    ],
    "next_issue_id": 100,
    "next_pr_id": 100,
}


class GitHubAPI:
    """
    Mock GitHub MCP Server.
    Provides tools for managing repositories, issues, pull requests, and files.
    """

    def __init__(self):
        self.state = None
        self._load_scenario({})

    def _load_scenario(self, scenario: dict):
        """Load a scenario state or reset to default."""
        import copy
        self.state = copy.deepcopy(DEFAULT_STATE)
        self.state.update(scenario)

    def _find_repo(self, owner: str, repo: str) -> Optional[Dict]:
        """Find a repository by owner and name."""
        for r in self.state["repositories"]:
            if r["owner"] == owner and r["name"] == repo:
                return r
        return None

    # =========================================================================
    # Authentication
    # =========================================================================

    def github_authenticate(self, token: str) -> Dict[str, Any]:
        """
        Authenticate with GitHub using a personal access token.

        Args:
            token (str): GitHub personal access token

        Returns:
            dict: Authentication result with user info
        """
        # Always succeed for benchmark purposes
        self.state["authenticated"] = True
        self.state["user"] = {
            "login": "benchmark-user",
            "id": 12345,
            "name": "Benchmark User",
            "email": "user@example.com",
        }
        return {
            "success": True,
            "user": self.state["user"],
        }

    # =========================================================================
    # Repository Operations
    # =========================================================================

    def search_repositories(self, query: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Search for GitHub repositories.

        Args:
            query (str): Search query string
            page (int): Page number for pagination
            per_page (int): Number of results per page

        Returns:
            dict: Search results with matching repositories
        """
        query_lower = query.lower()
        matches = []
        for repo in self.state["repositories"]:
            if (query_lower in repo["name"].lower() or
                query_lower in repo.get("description", "").lower()):
                matches.append({
                    "id": repo["id"],
                    "full_name": repo["full_name"],
                    "description": repo["description"],
                    "private": repo["private"],
                })

        return {
            "total_count": len(matches),
            "items": matches[(page-1)*per_page : page*per_page],
        }

    def create_repository(
        self,
        name: str,
        description: str = "",
        private: bool = False,
        auto_init: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new GitHub repository in your account.

        Args:
            name (str): Repository name
            description (str): Repository description
            private (bool): Whether the repository should be private
            auto_init (bool): Initialize with a README

        Returns:
            dict: Created repository details
        """
        new_repo = {
            "id": len(self.state["repositories"]) + 100,
            "owner": "benchmark-user",
            "name": name,
            "full_name": f"benchmark-user/{name}",
            "description": description,
            "private": private,
            "default_branch": "main",
            "branches": ["main"],
            "files": {"main": {"README.md": f"# {name}\n\n{description}"}} if auto_init else {"main": {}},
            "issues": [],
            "pull_requests": [],
        }
        self.state["repositories"].append(new_repo)
        return {
            "id": new_repo["id"],
            "full_name": new_repo["full_name"],
            "description": new_repo["description"],
            "private": new_repo["private"],
            "html_url": f"https://github.com/{new_repo['full_name']}",
        }

    def fork_repository(self, owner: str, repo: str, organization: str = None) -> Dict[str, Any]:
        """
        Fork a GitHub repository to your account or specified organization.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            organization (str): Optional organization to fork to

        Returns:
            dict: Forked repository details
        """
        source = self._find_repo(owner, repo)
        if not source:
            return {"error": f"Repository {owner}/{repo} not found"}

        fork_owner = organization or "benchmark-user"
        forked = {
            "id": len(self.state["repositories"]) + 100,
            "owner": fork_owner,
            "name": repo,
            "full_name": f"{fork_owner}/{repo}",
            "description": source["description"],
            "private": source["private"],
            "default_branch": source["default_branch"],
            "branches": list(source["branches"]),
            "files": dict(source["files"]),
            "issues": [],
            "pull_requests": [],
            "forked_from": source["full_name"],
        }
        self.state["repositories"].append(forked)
        return {
            "id": forked["id"],
            "full_name": forked["full_name"],
            "forked_from": source["full_name"],
        }

    # =========================================================================
    # File Operations
    # =========================================================================

    def get_file_contents(self, owner: str, repo: str, path: str, ref: str = None) -> Dict[str, Any]:
        """
        Get the contents of a file or directory from a GitHub repository.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            path (str): Path to file or directory
            ref (str): Branch or commit ref (defaults to default branch)

        Returns:
            dict: File contents or directory listing
        """
        repository = self._find_repo(owner, repo)
        if not repository:
            return {"error": f"Repository {owner}/{repo} not found"}

        branch = ref or repository["default_branch"]
        if branch not in repository["files"]:
            return {"error": f"Branch {branch} not found"}

        files = repository["files"][branch]
        if path in files:
            content = files[path]
            return {
                "name": path.split("/")[-1],
                "path": path,
                "type": "file",
                "content": content,
                "encoding": "utf-8",
            }

        # Check if it's a directory
        dir_contents = [f for f in files.keys() if f.startswith(path + "/") or path == ""]
        if dir_contents:
            return {
                "path": path,
                "type": "dir",
                "contents": [{"name": f.split("/")[-1], "path": f} for f in dir_contents],
            }

        return {"error": f"Path {path} not found in {owner}/{repo}"}

    def create_or_update_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str = None,
        sha: str = None
    ) -> Dict[str, Any]:
        """
        Create or update a single file in a GitHub repository.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            path (str): Path to file
            content (str): File content
            message (str): Commit message
            branch (str): Branch name (defaults to default branch)
            sha (str): SHA of file being replaced (for updates)

        Returns:
            dict: Commit details
        """
        repository = self._find_repo(owner, repo)
        if not repository:
            return {"error": f"Repository {owner}/{repo} not found"}

        branch = branch or repository["default_branch"]
        if branch not in repository["files"]:
            repository["files"][branch] = {}

        repository["files"][branch][path] = content

        return {
            "content": {
                "name": path.split("/")[-1],
                "path": path,
                "sha": "abc123def456",
            },
            "commit": {
                "sha": "commit789xyz",
                "message": message,
            },
        }

    def push_files(
        self,
        owner: str,
        repo: str,
        branch: str,
        files: List[Dict[str, str]],
        message: str
    ) -> Dict[str, Any]:
        """
        Push multiple files to a GitHub repository in a single commit.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            branch (str): Branch name
            files (List[Dict]): List of files with 'path' and 'content' keys
            message (str): Commit message

        Returns:
            dict: Commit details
        """
        repository = self._find_repo(owner, repo)
        if not repository:
            return {"error": f"Repository {owner}/{repo} not found"}

        if branch not in repository["files"]:
            repository["files"][branch] = {}

        for f in files:
            repository["files"][branch][f["path"]] = f["content"]

        return {
            "commit": {
                "sha": "multicommit123",
                "message": message,
                "files_changed": len(files),
            },
        }

    # =========================================================================
    # Branch Operations
    # =========================================================================

    def create_branch(self, owner: str, repo: str, branch: str, from_branch: str = None) -> Dict[str, Any]:
        """
        Create a new branch in a GitHub repository.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            branch (str): New branch name
            from_branch (str): Source branch (defaults to default branch)

        Returns:
            dict: Branch creation result
        """
        repository = self._find_repo(owner, repo)
        if not repository:
            return {"error": f"Repository {owner}/{repo} not found"}

        source = from_branch or repository["default_branch"]
        if source not in repository["branches"]:
            return {"error": f"Source branch {source} not found"}

        if branch in repository["branches"]:
            return {"error": f"Branch {branch} already exists"}

        repository["branches"].append(branch)
        repository["files"][branch] = dict(repository["files"].get(source, {}))

        return {
            "ref": f"refs/heads/{branch}",
            "created_from": source,
        }

    def list_commits(
        self,
        owner: str,
        repo: str,
        branch: str = None,
        per_page: int = 10
    ) -> Dict[str, Any]:
        """
        Get list of commits of a branch in a GitHub repository.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            branch (str): Branch name (defaults to default branch)
            per_page (int): Number of commits to return

        Returns:
            dict: List of commits
        """
        repository = self._find_repo(owner, repo)
        if not repository:
            return {"error": f"Repository {owner}/{repo} not found"}

        # Return mock commits
        return {
            "commits": [
                {
                    "sha": "abc123",
                    "message": "Initial commit",
                    "author": "benchmark-user",
                    "date": "2024-01-01T00:00:00Z",
                },
                {
                    "sha": "def456",
                    "message": "Add feature",
                    "author": "benchmark-user",
                    "date": "2024-01-02T00:00:00Z",
                },
            ],
        }

    # =========================================================================
    # Issue Operations
    # =========================================================================

    def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str = "",
        labels: List[str] = None,
        assignees: List[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new issue in a GitHub repository.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            title (str): Issue title
            body (str): Issue body/description
            labels (List[str]): Labels to apply
            assignees (List[str]): Users to assign

        Returns:
            dict: Created issue details
        """
        repository = self._find_repo(owner, repo)
        if not repository:
            return {"error": f"Repository {owner}/{repo} not found"}

        issue_number = self.state["next_issue_id"]
        self.state["next_issue_id"] += 1

        new_issue = {
            "number": issue_number,
            "title": title,
            "body": body,
            "state": "open",
            "labels": labels or [],
            "assignees": assignees or [],
            "created_at": "2024-01-20T12:00:00Z",
        }
        repository["issues"].append(new_issue)

        return {
            "number": issue_number,
            "title": title,
            "state": "open",
            "html_url": f"https://github.com/{owner}/{repo}/issues/{issue_number}",
        }

    def get_issue(self, owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
        """
        Get details of a specific issue in a GitHub repository.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            issue_number (int): Issue number

        Returns:
            dict: Issue details
        """
        repository = self._find_repo(owner, repo)
        if not repository:
            return {"error": f"Repository {owner}/{repo} not found"}

        for issue in repository["issues"]:
            if issue["number"] == issue_number:
                return issue

        return {"error": f"Issue #{issue_number} not found"}

    def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: str = None,
        per_page: int = 10
    ) -> Dict[str, Any]:
        """
        List issues in a GitHub repository with filtering options.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            state (str): Filter by state (open, closed, all)
            labels (str): Comma-separated list of labels to filter by
            per_page (int): Number of results per page

        Returns:
            dict: List of issues
        """
        repository = self._find_repo(owner, repo)
        if not repository:
            return {"error": f"Repository {owner}/{repo} not found"}

        issues = repository["issues"]

        if state != "all":
            issues = [i for i in issues if i["state"] == state]

        if labels:
            label_list = [l.strip() for l in labels.split(",")]
            issues = [i for i in issues if any(l in i["labels"] for l in label_list)]

        return {
            "total_count": len(issues),
            "items": issues[:per_page],
        }

    def update_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        title: str = None,
        body: str = None,
        state: str = None,
        labels: List[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing issue in a GitHub repository.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            issue_number (int): Issue number
            title (str): New title
            body (str): New body
            state (str): New state (open/closed)
            labels (List[str]): New labels

        Returns:
            dict: Updated issue details
        """
        repository = self._find_repo(owner, repo)
        if not repository:
            return {"error": f"Repository {owner}/{repo} not found"}

        for issue in repository["issues"]:
            if issue["number"] == issue_number:
                if title:
                    issue["title"] = title
                if body:
                    issue["body"] = body
                if state:
                    issue["state"] = state
                if labels is not None:
                    issue["labels"] = labels
                return issue

        return {"error": f"Issue #{issue_number} not found"}

    def add_issue_comment(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        body: str
    ) -> Dict[str, Any]:
        """
        Add a comment to an existing issue.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            issue_number (int): Issue number
            body (str): Comment body

        Returns:
            dict: Created comment details
        """
        repository = self._find_repo(owner, repo)
        if not repository:
            return {"error": f"Repository {owner}/{repo} not found"}

        for issue in repository["issues"]:
            if issue["number"] == issue_number:
                return {
                    "id": 99999,
                    "body": body,
                    "user": "benchmark-user",
                    "created_at": "2024-01-20T12:00:00Z",
                }

        return {"error": f"Issue #{issue_number} not found"}

    # =========================================================================
    # Pull Request Operations
    # =========================================================================

    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str
    ) -> Dict[str, Any]:
        """
        Create a new pull request in a GitHub repository.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            title (str): PR title
            body (str): PR description
            head (str): Head branch (source)
            base (str): Base branch (target)

        Returns:
            dict: Created pull request details
        """
        repository = self._find_repo(owner, repo)
        if not repository:
            return {"error": f"Repository {owner}/{repo} not found"}

        if head not in repository["branches"]:
            return {"error": f"Head branch {head} not found"}
        if base not in repository["branches"]:
            return {"error": f"Base branch {base} not found"}

        pr_number = self.state["next_pr_id"]
        self.state["next_pr_id"] += 1

        new_pr = {
            "number": pr_number,
            "title": title,
            "body": body,
            "state": "open",
            "head": head,
            "base": base,
            "author": "benchmark-user",
            "created_at": "2024-01-20T12:00:00Z",
            "mergeable": True,
            "files_changed": [],
            "reviews": [],
            "comments": [],
        }
        repository["pull_requests"].append(new_pr)

        return {
            "number": pr_number,
            "title": title,
            "state": "open",
            "html_url": f"https://github.com/{owner}/{repo}/pull/{pr_number}",
        }

    def get_pull_request(self, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
        """
        Get details of a specific pull request.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            pull_number (int): Pull request number

        Returns:
            dict: Pull request details
        """
        repository = self._find_repo(owner, repo)
        if not repository:
            return {"error": f"Repository {owner}/{repo} not found"}

        for pr in repository["pull_requests"]:
            if pr["number"] == pull_number:
                return pr

        return {"error": f"Pull request #{pull_number} not found"}

    def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        per_page: int = 10
    ) -> Dict[str, Any]:
        """
        List and filter repository pull requests.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            state (str): Filter by state (open, closed, all)
            per_page (int): Number of results per page

        Returns:
            dict: List of pull requests
        """
        repository = self._find_repo(owner, repo)
        if not repository:
            return {"error": f"Repository {owner}/{repo} not found"}

        prs = repository["pull_requests"]

        if state != "all":
            prs = [pr for pr in prs if pr["state"] == state]

        return {
            "total_count": len(prs),
            "items": prs[:per_page],
        }

    def merge_pull_request(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        commit_title: str = None,
        merge_method: str = "merge"
    ) -> Dict[str, Any]:
        """
        Merge a pull request.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            pull_number (int): Pull request number
            commit_title (str): Custom merge commit title
            merge_method (str): Merge method (merge, squash, rebase)

        Returns:
            dict: Merge result
        """
        repository = self._find_repo(owner, repo)
        if not repository:
            return {"error": f"Repository {owner}/{repo} not found"}

        for pr in repository["pull_requests"]:
            if pr["number"] == pull_number:
                if pr["state"] != "open":
                    return {"error": "Pull request is not open"}
                if not pr.get("mergeable", True):
                    return {"error": "Pull request is not mergeable"}

                pr["state"] = "merged"
                return {
                    "merged": True,
                    "sha": "mergecommit123",
                    "message": commit_title or f"Merge pull request #{pull_number}",
                }

        return {"error": f"Pull request #{pull_number} not found"}

    # =========================================================================
    # Search Operations
    # =========================================================================

    def search_code(self, query: str, per_page: int = 10) -> Dict[str, Any]:
        """
        Search for code across GitHub repositories.

        Args:
            query (str): Search query
            per_page (int): Number of results per page

        Returns:
            dict: Search results
        """
        results = []
        query_lower = query.lower()

        for repo in self.state["repositories"]:
            for branch, files in repo["files"].items():
                for path, content in files.items():
                    if query_lower in content.lower():
                        results.append({
                            "repository": repo["full_name"],
                            "path": path,
                            "branch": branch,
                        })

        return {
            "total_count": len(results),
            "items": results[:per_page],
        }

    def search_issues(self, query: str, per_page: int = 10) -> Dict[str, Any]:
        """
        Search for issues and pull requests across GitHub repositories.

        Args:
            query (str): Search query
            per_page (int): Number of results per page

        Returns:
            dict: Search results
        """
        results = []
        query_lower = query.lower()

        for repo in self.state["repositories"]:
            for issue in repo["issues"]:
                if (query_lower in issue["title"].lower() or
                    query_lower in issue.get("body", "").lower()):
                    results.append({
                        "repository": repo["full_name"],
                        "number": issue["number"],
                        "title": issue["title"],
                        "state": issue["state"],
                        "type": "issue",
                    })
            for pr in repo["pull_requests"]:
                if (query_lower in pr["title"].lower() or
                    query_lower in pr.get("body", "").lower()):
                    results.append({
                        "repository": repo["full_name"],
                        "number": pr["number"],
                        "title": pr["title"],
                        "state": pr["state"],
                        "type": "pull_request",
                    })

        return {
            "total_count": len(results),
            "items": results[:per_page],
        }

    def search_users(self, query: str, per_page: int = 10) -> Dict[str, Any]:
        """
        Search for users on GitHub.

        Args:
            query (str): Search query
            per_page (int): Number of results per page

        Returns:
            dict: Search results
        """
        # Mock user search results
        return {
            "total_count": 2,
            "items": [
                {"login": "john-dev", "id": 1001, "type": "User"},
                {"login": "jane-dev", "id": 1002, "type": "User"},
            ],
        }
