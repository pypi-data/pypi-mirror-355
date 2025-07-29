import unittest
from unittest.mock import patch
from urllib.parse import urlparse
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from github_enterprise_mcp.server import GitHubConnection, AuthMethod

class TestURLValidation(unittest.TestCase):
    """Test URL validation logic for GitHub Enterprise MCP server"""

    def test_github_com_url(self):
        """Test that github.com URLs are correctly formatted as api.github.com"""
        conn = GitHubConnection(
            name="test",
            url="github.com",
            auth_method=AuthMethod.TOKEN,
            token="fake-token"
        )
        self.assertEqual(conn.url, "https://api.github.com")

        conn = GitHubConnection(
            name="test",
            url="https://github.com",
            auth_method=AuthMethod.TOKEN,
            token="fake-token"
        )
        self.assertEqual(conn.url, "https://api.github.com")
        
    def test_github_com_subdomain_url(self):
        """Test that subdomain.github.com URLs get /api appended"""
        conn = GitHubConnection(
            name="test",
            url="subdomain.github.com",
            auth_method=AuthMethod.TOKEN,
            token="fake-token"
        )
        self.assertEqual(conn.url, "https://subdomain.github.com/api")

    def test_api_github_com_url(self):
        """Test that api.github.com URLs are preserved"""
        conn = GitHubConnection(
            name="test",
            url="api.github.com",
            auth_method=AuthMethod.TOKEN,
            token="fake-token"
        )
        self.assertEqual(conn.url, "https://api.github.com")

        conn = GitHubConnection(
            name="test",
            url="https://api.github.com",
            auth_method=AuthMethod.TOKEN,
            token="fake-token"
        )
        self.assertEqual(conn.url, "https://api.github.com")

    def test_enterprise_url_with_api(self):
        """Test that enterprise URLs with /api are preserved"""
        # Modern format with /api
        conn = GitHubConnection(
            name="test",
            url="https://github.example.com/api",
            auth_method=AuthMethod.TOKEN,
            token="fake-token"
        )
        self.assertEqual(conn.url, "https://github.example.com/api")

    def test_enterprise_url_with_api_v3(self):
        """Test that enterprise URLs with /api/v3 are preserved"""
        # Older format with /api/v3
        conn = GitHubConnection(
            name="test",
            url="https://github.example.com/api/v3",
            auth_method=AuthMethod.TOKEN,
            token="fake-token"
        )
        self.assertEqual(conn.url, "https://github.example.com/api/v3")

    def test_enterprise_url_without_api(self):
        """Test that enterprise URLs without /api get /api appended (default format)"""
        # Base URL without path
        conn = GitHubConnection(
            name="test",
            url="https://github.example.com",
            auth_method=AuthMethod.TOKEN,
            token="fake-token"
        )
        self.assertEqual(conn.url, "https://github.example.com/api")

    def test_enterprise_url_with_trailing_slash(self):
        """Test that enterprise URLs with trailing slash get /api appended correctly"""
        # Base URL with trailing slash
        conn = GitHubConnection(
            name="test",
            url="https://github.example.com/",
            auth_method=AuthMethod.TOKEN,
            token="fake-token"
        )
        self.assertEqual(conn.url, "https://github.example.com/api")

if __name__ == '__main__':
    unittest.main()
