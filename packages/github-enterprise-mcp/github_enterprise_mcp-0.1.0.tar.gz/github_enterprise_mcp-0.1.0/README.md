# github-enterprise-mcp MCP server

An MCP server for GitHub Enterprise that handles repository access, branch creation, commits, and pushes.

## Components

### Resources

The server implements GitHub Enterprise repositories as resources:
- Custom github:// URI scheme for accessing repositories
- Each repository resource has a name, description and custom mimetype
- Resources are dynamically loaded from the connected GitHub Enterprise instance

### Prompts

The server provides the following prompts:
- repo-details: Gets detailed information about a repository
  - Required "repository" argument to specify the repository
  - Returns comprehensive information about the repository
- create-pr-description: Creates a pull request description based on changes
  - Required "repository", "base_branch", and "head_branch" arguments
  - Analyzes branch differences and suggests PR description

### Tools

The server implements the following tools:
- test-api-connection: Test connection to a GitHub API endpoint
  - Takes "url" as a required string argument
  - Tests multiple API endpoint formats to determine which works
  - Provides recommendations for the correct URL to use
  - Useful for troubleshooting API connectivity issues
- connect-github-enterprise: Connect to a GitHub Enterprise instance
  - Takes "name", "url", and "token" as required string arguments
  - For "url", use the correct format based on your GitHub instance:
    * GitHub.com: Use `https://github.com` or `https://api.github.com`
    * GitHub Enterprise: Use `https://HOSTNAME/api/v3` or `https://HOSTNAME/api`
  - Establishes and validates a connection to GitHub Enterprise
  - Automatically detects if 2FA is required and provides appropriate guidance
- connect-github-enterprise-2fa: Connect to a GitHub Enterprise instance with 2FA
  - Takes "name", "url", "username", "token", and "otp_code" as required string arguments
  - Establishes and validates a connection to GitHub Enterprise with Two-Factor Authentication
  - Validates OTP code format (typically 6-8 digits from an authenticator app)
- list-repositories: List repositories from the connected GitHub Enterprise instance
  - Takes "connection" as a required string argument
  - Returns a list of available repositories
- create-branch: Create a new branch in a repository
  - Takes "repository", "base_branch", and "new_branch" as required string arguments
  - Creates a new branch based on an existing branch
- commit-and-push: Commit file changes and push to a branch
  - Takes "repository", "branch", "file_path", "content", and "commit_message" as required arguments
  - Creates or updates files in a repository and commits changes

## Configuration

### GitHub Enterprise Setup

To use this MCP server with your GitHub Enterprise instance, you'll need:

1. **GitHub Enterprise URL**:
   - For GitHub.com: Use `https://github.com` or `https://api.github.com`
   - For GitHub Enterprise Server:
     * Simply use the base URL (e.g., `https://github.example.com`)
     * The server will try to detect the correct API path format automatically
     * Modern GitHub Enterprise: `/api` (added by default if no path is specified)
     * Older GitHub Enterprise: `/api/v3` (you can explicitly include this if needed)
     * If you're unsure, use the `test-api-connection` tool to determine the best format
   - The URL should be accessible from the machine where the MCP server is running
   - GitHub Enterprise API URLs can vary based on server version and configuration

2. **Authentication**:
   - **For standard authentication** (no 2FA):
     - Create a Personal Access Token (PAT) from your GitHub Enterprise instance
     - Required scopes:
       - `repo` (Full control of private repositories)
       - `read:org` (Read organization information)
       - `user` (Read user information)
     - For fine-grained tokens, ensure repository access is enabled
   
   - **For Two-Factor Authentication (2FA)**:
     - You will need:
       - Your GitHub Enterprise username
       - Your Personal Access Token (PAT) with the required scopes
       - A one-time password (OTP) from your authenticator app
     - Note that OTP codes are typically valid for 30-60 seconds
     - The server validates that the OTP code is in the correct format (6-8 digits)

3. **Connection Name**:
   - A friendly name to identify your connection within the MCP server
   - This will be used in subsequent commands

### Claude or Other LLM Integration

To use this MCP server with AI assistants like Claude:

1. **Configure your LLM client**:
   - For Claude Desktop, modify the configuration file as shown below in the Quickstart section
   - This tells Claude how to find and communicate with your GitHub Enterprise MCP server
   - The MCP server must be running on your machine when you use it with Claude

2. **Authentication Flow**:
   - When using the MCP server with an LLM, you'll need to connect to your GitHub Enterprise instance first
   - Use the `connect-github-enterprise` tool to establish the connection
   - Your personal access token is only stored in memory and not persisted between sessions
   - For security, restart the MCP server when you're done using it

3. **Security Considerations**:
   - The LLM only interacts with your GitHub Enterprise through the MCP server
   - Your credentials are never exposed to the LLM itself
   - Consider using tokens with limited scope and expiration for enhanced security
   - Never share your MCP server logs, as they might contain sensitive information

## Quickstart

### Install

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development/Unpublished Servers Configuration</summary>
  ```
  "mcpServers": {
    "github-enterprise-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/annmariyajoshy/vibecoding/github-enterprise-mcp",
        "run",
        "github-enterprise-mcp"
      ]
    }
  }
  ```
</details>

<details>
  <summary>Published Servers Configuration</summary>
  ```
  "mcpServers": {
    "github-enterprise-mcp": {
      "command": "uvx",
      "args": [
        "github-enterprise-mcp"
      ]
    }
  }
  ```
</details>

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

2. Build package distributions:
```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:
```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).


You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory /Users/annmariyajoshy/vibecoding/github-enterprise-mcp run github-enterprise-mcp
```


Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.

## Example Workflow

Here's how to use the GitHub Enterprise MCP server with an LLM assistant:

1. **Start the MCP server** by running:
   ```bash
   uv --directory /path/to/github-enterprise-mcp run github-enterprise-mcp
   ```

2. **Test your GitHub API connection** (recommended before connecting):
   Use the `test-api-connection` tool with:
   - `url`: Your GitHub or GitHub Enterprise URL (e.g., "https://github.com" or "https://github.example.com")
   
   This tool will:
   - Test multiple API endpoint formats automatically (base URL, /api, and /api/v3)
   - Try various GitHub API endpoints like /zen, /rate_limit, and /meta
   - Recommend the best URL format to use for your specific GitHub Enterprise instance
   - Provide diagnostics if connection issues are found
   - Help you troubleshoot network or configuration problems

3. **Connect to GitHub Enterprise**:

   - **For standard authentication** (no 2FA):
     Use the `connect-github-enterprise` tool with:
     - `name`: A name for your connection (e.g., "my-enterprise")
     - `url`: Your GitHub Enterprise URL (e.g., "https://github.example.com")
     - `token`: Your Personal Access Token
   
   - **For Two-Factor Authentication (2FA)**:
     Use the `connect-github-enterprise-2fa` tool with:
     - `name`: A name for your connection (e.g., "my-enterprise")
     - `url`: Your GitHub Enterprise URL (e.g., "https://github.example.com")
     - `username`: Your GitHub Enterprise username
     - `token`: Your Personal Access Token
     - `otp_code`: Current one-time password from your authenticator app

   *Note: If you attempt to use standard authentication with an account that has 2FA enabled, the server will automatically detect this and suggest using the 2FA-specific connection tool.*

3. **List available repositories**:
   Use the `list-repositories` tool with:
   - `connection`: The name you provided in step 2

4. **Create a branch**:
   Use the `create-branch` tool with:
   - `repository`: The repository name
   - `base_branch`: The source branch (typically "main" or "master")
   - `new_branch`: The name for your new branch

5. **Make file changes**:
   Use the `commit-and-push` tool with:
   - `repository`: The repository name
   - `branch`: The branch to commit to
   - `file_path`: Path to the file in the repository
   - `content`: The new content for the file
   - `commit_message`: Your commit message

6. **Generate a PR description**:
   Use the `create-pr-description` prompt with:
   - `repository`: The repository name
   - `base_branch`: The target branch for the PR
   - `head_branch`: Your feature branch with changes

This workflow enables AI-assisted repository management while keeping your code secure in your GitHub Enterprise instance.