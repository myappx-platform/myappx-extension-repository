# MyAppx ZZZ

**Summary:** System-level MyAppx customization plugin — tenant-scoped AD table validation rules, AD_Role name uniqueness (Java + Callout + DB index), and ODT/2Pack bootstrap via `ODT2PackActivator`.

## Features

* **Role name uniqueness:** `@BeforeNew` / `@BeforeChange` validation and `CalloutRoleName` on `AD_Role.Name` within the same tenant.
* **Tenant-scoped table rules:** Dynamic validation on `AD_User`, `AD_Role`, sessions, trees, change logs, etc.
* **ODT + 2Pack:** Installs `META-INF/ODTPackage.xml` and `ODT2Pack-1.0.0_SYSTEM_MYAPPX.ZZZ.zip` on bundle start.

## Compatibility

* **iDempiere Version:** 14.0
* **Java Version:** 17+
* **Database:** PostgreSQL
* **Requires:** MyAppx ODT (`org.idempiere.myappx.plugin.odt`)

## Database Changes

* **System PackIn:** ODT package **MyAppx ZZZ** (`EntityType=MYAPPX.ZZZ`) and 2Pack zip for table validation rules and forced SQL.
* **AD objects:** Entity type, rules, references, InfoWindow, unique index on `AD_Role` (`AD_Client_ID`, `Name`).

## Usage & Configuration

Install **after** ODT. On bundle start, `Activator` (extends `ODT2PackActivator`) runs ODT install then Pack-in of `ODT2Pack-*.zip` resources.

## Author / Support

* **Developer:** Ken Longnan
* **Source Code:** `myappx-plugins/myappx-plugin-zzz`
* **Documentation:** `myappx-plugin-zzz/readme.md`
