#!/usr/bin/env python3
"""
Publish the MyAppx extension catalog into this bundle's main/ directory.

Output: main/  (index.json, extensions/, bundles/)
The bundle serves that tree at /myappx-extension-repository/main/.

downloadUrl values use __MYAPPX_CATALOG_BASE__ unless --base-url or
MYAPPX_EXTENSION_REPOSITORY_URL is set. The web bundle rewrites the placeholder
to the host that requested the catalog.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from pathlib import Path

from cataloglib import (
    CATALOG_BASE_PLACEHOLDER,
    assert_extensions_inventory_1to1,
    current_version,
    find_plugin_jar,
    load_metadata,
    parse_extensions_list,
    repo_root,
    resolve_base_url,
    validate_metadata,
)
from generate_index import generate_index


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bundle_file_name(symbolic_name: str, version: str) -> str:
    return f"{symbolic_name}_{version}.jar"


def catalog_url(base_url: str, relative_path: str) -> str:
    return f"{base_url.rstrip('/')}/{relative_path.lstrip('/')}"


RENAME_ATTEMPTS = 20
RENAME_INITIAL_DELAY = 0.05


def rename_with_retry(src: Path, dst: Path, attempts: int = RENAME_ATTEMPTS) -> None:
    """Rename a directory, retrying when a watcher holds a handle inside it.

    On Windows a rename fails with WinError 5 (access denied) while any file
    under src is still open -- an editor, the search indexer, an antivirus or a
    file watcher that opened the tree the build just wrote. Those locks last
    milliseconds, so a short backoff turns a flaky build into a reliable one.
    WinError 183 (destination exists) is a real state error and is not retried.
    """
    delay = RENAME_INITIAL_DELAY
    for attempt in range(1, attempts + 1):
        try:
            src.rename(dst)
            return
        except PermissionError:
            if attempt == attempts:
                raise
            time.sleep(delay)
            delay = min(delay * 2, 1.0)


def rmtree_with_retry(path: Path, attempts: int = RENAME_ATTEMPTS) -> None:
    """Remove a tree, retrying while open handles inside it block the delete."""
    delay = RENAME_INITIAL_DELAY
    for attempt in range(1, attempts + 1):
        try:
            shutil.rmtree(path)
            return
        except FileNotFoundError:
            return
        except OSError:
            if attempt == attempts:
                raise
            time.sleep(delay)
            delay = min(delay * 2, 1.0)


def recover_failed_replace(dest: Path) -> None:
    backup = dest.with_name(dest.name + ".replaced")
    if not dest.exists() and backup.exists():
        rename_with_retry(backup, dest)


def replace_directory(staging: Path, dest: Path) -> None:
    """Swap staging into dest only after the new tree is complete.

    Every step retries: the previous tree and the new one are both large enough
    that an outside handle can hold either for a moment. Only the swap itself is
    allowed to fail the build; once dest is in place, leftover cleanup must not.
    """
    backup = dest.with_name(dest.name + ".replaced")
    if backup.exists():
        rmtree_with_retry(backup)
    moved = False
    if dest.exists():
        rename_with_retry(dest, backup)
        moved = True
    try:
        rename_with_retry(staging, dest)
    except Exception:
        if moved and backup.exists() and not dest.exists():
            rename_with_retry(backup, dest)
        raise
    if backup.exists():
        try:
            rmtree_with_retry(backup)
        except OSError as exc:
            print(f"[WARN] {backup.name} could not be removed ({exc}); delete it later.")


def check_inventory(root: Path) -> list[tuple[str, str]]:
    list_path = root / "extensions.list"
    if not list_path.is_file():
        raise SystemExit(f"Missing {list_path}")
    entries = parse_extensions_list(list_path)
    assert_extensions_inventory_1to1(root, entries)
    for index, (_module_folder, extension_id) in enumerate(entries):
        earlier = {eid for _, eid in entries[:index]}
        src_ext = root / "extensions" / extension_id
        version = current_version(src_ext, extension_id)
        metadata = load_metadata(src_ext / version / "metadata.json")
        validate_metadata(extension_id, version, metadata, earlier)
    return entries


def publish(base_url: str) -> None:
    root = repo_root()
    list_path = root / "extensions.list"
    if not list_path.is_file():
        raise SystemExit(f"Missing {list_path}")
    entries = check_inventory(root)
    recover_failed_replace(root / "main")

    planned: list[dict] = []
    missing_jars: list[str] = []
    for index, (module_folder, extension_id) in enumerate(entries):
        earlier = {eid for _, eid in entries[:index]}
        src_ext = root / "extensions" / extension_id
        version = current_version(src_ext, extension_id)
        metadata = load_metadata(src_ext / version / "metadata.json")
        validate_metadata(extension_id, version, metadata, earlier)
        jars: dict[str, Path] = {}
        for bundle in metadata["bundles"]:
            symbolic_name = str(bundle["symbolicName"]).strip()
            jar_src = find_plugin_jar(module_folder, extension_id, symbolic_name, version)
            if jar_src is None:
                missing_jars.append(
                    f"{extension_id} {version} ({symbolic_name}): expected "
                    f"{symbolic_name}-{version}.jar or {symbolic_name}-{version}-SNAPSHOT.jar "
                    f"under {module_folder}/target or {module_folder}/{symbolic_name}/target"
                )
            else:
                jars[symbolic_name] = jar_src
        planned.append(
            {
                "extension_id": extension_id,
                "src_ext": src_ext,
                "version": version,
                "metadata": metadata,
                "jars": jars,
            }
        )

    if missing_jars:
        raise SystemExit("Missing built jars:\n  " + "\n  ".join(missing_jars))

    staging = root / "main.staging"
    if staging.exists():
        try:
            rmtree_with_retry(staging)
        except OSError as exc:
            raise SystemExit(
                f"Cannot remove the leftover {staging} ({exc}). A process is holding a file inside it. "
                "Close it (editor, server, antivirus scan) and run the build again."
            ) from exc
    bundles_dir = staging / "bundles"
    extensions_out = staging / "extensions"
    bundles_dir.mkdir(parents=True)
    extensions_out.mkdir(parents=True)

    try:
        for item in planned:
            extension_id = item["extension_id"]
            src_ext: Path = item["src_ext"]
            dst_ext = extensions_out / extension_id
            dst_ext.mkdir(parents=True, exist_ok=True)
            for doc in ("info.md", "CHANGELOG.md"):
                src_doc = src_ext / doc
                if src_doc.is_file():
                    shutil.copy2(src_doc, dst_ext / doc)
            assets = src_ext / "assets"
            if assets.is_dir():
                shutil.copytree(assets, dst_ext / "assets")

            version = item["version"]
            metadata = json.loads(json.dumps(item["metadata"]))
            dst_version = dst_ext / version
            dst_version.mkdir(parents=True, exist_ok=True)
            for bundle in metadata["bundles"]:
                symbolic_name = str(bundle["symbolicName"]).strip()
                bundle_name = bundle_file_name(symbolic_name, version)
                bundle["downloadUrl"] = catalog_url(base_url, f"main/bundles/{bundle_name}")
                jar_src = item["jars"][symbolic_name]
                dst_jar = bundles_dir / bundle_name
                shutil.copy2(jar_src, dst_jar)
                bundle["sha256"] = sha256_file(dst_jar)
                print(f"[OK] Bundle {bundle_name} <= {jar_src.name}")
            (dst_version / "metadata.json").write_text(
                json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            print(f"[OK] Extension {extension_id} {version}")

        ordered_ids = [extension_id for _module, extension_id in entries]
        generate_index(extensions_out, base_url, staging / "index.json", ordered_ids)
        replace_directory(staging, root / "main")
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise

    print(f"[OK] Catalog written to {root / 'main'}")
    if base_url == CATALOG_BASE_PLACEHOLDER:
        print("     URLs use the request host when this bundle serves the catalog.")
    else:
        print(f"     URLs pinned to {base_url}")
    print("     Package this bundle, then copy the jar into the server plugins/ directory.")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Publish MyAppx extension catalog to main/")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("MYAPPX_EXTENSION_REPOSITORY_URL") or None,
        help="Pin catalog URLs to this absolute base. Default: placeholder rewritten per request, "
        "or MYAPPX_EXTENSION_REPOSITORY_URL when that environment variable is set.",
    )
    parser.add_argument(
        "--check-inventory",
        action="store_true",
        help="Validate extensions/ against extensions.list, metadata, and dependency order, then exit",
    )
    args = parser.parse_args()
    if args.check_inventory:
        entries = check_inventory(repo_root())
        print(f"[OK] extensions/ matches extensions.list ({len(entries)} extensions, metadata checked)")
        return
    publish(resolve_base_url(args.base_url))


if __name__ == "__main__":
    main()
