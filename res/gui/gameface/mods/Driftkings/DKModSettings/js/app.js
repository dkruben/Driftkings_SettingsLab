/* DK Mod Settings window: layout, sidebar, state patches, dialog and theme. */
(function () {
    'use strict';
    var DK = window.DK, el = DK.dom.el, setClass = DK.dom.setClass;
    var ICONS = 'coui://gui/gameface/mods/Driftkings/DKModSettings/assets/icons/';
    var KNOWN_ICONS = ['puzzle', 'gear', 'globe', 'chart', 'bars', 'speaker', 'palette'];
    var ui = {}, schema = null, state = null, mods = {}, controls = {}, rendered = null;
    var query = '', activeTab = '', profileSelection = '', profileDialog = null;
    var toastTimer = null, lastMessage = 0, lastAccent = null, disposed = false, confirmFocused = false;

    function labels() { return (schema && schema.labels) || {}; }
    function categoryLabel(category) {
        category = category || 'general';
        return labels()['category.' + category] || {general: 'General', battle: 'Battle', hangar: 'Hangar', system: 'System'}[category] || category;
    }
    function send(action, data) { DK.bridge.send(action, data); }

    function build() {
        var root = document.getElementById('dk-app');
        root.textContent = '';
        var win = ui.window = el('div', 'dk-window', null, root);
        var header = el('div', 'dk-header', null, win);
        var logo = el('img', 'dk-logo', null, header);
        logo.src = ICONS + 'gear.svg';
        ui.title = el('div', 'dk-title', null, header);
        el('div', 'dk-spacer', null, header);
        ui.close = el('button', 'dk-close', '×', header);
        ui.close.type = 'button';
        ui.close.addEventListener('click', function () { send('close'); });

        var body = el('div', 'dk-body', null, win);
        var sidebarArea = el('div', 'dk-sidebar-area', null, body);
        var searchArea = el('div', 'dk-sidebar-search', null, sidebarArea);
        ui.search = el('input', 'dk-search', null, searchArea);
        ui.search.type = 'text';
        ui.search.addEventListener('input', function () { query = ui.search.value.toLowerCase(); filter(); });
        var sidebarScrollArea = el('div', 'dk-sidebar-scroll-area', null, sidebarArea);
        ui.sidebar = el('div', 'dk-sidebar', null, sidebarScrollArea);
        ui.sidebarScroll = DK.dom.scrollbar(ui.sidebar, sidebarScrollArea);
        var content = el('div', 'dk-content', null, body);
        var head = ui.modHeader = el('div', 'dk-mod-header', null, content);
        ui.installed = footerButton(head, showInstalled, 'dk-installed-button');
        ui.modName = el('div', 'dk-mod-name', null, head);
        ui.modMeta = el('div', 'dk-mod-meta', null, head);
        ui.modDescription = el('div', 'dk-mod-description', null, head);
        ui.modStatus = el('div', 'dk-mod-status', null, head);
        ui.modDependencies = el('div', 'dk-mod-dependencies', null, head);
        ui.compatibilityWarnings = el('div', 'dk-compatibility-warnings', null, head);
        ui.banner = el('div', 'dk-banner', null, head);
        ui.themeReset = footerButton(head, function () { send('reset_theme'); }, 'dk-theme-reset');
        ui.tabs = el('div', 'dk-tabs', null, content);
        var controlArea = el('div', 'dk-control-area', null, content);
        ui.controls = el('div', 'dk-controls', null, controlArea);
        ui.controlScroll = DK.dom.scrollbar(ui.controls, controlArea);

        var footer = el('div', 'dk-footer', null, win);
        ui.reset = footerButton(footer, function () { send('reset', {mod: state.selected}); });
        ui.undo = footerButton(footer, function () { send('undo'); });
        ui.profiles = footerButton(footer, showProfiles);
        el('div', 'dk-spacer', null, footer);
        ui.unsaved = el('div', 'dk-unsaved', null, footer);
        ui.cancel = footerButton(footer, function () { send('cancel'); });
        ui.apply = footerButton(footer, function () { send('apply'); });
        ui.save = footerButton(footer, function () { send('save'); }, 'is-primary');

        ui.toast = el('div', 'dk-toast', null, win);
        ui.overlay = el('div', 'dk-overlay', null, win);
        var dialog = ui.dialog = el('div', 'dk-dialog', null, ui.overlay);
        ui.dialogTitle = el('div', 'dk-dialog-title', null, dialog);
        ui.dialogText = el('div', 'dk-dialog-text', null, dialog);
        var actions = el('div', 'dk-dialog-actions', null, dialog);
        ui.confirmStay = footerButton(actions, function () { send(state.restartPrompt ? 'restart' : 'confirm', {choice: state.restartPrompt ? 'later' : 'stay'}); });
        ui.confirmDiscard = footerButton(actions, function () { send('confirm', {choice: 'discard'}); });
        ui.confirmSave = footerButton(actions, function () { send(state.restartPrompt ? 'restart' : 'confirm', {choice: state.restartPrompt ? 'now' : 'save'}); }, 'is-primary');

        DK.layer.init(el('div', 'dk-layer', null, document.body));
        document.addEventListener('keydown', onKey);
    }
    function footerButton(parent, action, extra) {
        var node = el('button', 'dk-btn' + (extra ? ' ' + extra : ''), null, parent);
        node.type = 'button';
        node.addEventListener('click', function () { if (!node.disabled) { DK.layer.close(); action(); } });
        return node;
    }
    function onKey(event) {
        if (event.keyCode !== 27) { return; }
        if (DK.modal.isOpen()) { return; }
        if (state && state.capture) { return; }
        if (profileDialog) { closeProfiles(); return; }
        if (DK.layer.close()) { return; }
        if (state && state.restartPrompt) { send('restart', {choice: 'later'}); }
        else if (state && state.confirm) { send('confirm', {choice: 'stay'}); } else { send('close'); }
    }

    function icon(parent, mod) {
        var name = KNOWN_ICONS.indexOf(mod.icon) >= 0 ? mod.icon : 'puzzle';
        var image = el('img', 'dk-nav-icon', null, parent);
        image.src = ICONS + name + '.svg';
    }

    function onSchema(next) {
        schema = next; mods = {}; rendered = null;
        var text = labels();
        ui.installed.textContent = text.installed; ui.themeReset.textContent = text.resetTheme;
        ui.search.placeholder = text.search; ui.undo.textContent = text.undo; ui.profiles.textContent = text.profiles;
        ui.title.textContent = text.title || 'DK MOD SETTINGS';
        ui.unsaved.textContent = '● ' + (text.unsaved || '');
        ui.close.title = text.close || '';
        ui.reset.textContent = text.reset; ui.cancel.textContent = text.cancel;
        ui.apply.textContent = text.apply; ui.save.textContent = text.saveApply;
        ui.dialogTitle.textContent = text.confirmTitle; ui.dialogText.textContent = text.confirmText;
        ui.confirmStay.textContent = text.confirmStay; ui.confirmDiscard.textContent = text.confirmDiscard;
        ui.confirmSave.textContent = text.confirmSave;
        ui.sidebar.textContent = '';
        ui.nav = {}; ui.navStatus = {}; ui.groups = [];
        var grouped = {}, categoryOrder = ['general', 'battle', 'hangar', 'system'];
        schema.mods.forEach(function (mod) {
            var category = mod.category || 'general';
            var key = '$' + category;
            if (!grouped[key]) { grouped[key] = []; }
            grouped[key].push(mod);
            if (categoryOrder.indexOf(category) < 0) { categoryOrder.push(category); }
        });
        categoryOrder.forEach(function (category) {
            var items = grouped['$' + category];
            if (!items) { return; }
            var group = el('div', 'dk-nav-group', null, ui.sidebar);
            el('div', 'dk-nav-category', categoryLabel(category), group);
            ui.groups.push({node: group, ids: items.map(function (mod) { return mod.id; })});
            items.forEach(function (mod) {
            mods[mod.id] = mod;
            var item = el('button', 'dk-nav-item', null, group);
            item.type = 'button';
            icon(item, mod);
            var details = el('div', 'dk-nav-details', null, item);
            el('div', 'dk-nav-name', mod.name, details);
            ui.navStatus[mod.id] = el('div', 'dk-nav-status', null, details);
            el('div', 'dk-nav-dot', null, item);
            item.addEventListener('click', function () {
                if (!state || state.selected !== mod.id) { send('select', {mod: mod.id}); }
            });
            ui.nav[mod.id] = item;
            });
        });
        if (state) { onState(state); }
        filter();
    }

    function renderMod(modId) {
        DK.layer.cancelDrags(); DK.layer.close(); DK.layer.hideTip();
        Object.keys(controls).forEach(function (key) { if (controls[key].dispose) { controls[key].dispose(); } });
        controls = {}; rendered = modId; activeTab = '';
        ui.tabs.textContent = '';
        ui.controls.textContent = '';
        ui.updates = null;
        var mod = mods[modId], text = labels();
        ui.themeReset.style.display = modId === 'dk.settings' ? 'block' : 'none';
        if (!mod) {
            ui.modName.textContent = ''; ui.modMeta.textContent = ''; ui.modDescription.textContent = '';
            ui.modDependencies.textContent = '';
            el('div', 'dk-empty', text.noMods, ui.controls);
            return;
        }
        ui.modName.textContent = mod.name;
        var meta = mod.category ? [categoryLabel(mod.category)] : [];
        if (mod.version) { meta.push((modId === 'dk.settings' ? 'DriftKings' : (text.version || 'Version')) + ' ' + mod.version); }
        if (mod.author) { meta.push((text.author || 'Author') + ' ' + mod.author); }
        ui.modMeta.textContent = meta.join('   •   ');
        ui.modDescription.textContent = mod.description || '';
        if (mod.soundBank) { ui.modDescription.textContent += ' • ' + text['sound.bank'] + ': ' + mod.soundBank; }
        (mod.dependencies || []).forEach(function (dependency) { if (!dependency.installed) { ui.modDescription.textContent += ' • ' + text.dependencyMissing + ': ' + dependency.id; } });
        ui.modDependencies.textContent = (mod.dependencies || []).map(function (dependency) {
            return (dependency.installed ? '✓ ' + (text['status.available'] || 'Component available') : '! ' + (text.dependencyMissing || 'Missing dependency')) + ': ' + dependency.id;
        }).join(' • ');
        if (!mod.controls.length) { el('div', 'dk-empty', text.noControls, ui.controls); }
        var context = {
            labels: text,
            preview: function (key, value) { if (modId === 'dk.settings') { state.theme[key] = value; theme(state.theme); layout(); } },
            commit: function (key, value, alpha) { var payload = {mod: modId, key: key, value: value}; if (alpha !== undefined) { payload.alpha = alpha; } send('set', payload); },
            capture: function (key) { send('capture', {mod: modId, key: key}); },
            action: function (key) { send('button', {mod: modId, key: key}); }
        };
        var columns = null, tabs = [];
        mod.controls.forEach(function (def) {
            var control = DK.controls.create(def, context);
            if (def.column >= 0) {
                if (!columns) {
                    var columnBox = el('div', 'dk-columns', null, ui.controls);
                    columns = [el('div', 'dk-column', null, columnBox), el('div', 'dk-column', null, columnBox)];
                }
                columns[def.column === 1 ? 1 : 0].appendChild(control.node);
            } else {
                ui.controls.appendChild(control.node);
                columns = null;
            }
            control.definition = def;
            if (def.tab && tabs.indexOf(def.tab) < 0) { tabs.push(def.tab); }
            controls[def.id] = control;
        });
        if (modId === 'dk.settings') {
            var updates = ui.updates = el('div', 'dk-updates', null, ui.controls);
            el('div', 'dk-section', text['updates.title'], updates);
            ui.updateInstalled = el('div', 'dk-update-line', null, updates);
            ui.updateChannel = el('div', 'dk-update-line', null, updates);
            ui.updateLastCheck = el('div', 'dk-update-line', null, updates);
            ui.updateStatus = el('div', 'dk-update-line', null, updates);
            ui.updateBlocked = el('div', 'dk-update-blocked', null, updates);
            ui.updateOutcome = el('div', 'dk-update-result', null, updates);
            ui.updateLatest = el('div', 'dk-update-line', null, updates);
            ui.updateChanges = el('div', 'dk-update-changelog', null, updates);
            ui.updateCheck = footerButton(updates, function () { send('check_updates'); });
            ui.updateCheck.textContent = text['updates.check'];
            ui.updateDownload = footerButton(updates, function () { send('download_update'); });
            ui.updateDownload.className += ' dk-update-download';
            ui.updateDownload.textContent = text['updates.install'];
            ui.updateCancel = footerButton(updates, function () { send('cancel_update_download'); });
            ui.updateCancel.textContent = text['updates.cancelDownload'];
            ui.updateInstall = footerButton(updates, function () { send('schedule_update'); });
            ui.updateInstall.className += ' dk-update-install';
            ui.updateInstall.textContent = text['updates.install'];
            ui.updateRestart = footerButton(updates, function () { send('restart_update'); });
            ui.updateRestart.className += ' dk-update-restart';
            ui.updateRestart.textContent = text.restartNow;
            ui.updateLater = footerButton(updates, function () { send('defer_update'); });
            ui.updateLater.textContent = text['updates.later'];
            ui.updateCancelInstall = footerButton(updates, function () { send('cancel_update_install'); });
            ui.updateCancelInstall.textContent = text['updates.cancelInstall'];
        }
        if (tabs.length) {
            [text.all].concat(tabs).forEach(function (name, index) { footerButton(ui.tabs, function () { activeTab = index ? name : ''; filter(); }).textContent = name; });
        }
        filter();
        ui.controls.scrollTop = 0;
    }

    function contains(list, key) { return !!list && list.indexOf(key) >= 0; }

    function statusText(id) {
        var text = labels(), mod = mods[id], current = (state.status || {})[id] || {}, parts = [];
        if (current.status === 'configError') { parts.push('! ' + (text.statusConfigError || 'Configuration error')); }
        else if (current.status === 'error') { parts.push('! ' + (text.statusError || 'Error')); }
        else if (current.status && current.status !== 'active') { parts.push('! ' + (text['status.unavailable'] || 'Unavailable')); }
        else if (current.status === 'active' || current.enabled !== undefined) {
            parts.push(current.enabled === false ? (text['status.disabled'] || text.off || 'Off') : '✓ ' + (text['status.enabled'] || text.on || 'Active'));
        } else { parts.push(text['status.unknown'] || 'Status unavailable'); }
        (mod.dependencies || []).forEach(function (dependency) {
            if (!dependency.installed) { parts.push('! ' + (text.dependencyMissing || 'Missing dependency') + ': ' + dependency.id); }
        });
        if (current.restartRequired || contains(state.restartRequired, id)) { parts.push('↻ ' + (text['status.restart'] || 'Restart required')); }
        return parts.join(' • ');
    }

    function onState(next) {
        state = next;
        if (!schema) { return; }
        theme(state.theme || {});
        layout();
        if (rendered !== state.selected) { renderMod(state.selected); }
        var modId = state.selected, values = state.values[modId] || {};
        if (ui.updates) {
            var update = state.updater, strings = labels();
            ui.updates.style.display = update ? '' : 'none';
            if (update) {
                ui.updateInstalled.textContent = strings['updates.installed'] + ': ' + update.installedVersion;
                ui.updateChannel.textContent = strings['updates.channel'] + ': ' + update.channel;
                ui.updateLastCheck.textContent = strings['updates.lastCheck'] + ': ' + (update.lastCheck === null ? strings['updates.never'] : new Date(update.lastCheck * 1000).toLocaleString());
                ui.updateStatus.textContent = strings['updates.' + update.status] || update.status;
                if (update.status === 'IDLE' && update.lastCheck === null) { ui.updateStatus.textContent = strings['updates.notChecked']; }
                if (update.error === 'transportUnavailable') { ui.updateStatus.textContent = strings['updates.transportUnavailable']; }
                if (update.latestVersion && update.compatible === false) { ui.updateStatus.textContent += ' ' + strings['updates.incompatible']; }
                ui.updateLatest.textContent = update.latestVersion ? strings['updates.latest'] + ': ' + update.latestVersion : '';
                ui.updateChanges.textContent = (update.changelog || []).join('\n');
                var busy = ['CHECKING', 'DOWNLOADING', 'VERIFYING', 'INSTALLING', 'RESTART_REQUIRED'].indexOf(update.status) >= 0;
                ui.updateCheck.disabled = busy || update.status === 'READY' || !!update.cancellingInstall;
                var downloadable = update.canDownload && update.compatible === true && ['AVAILABLE', 'ERROR'].indexOf(update.status) >= 0;
                ui.updateDownload.style.display = downloadable ? '' : 'none';
                ui.updateDownload.disabled = !downloadable;
                ui.updateCancel.style.display = update.canCancel ? '' : 'none';
                ui.updateCancel.disabled = !update.canCancel;
                var installable = update.canInstall && update.compatible === true && ['READY', 'ERROR'].indexOf(update.status) >= 0 && !update.cancellingInstall;
                ui.updateInstall.style.display = installable ? '' : 'none';
                ui.updateInstall.disabled = !installable;
                var prepared = update.status === 'RESTART_REQUIRED' && update.installScheduled === true && !update.cancellingInstall;
                ui.updateRestart.style.display = prepared ? '' : 'none';
                ui.updateRestart.disabled = !prepared || !update.canRestart || !!state.unsaved;
                ui.updateLater.style.display = prepared && !update.restartDeferred ? '' : 'none';
                ui.updateLater.disabled = !prepared;
                ui.updateCancelInstall.style.display = update.status === 'INSTALLING' || update.installScheduled || update.cancellingInstall ? '' : 'none';
                ui.updateCancelInstall.disabled = !!update.cancellingInstall;
                ui.updateBlocked.textContent = update.installBlocked ? (strings['updates.block.' + update.installBlocked] || strings['updates.installBlocked']) : '';
                if (prepared) { ui.updateBlocked.textContent += ' ' + strings['updates.wgcLimit']; }
                if (update.cancellingInstall) { ui.updateStatus.textContent = strings['updates.cancelling']; }
                var outcome = update.lastInstallResult;
                ui.updateOutcome.textContent = outcome ? (strings['updates.result.' + outcome.status] || strings['updates.result.failed']).replace('{version}', outcome.version || '') : '';
                if (update.status === 'DOWNLOADING' && typeof update.downloadPercent === 'number') {
                    ui.updateStatus.textContent += ' ' + update.downloadPercent + '%';
                }
            }
        }
        var changed = state.changed[modId] || [], disabled = state.disabled[modId] || [];
        var updaterBusy = state.updater && ['CHECKING', 'DOWNLOADING', 'VERIFYING', 'INSTALLING'].indexOf(state.updater.status) >= 0;
        var secrets = state.secrets[modId] || [];
        Object.keys(controls).forEach(function (key) {
            var control = controls[key];
            control.info({disabled: contains(disabled, key) || !!(updaterBusy && modId === 'dk.settings' && key === 'updateChannel'), changed: contains(changed, key),
                          values: state.values[modId], secretSet: contains(secrets, key), keyNames: state.keyNames || {}, capture: state.capture && state.capture.mod === modId && state.capture.key === key});
            if (Object.prototype.hasOwnProperty.call(values, key)) { control.update(values[key]); }
            if (control.previewUpdate) { control.previewUpdate((state.previews || {})[key] || ''); }
        });
        Object.keys(ui.nav).forEach(function (id) {
            var item = ui.nav[id];
            setClass(item, 'is-selected', id === modId);
            setClass(item, 'is-changed', (state.changed[id] || []).length > 0);
            var current = (state.status || {})[id] || {};
            var missing = (mods[id].dependencies || []).some(function (dependency) { return !dependency.installed; });
            setClass(item, 'is-error', !!current.status && current.status !== 'active');
            setClass(item, 'is-off', current.enabled === false);
            setClass(item, 'is-warning', missing || !!current.restartRequired || contains(state.restartRequired, id));
            ui.navStatus[id].textContent = statusText(id);
            item.title = mods[id].name + ' — ' + statusText(id);
        });
        ui.modStatus.textContent = mods[modId] ? statusText(modId) : '';
        var warnings = (state.compatibilityWarnings || {})[modId] || [];
        ui.compatibilityWarnings.textContent = warnings.map(function (warning) { return '⚠ ' + warning.text; }).join('\n');
        ui.compatibilityWarnings.style.display = warnings.length ? '' : 'none';
        var status = state.status[modId] && state.status[modId].status, text = labels();
        ui.banner.textContent = status === 'configError' ? text.statusConfigError : status === 'error' ? text.statusError : '';
        setClass(ui.banner, 'is-visible', status === 'configError' || status === 'error');
        var mod = mods[modId];
        var hasValues = !!mod && mod.controls.some(function (def) { return 'default' in def; });
        ui.reset.disabled = !hasValues;
        ui.cancel.disabled = !state.pending;
        ui.apply.disabled = !state.pending;
        ui.save.disabled = false;
        ui.undo.disabled = !state.canUndo;
        [ui.reset, ui.cancel, ui.apply, ui.save, ui.undo].forEach(function (node) { setClass(node, 'is-disabled', node.disabled); });
        if (profileDialog && profileDialog.area && profileDialog.exported !== state.profileText) { profileDialog.area.value = state.profileText || ''; profileDialog.exported = state.profileText; }
        setClass(ui.unsaved, 'is-visible', !!state.unsaved || !!state.pending);
        ui.dialogTitle.textContent = state.restartPrompt ? text.restartTitle : text.confirmTitle;
        ui.dialogText.textContent = state.restartPrompt ? (state.restartReason === 'updater' ? text['updates.restartText'] : text.restartText) : text.confirmText;
        ui.confirmStay.textContent = state.restartPrompt ? text.restartLater : text.confirmStay;
        ui.confirmSave.textContent = state.restartPrompt ? text.restartNow : text.confirmSave;
        ui.confirmDiscard.style.display = state.restartPrompt ? 'none' : '';
        ui.confirmSave.disabled = !!(state.restartPrompt && (state.inBattle || state.unsaved ||
            state.restartReason === 'updater' && (!state.updater || !state.updater.canRestart)));
        ui.profiles.disabled = !!state.inBattle;
        var showDialog = !!(state.confirm || state.restartPrompt);
        setClass(ui.overlay, 'is-visible', showDialog);
        if (showDialog && !confirmFocused) {
            closeProfiles(); DK.layer.close();
            DK.modal.bind(ui.dialog, {cancel: function () { send(state.restartPrompt ? 'restart' : 'confirm', {choice: state.restartPrompt ? 'later' : 'stay'}); }});
        } else if (!showDialog && confirmFocused) { DK.modal.close(null); }
        confirmFocused = showDialog;
        toast(state.message);
        filter();
    }

    function toast(message) {
        if (!message || message.id === lastMessage) { return; }
        lastMessage = message.id;
        ui.toast.textContent = message.text;
        setClass(ui.toast, 'is-error', message.kind === 'error');
        setClass(ui.toast, 'is-visible', true);
        if (toastTimer !== null) { clearTimeout(toastTimer); }
        toastTimer = setTimeout(function () { toastTimer = null; setClass(ui.toast, 'is-visible', false); }, 3000);
    }

    /* Panel size in UI units: large on big screens, never larger than the client area. */
    function layout() {
        if (disposed) { return; }
        var customScale = state && state.theme ? (state.theme.uiScale || 100) / 100 : 1;
        document.documentElement.style.fontSize = (DK.bridge.scale() * customScale) + 'px';
        var actual = DK.bridge.clientSizeRem(), client = {width: actual.width / customScale, height: actual.height / customScale};
        setClass(ui.window, 'is-narrow', client.width < 1050);
        var width = Math.min(client.width - 20, Math.max(760, Math.min(1280, client.width - 160)));
        var height = Math.min(client.height - 20, Math.max(480, Math.min(840, client.height - 160)));
        ui.window.style.width = Math.round(width) + 'rem';
        ui.window.style.height = Math.round(height) + 'rem';
        setTimeout(function () { if (!disposed) { ui.sidebarScroll(); ui.controlScroll(); } }, 0);
    }

    function shade(hex, amount) {
        var value = parseInt(hex.slice(1), 16), channels = [(value >> 16) & 255, (value >> 8) & 255, value & 255];
        return 'rgb(' + channels.map(function (channel) {
            return Math.round(amount >= 0 ? channel + (255 - channel) * amount : channel * (1 + amount));
        }).join(',') + ')';
    }
    function themeCss(accent) {
        var light = shade(accent, 0.25), dark = shade(accent, -0.35);
        return [
            '.dk-nav-item.is-selected{border-left-color:' + accent + '}',
            '.dk-nav-badge,.dk-nav-dot,.dk-row.is-changed:before,.dk-slider-fill{background:' + accent + '}',
            '.dk-unsaved,.dk-section,.dk-option.is-selected{color:' + accent + '}',
            '.dk-btn.is-primary{background:' + accent + ';border-color:' + light + '}',
            '.dk-btn.is-primary:hover{background:' + light + ';color:#000}',
            '.dk-switch.is-on .dk-switch-track{background:' + dark + ';border-color:' + accent + '}',
            '.dk-switch.is-on .dk-switch-text{color:' + accent + '}',
            '.dk-checkbox.is-on{background:' + accent + ';border-color:' + light + '}',
            '.dk-text:focus,.dk-dropdown:focus{border-color:' + accent + '}',
            '.dk-slider-thumb{border-color:' + dark + '}',
            '.dk-window{border-color:' + shade(accent, -0.6) + '}'
        ].join('\n');
    }
    function theme(values) {
        var signature = JSON.stringify(values);
        if (signature === lastAccent) { return; }
        lastAccent = signature;
        var accent = DK.controls.normalizeHex(values.accent) || '#D98219';
        var bg = DK.controls.normalizeHex(values.background) || '#101113';
        var n = parseInt(bg.slice(1), 16);
        var rgba = 'rgba(' + [(n >> 16) & 255, (n >> 8) & 255, n & 255, (values.opacity || 96) / 100].join(',') + ')';
        var css = '.dk-label,.dk-text,.dk-dropdown{font-size:' + (values.fontSize || 15) + 'rem}' + themeCss(accent) + '.dk-window{background:' + rgba + ';color:' + (values.textColor || '#E8E4DA') + ';font-size:' + (values.fontSize || 15) + 'rem}';
        css += '.dk-section{font-size:' + (values.sectionFontSize || 18) + 'rem}.dk-sidebar{background:rgba(0,0,0,' + (Number(values.sidebarOpacity === undefined ? 35 : values.sidebarOpacity) / 100) + ')}';
        css += '.dk-label,.dk-text{color:' + (values.textColor || '#E8E4DA') + '}.dk-mod-description,.dk-mod-meta{color:' + (values.secondary || '#B3AE9F') + '}.dk-window{border-color:' + (values.border || '#4A463E') + '}.dk-nav-item:hover{background:' + (values.hover || '#39352B') + '}';
        document.getElementById('dk-theme').textContent = css;
    }

    function matches(def) {
        return !query || [def.name, def.label, def.category, def.category !== undefined || def.name !== undefined ? categoryLabel(def.category) : '', def.description, (def.keywords || []).join(' ')].join(' ').toLowerCase().indexOf(query) >= 0;
    }
    function filter() {
        Object.keys(ui.nav || {}).forEach(function (id) {
            var mod = mods[id];
            ui.nav[id].style.display = matches(mod) || mod.controls.some(matches) ? 'flex' : 'none';
        });
        Object.keys(controls).forEach(function (key) {
            var control = controls[key], def = control.definition;
            var visible = (!activeTab || !def.tab || def.tab === activeTab) && (matches(mods[rendered]) || matches(def));
            control.node.style.display = visible ? '' : 'none';
        });
        if (ui.updates) {
            var updateTitle = labels()['updates.title'] || '';
            ui.updates.style.display = state && state.updater && (!activeTab || activeTab === updateTitle) &&
                (!query || updateTitle.toLowerCase().indexOf(query) >= 0 || matches(mods[rendered])) ? '' : 'none';
        }
        (ui.groups || []).forEach(function (group) {
            group.node.style.display = group.ids.some(function (id) { return ui.nav[id].style.display !== 'none'; }) ? '' : 'none';
        });
        setTimeout(function () { if (!disposed) { ui.sidebarScroll(); ui.controlScroll(); } }, 0);
    }
    function closeProfiles() {
        if (profileDialog) { DK.modal.close(null); if (profileDialog.root.parentNode) { profileDialog.root.parentNode.removeChild(profileDialog.root); } profileDialog = null; }
    }
    function showInstalled() {
        closeProfiles();
        var text = labels(), root = el('div', 'dk-overlay is-visible', null, ui.window);
        var panel = el('div', 'dk-dialog dk-profile-dialog', null, root);
        el('div', 'dk-dialog-title', text.installed, panel);
        schema.mods.forEach(function (mod) {
            var row = el('div', 'dk-installed-row', null, panel), status = state.status[mod.id] || {};
            el('div', 'dk-nav-name', mod.name, row);
            el('div', 'dk-mod-meta', [mod.version, mod.author, status.enabled === false ? text.off : text.on].filter(Boolean).join(' • '), row);
            (mod.dependencies || []).forEach(function (dependency) { if (!dependency.installed) { el('div', 'dk-error', text.dependencyMissing + ': ' + dependency.id, row); } });
        });
        if (state.diagnostics) { var debug = el('textarea', 'dk-text dk-profile-json', null, panel); debug.readOnly = true; debug.value = JSON.stringify(state.diagnostics, null, 2); }
        footerButton(panel, closeProfiles).textContent = text.close;
        profileDialog = {root: root};
        DK.modal.bind(panel, {cancel: closeProfiles});
    }
    function showProfiles() {
        if (profileDialog) { closeProfiles(); return; }
        var text = labels(), root = el('div', 'dk-overlay is-visible', null, ui.window);
        var panel = el('div', 'dk-dialog dk-profile-dialog', null, root);
        el('div', 'dk-dialog-title', text.profiles, panel);
        el('div', 'dk-dialog-text', text.profileHelp, panel);
        var selector = DK.controls.create({id: 'profile', type: 'dropdown', label: text.profiles, options: (state.profiles || []).map(function (name) { return {value: name, label: name}; })}, {
            labels: text, commit: function (key, value) { profileSelection = value; name.value = value; }
        });
        panel.appendChild(selector.node);
        profileSelection = (state.profiles || [])[0] || ''; selector.update(profileSelection);
        var name = el('input', 'dk-text', null, panel); name.type = 'text'; name.placeholder = text.profileName; name.value = profileSelection;
        var actions = el('div', 'dk-profile-actions', null, panel);
        function action(operation, extra) { var data = extra || {}; data.operation = operation; send('profile', data); }
        footerButton(actions, function () { action('create', {name: name.value}); }).textContent = text.profileCreate;
        footerButton(actions, function () { action('load', {name: profileSelection}); closeProfiles(); }).textContent = text.profileLoad;
        footerButton(actions, function () { action('rename', {name: profileSelection, target: name.value}); closeProfiles(); }).textContent = text.profileRename;
        var deleting = false, del = footerButton(actions, function () { if (!deleting) { deleting = true; del.textContent = text.confirmDelete; } else { action('delete', {name: profileSelection}); closeProfiles(); } }); del.textContent = text.profileDelete;
        var area = el('textarea', 'dk-text dk-profile-json', null, panel); area.maxLength = 2000000;
        profileDialog = {root: root, area: area, exported: ''};
        var bottom = el('div', 'dk-profile-actions', null, panel);
        footerButton(bottom, function () { action('export'); }).textContent = text.profileExport;
        footerButton(bottom, function () { action('import', {text: area.value}); }).textContent = text.profileImport;
        footerButton(bottom, closeProfiles).textContent = text.close;
        DK.modal.bind(panel, {cancel: closeProfiles});
    }

    function dispose() {
        if (disposed) { return; }
        disposed = true;
        if (toastTimer !== null) { clearTimeout(toastTimer); }
        document.removeEventListener('keydown', onKey);
        window.removeEventListener('resize', layout);
        window.removeEventListener('unload', dispose);
        Object.keys(controls).forEach(function (key) { if (controls[key].dispose) { controls[key].dispose(); } });
        closeProfiles(); DK.modal.close(null); DK.layer.close(); DK.layer.hideTip();
        DK.bridge.dispose();
    }

    build();
    layout();
    window.addEventListener('resize', layout);
    window.addEventListener('unload', dispose);
    DK.bridge.start({schema: onSchema, state: onState, layout: layout});
    DK.app = {dispose: dispose, themeCss: themeCss};
}());
