#!/usr/bin/env python3
"""
Migadu MCP Server - View and manage Migadu mailboxes
"""

import os
import base64
from typing import Optional, List, Dict, Any
import httpx
from fastmcp import FastMCP

# Initialize FastMCP server
mcp: FastMCP = FastMCP("Migadu Mailbox Manager")


class MigaduClient:
    """Simple HTTP client for Migadu API"""
    
    def __init__(self, email: str, api_key: str):
        credentials = base64.b64encode(f"{email}:{api_key}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.migadu.com/v1"
    
    async def request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to Migadu API"""
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.base_url}{path}",
                headers=self.headers,
                **kwargs
            )
            if response.status_code >= 400:
                raise Exception(f"API Error {response.status_code}: {response.text}")
            return response.json()

# Global client instance - will be initialized when server starts
_migadu_client: Optional[MigaduClient] = None

def get_migadu_client() -> MigaduClient:
    """Get configured Migadu client"""
    global _migadu_client
    if _migadu_client is None:
        # Initialize from environment variables
        email = os.getenv("MIGADU_EMAIL")
        api_key = os.getenv("MIGADU_API_KEY")
        
        if not email or not api_key:
            raise Exception("Please set MIGADU_EMAIL and MIGADU_API_KEY environment variables")
        
        _migadu_client = MigaduClient(email, api_key)
    
    return _migadu_client

def get_default_domain() -> str:
    """Get the default domain from environment variables"""
    domain = os.getenv("MIGADU_DOMAIN")
    if not domain:
        raise Exception("Please set MIGADU_DOMAIN environment variable")
    return domain

# === MAILBOX MANAGEMENT TOOLS ===

@mcp.tool
async def list_mailboxes(domain: str) -> Dict[str, Any]:
    """List all mailboxes for a domain"""
    client = get_migadu_client()
    return await client.request("GET", f"/domains/{domain}/mailboxes")

@mcp.tool
async def list_my_mailboxes() -> Dict[str, Any]:
    """List all mailboxes for the default configured domain"""
    domain = get_default_domain()
    client = get_migadu_client()
    return await client.request("GET", f"/domains/{domain}/mailboxes")

@mcp.tool
async def get_mailbox(domain: str, local_part: str) -> Dict[str, Any]:
    """Get details of a specific mailbox"""
    client = get_migadu_client()
    return await client.request("GET", f"/domains/{domain}/mailboxes/{local_part}")

async def _create_mailbox_internal(
    domain: str,
    local_part: str,
    name: str,
    password: Optional[str] = None,
    password_recovery_email: Optional[str] = None,
    is_internal: bool = False,
    forwarding_to: Optional[str] = None
) -> Dict[str, Any]:
    """Internal function to create a new mailbox"""
    client = get_migadu_client()
    
    data = {
        "local_part": local_part,
        "name": name,
        "is_internal": is_internal
    }
    
    if password:
        data["password"] = password
    elif password_recovery_email:
        data["password_method"] = "invitation"
        data["password_recovery_email"] = password_recovery_email
    
    if forwarding_to:
        data["forwarding_to"] = forwarding_to
    
    return await client.request("POST", f"/domains/{domain}/mailboxes", json=data)

@mcp.tool
async def create_mailbox(
    domain: str,
    local_part: str,
    name: str,
    password: Optional[str] = None,
    password_recovery_email: Optional[str] = None,
    is_internal: bool = False,
    forwarding_to: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new mailbox"""
    return await _create_mailbox_internal(
        domain, local_part, name, password,
        password_recovery_email, is_internal, forwarding_to
    )

@mcp.tool
async def create_my_mailbox(
    local_part: str,
    name: str,
    password: Optional[str] = None,
    password_recovery_email: Optional[str] = None,
    is_internal: bool = False,
    forwarding_to: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new mailbox on the default configured domain"""
    domain = get_default_domain()
    return await _create_mailbox_internal(
        domain, local_part, name, password,
        password_recovery_email, is_internal, forwarding_to
    )

@mcp.tool
async def get_my_mailbox(local_part: str) -> Dict[str, Any]:
    """Get details of a specific mailbox on the default domain"""
    domain = get_default_domain()
    client = get_migadu_client()
    return await client.request("GET", f"/domains/{domain}/mailboxes/{local_part}")

@mcp.tool
async def list_my_aliases() -> Dict[str, Any]:
    """List all aliases for the default configured domain"""
    domain = get_default_domain()
    client = get_migadu_client()
    return await client.request("GET", f"/domains/{domain}/aliases")

@mcp.tool
async def update_mailbox(
    domain: str, 
    local_part: str, 
    name: Optional[str] = None,
    may_send: Optional[bool] = None,
    may_receive: Optional[bool] = None,
    may_access_imap: Optional[bool] = None,
    may_access_pop3: Optional[bool] = None,
    spam_action: Optional[str] = None,
    spam_aggressiveness: Optional[str] = None
) -> Dict[str, Any]:
    """Update mailbox settings"""
    client = get_migadu_client()
    
    data: Dict[str, Any] = {}
    if name is not None:
        data["name"] = name
    if may_send is not None:
        data["may_send"] = may_send
    if may_receive is not None:
        data["may_receive"] = may_receive
    if may_access_imap is not None:
        data["may_access_imap"] = may_access_imap
    if may_access_pop3 is not None:
        data["may_access_pop3"] = may_access_pop3
    if spam_action is not None:
        data["spam_action"] = spam_action
    if spam_aggressiveness is not None:
        data["spam_aggressiveness"] = spam_aggressiveness
    
    return await client.request("PUT", f"/domains/{domain}/mailboxes/{local_part}", json=data)

@mcp.tool
async def delete_mailbox(domain: str, local_part: str) -> Dict[str, Any]:
    """Delete a mailbox"""
    client = get_migadu_client()
    return await client.request("DELETE", f"/domains/{domain}/mailboxes/{local_part}")

@mcp.tool
async def bulk_delete_mailboxes(domain: str, local_parts: List[str]) -> Dict[str, Any]:
    """Delete multiple mailboxes in bulk (handles Migadu API 500-error-means-success bug)"""
    client = get_migadu_client()
    results: Dict[str, Any] = {
        "deleted": [],
        "already_gone": [],
        "failed": [],
        "total_requested": len(local_parts)
    }
    
    for local_part in local_parts:
        try:
            await client.request("DELETE", f"/domains/{domain}/mailboxes/{local_part}")
            # If we get here without exception, it actually succeeded
            results["deleted"].append(local_part)
        except Exception as e:
            error_msg = str(e)
            if "500" in error_msg:
                # 500 error = successful deletion due to API bug
                results["deleted"].append(local_part)
            elif "404" in error_msg or "no such mailbox" in error_msg.lower():
                # Already deleted
                results["already_gone"].append(local_part)
            else:
                # Actual failure
                results["failed"].append({"local_part": local_part, "error": error_msg})
    
    return results

@mcp.tool
async def reset_mailbox_password(domain: str, local_part: str, new_password: str) -> Dict[str, Any]:
    """Reset mailbox password"""
    client = get_migadu_client()
    data = {"password": new_password}
    return await client.request("PUT", f"/domains/{domain}/mailboxes/{local_part}", json=data)

# === AUTORESPONDER TOOLS ===

@mcp.tool
async def set_autoresponder(
    domain: str, 
    local_part: str, 
    active: bool,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    expires_on: Optional[str] = None
) -> Dict[str, Any]:
    """Configure mailbox autoresponder"""
    client = get_migadu_client()
    
    data: Dict[str, Any] = {"autorespond_active": active}
    if subject:
        data["autorespond_subject"] = subject
    if body:
        data["autorespond_body"] = body
    if expires_on:
        data["autorespond_expires_on"] = expires_on
    
    return await client.request("PUT", f"/domains/{domain}/mailboxes/{local_part}", json=data)

# === IDENTITY MANAGEMENT TOOLS ===

@mcp.tool
async def list_identities(domain: str, mailbox: str) -> Dict[str, Any]:
    """List all identities for a mailbox"""
    client = get_migadu_client()
    return await client.request("GET", f"/domains/{domain}/mailboxes/{mailbox}/identities")

@mcp.tool
async def create_identity(
    domain: str, 
    mailbox: str, 
    local_part: str, 
    name: str,
    password: str
) -> Dict[str, Any]:
    """Create a new identity for a mailbox"""
    client = get_migadu_client()
    data = {
        "local_part": local_part,
        "name": name,
        "password": password
    }
    return await client.request("POST", f"/domains/{domain}/mailboxes/{mailbox}/identities", json=data)

@mcp.tool
async def get_identity(domain: str, mailbox: str, identity: str) -> Dict[str, Any]:
    """Get details of a specific identity"""
    client = get_migadu_client()
    return await client.request("GET", f"/domains/{domain}/mailboxes/{mailbox}/identities/{identity}")

@mcp.tool
async def update_identity(
    domain: str, 
    mailbox: str, 
    identity: str,
    name: Optional[str] = None,
    may_send: Optional[bool] = None,
    may_receive: Optional[bool] = None
) -> Dict[str, Any]:
    """Update identity settings"""
    client = get_migadu_client()
    
    data: Dict[str, Any] = {}
    if name is not None:
        data["name"] = name
    if may_send is not None:
        data["may_send"] = may_send
    if may_receive is not None:
        data["may_receive"] = may_receive
    
    return await client.request("PUT", f"/domains/{domain}/mailboxes/{mailbox}/identities/{identity}", json=data)

@mcp.tool
async def delete_identity(domain: str, mailbox: str, identity: str) -> Dict[str, Any]:
    """Delete an identity"""
    client = get_migadu_client()
    return await client.request("DELETE", f"/domains/{domain}/mailboxes/{mailbox}/identities/{identity}")

# === FORWARDING MANAGEMENT TOOLS ===

@mcp.tool
async def list_forwardings(domain: str, mailbox: str) -> Dict[str, Any]:
    """List all forwardings for a mailbox"""
    client = get_migadu_client()
    return await client.request("GET", f"/domains/{domain}/mailboxes/{mailbox}/forwardings")

@mcp.tool
async def create_forwarding(domain: str, mailbox: str, address: str) -> Dict[str, Any]:
    """Create a new forwarding for a mailbox"""
    client = get_migadu_client()
    data = {"address": address}
    return await client.request("POST", f"/domains/{domain}/mailboxes/{mailbox}/forwardings", json=data)

@mcp.tool
async def get_forwarding(domain: str, mailbox: str, address: str) -> Dict[str, Any]:
    """Get details of a specific forwarding"""
    client = get_migadu_client()
    # URL encode the email address
    encoded_address = address.replace("@", "%40")
    return await client.request("GET", f"/domains/{domain}/mailboxes/{mailbox}/forwardings/{encoded_address}")

@mcp.tool
async def update_forwarding(
    domain: str, 
    mailbox: str, 
    address: str,
    is_active: Optional[bool] = None,
    expires_on: Optional[str] = None,
    remove_upon_expiry: Optional[bool] = None
) -> Dict[str, Any]:
    """Update forwarding settings"""
    client = get_migadu_client()
    
    data: Dict[str, Any] = {}
    if is_active is not None:
        data["is_active"] = is_active
    if expires_on is not None:
        data["expires_on"] = expires_on
    if remove_upon_expiry is not None:
        data["remove_upon_expiry"] = remove_upon_expiry
    
    encoded_address = address.replace("@", "%40")
    return await client.request("PUT", f"/domains/{domain}/mailboxes/{mailbox}/forwardings/{encoded_address}", json=data)

@mcp.tool
async def delete_forwarding(domain: str, mailbox: str, address: str) -> Dict[str, Any]:
    """Delete a forwarding"""
    client = get_migadu_client()
    encoded_address = address.replace("@", "%40")
    return await client.request("DELETE", f"/domains/{domain}/mailboxes/{mailbox}/forwardings/{encoded_address}")

# === ALIAS MANAGEMENT TOOLS ===

@mcp.tool
async def list_aliases(domain: str) -> Dict[str, Any]:
    """List all aliases for a domain"""
    client = get_migadu_client()
    return await client.request("GET", f"/domains/{domain}/aliases")

@mcp.tool
async def create_alias(
    domain: str, 
    local_part: str, 
    destinations: List[str],
    is_internal: bool = False
) -> Dict[str, Any]:
    """Create a new alias"""
    client = get_migadu_client()
    data = {
        "local_part": local_part,
        "destinations": ",".join(destinations),
        "is_internal": is_internal
    }
    return await client.request("POST", f"/domains/{domain}/aliases", json=data)

@mcp.tool
async def get_alias(domain: str, local_part: str) -> Dict[str, Any]:
    """Get details of a specific alias"""
    client = get_migadu_client()
    return await client.request("GET", f"/domains/{domain}/aliases/{local_part}")

@mcp.tool
async def update_alias(domain: str, local_part: str, destinations: List[str]) -> Dict[str, Any]:
    """Update alias destinations"""
    client = get_migadu_client()
    data = {"destinations": ",".join(destinations)}
    return await client.request("PUT", f"/domains/{domain}/aliases/{local_part}", json=data)

@mcp.tool
async def delete_alias(domain: str, local_part: str) -> Dict[str, Any]:
    """Delete an alias"""
    client = get_migadu_client()
    return await client.request("DELETE", f"/domains/{domain}/aliases/{local_part}")

# === REWRITE MANAGEMENT TOOLS ===

@mcp.tool
async def list_rewrites(domain: str) -> Dict[str, Any]:
    """List all rewrites for a domain"""
    client = get_migadu_client()
    return await client.request("GET", f"/domains/{domain}/rewrites")

@mcp.tool
async def create_rewrite(
    domain: str, 
    name: str, 
    local_part_rule: str, 
    destinations: List[str]
) -> Dict[str, Any]:
    """Create a new rewrite rule"""
    client = get_migadu_client()
    data = {
        "name": name,
        "local_part_rule": local_part_rule,
        "destinations": ",".join(destinations)
    }
    return await client.request("POST", f"/domains/{domain}/rewrites", json=data)

@mcp.tool
async def get_rewrite(domain: str, name: str) -> Dict[str, Any]:
    """Get details of a specific rewrite"""
    client = get_migadu_client()
    return await client.request("GET", f"/domains/{domain}/rewrites/{name}")

@mcp.tool
async def update_rewrite(
    domain: str, 
    name: str,
    new_name: Optional[str] = None,
    local_part_rule: Optional[str] = None,
    destinations: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Update rewrite settings"""
    client = get_migadu_client()
    
    data: Dict[str, Any] = {}
    if new_name is not None:
        data["name"] = new_name
    if local_part_rule is not None:
        data["local_part_rule"] = local_part_rule
    if destinations is not None:
        data["destinations"] = ",".join(destinations)
    
    return await client.request("PUT", f"/domains/{domain}/rewrites/{name}", json=data)

@mcp.tool
async def delete_rewrite(domain: str, name: str) -> Dict[str, Any]:
    """Delete a rewrite rule"""
    client = get_migadu_client()
    return await client.request("DELETE", f"/domains/{domain}/rewrites/{name}")

# === RESOURCES ===

@mcp.resource("mailboxes://{domain}")
async def domain_mailboxes(domain: str) -> Dict[str, Any]:
    """Get all mailboxes for a domain as a resource"""
    client = get_migadu_client()
    return await client.request("GET", f"/domains/{domain}/mailboxes")

@mcp.resource("mailbox://{domain}/{local_part}")
async def mailbox_details(domain: str, local_part: str) -> Dict[str, Any]:
    """Get detailed information about a specific mailbox"""
    client = get_migadu_client()
    return await client.request("GET", f"/domains/{domain}/mailboxes/{local_part}")

@mcp.resource("identities://{domain}/{mailbox}")
async def mailbox_identities(domain: str, mailbox: str) -> Dict[str, Any]:
    """Get all identities for a mailbox"""
    client = get_migadu_client()
    return await client.request("GET", f"/domains/{domain}/mailboxes/{mailbox}/identities")

@mcp.resource("forwardings://{domain}/{mailbox}")
async def mailbox_forwardings(domain: str, mailbox: str) -> Dict[str, Any]:
    """Get all forwardings for a mailbox"""
    client = get_migadu_client()
    return await client.request("GET", f"/domains/{domain}/mailboxes/{mailbox}/forwardings")

@mcp.resource("aliases://{domain}")
async def domain_aliases(domain: str) -> Dict[str, Any]:
    """Get all aliases for a domain"""
    client = get_migadu_client()
    return await client.request("GET", f"/domains/{domain}/aliases")

@mcp.resource("rewrites://{domain}")
async def domain_rewrites(domain: str) -> Dict[str, Any]:
    """Get all rewrites for a domain"""
    client = get_migadu_client()
    return await client.request("GET", f"/domains/{domain}/rewrites")

# === PROMPTS ===

@mcp.prompt
def mailbox_creation_wizard(domain: str, user_requirements: str) -> str:
    """Generate a step-by-step plan for creating mailboxes based on requirements"""
    return f"""
Please help me create mailboxes for domain {domain} based on these requirements:
{user_requirements}

Consider the following options:
1. Basic mailbox with password
2. Mailbox with invitation email for user to set password
3. Internal-only mailbox (no external email reception)
4. Mailbox with automatic forwarding
5. Mailbox with specific permissions (IMAP, POP3, etc.)

Provide a detailed plan with the specific create_mailbox commands needed.
"""

@mcp.prompt
def bulk_operation_planner(domain: str, operation_type: str, targets: str) -> str:
    """Plan bulk operations for multiple mailboxes or aliases"""
    return f"""
Help me plan a bulk {operation_type} operation for domain {domain}.
Targets: {targets}

Provide step-by-step commands and consider:
1. Order of operations to avoid conflicts
2. Error handling and rollback procedures
3. Verification steps after completion
4. Best practices for the specific operation type

Generate the specific tool commands needed.
"""

def main():
    """Entry point for the console script"""
    mcp.run()


if __name__ == "__main__":
    main()
