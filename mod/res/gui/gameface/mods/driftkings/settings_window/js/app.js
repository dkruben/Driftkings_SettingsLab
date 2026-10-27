/* DK Settings — janela completa: barra lateral, página do módulo, detalhe da opção, revisão de
   alterações, perfis, atualizações, confirmações, tema e teclado.
   Fala com o Python só pelas ações de presenter.py (select, set, apply, save, ...). */
(function () {
    'use strict';
    var DK = window.DK, h = DK.h, t = DK.t, tf = DK.tf, send = DK.bridge.send;
    var CORE = 'dk.settings';
    // Section pages name their "enabled" control field_<sha1("enabled")[:16]> (settings/panel/sections.py).
    var ENABLED_IDS = ['enabled', 'field_3ea3f9802accf881'];
    var ICONS = window.DK_ASSETS || 'coui://gui/gameface/mods/driftkings/settings_window/assets/';
    var CATEGORY_ORDER = ['general', 'battle', 'hangar', 'system'];
    // Icon per module (assets/mods/*.svg). Section pages are named legacy.<previous section name>.
    var MOD_ICONS = {
        'dk.settings': 'settings', 'legacy.main': 'general', 'legacy.BanksLoader': 'soundbank', 'legacy.BattleEfficiency': 'efficiency',
        'legacy.LogsSwapper': 'damagelog', 'legacy.ZoomExtended': 'sniper', 'legacy.DispersionCircle': 'reticle', 'legacy.ArcadeZoom': 'arcadezoom',
        'legacy.DispersionTimer': 'aimtimer', 'legacy.FlightTimer': 'flighttime', 'legacy.AimingAngles': 'traverse', 'legacy.AutoAimOptimize': 'autoaim',
        'legacy.DistanceMarker': 'distance', 'legacy.ArmorCalculator': 'penetration', 'legacy.InfoPanel': 'targetinfo', 'legacy.ArtySplash': 'artillery',
        'legacy.MinimapPlugins': 'minimap', 'legacy.VehicleMarkers': 'markers', 'legacy.SpottedExtendedLight': 'spotted', 'legacy.SixthSense': 'sixthsense',
        'legacy.PlayerPanelPro': 'teampanels', 'legacy.BattleStat': 'battlestats', 'legacy.OwnHealth': 'health', 'legacy.MainGun': 'highcaliber',
        'legacy.MarksOnGunBattle': 'marksbattle', 'legacy.RepairExtended': 'repair', 'legacy.BattleOptions': 'battleoptions',
        'legacy.ServerTurretExtended': 'turretsync', 'legacy.CarouselStats': 'carousel', 'legacy.CrewSettings': 'crew', 'legacy.HangarOptions': 'hangar',
        'legacy.MarksOnGunHangar': 'markshangar', 'legacy.MarksOnGunTechTree': 'markstree', 'legacy.profile_ratings': 'ratings', 'legacy.AutoClaimClan': 'clan'
    };
    function iconFor(mod) {
        var id = String(mod.id).split(':')[0];
        if (MOD_ICONS[id]) { return ICONS + 'mods/' + MOD_ICONS[id] + '.svg'; }
        return ICONS + 'icon_' + (/^(gear|speaker|puzzle)$/.test(mod.icon) ? mod.icon : 'puzzle') + '.svg';
    }

    var ui = {}, schema = null, state = null, mods = {}, order = [], index = {};
    var page = null;          // current module page: {id, controls: {id: control}, list: [...], tabs, markers}
    var saved = {};           // last saved value per module/option (see trackSaved)
    var query = '', tab = '', focusId = null, pendingFocus = null, collapsed = {};
    var dialogs = {confirm: null, review: null, profiles: null, installed: null};
    var lastMessage = 0, toastTimer = null, layoutTimer=null, lastLayout = '', lastTheme = '', disposed = false;

    /* Helpers --------------------------------------------------------------- */
    function categoryName(category) {
        category = category || 'general';
        return t('category.' + category, {general: 'General', battle: 'Battle', hangar: 'Hangar', system: 'System'}[category] || category);
    }
    function button(parent, text, fn, extra) {
        return h('button.dk-button' + (extra ? '.' + extra.split(' ').join('.') : ''), {text: text, onclick: function (event) {
            DK.stop(event);
            if (!this.disabled) { DK.layer.closeMenu(true); fn(); }
        }}, null, parent);
    }
    function enable(node, on) { node.disabled = !on; DK.toggle(node, 'is-disabled', !on); }
    function enabledKey(mod) {
        for (var i = 0; i < mod.controls.length; i++) {
            var def = mod.controls[i];
            if (DK.contains(ENABLED_IDS, def.id) && (def.type === 'checkbox' || def.type === 'switch')) { return def.id; }
        }
        return null;
    }
    function statusOf(id) { return (state.status || {})[id] || {}; }
    function restartNeeded(id) { return !!statusOf(id).restartRequired || DK.contains(state.restartRequired, id); }
    function missingDeps(id) { return (mods[id].dependencies || []).filter(function (d) { return !d.installed; }); }
    function changedCount(id) { return ((state.changed || {})[id] || []).length; }
    function statusText(id) {
        var current = statusOf(id), parts = [];
        if (current.status === 'configError') { parts.push(t('statusConfigError')); }
        else if (current.status === 'error') { parts.push(t('statusError')); }
        else if (current.status && current.status !== 'active') { parts.push(t('status.unavailable')); }
        else { parts.push(current.enabled === false ? t('status.disabled') : t('status.enabled')); }
        missingDeps(id).forEach(function (d) { parts.push(t('dependencyMissing') + ': ' + d.id); });
        if (restartNeeded(id)) { parts.push(t('status.restart')); }
        return parts;
    }

    /* Shell ------------------------------------------------------------------ */
    function build() {
        var app = document.getElementById('dk-app');
        DK.clear(app);
        ui.window = h('div.dk-window', null, null, app);
        h('div.dk-window-line', null, null, ui.window);

        var top = h('div.dk-top', null, null, ui.window);
        ui.brand = h('div.dk-brand', null, null, top);
        ui.version = h('div.dk-version', null, null, top);
        h('div.dk-spacer', null, null, top);
        ui.search = h('div.dk-search', null, null, top);
        h('div.dk-search-icon', null, null, ui.search);
        ui.searchInput = h('input.dk-search-input', {type: 'text', maxLength: 64}, null, ui.search);
        ui.searchInput.addEventListener('input', function () { setQuery(ui.searchInput.value); });
        ui.searchInput.addEventListener('focus', function () { DK.toggle(ui.search, 'is-focused', true); });
        ui.searchInput.addEventListener('blur', function () { DK.toggle(ui.search, 'is-focused', false); });
        ui.searchKey = h('div.dk-kbd', {text: 'Ctrl F'}, null, ui.search);
        ui.searchClear = h('button.dk-search-clear', {text: '×', onclick: function (event) { DK.stop(event); ui.searchInput.value = ''; setQuery(''); DK.focus(ui.searchInput); }}, null, ui.search);
        ui.installed = h('button.dk-top-link', {onclick: function (event) { DK.stop(event); openInstalled(); }}, null, top);
        ui.close = h('button.dk-close', {text: '×', onclick: function (event) { DK.stop(event); send('close'); }}, null, top);

        var body = h('div.dk-body', null, null, ui.window);
        var sideHost = h('div.dk-side', null, null, body);
        ui.nav = h('div.dk-nav', null, null, sideHost);
        ui.navScroll = DK.layer.scroller(ui.nav, sideHost);

        var main = h('div.dk-main', null, null, body);
        ui.head = h('div.dk-head', null, null, main);
        ui.crumb = h('div.dk-crumb', null, null, ui.head);
        var titleRow = h('div.dk-title-row', null, null, ui.head);
        ui.titleIcon = h('img.dk-title-icon', null, null, titleRow);
        ui.title = h('div.dk-title', null, null, titleRow);
        ui.power = h('div.dk-power', {tabIndex: 0, role: 'switch'}, null, titleRow);
        h('div.dk-switch', null, [h('div.dk-switch-knob')], ui.power);
        ui.powerText = h('div.dk-power-text', null, null, ui.power);
        ui.power.addEventListener('click', function (event) { DK.stop(event); togglePower(); });
        ui.power.addEventListener('keydown', function (event) { if (event.keyCode === 13 || event.keyCode === 32) { DK.stop(event); togglePower(); } });
        h('div.dk-spacer', null, null, titleRow);
        ui.themeReset = button(titleRow, '', function () { send('reset_theme'); }, 'is-small');
        ui.description = h('div.dk-description', null, null, ui.head);
        ui.pills = h('div.dk-pills', null, null, ui.head);
        ui.notices = h('div.dk-notices', null, null, ui.head);
        ui.tabs = h('div.dk-tabs', null, null, ui.head);

        var listHost = h('div.dk-list-host', null, null, main);
        ui.list = h('div.dk-list', null, null, listHost);
        ui.listScroll = DK.layer.scroller(ui.list, listHost);

        ui.detail = h('div.dk-detail', null, null, body);
        ui.liveHost = h('div.dk-live-host', null, null, ui.detail);
        ui.detailBody = h('div.dk-detail-body', null, null, ui.detail);

        var foot = h('div.dk-foot', null, null, ui.window);
        ui.undo = button(foot, '', function () { send('undo'); }, 'is-quiet');
        ui.profiles = button(foot, '', openProfiles, 'is-quiet');
        ui.reset = button(foot, '', function () { send('reset', {mod: state.selected}); }, 'is-quiet');
        h('div.dk-spacer', null, null, foot);
        ui.summary = h('button.dk-summary', {onclick: function (event) { DK.stop(event); openReview(); }}, null, foot);
        h('span.dk-summary-dot', null, null, ui.summary);
        ui.summaryText = h('span.dk-summary-text', null, null, ui.summary);
        ui.summaryLink = h('span.dk-summary-link', null, null, ui.summary);
        ui.cancel = button(foot, '', function () { send('cancel'); });
        ui.apply = button(foot, '', function () { send('apply'); });
        ui.save = button(foot, '', function () { send('save'); }, 'is-primary');

        ui.toast = h('button.dk-toast', {onclick: function (event) { DK.stop(event); showToastText(); }}, null, ui.window);
        DK.layer.init(h('div.dk-layer', null, null, ui.window));
        document.addEventListener('keydown', onKey, true);
    }

    /* Schema: sidebar ------------------------------------------------------- */
    function onSchema(next) {
        disposePage();DK.modal.closeAll();DK.layer.closeMenu(true);
        schema = next;
        DK.setCatalog(schema.labels, schema.language);
        mods = {}; order = []; index = {};
        var title = String(t('title', 'DRIFTKINGS · SETTINGS')), cut = title.indexOf(' · ');
        DK.clear(ui.brand);
        h('span.dk-brand-mark', {text: cut > 0 ? title.slice(0, cut) : 'DK'}, null, ui.brand);
        h('span.dk-brand-name', {text: cut > 0 ? title.slice(cut + 3) : title}, null, ui.brand);
        ui.searchInput.placeholder = t('search', '');
        ui.searchClear.title = t('search.clear');
        ui.installed.textContent = t('installed', 'Installed');
        ui.close.title = t('close') + ' (Esc)';
        ui.themeReset.textContent = t('resetTheme');
        ui.undo.textContent = '↶  ' + t('undo'); ui.undo.title = t('undoHint', '') + ' (Ctrl+Z)';
        ui.profiles.textContent = t('profiles'); ui.reset.textContent = t('reset'); ui.reset.title = t('resetHint', '');
        ui.cancel.textContent = t('cancel'); ui.cancel.title = t('cancelHint', '');
        ui.apply.textContent = t('apply'); ui.apply.title = t('applyHint', '');
        ui.save.textContent = t('saveApply'); ui.save.title = t('saveApplyHint', '') + ' (Ctrl+S)';
        ui.summaryLink.textContent = t('review.open');

        var groups = {}, categories = CATEGORY_ORDER.slice();
        schema.mods.forEach(function (mod) {
            var category = mod.category || 'general';
            if (!groups[category]) { groups[category] = []; }
            if (!DK.contains(categories, category)) { categories.push(category); }
            groups[category].push(mod);
            mods[mod.id] = mod;
            index[mod.id] = {};
            mod.controls.forEach(function (def) { index[mod.id][def.id] = def; });
            if (mod.id === CORE) { ui.version.textContent = mod.version ? 'v' + mod.version : ''; }
        });
        DK.clear(ui.nav);
        ui.navItems = {}; ui.navGroups = [];
        categories.forEach(function (category) {
            var items = groups[category];
            if (!items) { return; }
            var group = h('div.dk-nav-group', null, null, ui.nav);
            var head = h('button.dk-nav-head', null, [h('span.dk-nav-caret'), h('span.dk-nav-head-name', {text: categoryName(category)})], group);
            var count = h('span.dk-nav-head-count', {text: String(items.length)}, null, head);
            var box = h('div.dk-nav-items', null, null, group);
            head.addEventListener('click', function (event) {
                DK.stop(event);
                collapsed[category] = !collapsed[category];
                DK.toggle(group, 'is-collapsed', collapsed[category]);
                ui.navScroll.update();
            });
            DK.toggle(group, 'is-collapsed', !!collapsed[category]);
            ui.navGroups.push({node: group, count: count, category: category, ids: items.map(function (mod) { return mod.id; })});
            items.forEach(function (mod) {
                order.push(mod.id);
                var item = h('button.dk-nav-item', null, null, box);
                h('img.dk-nav-icon', {src: iconFor(mod)}, null, item);
                h('span.dk-nav-name', {text: mod.name}, null, item);
                var badge = h('span.dk-nav-badge', null, null, item);
                h('span.dk-nav-state', null, null, item);
                item.addEventListener('click', function (event) { DK.stop(event); select(mod.id); });
                ui.navItems[mod.id] = {node: item, badge: badge};
            });
        });
        ui.navEmpty = h('div.dk-nav-empty', null, null, ui.nav);
        page = null;
        if (state) { onState(state); }
    }
    function select(id) {
        if (state && state.selected !== id) { send('select', {mod: id}); }
    }

    /* Module page ------------------------------------------------------------ */
    function context(modId) {
        return {
            commit: function (key, value, alpha) {
                var payload = {mod: modId, key: key, value: value};
                if (alpha !== undefined) { payload.alpha = alpha; }
                send('set', payload);
            },
            capture: function (key) { send('capture', {mod: modId, key: key}); },
            // Example values for formatted text: the module's own middle colour stands in for %(color)s.
            sample: function () {
                var colors = (mods[modId] ? mods[modId].controls : []).filter(function (def) { return def.type === 'color'; });
                var values = (state && state.values[modId]) || {}, pick = colors[Math.floor(colors.length / 2)];
                return {color: pick ? values[pick.id] : null};
            },
            action: function (key) { send('button', {mod: modId, key: key}); },
            // Theme sliders and the minimap preview follow a slider while it is dragged;
            // the value itself is only sent on release.
            preview: function (key, value) {
                if (modId === CORE) { var theme = DK.copy(state.theme || {}); theme[key] = value; applyTheme(theme); }
                if (page && page.id === modId && page.live) { page.live.preview(key, value); }
            }
        };
    }
    function disposePage() {
        if (!page) { return; }
        Object.keys(page.controls).forEach(function (id) { page.controls[id].dispose(); });
        if (page.markers) { page.markers.dispose(); }
        if (page.live) { page.live.dispose(); }
        page = null;
    }
    function renderPage(modId) {
        disposePage();
        DK.layer.closeMenu(true); DK.layer.hideTip();
        DK.clear(ui.list); DK.clear(ui.tabs);
        tab = ''; focusId = null;
        var mod = mods[modId];
        page = {id: modId, controls: {}, list: [], tabs: [], power: mod ? enabledKey(mod) : null, markers: null, updates: null, live: null};
        DK.show(ui.themeReset, modId === CORE);
        DK.toggle(ui.window, 'has-wide-page', false);
        DK.toggle(ui.window, 'has-live', false);
        var live = mod && (DK.minimapPreview.supports(mod) ? DK.minimapPreview : DK.hudPreview.supports(mod) ? DK.hudPreview
            : DK.carouselPreview.supports(mod) ? DK.carouselPreview : null);
        if (live) {
            page.live = live.create(ui.liveHost, mod);
            DK.toggle(ui.window, 'has-live', true);
            // Draw again once the wider column has been laid out.
            setTimeout(function () { if (page && page.live) { page.live.redraw(); } }, 0);
        }
        if (!mod) {
            ui.title.textContent = ''; ui.crumb.textContent = ''; ui.description.textContent = '';
            DK.show(ui.titleIcon, false);
            h('div.dk-empty', {text: t('noMods')}, null, ui.list);
            DK.show(ui.power, false);
            return;
        }
        ui.crumb.textContent = categoryName(mod.category);
        ui.title.textContent = mod.name;
        ui.titleIcon.src = iconFor(mod);
        DK.show(ui.titleIcon, true);
        var description = mod.description || '';
        if (mod.soundBank) { description += (description ? '  ·  ' : '') + t('sound.bank') + ': ' + mod.soundBank; }
        ui.description.textContent = description;
        DK.show(ui.description, !!description);
        DK.show(ui.power, !!page.power);
        var ctx = context(modId);
        if (mod.preview && mod.preview.kind === 'vehicleMarkers') {
            DK.toggle(ui.window, 'has-wide-page', true);
            page.markers = DK.markers.create(ui.list, mod, ctx);
            DK.show(ui.tabs, false);
            return;
        }
        if (!mod.controls.length) { h('div.dk-empty', {text: t('noControls')}, null, ui.list); }
        var section = null;
        mod.controls.forEach(function (def) {
            if (def.id === page.power || (def.type === 'button' && /^sound(Preview|Stop)$/.test(def.id) && def.visible === false)) { return; }
            var control = DK.controls.create(def, ctx);
            ui.list.appendChild(control.node);
            page.controls[def.id] = control;
            if (def.type === 'section') { section = {control: control, members: []}; page.list.push(section); }
            else if (section) { section.members.push(control); }
            else { page.list.push({control: null, members: [control]}); section = page.list[page.list.length - 1]; }
            if (def.tab && !DK.contains(page.tabs, def.tab)) { page.tabs.push(def.tab); }
            if (DK.controls.isValue(def)) {
                control.node.addEventListener('mouseenter', function () { setFocus(def.id); });
                control.node.addEventListener('focus', function () { setFocus(def.id); }, true);
            }
        });
        ui.noResults = h('div.dk-empty.dk-no-results', {text: t('noResults')}, null, ui.list);
        if (modId === CORE) { renderCoreExtras(); }
        DK.show(ui.tabs, page.tabs.length > 0);
        if (page.tabs.length) {
            [''].concat(page.tabs).forEach(function (name) {
                var b = h('button.dk-tab', null, [h('span', {text: name || t('all')}), h('span.dk-tab-dot')], ui.tabs);
                b.addEventListener('click', function (event) { DK.stop(event); tab = name; renderTabs(); filter(); });
                b.tabName = name;
            });
        }
        ui.list.scrollTop = 0;
    }
    function renderCoreExtras() {
        var updates = h('div.dk-updates', null, null, ui.list);
        h('div.dk-section', null, [h('span', {text: t('updates.title')})], updates);
        var u = page.updates = {root: updates, lines: h('div.dk-update-lines', null, null, updates)};
        u.changelog = h('div.dk-update-changelog', null, null, updates);
        u.note = h('div.dk-update-note', null, null, updates);
        var actions = h('div.dk-update-actions', null, null, updates);
        u.check = button(actions, t('updates.check'), function () { send('check_updates'); }, 'is-small');
        u.download = button(actions, t('updates.download'), function () { send('download_update'); }, 'is-small is-primary');
        u.cancel = button(actions, t('updates.cancelDownload'), function () { send('cancel_update_download'); }, 'is-small');
        u.install = button(actions, t('updates.install'), function () { send('schedule_update'); }, 'is-small is-primary');
        u.restart = button(actions, t('restartNow'), function () { send('restart_update'); }, 'is-small is-primary');
        u.later = button(actions, t('updates.later'), function () { send('defer_update'); }, 'is-small');
        u.cancelInstall = button(actions, t('updates.cancelInstall'), function () { send('cancel_update_install'); }, 'is-small');
        u.manual = button(actions, t('updates.manual'), function () { send('manual_update'); }, 'is-small');
        var community = page.community = h('div.dk-community', null, null, ui.list);
        h('div.dk-section', null, [h('span', {text: 'Discord'})], community);
        button(community, 'discord.gg/GJcy4x7SP', function () { send('open_discord'); }, 'is-small');
    }
    function renderUpdates() {
        var u = page && page.updates, update = state.updater;
        if (!u) { return; }
        DK.show(u.root, !!update);
        if (!update) { return; }
        DK.clear(u.lines);
        var status = t('updates.' + update.status, update.status);
        if (update.status === 'IDLE' && update.lastCheck === null) { status = t('updates.notChecked'); }
        if (update.error === 'transportUnavailable') { status = t('updates.transportUnavailable'); }
        if (update.latestVersion && update.compatible === false) { status += ' ' + t('updates.incompatible'); }
        if (update.cancellingInstall) { status = t('updates.cancelling'); }
        if (update.status === 'DOWNLOADING' && typeof update.downloadPercent === 'number') { status += ' ' + update.downloadPercent + '%'; }
        [[t('updates.installed'), update.installedVersion], [t('updates.channel'), update.channel],
         [t('updates.lastCheck'), update.lastCheck === null ? t('updates.never') : new Date(update.lastCheck * 1000).toLocaleString()],
         [t('updates.latest'), update.latestVersion || '—'], ['', status]].forEach(function (line) {
            h('div.dk-kv', null, [h('div.dk-kv-key', {text: line[0]}), h('div.dk-kv-value', {text: line[1]})], u.lines);
        });
        u.changelog.textContent = (update.changelog || []).join('\n');
        var busy = DK.contains(['CHECKING', 'DOWNLOADING', 'VERIFYING', 'INSTALLING', 'RESTART_REQUIRED'], update.status);
        var prepared = update.status === 'RESTART_REQUIRED' && update.installScheduled === true && !update.cancellingInstall;
        var note = update.installBlocked ? t('updates.block.' + update.installBlocked, t('updates.installBlocked')) : '';
        if (prepared) { note += (note ? ' ' : '') + t('updates.wgcLimit'); }
        var outcome = update.lastInstallResult;
        if (outcome) { note += (note ? '\n' : '') + String(t('updates.result.' + outcome.status, t('updates.result.failed'))).replace('{version}', outcome.version || ''); }
        u.note.textContent = note;
        enable(u.check, !busy && update.status !== 'READY' && !update.cancellingInstall);
        var downloadable = update.canDownload && update.compatible === true && DK.contains(['AVAILABLE', 'ERROR'], update.status);
        DK.show(u.download, downloadable); enable(u.download, downloadable);
        DK.show(u.cancel, !!update.canCancel); enable(u.cancel, !!update.canCancel);
        var installable = update.canInstall && update.compatible === true && DK.contains(['READY', 'ERROR'], update.status) && !update.cancellingInstall;
        DK.show(u.install, installable); enable(u.install, installable);
        DK.show(u.restart, prepared); enable(u.restart, prepared && update.canRestart && !state.unsaved);
        DK.show(u.later, prepared && !update.restartDeferred); enable(u.later, prepared);
        DK.show(u.cancelInstall, update.status === 'INSTALLING' || !!update.installScheduled || !!update.cancellingInstall);
        enable(u.cancelInstall, !update.cancellingInstall);
        enable(u.manual, !DK.contains(['INSTALLING', 'RESTART_REQUIRED'], update.status));
    }
    function renderTabs() {
        var changed = (state && state.changed[page.id]) || [];
        for (var i = 0; i < ui.tabs.childNodes.length; i++) {
            var node = ui.tabs.childNodes[i], name = node.tabName;
            DK.toggle(node, 'is-selected', name === tab);
            DK.toggle(node, 'is-changed', !!name && changed.some(function (id) { return page.controls[id] && page.controls[id].def.tab === name; }));
        }
    }
    function togglePower() {
        var key = page && page.power;
        if (!key || DK.contains(state.disabled[page.id], key)) { return; }
        send('set', {mod: page.id, key: key, value: (state.values[page.id] || {})[key] !== true});
    }

    /* Header ----------------------------------------------------------------- */
    function pill(text, kind, alert) {
        var node = h('div.dk-pill' + (kind ? '.is-' + kind : ''), null, null, ui.pills);
        if (alert) { h('span.dk-alert', null, null, node); }
        h('span', {text: text}, null, node);
    }
    function renderHead() {
        var id = page.id, mod = mods[id];
        DK.clear(ui.pills); DK.clear(ui.notices);
        if (!mod) { return; }
        var current = statusOf(id), count = changedCount(id);
        if (count) { pill(count === 1 ? t('changes.one') : tf('changes.many', {n: count}), 'accent'); }
        if (current.status && current.status !== 'active') { pill(statusText(id)[0], 'error', true); }
        if (restartNeeded(id)) { pill(t('status.restart'), 'warning', true); }
        (mod.dependencies || []).forEach(function (d) { pill((d.installed ? '✓ ' : '') + (d.installed ? t('status.available') : t('dependencyMissing')) + ': ' + d.id, d.installed ? 'ok' : 'warning', !d.installed); });
        if (mod.version) { pill((id === CORE ? 'Driftkings ' : t('version') + ' ') + mod.version); }
        if (mod.author) { pill(mod.author); }
        ((state.compatibilityWarnings || {})[id] || []).forEach(function (warning) {
            h('div.dk-notice', null, [h('span.dk-alert'), h('span', {text: warning.text})], ui.notices);
        });
        if (current.status === 'configError' || current.status === 'error') {
            h('div.dk-notice.is-error', null, [h('span.dk-alert'), h('span', {text: current.status === 'error' ? t('statusError') : t('statusConfigError')})], ui.notices);
        }
        if (page.power) {
            var on = (state.values[id] || {})[page.power] === true;
            DK.toggle(ui.power.firstChild, 'is-on', on);
            DK.toggle(ui.power, 'is-on', on);
            DK.toggle(ui.power, 'is-disabled', DK.contains(state.disabled[id], page.power));
            ui.powerText.textContent = on ? t('module.on') : t('module.off');
        }
    }

    /* Saved values -------------------------------------------------------------- */
    // state.changed lists what differs from the saved file, so anything outside it is the saved value.
    function trackSaved() {
        Object.keys(state.values || {}).forEach(function (id) {
            var values = state.values[id], changed = state.changed[id] || [], secrets = state.secrets[id] || [];
            var store = saved[id] || (saved[id] = {});
            Object.keys(values).forEach(function (key) { if (!DK.contains(changed, key) && !DK.contains(secrets, key)) { store[key] = DK.copy(values[key]); } });
        });
    }

    /* Values as text --------------------------------------------------------------- */
    function valueText(def, value) {
        if (value === undefined) { return {text: '—'}; }
        switch (def.type) {
        case 'switch': case 'checkbox': return {text: value ? t('on', 'ON') : t('off', 'OFF')};
        case 'dropdown':
            for (var i = 0; i < def.options.length; i++) { if (def.options[i].value === value) { return {text: def.options[i].label}; } }
            return {text: String(value)};
        case 'multiselect': return {text: def.options.filter(function (o) { return DK.contains(value, o.value); }).map(function (o) { return o.label; }).join(', ') || '—'};
        case 'slider': case 'number': return {text: String(value) + (def.unit ? ' ' + def.unit : '')};
        case 'color': return {text: String(value), color: value};
        case 'hotkey':
            var names = state.keyNames || {};
            return {text: (value || []).map(function (g) { return g.map(function (c) { return names[String(c)] || String(c); }).join(' / '); }).join(' + ') || t('noKey')};
        case 'password': return {text: value ? '••••••' : t('secretEmpty')};
        default:
            var text = value === null ? '' : String(value);
            return {text: text ? (text.length > 48 ? text.slice(0, 48) + '…' : text) : '—'};
        }
    }
    function valueNode(parent, extra, def, value) {
        var shown = valueText(def, value), node = h('div.dk-value' + (extra ? '.' + extra : ''), {title: shown.text}, null, parent);
        if (shown.color) { h('span.dk-value-swatch', {style: {backgroundColor: shown.color}}, null, node); }
        h('span', {text: shown.text}, null, node);
        return node;
    }
    function lockedBy(def) {
        return Object.keys(def.dependsOn || {}).map(function (key) { return index[page.id][key] ? index[page.id][key].label : key; }).join(', ');
    }

    /* Detail panel ------------------------------------------------------------------ */
    function setFocus(id) {
        if (focusId === id) { return; }
        if (focusId && page.controls[focusId]) { DK.toggle(page.controls[focusId].node, 'is-focused', false); }
        focusId = id;
        if (id && page.controls[id]) { DK.toggle(page.controls[id].node, 'is-focused', true); }
        renderDetail();
    }
    function kv(parent, key, build) {
        var line = h('div.dk-kv', null, [h('div.dk-kv-key', {text: key})], parent);
        build(line);
    }
    function renderDetail() {
        var panel = ui.detailBody;
        DK.clear(panel);
        if (!page || !mods[page.id] || !state || page.markers) { return; }
        var compact = !!page.live;
        var mod = mods[page.id], control = focusId ? page.controls[focusId] : null;
        if (!control) {
            h('div.dk-detail-kicker', {text: t('detail.module')}, null, panel);
            h('div.dk-detail-title', {text: mod.name}, null, panel);
            h('div.dk-detail-text', {text: statusText(page.id).join('  ·  ')}, null, panel);
            var summary = h('div.dk-detail-facts', null, null, panel);
            kv(summary, t('detail.options'), function (line) { h('div.dk-value', {text: String(mod.controls.filter(DK.controls.isValue).length)}, null, line); });
            kv(summary, t('detail.changed'), function (line) { h('div.dk-value', {text: String(changedCount(page.id))}, null, line); });
            h('div.dk-detail-hint', {text: t('detail.hint')}, null, panel);
            if (compact) { return; }
            h('div.dk-spacer', null, null, panel);
            var keys = h('div.dk-detail-keys', null, [h('div.dk-detail-kicker', {text: t('detail.keys')})], panel);
            [['Ctrl F', 'keys.search'], ['Ctrl S', 'keys.save'], ['Ctrl Z', 'keys.undo'], ['Ctrl ↑ ↓', 'keys.module'], ['Esc', 'keys.close']].forEach(function (item) {
                h('div.dk-detail-key', null, [h('span.dk-kbd', {text: item[0]}), h('span', {text: t(item[1])})], keys);
            });
            return;
        }
        var def = control.def, id = page.id, current = (state.values[id] || {})[def.id];
        var changed = DK.contains(state.changed[id], def.id), locked = DK.contains(state.disabled[id], def.id);
        var before = (saved[id] || {})[def.id];
        h('div.dk-detail-kicker', {text: t('detail.option')}, null, panel);
        h('div.dk-detail-title', {text: def.label}, null, panel);
        if (def.description) { h('div.dk-detail-text', {text: def.description}, null, panel); }
        var facts = h('div.dk-detail-facts', null, null, panel);
        if (def.type !== 'password') {
            kv(facts, t('detail.saved'), function (line) { valueNode(line, null, def, changed ? before : current); });
            if (changed) { kv(facts, t('detail.new'), function (line) { valueNode(line, 'is-new', def, current); }); }
        }
        if ('default' in def) { kv(facts, t('detail.default'), function (line) { valueNode(line, null, def, def['default']); }); }
        if (def.type === 'slider' || def.type === 'number') {
            kv(facts, t('detail.range'), function (line) { h('div.dk-value', {text: def.min + ' – ' + def.max + (def.unit ? ' ' + def.unit : '')}, null, line); });
        }
        var timing = def.metadata && def.metadata.applyTiming;
        if (timing) { kv(facts, t('detail.applies'), function (line) { h('div.dk-value' + (timing === 'restart' ? '.is-warning' : ''), {text: t('timing.' + timing, timing)}, null, line); }); }
        if (def.dependsOn && Object.keys(def.dependsOn).length) { kv(facts, t('detail.depends'), function (line) { h('div.dk-value', {text: lockedBy(def)}, null, line); }); }
        if (locked) { h('div.dk-detail-hint.is-warning', {text: t('detail.locked')}, null, panel); }
        h('div.dk-spacer', null, null, panel);
        var actions = h('div.dk-detail-actions', null, null, panel);
        if (changed && before !== undefined && !locked) { button(actions, t('detail.revert'), function () { send('set', {mod: id, key: def.id, value: DK.copy(before)}); }, 'is-small'); }
        if ('default' in def && !DK.same(current, def['default']) && !locked) { button(actions, t('detail.reset'), function () { send('set', {mod: id, key: def.id, value: DK.copy(def['default'])}); }, 'is-small'); }
    }

    /* Filtering ----------------------------------------------------------------------- */
    function matches(text) { return !query || String(text || '').toLowerCase().indexOf(query) >= 0; }
    function defMatches(def) { return matches([def.label, def.description, (def.keywords || []).join(' ')].join(' ')); }
    function modMatches(mod) { return matches([mod.name, mod.description, categoryName(mod.category)].join(' ')); }
    function setQuery(value) {
        query = String(value || '').toLowerCase().replace(/^\s+|\s+$/g, '');
        DK.toggle(ui.search, 'has-query', !!query);
        filter();
    }
    function filter() {
        var anyNav = false;
        ui.navGroups.forEach(function (group) {
            var visible = 0;
            group.ids.forEach(function (id) {
                var mod = mods[id], shown = modMatches(mod) || mod.controls.some(defMatches);
                DK.show(ui.navItems[id].node, shown);
                if (shown) { visible += 1; }
            });
            DK.show(group.node, visible > 0);
            group.count.textContent = String(visible);
            // A search opens collapsed groups so matches are never hidden.
            DK.toggle(group.node, 'is-collapsed', !query && !!collapsed[group.category]);
            anyNav = anyNav || visible > 0;
        });
        ui.navEmpty.textContent = anyNav ? '' : t('noResults');
        if (!page) { return; }
        var whole = !!mods[page.id] && modMatches(mods[page.id]), any = false;
        page.list.forEach(function (section) {
            var visible = 0;
            section.members.forEach(function (control) {
                var def = control.def, shown = (!tab || !def.tab || def.tab === tab) && (whole || defMatches(def));
                DK.show(control.node, shown);
                if (shown && DK.controls.isValue(def)) { visible += 1; }
            });
            if (section.control) {
                var def = section.control.def;
                DK.show(section.control.node, visible > 0 && (!tab || !def.tab || def.tab === tab));
            }
            any = any || visible > 0;
        });
        if (ui.noResults) { DK.show(ui.noResults, !!query && !any && !page.markers); }
        var updatesTitle = t('updates.title');
        if (page.updates) { DK.show(page.updates.root, !!state.updater && (!tab || tab === updatesTitle) && (whole || matches(updatesTitle))); }
        if (page.community) { DK.show(page.community, !tab && !query); }
        ui.navScroll.update(); ui.listScroll.update();
    }

    /* State --------------------------------------------------------------------------- */
    function onState(next) {
        state = next;
        if (!schema) { return; }
        trackSaved();
        applyTheme(state.theme || {});
        layout();
        if (!page || page.id !== state.selected) { renderPage(state.selected); filter(); }
        var id = page.id, values = state.values[id] || {}, changed = state.changed[id] || [], disabled = state.disabled[id] || [];
        var secrets = state.secrets[id] || [];
        var updaterBusy = state.updater && DK.contains(['CHECKING', 'DOWNLOADING', 'VERIFYING', 'INSTALLING'], state.updater.status);
        Object.keys(page.controls).forEach(function (key) {
            var control = page.controls[key], off = DK.contains(disabled, key) || !!(updaterBusy && id === CORE && key === 'updateChannel');
            control.sync({disabled: off, changed: DK.contains(changed, key), value: values[key], values: values, secretSet: DK.contains(secrets, key),
                          keyNames: state.keyNames || {}, capturing: !!(state.capture && state.capture.mod === id && state.capture.key === key),
                          preview: (state.previews || {})[key] || '', lockedBy: off ? lockedBy(control.def) : ''});
            if (Object.prototype.hasOwnProperty.call(values, key)) { control.set(values[key]); }
        });
        if (page.markers) { page.markers.update(values, {disabled: disabled, changed: changed}); }
        if (page.live) { page.live.update(values, state.values); }
        renderNav();
        renderHead();
        renderTabs();
        renderUpdates();
        renderFoot();
        renderDetail();
        renderDialogs();
        toast(state.message);
        showPending();
        ui.navScroll.update(); ui.listScroll.update();
    }
    function renderNav() {
        Object.keys(ui.navItems).forEach(function (id) {
            var item = ui.navItems[id], current = statusOf(id), error = !!current.status && current.status !== 'active';
            var count = changedCount(id);
            DK.toggle(item.node, 'is-selected', id === state.selected);
            DK.toggle(item.node, 'is-error', error);
            DK.toggle(item.node, 'is-off', !error && current.enabled === false);
            DK.toggle(item.node, 'is-warning', !error && (missingDeps(id).length > 0 || restartNeeded(id)));
            item.badge.textContent = count ? String(count) : '';
            DK.show(item.badge, count > 0);
            item.node.title = mods[id].name + ' — ' + statusText(id).join(' · ');
        });
    }
    function renderFoot() {
        var mod = mods[page.id], total = 0, modules = 0;
        Object.keys(state.changed || {}).forEach(function (id) { var n = changedCount(id); total += n; if (n) { modules += 1; } });
        DK.toggle(ui.summary, 'is-visible', total > 0 || !!state.pending);
        var text = !total ? t('notApplied') : total === 1 ? t('changes.one') : modules === 1 ? tf('changes.many', {n: total}) : tf('changes.count', {n: total, m: modules});
        if (total && state.pending) { text += '  ·  ' + t('notApplied'); }
        ui.summaryText.textContent = text;
        DK.show(ui.summaryLink, total > 0);
        enable(ui.undo, !!state.canUndo);
        enable(ui.reset, !!mod && mod.controls.some(function (def) { return 'default' in def; }));
        enable(ui.profiles, !state.inBattle);
        enable(ui.cancel, !!state.pending);
        enable(ui.apply, !!state.pending);
    }

    /* Dialogs ------------------------------------------------------------------------- */
    function dialog(title, text) {
        var panel = h('div.dk-dialog');
        h('div.dk-dialog-title', {text: title}, null, panel);
        if (text) { h('div.dk-dialog-text', {text: text}, null, panel); }
        return panel;
    }
    function renderDialogs() {
        var wanted = state.restartPrompt ? 'restart' : state.confirm ? 'confirm' : null;
        var open = dialogs.confirm;
        if (open && open.kind !== wanted) { var old = open; dialogs.confirm = null; old.modal.close('code'); }
        if (wanted && !dialogs.confirm) {
            DK.layer.closeMenu(true);
            if (dialogs.review) { dialogs.review.modal.close('code'); }
            var restart = wanted === 'restart';
            var panel = dialog(restart ? t('restartTitle') : t('confirmTitle'),
                restart ? (state.restartReason === 'updater' ? t('updates.restartText') : t('restartText')) : t('confirmText'));
            var actions = h('div.dk-dialog-actions', null, null, panel), entry = {kind: wanted};
            if (restart) {
                button(actions, t('restartLater'), function () { send('restart', {choice: 'later'}); });
                entry.primary = button(actions, t('restartNow'), function () { send('restart', {choice: 'now'}); }, 'is-primary');
            } else {
                button(actions, t('confirmStay'), function () { send('confirm', {choice: 'stay'}); });
                button(actions, t('confirmDiscard'), function () { send('confirm', {choice: 'discard'}); }, 'is-danger');
                entry.primary = button(actions, t('confirmSave'), function () { send('confirm', {choice: 'save'}); }, 'is-primary');
            }
            entry.modal = DK.modal.open(panel, {dismissable: false, onClose: function (reason) {
                if (dialogs.confirm === entry) { dialogs.confirm = null; }
                if (reason === 'escape') { send(restart ? 'restart' : 'confirm', {choice: restart ? 'later' : 'stay'}); }
            }});
            dialogs.confirm = entry;
        }
        if (dialogs.confirm && dialogs.confirm.kind === 'restart') {
            enable(dialogs.confirm.primary, !(state.inBattle || state.unsaved || (state.restartReason === 'updater' && (!state.updater || !state.updater.canRestart))));
        }
        if (dialogs.review) { renderReview(); }
        if (dialogs.profiles) { renderProfiles(); }
    }

    /* Review ----------------------------------------------------------------------------- */
    function changeList() {
        var result = [];
        order.forEach(function (id) {
            ((state.changed || {})[id] || []).forEach(function (key) { if (index[id][key]) { result.push({mod: mods[id], def: index[id][key]}); } });
        });
        return result;
    }
    function openReview() {
        if (dialogs.review) { return; }
        var panel = dialog(t('review.title'), t('review.sub'));
        var host = h('div.dk-review-host', null, null, panel);
        var list = h('div.dk-review', null, null, host);
        var scroll = DK.layer.scroller(list, host);
        var actions = h('div.dk-dialog-actions', null, null, panel);
        var entry = {list: list, scroll: scroll};
        button(actions, t('close'), function () { entry.modal.close('button'); });
        h('div.dk-spacer', null, null, actions);
        entry.cancel = button(actions, t('cancel'), function () { send('cancel'); });
        entry.apply = button(actions, t('apply'), function () { send('apply'); });
        button(actions, t('saveApply'), function () { entry.modal.close('button'); send('save'); }, 'is-primary');
        entry.modal = DK.modal.open(panel, {className: 'dk-modal-wide', onClose: function () { scroll.dispose();dialogs.review = null; }});
        dialogs.review = entry;
        renderReview();
    }
    function renderReview() {
        var entry = dialogs.review, list = entry.list, items = changeList(), last = null;
        DK.clear(list);
        enable(entry.cancel, !!state.pending);
        enable(entry.apply, !!state.pending);
        if (!items.length) { h('div.dk-empty', {text: t('review.empty')}, null, list); entry.scroll.update(); return; }
        items.forEach(function (item) {
            var id = item.mod.id, def = item.def, before = (saved[id] || {})[def.id];
            if (last !== id) { last = id; h('div.dk-review-mod', {text: item.mod.name}, null, list); }
            var row = h('div.dk-review-row', null, null, list);
            h('div.dk-review-name', {text: def.label, title: def.label}, null, row);
            var values = h('div.dk-review-values', null, null, row);
            if (def.type === 'password') { h('div.dk-value.is-new', {text: t('modified')}, null, values); }
            else {
                valueNode(values, 'is-old', def, before);
                h('div.dk-review-arrow', {text: '→'}, null, values);
                valueNode(values, 'is-new', def, (state.values[id] || {})[def.id]);
            }
            button(row, t('review.go'), function () { goTo(id, def.id); }, 'is-small');
            var revert = button(row, t('review.revert'), function () { send('set', {mod: id, key: def.id, value: DK.copy(before)}); }, 'is-small');
            enable(revert, before !== undefined && def.type !== 'password' && !DK.contains(state.disabled[id], def.id));
        });
        entry.scroll.update();
    }
    function goTo(id, key) {
        if (dialogs.review) { dialogs.review.modal.close('button'); }
        ui.searchInput.value = ''; setQuery('');
        pendingFocus = {mod: id, key: key};
        if (state.selected !== id) { select(id); } else { showPending(); }
    }
    function showPending() {
        if (!pendingFocus || !page || pendingFocus.mod !== page.id) { return; }
        var control = page.controls[pendingFocus.key];
        pendingFocus = null;
        if (!control) { return; }
        tab = ''; renderTabs(); filter();
        setFocus(control.def.id);
        ui.listScroll.to(control.node.offsetTop - 80);
        DK.toggle(control.node, 'is-flash', true);
        setTimeout(function () { DK.toggle(control.node, 'is-flash', false); }, 1400);
    }

    /* Profiles ------------------------------------------------------------------------------ */
    function openProfiles() {
        if (dialogs.profiles || state.inBattle) { return; }
        var panel = dialog(t('profiles'), t('profileHelp'));
        var entry = {selected: '', exported: null};
        var columns = h('div.dk-profiles', null, null, panel);
        entry.list = h('div.dk-profile-list', null, null, columns);
        var side = h('div.dk-profile-side', null, null, columns);
        entry.name = h('input.dk-field', {type: 'text', maxLength: 64, placeholder: t('profileName')}, null, side);
        var row1 = h('div.dk-profile-actions', null, null, side);
        function op(operation, extra) { var data = extra || {}; data.operation = operation; send('profile', data); }
        entry.create = button(row1, t('profileCreate'), function () { op('create', {name: entry.name.value}); }, 'is-small');
        entry.load = button(row1, t('profileLoad'), function () { op('load', {name: entry.selected}); }, 'is-small is-primary');
        entry.rename = button(row1, t('profileRename'), function () { op('rename', {name: entry.selected, target: entry.name.value}); }, 'is-small');
        entry.remove = button(row1, t('profileDelete'), function () {
            if (!entry.confirming) { entry.confirming = true; entry.remove.textContent = t('confirmDelete'); return; }
            entry.confirming = false; entry.remove.textContent = t('profileDelete');
            op('delete', {name: entry.selected});
        }, 'is-small is-danger');
        entry.json = h('textarea.dk-field.dk-profile-json', {maxLength: 2000000}, null, panel);
        var row2 = h('div.dk-dialog-actions', null, null, panel);
        button(row2, t('profileExport'), function () { op('export'); }, 'is-small');
        button(row2, t('profileImport'), function () { op('import', {text: entry.json.value}); }, 'is-small');
        h('div.dk-spacer', null, null, row2);
        button(row2, t('close'), function () { entry.modal.close('button'); });
        entry.modal = DK.modal.open(panel, {className: 'dk-modal-wide', onClose: function () { dialogs.profiles = null; }});
        dialogs.profiles = entry;
        renderProfiles();
    }
    function renderProfiles() {
        var entry = dialogs.profiles, names = state.profiles || [];
        if (!DK.contains(names, entry.selected)) { entry.selected = names[0] || ''; }
        DK.clear(entry.list);
        if (!names.length) { h('div.dk-empty', {text: '—'}, null, entry.list); }
        names.forEach(function (name) {
            h('button.dk-profile' + (name === entry.selected ? '.is-selected' : ''), {text: name, onclick: function (event) {
                DK.stop(event); entry.selected = name; entry.name.value = name; entry.confirming = false; entry.remove.textContent = t('profileDelete'); renderProfiles();
            }}, null, entry.list);
        });
        [entry.load, entry.rename, entry.remove].forEach(function (b) { enable(b, !!entry.selected); });
        if (state.profileText && state.profileText !== entry.exported) { entry.exported = state.profileText; entry.json.value = state.profileText; }
    }

    /* Installed components ------------------------------------------------------------------- */
    function openInstalled() {
        if (dialogs.installed) { return; }
        var panel = dialog(t('installed'));
        var host = h('div.dk-review-host', null, null, panel), list = h('div.dk-review', null, null, host), scroll = DK.layer.scroller(list, host);
        order.forEach(function (id) {
            var mod = mods[id], row = h('div.dk-installed', null, null, list), current = statusOf(id);
            h('div.dk-installed-name', null, [h('img.dk-installed-icon', {src: iconFor(mod)}), h('span', {text: mod.name})], row);
            h('div.dk-installed-meta', {text: [categoryName(mod.category), mod.version, mod.author].filter(Boolean).join('  ·  ')}, null, row);
            h('div.dk-installed-state' + (current.enabled === false ? '.is-off' : '.is-on'), {text: statusText(id).join(' · ')}, null, row);
        });
        if (state.diagnostics) { h('textarea.dk-field.dk-profile-json', {value: JSON.stringify(state.diagnostics, null, 2), readOnly: true}, null, list); }
        var actions = h('div.dk-dialog-actions', null, null, panel), entry = {};
        button(actions, t('close'), function () { entry.modal.close('button'); });
        entry.modal = DK.modal.open(panel, {className: 'dk-modal-wide', onClose: function () { scroll.dispose();dialogs.installed = null; }});
        dialogs.installed = entry;
        setTimeout(scroll.update, 0);
    }

    /* Toast ---------------------------------------------------------------------------------- */
    function toast(message) {
        if (!message || message.id === lastMessage) { return; }
        lastMessage = message.id;
        ui.toast.textContent = message.text;
        ui.toast.title = message.text;
        DK.toggle(ui.toast, 'is-error', message.kind === 'error');
        DK.toggle(ui.toast, 'is-visible', true);
        if (toastTimer !== null) { clearTimeout(toastTimer); }
        toastTimer = setTimeout(function () { toastTimer = null; DK.toggle(ui.toast, 'is-visible', false); }, 3500);
    }
    function showToastText() {
        if (!ui.toast.textContent) { return; }
        var panel = dialog('', ui.toast.textContent), actions = h('div.dk-dialog-actions', null, null, panel), entry = {};
        button(actions, t('close'), function () { entry.modal.close('button'); });
        entry.modal = DK.modal.open(panel, {});
    }

    /* Theme and layout ------------------------------------------------------------------------- */
    function applyTheme(theme) {
        var signature = JSON.stringify(theme);
        if (signature === lastTheme) { return; }
        lastTheme = signature;
        var accent = DK.hex(theme.accent) || '#D98219', bg = DK.hex(theme.background) || '#101113';
        var text = DK.hex(theme.textColor) || '#E8E4DA', muted = DK.hex(theme.secondary) || '#B3AE9F';
        var border = DK.hex(theme.border) || '#4A463E', hover = DK.hex(theme.hover) || '#39352B';
        var opacity = (theme.opacity || 94) / 100, side = (theme.sidebarOpacity === undefined ? 35 : theme.sidebarOpacity) / 100;
        var size = theme.fontSize || 15, heading = theme.sectionFontSize || 18, light = DK.mix(accent, 0.28), deep = DK.mix(accent, -0.5);
        var css = [
            '.dk-window{background-color:' + DK.rgba(bg, opacity) + ';color:' + text + ';border-color:' + border + '}',
            '.dk-window-line{background-color:' + accent + '}',
            '.dk-brand-mark,.dk-section,.dk-review-mod,.dk-summary-link,.dk-crumb{color:' + light + '}',
            '.dk-row-label,.dk-title,.dk-detail-title,.dk-field,.dk-select,.dk-number,.dk-nav-item.is-selected,.dk-tab.is-selected{color:' + text + '}',
            '.dk-description,.dk-row-desc,.dk-detail-text,.dk-nav-item,.dk-tab,.dk-kv-key,.dk-dialog-text,.dk-detail-hint{color:' + muted + '}',
            '.dk-row-label{font-size:' + (size - 0.5) + 'rem}.dk-nav-item,.dk-field,.dk-select,.dk-number{font-size:' + (size - 1.5) + 'rem}',
            '.dk-section{font-size:' + Math.round(heading * 0.66) + 'rem}.dk-title{font-size:' + Math.round(heading * 1.55) + 'rem}',
            '.dk-side{background-color:rgba(0,0,0,' + side + ')}.dk-detail{background-color:rgba(0,0,0,' + (side * 0.6) + ')}',
            '.dk-top,.dk-foot,.dk-side,.dk-detail,.dk-tabs,.dk-section,.dk-row{border-color:' + DK.rgba(border, 0.7) + '}',
            '.dk-row:hover,.dk-row.is-focused,.dk-nav-item:hover,.dk-option:hover,.dk-review-row:hover{background-color:' + DK.rgba(hover, 0.55) + '}',
            '.dk-nav-item.is-selected{background-color:' + DK.rgba(accent, 0.14) + ';border-left-color:' + accent + '}',
            '.dk-nav-badge,.dk-tab-dot,.dk-summary-dot,.dk-row.is-changed .dk-row-text:before,.dk-slider-fill{background-color:' + accent + '}',
            '.dk-tab.is-selected{border-bottom-color:' + accent + '}',
            '.dk-switch.is-on{background-color:' + deep + ';border-color:' + accent + '}.dk-switch.is-on .dk-switch-knob{background-color:' + light + '}',
            '.dk-segment.is-selected,.dk-chip.is-selected,.dk-profile.is-selected,.dk-mk-item.is-selected{border-color:' + accent + ';color:' + light + '}',
            '.dk-button.is-primary{background-color:' + accent + ';border-color:' + light + '}.dk-button.is-primary:hover{background-color:' + light + '}',
            '.dk-pill.is-accent,.dk-value.is-new,.dk-option.is-selected{color:' + light + '}.dk-pill.is-accent{border-color:' + DK.rgba(accent, 0.6) + '}',
            '.dk-field:focus,.dk-number:focus,.dk-select:focus,.dk-search.is-focused,.dk-keys.is-capturing{border-color:' + accent + '}',
            '.dk-slider-thumb{border-color:' + accent + '}.dk-row.is-flash{background-color:' + DK.rgba(accent, 0.18) + '}',
            '.dk-mk-text.is-selected,.dk-mk-icon.is-selected,.dk-mk-bar.is-selected{outline-color:' + accent + '}',
            'button:focus,input:focus,textarea:focus,[tabindex]:focus{outline-color:' + DK.rgba(accent, 0.7) + '}'
        ];
        document.getElementById('dk-theme').textContent = css.join('\n');
    }
    function layout() {
        if (disposed) { return; }
        var scale = state && state.theme ? (state.theme.uiScale || 100) / 100 : 1, unit = DK.bridge.unit(), real = DK.bridge.clientRem();
        var client = {width: real.width / scale, height: real.height / scale};
        var signature = [real.width, real.height, unit, scale].join('|');
        if (signature === lastLayout) { return; }
        lastLayout = signature;
        document.documentElement.style.fontSize = (unit * scale) + 'px';
        DK.toggle(ui.window, 'is-compact', client.width < 1200);
        ui.window.style.width = Math.round(Math.min(client.width - 16, Math.max(860, Math.min(1480, client.width - 110)))) + 'rem';
        ui.window.style.height = Math.round(Math.min(client.height - 16, Math.max(540, Math.min(900, client.height - 110)))) + 'rem';
        if(layoutTimer!==null){clearTimeout(layoutTimer);}
        layoutTimer=setTimeout(function () {
            layoutTimer=null;
            if (disposed) { return; }
            ui.navScroll.update(); ui.listScroll.update();
            if (page && page.live) { page.live.redraw(); }
        }, 0);
    }

    /* Keyboard ---------------------------------------------------------------------------------- */
    function typing() {
        var node = document.activeElement, tag = node && node.tagName ? String(node.tagName).toLowerCase() : '';
        return tag === 'input' || tag === 'textarea';
    }
    function onKey(event) {
        // While Python captures a hotkey every key belongs to the capture.
        if (!state || state.capture) { return; }
        if (DK.layer.key(event)) { return; }
        var code = event.keyCode;
        if (code === 27) {
            DK.stop(event);
            if (typing() && document.activeElement === ui.searchInput && query) { ui.searchInput.value = ''; setQuery(''); return; }
            if (typing()) { document.activeElement.blur(); return; }
            send('close');
            return;
        }
        if (!event.ctrlKey || event.altKey || DK.modal.top()) { return; }
        if (code === 70) { DK.stop(event); DK.focus(ui.searchInput); if (ui.searchInput.select) { ui.searchInput.select(); } }
        else if (code === 83) { DK.stop(event); if (typing()) { document.activeElement.blur(); } send('save'); }
        else if (code === 90 && !typing()) { DK.stop(event); if (state.canUndo) { send('undo'); } }
        else if ((code === 38 || code === 40) && !typing()) { DK.stop(event); step(code === 38 ? -1 : 1); }
    }
    function step(direction) {
        var visible = order.filter(function (id) { return ui.navItems[id].node.style.display !== 'none'; });
        if (!visible.length) { return; }
        var position = visible.indexOf(state.selected);
        select(visible[(position + direction + visible.length) % visible.length]);
    }

    function dispose() {
        if (disposed) { return; }
        disposed = true;
        if (toastTimer !== null) { clearTimeout(toastTimer); }
        document.removeEventListener('keydown', onKey, true);
        window.removeEventListener('resize', layout);
        window.removeEventListener('unload',dispose);
        if(layoutTimer!==null){clearTimeout(layoutTimer);layoutTimer=null;}
        DK.layer.closeMenu(true);DK.layer.hideTip();
        ui.navScroll.dispose();ui.listScroll.dispose();
        DK.modal.closeAll();
        disposePage();
        DK.bridge.dispose();
    }

    build();
    window.addEventListener('resize', layout);
    window.addEventListener('unload', dispose);
    DK.bridge.start({schema: onSchema, state: onState, resize: layout});
    DK.app = {dispose: dispose};
}());
