# PF2e Builder RU character format

## Goals

The native application owns its data format. It must be versioned, locally exportable, testable and independent from any upstream backend.

## v1 envelope

```json
{
  "schema": "pf2e-builder-ru.character",
  "version": 1,
  "character": {
    "id": "uuid",
    "name": "Имя",
    "level": 1,
    "ancestry": "",
    "background": "",
    "className": "",
    "notes": ""
  }
}
```

## Compatibility rules

- Unknown schema identifiers are rejected rather than guessed.
- Unknown format versions are rejected until an explicit migration exists.
- Imported IDs replace the existing local record with the same ID; new IDs create a new local record.
- Levels are normalized to the supported 1–20 range.
- Empty names receive a visible fallback instead of producing an unusable record.

## Planned v2+

Future versions will add independent typed sections for ability scores, skills, ancestry/background/class selections, feats, equipment, spells, companions/familiars and calculated state. New sections should avoid encoding display-only Russian text as identity; stable project IDs should reference rules-data entities instead.
