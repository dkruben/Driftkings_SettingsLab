# Fonts and characters

Moved from `docs/FONTES.md` and translated on 2026-10-30; the technical content is unchanged.

## Resolution

Settings keep the configured font name and the original text: Unicode, `!`, `&#x115;` and `<font face="…">` are not converted into symbols from another font. Font names with non-ASCII characters are also accepted in the Gameface panels and the carousel.

Configurable Flash fields use `embedFonts = false`, which allows lookup in the client's shared library, in the font provider configured by the client and in the embedded fonts. `$FieldFont` and `$TitleFont` remain game aliases and follow the active language. Fields that only reproduce native text, such as the diagnostics panel, keep their native properties.

The library `flash_source/shared/as3/driftkings/utils/fontlibrary.as` embeds the resources below in the battle SWF and the marker SWF. The marker integration copies the font definitions, metadata and class symbols, assigning free IDs and preserving the native resources; copying only the ABC would lose the glyphs. Class symbols are bound after the ABC.

Gameface uses the same TTFs from `res/gui/fonts/driftkings`, with `@font-face` declarations shared between the pages and the injected-view loader. The `mono` alias uses the real font instead of the generic `monospace` substitute. Native aliases use the font loaded by the view.

Flash fonts are registered once per library with `Font.registerFont`, from the glyphs embedded in the SWFs themselves. There is no Python registration, extra DLL or `driftkings.fonts` package. Gameface keeps loading the TTFs through its `@font-face` rules. The names `dkm` and `DriftkingsFont` share the same symbol map; the former aliases were removed on 2026-10-30, so profiles must use `dkm`.

OpenWG Common was removed from the distribution: its font registration also loaded GPU, audio, network, profiler and other modules, and introduced FPS limits and options in the native interface. The OpenWG Gameface dependency used by the panel is separate and is retained. The removal isolates that variable for comparison; on its own it does not prove the cause of an FPS drop in battle.

Selection stays at `embedFonts = false` to preserve client fonts and HTML with different fonts in the same field. According to the Scaleform documentation, locally embedded glyphs remain available as a fallback when the client library and font provider cannot resolve the name. `embedFonts = true` is not forced on every text field, because that would prevent normal use of the game's localized aliases.

Marker fields also use advanced antialiasing, fixed-size boxes and `TextFieldEx.setNoTranslate`, following the reference behaviour without translating names, resolved macros or symbols.

| Resource | Available names | Author stated in the TTF |
| --- | --- | --- |
| DriftkingsFont.ttf | dkm, DriftkingsFont | DriftkingsMods, 2020–2026 (supplied metadata); original glyphs by demon2597 |
| VehicleType.ttf | VehicleType, vtype | XSerzHX, 2015–2018 |
| DynamicDefault.ttf | DynamicDefault, dynamic | XSerzHX, 2015–2018 |
| DynamicOutline.ttf | DynamicOutline, dynamic2 | XSerzHX, 2015–2018 |
| ZurichCondMono.ttf | mono, ZurichCondMono | demon2597, 2012–2018 |

## Origin and licence

The four auxiliary fonts were copied unchanged from `xvm-master/src/xvm_fonts/assets`, the project's local reference of [XVM](https://modxvm.com/en/). The original reference distributes these resources under GPL-3.0; the licence text is in [licence](../../licence). The original aliases and credits are preserved; the source mod does not need to be installed. The TTFs are the source resources used to produce the Flash glyphs.

`DriftkingsFont.ttf` was supplied by the maintainer, unchanged. It replaces the `XVMSymbol.ttf` resource: inspection confirmed the same 114 characters and a `glyf` outline table identical to the previous font, so the credits for the original glyphs are preserved. Defaults use `dkm`; `dkm` and `DriftkingsFont` point to this resource in all three renderers.

SHA-256 of the imported resources:

- `DynamicDefault.ttf`: `2f03c81e256ee51e1ee25707084aba3af8ce4eb891ccd4e0880e2c138b20da82`
- `DynamicOutline.ttf`: `3285c29f35987d6f561c11577691eded906a6c995bd5850c14aa4fdd0748b345`
- `VehicleType.ttf`: `7452d77dbe0f7ad2e9fae422395106434426c632865633ddd5dfecc3c29572f7`
- `DriftkingsFont.ttf`: `368e8ecd244dd6f9dbd805883d9c1bc6a108b39ad1bcc05c39b775e9f3c550da`
- `ZurichCondMono.ttf`: `6158cb45aff173627540a798b66140c2084a042c353b8ed8497047fc9d340ec6`

## Coverage and validation

No font contains every possible character. An additional font can only be drawn if it is available to the renderer, and a symbol depends on the glyph map of the selected font. A symbol font is never silently replaced by normal text. Windows fonts depend on the provider exposed by the client; do not assume they are all accessible. To ship another font with the mod, include the resource and its licence, add the Flash declaration and the `@font-face`, and rebuild the SWFs.

The lookup order follows the [Scaleform documentation](https://help.autodesk.com/cloudhelp/ENU/Scaleform-Help/scaleform_help/font/part_3.html). This setup does not change personal profiles or the resources and fonts of other mods.

Validation of the replacement: native build completed; tests of the embedded resources and aliases, the marker schema on Python 2.7 and Gameface passed. At that time the DefineFont3 tables of both SWFs contained twelve embedded names (ten since the alias removal); `dkm`, `DriftkingsFont`, `xvm` and `XVMSymbol` include 114 glyphs and U+0115. The maintainer confirmed working fonts and no observed lag in the NA client after removing Common. No controlled FPS comparison was carried out.

The EU log of 27 October 2026, 16:08, contained two Gameface warnings for `monospace` (weights 400/700). Replacing that generic name with the loaded `mono` font is part of this setup.
