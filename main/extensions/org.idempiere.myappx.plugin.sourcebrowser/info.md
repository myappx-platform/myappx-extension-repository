# MyAppx Source Browser

**Summary:** Independent read-only OSGi source pack browser (tree, search, Monaco). Not a git working tree. Dictionary via `ODT2PackActivator`. Only honors `MYAPPX_SOURCE_*`.

## Features

* **Form:** menu **Source Browser** / **源码浏览** — west tree + search, center Monaco iframe.
* **HTTP:** `/sourcebrowser` — ticket-gated `GET /api/{status,tree,file,search}` plus static `viewer/`.
* **Sandbox:** skip `.git` / `target` / `node_modules` and typical secrets. Human cap ~1MB / 8000 lines.
* **OSGi:** other plugins may look up `ISourceBrowser` to open this form.
* **ODT:** installs `META-INF/ODTPackage_MYAPPX.SRB.xml` on start. No SQL migration.

## Compatibility

* **iDempiere:** 14.0 · **Java:** 17+ · **Database:** PostgreSQL
* **Requires:** MyAppx ODT (`org.idempiere.myappx.plugin.odt`)

## Database Changes

* ODT package **MyAppx Source Browser** (`EntityType=MYAPPX.SRB`, `VersionNo=2`): entity type, Form/Menu (+ zh_CN), `AD_TreeNodeMM`, SysConfig `MYAPPX_SOURCE_ENABLED` / `MYAPPX_SOURCE_ROOTS`.

## Usage

1. Install **after** ODT. PackIn runs when XML `VersionNo` is newer than the database.
2. Assemble the pack. Standard: `{IDEMPIERE_HOME}/data/workspace/sources`. Portable: leave `MYAPPX_SOURCE_ROOTS` empty; `bin\env.bat` sets `IDEMPIERE_MYAPPX_SOURCE_ROOTS`.
3. `MYAPPX_SOURCE_ENABLED=Y`. Reset Cache. Grant the Form.
4. Build: `mvn -f myappx-plugin-sourcebrowser/pom.xml "-Drevision=14.0.0-SNAPSHOT" clean verify`

Docs: `myappx-plugin-sourcebrowser/readme.md` · `README.en.md`.

## Author / Support

* **Developer:** Ken Longnan
* **Source / Bundle:** `myappx-plugins/myappx-plugin-sourcebrowser` · `org.idempiere.myappx.plugin.sourcebrowser`
