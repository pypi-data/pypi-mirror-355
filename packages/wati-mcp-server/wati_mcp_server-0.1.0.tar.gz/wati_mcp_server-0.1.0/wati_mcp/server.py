"""
WATI MCP Server

A Model Context Protocol server for WhatsApp Business API integration using WATI.
Provides tools for sending messages, managing contacts, and retrieving conversation data.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

import requests
from mcp.server.fastmcp import FastMCP
import dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
dotenv.load_dotenv()


class WATIClient:
    """Client for interacting with the WATI WhatsApp Business API."""
    
    def __init__(self, api_endpoint: str, access_token: str):
        """Initialize the WATI client.
        
        Args:
            api_endpoint: The WATI API endpoint URL
            access_token: Your WATI API access token
        """
        self.api_endpoint = api_endpoint.rstrip('/')
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            'accept': '*/*',
            'Authorization': access_token
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the WATI API with error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for the request
            
        Returns:
            Dict containing the API response or error information
        """
        url = f"{self.api_endpoint}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            logger.error(f"{error_msg} (Status: {status_code})")
            return {
                "error": error_msg,
                "status_code": status_code
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}


def create_server() -> FastMCP:
    """Create and configure the MCP server."""
    
    # Get API credentials from environment
    api_endpoint = os.environ.get("API_ENDPOINT")
    access_token = os.environ.get("ACCESS_TOKEN")
    
    if not api_endpoint or not access_token:
        raise ValueError(
            "Missing required environment variables: API_ENDPOINT and ACCESS_TOKEN. "
            "Please set these in your .env file or environment."
        )
    
    # Initialize the WATI client
    wati_client = WATIClient(api_endpoint, access_token)
    
    # Create MCP server
    mcp = FastMCP("WATI WhatsApp MCP Server")
    
    @mcp.tool()
    def get_weather(city: str) -> str:
        """Get the weather data for a given city (demo function)."""
        return f"The weather in {city} is sunny."
    
    @mcp.tool()
    def get_messages(
        whatsapp_number: int, 
        page_size: int = 20, 
        page_number: int = 1, 
        from_date: Optional[str] = None, 
        to_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve WhatsApp messages for a specific number from the WATI API.
        
        Args:
            whatsapp_number: WhatsApp number with country code (e.g., 919909000282)
            page_size: Number of messages per page (default: 20)
            page_number: Page number for pagination (default: 1)
            from_date: Start date in UTC format (optional)
            to_date: End date in UTC format (optional)
        
        Returns:
            API response containing message data or error info.
        """
        params = {
            'pageSize': page_size,
            'pageNumber': page_number
        }
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date
            
        return wati_client._make_request(
            'GET', 
            f'/api/v1/getMessages/{whatsapp_number}',
            params=params
        )
    
    @mcp.tool()
    def get_message_templates(
        page_size: int = 10,
        page_number: int = 1
    ) -> Dict[str, Any]:
        """
        Retrieve WhatsApp message templates from the WATI API.

        Args:
            page_size: Number of templates per page (default: 10)
            page_number: Page number for pagination (default: 1)

        Returns:
            API response containing message templates or error info.
        """
        params = {
            'pageSize': page_size,
            'pageNumber': page_number
        }
        return wati_client._make_request(
            'GET', 
            '/api/v1/getMessageTemplates',
            params=params
        )
    
    @mcp.tool()
    def get_contacts_list(
        page_size: int = 10,
        page_number: int = 1,
        name: Optional[str] = None,
        attribute: Optional[str] = None,
        created_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve WhatsApp contacts from the WATI API with optional filters.

        Args:
            page_size: Number of contacts per page (default: 10)
            page_number: Page number for pagination (default: 1)
            name: Contact name to filter (optional)
            attribute: Advanced attribute filter as a JSON string (optional)
            created_date: Filter by created date (YYYY-MM-DD or MM-DD-YYYY, optional)

        Returns:
            API response containing contacts or error info.

        Examples:
            # Find contacts whose name contains "Jairaj"
            get_contacts_list(attribute='[{"name":"name","operator":"contain","value":"Jairaj"}]')

            # Find contacts in city "Ahmedabad"
            get_contacts_list(attribute='[{"name":"city","operator":"=","value":"Ahmedabad"}]')

            # Find contacts whose phone is not "919909000282"
            get_contacts_list(attribute='[{"name":"phone","operator":"!=","value":"919909000282"}]')

            # Find contacts where the "email" field exists
            get_contacts_list(attribute='[{"name":"email","operator":"exist"}]')

            # Combine multiple filters (AND logic)
            get_contacts_list(attribute='[{"name":"city","operator":"=","value":"Ahmedabad"},{"name":"name","operator":"contain","value":"Jairaj"}]')
        """
        params = {
            'pageSize': page_size,
            'pageNumber': page_number
        }
        if name:
            params['name'] = name
        if attribute:
            params['attribute'] = attribute
        if created_date:
            params['createdDate'] = created_date
            
        return wati_client._make_request(
            'GET', 
            '/api/v1/getContacts',
            params=params
        )
    
    @mcp.tool()
    def get_media_by_filename(file_name: str) -> Dict[str, Any]:
        """
        Retrieve media details from the WATI API by file name.

        Args:
            file_name: The name of the media file to retrieve.

        Returns:
            API response containing media details or error info.
        """
        params = {'fileName': file_name}
        return wati_client._make_request(
            'GET', 
            '/api/v1/getMedia',
            params=params
        )
    
    @mcp.tool()
    def update_contact_attributes(
        whatsapp_number: int,
        custom_params: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Update custom attributes for a WhatsApp contact in the WATI API.

        Args:
            whatsapp_number: WhatsApp number with country code (e.g., 919909000282)
            custom_params: List of dictionaries with 'name' and 'value' keys for attributes to update.

        Returns:
            API response indicating success or error info.
        """
        headers = {'Content-Type': 'application/json-patch+json'}
        data = {'customParams': custom_params}
        
        return wati_client._make_request(
            'POST',
            f'/api/v1/updateContactAttributes/{whatsapp_number}',
            headers=headers,
            json=data
        )
    
    @mcp.tool()
    def add_contact(
        whatsapp_number: int,
        name: str,
        custom_params: List[Dict[str, str]],
        source_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a new WhatsApp contact in the WATI API.

        Args:
            whatsapp_number: WhatsApp number with country code (e.g., 919909000283)
            name: Name of the contact
            custom_params: List of dictionaries with 'name' and 'value' keys for custom attributes
            source_type: Source type (e.g., "Facebook", optional)

        Returns:
            API response containing contact details or error info.
        """
        headers = {'Content-Type': 'application/json-patch+json'}
        params = {}
        if source_type:
            params['sourceType'] = source_type
            
        data = {
            'name': name,
            'customParams': custom_params
        }
        
        return wati_client._make_request(
            'POST',
            f'/api/v1/addContact/{whatsapp_number}',
            headers=headers,
            params=params,
            json=data
        )
    
    @mcp.tool()
    def send_file_to_opened_session(
        whatsapp_number: int,
        file_path: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a file to an open WhatsApp session using the WATI API.

        Args:
            whatsapp_number: WhatsApp number with country code (e.g., 919909000282)
            file_path: Path to the file to send
            caption: Optional caption for the file

        Returns:
            API response indicating success or error info.
        """
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
            
        params = {}
        if caption:
            params['caption'] = caption
            
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}
                return wati_client._make_request(
                    'POST',
                    f'/api/v1/sendSessionFile/{whatsapp_number}',
                    params=params,
                    files=files
                )
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}
    
    @mcp.tool()
    def send_message_to_opened_session(
        whatsapp_number: int,
        message_text: str,
        reply_context_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message to an open WhatsApp session using the WATI API.

        Args:
            whatsapp_number: WhatsApp number with country code (e.g., 919909000282)
            message_text: The message text to send
            reply_context_id: Optional WhatsApp message ID (wamid) to reply to

        Returns:
            API response indicating success or error info.
        """
        params = {'messageText': message_text}
        if reply_context_id:
            params['replyContextId'] = reply_context_id
            
        return wati_client._make_request(
            'POST',
            f'/api/v1/sendSessionMessage/{whatsapp_number}',
            params=params,
            data=''
        )
    
    @mcp.tool()
    def send_template_message(
        whatsapp_number: int,
        template_name: str,
        broadcast_name: str,
        parameters: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Send a template message to a WhatsApp number using the WATI API.

        Args:
            whatsapp_number: WhatsApp number with country code (e.g., 919909000282)
            template_name: Name of the template to use
            broadcast_name: Name for the broadcast
            parameters: List of dictionaries with 'name' and 'value' keys for template parameters

        Returns:
            API response indicating success or error info.
        """
        headers = {'Content-Type': 'application/json-patch+json'}
        params = {'whatsappNumber': whatsapp_number}
        data = {
            'template_name': template_name,
            'broadcast_name': broadcast_name,
            'parameters': parameters
        }
        
        return wati_client._make_request(
            'POST',
            '/api/v1/sendTemplateMessage',
            headers=headers,
            params=params,
            json=data
        )
    
    @mcp.tool()
    def send_template_messages(
        template_name: str,
        broadcast_name: str,
        receivers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Send template messages to multiple WhatsApp numbers using the WATI API.

        Args:
            template_name: Name of the template to use
            broadcast_name: Name for the broadcast
            receivers: List of dicts, each with 'whatsappNumber' and 'customParams' (list of dicts with 'name' and 'value')

        Returns:
            API response indicating success or error info.
        """
        headers = {'Content-Type': 'application/json-patch+json'}
        data = {
            'template_name': template_name,
            'broadcast_name': broadcast_name,
            'receivers': receivers
        }
        
        return wati_client._make_request(
            'POST',
            '/api/v1/sendTemplateMessages',
            headers=headers,
            json=data
        )
    
    @mcp.tool()
    def send_template_messages_from_csv(
        template_name: str,
        broadcast_name: str,
        csv_file_path: str
    ) -> Dict[str, Any]:
        """
        Send template messages using a CSV file upload via the WATI API.

        Args:
            template_name: Name of the template to use
            broadcast_name: Name for the broadcast
            csv_file_path: Path to the CSV file (must have a column called 'Phone')

        Returns:
            API response indicating success or error info.
        """
        if not os.path.exists(csv_file_path):
            return {"error": f"File not found: {csv_file_path}"}
            
        params = {
            'template_name': template_name,
            'broadcast_name': broadcast_name
        }
        
        try:
            with open(csv_file_path, 'rb') as f:
                files = {'whatsapp_numbers_csv': (os.path.basename(csv_file_path), f, 'text/csv')}
                return wati_client._make_request(
                    'POST',
                    '/api/v1/sendTemplateMessageCSV',
                    params=params,
                    files=files
                )
        except Exception as e:
            return {"error": f"Failed to read CSV file: {str(e)}"}
    
    # Add a dynamic greeting resource
    @mcp.resource("greeting://{name}")
    def get_greeting(name: str) -> str:
        """Get a personalized greeting."""
        return f"Hello, {name}!"
    
    return mcp


def main():
    """Main entry point for running the server."""
    try:
        server = create_server()
        logger.info("Starting WATI MCP Server...")
        server.run(transport="stdio")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    main() 