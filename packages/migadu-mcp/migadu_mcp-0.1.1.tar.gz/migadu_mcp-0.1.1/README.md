# Migadu MCP Server

A FastMCP server for managing Migadu mailboxes, identities, forwardings, aliases, and rewrites through the Model Context Protocol.

## Features

- **Mailbox Management**: Create, read, update, delete mailboxes
- **Identity Management**: Manage email identities for mailboxes
- **Forwarding Rules**: Set up and manage email forwarding
- **Alias Management**: Create and manage email aliases
- **Rewrite Rules**: Pattern-based email routing
- **Autoresponders**: Configure out-of-office messages
- **Resources**: Access mailbox data as MCP resources
- **Prompts**: Guided wizards for complex operations

## Installation

1. Clone or download this project
2. Install dependencies using uv:

```bash
uv sync
```

## Configuration

1. Get your Migadu API credentials:
   - Visit [Migadu Admin > My Account > API Keys](https://admin.migadu.com/account/api/keys)
   - Create a new API key

2. Configure the MCP server in your MCP client (e.g., Claude Desktop):

**For Claude Desktop/MCP Clients:**
Add to your MCP configuration (no separate installation needed):

```json
{
  "mcpServers": {
    "migadu": {
      "command": "uvx",
      "args": ["migadu-mcp"],
      "env": {
        "MIGADU_EMAIL": "your-email@domain.com",
        "MIGADU_API_KEY": "your-api-key-here",
        "MIGADU_DOMAIN": "yourdomain.com"
      }
    }
  }
}
```

**Alternative Local Installation:**
```bash
uv tool install migadu-mcp
```

**For Development:**
```bash
# Clone and install in development mode
git clone https://github.com/Michaelzag/migadu-mcp.git
cd migadu-mcp
uv sync

# Run locally
uv run -m migadu_mcp.main

# Or use fastmcp dev
uv run fastmcp dev migadu_mcp/main.py --with-editable .
```

**Testing the Server:**
```bash
# Set environment variables first
export MIGADU_EMAIL="your-email@domain.com"
export MIGADU_API_KEY="your-api-key-here"
export MIGADU_DOMAIN="yourdomain.com"

# Run with fastmcp
uv run fastmcp run migadu_mcp/main.py
```

### Available Tools

#### Mailbox Management
- `list_mailboxes(domain)` - List all mailboxes
- `get_mailbox(domain, local_part)` - Get mailbox details
- `create_mailbox(domain, local_part, name, ...)` - Create new mailbox
- `update_mailbox(domain, local_part, ...)` - Update mailbox settings
- `delete_mailbox(domain, local_part)` - Delete mailbox
- `reset_mailbox_password(domain, local_part, new_password)` - Reset password

#### Identity Management
- `list_identities(domain, mailbox)` - List mailbox identities
- `create_identity(domain, mailbox, local_part, name, password)` - Create identity
- `get_identity(domain, mailbox, identity)` - Get identity details
- `update_identity(domain, mailbox, identity, ...)` - Update identity
- `delete_identity(domain, mailbox, identity)` - Delete identity

#### Forwarding Management
- `list_forwardings(domain, mailbox)` - List forwardings
- `create_forwarding(domain, mailbox, address)` - Create forwarding
- `get_forwarding(domain, mailbox, address)` - Get forwarding details
- `update_forwarding(domain, mailbox, address, ...)` - Update forwarding
- `delete_forwarding(domain, mailbox, address)` - Delete forwarding

#### Alias Management
- `list_aliases(domain)` - List domain aliases
- `create_alias(domain, local_part, destinations)` - Create alias
- `get_alias(domain, local_part)` - Get alias details
- `update_alias(domain, local_part, destinations)` - Update alias
- `delete_alias(domain, local_part)` - Delete alias

#### Rewrite Management
- `list_rewrites(domain)` - List rewrite rules
- `create_rewrite(domain, name, local_part_rule, destinations)` - Create rewrite
- `get_rewrite(domain, name)` - Get rewrite details
- `update_rewrite(domain, name, ...)` - Update rewrite
- `delete_rewrite(domain, name)` - Delete rewrite

#### Autoresponder
- `set_autoresponder(domain, local_part, active, subject, body, expires_on)` - Configure auto-reply

### Available Resources

- `mailboxes://domain.com` - All mailboxes for domain
- `mailbox://domain.com/username` - Specific mailbox details
- `identities://domain.com/username` - Mailbox identities
- `forwardings://domain.com/username` - Mailbox forwardings
- `aliases://domain.com` - Domain aliases
- `rewrites://domain.com` - Domain rewrites

### Available Prompts

- `mailbox_creation_wizard(domain, user_requirements)` - Guided mailbox creation
- `bulk_operation_planner(domain, operation_type, targets)` - Plan bulk operations

## Examples

### Basic Mailbox Operations

```python
# List all mailboxes for a domain
await client.call_tool("list_mailboxes", {"domain": "example.com"})

# Create a new mailbox
await client.call_tool("create_mailbox", {
    "domain": "example.com",
    "local_part": "john",
    "name": "John Doe",
    "password": "secure-password"
})

# Create mailbox with invitation
await client.call_tool("create_mailbox", {
    "domain": "example.com", 
    "local_part": "jane",
    "name": "Jane Smith",
    "password_recovery_email": "jane@personal.com"
})
```

### Forwarding Setup

```python
# Create forwarding rule
await client.call_tool("create_forwarding", {
    "domain": "example.com",
    "mailbox": "support", 
    "address": "external@company.com"
})
```

### Alias Management

```python
# Create alias pointing to multiple destinations
await client.call_tool("create_alias", {
    "domain": "example.com",
    "local_part": "team",
    "destinations": ["john@example.com", "jane@example.com"]
})
```

### Using Resources

```python
# Get mailbox data as resource
mailboxes = await client.read_resource("mailboxes://example.com")
```

## Integration with Claude Desktop

Install the server for use with Claude Desktop:

```bash
uv run fastmcp install main.py
```

Then configure your environment variables in the Claude Desktop MCP settings.

## Error Handling

The server includes comprehensive error handling for:
- Invalid API credentials
- Network connectivity issues
- Migadu API errors
- Malformed requests

All errors are returned as structured responses with details about the failure.

## Development

This project uses:
- **FastMCP** for MCP protocol implementation
- **httpx** for async HTTP requests
- **uv** for dependency management

To contribute:
1. Fork the repository
2. Create a feature branch
3. Make changes and test
4. Submit a pull request

## License

This project is open source. Check the LICENSE file for details.

## Support

- [Migadu API Documentation](https://migadu.com/api/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- Create issues for bugs or feature requests