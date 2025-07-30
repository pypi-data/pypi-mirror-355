"""
Tests for the WATI MCP server.
"""

import os
import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest

from wati_mcp.server import WATIClient, create_server


class TestWATIClient(unittest.TestCase):
    """Test cases for the WATIClient class."""
    
    def setUp(self):
        """Set up test client."""
        self.client = WATIClient(
            api_endpoint="https://test.example.com",
            access_token="test_token"
        )
    
    def test_client_initialization(self):
        """Test client initialization."""
        self.assertEqual(self.client.api_endpoint, "https://test.example.com")
        self.assertEqual(self.client.access_token, "test_token")
        self.assertIsNotNone(self.client.session)
    
    def test_client_initialization_strips_slash(self):
        """Test that trailing slash is stripped from endpoint."""
        client = WATIClient(
            api_endpoint="https://test.example.com/",
            access_token="test_token"
        )
        self.assertEqual(client.api_endpoint, "https://test.example.com")
    
    @patch('wati_mcp.server.requests.Session.request')
    def test_make_request_success(self, mock_request):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        result = self.client._make_request('GET', '/test')
        
        self.assertEqual(result, {"success": True})
        mock_request.assert_called_once()
    
    @patch('wati_mcp.server.requests.Session.request')
    def test_make_request_failure(self, mock_request):
        """Test failed API request."""
        mock_request.side_effect = Exception("Network error")
        
        result = self.client._make_request('GET', '/test')
        
        self.assertIn("error", result)
        self.assertIn("Network error", result["error"])


class TestServerCreation(unittest.TestCase):
    """Test cases for server creation."""
    
    @patch.dict(os.environ, {
        'API_ENDPOINT': 'https://test.example.com',
        'ACCESS_TOKEN': 'test_token'
    })
    def test_create_server_success(self):
        """Test successful server creation with environment variables."""
        server = create_server()
        self.assertIsNotNone(server)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_create_server_missing_env_vars(self):
        """Test server creation fails without environment variables."""
        with self.assertRaises(ValueError) as context:
            create_server()
        
        self.assertIn("Missing required environment variables", str(context.exception))
    
    @patch.dict(os.environ, {'API_ENDPOINT': 'https://test.example.com'}, clear=True)
    def test_create_server_missing_token(self):
        """Test server creation fails without access token."""
        with self.assertRaises(ValueError) as context:
            create_server()
        
        self.assertIn("Missing required environment variables", str(context.exception))


# Integration tests that require actual environment setup
class TestIntegration(unittest.TestCase):
    """Integration tests for the MCP server."""
    
    def setUp(self):
        """Set up integration tests."""
        # Skip integration tests if environment variables are not set
        self.api_endpoint = os.environ.get("API_ENDPOINT")
        self.access_token = os.environ.get("ACCESS_TOKEN")
        
        if not self.api_endpoint or not self.access_token:
            self.skipTest("Integration tests require API_ENDPOINT and ACCESS_TOKEN environment variables")
    
    def test_server_tools_registration(self):
        """Test that all expected tools are registered."""
        server = create_server()
        
        # Get the list of registered tools
        # Note: This would need to be adapted based on the actual FastMCP API
        # for getting registered tools
        self.assertIsNotNone(server)


if __name__ == '__main__':
    unittest.main() 