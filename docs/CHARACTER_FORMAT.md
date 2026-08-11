# PF2e Builder RU character format

## Goals

The native application owns its data format. It is versioned, locally exportable, testable and independent from any upstream backend.

## v2 envelope

```json
{
  "schema": "pf2e-builder-ru.character",
  "version": 2,
  "character": {
    "id": "uuid",
    "name": "Имя",
    "level": 1,
    "ancestry": "",
    "background": "",
    "className": "",
    "attributes": {
      "strength": 0,
      "dexterity": 0,
      "constitution": 0,
      "intelligence": 0,
      "wisdom": 0,
      "charisma": 0
    },
    "notes": ""
  }
}
```

In the Russian UI `constitution` is displayed as **Выносливость** to match the project's PF2e RU terminology reference.

## v1 -> v2 migration

The importer accepts both versions. A v1 character had no `attributes` object, so migration supplies `0` for all six modifiers. The next export writes v2.

## Compatibility rules

- Unknown schema identifiers are rejected rather than guessed.
- Future format versions are rejected until an explicit migration exists.
- Imported IDs replace the existing local record with the same ID; new IDs create a new local record.
- Levels are normalized to 1–20.
- Attribute modifier input is protected by wide corruption/import safety bounds; actual character-building legality belongs to the rules engine, not the storage codec.
- Empty names receive a visible fallback instead of producing an unusable record.

## Planned v3+

Future versions will add independent typed sections for skills, ancestry/background/class selections, feats, equipment, spells, companions/familiars and calculated state. New sections should avoid encoding display-only Russian text as identity; stable project IDs reference rules-data entities instead.
