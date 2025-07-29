import asyncio
import os
import json
import re
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse

from github import Github, GithubException, Auth, GithubIntegration
from github.Repository import Repository
from github.ContentFile import ContentFile
from pydantic import AnyUrl, BaseModel, Field, field_validator, ConfigDict

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions
from mcp.server import Server
import mcp.server.stdio

# Authentication methods supported
class AuthMethod(str, Enum):
    TOKEN = "token"  # Personal Access Token
    USERNAME_TOKEN = "username_token"  # Username + Personal Access Token (for 2FA)
    APP = "app"  # GitHub App authentication

# Model for storing GitHub connection information
class GitHubConnection(BaseModel):
    name: str
    url: str
    auth_method: AuthMethod = AuthMethod.TOKEN
    token: str = ""
    username: Optional[str] = None
    otp_code: Optional[str] = None  # One-time password for 2FA
    app_id: Optional[str] = None
    private_key: Optional[str] = None
    installation_id: Optional[int] = None
    repositories: Dict[str, Any] = Field(default_factory=dict)
    requires_2fa: bool = False
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    @field_validator('url')
    def validate_enterprise_url(cls, v):
        """Ensure URL is properly formatted for GitHub Enterprise"""
        # Parse the URL to extract components
        parsed = urlparse(v)
        
        # If no scheme is provided, assume https
        if not parsed.scheme:
            v = f"https://{v}"
            parsed = urlparse(v)
        
        # Handle GitHub.com URLs specially
        if "github.com" in parsed.netloc:
            # For api.github.com, keep as is - it's already the correct API endpoint
            if parsed.netloc == "api.github.com":
                return v
                
            # For github.com (exact match only), use api.github.com
            if parsed.netloc == "github.com":
                return "https://api.github.com"
                
            # For subdomains of github.com, treat like a GitHub Enterprise server
            # This handles cases like "subdomain.github.com"
        
        # For GitHub Enterprise or subdomains
        # Check if URL already has API path
        has_api_v3 = "/api/v3" in parsed.path
        has_api = "/api" in parsed.path and not has_api_v3
        
        # If no API path, use just /api (newer GitHub Enterprise format)
        # This is more likely to work with modern GitHub Enterprise instances
        if not has_api_v3 and not has_api:
            if v.endswith('/'):
                v = f"{v}api"
            else:
                v = f"{v}/api"
                    
        return v
        
    def get_github_client(self):
        """Create a GitHub client with the appropriate authentication method"""
        if self.auth_method == AuthMethod.TOKEN:
            # Simple token authentication
            return Github(
                auth=Auth.Token(self.token), 
                base_url=self.url
            )
        
        elif self.auth_method == AuthMethod.USERNAME_TOKEN:
            # Username + token (for 2FA)
            if self.otp_code:
                # When 2FA is enabled and OTP is provided
                headers = {"X-GitHub-OTP": self.otp_code}
                return Github(
                    auth=Auth.Login(self.username, self.token), 
                    base_url=self.url,
                    headers=headers
                )
            else:
                # Without OTP
                return Github(
                    auth=Auth.Login(self.username, self.token),
                    base_url=self.url
                )
        
        elif self.auth_method == AuthMethod.APP:
            # GitHub App authentication
            if not self.app_id or not self.private_key or not self.installation_id:
                raise ValueError("GitHub App authentication requires app_id, private_key, and installation_id")
                
            integration = GithubIntegration(
                self.app_id,
                self.private_key,
                base_url=self.url
            )
            auth_token = integration.get_access_token(self.installation_id)
            return Github(
                auth=Auth.Token(auth_token.token), 
                base_url=self.url
            )
        
        else:
            raise ValueError(f"Unsupported authentication method: {self.auth_method}")
    
# Store GitHub connections
connections: Dict[str, GitHubConnection] = {}
current_connection: Optional[str] = None

server = Server("github-enterprise-mcp")

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """
    List available GitHub Enterprise repositories as resources.
    Each repository is exposed as a resource with a custom github:// URI scheme.
    """
    resources = []
    
    if not connections:
        return resources
    
    if not current_connection:
        return resources
        
    connection = connections[current_connection]
    github_client = connection.get_github_client()
    
    try:
        for repo in github_client.get_user().get_repos():
            connection.repositories[repo.name] = repo
            resources.append(
                types.Resource(
                    uri=AnyUrl(f"github://{connection.name}/{repo.name}"),
                    name=f"Repository: {repo.name}",
                    description=repo.description or f"GitHub repository: {repo.name}",
                    mimeType="application/github-repository",
                )
            )
    except GithubException as e:
        pass  # Handle exception appropriately
        
    return resources

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """
    Read a specific repository's content by its URI.
    Returns repository information as formatted text.
    """
    if uri.scheme != "github":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    # Extract connection name and repo name from URI path
    parts = uri.path.strip("/").split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub resource URI: {uri}")
    
    conn_name = parts[0]
    repo_name = parts[1]
    
    if conn_name not in connections:
        raise ValueError(f"Connection not found: {conn_name}")
    
    connection = connections[conn_name]
    
    # Use cached repository if available, otherwise fetch it
    if repo_name in connection.repositories:
        repo = connection.repositories[repo_name]
    else:
        github_client = connection.get_github_client()
        try:
            repo = github_client.get_user().get_repo(repo_name)
            connection.repositories[repo_name] = repo
        except GithubException as e:
            raise ValueError(f"Repository not found: {repo_name}. Error: {str(e)}")
    
    # Format repository information
    return f"""
Repository: {repo.name}
Owner: {repo.owner.login}
Description: {repo.description or 'No description'}
URL: {repo.html_url}
Default Branch: {repo.default_branch}
Stars: {repo.stargazers_count}
Forks: {repo.forks_count}
Open Issues: {repo.open_issues_count}
    """

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available GitHub Enterprise tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        types.Tool(
            name="test-api-connection",
            description="Test connection to a GitHub API endpoint without storing credentials",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string", 
                        "description": "GitHub Enterprise URL to test (e.g., https://github.com, https://api.github.com, https://github.example.com). The tool will automatically test multiple API formats (/api or /api/v3) to determine which one works for your GitHub Enterprise instance."
                    },
                },
                "required": ["url"],
            },
        ),
        types.Tool(
            name="connect-github-enterprise",
            description="Connect to a GitHub Enterprise instance using a personal access token",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string", 
                        "description": "A name for this connection (e.g., 'my-enterprise')"
                    },
                    "url": {
                        "type": "string", 
                        "description": "GitHub Enterprise URL (e.g., https://github.example.com). For GitHub.com, use github.com or api.github.com. For GitHub Enterprise, you can use the base URL, /api, or /api/v3 endpoints."
                    },
                    "token": {
                        "type": "string", 
                        "description": "Personal Access Token with repo, read:org, user scopes (classic token or fine-grained token with repository access)"
                    },
                },
                "required": ["name", "url", "token"],
            },
        ),
        types.Tool(
            name="connect-github-enterprise-2fa",
            description="Connect to a GitHub Enterprise instance with two-factor authentication",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string", 
                        "description": "A name for this connection (e.g., 'my-enterprise')"
                    },
                    "url": {
                        "type": "string", 
                        "description": "GitHub Enterprise URL (e.g., https://github.example.com). For GitHub.com, use github.com or api.github.com. For GitHub Enterprise, you can use the base URL, /api, or /api/v3 endpoints."
                    },
                    "username": {
                        "type": "string", 
                        "description": "GitHub Enterprise username"
                    },
                    "token": {
                        "type": "string", 
                        "description": "Personal Access Token or password (token is strongly recommended over password)"
                    },
                    "otp_code": {
                        "type": "string", 
                        "description": "One-time password from your authenticator app for 2FA"
                    }
                },
                "required": ["name", "url", "username", "token", "otp_code"],
            },
        ),
        types.Tool(
            name="list-repositories",
            description="List repositories from the connected GitHub Enterprise instance",
            inputSchema={
                "type": "object",
                "properties": {
                    "connection": {"type": "string", "description": "Connection name to use"},
                },
                "required": ["connection"],
            },
        ),
        types.Tool(
            name="create-branch",
            description="Create a new branch in a repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "repository": {"type": "string", "description": "Repository name"},
                    "base_branch": {"type": "string", "description": "Base branch name (usually main or master)"},
                    "new_branch": {"type": "string", "description": "New branch name to create"},
                },
                "required": ["repository", "base_branch", "new_branch"],
            },
        ),
        types.Tool(
            name="commit-and-push",
            description="Commit file changes and push to a branch",
            inputSchema={
                "type": "object",
                "properties": {
                    "repository": {"type": "string", "description": "Repository name"},
                    "branch": {"type": "string", "description": "Branch name to commit to"},
                    "file_path": {"type": "string", "description": "Path to the file within the repository"},
                    "content": {"type": "string", "description": "New content for the file"},
                    "commit_message": {"type": "string", "description": "Commit message"},
                },
                "required": ["repository", "branch", "file_path", "content", "commit_message"],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests for GitHub Enterprise operations.
    Tools can modify server state and notify clients of changes.
    """
    global current_connection
    
    if not arguments:
        raise ValueError("Missing arguments")
        
    if name == "test-api-connection":
        url = arguments.get("url")
        
        if not url:
            raise ValueError("Missing URL parameter")
            
        # Parse the URL to extract components
        parsed = urlparse(url)
        
        # If no scheme is provided, assume https
        if not parsed.scheme:
            url = f"https://{url}"
            parsed = urlparse(url)
            
        # Build list of endpoints to test
        endpoints_to_test = []
        
        # For GitHub.com URLs
        if "github.com" in parsed.netloc:
            # For api.github.com, test directly
            if parsed.netloc == "api.github.com":
                base = "https://api.github.com"
                endpoints_to_test.append(base)
            # For github.com, test using api.github.com
            else:
                base = "https://api.github.com"
                endpoints_to_test.append(base)
        # For GitHub Enterprise URLs
        else:
            base = url.rstrip('/')
            
            # Check if URL already contains API path
            has_api_v3 = "/api/v3" in parsed.path
            has_api = "/api" in parsed.path and not has_api_v3
            
            # Add the provided URL first
            if has_api_v3 or has_api:
                endpoints_to_test.append(base)
            
            # Then add candidates for alternate formats
            if not has_api and not has_api_v3:
                # Modern format with just /api (preferred for newer GitHub Enterprise instances)
                endpoints_to_test.append(f"{base}/api")
                # Legacy format with /api/v3
                endpoints_to_test.append(f"{base}/api/v3")
                # Base URL as fallback
                endpoints_to_test.append(base)
            elif has_api and not has_api_v3:
                # Test legacy format too
                endpoints_to_test.append(f"{base.replace('/api', '/api/v3')}")
            elif has_api_v3:
                # Test modern format too
                endpoints_to_test.append(f"{base.replace('/api/v3', '/api')}")
        
        # For each base endpoint, add specific API endpoints to test
        full_endpoints_to_test = []
        for base_endpoint in endpoints_to_test:
            full_endpoints_to_test.append(base_endpoint)  # Test base endpoint
            full_endpoints_to_test.append(f"{base_endpoint}/zen")  # Test zen endpoint
            full_endpoints_to_test.append(f"{base_endpoint}/rate_limit")  # Test rate limit endpoint
            full_endpoints_to_test.append(f"{base_endpoint}/meta")  # Test meta endpoint
        
        # Remove duplicates while preserving order
        seen = set()
        endpoints_to_test = [x for x in full_endpoints_to_test if not (x in seen or seen.add(x))]
            
        # Test and report results
        import requests
        
        results = []
        
        for endpoint in endpoints_to_test:
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code < 400:  # Any 2xx or 3xx status is generally OK
                    status = f"✅ Success ({response.status_code})"
                    if endpoint.endswith('/zen') and response.status_code == 200:
                        status += f" - Response: {response.text}"
                else:
                    status = f"❌ Failed ({response.status_code})"
            except Exception as e:
                status = f"❌ Error: {str(e)}"
                
            results.append(f"- {endpoint}: {status}")
        
        # Determine best URL to use
        suggestion = ""
        working_endpoints = [ep for ep, res in zip(endpoints_to_test, results) if "✅ Success" in res]
        
        if working_endpoints:
            suggestion = f"""
Based on successful connections, the recommended API URL to use is:
{working_endpoints[0]}

When connecting, use this URL with the connect-github-enterprise tool."""
        else:
            suggestion = """
No successful connections were established. Please check:
1. Network connectivity to the GitHub instance
2. If the GitHub instance is behind VPN or firewall
3. If the hostname is correct
4. If the GitHub Enterprise instance is properly configured

You may need to contact your GitHub Enterprise administrator for assistance."""
            
        return [
            types.TextContent(
                type="text",
                text=f"""GitHub API Connection Test Results:

{chr(10).join(results)}
{suggestion}
""",
            )
        ]

    if name == "connect-github-enterprise":
        conn_name = arguments.get("name")
        url = arguments.get("url")
        token = arguments.get("token")
        
        if not conn_name or not url or not token:
            raise ValueError("Missing connection parameters")
        
        # Create the connection with URL validation
        try:
            connection = GitHubConnection(
                name=conn_name,
                url=url,
                auth_method=AuthMethod.TOKEN,
                token=token
            )
            
            # Test the connection with the validated URL
            github_client = connection.get_github_client()
            user = github_client.get_user()
            
            # Test a simple API call and get user info
            login = user.login
            
            # Try to get organizations to verify broader permissions
            try:
                orgs = list(github_client.get_user().get_orgs()[:5])
                org_names = [org.login for org in orgs]
                org_message = f"Access to organizations: {', '.join(org_names) if org_names else 'None detected'}"
            except GithubException:
                org_message = "Limited organization access (may restrict some operations)"
                
            # Test repo access
            try:
                repos = list(github_client.get_user().get_repos()[:5])
                if not repos:
                    repo_message = "No repositories found. Make sure your token has appropriate repository access."
                else:
                    repo_message = f"Successfully accessed {len(repos)} repositories"
            except GithubException:
                repo_message = "Could not access repositories. Check token permissions."
                
            # Store the connection
            connections[conn_name] = connection
            current_connection = conn_name
            
            # Notify clients that resources have changed
            await server.request_context.session.send_resource_list_changed()
            
            return [
                types.TextContent(
                    type="text",
                    text=f"""Successfully connected to GitHub Enterprise as {login}
Connection name: {conn_name}
API URL: {connection.url}
{repo_message}
{org_message}

You can now use this connection with other GitHub Enterprise tools.""",
                )
            ]
        except GithubException as e:
            error_message = str(e)
            requires_2fa = False
            
            # Check if the error is related to 2FA
            if "two-factor" in error_message.lower() or "2fa" in error_message.lower() or e.status == 401 and "OTP" in str(e.data):
                requires_2fa = True
                
            suggestion = ""
            if requires_2fa:
                suggestion = """
Two-Factor Authentication (2FA) is required for this account.
Please use the 'connect-github-enterprise-2fa' tool instead, which allows you to provide:
- Your GitHub Enterprise username
- Your Personal Access Token
- A one-time password (OTP) code from your authenticator app"""
            elif "401" in error_message:
                suggestion = """
Suggestions:
- Verify your token is correct and not expired
- Make sure the token has the required scopes (repo, read:org, user)
- For GitHub Enterprise, ensure your token works with the Enterprise instance
- If you have 2FA enabled, use the 'connect-github-enterprise-2fa' tool instead"""
            elif "404" in error_message:
                suggestion = """
Suggestions:
- Check if the GitHub Enterprise URL is correct
- For GitHub.com use: https://github.com or https://api.github.com
- For GitHub Enterprise Server, the server now tries the /api format by default
- If that fails, you can explicitly specify the API format:
  * For newer versions: https://HOSTNAME/api
  * For older versions: https://HOSTNAME/api/v3
- Use the test-api-connection tool to determine which URL format works for your GitHub Enterprise instance
- Verify network connectivity to the GitHub Enterprise instance
- Check if your GitHub Enterprise instance requires VPN or specific network access"""
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Failed to connect to GitHub Enterprise: {error_message}\n{suggestion}",
                )
            ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Failed to connect to GitHub Enterprise: {str(e)}\n\nTry using the 'connect-github-enterprise-2fa' tool if you have Two-Factor Authentication enabled.",
                )
            ]
    
    elif name == "connect-github-enterprise-2fa":
        conn_name = arguments.get("name")
        url = arguments.get("url")
        username = arguments.get("username")
        token = arguments.get("token")
        otp_code = arguments.get("otp_code")
        
        if not conn_name or not url or not username or not token or not otp_code:
            raise ValueError("Missing connection parameters")
            
        # Validate OTP code format (typically 6-8 digits)
        if not re.match(r'^\d{6,8}$', otp_code):
            return [
                types.TextContent(
                    type="text",
                    text="Invalid OTP code format. Please provide a valid one-time password from your authenticator app (typically 6-8 digits).",
                )
            ]
        
        # Create the connection with URL validation
        try:
            connection = GitHubConnection(
                name=conn_name,
                url=url,
                auth_method=AuthMethod.USERNAME_TOKEN,
                username=username,
                token=token,
                otp_code=otp_code,
                requires_2fa=True
            )
            
            # Test the connection with the validated URL
            github_client = connection.get_github_client()
            user = github_client.get_user()
            
            # Test a simple API call and get user info
            login = user.login
            
            # Try to get organizations to verify broader permissions
            try:
                orgs = list(github_client.get_user().get_orgs()[:5])
                org_names = [org.login for org in orgs]
                org_message = f"Access to organizations: {', '.join(org_names) if org_names else 'None detected'}"
            except GithubException:
                org_message = "Limited organization access (may restrict some operations)"
                
            # Test repo access
            try:
                repos = list(github_client.get_user().get_repos()[:5])
                if not repos:
                    repo_message = "No repositories found. Make sure your token has appropriate repository access."
                else:
                    repo_message = f"Successfully accessed {len(repos)} repositories"
            except GithubException:
                repo_message = "Could not access repositories. Check token permissions."
                
            # Store the connection
            connections[conn_name] = connection
            current_connection = conn_name
            
            # Notify clients that resources have changed
            await server.request_context.session.send_resource_list_changed()
            
            return [
                types.TextContent(
                    type="text",
                    text=f"""Successfully connected to GitHub Enterprise with 2FA as {login}
Connection name: {conn_name}
API URL: {connection.url}
{repo_message}
{org_message}

You can now use this connection with other GitHub Enterprise tools.
Note: Your OTP code is valid only for this session and will expire. 
For long-term access, create and use a Personal Access Token with the appropriate scopes.""",
                )
            ]
        except Exception as e:
            error_message = str(e)
            
            suggestion = ""
            if "401" in error_message or "authentication failed" in error_message.lower():
                suggestion = """
Suggestions:
- Verify your username and token are correct
- Make sure your OTP code is current (get a fresh code from your authenticator app)
- For GitHub Enterprise, ensure you're using the correct authentication method
- If using a Personal Access Token instead of a password, ensure it has the required scopes"""
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Failed to connect to GitHub Enterprise with 2FA: {error_message}\n{suggestion}",
                )
            ]
        
    elif name == "list-repositories":
        conn_name = arguments.get("connection")
        
        if not conn_name:
            raise ValueError("Missing connection name")
        
        if conn_name not in connections:
            raise ValueError(f"Connection not found: {conn_name}")
        
        connection = connections[conn_name]
        current_connection = conn_name
        
        github_client = connection.get_github_client()
        
        try:
            repos = github_client.get_user().get_repos()
            repo_list = []
            
            for repo in repos:
                connection.repositories[repo.name] = repo
                repo_list.append({
                    "name": repo.name,
                    "description": repo.description or "No description",
                    "url": repo.html_url,
                    "default_branch": repo.default_branch
                })
            
            # Notify clients that resources have changed
            await server.request_context.session.send_resource_list_changed()
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Found {len(repo_list)} repositories:\n\n" + 
                    "\n".join([f"- {r['name']}: {r['description']} ({r['url']})" for r in repo_list]),
                )
            ]
        except GithubException as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Failed to list repositories: {str(e)}",
                )
            ]
            
    elif name == "create-branch":
        if not current_connection:
            raise ValueError("No active GitHub Enterprise connection")
            
        repo_name = arguments.get("repository")
        base_branch = arguments.get("base_branch")
        new_branch = arguments.get("new_branch")
        
        if not repo_name or not base_branch or not new_branch:
            raise ValueError("Missing branch creation parameters")
        
        connection = connections[current_connection]
        
        try:
            # Get or fetch the repository
            if repo_name in connection.repositories:
                repo = connection.repositories[repo_name]
            else:
                github_client = connection.get_github_client()
                repo = github_client.get_user().get_repo(repo_name)
                connection.repositories[repo_name] = repo
            
            # Get the base branch reference
            base_ref = repo.get_git_ref(f"heads/{base_branch}")
            base_sha = base_ref.object.sha
            
            # Create a new reference (branch)
            repo.create_git_ref(f"refs/heads/{new_branch}", base_sha)
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Created new branch '{new_branch}' in repository '{repo_name}' based on '{base_branch}'",
                )
            ]
        except GithubException as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Failed to create branch: {str(e)}",
                )
            ]
            
    elif name == "commit-and-push":
        if not current_connection:
            raise ValueError("No active GitHub Enterprise connection")
            
        repo_name = arguments.get("repository")
        branch = arguments.get("branch")
        file_path = arguments.get("file_path")
        content = arguments.get("content")
        commit_message = arguments.get("commit_message")
        
        if not repo_name or not branch or not file_path or content is None or not commit_message:
            raise ValueError("Missing commit parameters")
        
        connection = connections[current_connection]
        
        try:
            # Get or fetch the repository
            if repo_name in connection.repositories:
                repo = connection.repositories[repo_name]
            else:
                github_client = connection.get_github_client()
                repo = github_client.get_user().get_repo(repo_name)
                connection.repositories[repo_name] = repo
                
            # Check if the file already exists
            try:
                contents = repo.get_contents(file_path, ref=branch)
                # Update the file
                repo.update_file(contents.path, commit_message, content, contents.sha, branch=branch)
                action = "Updated"
            except GithubException as e:
                # Create the file if it doesn't exist
                if e.status == 404:
                    repo.create_file(file_path, commit_message, content, branch=branch)
                    action = "Created"
                else:
                    raise e
                
            return [
                types.TextContent(
                    type="text",
                    text=f"{action} file '{file_path}' in repository '{repo_name}' on branch '{branch}' with commit message: {commit_message}",
                )
            ]
        except GithubException as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Failed to commit and push: {str(e)}",
                )
            ]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """
    List available prompts for GitHub Enterprise operations.
    Each prompt can have optional arguments to customize its behavior.
    """
    return [
        types.Prompt(
            name="repo-details",
            description="Gets detailed information about a repository",
            arguments=[
                types.PromptArgument(
                    name="repository",
                    description="Name of the repository",
                    required=True,
                )
            ],
        ),
        types.Prompt(
            name="create-pr-description", 
            description="Creates a pull request description based on changes",
            arguments=[
                types.PromptArgument(
                    name="repository",
                    description="Name of the repository",
                    required=True,
                ),
                types.PromptArgument(
                    name="base_branch",
                    description="Base branch for the PR",
                    required=True,
                ),
                types.PromptArgument(
                    name="head_branch",
                    description="Branch with changes for the PR",
                    required=True,
                )
            ],
        )
    ]

@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """
    Generate prompts for GitHub Enterprise operations.
    """
    if not current_connection:
        raise ValueError("No active GitHub Enterprise connection")
        
    connection = connections[current_connection]
    
    if name == "repo-details":
        if not arguments or "repository" not in arguments:
            raise ValueError("Missing repository argument")
            
        repo_name = arguments["repository"]
        
        try:
            if repo_name in connection.repositories:
                repo = connection.repositories[repo_name]
            else:
                github_client = connection.get_github_client()
                repo = github_client.get_user().get_repo(repo_name)
                connection.repositories[repo_name] = repo
                
            # Get more detailed information about the repository
            languages = repo.get_languages()
            contributors = [c.login for c in repo.get_contributors()[:5]]
            
            return types.GetPromptResult(
                description=f"Details for repository {repo_name}",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"""Please analyze this GitHub repository information:

Repository: {repo.name}
Owner: {repo.owner.login}
Description: {repo.description or 'No description'}
URL: {repo.html_url}
Default Branch: {repo.default_branch}
Main Languages: {', '.join([f'{lang} ({size} bytes)' for lang, size in languages.items()])}
Top Contributors: {', '.join(contributors) if contributors else 'None found'}
Stars: {repo.stargazers_count}
Forks: {repo.forks_count}
Open Issues: {repo.open_issues_count}
Created: {repo.created_at}
Last Updated: {repo.updated_at}

Summarize this repository's purpose, main technologies, and activity level. What kind of project is this?
""",
                        ),
                    )
                ],
            )
        except GithubException as e:
            return types.GetPromptResult(
                description="Error fetching repository details",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"Failed to fetch repository details for {repo_name}: {str(e)}",
                        ),
                    )
                ],
            )
    
    elif name == "create-pr-description":
        if not arguments or "repository" not in arguments or "base_branch" not in arguments or "head_branch" not in arguments:
            raise ValueError("Missing required arguments")
            
        repo_name = arguments["repository"]
        base_branch = arguments["base_branch"]
        head_branch = arguments["head_branch"]
        
        try:
            if repo_name in connection.repositories:
                repo = connection.repositories[repo_name]
            else:
                github_client = connection.get_github_client()
                repo = github_client.get_user().get_repo(repo_name)
                connection.repositories[repo_name] = repo
                
            # Get comparison between branches to analyze changes
            comparison = repo.compare(base_branch, head_branch)
            
            # Create a summary of the changes
            file_changes = []
            for file in comparison.files:
                file_changes.append(f"- {file.filename} ({file.status}, +{file.additions}, -{file.deletions})")
            
            return types.GetPromptResult(
                description=f"Generate PR description for changes from {head_branch} to {base_branch}",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"""Please create a comprehensive pull request description based on these changes:

Repository: {repo.name}
Base Branch: {base_branch}
Head Branch: {head_branch}
Total Commits: {comparison.total_commits}
Total Additions: {comparison.ahead_by}
Total Deletions: {comparison.behind_by}

Files changed:
{chr(10).join(file_changes)}

Based on these changes, please create a well-structured pull request description with:
1. A concise title
2. Summary of changes
3. Key implementation details
4. Testing instructions
5. Any notes or considerations for reviewers
""",
                        ),
                    )
                ],
            )
        except GithubException as e:
            return types.GetPromptResult(
                description="Error generating PR description",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"Failed to generate PR description: {str(e)}",
                        ),
                    )
                ],
            )
    
    else:
        raise ValueError(f"Unknown prompt: {name}")

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="github-enterprise-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )