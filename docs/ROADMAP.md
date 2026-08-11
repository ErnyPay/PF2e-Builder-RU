# Roadmap

## Product rule

The product baseline is `Pathbuilder2e_256_RU_DB76_round5_polished`.

We keep its working PF2e mechanics, calculations, rules dictionaries, Russian translations/descriptions and polished content databases intact. Product work changes the app around that content: identity, branding, UX, unwanted services and technical ownership layers.

A feature is never removed just because we plan to replace its implementation later. Internal replacements are allowed only as verified 1:1 replacements.

## 0.1 — Baseline protection and reproducibility

- [x] deterministic polished base-APK fingerprint check;
- [x] protected `assets/master.db` SHA-256 baseline;
- [x] protected `assets/remaster.db` SHA-256 baseline;
- [x] verify protected database hashes in produced transition APKs;
- [x] v1/v2 signing and DEX verification tooling;
- [ ] device smoke test of the next protected-content transition build;
- [ ] freeze and securely back up the release signing key.

Protected content hashes:

- `assets/master.db`: `06f09830b2e578dd1ab01730537ec76b9b05e37a68902fe744a9f6c37b889b81`
- `assets/remaster.db`: `8485608ddf46b3b5437bd8b051b2d47fa6118b0bfaa5187a59bdd3f831289f1d`

## 0.2 — Make the existing app ours: identity and shell

- [x] independent app name;
- [x] independent application ID/local data directory;
- [x] independent provider authorities;
- [x] original launcher icon/logo generation;
- [x] project-owned faceted action glyph generation;
- [ ] finish app name/About/splash/branding consistency across all screens;
- [ ] remove remaining original-brand UI strings where they are not rules/content;
- [ ] verify character creation, character sheet and existing content behave exactly like the polished baseline.

## 0.3 — Detach inherited services without touching gameplay

- [x] inventory Google/Firebase/ads/billing dependencies;
- [ ] isolate ads/billing/analytics paths one dependency at a time;
- [ ] stop claiming original application/store/deep-link identity where safe;
- [ ] preserve all offline character-builder mechanics during service removal;
- [ ] verify export/import/share flows after each service change;
- [ ] keep third-party notices/licenses/attribution required by bundled content.

## 0.4 — Own the UX incrementally

- [ ] document current polished screens and navigation as regression reference;
- [ ] introduce project theme/components without changing rules text or calculations;
- [ ] replace visual elements screen-by-screen, not with a blank new builder;
- [ ] keep information density and existing user workflows unless a deliberate UX task says otherwise;
- [ ] device regression check after every substantial screen change.

## 0.5 — Technical replacements only where useful

- [ ] identify internal modules that actually need replacement;
- [ ] define observable behavior/data contract before each replacement;
- [ ] implement replacement behind the same user workflow;
- [ ] compare outputs against the polished baseline;
- [ ] remove old implementation only after parity is demonstrated.

## Native research track (secondary)

`native/` remains useful for experiments with project-owned Android code, storage and components. It is not the current product replacement and it does not own or replace the polished rules/translations databases.

- [x] native Android proof-of-concept exists;
- [x] independent native storage/JSON experiments exist;
- [ ] reuse native components only when they can replace a real product component without losing behavior/content;
- [ ] keep `rules/catalog` isolated from the polished product content unless a future explicit decision changes this rule.

## 1.0 target

- [ ] recognizable project-owned identity and UX;
- [ ] polished rules/content preserved and regression-protected;
- [ ] unwanted inherited online/commercial services removed or isolated where feasible;
- [ ] stable character data/update path;
- [ ] signed release/update workflow with protected secrets;
- [ ] licenses/notices/provenance retained;
- [ ] public distribution only after a separate rights/permission review.
