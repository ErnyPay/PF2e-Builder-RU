# Distribution and licensing notes

This document is project hygiene, not legal advice.

## Upstream application

Pathbuilder 2e is distributed by Redrazors Ltd. This repository does not assume that possession of an APK grants permission to redistribute its proprietary application code or artwork. Therefore upstream APKs, extracted DEX files, decrypted databases and original assets are excluded from Git.

Before publishing a modified APK to GitHub Releases or an app store, obtain permission or replace upstream proprietary components with our own implementation / otherwise lawfully redistributable components.

## Pathfinder / Paizo content

Paizo publishes different categories of material under different policies/licenses. In particular:

- ORC covers designated Licensed Material (game-rules content), not trademarks or Reserved Material;
- Paizo's Community Use Policy permits certain freely available non-commercial uses subject to its conditions and required notice;
- Paizo's Compatibility License FAQ says the compatibility license itself is not available for apps and distinguishes game-content licenses from trademark rights.

Because an app can combine rules, names, setting material, translations and artwork from different sources, each data source needs provenance and an applicable license/permission.

Official references:

- https://paizo.com/licenses
- https://paizo.com/orclicense
- https://paizo.com/licenses/communityuse
- https://paizo.com/licenses/compatibility/faq

## Project naming

The project uses `PF2e Builder RU` rather than the full `Pathfinder` mark. Do not add Paizo/Pathfinder logos or imply endorsement without a license that permits it.

## Signing key

The Android private signing key is a secret and must never be committed. Losing it prevents seamless updates of an installed package; leaking it allows third parties to sign malicious updates under the same certificate.
