# Migadu MCP Server

Manage Migadu email hosting through the Model Context Protocol.

## Features

- **Mailbox Management**: Create, delete, update mailboxes and passwords
- **Email Forwarding**: Configure forwarding rules
- **Alias Management**: Create and manage email aliases
- **Bulk Operations**: Efficient multi-mailbox operations
- **Identity Management**: Handle multiple email identities
- **Autoresponders**: Configure out-of-office messages

## Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "migadu": {
      "command": "uvx",
      "args": ["migadu-mcp"],
      "env": {
        "MIGADU_EMAIL": "admin@yourdomain.com",
        "MIGADU_API_KEY": "your-api-key",
        "MIGADU_DOMAIN": "yourdomain.com"
      }
    }
  }
}
```

Get your API key from [Migadu Admin > My Account > API Keys](https://admin.migadu.com/account/api/keys).

## Available Tools

### Mailbox Operations
- `list_mailboxes(domain)` / `list_my_mailboxes()`
- `get_mailbox(domain, local_part)` / `get_my_mailbox(local_part)`
- `create_mailbox(domain, local_part, name, ...)` / `create_my_mailbox(...)`
- `update_mailbox(domain, local_part, ...)`
- `delete_mailbox(domain, local_part)`
- `bulk_delete_mailboxes(domain, local_parts)` - Handles Migadu API quirks
- `reset_mailbox_password(domain, local_part, new_password)`

### Email Routing
- `list_aliases(domain)` / `list_my_aliases()`
- `create_alias(domain, local_part, destinations)`
- `update_alias(domain, local_part, destinations)`
- `delete_alias(domain, local_part)`

### Forwarding
- `list_forwardings(domain, mailbox)`
- `create_forwarding(domain, mailbox, address)`
- `update_forwarding(domain, mailbox, address, ...)`
- `delete_forwarding(domain, mailbox, address)`

### Identity Management
- `list_identities(domain, mailbox)`
- `create_identity(domain, mailbox, local_part, name, password)`
- `update_identity(domain, mailbox, identity, ...)`
- `delete_identity(domain, mailbox, identity)`

### Advanced Features
- `set_autoresponder(domain, local_part, active, subject, body, expires_on)`
- `list_rewrites(domain)` / `create_rewrite(...)` / `update_rewrite(...)` / `delete_rewrite(...)`

## Resources

Access structured data:
- `mailboxes://domain.com` - All mailboxes
- `mailbox://domain.com/username` - Specific mailbox details
- `aliases://domain.com` - Domain aliases
- `identities://domain.com/mailbox` - Mailbox identities
- `forwardings://domain.com/mailbox` - Forwarding rules

## Special Features

**Bulk Delete**: The `bulk_delete_mailboxes` tool properly handles Migadu's API behavior where successful deletions return 500 status codes.

**Error Handling**: Comprehensive error handling for API authentication, network issues, and malformed requests.

## License

MIT License - see LICENSE file for details.