/* Reusable controls built from Python definitions. Text is always set with textContent. */
(function () {
    'use strict';
    var DK = window.DK = window.DK || {};

    function handled(event) {
        if (event && event.keyCode !== undefined && event.preventDefault) { event.preventDefault(); }
        if (event && event.stopPropagation) { event.stopPropagation(); }
        if (typeof viewEnv !== 'undefined' && typeof viewEnv.setEventHandled === 'function') { viewEnv.setEventHandled(); }
    }
    function scrollWheel(event) {
        var delta = Number(event.deltaY);
        if (!isFinite(delta) || delta === 0) { return; }
        // Gameface reports positive delta for wheel-up (opposite to browser DOM).
        // Use UI units per wheel event instead of Gameface's slow native overflow scroll.
        var scale = parseFloat(document.documentElement.style.fontSize) || 1;
        var max = Math.max(0, this.scrollHeight - this.clientHeight);
        this.scrollTop = Math.max(0, Math.min(max, this.scrollTop + (delta > 0 ? -72 : 72) * scale));
        if (this.updateScrollbar) { this.updateScrollbar(); }
        if (event.preventDefault) { event.preventDefault(); }
        handled(event);
        hideTip();
    }
    function el(tag, className, text, parent) {
        var node = document.createElement(tag);
        if (className) { node.className = className; }
        if (text !== undefined && text !== null) { node.textContent = String(text); }
        if (parent) { parent.appendChild(node); }
        if (tag === 'button') { node.addEventListener('click', handled); }
        if (tag === 'textarea' || /(^| )(dk-sidebar|dk-controls|dk-popup|dk-profile-dialog)( |$)/.test(className || '')) {
            node.addEventListener('wheel', scrollWheel);
        }
        return node;
    }
    function setClass(node, name, on) {
        var parts = (node.className || '').split(' ').filter(function (part) { return part && part !== name; });
        if (on) { parts.push(name); }
        node.className = parts.join(' ');
    }
    function inside(node, container) {
        while (node) {
            if (node === container) { return true; }
            node = node.parentNode;
        }
        return false;
    }
    function decimals(step) {
        var text = String(step), dot = text.indexOf('.');
        return dot < 0 ? 0 : text.length - dot - 1;
    }
    function snap(value, def) {
        var steps = Math.round((value - def.min) / def.step);
        var result = def.min + steps * def.step;
        result = Math.max(def.min, Math.min(def.max, result));
        return parseFloat(result.toFixed(decimals(def.step)));
    }
    var normalizeHex = DK.colors.normalizeColor;
    var hexToRgb = DK.colors.hexToRgb, rgbToHex = DK.colors.rgbToHex;

    /* Popup and tooltip layer, positioned from the anchor's client rectangle. */
    var activeDrags = [];
    function cancelDrags() { activeDrags.slice().forEach(function (cancel) { cancel(); }); }
    var layer = {root: null, popup: null, anchor: null, onClose: null, tip: null};
    function closePopup() {
        if (!layer.popup) { return false; }
        cancelDrags();
        var callback = layer.onClose, origin = layer.anchor;
        if (layer.popup.parentNode) { layer.popup.parentNode.removeChild(layer.popup); }
        layer.popup = layer.anchor = layer.onClose = null;
        document.removeEventListener('mousedown', outside);
        DK.modal.focus(origin);
        if (callback) { callback(); }
        return true;
    }
    function outside(event) {
        if (layer.popup && !inside(event.target, layer.popup) && !inside(event.target, layer.anchor)) { closePopup(); }
    }
    function place(node, anchor, below) {
        var rect = anchor.getBoundingClientRect();
        var height = node.offsetHeight || 0, width = node.offsetWidth || 0;
        var top = below ? rect.bottom + 2 : rect.top - height - 6;
        if (below && top + height > window.innerHeight) { top = Math.max(0, rect.top - height - 2); }
        if (top < 0) { top = rect.bottom + 6; }
        var left = Math.max(0, Math.min(rect.left, window.innerWidth - width - 4));
        node.style.left = left + 'px';
        node.style.top = top + 'px';
    }
    function openPopup(anchor, content, onClose) {
        closePopup();
        var popup = el('div', 'dk-popup', null, layer.root);
        popup.appendChild(content);
        popup.style.minWidth = anchor.getBoundingClientRect().width + 'px';
        layer.popup = popup; layer.anchor = anchor; layer.onClose = onClose || null;
        place(popup, anchor, true);
        document.addEventListener('mousedown', outside);
        return popup;
    }
    function showTip(anchor, text) {
        hideTip();
        layer.tip = el('div', 'dk-tooltip', text, layer.root);
        place(layer.tip, anchor, false);
    }
    function hideTip() {
        if (layer.tip && layer.tip.parentNode) { layer.tip.parentNode.removeChild(layer.tip); }
        layer.tip = null;
    }

    /* Row layout shared by value controls. */
    function row(def, extraClass) {
        var node = el('div', 'dk-row' + (extraClass ? ' ' + extraClass : ''));
        var labelArea = el('div', 'dk-label-area', null, node);
        el('div', 'dk-label', def.label, labelArea);
        if (def.description) {
            var help = el('div', 'dk-help', '?', labelArea);
            help.addEventListener('mouseenter', function () { showTip(help, def.description); });
            help.addEventListener('mouseleave', hideTip);
        }
        return {node: node, input: el('div', 'dk-input-area', null, node)};
    }
    function textInput(type, def) {
        var input = document.createElement('input');
        input.type = type; input.className = 'dk-text';
        if (def.maxLength) { input.maxLength = def.maxLength; }
        if (def.placeholder) { input.placeholder = def.placeholder; }
        input.autocomplete = 'off';
        return input;
    }
    function onCommit(input, commit) {
        input.addEventListener('keydown', function (event) {
            if (event.keyCode === 13) { commit(); }
        });
        input.addEventListener('blur', commit);
    }
    function flashInvalid(input) {
        setClass(input, 'is-invalid', true);
        setTimeout(function () { setClass(input, 'is-invalid', false); }, 1200);
    }
    function base(r) {
        var state = {disabled: false};
        return {
            node: r.node, state: state,
            info: function (info) {
                state.disabled = !!info.disabled;
                setClass(r.node, 'is-disabled', state.disabled);
                setClass(r.node, 'is-changed', !!info.changed);
                if (r.node.querySelectorAll) { var inputs = r.node.querySelectorAll('input,textarea,button,[tabindex]'); for (var i = 0; i < inputs.length; i++) { inputs[i].disabled = state.disabled; if (inputs[i]._dkTab === undefined) { inputs[i]._dkTab = inputs[i].tabIndex; } inputs[i].tabIndex = state.disabled ? -1 : inputs[i]._dkTab; } }
            }
        };
    }

    function toggle(def, ctx, kind) {
        var r = row(def, 'dk-toggle-row'), api = base(r), value = false, root, text;
        if (kind === 'switch') {
            root = el('div', 'dk-switch', null, r.input);
            text = el('div', 'dk-switch-text', null, root);
            el('div', 'dk-switch-knob', null, el('div', 'dk-switch-track', null, root));
        } else {
            root = el('div', 'dk-checkbox', null, r.input);
            el('div', 'dk-checkbox-mark', null, root);
        }
        function render() {
            setClass(root, 'is-on', value);
            if (text) { text.textContent = value ? ctx.labels.on : ctx.labels.off; }
        }
        root.tabIndex = 0;
        root.addEventListener('keydown', function (event) { if (event.keyCode === 13 || event.keyCode === 32) { handled(event); if (!api.state.disabled) { value = !value; render(); ctx.commit(def.id, value); } } });
        root.addEventListener('click', function (event) {
            handled(event);
            if (api.state.disabled) { return; }
            value = !value; render(); ctx.commit(def.id, value);
        });
        api.update = function (next) { value = next === true; render(); };
        return api;
    }

    function dropdown(def, ctx) {
        var r = row(def), api = base(r), value = null;
        var box = el('div', 'dk-dropdown', null, r.input), label = el('span', null, null, box);
        el('div', 'dk-dropdown-arrow', null, box);
        function labelOf(current) {
            for (var i = 0; i < def.options.length; i++) {
                if (def.options[i].value === current) { return def.options[i].label; }
            }
            return String(current);
        }
        box.tabIndex = 0;
        box.addEventListener('keydown', function (event) {
            if (api.state.disabled || [13,27,35,36,38,40].indexOf(event.keyCode) < 0) { return; }
            handled(event);
            if (event.keyCode === 27) { closePopup(); return; }
            if (event.keyCode === 13) { box.click(); return; }
            var index = def.options.map(function (option) { return option.value; }).indexOf(value);
            index = event.keyCode === 36 ? 0 : event.keyCode === 35 ? def.options.length - 1 : Math.max(0, Math.min(def.options.length - 1, index + (event.keyCode === 38 ? -1 : 1)));
            value = def.options[index].value; label.textContent = def.options[index].label; ctx.commit(def.id, value);
        });
        box.addEventListener('click', function (event) {
            handled(event);
            if (api.state.disabled) { return; }
            if (layer.anchor === box) { closePopup(); return; }
            var list = el('div');
            def.options.forEach(function (option, index) {
                var item = el('button', 'dk-option' + (option.value === value ? ' is-selected' : ''), option.label, list);
                var source = def.preview && def.preview.images && def.preview.images[index];
                if (source) {
                    item.textContent = '';
                    setClass(item, 'dk-image-option', true);
                    var icon = el('img', 'dk-option-image', null, item);
                    icon.src = source;
                    icon.addEventListener('error', function () { icon.style.visibility = 'hidden'; });
                    el('span', null, option.label, item);
                }
                item.addEventListener('keydown', function (event) {
                    if (event.keyCode === 27) { handled(event); closePopup(); return; }
                    if ([35,36,38,40].indexOf(event.keyCode) < 0) { return; }
                    handled(event);
                    var next = event.keyCode === 36 ? 0 : event.keyCode === 35 ? def.options.length-1 : Math.max(0, Math.min(def.options.length-1, index+(event.keyCode === 38 ? -1 : 1)));
                    value = def.options[next].value; label.textContent = def.options[next].label;
                    DK.modal.focus(list.children[next]); ctx.commit(def.id, value);
                });
                item.addEventListener('click', function () {
                    closePopup();
                    if (option.value !== value) {
                        value = option.value; label.textContent = option.label; ctx.commit(def.id, value);
                    }
                });
            });
            openPopup(box, list);
        });
        api.update = function (next) { value = next; label.textContent = labelOf(next); };
        return api;
    }

    function sliderWidget(parent, def, onInput, onDone) {
        var wrap = el('div', 'dk-slider', null, parent);
        var track = el('div', 'dk-slider-track', null, wrap);
        el('div', 'dk-slider-rail', null, track);
        var fill = el('div', 'dk-slider-fill', null, track), thumb = el('div', 'dk-slider-thumb', null, track);
        var text = el('input', 'dk-slider-value', null, wrap);
        text.type = 'text';
        if (def.unit) { el('span', 'dk-unit', def.unit, wrap); }
        var widget = {track: track, value: def.min, disabled: false, dragging: false};
        widget.render = function () {
            var ratio = (widget.value - def.min) / (def.max - def.min);
            ratio = Math.max(0, Math.min(1, ratio));
            fill.style.width = (ratio * 100) + '%';
            thumb.style.left = (ratio * 100) + '%';
            if (document.activeElement !== text) { text.value = String(widget.value); }
        };
        function commitValue(next) {
            widget.value = snap(next, def);
            text.value = String(widget.value);
            widget.render();
            if (onInput) { onInput(widget.value); }
            onDone(widget.value);
        }
        onCommit(text, function () {
            if (widget.disabled) { return; }
            var raw = String(text.value).trim(), next = Number(raw.replace(',', '.'));
            if (!raw || !isFinite(next) || next < def.min || next > def.max) {
                flashInvalid(text); text.value = String(widget.value); return;
            }
            commitValue(next);
        });
        track.tabIndex = 0;
        track.addEventListener('keydown', function (event) {
            if (widget.disabled || [33,34,35,36,37,38,39,40].indexOf(event.keyCode) < 0) { return; }
            handled(event);
            if (event.preventDefault) { event.preventDefault(); }
            commitValue(event.keyCode === 36 ? def.min : event.keyCode === 35 ? def.max : widget.value +
                (event.keyCode === 37 || event.keyCode === 40 || event.keyCode === 34 ? -1 : 1) * def.step * (event.keyCode === 33 || event.keyCode === 34 ? 10 : event.shiftKey ? 5 : 1));
        });
        function fromEvent(event) {
            var rect = track.getBoundingClientRect();
            var ratio = rect.width > 0 ? (event.clientX - rect.left) / rect.width : 0;
            var next = snap(def.min + Math.max(0, Math.min(1, ratio)) * (def.max - def.min), def);
            if (next !== widget.value) { widget.value = next; widget.render(); if (onInput) { onInput(next); } }
        }
        function move(event) { fromEvent(event); }
        function cancel() {
            widget.dragging = false;
            document.removeEventListener('mousemove', move);
            document.removeEventListener('mouseup', up);
            var index = activeDrags.indexOf(cancel); if (index >= 0) { activeDrags.splice(index, 1); }
        }
        widget.dispose = cancel;
        function up(event) {
            fromEvent(event);
            cancel();
            onDone(widget.value);
        }
        track.addEventListener('mousedown', function (event) {
            if (widget.disabled) { return; }
            widget.dragging = true;
            activeDrags.push(cancel);
            fromEvent(event);
            document.addEventListener('mousemove', move);
            document.addEventListener('mouseup', up);
        });
        return widget;
    }

    function slider(def, ctx) {
        var r = row(def), api = base(r), committed = null;
        var widget = sliderWidget(r.input, def, function (value) { if (ctx.preview) { ctx.preview(def.id, value); } }, function (value) {
            if (value !== committed) { committed = value; ctx.commit(def.id, value); }
        });
        api.dispose = widget.dispose;
        var info = api.info;
        api.info = function (state) { info(state); widget.disabled = api.state.disabled; };
        api.update = function (next) {
            committed = next;
            if (!widget.dragging) { widget.value = next; widget.render(); }
        };
        return api;
    }

    function text(def, ctx) {
        var r = row(def), api = base(r), value = '';
        var input = def.type === 'textarea' ? el('textarea', 'dk-text dk-multiline') : textInput('text', def);
        r.input.appendChild(input);
        onCommit(input, function () {
            if (api.state.disabled) { return; }
            if (input.value !== value) { value = input.value; ctx.commit(def.id, value); }
        });
        api.update = function (next) {
            value = next || '';
            if (document.activeElement !== input) { input.value = value; }
        };
        return api;
    }

    function password(def, ctx) {
        var r = row(def), api = base(r);
        var input = textInput('password', def);
        var clear = el('button', 'dk-btn dk-secret-clear', ctx.labels.clearSecret);
        clear.type = 'button';
        r.input.appendChild(input); r.input.appendChild(clear);
        onCommit(input, function () {
            if (api.state.disabled) { return; }
            // The stored secret is never sent to the view; only a new value is submitted.
            if (input.value !== '') { var next = input.value; input.value = ''; ctx.commit(def.id, next); }
        });
        clear.addEventListener('click', function () { if (!api.state.disabled) { ctx.commit(def.id, ''); } });
        var info = api.info;
        api.info = function (state) {
            info(state);
            input.placeholder = def.placeholder && !state.secretSet ? def.placeholder :
                (state.secretSet ? ctx.labels.secretSet : ctx.labels.secretEmpty);
            clear.style.display = state.secretSet ? 'block' : 'none';
        };
        api.update = function () {};
        return api;
    }

    function color(def, ctx) {
        var r = row(def), api = base(r), value = '#FFFFFF', alpha = 100;
        var meta = def.metadata || {}, hasAlpha = !!(meta.allowAlpha && meta.alphaKey);
        var wrap = el('div', 'dk-color', null, r.input);
        var swatch = el('button', 'dk-color-swatch', null, wrap), input = textInput('text', {maxLength: 8});
        swatch.type = 'button'; wrap.appendChild(input);
        function show() { swatch.style.backgroundColor = value; if (document.activeElement !== input) { input.value = value; } }
        onCommit(input, function () {
            if (api.state.disabled) { return; }
            var hex = normalizeHex(input.value);
            if (!hex) { flashInvalid(input); input.value = value; return; }
            if (hex !== value) { value = hex; show(); ctx.commit(def.id, hex); }
        });
        function open() {
            if (api.state.disabled) { return; }
            var draft = value, draftAlpha = alpha, position = DK.colors.spectrumPosition(value), x = position.x, y = position.y;
            var panel = el('div', 'dk-color-picker'), area = el('div', 'dk-spectrum', null, panel);
            area.tabIndex = 0; area.setAttribute('aria-label', ctx.labels['color.area'] || 'Color spectrum');
            var canvas = el('canvas', 'dk-spectrum-canvas', null, area), cursor = el('div', 'dk-spectrum-cursor', null, area);
            canvas.width = 256; canvas.height = 192;
            try {
                var paint = canvas.getContext && canvas.getContext('2d');
                if (paint) {
                    var pixels = paint.createImageData(256,192);
                    for (var py=0; py<192; py++) { for (var px=0; px<256; px++) {
                        var rgb = hexToRgb(DK.colors.spectrum(px/255,py/191)), offset=(py*256+px)*4;
                        pixels.data[offset]=rgb[0]; pixels.data[offset+1]=rgb[1]; pixels.data[offset+2]=rgb[2]; pixels.data[offset+3]=255;
                    } }
                    paint.putImageData(pixels,0,0);
                } else { canvas.style.display='none'; }
            } catch (ignore) { canvas.style.display='none'; }
            var previews = el('div', 'dk-color-comparison', null, panel);
            function preview(label) {
                var box=el('div', '', null, previews); el('div','dk-color-title',label,box);
                return el('div','dk-color-preview dk-checker',null,box);
            }
            var current=preview(ctx.labels['color.current'] || 'Current'), next=preview(ctx.labels['color.new'] || 'New');
            var currentFill=el('div','dk-preview-fill',null,current), nextFill=el('div','dk-preview-fill',null,next);
            currentFill.style.backgroundColor=value; currentFill.style.opacity=alpha/100;
            el('div','dk-color-title','HEX',panel);
            var hexInput=textInput('text',{maxLength:8}); panel.appendChild(hexInput);
            var alphaWidget=null, alphaLabel=null, alphaLine=null;
            function render() {
                cursor.style.left=(x*100)+'%'; cursor.style.top=(y*100)+'%';
                nextFill.style.backgroundColor=draft; nextFill.style.opacity=draftAlpha/100;
                hexInput.value=draft;
                if (alphaLabel) { alphaLabel.textContent=Math.round(draftAlpha)+'%'; }
                if (alphaLine) { alphaLine.style.backgroundImage='linear-gradient(to right, transparent, '+draft+')'; }
            }
            function select(e) {
                var rect=area.getBoundingClientRect(); x=Math.max(0,Math.min(1,(e.clientX-rect.left)/Math.max(1,rect.width)));
                y=Math.max(0,Math.min(1,(e.clientY-rect.top)/Math.max(1,rect.height))); draft=DK.colors.spectrum(x,y); render();
            }
            function stop() { document.removeEventListener('mousemove',select); document.removeEventListener('mouseup',stop); }
            area.addEventListener('mousedown',function(e) { handled(e); DK.modal.focus(area); select(e); document.addEventListener('mousemove',select); document.addEventListener('mouseup',stop); });
            area.addEventListener('keydown',function(e) {
                if ([37,38,39,40].indexOf(e.keyCode)<0) { return; } handled(e);
                var step=e.shiftKey ? 0.05 : 0.005;
                x=Math.max(0,Math.min(1,x+(e.keyCode===37?-step:e.keyCode===39?step:0)));
                y=Math.max(0,Math.min(1,y+(e.keyCode===38?-step:e.keyCode===40?step:0)));
                draft=DK.colors.spectrum(x,y); render();
            });
            function readHex() { var hex=normalizeHex(hexInput.value); if (!hex) { flashInvalid(hexInput); return false; } draft=hex; position=DK.colors.spectrumPosition(draft); x=position.x; y=position.y; render(); return true; }
            onCommit(hexInput,readHex);
            if (hasAlpha) {
                el('div','dk-color-title','Alpha',panel);
                var alphaHost=el('div','dk-alpha dk-checker',null,panel);
                alphaWidget=sliderWidget(alphaHost,{min:0,max:100,step:1},function(n){ draftAlpha=n; render(); },function(){});
                alphaLine=alphaHost.querySelectorAll('.dk-slider-rail')[0];
                alphaWidget.track.setAttribute('aria-label', 'Alpha');
                alphaLabel=el('div','dk-alpha-value',null,panel);
                alphaWidget.value=draftAlpha; alphaWidget.render();
            }
            if (def.presets) {
                var presets=el('div','dk-presets',null,panel);
                def.presets.forEach(function(p) { var btn=el('button','dk-preset',null,presets); btn.style.backgroundColor=p.value; btn.title=p.label;
                    btn.addEventListener('click',function(){ draft=normalizeHex(p.value); position=DK.colors.spectrumPosition(draft); x=position.x; y=position.y; render(); }); });
            }
            var actions=el('div','dk-modal-actions',null,panel);
            el('button','dk-btn',ctx.labels.cancel || 'Cancel',actions).addEventListener('click',function(){DK.modal.close(false);});
            el('button','dk-btn dk-primary',ctx.labels.apply || 'Apply',actions).addEventListener('click',function(){if(readHex()){DK.modal.close(true);}});
            render(); DK.modal.open(panel,{origin:swatch, cleanup:function(){stop(); if(alphaWidget){alphaWidget.dispose();}}, apply:function(){
                if(draft!==value || draftAlpha!==alpha) {
                    value=draft; alpha=draftAlpha; show();
                    ctx.commit(def.id,draft,hasAlpha ? DK.colors.alphaFromUi(draftAlpha,meta.alphaScale) : undefined);
                }
            }});
        }
        swatch.addEventListener('click',open);
        api.dispose=function(){if(DK.modal.isOpen()){DK.modal.close(false);}};
        api.update=function(next){value=normalizeHex(next)||value; show();};
        var info=api.info;
        api.info=function(state){info(state); if(hasAlpha && state.values){var n=DK.colors.alphaToUi(state.values[meta.alphaKey],meta.alphaScale); alpha=n===null?100:n;}};
        return api;
    }

    function stepper(def, ctx) {
        var r=row(def), api=base(r), value=def.min, input=textInput('text',def); r.input.appendChild(input);
        function commit(n){if(api.state.disabled){return;} n=snap(n,def); if(n!==value){value=n;input.value=String(n);ctx.commit(def.id,n);}}
        onCommit(input,function(){var n=Number(input.value);if(String(input.value).trim() && isFinite(n) && n>=def.min && n<=def.max){commit(n);}else{flashInvalid(input);input.value=String(value);}});
        input.addEventListener('keydown',function(e){if(api.state.disabled || [35,36,38,40].indexOf(e.keyCode)<0){return;} handled(e);commit(e.keyCode===36?def.min:e.keyCode===35?def.max:value+(e.keyCode===38?1:-1)*def.step*(e.shiftKey?10:1));});
        [-1,1].forEach(function(direction){el('button','dk-btn dk-step',direction<0?'−':'+',r.input).addEventListener('click',function(){commit(value+direction*def.step);});});
        api.update=function(n){value=n;if(document.activeElement!==input){input.value=String(n);}}; return api;
    }
    function radio(def,ctx){
        var r=row(def),api=base(r),value=null,buttons=[];
        function choose(index){if(api.state.disabled){return;}index=Math.max(0,Math.min(def.options.length-1,index));value=def.options[index].value;render();DK.modal.focus(buttons[index]);ctx.commit(def.id,value);}
        function render(){buttons.forEach(function(b,i){setClass(b,'is-selected',def.options[i].value===value);});}
        def.options.forEach(function(option,i){var b=el('button','dk-btn dk-radio',option.label,r.input);buttons.push(b);b.addEventListener('click',function(){choose(i);});b.addEventListener('keydown',function(e){if([13,32,35,36,37,39].indexOf(e.keyCode)<0 || api.state.disabled){return;}handled(e);choose(e.keyCode===36?0:e.keyCode===35?buttons.length-1:i+(e.keyCode===37?-1:e.keyCode===39?1:0));});});
        api.update=function(n){value=n;render();};return api;
    }

    function hotkey(def, ctx) {
        var r = row(def), api = base(r), values = [], names = {}, capturing = false;
        var box = el('button', 'dk-btn', null, r.input); box.type = 'button';
        var clear = el('button', 'dk-btn dk-secret-clear', ctx.labels.clearSecret, r.input); clear.type = 'button';
        function render() {
            box.textContent = capturing ? ctx.labels.pressKey : values.map(function (group) { return group.map(function (code) { return names[String(code)] || String(code); }).join('/'); }).join(' + ') || ctx.labels.noKey;
        }
        box.addEventListener('click', function () { if (!api.state.disabled) { ctx.capture(def.id); } });
        clear.addEventListener('click', function () { if (!api.state.disabled) { ctx.commit(def.id, []); } });
        var info = api.info;
        api.info = function (state) { info(state); names = state.keyNames || {}; capturing = !!state.capture; render(); };
        api.update = function (next) { values = next || []; render(); };
        return api;
    }
    function multiselect(def, ctx) {
        var r = row(def), api = base(r), values = [], options = [];
        def.options.forEach(function (option) {
            var item = el('div', 'dk-option', option.label, r.input); options.push(item);
            item.addEventListener('click', function () {
                if (api.state.disabled) { return; }
                var index = values.indexOf(option.value); if (index < 0) { values.push(option.value); } else { values.splice(index, 1); }
                ctx.commit(def.id, values.slice());
            });
        });
        api.update = function (next) { values = next.slice(); options.forEach(function (item, index) { setClass(item, 'is-selected', values.indexOf(def.options[index].value) >= 0); }); };
        return api;
    }

    function button(def, ctx) {
        var r = row(def), api = base(r);
        var node = el('button', 'dk-btn', def.text || def.label, r.input);
        node.type = 'button';
        node.addEventListener('click', function () { if (!api.state.disabled) { ctx.action(def.id); } });
        api.update = function () {};
        return api;
    }

    function staticNode(def) {
        var node = def.type === 'section' ? el('div', 'dk-section', def.label) :
            def.type === 'separator' ? el('div', 'dk-separator') : el('div', 'dk-info', def.label);
        return {node: node, state: {}, info: function () {}, update: function () {}};
    }

    var factories = {
        'switch': function (def, ctx) { return toggle(def, ctx, 'switch'); },
        checkbox: function (def, ctx) { return toggle(def, ctx, 'checkbox'); },
        dropdown: dropdown, slider: slider, number: stepper, text: text, password: password,
        color: color, button: button, hotkey: hotkey, multiselect: multiselect, textarea: text, file: text, directory: text
    };

    function scrollbar(node, host) {
        var track = el('div', 'dk-scroll-track', null, host);
        var thumb = el('div', 'dk-scroll-thumb', null, track);
        function update() {
            var height = node.clientHeight || 0, total = node.scrollHeight || 0;
            var usable = track.clientHeight || height;
            track.style.display = total > height ? 'block' : 'none';
            var size = Math.min(usable, Math.max(24, usable * height / Math.max(1, total)));
            thumb.style.height = size + 'px';
            thumb.style.top = (Math.max(0, usable - size) * node.scrollTop / Math.max(1, total - height)) + 'px';
        }
        track.addEventListener('mousedown', function (event) {
            if (event.button !== undefined && event.button !== 0) { return; }
            handled(event);
            if (event.preventDefault) { event.preventDefault(); }
            var rect = track.getBoundingClientRect(), thumbRect = thumb.getBoundingClientRect();
            var grip = event.target === thumb ? event.clientY - thumbRect.top : thumbRect.height / 2;
            function move(e) {
                var span = Math.max(1, rect.height - thumbRect.height);
                node.scrollTop = Math.max(0, Math.min(1, (e.clientY - rect.top - grip) / span)) * Math.max(0, node.scrollHeight - node.clientHeight);
                update(); handled(e);
            }
            function end() {
                document.removeEventListener('mousemove', move);
                document.removeEventListener('mouseup', end);
                var index = activeDrags.indexOf(end);
                if (index >= 0) { activeDrags.splice(index, 1); }
            }
            activeDrags.push(end);
            document.addEventListener('mousemove', move);
            document.addEventListener('mouseup', end);
            if (event.target !== thumb) { move(event); }
        });
        node.addEventListener('scroll', update);
        node.updateScrollbar = update;
        return update;
    }
    DK.dom = {el: el, setClass: setClass, scrollbar: scrollbar};
    DK.layer = {
        init: function (root) { layer.root = root; },
        close: closePopup, hideTip: hideTip, cancelDrags: cancelDrags,
        isOpen: function () { return !!layer.popup; }
    };
    DK.controls = {
        create: function (def, ctx) {
            var factory = factories[def.type];
            if (def.metadata && def.metadata.sourceType === 'NumericStepper') { factory = stepper; }
            if (def.metadata && def.metadata.sourceType === 'RadioButtonGroup' && def.options.length <= 5) { factory = radio; }
            var api = factory ? factory(def, ctx) : staticNode(def);
            var timing = def.metadata && def.metadata.applyTiming;
            if (['live', 'battle', 'view', 'restart'].indexOf(timing) >= 0) {
                var labels = (ctx && ctx.labels) || {};
                var badge = el('div', 'dk-apply-timing dk-apply-timing--' + timing,
                    (timing === 'restart' ? '↻ ' : '• ') + (labels['timing.' + timing] || {live: 'Immediate', battle: 'Next battle', view: 'Next view opening', restart: 'Requires restart'}[timing]), api.node);
                badge.title = labels['applyTiming.' + timing] || '';
            }
            if (def.preview && def.preview.kind === 'image') {
                setClass(api.node, 'dk-media-row', true);
                var preview = el('div', 'dk-image-preview', null, api.node);
                var picture = el('img', 'dk-preview-image', null, preview);
                var missing = el('div', 'dk-preview-missing', ctx.labels['image.unavailable'], preview);
                var lastSource = null;
                picture.addEventListener('load', function () {
                    setClass(preview, 'is-empty', !lastSource);
                    picture.style.display = lastSource ? 'block' : 'none';
                    missing.style.display = lastSource ? 'none' : 'block';
                });
                picture.addEventListener('error', function () { setClass(preview, 'is-empty', true); picture.style.display = 'none'; missing.style.display = 'block'; });
                api.previewUpdate = function (source) {
                    if (source === lastSource) { return; }
                    lastSource = source;
                    setClass(preview, 'is-empty', !source);
                    picture.style.display = 'none'; missing.style.display = 'block';
                    picture.src = source || '';
                };
            } else if (def.preview && def.preview.kind === 'audio') {
                setClass(api.node, 'dk-media-row', true);
                setClass(api.node, 'dk-audio-row', true);
                var actions = el('div', 'dk-audio-actions', null, api.node);
                ['play', 'stop'].forEach(function (action) {
                    var button = el('button', 'dk-btn', ctx.labels['sound.' + action], actions);
                    button.type = 'button';
                    // Audition is independent of enabling the sound in battle.
                    // Python validates the preview action against the session.
                    button.addEventListener('click', function () { ctx.action(def.preview[action]); });
                });
            }
            return api;
        },
        normalizeHex: normalizeHex, snap: snap
    };
}());
