# AccountManager Gameface

The account launcher and editor use an owned Gameface layout. The unified package
does not include the three legacy AccountsManager SWFs. The existing OpenWG
dependency resolves the layout; authentication still goes through the client's
native Python LoginView and its active login mode.

The launcher retains the original 39 px account icon with normal/hover images.
The selection panel uses compact icon actions from the client's assets (enter,
edit and delete), with native tooltips, a gold primary action and restrained
metallic backgrounds. Its height follows the number of accounts, with a screen
height limit and scrolling for long lists. The editor, delete confirmation,
auto-enter and show-password toggle remain. Empty edited passwords retain the
saved value.

Launcher positioning reads the active native form's `keyboardLang.x` and
`submit.y` relative to its parent, matching the original AMButton placement.
WGC's filled form has no keyboard label, so its submit button's right edge is the
anchor. Login updates and resolution/UI-scale changes refresh the placement.
Before the form is ready, the current LoginFormPositionHelper supplies a fallback.

Gameface has no native HTML select control. The dropdown and checkboxes are owned
DOM controls with keyboard handling; Escape first dismisses the dropdown, then
the editor or confirmation, then the window. Form drafts survive validation and
save errors. The text input fields remain native Gameface text/password inputs.

The 2026-10-03 log exposed size-calculation timeouts, unloaded Arial fonts and
unsupported CSS selectors in the first migration. The layout now loads the
client's Warhelios fonts, sets explicit root dimensions and publishes its pixel
size after two animation frames, following native layout measurement. There is
no percentage-based viewport dependency during initial sizing.

The launcher and editor are available only in the login context and close when
it ends. The hangar cannot create or open either window, including through a late
callback. Auto-enter submits the selected account; disabling it fills the native
login form. A Steam client must select its account through Steam.

Storage remains in the existing preferences directory under
`Driftkings/accounts.manager`, with the existing BigWorld protection and compressed
JSON format. Legacy JSON is also readable. Editing with an empty password keeps
the stored value. A new server URL field preserves the choice when the host list
changes; older entries retain their numeric index until edited. Unreadable files
block writes, and failed saves restore the previous in-memory list.

The view model never contains a saved password. The email is decoded when editing;
the saved password is decoded only by the Python login operation. New passwords
are submitted through a model command, cleared from the form and never logged.

## Validation

The Gameface DOM/command test is `build_tools/tests/accounts_gameface_test.js`.
It also covers deferred measurement, UI scale, original images, disabled actions,
dropdown and checkbox interaction, confirmation, invalid form fields, error
drafts and cancelling pending layout work at disposal. Synthetic browser previews
are in `build/account-manager-preview/`; they are not in-game screenshots.
Account service checks with synthetic data covered list/edit exposure, keeping an
unchanged password, host reordering, failed writes and unreadable-store rejection.
The Python 2.7 build and package audit also check the included files.

In-game verification remains required: open the launcher at login; add, edit and
delete a test entry; check adaptive height, icon tooltips and placement at multiple
UI scales; test fill-only and auto-enter; then enter the hangar and check that the
launcher and editor have both disappeared. Return to login to check recreation.
No real account data was read during development, and the package was not deployed.
