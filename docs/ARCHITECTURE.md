# Architecture

## Current transition architecture

PF2e Builder RU currently treats the known-working localized APK as an **external build input** and applies a narrow, verified overlay.

### 1. Manifest migration

`scripts/manifest_patch.py` edits binary Android XML without decompiling/recompiling application code. It:

- sets our application ID;
- sets our user-facing name and version;
- assigns unique provider authorities;
- gives the generated AndroidX receiver permission a unique package-scoped name.

Java/Kotlin component class names are left untouched. Android allows an APK application ID to differ from the package namespaces of its classes.

### 2. Safe DEX patching

`scripts/dex_patch.py` changes only strings whose encoded `string_data_item` size is exactly preserved. It then recomputes DEX SHA-1/Adler32 and verifies global `string_ids` ordering.

Current DEX migrations:

- old application ID -> PF2e Builder RU application ID;
- old hard-coded database path -> our data directory;
- old FileProvider authority -> a unique authority.

No string table reconstruction is performed.

### 3. Resource branding

`scripts/brand_assets.py` generates independent launcher icons and in-app logo assets. `scripts/arsc_patch.py` updates the legacy app-name resource without shifting resource-table offsets.

### 4. Repack and signing

`scripts/apk_sign.py`:

- removes old signature entries;
- preserves original compression methods;
- preserves required 4-byte / 4096-byte alignment for stored entries and native libraries;
- signs v1 with `jarsigner`;
- adds APK Signature Scheme v2;
- verifies the final ZIP/signature structure.

### 5. Verification

`scripts/verify_apk.py` checks:

- ZIP CRCs;
- DEX SHA-1 and Adler32;
- DEX string ordering required by ART;
- JAR/v1 signature;
- APK Signature Scheme v2 content digest and certificate signature.

## Target architecture

Binary patching is a migration mechanism, not the desired end state.

Long term we want:

1. own Android UI/application shell;
2. own domain model and character engine;
3. versioned, source-controlled rules data using only content we are allowed to redistribute;
4. import/export compatibility adapters;
5. deterministic tests for calculations and advancement rules;
6. zero dependency on upstream APK internals.
