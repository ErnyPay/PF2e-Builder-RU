# Branding — RuneSheet RU

## Product name

**RuneSheet RU**

The public-facing name deliberately does not contain Pathbuilder or Pathfinder. Compatibility may be described separately in documentation/about text, not as the product identity.

## Visual direction

The visual system is intentionally unrelated to Pathbuilder/Pathfinder trade dress:

- deep slate + cyan + amber instead of red/black/parchment branding;
- original rune/compass sigil instead of PF/P2/d20 monograms;
- geometric/grid backgrounds instead of fantasy illustration banners;
- baked-in home labels are Russian and use a modern utility-card layout;
- project-owned action language: one/two/three cyan diamond pips for action cost, a circular-arrow diamond for reaction, and a hollow radiant diamond for a free action;
- inherited light-theme parchment, red braces and scroll ornament are replaced by neutral project-owned assets;
- no Paizo/Pathfinder/Pathbuilder logos or official art.

The old temporary `1 / 2 / 3 / R / F` badges were removed in `0.3.0-alpha.3`; they looked like developer placeholders rather than product UI.

## Android identity

- application ID: `com.pf2ebuilder.ru.builderx` (temporary transition ID; kept for safe in-place updates)
- display name: `RuneSheet RU`
- current transition version: `0.3.0-alpha.3`

The transition ID is intentionally kept stable to avoid risky DEX string-table relocation. The visible product identity is RuneSheet RU; a clean package ID belongs to the native codebase, where it can be changed without binary patching.

## Legal positioning

Visual differentiation reduces brand confusion but does **not** change ownership of inherited binary code or data. The transition build remains a migration/testing layer. Public redistribution requires a separate rights/licensing review and must not imply endorsement by Paizo or Redrazors.
