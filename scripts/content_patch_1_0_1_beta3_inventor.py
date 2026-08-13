#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sqlite3
from pathlib import Path

# Fingerprint of the Inventor class-introduction text that was accidentally
# pasted into modification descriptions in the beta2 audit.
MISBOUND_SHA256 = "04aafe1c8eee9fffe5b41de8c66eaa2058595578969ac0c3015ea1ee39f8b3a5"

# Translation policy:
# - Legacy mechanics/wording were checked against the Russian Inventor reference
#   (Guns & Gears translation).
# - Remaster mechanics/terminology were checked against the current PF2e-RU
#   classfeatures translation used by the live Foundry module.
# - Text below is a concise RuneSheet rendering, not a bulk copy of either source.
SOURCE_AUDIT = {
    "legacy": "pf2e-ru-translation Inventor / Guns & Gears",
    "remaster": "PF2ERUS current classfeatures / PF2e 8.x",
    "mortar": "PF2ERUS current Light Mortar Innovation / Battlecry",
}

ARMOR_COMMON = {
    "Harmonic Oscillator": "Вы настроили доспех на частоту, гасящую силовые и звуковые колебания. Вы получаете сопротивление урону силой и звуком, равное 3 + половине вашего уровня; во время Перегрузки оно увеличивается ещё на 2.",
    "Metallic Reactance": "Сплавы доспеха отводят электричество и защищают от кислоты. Вы получаете сопротивление кислоте и электричеству, равное 3 + половине вашего уровня; во время Перегрузки оно увеличивается ещё на 2.",
    "Muscular Exoskeleton": "Экзоскелет усиливает движения силового доспеха. Во время Перегрузки вы получаете бонус обстоятельства +1 к проверкам Атлетики, а если вы мастер Ремесла — +2.",
    "Phlogistonic Regulator": "Изоляция доспеха защищает от резких перепадов температуры. Вы получаете сопротивление огню и холоду, равное половине вашего уровня; во время Перегрузки оно увеличивается ещё на 2.",
    "Speed Boosters": "Ускорители дают статусный бонус +5 футов к Скорости, а во время Перегрузки — +10 футов.",
    "Subtle Dampeners": "Системы маскировки и шумоподавления помогают скрываться. Во время Перегрузки вы получаете бонус обстоятельства +1 к Скрытности, а если вы мастер Ремесла — +2.",
    "Antimagic Plating": "Пока вы носите этот доспех, вы получаете бонус обстоятельства +1 к спасброскам и КБ против заклинаний. Если заклинание напрямую нацелено на сам доспех, бонус становится +4.",
    "Camouflage Pigmentation": "Покрытие доспеха подстраивается под окружение. Пока вы его носите, вы можете Спрятаться даже без укрытия или сокрытия.",
    "Dense Plating": "Пока вы носите доспех, вы получаете сопротивление рубящему урону, равное половине вашего уровня.",
    "Enhanced Resistance": "Выберите одну начальную модификацию доспеха, дающую сопротивление. Сопротивление от неё добавляет ваш полный уровень вместо половины уровня.",
    "Hyper Boosters": "Усовершенствованные ускорители дают статусный бонус +10 футов к Скорости, +20 футов во время Перегрузки и +30 футов во время Перегрузки, если вы легенда Ремесла. Требуются Speed Boosters.",
    "Layered Mesh": "Пока вы носите доспех, вы получаете сопротивление колющему урону, равное половине вашего уровня.",
    "Tensile Absorption": "Пока вы носите доспех, вы получаете сопротивление дробящему урону, равное половине вашего уровня.",
    "Automated Impediments": "Пока вы носите доспех, все соседние с вами клетки являются сложной местностью для ваших врагов.",
    "Incredible Resistance": "Выберите Dense Plating, Layered Mesh или Tensile Absorption на своей инновации. Сопротивление выбранной модификации становится равно вашему уровню вместо половины уровня.",
    "Multisensory Mask": "Пока вы носите доспех, вы получаете сокрытие от всех существ, в том числе использующих точные невизуальные чувства. Это сокрытие нельзя использовать для Спрятаться или Красться; после враждебного действия оно прекращается, пока вы не восстановите маску одиночным действием с признаком воздействие.",
    "Perfect Fortification": "При критическом попадании по вам в этом доспехе совершите чистую проверку КС 13; при успехе попадание становится обычным. Эффект не складывается с укреплением и аналогичными эффектами. Вы также получаете сопротивление точному урону 2 + половина вашего уровня.",
    "Physical Protections": "Пока вы носите доспех, вы получаете сопротивление всему физическому урону, включая продолжительный урон кровотечением, равное половине вашего уровня. Требуется Dense Plating, Layered Mesh или Tensile Absorption.",
    "Rune Capacity": "Инновация может иметь на одну руну свойства больше обычного предмета того же типа, максимум четыре руны свойства при руне мощи +3.",
}

ARMOR_LEGACY = {
    **ARMOR_COMMON,
    "Otherworldly Protection": "Вы получаете сопротивление негативному урону, равное 3 + половине вашего уровня; если у вас негативное исцеление, вместо этого сопротивление действует против позитивного урона. Вы также получаете такое же сопротивление тем видам урона мировоззрением, которые способны причинить вам вред.",
    "Heavy Construction": "Инновация становится тяжёлым доспехом, а владение именно этим доспехом повышается до уровня вашего владения средними доспехами. При Силе 16 или выше вы полностью игнорируете штраф к Скорости. Итоговые параметры: КБ +5, предел Лвк +1, штраф проверок −2, штраф Скорости −10 футов, Сила 16, Масса 3, группа композитный, признак bulwark.",
    "Energy Barrier": "Пока вы носите доспех, вы получаете сопротивление всему энергетическому урону — кислоте, холоду, электричеству, огню, силе, негативному, позитивному и звуковому — равное 2 + половине вашего уровня. Требуется Harmonic Oscillator, Metallic Reactance или Phlogistonic Regulator.",
}

ARMOR_REMASTER = {
    **ARMOR_COMMON,
    "Otherworldly Protection": "Вы получаете сопротивление урону пустотой, равное 3 + половине вашего уровня; если у вас исцеление пустотой, вместо этого сопротивление действует против урона жизненностью. Вы также получаете такое же сопротивление духовному урону; при освящении оно действует и против противоположного святого или нечестивого урона.",
    "Heavy Construction": "Инновация становится тяжёлым доспехом, а владение именно этим доспехом повышается до уровня вашего владения средними доспехами. При Силе +3 или выше вы полностью игнорируете штраф к Скорости. Итоговые параметры: КБ +5, предел Лвк +1, штраф проверок −2, штраф Скорости −10 футов, Сила +3, Масса 3, группа композитный; признаки bulwark и entrench.",
    "Energy Barrier": "Пока вы носите доспех, вы получаете сопротивление всему энергетическому урону — звуку, жизненности, кислоте, огню, пустоте, силе, холоду и электричеству — равное 2 + половине вашего уровня. Требуется Harmonic Oscillator, Metallic Reactance или Phlogistonic Regulator.",
}

CONSTRUCT = {
    "Accelerated Mobility": "Наземная Скорость вашей инновации увеличивается до 40 футов.",
    "Amphibious Construction": "Ваша инновация получает Скорость плавания 25 футов.",
    "Increased Size": "Ваша конструкция становится Большой. Если позднее она получает Большой размер другим способом, вы можете немедленно заменить эту модификацию другой начальной модификацией конструкта.",
    "Manual Dexterity": "У конструкции есть до двух достаточно ловких конечностей для действий с признаком воздействие. Как обычный компаньон, она всё ещё не может пользоваться оружием или удерживаемыми предметами без признака companion и не может активировать предметы.",
    "Projectile Launcher": "Конструкция получает дистанционную безоружную атаку, наносящую 1d4 дробящего или колющего урона на ваш выбор, с признаком propulsive и шагом дистанции 30 футов.",
    "Sensory Array": "Конструкция получает сумеречное зрение, тёмное зрение и неточное чувство вибрации на 30 футов.",
    "Wonder Gears": "Конструкция становится обучена Запугиванию, Скрытности и Выживанию.",
    "Advanced Weaponry": "Выберите одну безоружную атаку конструкции и дайте ей одну доступную вам начальную модификацию оружия. Атака должна выполнять требования выбранной модификации.",
    "Antimagic Construction": "Конструкция получает бонус обстоятельства +2 ко всем спасброскам и КБ против заклинаний.",
    "Climbing Limbs": "Конструкция получает Скорость карабканья, равную её наземной Скорости.",
    "Durable Construction": "Максимальные ОЗ конструкции увеличиваются на ваш уровень.",
    "Marvelous Gears": "Конструкция становится экспертом Запугивания, Скрытности и Выживания; навыки, в которых она уже эксперт, повышаются до мастера. После получения Revolutionary Innovation эти ранги повышаются до мастера или легенды соответственно. Требуются Wonder Gears.",
    "Turret Configuration": "Конструкция может одиночным действием с признаком воздействие превращаться в неподвижную турель и обратно. В форме турели она обездвижена, но урон Projectile Launcher становится d6, а шаг дистанции — 60 футов. Требуется Projectile Launcher.",
    "Flight Chassis": "Конструкция получает Скорость полёта 25 футов.",
    "Miracle Gears": "Модификатор Интеллекта конструкции увеличивается на 2, она изучает один известный вам язык, может использовать действия, требующие более высокого Интеллекта, и становится легендой в двух выбранных навыках на Интеллекте или Харизме. Требуются Marvelous Gears.",
    "Resistant Coating": "Конструкция получает сопротивление 5 всему урону, кроме адамантина.",
    "Runic Keystone": "В конструкцию встроен аналог рунного камня, позволяющий нанести одну руну свойства. Руна доспеха действует на саму конструкцию, если обычно действует на носителя; руна оружия действует на подходящие безоружные атаки с соблюдением обычных требований. Руны, меняющие только физическую форму или внешний вид предмета, эффекта не дают.",
    "Wall Configuration": "Конструкция может за 2 действия с признаком воздействие развернуться в прямую стену высотой до 10 футов и длиной до 30 футов, проходящую через её исходную клетку. В форме стены она не действует, кроме обратного превращения, становится застигнутой врасплох и получает дополнительный статусный штраф −2 к КБ. Стена перекрывает линию видимости и эффекта; при половине ОЗ или меньше через повреждения можно видеть и атаковать с укрытием, а Крошечные существа могут проходить.",
}

WEAPON_LEGACY = {
    "Blunt Shot": "Дистанционное оружие получает признаки nonlethal и versatile B; для каждой атаки вы решаете, применять ли nonlethal.",
    "Complex Simplicity": "Если основа — простое оружие, увеличьте кость урона на один шаг и выберите один признак: versatile B, versatile P или versatile S.",
    "Dynamic Weighting": "Подходящее одноручное оружие ближнего боя получает признак two-hand с костью на один шаг выше обычной и versatile B.",
    "Entangling Form": "Оружие ближнего боя получает признаки grapple и trip.",
    "Hampering Spikes": "Оружие ближнего боя получает признаки hampering и versatile P.",
    "Hefty Composition": "Оружие ближнего боя получает признаки shove и versatile B.",
    "Modular Head": "Инновация получает modular для дробящего, колющего и рубящего урона. При Взаимодействии для смены modular вы также можете добавить или убрать признак nonlethal.",
    "Pacification Tools": "Оружие ближнего боя получает disarm и nonlethal; для каждой атаки вы решаете, применять ли nonlethal.",
    "Razor Prongs": "Оружие ближнего боя получает trip и versatile S.",
    "Segmented Frame": "Инновация получает modular для дробящего, колющего и рубящего урона. Взаимодействием её можно сложить до лёгкой Массы и разложить обратно; в сложенном виде она получает concealable и даёт +2 обстоятельства к проверкам и КС Скрытности для сокрытия оружия.",
    "Advanced Rangefinder": "Дистанционное оружие получает backstabber, а его шаг дистанции увеличивается на 10 футов.",
    "Aerodynamic Construction": "Оружие ближнего боя получает sweep и versatile S.",
    "Inconspicuous Appearance": "Оружие ближнего боя получает backstabber и versatile P; если оно лёгкой Массы, также получает concealable.",
    "Integrated Gauntlet": "Подходящее одноручное оружие без признака two-hand получает free-hand.",
    "Manifold Alloy": "Инновация считается одновременно оружием из холодного железа и серебра.",
    "Rope Shot": "Дистанционное оружие получает climbing и ranged trip.",
    "Tangle Line": "Метательное оружие получает ranged trip и tethered.",
    "Attack Refiner": "Инновация получает backswing и shove.",
    "Deadly Strike": "Инновация получает deadly d8. Если deadly уже есть, его кость увеличивается до d12.",
    "Enhanced Damage": "Увеличьте кость урона оружия на один шаг. Это не складывается с Complex Simplicity и не может увеличить кость более чем на один шаг.",
    "Extensible Weapon": "Оружие ближнего боя получает reach; если reach уже был, дальность досягаемости увеличивается ещё на 10 футов вместо обычных 5.",
    "Impossible Alloy": "Инновация считается одновременно всеми семью небесными металлами для определения уязвимостей существ, но не получает прочие специальные свойства этих материалов.",
    "Momentum Retainer": "Оружие ближнего боя получает forceful и versatile B.",
    "Omnirange Stabilizers": "У дистанционного оружия удаляется volley, если он был; иначе шаг дистанции увеличивается на 50 футов или на исходный шаг дистанции, в зависимости от того, что больше.",
    "Rune Capacity": "Инновация может иметь на одну руну свойства больше обычного оружия, максимум четыре руны свойства при руне мощи +3.",
}

WEAPON_REMASTER = {
    "Blunt Shot": "Дистанционное оружие получает признаки concussive и ranged trip.",
    "Complex Simplicity": "Если основа — простое оружие, увеличьте кость урона на один шаг и выберите два признака из versatile B, versatile P, versatile S и razing.",
    "Dynamic Weighting": "Подходящее одноручное оружие ближнего боя получает two-hand с костью на один шаг выше и versatile B; если оно метательное, также получает tethered.",
    "Entangling Form": "Оружие ближнего боя получает disarm, grapple и trip.",
    "Hampering Spikes": "Оружие ближнего боя получает hampering, trip и versatile P.",
    "Hefty Composition": "Оружие ближнего боя получает razing, shove и versatile B.",
    "Modular Head": WEAPON_LEGACY["Modular Head"],
    "Pacification Tools": "Оружие ближнего боя получает hampering, nonlethal и disarm; для каждой атаки вы решаете, применять ли nonlethal.",
    "Razor Prongs": "Оружие ближнего боя получает tearing, trip и versatile S.",
    "Segmented Frame": WEAPON_LEGACY["Segmented Frame"],
    "Advanced Design": "В качестве основы инновации используйте параметры доступного вам обычного продвинутого оружия 0-го уровня; для определения владения вы считаете его воинским оружием.",
    "Advanced Rangefinder": "Дистанционное оружие получает backstabber, а его шаг дистанции увеличивается на 20 футов.",
    "Aerodynamic Construction": WEAPON_LEGACY["Aerodynamic Construction"],
    "Inconspicuous Appearance": WEAPON_LEGACY["Inconspicuous Appearance"],
    "Integrated Gauntlet": "Подходящее одноручное оружие без признаков two-hand и fatal aim получает free-hand.",
    "Manifold Alloy": WEAPON_LEGACY["Manifold Alloy"],
    "Rope Shot": "Дистанционное оружие получает climbing и ranged trip; если оно метательное, также получает tethered.",
    "Tangle Line": "Метательное оружие получает ranged trip, parry и tethered.",
    "Attack Refiner": "Инновация получает backswing и forceful.",
    "Deadly Strike": "Инновация получает deadly d8. Если deadly уже есть, увеличьте его кость на два шага, максимум до d12.",
    "Enhanced Damage": WEAPON_LEGACY["Enhanced Damage"],
    "Extensible Weapon": WEAPON_LEGACY["Extensible Weapon"],
    "Impossible Alloy": WEAPON_LEGACY["Impossible Alloy"],
    "Momentum Enhancer": "Инновация получает agile; если у оружия есть перезарядка, один раз за раунд вы можете перезарядить его свободным действием.",
    "Omnirange Stabilizers": WEAPON_LEGACY["Omnirange Stabilizers"],
    "Rune Capacity": WEAPON_LEGACY["Rune Capacity"],
}

MORTAR_REMASTER = {
    "Contained Shrapnel": "Инновация получает nonlethal. При каждом Выстреле вы решаете, применять ли этот признак.",
    "Enhanced Shrapnel": "Инновация получает versatile P и versatile S; при каждом Выстреле вы можете выбрать один из этих типов урона.",
    "Spring-Loaded": "Вы можете развернуть лёгкую мортиру свободным действием.",
    "Blanching Chamber": "Боеприпасы, прошедшие через камору, считаются изготовленными из серебра и холодного железа.",
    "Earthbreaker": "При каждом Выстреле вы можете направить основную силу взрыва вниз: он наносит половину урона, но создаёт сложную местность в области взрыва.",
    "Narrow Blast": "При каждом Выстреле вы можете заменить 10-футовый взрыв 20-футовым конусом из точки попадания, направленным прямо от вас либо под углом 45 градусов в любую сторону.",
    "Enhanced Damage": "Увеличьте кость урона мортиры на один шаг (d6 становится d8). Как обычно, кость нельзя увеличить более чем на один шаг.",
    "Impossible Alloy": "При Выстреле боеприпасы мортиры считаются изготовленными из всех семи небесных металлов для определения уязвимостей, но не получают прочие специальные свойства этих материалов.",
    "Precise Blast": "При Выстреле вы можете исключить из области взрыва число клеток, не превышающее ваш модификатор Интеллекта.",
}


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_name(name: str) -> str:
    value = name.strip()
    while True:
        stripped = re.sub(r"\s+\([^)]*\)\s*$", "", value).strip()
        if stripped == value:
            return value
        value = stripped


def inventor_tables(db: sqlite3.Connection) -> list[str]:
    tables: list[str] = []
    for (table,) in db.execute(
        "select name from sqlite_master where type='table' and name like 'specials_class_inventor%' order by name"
    ):
        columns = {c[1] for c in db.execute(f'pragma table_info("{table}")')}
        if {"name", "text_descrip"}.issubset(columns):
            tables.append(table)
    return tables


def category_for_table(table: str, *, remaster: bool) -> tuple[str, dict[str, str]]:
    lower = table.lower()
    if "armor" in lower or "armour" in lower:
        return "armor", ARMOR_REMASTER if remaster else ARMOR_LEGACY
    if "construct" in lower:
        return "construct", CONSTRUCT
    if "weapon" in lower:
        return "weapon", WEAPON_REMASTER if remaster else WEAPON_LEGACY
    if "mortar" in lower and remaster:
        return "mortar", MORTAR_REMASTER
    raise KeyError(table)


def suspect_rows(db: sqlite3.Connection) -> list[tuple[str, int, str, str]]:
    rows: list[tuple[str, int, str, str]] = []
    for table in inventor_tables(db):
        for rowid, name, text in db.execute(
            f'select rowid,name,text_descrip from "{table}" where text_descrip is not null'
        ):
            if sha_text(text) == MISBOUND_SHA256:
                rows.append((table, rowid, name, text))
    return rows


def schema_guard(db: sqlite3.Connection) -> dict[str, object]:
    schema = db.execute(
        "select type,name,tbl_name,coalesce(sql,'') from sqlite_master order by type,name,tbl_name"
    ).fetchall()
    counts: dict[str, int] = {}
    for (table,) in db.execute(
        "select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name"
    ):
        counts[table] = db.execute(f'select count(*) from "{table}"').fetchone()[0]
    return {
        "schema_sha256": hashlib.sha256(json.dumps(schema, ensure_ascii=False).encode("utf-8")).hexdigest(),
        "row_counts": counts,
    }


def integrity(db: sqlite3.Connection) -> dict[str, object]:
    return {
        "integrity_check": db.execute("pragma integrity_check").fetchone()[0],
        "foreign_key_violations": len(db.execute("pragma foreign_key_check").fetchall()),
    }


def ensure_no_target_triggers(db: sqlite3.Connection) -> None:
    targets = set(inventor_tables(db))
    triggers = db.execute(
        "select name,tbl_name from sqlite_master where type='trigger' order by name"
    ).fetchall()
    bad = [(name, table) for name, table in triggers if table in targets]
    if bad:
        raise RuntimeError(f"refusing guarded patch: Inventor target tables have triggers: {bad}")


def patch_one(src: Path, dst: Path, *, remaster: bool, audit_only: bool) -> dict[str, object]:
    if not audit_only and src.resolve() == dst.resolve():
        raise RuntimeError("input and output must be different paths")
    if not audit_only:
        shutil.copy2(src, dst)
    target = src if audit_only else dst
    db = sqlite3.connect(target)
    try:
        db.execute("pragma foreign_keys=on")
        ensure_no_target_triggers(db)
        before_schema = schema_guard(db)
        rows = suspect_rows(db)
        planned = []
        unknown = []

        for table, rowid, raw_name, old_text in rows:
            key = canonical_name(raw_name)
            try:
                category, rules = category_for_table(table, remaster=remaster)
            except KeyError:
                unknown.append({
                    "table": table,
                    "rowid": rowid,
                    "name": raw_name,
                    "canonical": key,
                    "reason": "unknown Inventor table category",
                })
                continue
            replacement = rules.get(key)
            if replacement is None:
                unknown.append({
                    "table": table,
                    "rowid": rowid,
                    "name": raw_name,
                    "canonical": key,
                    "category": category,
                    "reason": "name absent from source-verified map",
                })
                continue
            planned.append((table, rowid, raw_name, old_text, category, key, replacement))

        if unknown:
            raise RuntimeError(
                "unmapped Inventor rows still carry the misbound class-introduction fingerprint: "
                + json.dumps(unknown, ensure_ascii=False)
            )

        changes = []
        if not audit_only:
            for table, rowid, raw_name, old_text, category, key, replacement in planned:
                if sha_text(old_text) != MISBOUND_SHA256:
                    raise RuntimeError(f"before-value fingerprint changed: {table}/{rowid}/{raw_name}")
                cur = db.execute(
                    f'update "{table}" set text_descrip=? where rowid=? and name=? and text_descrip=?',
                    (replacement, rowid, raw_name, old_text),
                )
                if cur.rowcount != 1:
                    raise RuntimeError(f"before-value guard failed: {table}/{rowid}/{raw_name}")
                changes.append({
                    "table": table,
                    "rowid": rowid,
                    "name": raw_name,
                    "canonical": key,
                    "category": category,
                    "column": "text_descrip",
                    "before_sha256": MISBOUND_SHA256,
                    "after_sha256": sha_text(replacement),
                })
            db.commit()

            leftovers = suspect_rows(db)
            if leftovers:
                raise RuntimeError(
                    "misbound Inventor rows remain after patch: "
                    + json.dumps(
                        [{"table": t, "rowid": r, "name": n} for t, r, n, _ in leftovers],
                        ensure_ascii=False,
                    )
                )

            after_schema = schema_guard(db)
            if after_schema != before_schema:
                raise RuntimeError("schema or table row counts changed during content-only patch")

            check = integrity(db)
            if check["integrity_check"] != "ok" or check["foreign_key_violations"]:
                raise RuntimeError(f"sqlite integrity failed: {check}")
        else:
            check = integrity(db)

        by_category: dict[str, int] = {}
        for change in changes:
            by_category[change["category"]] = by_category.get(change["category"], 0) + 1

        return {
            "edition": "remaster" if remaster else "legacy",
            "input_sha256": sha_file(src),
            "audit_only": audit_only,
            "suspect_rows": len(rows),
            "mapped_rows": len(planned),
            "changed_cells": len(changes),
            "changed_by_category": by_category,
            "remaining_misbound_rows": len(rows) if audit_only else 0,
            "output_sha256": None if audit_only else sha_file(dst),
            "integrity": check,
            "schema_guard": before_schema,
            "changes": changes,
        }
    finally:
        db.close()


def main() -> None:
    p = argparse.ArgumentParser(
        description="Guarded RuneSheet 1.0.1 beta3 fix for misbound Inventor modification descriptions"
    )
    p.add_argument("master", type=Path, help="decrypted beta2 legacy/master sqlite")
    p.add_argument("remaster", type=Path, help="decrypted beta2 remaster sqlite")
    p.add_argument("master_out", type=Path)
    p.add_argument("remaster_out", type=Path)
    p.add_argument("--audit-only", action="store_true")
    p.add_argument("--report", type=Path)
    args = p.parse_args()

    master = patch_one(args.master, args.master_out, remaster=False, audit_only=args.audit_only)
    remaster = patch_one(args.remaster, args.remaster_out, remaster=True, audit_only=args.audit_only)
    result = {
        "release_candidate": "1.0.1-beta3",
        "policy": "content-only; exact old-text fingerprint; source-verified map; fail on unknown rows, triggers, leftovers, schema drift or FK/integrity failure",
        "sources": SOURCE_AUDIT,
        "master": master,
        "remaster": remaster,
        "total_changed_cells": master["changed_cells"] + remaster["changed_cells"],
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.report:
        args.report.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
