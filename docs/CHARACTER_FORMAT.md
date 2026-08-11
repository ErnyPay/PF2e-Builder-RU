# RuneSheet character format

Current schema: `pf2e-builder-ru.character` v3.

## Stable rules references

Starting with v3, character files preserve project-owned stable rule IDs separately from display text:

- `rules.ancestryId`
- `rules.backgroundId`
- `rules.classId`

Legacy `ancestry`, `background` and `className` strings remain in the file as readable/fallback display values. This lets translations and descriptions change without breaking saved characters.

Older v1/v2 exports remain importable. Missing stable IDs are resolved opportunistically in the UI by matching their legacy Russian/English names against the bundled rules catalog; unmatched text is preserved.

## Attributes

The six attribute modifiers are stored under `attributes`:

- `strength`
- `dexterity`
- `constitution`
- `intelligence`
- `wisdom`
- `charisma`

## Compatibility

The format is project-owned and versioned independently from any transition/upstream storage. New fields must be added compatibly, and migrations should preserve unknown or legacy user-visible data whenever possible.
