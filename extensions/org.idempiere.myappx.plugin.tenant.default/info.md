# MyAppx Tenant Default

**Summary:** Pre-provisions a **Default** tenant (client + org + admin role seed) and Pack-in system/tenant 2Pack archives for a repeatable low-code multi-tenant baseline.

## Features

* **Default tenant bootstrap:** Creates `AD_Client` / `AD_Org` named **Default** with fixed UUID seeds when missing.
* **System entity type:** Registers `EntityType=DEFAULT` with `ModelPackage=org.idempiere.myappx.plugin.tenant.x`.
* **Tenant dictionary Pack-in:** Roles, users, validations, `AD_UserDef_*`, toolbar restrictions for the Default tenant.
* **Custom Initial Setup:** `CustomInitialClientSetup` process for tenant creation aligned with Pack UUIDs.

## Compatibility

* **iDempiere Version:** 14.0
* **Java Version:** 17+
* **Database:** PostgreSQL
* **Requires:** MyAppx ODT (`org.idempiere.myappx.plugin.odt`)

## Database Changes

* **System PackIn:** `ODT2Pack-1.0.0_SYSTEM_Tenant_Default.zip`, optional `ODT2Pack-1.0.2_SYSTEM_DefaultCustomInitialSetup.zip`.
* **Tenant PackIn:** `ODT2Pack-1.0.1_Default_Tenant.zip` (bundled under `META-INF/`).
* **Runtime:** May create **Default** client/org on first bundle start via Activator.

## Usage & Configuration

Install **after** ODT (uses `ODT2PackActivator`). Suitable for empty or fresh iDempiere databases that need a starter tenant.

## Author / Support

* **Developer:** Ken Longnan
* **Source Code:** `myappx-plugins/myappx-plugin-tenant-default`
* **Documentation:** `myappx-plugin-tenant-default/readme.md`
