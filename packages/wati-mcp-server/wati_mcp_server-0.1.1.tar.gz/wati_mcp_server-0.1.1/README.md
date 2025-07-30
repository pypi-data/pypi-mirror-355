# WATI MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that provides seamless integration with the WATI WhatsApp Business API. This server enables AI assistants to send messages, manage contacts, retrieve conversation data, and handle media files through WhatsApp Business accounts.

## Features

- **Message Management**: Send and receive WhatsApp messages
- **Contact Management**: Add, update, and search contacts with custom attributes
- **Template Messages**: Send pre-approved template messages and broadcasts
- **Media Handling**: Send and receive media files (images, documents, etc.)
- **Conversation History**: Retrieve message history with pagination and filtering
- **Bulk Operations**: Send messages to multiple recipients via CSV upload
- **Real-time Integration**: Works with any MCP-compatible AI assistant

## Installation

### Step 1: Install the Package

**Recommended:** Using pipx (best for CLI tools)
```bash
pipx install wati-mcp-server
```

**Alternative:** Using pip with virtual environment
```bash
python3 -m venv mcp-env
source mcp-env/bin/activate
pip install wati-mcp-server
```

### Step 2: Find Installation Path

Find where the command was installed:
```bash
which wati-mcp-server
```

This will show a path like `/Users/username/.local/bin/wati-mcp-server` (pipx) or `/path/to/mcp-env/bin/wati-mcp-server` (venv).

### Step 3: Configure Your MCP Client

**For Claude Desktop:** Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

**For Cursor:** Edit your Cursor MCP configuration file

Add this configuration:

```json
{
  "mcpServers": {
    "wati": {
      "command": "/full/path/from/which/command",
      "env": {
        "API_ENDPOINT": "https://live-mt-server.wati.io/YOUR_TENANT_ID",
        "ACCESS_TOKEN": "Bearer YOUR_WATI_ACCESS_TOKEN"
      }
    }
  }
}
```

**Or if pipx added it to your PATH, you can use:**
```json
{
  "mcpServers": {
    "wati": {
      "command": "wati-mcp-server",
      "env": {
        "API_ENDPOINT": "https://live-mt-server.wati.io/YOUR_TENANT_ID",
        "ACCESS_TOKEN": "Bearer YOUR_WATI_ACCESS_TOKEN"
      }
    }
  }
}
```

### Step 4: Get Your WATI Credentials

1. Sign up for a [WATI account](https://www.wati.io/)
2. Get your WhatsApp Business API approved
3. Find your API endpoint and access token in the WATI dashboard
4. Replace `YOUR_TENANT_ID` and `YOUR_WATI_ACCESS_TOKEN` in the config above

### Step 5: Restart Your MCP Client

After updating the configuration, completely restart Claude Desktop or Cursor.

## Available Tools

The server provides the following MCP tools:

### Message Operations
- `get_messages` - Retrieve WhatsApp messages for a specific number
- `send_message_to_opened_session` - Send a message to an open WhatsApp session
- `send_template_message` - Send a pre-approved template message
- `send_template_messages` - Send template messages to multiple recipients
- `send_template_messages_from_csv` - Bulk send template messages from CSV file

### Contact Management
- `get_contacts_list` - Retrieve contacts with filtering options
- `add_contact` - Add a new WhatsApp contact
- `update_contact_attributes` - Update custom attributes for a contact

### Templates and Media
- `get_message_templates` - Retrieve available message templates
- `get_media_by_filename` - Get media file details
- `send_file_to_opened_session` - Send files to WhatsApp sessions

### Utility
- `get_weather` - Demo weather function (for testing)

## Usage Examples

### Send a Template Message

```python
# The AI assistant can use this tool:
send_template_message(
    whatsapp_number=919909000282,
    template_name="welcome_message",
    broadcast_name="new_user_welcome",
    parameters=[
        {"name": "customer_name", "value": "John Doe"},
        {"name": "company_name", "value": "ACME Corp"}
    ]
)
```

### Search Contacts

```python
# Find contacts in a specific city
get_contacts_list(
    attribute='[{"name":"city","operator":"=","value":"Mumbai"}]',
    page_size=20
)
```

### Send Bulk Messages

```python
# Send to multiple recipients
send_template_messages(
    template_name="promotional_offer",
    broadcast_name="summer_sale_2024",
    receivers=[
        {
            "whatsappNumber": "919909000282",
            "customParams": [{"name": "offer_code", "value": "SUMMER25"}]
        },
        {
            "whatsappNumber": "919909000283", 
            "customParams": [{"name": "offer_code", "value": "SUMMER30"}]
        }
    ]
)
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `API_ENDPOINT` | Your WATI API endpoint URL | Yes |
| `ACCESS_TOKEN` | Your WATI API access token | Yes |

## Development

### Setting up for Development

```bash
# Clone the repository
git clone https://github.com/Jairajmehra/wati_whatsapp_mcp.git
cd wati_whatsapp_mcp

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black wati_mcp/
flake8 wati_mcp/
mypy wati_mcp/
```

### Building for Distribution

```bash
python -m build
```

## API Reference

### WATIClient Class

The core client class that handles all API interactions:

```python
from wati_mcp.server import WATIClient

client = WATIClient(api_endpoint="...", access_token="...")
```

### Server Creation

```python
from wati_mcp.server import create_server

# Create a configured MCP server
server = create_server()
```

## Error Handling

The server includes comprehensive error handling:

- API request failures are caught and returned as structured error responses
- File operations include existence checks and proper error messages
- Environment variable validation with helpful error messages
- Structured logging for debugging and monitoring

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [GitHub Repository](https://github.com/Jairajmehra/wati_whatsapp_mcp)
- **Issues**: [GitHub Issues](https://github.com/Jairajmehra/wati_whatsapp_mcp/issues)
- **WATI Documentation**: [WATI API Docs](https://www.wati.io/developers)

## Changelog

### v0.1.0
- Initial release
- Core WhatsApp messaging functionality
- Contact management features
- Template message support
- Media file handling
- Bulk messaging capabilities

---

Built with ❤️ for the MCP ecosystem
