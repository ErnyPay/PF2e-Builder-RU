#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
ALLOWED_TYPES = {"ancestry", "background", "class", "feat", "spell", "equipment", "trait", "action", "condition", "rule"}


def validate_file(path: Path, global_ids: set[str]) -> list[str]:
    errors: list[str] = []
    try:
        root = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path}: invalid JSON: {exc}"]

    if root.get("schemaVersion") != 1:
        errors.append(f"{path}: schemaVersion must be 1")
    if not str(root.get("catalogId", "")).strip():
        errors.append(f"{path}: catalogId is required")

    provenance = root.get("provenance")
    if not isinstance(provenance, dict):
        errors.append(f"{path}: provenance object is required")
    else:
        for key in ("source", "license"):
            if not str(provenance.get(key, "")).strip():
                errors.append(f"{path}: provenance.{key} is required")

    entities = root.get("entities")
    if not isinstance(entities, list):
        errors.append(f"{path}: entities must be an array")
        return errors

    local_ids: set[str] = set()
    for index, entity in enumerate(entities):
        where = f"{path}:entities[{index}]"
        if not isinstance(entity, dict):
            errors.append(f"{where}: must be an object")
            continue
        entity_id = entity.get("id")
        if not isinstance(entity_id, str) or not ID_RE.fullmatch(entity_id):
            errors.append(f"{where}: invalid stable id {entity_id!r}")
        elif entity_id in local_ids or entity_id in global_ids:
            errors.append(f"{where}: duplicate id {entity_id}")
        else:
            local_ids.add(entity_id)
        if entity.get("type") not in ALLOWED_TYPES:
            errors.append(f"{where}: unsupported type {entity.get('type')!r}")
        name = entity.get("name")
        if not isinstance(name, dict) or not str(name.get("ru", "")).strip():
            errors.append(f"{where}: non-empty name.ru is required")
        level = entity.get("level")
        if level is not None and (not isinstance(level, int) or isinstance(level, bool) or not 0 <= level <= 30):
            errors.append(f"{where}: level must be an integer from 0 to 30")
        traits = entity.get("traits", [])
        if not isinstance(traits, list) or any(not isinstance(x, str) for x in traits) or len(traits) != len(set(traits)):
            errors.append(f"{where}: traits must be a unique string array")

    global_ids.update(local_ids)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path, default=Path("rules/catalog"))
    args = parser.parse_args()
    files = sorted(args.path.rglob("*.json")) if args.path.is_dir() else [args.path]
    if not files:
        print(f"no catalog JSON found under {args.path}")
        return 1
    ids: set[str] = set()
    errors: list[str] = []
    for path in files:
        errors.extend(validate_file(path, ids))
    if errors:
        print("\n".join(errors))
        return 1
    print(f"rules catalogs: OK ({len(files)} files, {len(ids)} entities)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
