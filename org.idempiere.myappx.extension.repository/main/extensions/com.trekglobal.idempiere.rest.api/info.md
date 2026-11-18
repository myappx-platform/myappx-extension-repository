# iDempiere REST API

**Summary:** OSGi JAX-RS REST API for iDempiere — JWT authentication, model/window/process resources, and the `/api` web context used by other extensions (AI chat login, MCP tools, integrations).

## Features

* **Auth:** `POST/PUT /api/v1/auth/tokens` — JWT access tokens for REST and SSE clients.
* **Models & windows:** CRUD-style access to PO, attachments, windows/tabs, forms.
* **Processes & files:** Run processes/reports; download generated files.
* **Ops:** caches, nodes/logs, servers/schedulers, info windows, workflow actions.
* **Web context:** `Web-ContextPath: api` (e.g. `http://host:18080/api/v1/...`).

## Compatibility

* **iDempiere Version:** 14.0 (bundle also builds against 12+ base)
* **Java Version:** 17+
* **Database:** PostgreSQL, Oracle
* **Requires:** `org.adempiere.base` (core)

## Database Changes

* Uses iDempiere REST Auth Token / related AD objects as documented upstream. Prefer installing via Extension Management so dependent extensions can record this package as installed.

## Usage & Configuration

1. Build: `mvn -f id-plugin-bxservice-idempiere-rest/pom.xml clean verify`
2. Install via Extension Management (or OSGi). Ensure the bundle starts (`sta com.trekglobal.idempiere.rest.api` if needed).
3. Docs: [idempiere-rest-docs](https://bxservice.github.io/idempiere-rest-docs/)
4. Smoke test: `POST /api/v1/auth/tokens` with user credentials.

Install **before** `org.idempiere.mcp.server` and `org.idempiere.myappx.plugin.aic`.

## Author / Support

* **Vendor:** Trek Global / bxservice
* **Upstream:** [bxservice/idempiere-rest](https://github.com/bxservice/idempiere-rest)
* **MyAppx fork:** `myappx-plugins/id-plugin-bxservice-idempiere-rest`
* **Bundle:** `com.trekglobal.idempiere.rest.api`
