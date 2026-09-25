# PF2eRUS / RuneSheet modernization

## Goal
Maintain a reproducible Russian-localized Android build based on the user's working RuneSheet experience while tracking current Pathbuilder 2e data/runtime compatibility.

## Functional requirements
- Preserve the RuneSheet Russian UI and familiar workflow where technically possible.
- Track the current Pathbuilder 2e runtime/data baseline (initial modernization target: 294).
- Support current PF2e classes and their actual character-building data, not placeholder class names.
- Preserve character creation/editing behavior.
- Add/retain Pathbuilder character transfer/import functionality.
- Produce installable modern Android APKs with correct alignment and APK Signature Scheme v2/v3 signing.

## Validation gates
A build must not be called a release until the available checks pass:
1. ZIP integrity.
2. AndroidManifest/resources parse successfully.
3. DEX headers/checksums and cross-DEX references are structurally valid.
4. Native libraries match the intended ABI packaging.
5. APK is zipaligned.
6. APK signature is verified with Android apksigner (v2/v3 as applicable).
7. Install/launch smoke test is performed on an Android environment or physical target device.

## Repository policy
Do not commit proprietary upstream APK/XAPK files, signing keys, decrypted databases, or generated APKs. Keep reproducible tooling, documentation, patches/diffs that may legally be distributed, and CI definitions in Git.
