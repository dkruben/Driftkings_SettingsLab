/* DK Settings — editor dos marcadores dos veículos.
   Os marcadores vivem em cinco campos de texto JSON (markers.json e os quatro ficheiros
   vivo/destruído × normal/Alt). O editor lê esses textos, mostra uma pré-visualização,
   um formulário por elemento e o JSON em bruto, e grava pelo mesmo ctx.commit dos outros controlos. */
(function () {
    'use strict';
    var DK = window.DK, h = DK.h, t = DK.t, M=DK.vehicleMarkerModel;
    var FILES = {alive: {normal: 'markersAliveNormal', extended: 'markersAliveExtended'}, dead: {normal: 'markersDeadNormal', extended: 'markersDeadExtended'}};
    var TEAM = {ally: '#60D35A', enemy: '#F0413B'};
    // Marker numbers with a known range: [min, max, unit].
    var RANGES = {alpha: [0, 100, '%'], amount: [0, 100, '%'], size: [6, 40, 'px'], angle: [0, 360, '°'], blur: [0, 30, ''],
                  strength: [0, 10, ''], maxScale: [0, 200, '%']};
    var ICON_ELEMENTS = {actionMarker: '!', vehicleIcon: '◆', levelIcon: 'VIII', hoverMarker: '▼', vehicleStatusMarker: '●', damageIndicator: '✦'};

    function label(preview, key) { return (preview.labels && preview.labels[key]) || key; }
    function getPath(object, path) { for (var i = 0; i < path.length; i++) { if (object === null || object === undefined) { return undefined; } object = object[path[i]]; } return object; }
    function setPath(object,path,value){
        var parent=object;
        for(var i=0;i<path.length-1;i++){
            if(!parent[path[i]]||typeof parent[path[i]]!=='object'){parent[path[i]]={};}
            parent=parent[path[i]];
        }
        parent[path[path.length-1]]=value;
    }
    function refPath(value) {
        if (value && typeof value === 'object' && value.$ref && value.$ref.path) { return value.$ref.path.split('.'); }
        var match = typeof value === 'string' ? /^\$\{([\w.]+)\}$/.exec(value) : null;
        return match ? match[1].split('.') : null;
    }
    function resolve(doc, value) {
        for (var guard = 0; guard < 5; guard++) {
            var path = refPath(value);
            if (!path) { return value; }
            value = getPath(doc, path);
        }
        return value;
    }
    function create(host, mod, ctx) {
        var preview = mod.preview, bindings = preview.bindings || {}, values = {}, disabled = [], changed = [];
        var sel = {team: 'ally', state: 'alive', mode: 'normal', element: null, path: null, json: false};
        var docs = {}, texts = {}, sliders = [], current=null, awaiting=false;
        function sample(){return {group:sel.team,state:sel.state,alt:sel.mode==='extended',blind:false,hp:hp.value,distance:350,name:'Driftkings'};}
        function resolved(){
            var general=doc('markers'),raw=general?DK.copy(general.markers):{};
            raw={enabled:values[bindings.enabled]!==false,markers:raw};
            M.STATE_KEYS.forEach(function(key){raw[key]=doc(key);});
            return M.state(raw,sample(),preview.palettes);
        }
        function color(value,fallback){return DK.hex(value)||((current&&value)?DK.hex(M.text(value,current.config,sample())):null)||fallback;}
        var root = h('div.dk-markers', null, null, host);

        /* Top bar: general switches rendered as ordinary controls */
        var general = h('div.dk-markers-general', null, null, root);
        var generalControls = [];
        mod.controls.forEach(function (def) {
            if (def.type === 'textarea' || def.id === bindings.enabled) { return; }
            var control = DK.controls.create(def, ctx);
            general.appendChild(control.node);
            generalControls.push(control);
        });

        /* Selectors */
        var bar = h('div.dk-markers-bar', null, null, root);
        function segment(title, key, options) {
            var box = h('div.dk-markers-choice', null, [h('div.dk-markers-choice-label', {text: title})], bar);
            var group = h('div.dk-segments', null, null, box), buttons = {};
            options.forEach(function (option) {
                buttons[option[0]] = h('button.dk-segment', {text: option[1], onclick: function (event) {
                    DK.stop(event); sel[key] = option[0]; sel.path = null; render();
                }}, null, group);
            });
            return buttons;
        }
        var choices = {
            team: segment(t('markers.team'), 'team', [['ally', label(preview, 'ally')], ['enemy', label(preview, 'enemy')]]),
            state: segment(t('markers.state'), 'state', [['alive', label(preview, 'alive')], ['dead', label(preview, 'dead')]]),
            mode: segment(t('markers.mode'), 'mode', [['normal', t('markers.normal')], ['extended', t('markers.extended')]])
        };
        h('div.dk-spacer', null, null, bar);
        var viewButtons = h('div.dk-segments', null, null, bar);
        var formButton = h('button.dk-segment', {text: t('markers.form'), onclick: function (event) { DK.stop(event); sel.json = false; render(); }}, null, viewButtons);
        var jsonButton = h('button.dk-segment', {text: t('markers.json'), onclick: function (event) { DK.stop(event); sel.json = true; render(); }}, null, viewButtons);

        /* Body: preview + element list + form */
        var body = h('div.dk-markers-body', null, null, root);
        var stage = h('div.dk-markers-stage', null, null, body);
        var tank = h('img.dk-markers-tank', {src: DK.asset(preview.tank)}, null, stage);
        tank.addEventListener('error', function () { DK.show(tank, false); });
        var anchor = h('div.dk-markers-anchor', null, null, stage);
        var hpBox = h('div.dk-markers-hp', null, [h('span', {text: t('markers.hp')})], stage);
        var hp = {value: 75}, hpButtons = [];
        var hpGroup = h('div.dk-segments', null, null, hpBox);
        [100, 75, 40, 10].forEach(function (value) {
            hpButtons.push(h('button.dk-segment' + (value === hp.value ? '.is-selected' : ''), {text: value + '%', onclick: function (event) {
                DK.stop(event);
                hp.value = value;
                hpButtons.forEach(function (b) { DK.toggle(b, 'is-selected', b.textContent === value + '%'); });
                draw();
            }}, null, hpGroup));
        });
        var side = h('div.dk-markers-side', null, null, body);
        var list = h('div.dk-markers-list', null, null, side);
        var editor = h('div.dk-markers-editor', null, null, side);
        var editorScroll = DK.layer.scroller(editor, side);

        function fieldId(key) { return bindings[key]; }
        function doc(key) {
            var text = values[fieldId(key)];
            if (text !== texts[key]) {
                texts[key] = text;
                try { docs[key] = JSON.parse(text); } catch (error) { docs[key] = null; }
            }
            return docs[key];
        }
        function locked(key) { return DK.contains(disabled, fieldId(key)); }
        function commit(key, document) {
            var raw = texts[key] || '', ascii = !/[^\x00-\x7f]/.test(raw);
            awaiting=true;ctx.commit(fieldId(key), DK.pyJson(document, ascii));
        }

        /* Preview drawing */
        function draw() {
            DK.clear(anchor);
            var d = doc(FILES[sel.state][sel.mode]);
            var team = d && d[sel.team];
            if (!team) { return; }
            try{current=resolved();}catch(error){current=null;return;}
            var base=M.teamColor(current.config,sample());
            Object.keys(team).forEach(function (key) {
                var item = resolve(d, team[key]);
                if (key === 'textFields' && DK.isArray(item)) {
                    item.forEach(function (field, index) { text(resolve(d, field), key, index, base); });
                    return;
                }
                if (!item || typeof item !== 'object' || item.enabled === false || typeof item.x !== 'number') { return; }
                var node;
                if (key === 'healthBar') {
                    node = h('div.dk-mk-bar', null, null, anchor);
                    node.style.width = (item.width || 70) + 'px'; node.style.height = (item.height || 10) + 'px';
                    var border = item.border || {};
                    node.style.borderWidth = (border.size === undefined ? 1 : border.size) + 'px';
                    node.style.borderColor = DK.rgba(color(border.color, '#000000'), (border.alpha === undefined ? 100 : border.alpha) / 100);
                    var fill = h('div.dk-mk-fill', null, null, node);
                    fill.style.width = (sel.state==='dead'?0:hp.value) + '%';
                    fill.style.backgroundColor = DK.rgba(color(item.color, base), ((item.fill && item.fill.alpha) === undefined ? 100 : item.fill.alpha) / 100);
                    node.style.left = item.x + 'px'; node.style.top = item.y + 'px';
                } else if (key === 'contourIcon' || key === 'vehicleDist' || ICON_ELEMENTS[key]) {
                    var shown = key === 'vehicleDist' ? '350 m' : key === 'contourIcon' ? '▭' : ICON_ELEMENTS[key];
                    node = h('div.dk-mk-icon', {text: shown}, null, anchor);
                    node.style.left = item.x + 'px'; node.style.top = item.y + 'px';
                    node.style.color = color(item.color,key === 'levelIcon' ? '#F2E3B5' : base);
                } else { return; }
                node.style.opacity = (item.alpha === undefined ? 100 : item.alpha) / 100;
                node.title = label(preview, key);
                hook(node, [sel.team, key]);
            });
        }
        function text(field, key, index, base) {
            if (!field || typeof field !== 'object' || field.enabled === false) { return; }
            var format = field.textFormat || {};
            var node = h('div.dk-mk-text', null, null, anchor);
            DK.richText.render(node,M.text(field.format || field.name || '',current.config,sample()),{size:format.size||13});
            node.style.fontFamily=format.font&&format.font!=='$FieldFont'&&format.font!=='$TitleFont'?format.font:'Warhelios';
            node.style.fontStyle=format.italic?'italic':'normal';
            node.style.fontSize = (format.size || 13) + 'px';
            node.style.fontWeight = format.bold ? '700' : '400';
            node.style.color = color(format.color, '#FFFFFF');
            node.style.opacity = Number(M.text(String(field.alpha === undefined ? 100 : field.alpha),current.config,sample())) / 100;
            node.style.left = (field.x || 0) + 'px';
            node.style.top = (field.y || 0) + 'px';
            DK.toggle(node, 'is-' + (field.align || 'center'), true);
            node.title = field.name || label(preview, key);
            hook(node, [sel.team, key, index]);
        }
        function hook(node, path) {
            var selected = sel.path && sel.path.file === undefined && DK.same(sel.path.path, path.slice(0, 2));
            DK.toggle(node, 'is-selected', !!selected);
            node.addEventListener('mousedown', function (event) { DK.stop(event); sel.path = {path: path.slice(0, 2)}; render(); });
        }

        /* Element list */
        function elements() {
            var d = doc(FILES[sel.state][sel.mode]), team = d && d[sel.team];
            return team ? Object.keys(team) : [];
        }
        function renderList() {
            DK.clear(list);
            var generalItem = h('button.dk-mk-item' + (sel.path && sel.path.file === 'markers' ? '.is-selected' : ''), {text: t('markers.general')}, null, list);
            generalItem.addEventListener('click', function (event) { DK.stop(event); sel.path = {file: 'markers', path: []}; render(); });
            elements().forEach(function (key) {
                var current = sel.path && !sel.path.file && sel.path.path[1] === key;
                var item = h('button.dk-mk-item' + (current ? '.is-selected' : ''), {text: label(preview, key)}, null, list);
                item.addEventListener('click', function (event) { DK.stop(event); sel.path = {path: [sel.team, key]}; render(); });
            });
        }

        /* Generic form ------------------------------------------------------ */
        function isColorKey(key, value) { return (typeof value==='string'||value===null)&&/color$/i.test(key); }
        function field(container, document, key, path, value, fileKeyName, readOnly) {
            function save(next) { if(readOnly){return;} var draft=DK.copy(document);setPath(draft,path,next);commit(fileKeyName,draft); }
            var range = RANGES[key];
            if (typeof value === 'number' && range && value >= range[0] && value <= range[1] && value === Math.round(value)) {
                // Known bounded numbers get a slider; positions and sizes keep the free number field.
                var control = DK.controls.create({id: path.join('.'), type: 'slider', label: label(preview, key), min: range[0], max: range[1], step: 1, unit: range[2]},
                                                 {commit: function (id, next) { if (!readOnly) { save(next); } }});
                control.sync({disabled: readOnly, changed: false, value: value});
                control.set(value);
                control.node.setAttribute('data-property',fileKeyName+'.'+path.join('.'));
                DK.toggle(control.node, 'dk-mk-slider', true);
                container.appendChild(control.node);
                sliders.push(control);
                return;
            }
            var row = h('div.dk-mk-row', {'data-property':fileKeyName+'.'+path.join('.')}, [h('div.dk-mk-label', {text: label(preview, key)})], container);
            var input = h('div.dk-mk-input', null, null, row);
            if (typeof value === 'boolean') {
                var sw = h('div.dk-switch' + (value ? '.is-on' : ''), {tabIndex: 0}, [h('div.dk-switch-knob')], input);
                sw.addEventListener('click', function (event) { DK.stop(event); if (!readOnly) { save(!value); } });
                sw.addEventListener('keydown', function (event) { if (event.keyCode === 13 || event.keyCode === 32) { DK.stop(event); if (!readOnly) { save(!value); } } });
            } else if (typeof value === 'number') {
                var numberField = h('input.dk-field.dk-mk-number', {type: 'text', value: String(value), readOnly: readOnly}, null, input);
                var commitNumber = function () {
                    var next = Number(String(numberField.value).replace(',', '.'));
                    if (!isFinite(next) || String(numberField.value).replace(/\s/g, '') === '') { numberField.value = String(value); return; }
                    if (next !== value) { save(next); }
                };
                numberField.addEventListener('keydown', function (event) {
                    if (event.keyCode === 13) { DK.stop(event); commitNumber(); }
                    if ((event.keyCode === 38 || event.keyCode === 40) && !readOnly) { DK.stop(event); save(value + (event.keyCode === 38 ? 1 : -1) * (event.shiftKey ? 10 : 1)); }
                });
                numberField.addEventListener('blur', commitNumber);
            } else if (isColorKey(key, value)) {
                var swatch = h('button.dk-swatch', null, [h('span.dk-swatch-fill')], input);
                swatch.firstChild.style.backgroundColor = value || 'transparent';
                var colorField=h('input.dk-field',{type:'text',value:value||'',placeholder:label(preview,'team'),readOnly:readOnly},null,input);
                function readColor(){var next=colorField.value||null;if(next!==value){save(next);}}
                colorField.addEventListener('blur',readColor);
                colorField.addEventListener('keydown',function(event){if(event.keyCode===13){DK.stop(event);readColor();}});
                swatch.addEventListener('click', function (event) {
                    DK.stop(event);
                    if (readOnly) { return; }
                    DK.colorPicker.open({value: value || TEAM[sel.team], alpha: null, title: label(preview, key), origin: swatch}, function (next) { save(next); });
                });
                if (value !== null) { h('button.dk-button.is-small', {text: '×', title: t('clearSecret', ''), onclick: function (event) { DK.stop(event); if (!readOnly) { save(null); } }}, null, input); }
            } else if (value === null || typeof value === 'string') {
                var ref = refPath(value);
                var textField = h('input.dk-field', {type: 'text', value: value === null ? '' : value, placeholder: 'null', readOnly: readOnly}, null, input);
                var commitText = function () {
                    var next = textField.value === '' && value === null ? null : textField.value;
                    if (next !== value) { save(next); }
                };
                textField.addEventListener('keydown', function (event) { if (event.keyCode === 13) { DK.stop(event); commitText(); } });
                textField.addEventListener('blur', commitText);
                if (ref) { h('button.dk-button.is-small', {text: t('markers.editShared'), onclick: function (event) { DK.stop(event); sel.path = {path: ref, shared: true}; render(); }}, null, input); }
            } else if (DK.isArray(value)) {
                DK.toggle(row, 'is-group', true);
                var listBox = h('div.dk-mk-group', null, null, row);
                value.forEach(function (item, index) {
                    var head = h('div.dk-mk-group-head', null, [h('span', {text: DK.tf('markers.item', {n: index + 1})})], listBox);
                    h('button.dk-button.is-small', {text: t('markers.remove'), onclick: function (event) {
                        DK.stop(event); if (!readOnly) { var next=DK.copy(value);next.splice(index,1);save(next); }
                    }}, null, head);
                    if (item !== null && typeof item === 'object') { form(listBox, document, item, path.concat([index]), fileKeyName, readOnly); }
                    else { field(listBox, document, '#' + (index + 1), path.concat([index]), item, fileKeyName, readOnly); }
                });
                h('button.dk-button.is-small', {text: t('markers.add'), onclick: function (event) {
                    DK.stop(event); if (!readOnly) { var next=DK.copy(value);next.push(path[path.length-1]==='textFields'?DK.copy(M.field):value.length?DK.copy(value[value.length-1]):{});save(next); }
                }}, null, listBox);
            } else if (value && typeof value === 'object') {
                DK.toggle(row, 'is-group', true);
                if (refPath(value)) {
                    var target = refPath(value);
                    h('div.dk-mk-hint', {text: DK.tf('markers.inherits', {path: target.join('.')})}, null, row);
                    h('button.dk-button.is-small', {text: t('markers.editShared'), onclick: function (event) { DK.stop(event); sel.path = {path: target, shared: true}; render(); }}, null, row);
                } else {
                    form(h('div.dk-mk-group', null, null, row), document, value, path, fileKeyName, readOnly);
                }
            }
        }
        function form(container, document, object, path, fileKeyName, readOnly, skip) {
            if(path.join('.')==='markers.colors'&&current){object=M.merge(current.config.colors,object);}
            Object.keys(object || {}).forEach(function (key) {
                if (skip && DK.contains(skip, key)) { return; }
                field(container, document, key, path.concat([key]), object[key], fileKeyName, readOnly);
            });
        }

        function renderEditor() {
            var top = editor.scrollTop;
            sliders.forEach(function (control) { control.dispose(); });
            sliders = [];
            DK.clear(editor);
            var key = sel.path && sel.path.file === 'markers' ? 'markers' : FILES[sel.state][sel.mode];
            var d = doc(key), readOnly = locked(key);
            if (sel.json) {
                var area = h('textarea.dk-field.dk-mk-json', {value: values[fieldId(key)] || '', readOnly: readOnly}, null, editor);
                var status = h('div.dk-mk-hint', null, null, editor);
                h('button.dk-button.is-primary.is-small', {text: t('markers.apply'), onclick: function (event) {
                    DK.stop(event);
                    try { JSON.parse(area.value); } catch (error) { status.textContent = t('markers.invalid'); return; }
                    if (!readOnly) { awaiting=true;ctx.commit(fieldId(key), area.value); }
                }}, null, editor);
                editorScroll.update();
                return;
            }
            if (!d) { h('div.dk-mk-hint', {text: t('markers.invalid')}, null, editor); return; }
            if (!sel.path) { sel.path = {path: [sel.team, elements()[0]]}; }
            var path = sel.path.file === 'markers' ? [] : sel.path.path;
            var object = path.length ? getPath(d, path) : d;
            h('div.dk-mk-title', {text: sel.path.file === 'markers' ? t('markers.general') : path.join(' › ')}, null, editor);
            if (object === undefined) { return; }
            if (object !== null && typeof object === 'object' && !DK.isArray(object) && !refPath(object)) {
                form(editor, d, object, path, key, readOnly, sel.path.file === 'markers' ? ['ally', 'enemy', 'debug', 'colorRating', 'ratingType'] : null);
            } else {
                field(editor, d, path[path.length - 1], path, object, key, readOnly);
            }
            editor.scrollTop = top;
            editorScroll.update();
        }

        function render() {
            Object.keys(choices).forEach(function (name) {
                Object.keys(choices[name]).forEach(function (value) { DK.toggle(choices[name][value], 'is-selected', sel[name] === value); });
            });
            DK.toggle(formButton, 'is-selected', !sel.json);
            DK.toggle(jsonButton, 'is-selected', sel.json);
            renderList(); draw(); renderEditor();
        }

        return {
            update: function (nextValues, info) {
                var before = JSON.stringify([fieldId(FILES[sel.state][sel.mode]), values[bindings.markers]].map(function (id) { return values[id]; }));
                values = nextValues || {};
                disabled = info.disabled || []; changed = info.changed || [];
                generalControls.forEach(function (control) {
                    var id = control.def.id;
                    control.sync({disabled: DK.contains(disabled, id), changed: DK.contains(changed, id), value: values[id], values: values});
                    control.set(values[id]);
                });
                var after = JSON.stringify([fieldId(FILES[sel.state][sel.mode]), values[bindings.markers]].map(function (id) { return values[id]; }));
                if (before !== after || awaiting || !list.firstChild) { awaiting=false;render(); }
            },
            dispose: function () { editorScroll.dispose();sliders.forEach(function(control){control.dispose();}); generalControls.forEach(function (control) { control.dispose(); }); DK.remove(root); }
        };
    }

    DK.markers = {create: create};
}());
