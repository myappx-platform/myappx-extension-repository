"""Build main/index.json from a published extensions/ tree."""
from __future__ import annotations

import json
import os
import datetime
from pathlib import Path

from cataloglib import (
    load_metadata,
    parse_extensions_list,
    repo_root,
    resolve_base_url,
    version_key,
)


def catalog_url(base_url: str, relative_path: str) -> str:
    return f"{base_url.rstrip('/')}/{relative_path.lstrip('/')}"


def generate_index(
    extensions_dir: Path,
    base_url: str,
    output_file: Path,
    ordered_ids: list[str],
) -> None:
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    index_data = {
        "generatedAt": now_utc,
        "extensions": [],
    }

    if not extensions_dir.is_dir():
        raise SystemExit(f"Extensions directory not found: {extensions_dir}")

    base_url = base_url.rstrip("/")
    dir_ids = [p.name for p in extensions_dir.iterdir() if p.is_dir()]
    listed_set = set(ordered_ids)
    dir_set = set(dir_ids)
    missing = sorted(listed_set - dir_set)
    extra = sorted(dir_set - listed_set)
    if missing or extra:
        lines = ["Catalog extensions/ must match extensions.list (1:1)"]
        if missing:
            lines.append(f"  listed but missing: {', '.join(missing)}")
        if extra:
            lines.append(f"  present but not listed: {', '.join(extra)}")
        raise SystemExit("\n".join(lines))
    if len(ordered_ids) != len(listed_set):
        raise SystemExit("Duplicate ids in extensions.list")

    for extension_id in ordered_ids:
        extension_path = extensions_dir / extension_id
        versions = []
        for version_dir in extension_path.iterdir():
            metadata_file = version_dir / "metadata.json"
            if not version_dir.is_dir() or not metadata_file.is_file():
                continue
            meta = load_metadata(metadata_file)
            folder_name = version_dir.name
            version = meta.get("version")
            if version != folder_name:
                raise SystemExit(
                    f"{metadata_file}: version {version!r} != folder {folder_name}"
                )
            if meta.get("id") != extension_id:
                raise SystemExit(f"{metadata_file}: id {meta.get('id')!r} != directory {extension_id}")
            versions.append((folder_name, meta))

        if not versions:
            raise SystemExit(f"No metadata.json for {extension_id}")

        versions.sort(key=lambda item: version_key(item[0]), reverse=True)
        latest = versions[0][1]
        extension_entry = {
            "id": latest.get("id"),
            "name": latest.get("name"),
            "description": latest.get("description"),
            "categories": latest.get("categories", []),
            "tags": latest.get("tags", []),
            "entityType": latest.get("entityType"),
            "versions": [],
        }

        rel_ext = f"extensions/{extension_id}"
        for folder_name, _meta in versions:
            extension_entry["versions"].append(
                {
                    "version": folder_name,
                    "metadataUrl": catalog_url(base_url, f"main/{rel_ext}/{folder_name}/metadata.json"),
                }
            )

        if (extension_path / "info.md").is_file():
            extension_entry["infoUrl"] = catalog_url(base_url, f"main/{rel_ext}/info.md")
        if (extension_path / "CHANGELOG.md").is_file():
            extension_entry["changeLogUrl"] = catalog_url(base_url, f"main/{rel_ext}/CHANGELOG.md")

        assets_dir = extension_path / "assets"
        if assets_dir.is_dir():
            assets = []
            for asset_path in sorted(assets_dir.iterdir(), key=lambda path: path.name):
                if asset_path.is_file():
                    assets.append(
                        {
                            "name": asset_path.name,
                            "url": catalog_url(base_url, f"main/{rel_ext}/assets/{asset_path.name}"),
                        }
                    )
            if assets:
                extension_entry["assets"] = assets

        index_data["extensions"].append(extension_entry)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as handle:
        json.dump(index_data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"Successfully generated {output_file}")


def main() -> None:
    import argparse

    root = repo_root()
    parser = argparse.ArgumentParser(description="Regenerate main/index.json from main/extensions")
    parser.add_argument(
        "output_dir",
        nargs="?",
        default=str(root / "main"),
        help="Catalog directory that contains extensions/ (default: main)",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("MYAPPX_EXTENSION_REPOSITORY_URL") or None,
        help="Pin URLs to this base. Default is the request-host placeholder.",
    )
    args = parser.parse_args()

    list_path = root / "extensions.list"
    if not list_path.is_file():
        raise SystemExit(f"Missing {list_path}")
    ordered_ids = [extension_id for _module, extension_id in parse_extensions_list(list_path)]
    output_dir = Path(args.output_dir)
    generate_index(
        output_dir / "extensions",
        resolve_base_url(args.base_url),
        output_dir / "index.json",
        ordered_ids,
    )


if __name__ == "__main__":
    main()
