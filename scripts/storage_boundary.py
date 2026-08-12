from __future__ import annotations

import argparse
import json
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "storage_boundary.json"


def _uleb(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if byte < 0x80:
            return value, offset
        shift += 7


def _dex_strings(data: bytes) -> list[str]:
    u32 = lambda off: struct.unpack_from("<I", data, off)[0]
    size = u32(0x38)
    table = u32(0x3C)
    result: list[str] = []
    for index in range(size):
        item = u32(table + 4 * index)
        _, payload = _uleb(data, item)
        end = data.index(0, payload)
        result.append(data[payload:end].decode("utf-8", "replace"))
    return result


def _dex_methods(data: bytes) -> set[tuple[str, str]]:
    u32 = lambda off: struct.unpack_from("<I", data, off)[0]
    strings = _dex_strings(data)

    type_size = u32(0x40)
    type_off = u32(0x44)
    type_ids = [u32(type_off + 4 * index) for index in range(type_size)]

    method_size = u32(0x58)
    method_off = u32(0x5C)
    methods: set[tuple[str, str]] = set()
    for index in range(method_size):
        class_idx, _, name_idx = struct.unpack_from("<HHI", data, method_off + 8 * index)
        methods.add((strings[type_ids[class_idx]], strings[name_idx]))
    return methods


def _pairs(section: dict[str, list[str]]) -> set[tuple[str, str]]:
    return {(class_name, method) for class_name, methods in section.items() for method in methods}


def load_storage_boundary(path: Path = DEFAULT_CONFIG) -> dict:
    config = json.loads(path.read_text(encoding="utf8"))
    if config.get("cloud_storage_enabled") is not False:
        raise RuntimeError("RuneSheet transition storage boundary requires cloud_storage_enabled=false")
    contract = str(config.get("owned_contract", ""))
    if not contract.startswith("com.runesheet.storage."):
        raise RuntimeError(f"owned storage contract is not RuneSheet-owned: {contract!r}")
    order = config.get("migration_order")
    if order != ["save", "load", "folders", "state"]:
        raise RuntimeError(f"unexpected local-storage migration order: {order!r}")
    return config


def verify_storage_boundary(dex: bytes, config_path: Path = DEFAULT_CONFIG) -> dict:
    """Verify the pinned 2.56 local-storage seam before patching the transition APK.

    This does not modify DEX. It turns the remaining inherited local persistence
    implementation into an explicit compatibility boundary so each slice can be
    replaced by RuneSheet code independently. Cloud methods are deliberately
    listed in a separate isolated section and must never enter the local adapter.
    """
    config = load_storage_boundary(config_path)
    methods = _dex_methods(dex)

    legacy = config["legacy_transition"]
    local_pairs: set[tuple[str, str]] = set()
    for name in ("save", "load", "folders", "state"):
        local_pairs |= _pairs(legacy[name])
    cloud_pairs = _pairs(config["isolated_cloud_runtime"])

    overlap = local_pairs & cloud_pairs
    if overlap:
        raise RuntimeError(f"cloud/local storage boundary overlap: {sorted(overlap)!r}")

    cloud_classes = {class_name for class_name, _ in cloud_pairs}
    leaked_cloud_classes = sorted({class_name for class_name, _ in local_pairs if "CloudStorageHelper" in class_name})
    if leaked_cloud_classes:
        raise RuntimeError(f"cloud helper leaked into local adapter: {leaked_cloud_classes!r}")

    missing_local = sorted(local_pairs - methods)
    missing_cloud = sorted(cloud_pairs - methods)
    if missing_local:
        raise RuntimeError(f"legacy local-storage seam changed: missing {missing_local!r}")
    if missing_cloud:
        raise RuntimeError(f"isolated cloud seam changed: missing {missing_cloud!r}")

    return {
        "ok": True,
        "owned_contract": config["owned_contract"],
        "cloud_storage_enabled": False,
        "migration_order": config["migration_order"],
        "legacy_local_methods": len(local_pairs),
        "isolated_cloud_methods": len(cloud_pairs),
        "isolated_cloud_classes": sorted(cloud_classes),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify RuneSheet transition local-storage boundary")
    parser.add_argument("apk", type=Path)
    parser.add_argument("--dex", default="classes2.dex")
    args = parser.parse_args()
    with zipfile.ZipFile(args.apk) as archive:
        result = verify_storage_boundary(archive.read(args.dex))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
