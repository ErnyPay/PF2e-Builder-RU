#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

MASTER_PLAINTEXT_SHA256 = "86389697253f2046a09ac266ca1a78ac6f3fc2653c8ccb6fb8a5c9284e28efc9"
REMASTER_PLAINTEXT_SHA256 = "bebaf99cfe5a6503681b2876a8c963af9dcb779c4232312ebeb8c75438eaf16e"
EXPECTED_MASTER_CHANGES = 37
EXPECTED_REMASTER_CHANGES = 8

MASTER_CLASS_TEXT = {
    "Lightning Reflexes": "Ваши рефлексы молниеносны. Ваше мастерство спасбросков Рефлекса улучшается до эксперта.",
    "Resolve": "Вы закалили свой разум решимостью. Ваше мастерство спасбросков Воли улучшается до мастера. Когда при спасброске Воли вы получаете успех, результат считается критическим успехом.",
    "Great Fortitude": "Ваше тело невероятно выносливо. Ваше мастерство спасбросков Стойкости улучшается до эксперта.",
    "Vigilant Senses": "Благодаря вашим приключениям вы развили острую наблюдательность и внимание к деталям. Ваше мастерство Восприятия улучшается до мастера.",
    "Weapon Mastery": "Вы полностью понимаете своё оружие. Ваше мастерство безоружных атак, а также обращения с простым и воинским оружием, улучшается до мастера.",
    "Incredible Senses": "Вы подмечаете детали, которые невозможно заметить простому обывателю. Ваше мастерство Восприятия улучшается до легенды.",
}

REMASTER_CLASS_TEXT = {
    ("specials_class_rogue", "Perception Legend"): "Вы замечаете то, что почти незаметно. Ваше мастерство Восприятия улучшается до легенды.",
    ("specials_class_witch", "Reflex Expertise"): "Вы научились уклоняться от опасности. Ваше мастерство спасбросков Рефлекса улучшается до эксперта.",
    ("specials_class_sorcerer", "Reflex Expertise"): "Вы научились уклоняться от опасности. Ваше мастерство спасбросков Рефлекса улучшается до эксперта.",
    ("specials_class_barbarian", "Weapon Mastery"): "Ваша ярость делает вас ещё более эффективным с оружием, которым вы владеете. Ваше мастерство безоружных атак, а также обращения с простым и воинским оружием, улучшается до мастера.",
    ("specials_class_swashbuckler", "Weapon Mastery"): "Вы полностью понимаете своё оружие. Ваше мастерство безоружных атак, а также обращения с простым и воинским оружием, улучшается до мастера.",
    ("specials_class_barbarian", "Perception Mastery"): "Ваш инстинкт усиливает каждое из ваших чувств. Ваше мастерство Восприятия улучшается до мастера.",
    ("specials_class_swashbuckler", "Perception Mastery"): "Во время странствий вы привыкли подмечать малейшие детали. Ваше мастерство Восприятия улучшается до мастера.",
    ("specials_class_barbarian", "Armor Mastery"): "Ваши тренировки и ярость углубили связь с доспехом. Ваше мастерство ношения лёгких и средних доспехов, а также защиты без доспехов, улучшается до мастера.",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def integrity(path: Path) -> dict:
    db = sqlite3.connect(path)
    try:
        return {
            "integrity_check": db.execute("pragma integrity_check").fetchone()[0],
            "foreign_key_violations": len(db.execute("pragma foreign_key_check").fetchall()),
        }
    finally:
        db.close()


def apply(master_in: Path, remaster_in: Path, master_out: Path, remaster_out: Path) -> dict:
    if sha256(master_in) != MASTER_PLAINTEXT_SHA256:
        raise RuntimeError("master plaintext baseline hash changed; refusing content patch")
    if sha256(remaster_in) != REMASTER_PLAINTEXT_SHA256:
        raise RuntimeError("remaster plaintext baseline hash changed; refusing content patch")

    shutil.copy2(master_in, master_out)
    shutil.copy2(remaster_in, remaster_out)
    changes = []

    master = sqlite3.connect(master_out)
    remaster_source = sqlite3.connect(remaster_in)
    try:
        tables = [r[0] for r in master.execute(
            "select name from sqlite_master where type='table' and name like 'specials_class_%'"
        )]
        for table in tables:
            columns = [r[1] for r in master.execute(f'pragma table_info("{table}")')]
            if "name" not in columns or "text_descrip" not in columns:
                continue
            for name, new_text in MASTER_CLASS_TEXT.items():
                rows = master.execute(
                    f'select rowid,text_descrip from "{table}" where name=? and text_descrip like "*%"',
                    (name,),
                ).fetchall()
                for rowid, old_text in rows:
                    cur = master.execute(
                        f'update "{table}" set text_descrip=? where rowid=? and text_descrip=?',
                        (new_text, rowid, old_text),
                    )
                    if cur.rowcount != 1:
                        raise RuntimeError(f"guard failed: master/{table}/{rowid}/{name}")
                    changes.append(("master.db", table, rowid, name, "text_descrip"))

        # These legacy entries are incomplete EN/RU translations. The remaster
        # DB has the exact same entity name + AoN URL with a complete Russian
        # description, so it is used as a translation donor only.
        for table, pattern in (
            ("items_property_runes_armor", "Energy Resistant%"),
            ("items_all", "Magentic Suit%"),
        ):
            donor = {
                (name, url): description
                for name, url, description in remaster_source.execute(
                    f'select name,url,description from "{table}" where name like ?',
                    (pattern,),
                )
            }
            rows = master.execute(
                f'select rowid,name,url,description from "{table}" where name like ?',
                (pattern,),
            ).fetchall()
            for rowid, name, url, old_text in rows:
                new_text = donor.get((name, url))
                if new_text is None or new_text == old_text:
                    raise RuntimeError(f"safe donor missing: {table}/{name}/{url}")
                cur = master.execute(
                    f'update "{table}" set description=? where rowid=? and description=?',
                    (new_text, rowid, old_text),
                )
                if cur.rowcount != 1:
                    raise RuntimeError(f"guard failed: master/{table}/{rowid}/{name}")
                changes.append(("master.db", table, rowid, name, "description"))
        master.commit()
    finally:
        master.close()
        remaster_source.close()

    remaster = sqlite3.connect(remaster_out)
    try:
        for (table, name), new_text in REMASTER_CLASS_TEXT.items():
            rows = remaster.execute(
                f'select rowid,text_descrip from "{table}" where name=?', (name,)
            ).fetchall()
            if len(rows) != 1:
                raise RuntimeError(f"target cardinality changed: remaster/{table}/{name}")
            rowid, old_text = rows[0]
            if not old_text.lstrip().startswith("*"):
                raise RuntimeError(f"target no longer looks misbound: remaster/{table}/{name}")
            cur = remaster.execute(
                f'update "{table}" set text_descrip=? where rowid=? and text_descrip=?',
                (new_text, rowid, old_text),
            )
            if cur.rowcount != 1:
                raise RuntimeError(f"guard failed: remaster/{table}/{rowid}/{name}")
            changes.append(("remaster.db", table, rowid, name, "text_descrip"))
        remaster.commit()
    finally:
        remaster.close()

    master_count = sum(1 for row in changes if row[0] == "master.db")
    remaster_count = sum(1 for row in changes if row[0] == "remaster.db")
    if master_count != EXPECTED_MASTER_CHANGES or remaster_count != EXPECTED_REMASTER_CHANGES:
        raise RuntimeError(
            f"unexpected patch count: master={master_count}, remaster={remaster_count}"
        )

    master_check = integrity(master_out)
    remaster_check = integrity(remaster_out)
    for label, check in (("master", master_check), ("remaster", remaster_check)):
        if check["integrity_check"] != "ok" or check["foreign_key_violations"]:
            raise RuntimeError(f"{label} integrity failed: {check}")

    return {
        "total_changed_cells": len(changes),
        "master_changed_cells": master_count,
        "remaster_changed_cells": remaster_count,
        "master_integrity": master_check,
        "remaster_integrity": remaster_check,
        "changes": [
            {"db": db, "table": table, "rowid": rowid, "name": name, "column": column}
            for db, table, rowid, name, column in changes
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply RuneSheet 1.0.1-beta1 guarded content fixes")
    parser.add_argument("master", type=Path, help="decrypted baseline master sqlite")
    parser.add_argument("remaster", type=Path, help="decrypted baseline remaster sqlite")
    parser.add_argument("master_out", type=Path)
    parser.add_argument("remaster_out", type=Path)
    args = parser.parse_args()
    result = apply(args.master, args.remaster, args.master_out, args.remaster_out)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
