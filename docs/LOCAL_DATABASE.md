# Native local database

PF2e Builder RU owns a local SQLite database named `pf2e-builder-ru.db`.

## Schema v1

Table `characters`:

- `id TEXT PRIMARY KEY` — stable character UUID;
- `name TEXT`;
- `level INTEGER`;
- `ancestry TEXT`;
- `background TEXT`;
- `class_name TEXT`;
- `notes TEXT`;
- `updated_at INTEGER`.

`updated_at` is indexed and currently drives the default most-recently-edited ordering.

## Migration policy

The first SQLite repository automatically imports the temporary `characters-v1` SharedPreferences collection from earlier native dev builds and then removes that legacy JSON payload.

Future database versions must use explicit migrations. The database helper intentionally fails loudly when a version bump has no migration rather than silently destroying user characters.

As the character model grows, normalized child tables will be introduced for selections, feats, equipment, spells and other repeating structures. The JSON export format remains the portable compatibility boundary and can evolve independently through its own versioned migrations.
