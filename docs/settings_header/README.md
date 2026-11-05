# Settings window header

Implemented locally on `feature/settings-header`, based on `develop` at `832d3263`, after explicit approval of proposal 01. The separate CT worktree is preserved. This change does not alter the release version, Python integration, settings persistence or social URLs.

The header remains 80rem high. `app.js` builds the existing top container with a centered independent logo, the dynamic registered core version at the upper left, and social buttons followed by the close button at the right. The compact layout reduces the logo width from 320rem to 220rem and keeps the version visible. No CSS Grid, masks, filters or external libraries are used.

## Assets

- `assets/header_driftkings.png`: 2800×160 PNG, 222040 bytes; original industrial/orange artwork generated with the built-in image tool and prepared as an approved panoramic background.
- `assets/driftkings_settingslab.png`: 820×274 transparent PNG, 162770 bytes; independent generated metallic wordmark/crown. The version is never part of either image.
- Existing `assets/social/*.svg` files remain the canonical icons. The old header JPEG is preserved.

The existing component manifest includes `settings_window/**`, so both PNGs are automatically selected. No new scripts, layout IDs or resource declarations are required.

## Theme and interaction

Normal social icons use their existing local SVG URLs. On mouse hover or keyboard focus, `app.js` recolors a trusted embedded copy of the corresponding SVG with the sanitized active theme accent and assigns an encoded SVG image URI. The header test checks that these templates match the canonical local SVGs. This avoids an asynchronous file request, SVG DOM manipulation, unsupported CSS tint filters or extra dependencies. Live theme changes update an active hover/focus immediately; leaving the button restores the local normal icon. An image decode error restores that normal icon and prevents repeated retries until the theme changes.

The X hover/focus color is emitted through the existing `applyTheme` style block. Button click actions remain `open_discord`, `open_facebook`, `open_youtube`, `open_github` and `close`; Escape follows the existing handling, including open dialogs and field focus. Keyboard focus outlines remain available.

## Verification and in-game approval

All 19 frontend suites and ES5 lint passed. The build-resource validator includes both new images (310 assets); the UI catalog remains unchanged and valid. Header regression coverage includes stable/beta/missing versions, schema refresh, live theme changes, hover/focus overlap, fallback after an image error, social actions, X and Escape.

A temporary browser harness ran the real frontend with a simulated native model across 80 combinations: WoT/Dark/Black/Transparent/Custom palettes; 1024×768, 1280×720, 1920×1080 and 2560×1440; and UI scale 80%, 100%, 130% and 140%. Geometry checks found no overlap between the version, logo and controls, kept the logo centered and the version visible. The browser also decoded the themed SVG image successfully. This is browser evidence, not native Gameface acceptance.

The owner confirmed the completed panel in the EU client after testing local build `0.1.7-beta.5` and explicitly approved commit and push on 2026-11-05. This includes the final Account Manager icon correction. This is owner-declared in-game acceptance, not an independently recorded per-theme/per-resolution game matrix or new NA/ASIA validation. If another renderer rejects the tinted SVG URI, the normal packaged icon remains the fallback. Test builds were compiled locally; no release publication is part of this panel change.

## In-game sizing correction

The first EU test screenshot showed the logo vertically flattened despite the browser preview. The logo now has explicit width, height and top offset in rem, derived from the PNG ratio 820:274: 320×106.93rem at top -13.46rem, and 240×80.2rem at top -0.1rem in compact mode. This removes intrinsic auto-height and percentage-transform dependencies. The owner subsequently confirmed the corrected logo in game.

## Account icon and social sizing

A new native SVG icon at `assets/mods/accounts.svg` uses the existing 24×24 stroked icon style, depicting a user and key. `legacy.AccountManager` now selects it for the settings sidebar and section heading; the account-manager launcher images and login/account behavior are unchanged. Social glyphs are reduced from 24rem to 18rem while preserving their 40rem click targets (36rem wide in compact mode). The close-button margin is increased from 4rem to 16rem. The compact logo now uses 220×73.51rem at top 3.24rem, maintaining the PNG ratio and enough clearance at the smallest checked viewport/scale. The updated 80-case browser geometry matrix and all 19 frontend suites passed.

The first Account Manager icon mapping incorrectly used the canonical settings key. It now uses the actual panel schema ID `legacy.AccountManager`, derived by the backend from its legacy-name mapping. The real-schema frontend test verifies both the sidebar and section heading, so a fabricated fixture ID cannot mask this mismatch again.
