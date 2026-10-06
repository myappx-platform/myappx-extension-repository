# MyAppx ObjectData Tool (ODT)

**Summary:** OSGi extension for iDempiere that manages Application Dictionary metadata as structured ObjectData packages — export, version, import, install, and bootstrap plugin dictionaries via `META-INF/ODTPackage.xml`.

## Features

* **ODT packages:** Serialize AD objects (windows, tables, fields, menus, indexes, etc.) to XML with UUID-based identity.
* **Version control:** Package + Version records in `KS_ODTPackage` / `KS_ODTVersion` with install and refresh processes.
* **Bootstrap install:** First-time bundle activation can install ODT dictionary and physical tables from bundled XML.
* **2Pack integration:** Optional `ODT2PackActivator` pipeline for ODT + `2Pack_*.zip` + `ODT2Pack-*.zip` Pack-in.

## Compatibility

* **iDempiere Version:** 14.0
* **Java Version:** 17+
* **Database:** PostgreSQL

## Database Changes

* **ODT runtime tables:** `KS_ODTPackage`, `KS_ODTVersion`, `KS_ODTObjectData`, `KS_ODTObjectDataLine` (installed via ODT bootstrap or Pack-in).
* **System PackIn:** Bundled `META-INF/ODTPackage.xml` applies AD dictionary on bundle start when version increases.

## Usage & Configuration

1. Build: `mvn -f myappx-plugin-odt/pom.xml "-Drevision=14.0.0-SNAPSHOT" clean verify`
2. Install the bundle (Extension Management or OSGi console).
3. On start, `Activator` installs `META-INF/ODTPackage.xml` when the bundled version is newer than the database.

Other MyAppx extensions (ZZZ, Source Browser, tenant-default) depend on this plugin.

## Author / Support

* **Developer:** Ken Longnan
* **Source Code:** `myappx-plugins/myappx-plugin-odt`
* **Documentation:** `myappx-plugin-odt/README.md`
