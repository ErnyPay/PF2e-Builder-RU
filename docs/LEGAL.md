# Distribution and licensing notes

This document is project hygiene, not legal advice.

## RuneSheet RU transition build

`RuneSheet RU` is the public-facing visual identity of the temporary transition build. The transition APK deliberately avoids using Pathbuilder/Pathfinder/Paizo as its product name and replaces inherited launch art, parchment/ornament assets and action glyph artwork with project-owned generated resources.

That visual differentiation is only a branding step. It does **not** grant redistribution rights to inherited application code, databases or third-party assets. Do not treat a reskinned APK as independently licensed software.

Pathbuilder 2e is distributed by Redrazors Ltd. This repository does not assume that possession of an APK grants permission to redistribute its application code or artwork. Therefore upstream APKs, extracted DEX files, decrypted databases and original assets are excluded from Git.

Before publishing a modified transition APK to GitHub Releases or an app store, independently verify rights to redistribute/modify the inherited binary code or replace those components with our own implementation / otherwise lawfully redistributable components.

## Pathfinder / Paizo content

Paizo uses several different policies and licenses for different material:

- ORC can cover designated rules material, but does not grant rights to Paizo trademarks or Reserved Material;
- Paizo's reinstated Community Use Policy permits certain non-commercial uses subject to its conditions, but does not replace the licenses needed for game-rules products;
- Paizo's Fan Content Policy explicitly treats character builders/rules databases as RPG products and says those products are not publishable under that policy;
- therefore rules content, trademarks, setting material, translations and artwork must each have a clear provenance and applicable license/permission.

Official references:

- https://paizo.com/licenses
- https://paizo.com/licenses/communityuse
- https://paizo.com/licenses/fancontent/
- https://paizo.com/licenses/fancontent/faq

## Branding / trade dress

The transition product identity is **RuneSheet RU**. Do not use Pathbuilder, Paizo or Pathfinder logos as RuneSheet branding, and do not make the UI intentionally imitate their visual presentation. Compatibility references should be descriptive and separated from the product name.

The current generated identity uses an original rune/compass sigil, slate/cyan/amber palette, geometric cards, neutral backgrounds and project-owned action notation.

## Inherited services

Before presenting the transition build as an independent public product, remove or replace inherited service identities where technically possible, including upstream ad IDs, billing flows, Firebase/backend configuration, support links and other external endpoints. Do not redirect or impersonate upstream services.

## Native app

The clean `native/` codebase remains the preferred route for a distributable independent product because code ownership, package identity, UI, storage and service dependencies can be controlled directly.

## Signing key

The Android private signing key is a secret and must never be committed. Losing it prevents seamless updates of an installed package; leaking it allows third parties to sign malicious updates under the same certificate.
