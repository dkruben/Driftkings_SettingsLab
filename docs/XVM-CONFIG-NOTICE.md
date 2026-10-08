# XVM adaptation attribution

PlayerPanelPro v2 defaults are adapted from XVM Contributors' WG configurations:
`playersPanel.xc`, `battleLoading.xc`, `battleLoadingTips.xc`, `statisticForm.xc`.
The geometry and option semantics were checked against XVM's
`PlayersPanelListItemProxyBase.as`, `PlayersPanelListItemProxy.as`,
`UI_PlayersPanel.as`, `StatsTableItemXvm.as`, and
`XvmBattleLoadingItemRendererProxyBase.as`, plus `macros.txt` and `extra-field.txt`.
Reference: the local `WoT_Tools/xvm-master` checkout, https://modxvm.com/.

These adapted configurations and the new PlayerPanelPro renderer are provided under
GPL-3.0-or-later. The license is included in `XVM-CONFIG-LICENSE.txt`.

Changes: JSON instead of XC; a new data-only Python macro parser and DAAPI bridge;
new ActionScript renderers using native client public components; native fonts;
no XMQP, clan icons, service flags or XVM-user markers; native badge graphics;
selected Driftkings rating/color scales. See PLAYER_PANEL_PRO.md for the compatibility
boundaries and client testing requirements. No XFW runtime is included.
