"""Shared helpers for the MyAppx extension catalog publish scripts."""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

# Replaced at request time by CatalogBaseUrlFilter. Keep in sync with that class.
CATALOG_BASE_PLACEHOLDER = "__MYAPPX_CATALOG_BASE__"

VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(\.[A-Za-z0-9_-]+)?$")
REQUIRED_FIELDS = ("id", "name", "version", "idempiereVersion", "bundles")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def plugins_root() -> Path:
    """Directory that contains sibling plugin modules (myappx-plugins).

    This bundle sits one level under the git root:
    myappx-plugins/myappx-extension-repository/<this-bundle>/scripts
    """
    return repo_root().parent.parent


def version_key(version_str: str) -> tuple:
    """OSGi-like order: 1.0.0.beta < 1.0.0 < 1.0.1. Missing numeric parts sort first."""
    raw = version_str.split(".")
    numbers: list[int] = []
    for part in raw[:3]:
        numbers.append(int(part) if part.isdigit() else -1)
    while len(numbers) < 3:
        numbers.append(-1)
    qualifier = ".".join(raw[3:])
    if qualifier:
        return (numbers[0], numbers[1], numbers[2], 0, qualifier)
    return (numbers[0], numbers[1], numbers[2], 1, "")


def parse_extensions_list(list_path: Path) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for line in list_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2 or not parts[0] or not parts[1]:
            raise SystemExit(f"Invalid extensions.list line: {line}")
        entries.append((parts[0], parts[1]))
    return entries


def assert_extensions_inventory_1to1(root: Path, entries: list[tuple[str, str]]) -> None:
    """Fail unless extensions/ directories match extensions.list ids exactly (1:1)."""
    extensions_dir = root / "extensions"
    if not extensions_dir.is_dir():
        raise SystemExit(f"Missing source directory: {extensions_dir}")

    listed_ids = [eid for _, eid in entries]
    listed_set = set(listed_ids)
    if len(listed_ids) != len(listed_set):
        dupes = sorted({eid for eid in listed_ids if listed_ids.count(eid) > 1})
        raise SystemExit(f"Duplicate Bundle-SymbolicName in extensions.list: {', '.join(dupes)}")

    dir_ids = sorted(p.name for p in extensions_dir.iterdir() if p.is_dir())
    dir_set = set(dir_ids)

    missing = sorted(listed_set - dir_set)
    extra = sorted(dir_set - listed_set)
    if missing or extra:
        lines = ["extensions/ must be 1:1 with extensions.list"]
        if missing:
            lines.append(f"  listed but missing under extensions/: {', '.join(missing)}")
        if extra:
            lines.append(f"  under extensions/ but not in extensions.list (remove or add a list row): {', '.join(extra)}")
        raise SystemExit("\n".join(lines))


def version_dirs(ext_dir: Path) -> list[str]:
    versions: list[str] = []
    if not ext_dir.is_dir():
        return versions
    for child in ext_dir.iterdir():
        if child.is_dir() and (child / "metadata.json").is_file():
            versions.append(child.name)
    versions.sort(key=version_key)
    return versions


def current_version(ext_dir: Path, extension_id: str) -> str:
    """Each extension has one current version. Older version folders are not published."""
    versions = version_dirs(ext_dir)
    if not versions:
        raise SystemExit(f"No version folder with metadata.json for {extension_id}")
    if len(versions) > 1:
        raise SystemExit(
            f"{extension_id} has multiple version folders ({', '.join(versions)}). "
            "Keep only the current version."
        )
    return versions[0]


def load_metadata(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must be a JSON object")
    return data


def validate_metadata(extension_id: str, folder_name: str, metadata: dict, earlier_ids: set[str]) -> None:
    """Fail when metadata does not match the schema rules publish relies on."""
    where = f"{extension_id}/{folder_name}"
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        value = metadata.get(field)
        if value is None or value == "" or value == []:
            errors.append(f"missing {field}")

    if metadata.get("id") not in (None, "") and metadata.get("id") != extension_id:
        errors.append(f"id {metadata.get('id')!r} != directory {extension_id}")

    version = metadata.get("version")
    if isinstance(version, str):
        if not VERSION_PATTERN.match(version):
            errors.append(f"version {version!r} does not match {VERSION_PATTERN.pattern}")
        elif version != folder_name:
            errors.append(f"version {version} != folder {folder_name}")

    bundles = metadata.get("bundles")
    seen_names: set[str] = set()
    if isinstance(bundles, list):
        if len(bundles) < 1:
            errors.append("bundles must contain at least one item")
        for index, bundle in enumerate(bundles):
            if not isinstance(bundle, dict) or not str(bundle.get("symbolicName") or "").strip():
                errors.append(f"bundles[{index}].symbolicName is required")
                continue
            name = str(bundle["symbolicName"]).strip()
            if any(token in name for token in ("/", "\\", "..")):
                errors.append(f"bundles[{index}].symbolicName must be a single bundle name")
            elif name in seen_names:
                errors.append(f"duplicate bundle symbolicName {name}")
            else:
                seen_names.add(name)

    dependencies = metadata.get("dependencies", [])
    if dependencies is None:
        dependencies = []
    if not isinstance(dependencies, list):
        errors.append("dependencies must be an array")
    else:
        for index, dep in enumerate(dependencies):
            if not isinstance(dep, dict):
                errors.append(f"dependencies[{index}] must be an object")
                continue
            dep_id = str(dep.get("id") or "").strip()
            dep_version = dep.get("version")
            if not dep_id:
                errors.append(f"dependencies[{index}].id is required")
            elif dep_id == extension_id:
                errors.append(f"dependency on itself: {dep_id}")
            elif dep_id not in earlier_ids:
                errors.append(f"dependency {dep_id} must appear earlier in extensions.list")
            if not isinstance(dep_version, str) or not dep_version.strip():
                errors.append(f"dependencies[{index}].version is required")

    database = metadata.get("database")
    if database is not None:
        if not isinstance(database, list):
            errors.append("database must be an array")
        else:
            for index, item in enumerate(database):
                if not isinstance(item, dict) or not str(item.get("id") or "").strip():
                    errors.append(f"database[{index}].id is required")

    version_file = metadata.get("versionFile")
    has_version_file = isinstance(version_file, str) and bool(version_file.strip())
    if version_file is not None and not has_version_file:
        errors.append("versionFile must be a module-relative path")
    elif has_version_file:
        try:
            version_file_path(version_file.strip())
        except SystemExit as exc:
            errors.append(str(exc))

    artifact_version = metadata.get("artifactVersion")
    has_artifact_version = isinstance(artifact_version, str) and bool(artifact_version.strip())
    if artifact_version is not None and not has_artifact_version:
        errors.append("artifactVersion must be a version string")
    elif has_artifact_version and not VERSION_PATTERN.match(artifact_version.strip()):
        errors.append(f"artifactVersion {artifact_version!r} does not match {VERSION_PATTERN.pattern}")
    if has_version_file and not has_artifact_version:
        errors.append("artifactVersion is required when versionFile is set")

    if errors:
        raise SystemExit(where + ": " + "; ".join(errors))


def candidate_jar_names(symbolic_name: str, version: str) -> list[str]:
    return [
        f"{symbolic_name}-{version}.jar",
        f"{symbolic_name}-{version}-SNAPSHOT.jar",
    ]


def find_plugin_jar(module_folder: str, extension_id: str, symbolic_name: str, version: str) -> Path | None:
    """Return the Maven jar for this exact version. Release wins over SNAPSHOT."""
    module_path = plugins_root() / module_folder
    target_dirs = [
        module_path / symbolic_name / "target",
        module_path / extension_id / "target",
        module_path / "target",
    ]
    names = candidate_jar_names(symbolic_name, version)
    seen: set[Path] = set()
    for target_dir in target_dirs:
        if not target_dir.is_dir():
            continue
        resolved = target_dir.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        for name in names:
            jar = target_dir / name
            if jar.is_file():
                return jar
    return None


def uses_external_version(metadata: dict) -> bool:
    """True when the catalog version is not the Maven artifact version."""
    version_file = metadata.get("versionFile")
    artifact_version = metadata.get("artifactVersion")
    return (isinstance(version_file, str) and bool(version_file.strip())) or (
        isinstance(artifact_version, str) and bool(artifact_version.strip())
    )


def maven_artifact_version(metadata: dict, catalog_version: str) -> str:
    """Jar file version. Defaults to the catalog version."""
    artifact_version = metadata.get("artifactVersion")
    if isinstance(artifact_version, str) and artifact_version.strip():
        return artifact_version.strip()
    return catalog_version


def version_file_path(relative: str) -> Path:
    """Return a module-relative path. The caller joins it to the module directory."""
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise SystemExit(f"versionFile must stay inside the module: {relative}")
    return rel


def read_declared_version(module_folder: str, extension_id: str, relative: str) -> str:
    """First line of the module file named by metadata versionFile."""
    path = (plugins_root() / module_folder / version_file_path(relative)).resolve()
    module = (plugins_root() / module_folder).resolve()
    if path != module and module not in path.parents:
        raise SystemExit(f"{extension_id}: versionFile escapes the module: {relative}")
    if not path.is_file():
        raise SystemExit(f"{extension_id}: version file not found: {path}")
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise SystemExit(f"{extension_id}: version file is empty: {path}")
    latest = lines[0]
    if not VERSION_PATTERN.match(latest):
        raise SystemExit(f"{extension_id}: {path.name} has invalid version {latest!r}")
    return latest


def release_day_from_module(module_folder: str) -> str | None:
    """YYYY-MM-DD from the module latest.yml releaseDate, when that feed exists."""
    path = plugins_root() / module_folder / "latest.yml"
    if not path.is_file():
        return None
    match = re.search(r"^releaseDate:\s*'?(\d{4}-\d{2}-\d{2})", path.read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1) if match else None


def bundle_version_from_jar(jar_path: Path) -> str:
    """OSGi Bundle-Version from the jar manifest, including folded header lines."""
    with zipfile.ZipFile(jar_path) as archive:
        try:
            raw = archive.read("META-INF/MANIFEST.MF")
        except KeyError as exc:
            raise SystemExit(f"{jar_path.name} has no META-INF/MANIFEST.MF") from exc
    logical: list[str] = []
    for line in raw.decode("utf-8", errors="replace").splitlines():
        if line.strip() == "" and logical:
            break
        if line.startswith((" ", "\t")) and logical:
            logical[-1] += line[1:]
        else:
            logical.append(line)
    for line in logical:
        if line.startswith("Bundle-Version:"):
            version = line.split(":", 1)[1].strip()
            if version:
                return version
    raise SystemExit(f"{jar_path.name} manifest has no Bundle-Version")


def resolve_base_url(explicit: str | None) -> str:
    if explicit and explicit.strip():
        return explicit.strip().rstrip("/")
    return CATALOG_BASE_PLACEHOLDER
