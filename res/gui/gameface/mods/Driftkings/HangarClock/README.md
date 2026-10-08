# Hangar clock

Included in HangarOptions, rendered by the owned Driftkings Gameface bridge in RandomHangar.
The model injects `clock.js` and `clock.css`; `model.html` is the resource-map entry.

Five `clockStyle` values: 0 minimal, 1 digital, 2 analog, 3 flip-style tiles,
4 dashboard. The flip style uses split tiles; it does not animate a mechanical flap.
`clockX` is an offset from the right edge, `clockY` from the top, in UI units.
`clockScale` accepts 50–200 percent. `clockSeconds` and `clock24Hour` control time display.
Time and date use the computer's local clock and browser locale.

The clock is hidden outside RandomHangar, including login and battle. No global
Python timer or GUIFlash component remains. Browser timers stop when hidden;
model callbacks and DOM elements are removed on disposal or reinjection.
Legacy `text`, `customClockText`, `customClockFormat` and `panel` JSON values are
retained for reference but no longer style this Gameface clock.

Preview: `previews/HangarClock.html` loads the production assets directly.
Validate placement, scaling and transitions to other screens in the client.
