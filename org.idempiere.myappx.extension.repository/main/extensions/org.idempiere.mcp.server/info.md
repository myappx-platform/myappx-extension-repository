# iDempiere MCP Server

**Summary:** Model Context Protocol (MCP) server for iDempiere — Streamable HTTP under `/mcp/`, enabling AI assistants and the AI orchestrator to query data, run processes, and manage records via tools.

## Features

* **MCP over HTTP:** Web context `/mcp/` (trailing slash required for clients).
* **Auth:** Bearer JWT from iDempiere REST; optional `create_auth_token` / `set_auth_token` tools.
* **Tools:** Business data, processes, server jobs, and related ERP actions (see upstream demos).
* **Ops tuning:** Env vars for session TTL, heartbeat, CORS, thread pool (`MCP_*`).

## Compatibility

* **iDempiere Version:** 14.0
* **Java Version:** 17+
* **Database:** PostgreSQL, Oracle
* **Requires:** `com.trekglobal.idempiere.rest.api` (install first via Extension Management)

## Database Changes

* Relies on REST Auth Token infrastructure from idempiere-rest. No separate MCP 2Pack required for basic use.

## Usage & Configuration

1. Install **iDempiere REST API** first.
2. Build: `mvn -f id-plugin-hengsin-idempiere-mcp/org.idempiere.mcp.server/pom.xml "-Drevision=1.0.0-SNAPSHOT" clean verify`
3. Install this extension, then restart if needed.
4. Inspector: `npx @modelcontextprotocol/inspector` → `http://localhost:18080/mcp/` with Bearer token.
5. Recommended before installing `org.idempiere.myappx.plugin.aic` for full tool-calling.

Status: proof-of-concept — use with care (upstream note).

## Author / Support

* **Upstream:** [hengsin/idempiere-mcp](https://github.com/hengsin/idempiere-mcp)
* **MyAppx fork:** `myappx-plugins/id-plugin-hengsin-idempiere-mcp`
* **Bundle:** `org.idempiere.mcp.server`
* **Documentation:** `id-plugin-hengsin-idempiere-mcp/README.md`
