(function() {
    'use strict';
    if (window.__dkHangarClock) window.__dkHangarClock.dispose();
    var disposed = false,
        cfg = {},
        timer = null,
        callbackId = null,
        resourceId = null,
        model = null,
        lastPayload = null;

    function pad(n) {
        return n < 10 ? '0' + n : String(n);
    }

    function bounded(v, fallback, min, max) {
        v = Number(v);
        return isFinite(v) ? Math.max(min, Math.min(max, v)) : fallback;
    }
    var custom = null,
        customFields = [],
        policy = null;

    function dateFormat(pattern, now) {
        var names = cfg.calendar || {},
            weekday = (now.getDay() + 6) % 7,
            month = now.getMonth();
        var days = names.days || ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        var shortDays = names.shortDays || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        var months = names.months || ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
        var shortMonths = names.shortMonths || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        var h = now.getHours(),
            values = {
                H: pad(h),
                I: pad(h % 12 || 12),
                M: pad(now.getMinutes()),
                S: pad(now.getSeconds()),
                d: pad(now.getDate()),
                m: pad(now.getMonth() + 1),
                Y: String(now.getFullYear()),
                y: pad(now.getFullYear() % 100),
                A: days[weekday],
                a: shortDays[weekday],
                B: months[month],
                b: shortMonths[month],
                p: h < 12 ? 'AM' : 'PM'
            };
        return String(pattern).replace(/%([aAbB][ul]|[HIMSdmYyaAbBp%])/g, function(all, key) {
            if (key === '%') return '%';
            var value = values[key.charAt(0)];
            return key.length === 1 ? value : key.charAt(1) === 'u' ? value.toUpperCase() : value.toLowerCase();
        });
    }

    function clockColor(value, fallback) {
        value = String(value || '');
        return /^#[0-9a-f]{6}$/i.test(value) ? value : fallback;
    }

    function clockImage(src) {
        // Only packaged game resources, such as gui/maps/driftkings/clock/clockbg.svg.
        return /^(?:coui:\/\/)?gui\/[a-zA-Z0-9_./-]+\.(png|svg|dds|webp)$/i.test(src) && src.indexOf('..') < 0 ? src.replace(/^(?!coui:\/\/)/, 'coui://') : '';
    }

    // Flash HTML text is laid out line by line: each <br> ends a line, and the enclosing
    // <textformat> gives that line its margins and the leading added after it. A negative
    // leading pulls the next line up, which puts the date beside the time.
    function richClock(parent, html, align) {
        var base = {size: 15, color: '', face: '', bold: false, italic: false, leading: 0, leftMargin: 0, rightMargin: 0},
            stack = [base],
            style = base,
            line = null;

        function inherit(attrs, type) {
            var next = {};
            for (var key in style) next[key] = style[key];
            if (attrs.color) next.color = clockColor(attrs.color, '#959688');
            if (attrs.size) next.size = bounded(attrs.size, 15, 6, 120);
            if (attrs.face) next.face = attrs.face === '$FieldFont' ? 'Arial, sans-serif' : attrs.face.replace(/[^a-zA-Z0-9 ,_-]/g, '');
            if (type === 'b') next.bold = true;
            if (type === 'i') next.italic = true;
            if (type === 'textformat') {
                if (attrs.leading !== undefined) next.leading = bounded(attrs.leading, 0, -120, 120);
                if (attrs.leftmargin !== undefined) next.leftMargin = bounded(attrs.leftmargin, 0, -1000, 1000);
                if (attrs.rightmargin !== undefined) next.rightMargin = bounded(attrs.rightmargin, 0, -1000, 1000);
            }
            return next;
        }

        function open() {
            if (line) return line;
            line = {node: document.createElement('div'), size: 0, style: style};
            line.node.className = 'dk-clock-custom__line';
            line.node.style.justifyContent = align === 'right' ? 'flex-end' : align === 'center' ? 'center' : 'flex-start';
            line.node.style.marginLeft = style.leftMargin + 'px';
            line.node.style.marginRight = style.rightMargin + 'px';
            parent.appendChild(line.node);
            return line;
        }

        function close(empty) {
            if (!line && !empty) return;
            var current = open(),
                height = Math.round((current.size || style.size) * 1.15);
            // A minimum, not a fixed height: an <img> without a size attribute must grow its line.
            current.node.style.minHeight = height + 'px';
            current.node.style.lineHeight = height + 'px';
            // Leading belongs to the line it follows; it may overlap the next one.
            current.node.style.marginBottom = style.leading + 'px';
            line = null;
        }

        function append(node, size) {
            var current = open();
            current.size = Math.max(current.size, size);
            current.node.appendChild(node);
        }

        html.split(/(<[^>]*>)/g).forEach(function(part) {
            if (!part) return;
            if (/^<\/(font|textformat|b|i)>$/i.test(part)) {
                if (stack.length > 1) stack.pop();
                style = stack[stack.length - 1];
                return;
            }
            if (/^<br\s*\/?>$/i.test(part)) {
                close(true);
                return;
            }
            var tag = /^<(font|textformat|b|i|img|tab)(\s[^>]*)?\/?>$/i.exec(part);
            if (tag) {
                var attrs = {},
                    match, re = /([a-z]+)\s*=\s*(['"])(.*?)\2/gi;
                while ((match = re.exec(tag[2] || ''))) attrs[match[1].toLowerCase()] = match[3];
                var type = tag[1].toLowerCase();
                if (type === 'img') {
                    var src = clockImage(attrs.src || '');
                    if (!src) return;
                    var image = document.createElement('img');
                    image.src = src;
                    image.alt = '';
                    ['width', 'height'].forEach(function(k) {
                        if (attrs[k]) image.style[k] = bounded(attrs[k], 0, 0, 4096) + 'px';
                    });
                    append(image, attrs.height ? bounded(attrs.height, 0, 0, 4096) / 1.15 : style.size);
                    return;
                }
                if (type === 'tab') {
                    var tab = document.createElement('span');
                    tab.textContent = '\u00a0\u00a0\u00a0\u00a0';
                    append(tab, style.size);
                    return;
                }
                style = inherit(attrs, type);
                stack.push(style);
                return;
            }
            if (part.charAt(0) !== '<') {
                var text = document.createElement('span');
                text.textContent = part;
                text.style.fontSize = style.size + 'px';
                if (style.color) text.style.color = style.color;
                if (style.face) text.style.fontFamily = style.face;
                if (style.bold) text.style.fontWeight = 'bold';
                if (style.italic) text.style.fontStyle = 'italic';
                append(text, style.size);
            }
        });
        close(false);
    }

    function shadowStyle(shadow, color) {
        var n = parseInt(color.slice(1), 16);
        var angle = bounded(shadow.angle, 0, 0, 360) * Math.PI / 180;
        var distance = bounded(shadow.distance, 0, 0, 255);
        var rgba = [
            (n >> 16) & 255,
            (n >> 8) & 255,
            n & 255,
            bounded(shadow.alpha, 100, 0, 100) / 100
        ];
        var effect = (distance * Math.cos(angle)) + 'px ' +
            (distance * Math.sin(angle)) + 'px ' +
            bounded(shadow.blur, 4, 0, 255) + 'px rgba(' + rgba.join(',') + ')';
        var copies = [];
        var count = Math.max(1, Math.min(8, Math.round(bounded(shadow.strength, 1, 0, 255))));
        for (var i = 0; i < count; i++) {
            copies.push(effect);
        }
        return copies.join(',');
    }

    function configureCustom() {
        if (custom && custom.parentNode) custom.parentNode.removeChild(custom);
        custom = null;
        customFields = [];
        if (!policy) {
            policy = document.createElement('style');
            document.body.appendChild(policy);
        }
        policy.textContent = cfg.hidePrestige ? '[class*="Information_prestige_"] { display:none; }' : '';
        // main.json clock.formats: each field is placed on the screen and drawn on its own.
        var formats = cfg.formats;
        if (!Array.isArray(formats) || formats.length > 32) return;
        custom = document.createElement('div');
        custom.className = 'dk-clock-custom';
        document.body.appendChild(custom);
        formats.forEach(function(def) {
            if (!def || typeof def.format !== 'string') return;
            var field = document.createElement('div');
            field.className = 'dk-clock-custom__field';
            var tf = def.textFormat || {},
                shadow = def.shadow || {},
                color = clockColor(shadow.color, '#000000');
            field.style.color = clockColor(tf.color, '#959688');
            field.style.textAlign = ['left', 'center', 'right'].indexOf(tf.align) >= 0 ? tf.align : 'left';
            field.style.display = 'flex';
            field.style.flexDirection = 'column';
            field.style.justifyContent = tf.valign === 'bottom' ? 'flex-end' : tf.valign === 'center' ? 'center' : 'flex-start';
            if (shadow.enabled) {
                field.style.textShadow = shadowStyle(shadow, color);
            }
            var content = document.createElement('div');
            content.className = 'dk-clock-custom__content';
            content.style.alignSelf = tf.align === 'right' ? 'flex-end' : tf.align === 'center' ? 'center' : 'flex-start';
            content.style.alignItems = content.style.alignSelf;
            field.appendChild(content);
            custom.appendChild(field);
            customFields.push({
                def: def,
                node: field,
                content: content,
                last: null
            });
        });
    }

    function tickCustom(now) {
        if (!custom) return false;
        customFields.forEach(function(entry) {
            var def = entry.def,
                field = entry.node,
                html = dateFormat(def.format, now);
            if (entry.last !== html) {
                while (entry.content.firstChild) entry.content.removeChild(entry.content.firstChild);
                richClock(entry.content, html, (def.textFormat || {}).align);
                entry.last = html;
            }
            var width = bounded(def.width, 0, 0, 4096),
                height = bounded(def.height, 0, 0, 2160),
                x = bounded(def.x, 0, -4096, 4096);
            field.style.width = width ? width + 'px' : 'auto';
            field.style.height = height ? height + 'px' : 'auto';
            var left = def.screenHAlign === 'right' ?
                window.innerWidth - (width || field.offsetWidth) :
                def.screenHAlign === 'center' ?
                    (window.innerWidth - (width || field.offsetWidth)) / 2 : 0;
            field.style.left = (left + x) + 'px';
            field.style.top = bounded(def.y, 0, -2160, 2160) + 'px';
        });
        return true;
    }

    function tick() {
        if (!disposed && cfg.visible) tickCustom(new Date());
    }

    function release() {
        if (callbackId !== null) viewEnv.removeDataChangedCallback(callbackId, resourceId);
        callbackId = null;
        resourceId = null;
        model = null;
        lastPayload = null;
    }

    function refresh() {
        if (disposed) return;
        var found = null,
            id = null;
        if (window.subViews) {
            var ids = window.subViews.ids();
            for (var i = 0; i < ids.length; i++) {
                var child = window.subViews.get(ids[i]);
                if (child && child.model && child.model.DriftkingsUI && child.model.DriftkingsUI.name === 'DriftkingsHangarClock') {
                    found = child.model;
                    id = ids[i];
                    break;
                }
            }
        }
        if (resourceId !== id) {
            release();
            resourceId = id;
            if (id !== null) callbackId = viewEnv.addDataChangedCallback('model', id, true);
        }
        model = found;
        var payload = found ? found.payload || '{}' : '{}';
        if (custom && lastPayload === payload) return;
        lastPayload = payload;
        try {
            cfg = JSON.parse(payload).config || {};
        } catch (e) {
            cfg = {};
        }
        configureCustom();
        if (custom) custom.style.display = cfg.visible ? 'block' : 'none';
        if (timer !== null) {
            clearInterval(timer);
            timer = null;
        }
        if (cfg.visible) {
            tick();
            timer = setInterval(tick, 1000);
        }
    }

    function changed() {
        if (!model || model.payload !== lastPayload) refresh();
    }

    function dispose() {
        if (disposed) return;
        disposed = true;
        if (timer !== null) {
            clearInterval(timer);
            timer = null;
        }
        engine.off('viewEnv.onDataChanged', changed);
        engine.off('subViews.onAdded', refresh);
        engine.off('subViews.onRemoved', refresh);
        release();
        window.removeEventListener('resize', tick);
        window.removeEventListener('unload', dispose);
        if (custom && custom.parentNode) custom.parentNode.removeChild(custom);
        custom = null;
        customFields = [];
        if (policy && policy.parentNode) policy.parentNode.removeChild(policy);
        policy = null;
    }
    window.__dkHangarClock = {
        dispose: dispose
    };
    engine.whenReady.then(function() {
        if (disposed) return;
        engine.on('viewEnv.onDataChanged', changed);
        engine.on('subViews.onAdded', refresh);
        engine.on('subViews.onRemoved', refresh);
        window.addEventListener('resize', tick);
        window.addEventListener('unload', dispose);
        refresh();
    });
}());
