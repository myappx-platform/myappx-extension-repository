# MyAppx Desktop Portal

**Summary:** OSGi web bundle that serves the MyAppx Desktop download page and the electron-updater feed at `/desktop/`.

## Features

* **Download page:** `/desktop/` links to the current Windows setup and the install / upgrade / help pages.
* **Updater feed:** `latest.yml` and the NSIS installer sit next to each other, so an installed desktop client can update from this server.
* **Feed refresh:** `myappx-desktop-portal/publish.py` replaces `latest.yml`, `latest.txt`, the installer, and the version shown on `index.html` from `myappx-desktop/release`.

## Compatibility

* **iDempiere:** 14.0 · **Java:** 17+
* **Catalog version:** the desktop client version in `latest.txt` (for example `6.2.2`), not the Maven `14.0.0` artifact version
* **Requires:** nothing else in this catalog

## Database Changes

* None.

## Usage & Configuration

1. Install from Extension Management after this catalog bundle is running. The portal has no dictionary pack-in.
2. Open `http://<host>:<port>/desktop/`.
3. A new desktop release updates this entry only after both bundles are rebuilt: the portal `prepare-package` refreshes the feed, then the catalog publish copies the new jar and moves this extension's version folder to the new `latest.txt` value.
4. On a server that already has the portal installed, run **Update** in Extension Management. The catalog `version` must be greater than the installed one, and `bundles[].version` is the portal jar's `Bundle-Version`.

## Author / Support

* **Developer:** Ken Longnan
* **Source / Bundle:** `myappx-plugins/myappx-desktop-portal` · `org.idempiere.myappx.desktop.portal`
