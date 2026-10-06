# iDempiere AI Core

**Summary:** Central AI orchestrator for iDempiere — LLM providers (Bedrock / SiliconFlow), MCP tool use, desktop Context AI Copilot, and chat APIs under `/ai`.

## Features

* **Orchestration:** User messages → LLM (AWS Bedrock or OpenAI-compatible HTTP) with MCP function calling.
* **Desktop Copilot:** Toolbar **Context AI** (`AiDesktop`) embeds **AI Copilot** in the East panel; write tools can require Approve/Deny.
* **REST / SSE:** Web context `/ai` — `/ai/sse`, `/ai/v1/chat/*`, `/ai/status`. Login via iDempiere REST JWT.
* **Dictionary:** ODT pack-in `ODTPackage_MYAPPX.AIC.xml` (VersionNo 2) plus `ODT2Pack-1.0.0_SYSTEM_MYAPPX.AIC.zip` (`AI_Context` recipes).
* **Quota:** `AI_TokenQuota` plus SysConfig fallbacks; over limit returns HTTP 429.

## Compatibility

* **iDempiere Version:** 14.0
* **Java Version:** 17+
* **Database:** PostgreSQL (ODT pack-in). Oracle not shipped for this extension.
* **Requires (install first via Extension Management):**
  1. `org.idempiere.myappx.plugin.odt`
  2. `com.trekglobal.idempiere.rest.api`
  3. `org.idempiere.mcp.server`

## Database Changes

* ODT on bundle start: windows **LLM Provider**, **System Context**, **Conversation**, **Token Quota**; tables `AI_LLMProvider`, `AI_Conversation`, `AI_ConversationMessage`, `AI_Context`, `AI_TokenQuota`; SysConfig and **Rebuild AI Knowledge Index**.
* Seed: tenant + model-scope `AI_Context` rows from the ODT2Pack zip.

## Usage & Configuration

1. Install **ODT → REST → MCP → AI**, then **full restart**.
2. Create a default **LLM Provider** (`IsDefault = Y`; type **BED** or **SIF**).
3. After login, click toolbar **Context AI**.
4. Build: `mvn "-Drevision=14.0.0-SNAPSHOT" clean verify -pl myappx-plugin-odt/org.idempiere.myappx.plugin.odt,myappx-plugin-aicopilot -am`

Docs: `myappx-plugin-aicopilot/README.md` (`README.zh-CN.md`), `docs/Guide.md` (`Guide.zh-CN.md`), `docs/Data.md` (`Data.zh-CN.md`).

## Author / Support

* **Upstream:** [alanlesc1/idempiere-ai](https://github.com/alanlesc1/idempiere-ai)
* **MyAppx fork:** `myappx-plugins/myappx-plugin-aicopilot`
* **Bundle:** `org.idempiere.myappx.plugin.aic`
* **Entity Type:** `AI`
