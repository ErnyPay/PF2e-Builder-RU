# Roadmap

## 0.1 — Identity and reproducibility

- [x] independent app name;
- [x] independent application ID;
- [x] independent local data directory;
- [x] independent provider authorities;
- [x] original launcher icon/logo generation;
- [x] deterministic base-APK fingerprint check;
- [x] v1/v2 signing and DEX verification;
- [ ] device smoke test of side-by-side transition alpha;
- [ ] freeze and securely back up the release signing key.

## 0.2 — Remove inherited service dependencies from transition build

- [x] inventory Google/Firebase/ads/billing dependencies;
- [ ] disable or replace features tied to the original package/store listing;
- [ ] stop claiming original Pathbuilder deep links;
- [ ] add explicit local backup/export flow to transition build;
- [ ] verify offline core after inherited network paths are disabled.

## 0.3 — Data ownership layer

- [x] define v1 source-controlled catalog shape and provenance requirements;
- [x] add CI validation for catalog IDs/provenance;
- [ ] create importers from license-compatible sources;
- [ ] move Russian terminology overrides into source control;
- [ ] create automated English/mixed-string audit for owned catalogs;
- [ ] add attribution generation where applicable.

## 0.4 — Native PF2e Builder RU

- [x] new Android project owned by this repository;
- [x] own theme/icon and diagnostics screen;
- [x] local character list;
- [x] create/edit/delete basic character record;
- [x] own versioned JSON character format with v1 -> v2 migration;
- [x] local JSON export/import;
- [x] native CI producing a debug APK artifact;
- [x] own SQLite database + explicit v1 -> v2 migration;
- [x] six PF2e attribute modifiers in owned character model;
- [ ] ancestry/background/class rules selection from owned rules catalog;
- [ ] proficiencies/skills and derived calculations;
- [ ] feats/spells/equipment domain modules;
- [ ] transition/legacy character migration adapter.

## 0.5 — Replace transition app feature-by-feature

- [ ] character creation parity for core rules;
- [ ] character sheet and level-up workflow;
- [ ] equipment and inventory;
- [ ] feats/actions;
- [ ] spells/focus/preparations;
- [ ] companions/familiars where supported by licensed data;
- [ ] PDF/local share export;
- [ ] migration tests against user-owned exported fixtures.

## 1.0

- [ ] no runtime dependency on upstream APK code;
- [ ] reproducible release build from source-controlled native project;
- [ ] signed release/update workflow with protected secrets;
- [ ] public distribution only after license/permission review;
- [ ] migration path for alpha users.
