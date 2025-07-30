<div align="center">

# 🔧 Migadu MCP Server

**Professional email management for Migadu hosting through the Model Context Protocol**

[![PyPI version](https://badge.fury.io/py/migadu-mcp.svg)](https://badge.fury.io/py/migadu-mcp)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Production Ready](https://img.shields.io/badge/Status-Production%20Ready-green.svg)](https://github.com/Michaelzag/migadu-mcp)

[![CI](https://github.com/Michaelzag/migadu-mcp/workflows/CI/badge.svg)](https://github.com/Michaelzag/migadu-mcp/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-pytest-blue.svg)](https://github.com/Michaelzag/migadu-mcp/actions/workflows/ci.yml)
[![Code Quality](https://img.shields.io/badge/code%20quality-ruff%20%2B%20mypy-blue.svg)](https://github.com/Michaelzag/migadu-mcp/actions/workflows/ci.yml)
[![Security](https://img.shields.io/badge/security-bandit-green.svg)](https://github.com/Michaelzag/migadu-mcp/actions/workflows/ci.yml)

</div>

---

A comprehensive MCP server for managing [Migadu](https://migadu.com/) email hosting services. This professional-grade integration provides complete control over mailboxes, aliases, identities, forwardings, and advanced email routing through an intuitive, agent-friendly API with enterprise-grade documentation and intelligent error handling.

Built with enterprise architecture patterns, the Migadu MCP Server bridges the gap between AI agents and professional email management by offering seamless integration with Migadu's email hosting platform. The server enables AI agents to manage complex email infrastructures with ease, providing comprehensive email administration capabilities through the Model Context Protocol.

### 🎯 Core Capabilities

- **Complete Email Infrastructure Management**: Full CRUD operations for mailboxes, aliases, identities, and routing rules
- **Intelligent Bulk Operations**: Smart batch processing with automatic API quirk handling and error recovery
- **Advanced Email Routing**: Pattern-based rewrites, conditional forwarding, and sophisticated alias management
- **Professional Administration**: Autoresponders, permission management, spam filtering, and security controls
- **Agent-Optimized Documentation**: Comprehensive endpoint descriptions with use cases, parameters, and best practices

### 🏢 About Migadu

[Migadu](https://migadu.com/) is a Swiss-based email hosting service that positions itself as "The Missing Email Service For Domains." Founded in 2014, Migadu offers standards-oriented email hosting with a unique approach to pricing and email management.

**Key Differentiators:**
- 🔓 **Unlimited Email Addresses** - Pricing based on usage, not address count
- 🔧 **Standards-Based** - Full SMTP/IMAP/POP3 support with no vendor lock-in
- 🔒 **Privacy-Focused** - Swiss company with no ads, tracking, or data mining
- 🔍 **Transparent Operations** - Open about limitations and focused on human email use
- 🏛️ **Independent & Bootstrapped** - Self-funded with user-aligned interests

*Perfect for individuals, families, web agencies, startups, and organizations requiring reliable, privacy-respecting email hosting with unlimited address flexibility.*

## ✨ Features

### 📧 Core Email Management
- **📬 Mailbox Operations** - Complete lifecycle management with authentication and permissions
- **🔄 Email Forwarding** - External forwarding with confirmation and expiration handling
- **📮 Alias Management** - Unlimited address forwarding without storage requirements
- **🆔 Identity Management** - Multiple send-as addresses with individual permissions
- **🤖 Autoresponders** - Automated out-of-office and notification systems

### ⚡ Advanced Capabilities
- **🔧 Bulk Operations** - Intelligent batch processing with API error handling
- **🎯 Pattern Routing** - Wildcard-based rewrite rules for dynamic email routing
- **🛡️ Security Controls** - Spam filtering, access permissions, and protocol restrictions
- **📊 Comprehensive Resources** - Structured data access through MCP resource system

### 🏗️ Enterprise Architecture
- **🔒 Production Ready** - Stable classification with comprehensive error handling
- **📚 Agent-Optimized** - Extensive documentation with use cases and examples
- **🏛️ Modular Design** - Clean separation of concerns with dependency injection
- **🔧 API Intelligence** - Automatic handling of Migadu API quirks and limitations

---

## 🚀 Quick Start

### Installation
```bash
uvx install migadu-mcp
```

### Configuration

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

---

## 📋 API Reference

### 📬 Mailbox Operations
- `list_mailboxes(domain)` / `list_my_mailboxes()` - Comprehensive mailbox inventory with permissions and settings
- `get_mailbox(domain, local_part)` / `get_my_mailbox(local_part)` - Detailed mailbox configuration and status
- `create_mailbox(domain, local_part, name, ...)` / `create_my_mailbox(...)` - Full lifecycle mailbox creation with flexible authentication
- `update_mailbox(domain, local_part, ...)` - Granular permission and configuration management
- `delete_mailbox(domain, local_part)` - Safe mailbox removal with automatic API quirk handling
- `bulk_delete_mailboxes(domain, local_parts)` - Intelligent batch operations with comprehensive error categorization
- `reset_mailbox_password(domain, local_part, new_password)` - Secure password management

### 📮 Email Routing & Aliases
- `list_aliases(domain)` / `list_my_aliases()` - Domain-wide alias inventory and configuration
- `create_alias(domain, local_part, destinations)` - Flexible email forwarding without storage overhead
- `update_alias(domain, local_part, destinations)` - Dynamic destination management
- `delete_alias(domain, local_part)` - Clean alias removal

### 🔄 External Forwarding
- `list_forwardings(domain, mailbox)` - External forwarding rules with confirmation status
- `create_forwarding(domain, mailbox, address)` - Verified external forwarding with confirmation workflow
- `update_forwarding(domain, mailbox, address, ...)` - Expiration and activation control
- `delete_forwarding(domain, mailbox, address)` - Safe forwarding rule removal

### 🆔 Identity Management
- `list_identities(domain, mailbox)` - Send-as address inventory with individual permissions
- `create_identity(domain, mailbox, local_part, name, password)` - Additional sending addresses with authentication
- `update_identity(domain, mailbox, identity, ...)` - Granular identity permission control
- `delete_identity(domain, mailbox, identity)` - Clean identity removal

### 🎯 Advanced Features
- `set_autoresponder(domain, local_part, active, subject, body, expires_on)` - Professional out-of-office management
- `list_rewrites(domain)` / `create_rewrite(...)` / `update_rewrite(...)` / `delete_rewrite(...)` - Pattern-based email routing with wildcard support

## 📊 MCP Resources

Structured data access through the MCP resource system:
- `mailboxes://domain.com` - Complete domain mailbox inventory with configurations
- `mailbox://domain.com/username` - Individual mailbox details and status information
- `aliases://domain.com` - Domain alias configurations and destination mappings
- `identities://domain.com/mailbox` - Mailbox identity permissions and settings
- `forwardings://domain.com/mailbox` - External forwarding rules and confirmation status

## 🔧 Advanced Capabilities

**Intelligent Bulk Operations**: The `bulk_delete_mailboxes` tool automatically handles Migadu's API behavior where successful deletions return 500 status codes, providing clear categorization of results.

**Enterprise Error Handling**: Comprehensive error management for API authentication, network issues, malformed requests, and service-specific quirks with detailed diagnostic information.

**Production Architecture**: Built with dependency injection, service patterns, and modular design for reliability and maintainability in production environments.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.