(function () {
    'use strict';
    var root = document.getElementById('accounts'), disposed = false, callbackId = null;
    var autoEnter = true, pendingDelete = null, current = null, frame = null, dropdown = null;
    var draft = null, formSave = null, tooltipVisible = false;
    function node(tag, text, className) {
        var element = document.createElement(tag);
        if (text !== undefined) { element.textContent = text; }
        if (className) { element.className = className; }
        return element;
    }
    function handled(event) {
        if (event) { event.preventDefault(); event.stopPropagation(); }
        viewEnv.setEventHandled();
    }
    function send(action, data) {
        if (disposed) { return; }
        var message = data || {};
        message.action = action;
        window.model.onAction({data: JSON.stringify(message)});
    }
    function button(text, action, className, disabled) {
        var element = node('div', text, 'button ' + (className || '') + (disabled ? ' disabled' : ''));
        element.setAttribute('role', 'button'); element.setAttribute('aria-label', text);
        element.setAttribute('aria-disabled', disabled ? 'true' : 'false');
        element.tabIndex = disabled ? -1 : 0;
        element.onclick = function (event) { handled(event); if (!disabled) { action(); } };
        element.onkeydown = function (event) {
            if (event.keyCode === 13 || event.keyCode === 32) { element.onclick(event); }
        };
        return element;
    }
    function checkbox(text, checked, change) {
        var control = button('', function () { checked = !checked; update(); change(checked); }, 'check');
        var mark = node('span', '', 'check-box');
        control.appendChild(mark); control.appendChild(node('span', text, 'check-label'));
        control.setAttribute('role', 'checkbox'); control.setAttribute('aria-label', text);
        function update() { mark.textContent = checked ? '\u2713' : ''; control.setAttribute('aria-checked', String(checked)); }
        update(); return control;
    }
    function tooltip(show, title, description) {
        if (!current || tooltipVisible === show) { return; }
        tooltipVisible = show;
        viewEnv.handleViewEvent({__Type: 'GFViewEventProxy', type: 1, on: show, isMouseEvent: true,
            contentID: current.tooltipContent, decoratorID: current.tooltipDecorator, targetID: 0,
            arguments: [{__Type: 'GFValueProxy', name: 'header', string: title || current.labels.title},
                        {__Type: 'GFValueProxy', name: 'body', string: description || ''}]});
    }
    function iconButton(label, icon, action, disabled, description) {
        var control = button(label, function () { tooltip(false); action(); }, 'icon-button ' + icon, disabled);
        control.textContent = '';
        control.appendChild(node('div', undefined, 'action-icon icon-' + icon));
        control.onmouseenter = function () { tooltip(true, label, description); };
        control.onmouseleave = function () { tooltip(false); };
        control.onfocus = control.onmouseenter;
        control.onblur = control.onmouseleave;
        return control;
    }
    function dimensions() {
        if (current.launcher) { return [41, 41]; }
        var screen = viewEnv.getClientSizeRem();
        var rows = (current.accounts || []).length;
        var messageHeight = current.message ? Math.min(96, Math.ceil(current.message.length / 45) * 17 + 6) : 0;
        var height = current.editing ? 350 : (rows ? 126 + rows * 74 : 170);
        if (pendingDelete !== null) { height = Math.max(230, height); }
        return [Math.min(current.editing ? 360 : 420, screen.width - 40),
                Math.min(height + messageHeight, Math.max(150, screen.height - 80))];
    }
    // Fallback during initial form creation. Python prefers the original
    // keyboardLang.x / submit.y anchors read from the active native form.
    function launcherPosition() {
        var size = viewEnv.getClientSizeRem(), x = 24, y = 80;
        if (current.canLogin) {
            var heights = [768, 1080, 1440, 2160], positions = [461, 700, 848, 1240];
            var height = Math.max(768, size.height), base = positions[3] * height / heights[3];
            for (var i = 0; i < heights.length - 1; i++) {
                if (height <= heights[i + 1]) {
                    base = positions[i] + (positions[i + 1] - positions[i]) * (height - heights[i]) / (heights[i + 1] - heights[i]);
                    break;
                }
            }
            x = size.width / 2 + 92; y = base + 98;
        }
        return {x: Math.max(0, Math.min(size.width - 41, Math.round(x))),
                y: Math.max(0, Math.min(size.height - 41, Math.round(y)))};
    }
    function layout() {
        if (disposed || !current) { return; }
        var size = dimensions();
        root.style.width = size[0] + 'rem'; root.style.height = size[1] + 'rem';
        if (frame !== null) { cancelAnimationFrame(frame); }
        // Wulf must receive the size after the document has laid out, not before
        // inserting the content. A fixed root avoids a circular 100% viewport size.
        frame = requestAnimationFrame(function () {
            frame = requestAnimationFrame(function () {
                frame = null;
                if (disposed) { return; }
                viewEnv.resizeViewPx(Math.ceil(root.scrollWidth), Math.ceil(root.scrollHeight));
                send('layout', current.launcher ? launcherPosition() : {});
            });
        });
    }
    function render() {
        if (disposed || !window.model) { return; }
        var data = JSON.parse(window.model.payload || '{}'), labels = data.labels;
        if (!labels) { return; }
        tooltip(false);
        current = data; dropdown = null; formSave = null; root.textContent = '';
        if (data.launcher) {
            var launcher = button(labels.title, function () { tooltip(false); send('open'); }, 'launcher');
            launcher.textContent = ''; launcher.onmouseenter = function () { tooltip(true, labels.title, labels.manage); };
            launcher.onmouseleave = function () { tooltip(false); };
            root.appendChild(launcher); layout(); return;
        }
        var panel = node('div', undefined, 'window'), header = node('div', undefined, 'header');
        header.appendChild(node('div', data.editing ? labels.manage : labels.title, 'title'));
        header.appendChild(button('X', function () { send('close'); }, 'close'));
        panel.appendChild(header);
        var error = node('div', data.message || '', 'error');
        panel.appendChild(error);
        if (data.editing) { editForm(panel, data, error); }
        else { draft = null; accountList(panel, data); }
        root.appendChild(panel); layout();
    }
    function serverPicker(servers, value, change) {
        var wrapper = node('div', undefined, 'picker'), selected = value, menu = node('div', undefined, 'options hidden');
        var selectedLabel = function () {
            for (var i = 0; i < servers.length; i++) { if (servers[i].id === selected) { return servers[i].label; } }
            return '-';
        };
        var toggle = button(selectedLabel() + ' \u25be', function () { menu.className = 'options'; dropdown = close; }, 'select');
        toggle.setAttribute('role', 'combobox'); toggle.setAttribute('aria-expanded', 'false');
        function close() { menu.className = 'options hidden'; toggle.setAttribute('aria-expanded', 'false'); dropdown = null; }
        function choose(id) { selected = id; toggle.textContent = selectedLabel() + ' \u25be'; change(id); close(); toggle.focus(); }
        toggle.onclick = function (event) {
            handled(event);
            if (dropdown) { close(); } else { menu.className = 'options'; toggle.setAttribute('aria-expanded', 'true'); dropdown = close; }
        };
        toggle.onkeydown = function (event) {
            if (event.keyCode === 38 || event.keyCode === 40) {
                handled(event); var index = -1;
                servers.forEach(function (server, i) { if (server.id === selected) { index = i; } });
                index = Math.max(0, Math.min(servers.length - 1, index + (event.keyCode === 40 ? 1 : -1)));
                if (servers[index]) { choose(servers[index].id); }
            } else if (event.keyCode === 13 || event.keyCode === 32) { toggle.onclick(event); }
        };
        servers.forEach(function (server) { menu.appendChild(button(server.label, function () { choose(server.id); }, 'option')); });
        menu.setAttribute('role', 'listbox');
        menu.onwheel = function (event) { menu.scrollTop += event.deltaY; handled(event); };
        wrapper.appendChild(toggle); wrapper.appendChild(menu); return wrapper;
    }
    function editForm(panel, data, error) {
        var labels = data.labels, account = data.editing, form = node('div', undefined, 'form');
        if (!draft || draft.id !== account.id) {
            draft = {id: account.id, title: account.title, email: account.email, cluster: account.cluster};
        }
        function field(label, type, value, key) {
            var wrapper = node('div', undefined, 'field'), input = node('input');
            wrapper.appendChild(node('div', label, 'field-label'));
            input.type = type; input.value = value || ''; input.setAttribute('autocomplete', 'off');
            input.setAttribute('aria-label', label); input.className = 'text-input';
            if (key) { input.oninput = function () { draft[key] = input.value; }; }
            wrapper.appendChild(input); form.appendChild(wrapper); return input;
        }
        var title = field(labels.name, 'text', draft.title, 'title');
        var email = field(labels.email, 'text', draft.email, 'email');
        var password = field(labels.password, 'password', '');
        form.appendChild(checkbox(labels.showPassword, false, function (value) { password.type = value ? 'text' : 'password'; }));
        if (account.id) { form.appendChild(node('div', labels.keepPassword, 'hint')); }
        var serverField = node('div', undefined, 'field');
        serverField.appendChild(node('div', labels.server, 'field-label'));
        serverField.appendChild(serverPicker(data.servers, draft.cluster, function (id) { draft.cluster = id; }));
        form.appendChild(serverField);
        var actions = node('div', undefined, 'form-actions');
        formSave = function () {
            var valid = true;
            [[title, !!title.value.trim()], [email, /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())],
             [password, !!account.id || !!password.value]].forEach(function (item) {
                item[0].className = 'text-input' + (item[1] ? '' : ' invalid');
                if (!item[1]) { if (valid) { item[0].focus(); } valid = false; }
            });
            if (!valid) { return; }
            draft.title = title.value; draft.email = email.value;
            send('save', {id: account.id, title: title.value, email: email.value,
                          password: password.value, cluster: draft.cluster});
            password.value = '';
        };
        actions.appendChild(button(labels.save, formSave, 'primary'));
        actions.appendChild(button(labels.cancel, function () { password.value = ''; draft = null; send('cancel'); }));
        form.appendChild(actions); panel.appendChild(form);
    }
    function accountList(panel, data) {
        var labels = data.labels, list = node('div', undefined, 'list');
        if (!data.accounts.length) { list.appendChild(node('div', labels.empty, 'hint')); }
        data.accounts.forEach(function (account) {
            var row = node('div', undefined, 'row'), actions = node('div', undefined, 'account-actions');
            var info = node('div', undefined, 'account-info');
            info.appendChild(node('div', account.title, 'name'));
            var server = node('div', undefined, 'server');
            server.appendChild(node('div', undefined, 'server-icon'));
            server.appendChild(node('span', account.server)); info.appendChild(server); row.appendChild(info);
            var blocked = pendingDelete !== null;
            actions.appendChild(iconButton(labels.enter, 'enter', function () { send('enter', {id: account.id, autoEnter: autoEnter}); },
                                          blocked || !data.canLogin || !account.available));
            actions.appendChild(iconButton(labels.edit, 'edit', function () { draft = null; send('edit', {id: account.id}); }, blocked));
            actions.appendChild(iconButton(labels.delete, 'delete', function () { pendingDelete = account.id; render(); }, blocked));
            row.appendChild(actions); list.appendChild(row);
        });
        list.onwheel = function (event) { list.scrollTop += event.deltaY; handled(event); };
        panel.appendChild(list);
        var footer = node('div', undefined, 'footer');
        footer.appendChild(checkbox(labels.autoEnter, autoEnter, function (value) { autoEnter = value; }));
        var add = button('', function () { draft = null; send('add'); }, 'add-account', pendingDelete !== null);
        add.setAttribute('aria-label', labels.add);
        add.appendChild(node('div', undefined, 'action-icon icon-add'));
        add.appendChild(node('span', labels.add)); footer.appendChild(add); panel.appendChild(footer);
        if (pendingDelete !== null) {
            var shade = node('div', undefined, 'shade'), dialog = node('div', undefined, 'confirm');
            dialog.appendChild(node('div', labels.confirmDelete, 'confirm-message'));
            var choices = node('div', undefined, 'actions');
            choices.appendChild(button(labels.delete, function () {
                var id = pendingDelete; pendingDelete = null; send('delete', {id: id, confirmed: true});
            }, 'danger'));
            choices.appendChild(button(labels.cancel, function () { pendingDelete = null; render(); }));
            dialog.appendChild(choices); shade.appendChild(dialog); panel.appendChild(shade);
        }
    }
    function keydown(event) {
        if (disposed || !current || current.launcher) { return; }
        if (event.keyCode === 27) {
            handled(event);
            if (dropdown) { dropdown(); }
            else if (pendingDelete !== null) { pendingDelete = null; render(); }
            else if (current.editing) { draft = null; send('cancel'); }
            else { send('close'); }
        } else if (event.keyCode === 13 && formSave && !dropdown) { handled(event); formSave(); }
    }
    function changed(data, indexes, ids) {
        if (!disposed && ids && ids.indexOf(callbackId) >= 0) { render(); }
    }
    function dispose() {
        if (disposed) { return; }
        tooltip(false); disposed = true;
        if (frame !== null) { cancelAnimationFrame(frame); }
        engine.off('viewEnv.onDataChanged', changed);
        engine.off('clientResized', layout); engine.off('self.onScaleUpdated', layout);
        engine.off('self.onLoaded', layout);
        if (callbackId !== null) { viewEnv.removeDataChangedCallback(callbackId, 0); }
        draft = null; formSave = null; current = null; root.textContent = '';
        window.removeEventListener('keydown', keydown); window.removeEventListener('unload', dispose);
    }
    engine.whenReady.then(function () {
        if (disposed) { return; }
        callbackId = viewEnv.addDataChangedCallback('model', 0, true);
        engine.on('viewEnv.onDataChanged', changed);
        engine.on('clientResized', layout); engine.on('self.onScaleUpdated', layout);
        engine.on('self.onLoaded', layout);
        render();
    });
    window.addEventListener('keydown', keydown); window.addEventListener('unload', dispose);
}());
