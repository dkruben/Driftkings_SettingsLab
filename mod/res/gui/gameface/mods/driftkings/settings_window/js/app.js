/* Driftkings Mod Settings window: layout, sidebar, mod page, state patches and confirmation dialog. */
(function () {
    'use strict';
    var DK = window.DK, el = DK.dom.el, setClass = DK.dom.setClass;
    var ICONS = 'coui://gui/gameface/mods/driftkings/settings_window/assets/icons/';
    var KNOWN_ICONS = ['puzzle', 'gear', 'globe', 'chart', 'bars', 'speaker', 'palette'];
    var ui = {}, schema = null, state = null, mods = {}, controls = {}, rendered = null;
    var query = '', activeTab = '';
    var toastTimer = null, lastMessage = 0, disposed = false, confirmFocused = false;
    var lastLayout = null, lastFilter = null, scrollbarTimer = null;

    function labels() { return (schema && schema.labels) || {}; }
    function label(key, fallback) {
        var value = labels()[key];
        return value === undefined || value === null ? fallback : value;
    }
    function categoryLabel(category) {
        category = category || 'general';
        return label('category.' + category, {general: 'General', battle: 'Battle', hangar: 'Hangar', system: 'System'}[category] || category);
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
        el('span', 'dk-alert-icon', null, ui.banner);
        ui.bannerText = el('span', '', null, ui.banner);
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

        ui.toast = el('button', 'dk-toast', null, win);
        ui.toast.type = 'button';
        ui.toast.addEventListener('click', showNotice);
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
        if (DK.profileDialogs.isOpen()) { closeProfiles(); return; }
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
        lastFilter = null;
        schema = next; mods = {}; rendered = null;
        var text = labels();
        ui.installed.textContent = text.installed; ui.themeReset.textContent = text.resetTheme;
        ui.search.placeholder = text.search; ui.undo.textContent = text.undo; ui.profiles.textContent = text.profiles;
        ui.title.textContent = label('title', 'DK MOD SETTINGS');
        ui.unsaved.textContent = '● ' + (text.unsaved || '');
        ui.close.title = text.close || '';
        ui.reset.textContent = text.reset; ui.cancel.textContent = text.cancel;
        ui.apply.textContent = text.apply; ui.save.textContent = text.saveApply;
        ui.apply.title = text.applyHint || '';
        ui.save.title = text.saveApplyHint || '';
        ui.cancel.title = text.cancelHint || '';
        ui.undo.title = text.undoHint || '';
        ui.reset.title = text.resetHint || '';
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
        lastFilter = null;
        if (ui.markerEditor) { ui.markerEditor.dispose(); ui.markerEditor = null; }
        DK.layer.cancelDrags(); DK.layer.close(); DK.layer.hideTip();
        Object.keys(controls).forEach(function (key) { if (controls[key].dispose) { controls[key].dispose(); } });
        controls = {}; rendered = modId; activeTab = '';
        ui.tabs.textContent = '';
        ui.controls.textContent = '';
        ui.updates = ui.updater = null;
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
        if (mod.version) { meta.push((modId === 'dk.settings' ? 'DriftKings' : label('version', 'Version')) + ' ' + mod.version); }
        if (mod.author) { meta.push(label('author', 'Author') + ' ' + mod.author); }
        ui.modMeta.textContent = meta.join('   •   ');
        ui.modDescription.textContent = mod.description || '';
        if (mod.soundBank) { ui.modDescription.textContent += ' • ' + text['sound.bank'] + ': ' + mod.soundBank; }
        (mod.dependencies || []).forEach(function (dependency) { if (!dependency.installed) { ui.modDescription.textContent += ' • ' + text.dependencyMissing + ': ' + dependency.id; } });
        ui.modDependencies.textContent = (mod.dependencies || []).map(function (dependency) {
            return (dependency.installed ? '✓ ' + label('status.available', 'Component available') : '! ' + label('dependencyMissing', 'Missing dependency')) + ': ' + dependency.id;
        }).join(' • ');
        if (!mod.controls.length) { el('div', 'dk-empty', text.noControls, ui.controls); }
        var context = {
            labels: text,
            preview: function (key, value) { if (modId === 'dk.settings') { state.theme[key] = value; theme(state.theme); layout(); } },
            commit: function (key, value, alpha) { var payload = {mod: modId, key: key, value: value}; if (alpha !== undefined) { payload.alpha = alpha; } send('set', payload); },
            capture: function (key) { send('capture', {mod: modId, key: key}); },
            action: function (key) { send('button', {mod: modId, key: key}); }
        };
        if (mod.preview && mod.preview.kind === 'vehicleMarkers' && DK.vehicleMarkersEditor) {
            ui.markerEditor = DK.vehicleMarkersEditor.create(ui.controls, mod, context);
            filter(); ui.controls.scrollTop = 0;
            return;
        }
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
            var community = el('div', 'dk-section', null, ui.controls);
            var discord = footerButton(community, function () { send('open_discord'); });
            discord.textContent = 'Discord';
            discord.title = 'https://discord.gg/GJcy4x7SP';
            ui.updater = DK.updaterPanel.build(ui.controls, text, footerButton, send);
            ui.updates = ui.updater.root;
        }
        if (tabs.length) {
            [text.all].concat(tabs).forEach(function (name, index) { footerButton(ui.tabs, function () { activeTab = index ? name : ''; filter(); }).textContent = name; });
        }
        filter();
        ui.controls.scrollTop = 0;
    }

    function contains(list, key) { return !!list && list.indexOf(key) >= 0; }

    function statusParts(id) {
        var mod = mods[id], current = (state.status || {})[id] || {}, parts = [];
        if (current.status === 'configError') { parts.push(label('statusConfigError', 'Configuration error')); }
        else if (current.status === 'error') { parts.push(label('statusError', 'Error')); }
        else if (current.status && current.status !== 'active') { parts.push(label('status.unavailable', 'Unavailable')); }
        else if (current.status === 'active' || current.enabled !== undefined) {
            parts.push(current.enabled === false ? label('status.disabled', label('off', 'Off')) : '✓ ' + label('status.enabled', label('on', 'Active')));
        } else { parts.push(label('status.unknown', 'Status unavailable')); }
        (mod.dependencies || []).forEach(function (dependency) {
            if (!dependency.installed) { parts.push(label('dependencyMissing', 'Missing dependency') + ': ' + dependency.id); }
        });
        if (restartRequired(id)) { parts.push(label('status.restart', 'Restart required')); }
        return parts;
    }

    function restartRequired(id) {
        return !!((state.status || {})[id] || {}).restartRequired || contains(state.restartRequired, id);
    }
    function missingDependency(id) {
        return (mods[id].dependencies || []).some(function (dependency) { return !dependency.installed; });
    }
    // The alert icon marks errors, missing dependencies and pending restarts.
    function needsAttention(id) {
        var current = (state.status || {})[id] || {};
        return (!!current.status && current.status !== 'active') || missingDependency(id) || restartRequired(id);
    }
    function alertText(parent, text) {
        var row = el('div', '', null, parent);
        el('span', 'dk-alert-icon', null, row);
        el('span', '', text, row);
    }

    function statusText(id) { return statusParts(id).join(' • '); }
    function renderStatus(node, id) {
        if (!node.stateText) {
            node.textContent = '';
            node.alertIcon = el('span', 'dk-alert-icon', null, node);
            node.stateText = el('span', '', null, node);
            node.stateDetails = el('span', '', null, node);
        }
        setClass(node.alertIcon, 'is-hidden', !mods[id] || !needsAttention(id));
        if (!mods[id]) { node.stateText.textContent = ''; node.stateDetails.textContent = ''; return; }
        var current = (state.status || {})[id] || {}, parts = statusParts(id);
        var error = !!current.status && current.status !== 'active';
        node.stateText.className = 'dk-status-state' + (error ? ' is-error' : current.enabled === false ? ' is-off' :
            current.status === 'active' || current.enabled === true ? ' is-on' : '');
        node.stateText.textContent = parts[0];
        node.stateDetails.textContent = parts.length > 1 ? ' • ' + parts.slice(1).join(' • ') : '';
    }

    function onState(next) {
        state = next;
        if (!schema) { return; }
        theme(state.theme || {});
        layout();
        if (rendered !== state.selected) { renderMod(state.selected); }
        var modId = state.selected, values = state.values[modId] || {};
        if (ui.updater && state.updater) { DK.updaterPanel.render(ui.updater, state.updater, labels(), state.unsaved); }
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
        if (ui.markerEditor) { ui.markerEditor.update(values); }
        Object.keys(ui.nav).forEach(function (id) {
            var item = ui.nav[id];
            setClass(item, 'is-selected', id === modId);
            setClass(item, 'is-changed', (state.changed[id] || []).length > 0);
            var current = (state.status || {})[id] || {};
            setClass(item, 'is-error', !!current.status && current.status !== 'active');
            setClass(item, 'is-off', current.enabled === false);
            setClass(item, 'is-warning', missingDependency(id) || restartRequired(id));
            renderStatus(ui.navStatus[id], id);
            item.title = mods[id].name + ' — ' + statusText(id);
        });
        renderStatus(ui.modStatus, modId);
        var warnings = (state.compatibilityWarnings || {})[modId] || [];
        while (ui.compatibilityWarnings.firstChild) { ui.compatibilityWarnings.removeChild(ui.compatibilityWarnings.firstChild); }
        warnings.forEach(function (warning) { alertText(ui.compatibilityWarnings, warning.text); });
        ui.compatibilityWarnings.style.display = warnings.length ? '' : 'none';
        var status = state.status[modId] && state.status[modId].status, text = labels();
        ui.bannerText.textContent = status === 'configError' ? text.statusConfigError : status === 'error' ? text.statusError : '';
        setClass(ui.banner, 'is-visible', status === 'configError' || status === 'error');
        var mod = mods[modId];
        var hasValues = !!mod && mod.controls.some(function (def) { return 'default' in def; });
        ui.reset.disabled = !hasValues;
        ui.cancel.disabled = !state.pending;
        ui.apply.disabled = !state.pending;
        ui.save.disabled = false;
        ui.undo.disabled = !state.canUndo;
        [ui.reset, ui.cancel, ui.apply, ui.save, ui.undo].forEach(function (node) { setClass(node, 'is-disabled', node.disabled); });
        DK.profileDialogs.showExport(state.profileText);
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
        scheduleScrollbars();
    }

    function showNotice() {
        if (!ui.toast.textContent || DK.modal.isOpen()) { return; }
        var panel = el('div', 'dk-notice-dialog');
        el('div', 'dk-notice-text', ui.toast.textContent, panel);
        var actions = el('div', 'dk-notice-actions', null, panel);
        footerButton(actions, function () { DK.modal.close(false); }).textContent = label('close', 'Close');
        // The toast may expire while reading; return focus to a stable control.
        DK.modal.open(panel, {origin: ui.close});
    }

    function toast(message) {
        if (!message || message.id === lastMessage) { return; }
        lastMessage = message.id;
        ui.toast.textContent = message.text;
        ui.toast.title = message.text;
        setClass(ui.toast, 'is-error', message.kind === 'error');
        setClass(ui.toast, 'is-visible', true);
        setClass(ui.window, 'has-toast', true);
        if (toastTimer !== null) { clearTimeout(toastTimer); }
        toastTimer = setTimeout(function () {
            toastTimer = null;
            setClass(ui.toast, 'is-visible', false);
            setClass(ui.window, 'has-toast', false);
        }, 3000);
    }

    /* Panel size in UI units: large on big screens, never larger than the client area. */
    function scheduleScrollbars() {
        if (disposed || scrollbarTimer !== null) { return; }
        scrollbarTimer = setTimeout(function () {
            scrollbarTimer = null;
            if (!disposed) { ui.sidebarScroll(); ui.controlScroll(); }
        }, 0);
    }
    function layout() {
        if (disposed) { return; }
        var customScale = state && state.theme ? (state.theme.uiScale || 100) / 100 : 1;
        var unit = DK.bridge.scale();
        var actual = DK.bridge.clientSizeRem(), client = {width: actual.width / customScale, height: actual.height / customScale};
        var signature = [actual.width, actual.height, unit, customScale].join('|');
        if (signature === lastLayout) { return; }
        lastLayout = signature;
        document.documentElement.style.fontSize = (unit * customScale) + 'px';
        setClass(ui.window, 'is-narrow', client.width < 1050);
        var width = Math.min(client.width - 20, Math.max(760, Math.min(1280, client.width - 160)));
        var height = Math.min(client.height - 20, Math.max(480, Math.min(840, client.height - 160)));
        ui.window.style.width = Math.round(width) + 'rem';
        ui.window.style.height = Math.round(height) + 'rem';
        scheduleScrollbars();
    }

    function theme(values) { DK.theme.apply(values); }

    function matches(def) {
        return !query || [def.name, def.label, def.category, def.category !== undefined || def.name !== undefined ? categoryLabel(def.category) : '', def.description, (def.keywords || []).join(' ')].join(' ').toLowerCase().indexOf(query) >= 0;
    }
    function filter() {
        var signature = JSON.stringify([query, activeTab, rendered, !!(state && state.updater)]);
        if (signature === lastFilter) { return; }
        lastFilter = signature;
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
        scheduleScrollbars();
    }
    function dialogContext() {
        return {window: ui.window, labels: labels(), state: state, schema: schema, button: footerButton, send: send};
    }
    function closeProfiles() { DK.profileDialogs.close(); }
    function showInstalled() { DK.profileDialogs.installed(dialogContext()); }
    function showProfiles() { DK.profileDialogs.profiles(dialogContext()); }

    function dispose() {
        if (ui.markerEditor) { ui.markerEditor.dispose(); ui.markerEditor = null; }
        if (disposed) { return; }
        disposed = true;
        if (toastTimer !== null) { clearTimeout(toastTimer); }
        if (scrollbarTimer !== null) { clearTimeout(scrollbarTimer); scrollbarTimer = null; }
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
    DK.app = {dispose: dispose, themeCss: DK.theme.css};
}());
