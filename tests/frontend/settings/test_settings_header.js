const assert = require('assert');
const fs = require('fs');
const path = require('path');
const {createEnvironment, root} = require('../../support/frontend/dom_fixture');
const env = createEnvironment();
const {app, callbacks, sent, document, DK, themeStyle} = env;
const schema = {labels: {title: 'DRIFTKINGS · SETTINGS', close: 'Close'}, mods: [
    {id: 'dk.settings', name: 'Driftkings', version: '0.1.7-beta.1', category: 'system', controls: [], dependencies: []}
]};
const state = {selected: 'dk.settings', values: {'dk.settings': {}}, changed: {}, disabled: {}, secrets: {},
    status: {'dk.settings': {status: 'active', enabled: true}}, theme: {accent: '#D98219'},
    profiles: ['default'], restartRequired: [], keyNames: {}, updater: {status: 'IDLE'}};
callbacks.schema(schema); callbacks.state(state);
const logo = app.querySelector('.dk-brand-logo');
assert(logo.src.endsWith('/driftkings_settingslab.png'));
assert.strictEqual(app.querySelector('.dk-version').textContent, 'v0.1.7-beta.1');
const socials = app.querySelectorAll('.dk-social');
const controls = app.querySelector('.dk-top-controls');
assert.strictEqual(controls.lastChild, app.querySelector('.dk-close'));
['discord', 'facebook', 'youtube', 'github'].forEach((service, i) => {
    const button = socials[i], image = button.querySelector('img'), normal = image.src;
    const canonical = fs.readFileSync(path.join(root,
        'mod/res/gui/gameface/mods/driftkings/settings_window/assets/social', service + '.svg'), 'utf8').trim();
    const count = sent.length;
    button.fire('mouseenter');
    assert.strictEqual(decodeURIComponent(image.src.split(',').slice(1).join(',')), canonical.replace(/#FFFFFF/g, '#D98219'));
    button.fire('focus'); button.fire('mouseleave');
    assert(image.src.startsWith('data:image/svg+xml;'), 'keyboard focus keeps theme tint after mouse leaves');
    state.theme = {accent: '#CA00FF'}; callbacks.state(state);
    assert(decodeURIComponent(image.src).includes('#CA00FF'), 'active hover/focus follows live theme changes');
    button.fire('blur'); assert.strictEqual(image.src, normal);
    assert.strictEqual(sent.length, count, 'presentation events do not mutate settings or open links');
    button.fire('mouseenter'); image.fire('error');
    assert.strictEqual(image.src, normal, 'an unsupported tinted image falls back to the packaged SVG');
    button.fire('mouseleave'); button.fire('mouseenter'); assert.strictEqual(image.src, normal);
    button.fire('mouseleave');
    button.fire('click'); assert.strictEqual(sent[sent.length - 1][0], 'open_' + service);
    state.theme = {accent: '#D98219'}; callbacks.state(state);
});
// Schema refreshes keep the logo and read the version from data, including stable versions.
schema.mods[0].version = '0.1.7'; callbacks.schema(schema); callbacks.state(state);
assert.strictEqual(app.querySelector('.dk-brand-logo'), logo);
assert.strictEqual(app.querySelector('.dk-version').textContent, 'v0.1.7');
schema.mods[0].version = ''; callbacks.schema(schema); callbacks.state(state);
assert.strictEqual(app.querySelector('.dk-version').textContent, '');
schema.mods.push({id: 'legacy.AccountManager', name: 'Gestor de contas', category: 'general', controls: [], dependencies: []});
state.values['legacy.AccountManager'] = {};
state.selected = 'legacy.AccountManager';
callbacks.schema(schema); callbacks.state(state);
assert(app.querySelector('.dk-title-icon').src.endsWith('/mods/accounts.svg'));
assert(app.querySelectorAll('.dk-nav-icon').some(icon => icon.src.endsWith('/mods/accounts.svg')));
assert(themeStyle.textContent.includes('.dk-close:hover'));
app.querySelector('.dk-close').fire('click'); assert.strictEqual(sent[sent.length - 1][0], 'close');
const beforeEscape = sent.length;
(document.listeners.keydown || []).forEach(fn => fn({keyCode: 27, target: document.body,
    preventDefault() {}, stopPropagation() {}}));
assert.strictEqual(sent.length, beforeEscape + 1);
assert.strictEqual(sent[sent.length - 1][0], 'close');
DK.app.dispose();
console.log('Settings header: dynamic version, canonical icons, live theme tint, fallback, social actions and close passed');
