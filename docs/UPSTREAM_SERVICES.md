# Inherited service inventory

Static inventory from the `0.1.0-alpha.1` transition build. This is a migration checklist, not proof that every bundled SDK is actively used on every code path.

## Must be detached or replaced

### Google Mobile Ads

The manifest still requests ad/attribution permissions, declares Google Mobile Ads activities/services/providers, and carries the upstream AdMob application identifier.

Target: remove the original publisher identity and disable/remove ad initialization before any public PF2e Builder RU distribution.

### Google Play Billing

The APK bundles BillingClient 8.0.0, requests `com.android.vending.BILLING`, and contains the upstream billing flow.

Target: remove or replace purchase/entitlement behavior. Never sell an entitlement through the upstream product identifiers from our package.

### Firebase

The APK contains Firebase Auth, Realtime Database, Analytics/Measurement, Installations and related initialization providers. The legacy code also contains Firebase export/sync model classes.

Target: feature-gate network sync first, then replace it with our own optional backend or a local-only implementation. Do not silently send PF2e Builder RU data to an upstream Firebase project.

### Original Pathbuilder web/backend links

Static DEX strings include legacy endpoints and links such as:

- `pathbuilder2e.com/json.php?id=...`;
- `pathbuilder2e.com/launch.html` / build links;
- old Pathbuilder issue tracker;
- original Patreon links;
- original Google Play / market package links.

Target: remove, replace, or clearly isolate these routes. Import compatibility may keep a parser for user-supplied legacy data without claiming or depending on the upstream service.

### Google Sign-In / Drive

Google Sign-In classes and Drive scopes are bundled, including `drive.appdata`.

Target: decide whether cloud backup remains a feature. If yes, implement it under credentials registered to our own application ID; otherwise provide reliable local export/import.

## Probably safe framework dependencies

These are not upstream product identity by themselves and can remain while we migrate functionality:

- AndroidX WorkManager;
- AndroidX Startup;
- Room multi-instance invalidation;
- standard Google Play services plumbing that remains required by a feature we deliberately keep.

They should still be trimmed when no longer needed.

## Migration order

1. Device smoke-test the side-by-side alpha before changing behavior.
2. Add a diagnostics screen / feature flags so inherited network features can be disabled explicitly.
3. Disable ads and original store billing paths.
4. Disable original Firebase initialization and verify fully local character creation/editing.
5. Replace backup/export with local files first.
6. Add our own optional cloud integration only after independent credentials, privacy policy and data model exist.
7. Remove dead SDKs/resources from the eventual native source project.

## Verification requirements

Every service-removal change must preserve offline character creation, editing, level-up, equipment, spell/feat selection, save/load and local export/import. Network calls should be observable in diagnostics and covered by a deny-by-default policy in the native rewrite.
