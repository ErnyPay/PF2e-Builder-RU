# Roadmap

## 0.1 — Identity and reproducibility

- [x] independent app name;
- [x] independent application ID;
- [x] independent local data directory;
- [x] independent provider authorities;
- [x] original launcher icon/logo generation;
- [x] deterministic base-APK fingerprint check;
- [x] v1/v2 signing and DEX verification;
- [ ] device smoke test of side-by-side installation;
- [ ] freeze and securely back up the release signing key.

## 0.2 — Remove inherited service dependencies

- [ ] inventory Google/Firebase/ads/billing dependencies;
- [ ] disable or replace features tied to the original package/store listing;
- [ ] stop claiming original Pathbuilder deep links;
- [ ] add our own About / diagnostics screen;
- [ ] add explicit local backup/export flow.

## 0.3 — Data ownership layer

- [ ] define open JSON/SQLite schema for rules data;
- [ ] create importers from license-compatible sources;
- [ ] move Russian terminology overrides into source control;
- [ ] create automated English/mixed-string audit;
- [ ] add ORC/OGL attribution generation where applicable.

## 0.4 — Native PF2e Builder RU shell

- [ ] new Android project owned by this repository;
- [ ] home/character-list screen;
- [ ] character creation wizard;
- [ ] character sheet;
- [ ] feats/spells/equipment search;
- [ ] import bridge from legacy local format.

## 1.0

- [ ] no runtime dependency on upstream APK code;
- [ ] reproducible release build from source;
- [ ] public distribution only after license/permission review;
- [ ] migration path for users of alpha builds.
