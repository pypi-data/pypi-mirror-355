#!/usr/bin/env python3
"""
MCP resources for Migadu API
"""

from typing import Dict, Any
from fastmcp import FastMCP
from migadu_mcp.services.service_factory import get_service_factory


def register_resources(mcp: FastMCP):
    """Register resources with FastMCP instance"""
    
    @mcp.resource("mailboxes://{domain}")
    async def domain_mailboxes(domain: str) -> Dict[str, Any]:
        """Resource providing comprehensive overview of all email mailboxes configured for a domain.
        Returns detailed information for each mailbox including storage status, permissions, spam settings,
        autoresponder configuration, and account security options. Use this resource for domain-wide
        mailbox auditing, capacity planning, and organizational email infrastructure analysis.
        
        URI Format: mailboxes://example.org
        """
        factory = get_service_factory()
        service = factory.mailbox_service()
        return await service.list_mailboxes(domain)

    @mcp.resource("mailbox://{domain}/{local_part}")
    async def mailbox_details(domain: str, local_part: str) -> Dict[str, Any]:
        """Resource providing complete configuration details for a specific email mailbox. Includes
        authentication settings, protocol permissions (IMAP/POP3/ManageSieve), spam filtering configuration,
        autoresponder status, footer settings, allowlists/denylists, and security policies. Use this
        resource for detailed mailbox inspection, troubleshooting, and configuration verification.
        
        URI Format: mailbox://example.org/username
        """
        factory = get_service_factory()
        service = factory.mailbox_service()
        return await service.get_mailbox(domain, local_part)

    @mcp.resource("identities://{domain}/{mailbox}")
    async def mailbox_identities(domain: str, mailbox: str) -> Dict[str, Any]:
        """Resource providing all email identities (send-as addresses) configured for a specific mailbox.
        Shows additional email addresses the mailbox user can send from, each with their own permissions,
        display names, and access controls. Use this resource to audit send-as capabilities and manage
        role-based email address permissions within an organization.
        
        URI Format: identities://example.org/username
        """
        factory = get_service_factory()
        service = factory.identity_service()
        return await service.list_identities(domain, mailbox)

    @mcp.resource("forwardings://{domain}/{mailbox}")
    async def mailbox_forwardings(domain: str, mailbox: str) -> Dict[str, Any]:
        """Resource providing all external forwarding rules configured for a specific mailbox. Shows
        destination addresses, confirmation status, expiration settings, and active state for each
        forwarding rule. Use this resource to audit external message routing, verify forwarding
        confirmations, and manage temporary or scheduled forwarding arrangements.
        
        URI Format: forwardings://example.org/username
        """
        factory = get_service_factory()
        service = factory.mailbox_service()
        return await service.list_forwardings(domain, mailbox)

    @mcp.resource("aliases://{domain}")
    async def domain_aliases(domain: str) -> Dict[str, Any]:
        """Resource providing comprehensive overview of all email aliases configured for a domain.
        Shows forwarding addresses that redirect messages without storage, including destination
        addresses, internal-only status, and routing configuration. Use this resource for domain-wide
        forwarding audits, distribution list management, and email routing infrastructure analysis.
        
        URI Format: aliases://example.org
        """
        factory = get_service_factory()
        service = factory.alias_service()
        return await service.list_aliases(domain)

    @mcp.resource("rewrites://{domain}")
    async def domain_rewrites(domain: str) -> Dict[str, Any]:
        """Resource providing all pattern-based rewrite rules configured for a domain. Shows wildcard
        patterns, destination addresses, processing order, and rule configuration for dynamic email
        routing. Use this resource to audit pattern-based forwarding systems, verify rule precedence,
        and manage complex email routing scenarios that require wildcard matching.
        
        URI Format: rewrites://example.org
        """
        factory = get_service_factory()
        service = factory.rewrite_service()
        return await service.list_rewrites(domain)