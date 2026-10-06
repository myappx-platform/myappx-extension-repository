# MyAppx Extension Repository

**Language:** English | [中文](README.md)

Extension catalog for **MyAppx / iDempiere 14**. This project is the OSGi web bundle `org.idempiere.myappx.extension.repository` and serves the catalog over HTTP to **Extension Management**.

Spec: [extension-spec.md](extension-spec.md) · Schema: [metadata-schema.json](metadata-schema.json)  
Upstream layout: [iDempiere Extension Repository](https://github.com/idempiere/idempiere-extension-repository)

| Item | Value |
|------|--------|
| iDempiere | 14 |
| Bundle | `org.idempiere.myappx.extension.repository` |
| Web-ContextPath | `/myappx-extension-repository` |
| Default base URL | `http://127.0.0.1:18080/myappx-extension-repository` |
| Inventory / install order | [`extensions.list`](extensions.list) |
| Source metadata | `extensions/<Bundle-SymbolicName>/` (1:1 with list) |
| Generated catalog | `main/` (`index.json`, extensions, bundles), packed into this bundle |
| Deploy | Copy this bundle into the server `plugins/` directory |
| JVM property | `-DIDEMPIERE_EXTENSION_REPOSITORY=...` |
| Web UI | **System Admin → Extension Management** |

---

## Contents

1. [Role](#1-role)
2. [Layout](#2-layout)
3. [HTTP layout and URLs](#3-http-layout-and-urls)
4. [Source vs publish](#4-source-vs-publish)
5. [extensions.list](#5-extensionslist)
6. [Publish workflow](#6-publish-workflow)
7. [Scripts and options](#7-scripts-and-options)
8. [Add or remove an extension](#8-add-or-remove-an-extension)
9. [metadata.json](#9-metadatajson)
10. [Regenerate index only](#10-regenerate-index-only)
11. [Troubleshooting](#11-troubleshooting)
12. [Related docs](#12-related-docs)

---

## 1. Role

Extension Management reads this catalog to list installable extensions (name, version, dependencies) and downloads JARs from each `downloadUrl`.

This bundle serves the catalog from its `Web-ContextPath`. The catalog is not packed into `org.adempiere.server`. [`extensions.list`](extensions.list) is the single source of truth: only listed extensions are published, and list order is the install order (dependencies first). `extensions/` must be **1:1** with the list. Removing an extension deletes it from both the list and `extensions/`.

This bundle is platform infrastructure. Do not add it to `extensions.list`. It serves the catalog, so Extension Management cannot install it.

---

## 2. Layout

```text
myappx-extension-repository/
├── META-INF/MANIFEST.MF          # Web-ContextPath: /myappx-extension-repository
├── WEB-INF/web.xml               # DefaultServlet, dirAllowed=false
├── extensions.list               # Inventory + install order (source of truth)
├── extensions/                   # Source metadata; 1:1 with the list; not packed
│   └── <Bundle-SymbolicName>/
│       ├── info.md
│       ├── CHANGELOG.md          # optional
│       ├── assets/               # optional
│       └── <version>/
│           └── metadata.json
├── scripts/
│   ├── publish.py                # Build main/
│   └── generate_index.py         # Build index.json
├── publish.bat                   # Local catalog
├── main/                         # Generated HTTP catalog (packed into the bundle)
│   ├── index.json
│   ├── extensions/
│   └── bundles/*.jar             # gitignored; copied from Maven target on publish
├── extension-spec.md
└── metadata-schema.json
```

`build.properties` packs `META-INF/`, `WEB-INF/web.xml`, `main/`, and `.` (compiled classes, including the catalog URL filter). README, scripts, and `extensions/` are not in `bin.includes`, so this web path does not serve them.

---

## 3. HTTP layout and URLs

Once the bundle is installed and started, `main/` is served as:

```text
/myappx-extension-repository/main/
├── index.json
├── extensions/<Bundle-SymbolicName>/...
└── bundles/*.jar
```

| URL | Purpose |
|-----|---------|
| `http://127.0.0.1:18080/myappx-extension-repository/main/index.json` | Catalog (Extension Manager) |
| `http://127.0.0.1:18080/myappx-extension-repository/main/extensions/<id>/...` | `info.md`, `CHANGELOG.md`, `metadata.json` |
| `http://127.0.0.1:18080/myappx-extension-repository/main/bundles/*.jar` | Extension JAR downloads |

JVM:

```text
-DIDEMPIERE_EXTENSION_REPOSITORY=http://127.0.0.1:18080/myappx-extension-repository
```

`index.json` and `metadata.json` store `__MYAPPX_CATALOG_BASE__` by default. This bundle's filter rewrites that placeholder to an absolute URL using the host of **that request**. Extension Management loads `main/index.json` through the JVM property above, so download URLs follow that host. Change the property when the host or port changes; do not republish. Use `publish.bat --base-url` only when the URLs must be pinned (for example, a static host that is not this bundle).

---

## 4. Source vs publish

| Path | Role |
|------|------|
| `extensions/` | Git source; **1:1** with `extensions.list` |
| `extensions.list` | Publish inventory + install order |
| `scripts/publish.py` | Validate, then build `main/` from Maven JARs |
| `main/` | Generated HTTP catalog, then packed into this bundle |

`index.json` order comes from `extensions.list` (not a hardcoded map). Before replacing `main/`, `publish.py` checks the 1:1 inventory, `metadata.id` against the directory name, `version` against the version folder name, and that each dependency appears earlier in the list. A failed check leaves the existing `main/` in place.

---

## 5. extensions.list

Format:

```text
<module-folder>|<Bundle-SymbolicName>
```

- Blank lines and lines starting with `#` are ignored.
- Order = publish order = suggested Extension Management install order (dependencies first).
- Module folder is relative to `myappx-plugins/` and is used to find `target/*.jar`.

Example:

```text
example-plugin|com.example.plugin
```

`publish.py` looks up JARs by exact file name (release, then `-SNAPSHOT`; it does not select `tests`, `sources`, or `javadoc`):

1. `<module>/<symbolicName>/target/<symbolicName>-<version>.jar` or `...-<version>-SNAPSHOT.jar`
2. The same file name under `<module>/target/`

Each extension keeps one current version folder, and that folder name must equal `version`. Publish fails when more than one version folder is present.

The live inventory is [`extensions.list`](extensions.list). Republish after you change it.

---

## 6. Publish workflow

Catalog plugin modules are listed before this module. `mvn clean verify` builds those JARs, then this module's `prepare-package` runs `publish.py` (missing JARs fail the build) and packs `main/` into the bundle. `myappx-plugins/build.bat` is that one command.

```bat
cd myappx-plugins
mvn -Drevision=14.0.0-SNAPSHOT clean verify
```

To refresh the catalog when the plugin JARs are already in each module `target/`:

```bat
cd myappx-extension-repository
publish.bat
cd ..
mvn -Drevision=14.0.0-SNAPSHOT -pl myappx-extension-repository package
```

That `package` publishes again. Add `-Dmyappx.skip.catalog.publish=true` when `publish.bat` has just written `main/`.

Put `myappx-extension-repository/target/org.idempiere.myappx.extension.repository-*.jar` into a new server instance `plugins/` directory, set `IDEMPIERE_EXTENSION_REPOSITORY`, then start the server.

Publish writes the complete tree under `main.staging/` and replaces `main/` only after that succeeds. SHA-256 is computed from the copied JAR.

---

## 7. Scripts and options

```bat
publish.bat                              write main/; a missing JAR or extra version folder fails and leaves main/ unchanged
publish.bat --base-url http://host:18080/myappx-extension-repository
python scripts\publish.py --check-inventory   check list, metadata, and dependency order
```

Equivalent Python:

```bat
python scripts\publish.py
python scripts\publish.py --check-inventory
```

| Option | Meaning |
|------|---------|
| `--base-url` | Write this absolute base into `index.json` / `downloadUrl` so the filter does not rewrite them. Unset uses the placeholder, or `MYAPPX_EXTENSION_REPOSITORY_URL` when that variable is set |
| `--check-inventory` | Check the 1:1 inventory, one version folder per extension, metadata fields, version folder names, and dependency order, then exit |

---

## 8. Add or remove an extension

**Add**

1. Create `extensions/<symbolic.name>/` with `info.md`, optional `CHANGELOG.md` and `assets/`, and `<version>/metadata.json`. `version` must equal the folder name.
2. Append a line to `extensions.list` (dependencies first) — source dir and list row must exist together (1:1).
3. Build the module JAR. The file name must be `<symbolicName>-<version>.jar` or `<symbolicName>-<version>-SNAPSHOT.jar`.
4. Run `publish.bat`, package this bundle, and replace the jar in `plugins/`.

**Remove**

1. Delete the line from `extensions.list`.
2. Delete `extensions/<id>/`.
3. Republish and repackage. The generated catalog no longer includes that extension.

Suggested `info.md` sections are in [extension-spec.md](extension-spec.md): Summary, Features, Compatibility, Database Changes, Usage & Configuration, Author/Support.

---

## 9. metadata.json

`downloadUrl` / `sha256` in **source** metadata are overwritten by `publish.py` in `main/`. Source files may keep a relative Maven artifact path for local reference.

Required fields: `id` (equals the directory name), `name`, `version` (equals the version folder name), `idempiereVersion`, `bundles` (at least one entry with `symbolicName`). Each `dependencies[].id` must appear earlier in `extensions.list`. Full constraints: [metadata-schema.json](metadata-schema.json).

`idempiereVersion` and `dependencies.version` follow [OSGi semantic version ranges](https://docs.osgi.org/whitepaper/semantic-versioning/040-semantic-versions.html).

---

## 10. Regenerate index only

When `main/extensions/` already exists:

```bat
python scripts/generate_index.py main
python scripts/generate_index.py --base-url http://host:18080/myappx-extension-repository main
```

`generate_index.py` filters and sorts by `extensions.list`. It fails if the catalog directories and the list diverge, or if `version` does not match the folder name. It does not copy JARs or recompute `sha256`.

---

## 11. Troubleshooting

| Symptom | What to do |
|---------|------------|
| Extension Management does not show an extension | Confirm it is in `extensions.list`, run `publish.bat`, package this bundle into the server `plugins/` directory, and confirm the bundle is started |
| Install fails / JAR cannot be downloaded | Rebuild that module, then republish. The JAR name must be `<symbolicName>-<version>.jar` or the `-SNAPSHOT` form |
| URL 404 | Confirm this bundle is installed and started, and `IDEMPIERE_EXTENSION_REPOSITORY` points at its Web-ContextPath |
| `index.json` order is wrong | Change order in `extensions.list` and republish |
| Publish reports a dependency order error | Move the dependency earlier in `extensions.list` |
| SHA check fails | Generated `sha256` must match the JAR copied this publish; republish and repackage after changing the JAR |
| Download host is wrong | Point `IDEMPIERE_EXTENSION_REPOSITORY` at the catalog clients can reach. Default JSON is rewritten for that request. Pin URLs with `publish.bat --base-url` |

---

## 12. Related docs

| Doc | Purpose |
|-----|---------|
| [extension-spec.md](extension-spec.md) | Catalog conventions, `info.md` and metadata examples |
| [metadata-schema.json](metadata-schema.json) | metadata JSON Schema |
| [extensions/extension.md](extensions/extension.md) | Source folder layout |
| [`extensions.list`](extensions.list) | Publish inventory and install order |
