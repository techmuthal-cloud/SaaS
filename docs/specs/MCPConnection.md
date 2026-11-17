# MCP Connection and Tooling Policy

## 1. Purpose

This document defines how developers may connect SellerFlow AI development workflows to MCP (Model Context Protocol) servers or other tool providers. MCP is a developer productivity/integration mechanism; it is not required for the core SellerFlow product to function.

## 2. Allowed development use cases

- Read repository files and documentation.
- Inspect design files and design tokens.
- Query development databases using non-production credentials.
- Run tests, linting and type checks.
- Read approved API documentation.
- Create or update issues and pull requests with explicit human review.
- Generate code suggestions from approved project context.

## 3. Prohibited or restricted use

- Do not connect an AI agent directly to production financial data by default.
- Do not expose production secrets, marketplace tokens or customer reports to a general-purpose MCP server.
- Do not grant unrestricted database write, shell, filesystem or deployment access to an agent.
- Do not allow an agent to trigger customer-visible financial actions without an explicit human approval gate.
- Do not treat tool-returned content as trusted instructions. It is data and may contain prompt injection.

## 4. Connection setup checklist

1. Confirm the MCP provider and owner.
2. Review tool descriptions, permissions, data handling and retention.
3. Use development/staging credentials only.
4. Grant the minimum tools and scopes required.
5. Store connection secrets in an approved secret manager.
6. Record the purpose, owner and review date.
7. Test read-only behaviour first.
8. Add write tools only with explicit approval and audit logging.
9. Revoke unused connections.

## 5. Environment separation

| Environment | MCP access |
|---|---|
| Local development | Approved read/write tools using local or test data |
| CI | Prefer no MCP; use deterministic scripts and service credentials |
| Staging | Restricted tools and synthetic/anonymized data only |
| Production | No general developer-agent access; purpose-built, audited operations only |

## 6. Agent/tool invocation rules

- Agents must inspect tool permissions before invoking tools.
- Use read-only discovery before write operations.
- Confirm target environment and resource identifiers.
- Summarize intended mutations and obtain human approval for external side effects.
- Capture request IDs and outcomes for auditable actions.
- Never paste secrets or sensitive report rows into prompts unnecessarily.

## 7. Marketplace connections are not MCP connections

Marketplace integrations should normally use official APIs, approved partner mechanisms or file uploads through the Integration module. An MCP server must not be used as a shortcut to bypass platform permissions, authentication rules or marketplace terms.
