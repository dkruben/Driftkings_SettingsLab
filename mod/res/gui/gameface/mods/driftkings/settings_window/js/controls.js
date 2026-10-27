/* DK Settings — controlos gerados a partir das definições do Python (Control.describe).
   Cada controlo devolve {node, def, set(value), sync(info), dispose()}; nunca guarda o valor
   como verdade: o estado vem sempre do Python e só ctx.commit o altera. */
(function () {
    'use strict';
    var DK = window.DK, h = DK.h, t = DK.t;
    var VALUE_TYPES = ['switch', 'checkbox', 'dropdown', 'slider', 'number', 'text', 'password', 'color', 'hotkey', 'multiselect', 'textarea', 'file', 'directory'];

    /* Row ------------------------------------------------------------------ */
    function firstLine(text) { return String(text || '').split('\n')[0]; }
    function row(def, ctx, extra) {
        var node = h('div.dk-row' + (extra ? '.' + extra : ''));
        var text = h('div.dk-row-text', null, null, node);
        var title = h('div.dk-row-title', null, null, text);
        h('span.dk-row-label', {text: def.label}, null, title);
        var timing = def.metadata && def.metadata.applyTiming;
        // Only timings that need the player to act get a badge; the detail panel shows every timing.
        if (timing === 'restart' || timing === 'view') {
            h('span.dk-badge.dk-badge-' + timing, {text: t('timing.' + timing, timing), title: t('applyTiming.' + timing, '')}, null, title);
        }
        if (def.description) { h('div.dk-row-desc', {text: firstLine(def.description)}, null, text); }
        var lock = h('div.dk-row-lock', null, null, text);
        var input = h('div.dk-row-input', null, null, node);
        var reset = null;
        if ('default' in def && def.type !== 'password') {
            reset = h('button.dk-row-reset', {title: t('resetOption', 'Reset'), onclick: function (event) {
                DK.stop(event);
                if (!DK.has(node, 'is-disabled')) { ctx.commit(def.id, DK.copy(def['default'])); }
            }}, null, node);
        }
        return {node: node, input: input, lock: lock, reset: reset};
    }
    function base(def, ctx, extra) {
        var r = row(def, ctx, extra);
        var control = {node: r.node, def: def, row: r, disabled: false, value: undefined};
        control.sync = function (info) {
            control.disabled = !!info.disabled;
            DK.toggle(r.node, 'is-disabled', control.disabled);
            DK.toggle(r.node, 'is-changed', !!info.changed);
            DK.toggle(r.node, 'is-default', 'default' in def && DK.same(info.value, def['default']));
            r.lock.textContent = control.disabled && info.lockedBy ? t('detail.depends') + ': ' + info.lockedBy : '';
            if (control.onSync) { control.onSync(info); }
        };
        control.set = function (value) { control.value = value; if (control.render) { control.render(); } };
        control.dispose = function () { if (control.onDispose) { control.onDispose(); } };
        return control;
    }
    function activate(node, fn) {
        node.addEventListener('click', function (event) { DK.stop(event); fn(); });
        node.addEventListener('keydown', function (event) { if (event.keyCode === 13 || event.keyCode === 32) { DK.stop(event); fn(); } });
    }
    function commitOnEnter(input, fn, multiline) {
        input.addEventListener('keydown', function (event) {
            if (event.keyCode === 13 && (!multiline || event.ctrlKey)) { DK.stop(event); fn(); }
            if (event.keyCode === 27 && document.activeElement === input) { input.blur(); }
        });
        input.addEventListener('blur', fn);
    }
    function invalid(input) {
        DK.toggle(input, 'is-invalid', true);
        setTimeout(function () { DK.toggle(input, 'is-invalid', false); }, 1200);
    }

    /* Toggle (switch and checkbox) ----------------------------------------- */
    function toggle(def, ctx) {
        var c = base(def, ctx, 'dk-row-toggle');
        var sw = h('div.dk-switch', {tabIndex: 0, role: 'switch'}, [h('div.dk-switch-knob')], c.row.input);
        var text = h('div.dk-switch-text', null, null, c.row.input);
        c.render = function () {
            DK.toggle(sw, 'is-on', c.value === true);
            text.textContent = c.value === true ? t('on', 'ON') : t('off', 'OFF');
        };
        activate(sw, function () { if (!c.disabled) { ctx.commit(def.id, c.value !== true); } });
        // The whole row toggles, like the client's own checkboxes.
        c.row.node.addEventListener('click', function (event) {
            if (!c.disabled && !DK.inside(event.target, sw) && !DK.has(event.target, 'dk-row-reset')) { ctx.commit(def.id, c.value !== true); }
        });
        return c;
    }

    /* Dropdown: menu, or segmented buttons for short radio groups ---------- */
    function optionLabel(def, value) {
        for (var i = 0; i < def.options.length; i++) { if (def.options[i].value === value) { return def.options[i].label; } }
        return value === undefined || value === null ? '' : String(value);
    }
    function segmented(def, ctx) {
        var c = base(def, ctx), buttons = [];
        var group = h('div.dk-segments', {role: 'radiogroup'}, null, c.row.input);
        def.options.forEach(function (option, index) {
            var b = h('button.dk-segment', {text: option.label, title: option.label}, null, group);
            b.addEventListener('click', function (event) { DK.stop(event); if (!c.disabled && option.value !== c.value) { ctx.commit(def.id, option.value); } });
            b.addEventListener('keydown', function (event) {
                var step = event.keyCode === 37 ? -1 : event.keyCode === 39 ? 1 : 0;
                if (!step || c.disabled) { return; }
                DK.stop(event);
                var next = DK.clamp(index + step, 0, def.options.length - 1);
                DK.focus(buttons[next]);
                ctx.commit(def.id, def.options[next].value);
            });
            buttons.push(b);
        });
        c.render = function () { buttons.forEach(function (b, i) { DK.toggle(b, 'is-selected', def.options[i].value === c.value); }); };
        return c;
    }
    function dropdown(def, ctx) {
        if (def.metadata && def.metadata.sourceType === 'RadioButtonGroup' && def.options.length <= 4) { return segmented(def, ctx); }
        var c = base(def, ctx);
        var images = def.preview && def.preview.images;
        var box = h('div.dk-select', {tabIndex: 0, role: 'listbox'}, null, c.row.input);
        var icon = images ? h('img.dk-select-image', null, null, box) : null;
        var label = h('span.dk-select-label', null, null, box);
        h('span.dk-select-arrow', null, null, box);
        function choose(value) { DK.layer.closeMenu(); if (value !== c.value) { ctx.commit(def.id, value); } }
        function open() {
            if (c.disabled) { return; }
            if (DK.layer.menuOpen()) { DK.layer.closeMenu(); return; }
            var list = h('div.dk-options'), current = null;
            def.options.forEach(function (option, index) {
                var item = h('button.dk-option' + (option.value === c.value ? '.is-selected' : ''), {title: option.label}, null, list);
                if (images && images[index]) { h('img.dk-option-image', {src: images[index]}, null, item); }
                h('span', {text: option.label}, null, item);
                item.addEventListener('click', function (event) { DK.stop(event); choose(option.value); });
                item.addEventListener('keydown', function (event) {
                    var step = event.keyCode === 38 ? -1 : event.keyCode === 40 ? 1 : 0;
                    if (!step) { return; }
                    DK.stop(event);
                    DK.focus(list.childNodes[DK.clamp(index + step, 0, def.options.length - 1)]);
                });
                if (option.value === c.value) { current = item; }
            });
            DK.layer.menu(box, list, null);
            DK.focus(current || list.firstChild);
            if (current) { list.parentNode.scrollTop = Math.max(0, current.offsetTop - 60); }
        }
        activate(box, open);
        box.addEventListener('keydown', function (event) {
            var step = event.keyCode === 38 ? -1 : event.keyCode === 40 ? 1 : 0;
            if (!step || c.disabled) { return; }
            DK.stop(event);
            var index = 0;
            for (var i = 0; i < def.options.length; i++) { if (def.options[i].value === c.value) { index = i; } }
            ctx.commit(def.id, def.options[DK.clamp(index + step, 0, def.options.length - 1)].value);
        });
        c.render = function () {
            label.textContent = optionLabel(def, c.value);
            if (icon) {
                var index = -1;
                for (var i = 0; i < def.options.length; i++) { if (def.options[i].value === c.value) { index = i; } }
                icon.src = index >= 0 && images[index] ? images[index] : '';
                DK.show(icon, index >= 0 && !!images[index]);
            }
        };
        return c;
    }

    /* Multiselect: toggle chips --------------------------------------------- */
    function multiselect(def, ctx) {
        var c = base(def, ctx, 'dk-row-wide'), chips = [];
        var group = h('div.dk-chips', null, null, c.row.input);
        def.options.forEach(function (option) {
            var chip = h('button.dk-chip', {text: option.label}, null, group);
            chip.addEventListener('click', function (event) {
                DK.stop(event);
                if (c.disabled) { return; }
                var next = (c.value || []).slice(), index = next.indexOf(option.value);
                if (index < 0) { next.push(option.value); } else { next.splice(index, 1); }
                ctx.commit(def.id, next);
            });
            chips.push(chip);
        });
        c.render = function () { chips.forEach(function (chip, i) { DK.toggle(chip, 'is-selected', DK.contains(c.value, def.options[i].value)); }); };
        return c;
    }

    /* Slider ----------------------------------------------------------------- */
    // Ranges with this many positions or more are too coarse to drag precisely; they get −/+ buttons.
    var WIDE_STEPS = 400;
    function slider(def, ctx) {
        var c = base(def, ctx), dragging = false, shown = def.min, fine = null;
        var wide = (def.max - def.min) / def.step >= WIDE_STEPS;
        var wrap = h('div.dk-slider' + (wide ? '.is-wide' : ''), null, null, c.row.input);
        var track = h('div.dk-slider-track', {tabIndex: 0, role: 'slider', title: t('slider.fine')}, null, wrap);
        var fill = h('div.dk-slider-fill', null, null, track);
        var thumb = h('div.dk-slider-thumb', null, null, track);
        var minus = wide ? h('button.dk-step', {text: '−', title: t('slider.step')}, null, wrap) : null;
        var field = h('input.dk-number', {type: 'text', maxLength: 12}, null, wrap);
        var plus = wide ? h('button.dk-step', {text: '+', title: t('slider.step')}, null, wrap) : null;
        if (def.unit) { h('span.dk-unit', {text: def.unit}, null, wrap); }
        function draw(value) {
            shown = value;
            var ratio = def.max > def.min ? DK.clamp((value - def.min) / (def.max - def.min), 0, 1) : 0;
            fill.style.width = (ratio * 100) + '%';
            thumb.style.left = (ratio * 100) + '%';
            if (document.activeElement !== field) { field.value = String(value); }
        }
        function commit(value) {
            value = DK.snap(value, def.min, def.max, def.step);
            draw(value);
            if (value !== c.value) { ctx.commit(def.id, value); }
        }
        // Shift + drag: fine adjustment, one step per UI unit of mouse movement from the current value.
        function fromPointer(event) {
            var value;
            if (fine) {
                var unit = parseFloat(document.documentElement.style.fontSize) || 1;
                value = DK.snap(fine.value + (event.clientX - fine.x) / unit * def.step, def.min, def.max, def.step);
            } else {
                var rect = track.getBoundingClientRect();
                var ratio = rect.width > 0 ? DK.clamp((event.clientX - rect.left) / rect.width, 0, 1) : 0;
                value = DK.snap(def.min + ratio * (def.max - def.min), def.min, def.max, def.step);
            }
            draw(value);
            if (ctx.preview) { ctx.preview(def.id, value); }
            return value;
        }
        function move(event) { fromPointer(event); }
        function up(event) {
            document.removeEventListener('mousemove', move);
            document.removeEventListener('mouseup', up);
            dragging = false;
            commit(fromPointer(event));
            fine = null;
            DK.toggle(wrap, 'is-fine', false);
        }
        track.addEventListener('mousedown', function (event) {
            if (c.disabled || event.button !== 0) { return; }
            DK.stop(event); DK.focus(track);
            dragging = true;
            fine = event.shiftKey ? {x: event.clientX, value: shown} : null;
            DK.toggle(wrap, 'is-fine', !!fine);
            fromPointer(event);
            document.addEventListener('mousemove', move);
            document.addEventListener('mouseup', up);
        });
        function nudge(direction, big) { commit(shown + direction * def.step * (big ? 10 : 1)); }
        [[minus, -1], [plus, 1]].forEach(function (pair) {
            if (!pair[0]) { return; }
            pair[0].addEventListener('click', function (event) { DK.stop(event); if (!c.disabled) { nudge(pair[1], event.shiftKey); } });
        });
        track.addEventListener('keydown', function (event) {
            if (c.disabled) { return; }
            var code = event.keyCode;
            if (code === 37 || code === 40) { DK.stop(event); nudge(-1, event.shiftKey); }
            else if (code === 39 || code === 38) { DK.stop(event); nudge(1, event.shiftKey); }
            else if (code === 36) { DK.stop(event); commit(def.min); }
            else if (code === 35) { DK.stop(event); commit(def.max); }
        });
        wrap.addEventListener('wheel', function (event) {
            if (c.disabled) { return; }
            var direction = DK.wheel(event);
            if (!direction) { return; }
            DK.stop(event);
            nudge(direction, event.shiftKey);
        });
        commitOnEnter(field, function () {
            if (c.disabled) { return; }
            var raw = String(field.value).replace(',', '.').replace(/^\s+|\s+$/g, ''), value = Number(raw);
            if (!raw || !isFinite(value) || value < def.min || value > def.max) { invalid(field); field.value = String(shown); return; }
            commit(value);
        });
        field.addEventListener('keydown', function (event) {
            if (event.keyCode === 38 || event.keyCode === 40) { DK.stop(event); if (!c.disabled) { nudge(event.keyCode === 38 ? 1 : -1, event.shiftKey); } }
        });
        c.render = function () { if (!dragging) { draw(c.value); } };
        c.onSync = function () {
            field.disabled = c.disabled; track.tabIndex = c.disabled ? -1 : 0;
            if (minus) { minus.disabled = plus.disabled = c.disabled; }
        };
        c.onDispose = function () { document.removeEventListener('mousemove', move); document.removeEventListener('mouseup', up); };
        return c;
    }

    /* Short numeric ranges: one button per value -------------------------------- */
    var CHOICE_LIMIT = 6;
    function isShortRange(def) {
        if (def.type !== 'slider' || !(def.step > 0)) { return false; }
        var count = Math.round((def.max - def.min) / def.step) + 1;
        return count >= 2 && count <= CHOICE_LIMIT && Math.abs((def.max - def.min) / def.step - (count - 1)) < 1e-6;
    }
    function choices(def, ctx) {
        var c = base(def, ctx), buttons = [], values = [];
        var group = h('div.dk-segments', {role: 'radiogroup'}, null, c.row.input);
        for (var value = def.min; value <= def.max + def.step / 2; value += def.step) { values.push(DK.snap(value, def.min, def.max, def.step)); }
        values.forEach(function (option, index) {
            var b = h('button.dk-segment', {text: option + (def.unit ? ' ' + def.unit : '')}, null, group);
            b.addEventListener('click', function (event) { DK.stop(event); if (!c.disabled && option !== c.value) { ctx.commit(def.id, option); } });
            b.addEventListener('keydown', function (event) {
                var step = event.keyCode === 37 ? -1 : event.keyCode === 39 ? 1 : 0;
                if (!step || c.disabled) { return; }
                DK.stop(event);
                var next = DK.clamp(index + step, 0, values.length - 1);
                DK.focus(buttons[next]);
                ctx.commit(def.id, values[next]);
            });
            buttons.push(b);
        });
        c.render = function () { buttons.forEach(function (b, i) { DK.toggle(b, 'is-selected', values[i] === c.value); }); };
        c.onSync = function () { buttons.forEach(function (b) { b.disabled = c.disabled; }); };
        return c;
    }

    /* Number (stepper) ------------------------------------------------------- */
    function number(def, ctx) {
        var c = base(def, ctx);
        var wrap = h('div.dk-stepper', null, null, c.row.input);
        var minus = h('button.dk-step', {text: '−'}, null, wrap);
        var field = h('input.dk-number', {type: 'text', maxLength: 12}, null, wrap);
        var plus = h('button.dk-step', {text: '+'}, null, wrap);
        if (def.unit) { h('span.dk-unit', {text: def.unit}, null, wrap); }
        function commit(value) {
            value = DK.snap(value, def.min, def.max, def.step);
            field.value = String(value);
            if (value !== c.value) { ctx.commit(def.id, value); }
        }
        minus.addEventListener('click', function (event) { DK.stop(event); if (!c.disabled) { commit(c.value - def.step); } });
        plus.addEventListener('click', function (event) { DK.stop(event); if (!c.disabled) { commit(c.value + def.step); } });
        commitOnEnter(field, function () {
            if (c.disabled) { return; }
            var value = Number(String(field.value).replace(',', '.'));
            if (!isFinite(value) || value < def.min || value > def.max || String(field.value).replace(/\s/g, '') === '') { invalid(field); field.value = String(c.value); return; }
            commit(value);
        });
        field.addEventListener('keydown', function (event) {
            if ((event.keyCode === 38 || event.keyCode === 40) && !c.disabled) { DK.stop(event); commit(c.value + (event.keyCode === 38 ? 1 : -1) * def.step * (event.shiftKey ? 10 : 1)); }
        });
        c.render = function () { if (document.activeElement !== field) { field.value = String(c.value); } };
        c.onSync = function () { field.disabled = minus.disabled = plus.disabled = c.disabled; };
        return c;
    }

    /* Text, textarea, file and directory ------------------------------------ */
    function text(def, ctx) {
        var multiline = def.type === 'textarea';
        var c = base(def, ctx, multiline ? 'dk-row-wide' : null);
        var field = multiline ? h('textarea.dk-field.dk-textarea', {maxLength: def.maxLength || 4096}, null, c.row.input)
            : h('input.dk-field', {type: 'text', maxLength: def.maxLength || 4096, placeholder: def.placeholder}, null, c.row.input);
        if (multiline) {
            field.addEventListener('wheel', function (event) {
                var max = field.scrollHeight - field.clientHeight;
                if (max <= 0) { return; }
                field.scrollTop = DK.clamp(field.scrollTop - DK.wheel(event) * 60, 0, max);
                DK.stop(event);
            });
        }
        commitOnEnter(field, function () {
            if (!c.disabled && field.value !== (c.value || '')) { ctx.commit(def.id, field.value); }
        }, multiline);
        // Formatted text (Flash HTML and macros) is shown rendered below the field, also while typing.
        var rich = null;
        function preview(source) {
            if (!DK.richText) { return; }
            if (!rich) {
                if (!DK.richText.applies(def, source)) { return; }
                rich = h('div.dk-rich', null, null, c.node);
                DK.toggle(c.node, 'dk-row-media', true);
            }
            DK.richText.render(rich, source, {extra: ctx.sample ? ctx.sample() : null});
        }
        field.addEventListener('input', function () { preview(field.value); });
        c.render = function () {
            if (document.activeElement !== field) { field.value = c.value || ''; }
            preview(document.activeElement === field ? field.value : c.value || '');
        };
        c.onSync = function () { field.disabled = c.disabled; };
        return c;
    }

    /* Password: the stored secret never reaches the view -------------------- */
    function password(def, ctx) {
        var c = base(def, ctx);
        var field = h('input.dk-field', {type: 'password', maxLength: def.maxLength || 4096}, null, c.row.input);
        var clear = h('button.dk-button.is-small', {text: t('clearSecret', 'Clear')}, null, c.row.input);
        commitOnEnter(field, function () {
            if (!c.disabled && field.value !== '') { var next = field.value; field.value = ''; ctx.commit(def.id, next); }
        });
        clear.addEventListener('click', function (event) { DK.stop(event); if (!c.disabled) { ctx.commit(def.id, ''); } });
        c.onSync = function (info) {
            field.disabled = clear.disabled = c.disabled;
            field.placeholder = info.secretSet ? t('secretSet', '••••') : (def.placeholder || t('secretEmpty', ''));
            DK.show(clear, !!info.secretSet);
        };
        return c;
    }

    /* Colour: swatch, HEX and the palette button ---------------------------- */
    function color(def, ctx) {
        var c = base(def, ctx), alpha = 100, meta = def.metadata || {};
        var withAlpha = !!(meta.allowAlpha && meta.alphaKey);
        var wrap = h('div.dk-color', null, null, c.row.input);
        var swatch = h('button.dk-swatch', {title: t('color.open')}, [h('span.dk-swatch-fill')], wrap);
        var field = h('input.dk-field.dk-hex', {type: 'text', maxLength: 7}, null, wrap);
        var pick = h('button.dk-palette', {title: t('color.open')}, null, wrap);
        function open() {
            if (c.disabled) { return; }
            DK.colorPicker.open({value: c.value, alpha: withAlpha ? alpha : null, presets: def.presets, title: def.label, origin: pick},
                function (value, nextAlpha) {
                    if (withAlpha) {
                        if (value !== c.value || nextAlpha !== alpha) { ctx.commit(def.id, value, DK.colorPicker.toScale(nextAlpha, meta.alphaScale)); }
                    } else if (value !== c.value) { ctx.commit(def.id, value); }
                });
        }
        swatch.addEventListener('click', function (event) { DK.stop(event); open(); });
        pick.addEventListener('click', function (event) { DK.stop(event); open(); });
        commitOnEnter(field, function () {
            if (c.disabled) { return; }
            var value = DK.hex(field.value);
            if (!value) { invalid(field); field.value = c.value || ''; return; }
            if (value !== c.value) { ctx.commit(def.id, value); }
        });
        c.render = function () {
            swatch.firstChild.style.backgroundColor = c.value || 'transparent';
            swatch.firstChild.style.opacity = alpha / 100;
            if (document.activeElement !== field) { field.value = c.value || ''; }
        };
        c.onSync = function (info) {
            field.disabled = swatch.disabled = pick.disabled = c.disabled;
            if (withAlpha && info.values) { alpha = DK.colorPicker.fromScale(info.values[meta.alphaKey], meta.alphaScale); c.render(); }
        };
        return c;
    }

    /* Hotkey: captured by Python (it reads the keyboard while capturing) ---- */
    function hotkey(def, ctx) {
        var c = base(def, ctx), names = {}, capturing = false;
        var keys = h('button.dk-keys', null, null, c.row.input);
        var clear = h('button.dk-button.is-small', {text: t('clearSecret', 'Clear')}, null, c.row.input);
        function render() {
            DK.clear(keys);
            DK.toggle(keys, 'is-capturing', capturing);
            if (capturing) { h('span.dk-keys-wait', {text: t('pressKey', 'Press a key')}, null, keys); return; }
            var groups = c.value || [];
            if (!groups.length) { h('span.dk-keys-none', {text: t('noKey', 'None')}, null, keys); return; }
            groups.forEach(function (group, index) {
                if (index) { h('span.dk-keys-plus', {text: '+'}, null, keys); }
                h('span.dk-key', {text: group.map(function (code) { return names[String(code)] || String(code); }).join(' / ')}, null, keys);
            });
        }
        keys.addEventListener('click', function (event) { DK.stop(event); if (!c.disabled && !capturing) { ctx.capture(def.id); } });
        clear.addEventListener('click', function (event) { DK.stop(event); if (!c.disabled) { ctx.commit(def.id, []); } });
        c.render = render;
        c.onSync = function (info) {
            names = info.keyNames || {};
            capturing = !!info.capturing;
            keys.disabled = clear.disabled = c.disabled;
            DK.show(clear, !!(c.value && c.value.length) && !capturing);
            render();
        };
        return c;
    }

    /* Action button and layout elements ------------------------------------- */
    function action(def, ctx) {
        var node = h('div.dk-row.dk-row-action');
        h('div.dk-row-text', null, [h('div.dk-row-title', null, [h('span.dk-row-label', {text: def.description ? def.label : ''})])], node);
        var b = h('button.dk-button', {text: def.text || def.label}, null, h('div.dk-row-input', null, null, node));
        var control = {node: node, def: def, set: function () {}, dispose: function () {}, disabled: false};
        control.sync = function (info) { control.disabled = !!info.disabled; b.disabled = control.disabled; DK.toggle(node, 'is-disabled', control.disabled); };
        b.addEventListener('click', function (event) { DK.stop(event); if (!control.disabled) { ctx.action(def.id); } });
        return control;
    }
    function layout(def) {
        var node = def.type === 'section' ? h('div.dk-section', null, [h('span', {text: def.label})])
            : def.type === 'separator' ? h('div.dk-separator') : h('div.dk-note', {text: def.label});
        return {node: node, def: def, set: function () {}, sync: function () {}, dispose: function () {}};
    }

    /* Media previews ---------------------------------------------------------- */
    function withImage(control) {
        var box = h('div.dk-media', null, null, control.node);
        var img = h('img.dk-media-image', null, null, box);
        var missing = h('div.dk-media-missing', {text: t('image.unavailable', '—')}, null, box);
        var last = null;
        img.addEventListener('load', function () { DK.show(img, !!last); DK.show(missing, !last); });
        img.addEventListener('error', function () { DK.show(img, false); DK.show(missing, true); });
        var sync = control.sync;
        control.sync = function (info) {
            sync(info);
            if (info.preview === last) { return; }
            last = info.preview || '';
            DK.show(img, false); DK.show(missing, !last);
            img.src = last;
        };
        DK.toggle(control.node, 'dk-row-media', true);
        return control;
    }
    function withAudio(control, ctx) {
        var bar = h('div.dk-media-actions', null, null, control.node);
        ['play', 'stop'].forEach(function (name) {
            var b = h('button.dk-button.is-small', {text: t('sound.' + name, name)}, null, bar);
            // Auditioning is allowed even when the sound itself is disabled in battle.
            b.addEventListener('click', function (event) { DK.stop(event); ctx.action(control.def.preview[name]); });
        });
        DK.toggle(control.node, 'dk-row-media', true);
        return control;
    }

    var FACTORIES = {
        'switch': toggle, checkbox: toggle, dropdown: dropdown, multiselect: multiselect, slider: slider, number: number,
        text: text, textarea: text, file: text, directory: text, password: password, color: color, hotkey: hotkey, button: action
    };
    DK.controls = {
        VALUE_TYPES: VALUE_TYPES,
        isValue: function (def) { return VALUE_TYPES.indexOf(def.type) >= 0; },
        create: function (def, ctx) {
            var factory = isShortRange(def) ? choices : FACTORIES[def.type];
            var control = factory ? factory(def, ctx) : layout(def);
            if (def.preview && def.preview.kind === 'image') { control = withImage(control); }
            else if (def.preview && def.preview.kind === 'audio') { control = withAudio(control, ctx); }
            return control;
        }
    };
}());
