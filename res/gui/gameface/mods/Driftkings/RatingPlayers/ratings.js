(function () {
    'use strict';
    var FEATURE = 'DriftkingsRatingPlayers';
    if (window.__dkPlayerRatings) { window.__dkPlayerRatings.dispose(); }
    var disposed = false, node = null, resourceId = null, callbackId = null;
    var lastPayload = null, timer = null;
    var tabData = null, tabFields = [], tabStyles = [];
    var tabExtras = [], profile = null, diagnosticModel = null;
    var roster = [], discoverDirty = true, lastDiscover = -10000, observer = null;
    var readNodes = [], readStyles = [], rectNodes = [], readRects = [], currentRow = null;
    var appearanceNodes=[], appearanceValues=[];
    var lookupData = null, lookup = null;
    var suspended=false, staged=[];
    var openingFrame=null;
    var useAnimationFrame=typeof window.requestAnimationFrame==='function' && typeof window.cancelAnimationFrame==='function';
    var OPENING_ROWS_PER_FRAME=6;
    var textStyleKeys=['fontFamily','fontSize','fontWeight','fontStyle','color','lineHeight','opacity','display'];
    var appearanceKeys=['opacity','display','visibility'];
    var tokens = ['UserInfo_userNameWrapper_','UserInfo_nickname_wrapper_','UserInfo_clanTag_',
        'Player_vehicleName_','Player_kills_','Player_vehicleContour_image_','Player_vehicleContour_level_',
        'Player_vehicleType_','Player_prestigeGrade_','Player_prestigeLevel_','Player_platoon_wrapper_',
        'UserInfo_badge_','Player_playerStatus_'];
    function computed(source, keys) {
        var index=readNodes.indexOf(source);
        if (index<0) {
            index=readNodes.length; readNodes.push(source); readStyles.push({});
        }
        var snapshot=readStyles[index], nativeStyle=null;
        // Copy only the properties this consumer needs. Ancestors need opacity
        // and visibility, not a full font/transform snapshot on every poll.
        keys.forEach(function(key) {
            if (!Object.prototype.hasOwnProperty.call(snapshot,key)) {
                if (!nativeStyle) { nativeStyle=getComputedStyle(source); }
                snapshot[key]=nativeStyle[key];
            }
        });
        return snapshot;
    }
    function bounds(source) {
        var index=rectNodes.indexOf(source);
        if (index<0) { index=rectNodes.length; rectNodes.push(source); readRects.push(source.getBoundingClientRect()); }
        return readRects[index];
    }
    function findField(element,token) { return currentRow.refs[token]; }
    function selectRow(record) {
        currentRow=record; tabFields=record.fields; tabStyles=record.styles; tabExtras=record.extras;
    }
    function saveRow(record) { record.fields=tabFields; record.styles=tabStyles; record.extras=tabExtras; }
    function queueOverlay(node) {
        if (node.parentNode!==document.body && staged.indexOf(node)<0) { staged.push(node); }
    }
    function attachOverlays() {
        if (!staged.length) { return; }
        var target=document.createDocumentFragment ? document.createDocumentFragment() : document.body;
        staged.forEach(function(node) { target.appendChild(node); });
        if (staged.length && target!==document.body) { document.body.appendChild(target); }
        staged=[];
    }
    function suspendRoster() {
        if (suspended) { return; }
        roster.forEach(function(record) {
            record.fields.forEach(function(field) {
                if (field.applied && field.source.style.visibility==='hidden') { field.source.style.visibility=field.visibility; }
                field.applied=false;
                if (field.node && field.node.parentNode) { field.node.parentNode.removeChild(field.node); }
            });
            record.styles.forEach(function(style) {
                if (style.source.style[style.key]===style.after) { style.source.style[style.key]=style.before; }
            });
            record.extras.forEach(function(field) { if (field.node.parentNode) { field.node.parentNode.removeChild(field.node); } });
            record.styles=[]; record.stamp=null;
        });
        suspended=true; discoverDirty=true; lookupData=null; lookup=null;
        readNodes=[]; readStyles=[]; rectNodes=[]; readRects=[]; appearanceNodes=[]; appearanceValues=[];
    }
    function clearRow(record) {
        selectRow(record);
        tabFields.concat(tabStyles,tabExtras).forEach(function(r) { r.used=false; });
        finishTab(); saveRow(record); record.stamp=null; record.prepared=false;
    }
    function cancelOpening() {
        if (openingFrame===null) { return; }
        if (useAnimationFrame) { window.cancelAnimationFrame(openingFrame); }
        else { clearTimeout(openingFrame); }
        openingFrame=null;
    }
    function continueOpening() {
        function next() {
            openingFrame=null;
            // Read the latest model, never a payload captured before closing,
            // replacement, or a statistics update between frames.
            if (!disposed && tabData && tabData.enabled) { renderTab(tabData); }
        }
        openingFrame=useAnimationFrame ? window.requestAnimationFrame(next) : setTimeout(next,16);
    }
    function clearRoster() {
        roster.forEach(clearRow); roster=[]; discoverDirty=true; lookupData=null; lookup=null;
        suspended=false; staged=[];
        tabFields=[]; tabStyles=[]; tabExtras=[]; currentRow=null;
        readNodes=[]; readStyles=[]; rectNodes=[]; readRects=[]; appearanceNodes=[]; appearanceValues=[];
    }
    function discover(now) {
        if (!discoverDirty && now-lastDiscover<(observer ? 5000 : 1000)) { return false; }
        var next=[];
        Array.prototype.forEach.call(document.querySelectorAll('[class*="Player_base_"]'),function(element) {
            if (!/(^|\s)Player_base_[a-f0-9]+(\s|$)/.test(element.className)) { return; }
            var record=roster.filter(function(r) { return r.element===element; })[0];
            if (!record) { record={element:element,refs:{},fields:[],styles:[],extras:[],stamp:null}; }
            tokens.forEach(function(token) {
                var field=element.querySelector('[class*="'+token+'"]');
                if (record.refs[token]!==field) { record.stamp=null; }
                record.refs[token]=field;
            });
            next.push(record);
        });
        roster.forEach(function(record) { if (next.indexOf(record)<0) { clearRow(record); } });
        roster=next; discoverDirty=false; lastDiscover=now; return true;
    }
    function ownedNode(node) {
        while(node && node!==document.body) {
            if (/\bdk-tab-(roster-field|extra)\b/.test(String(node.className))) { return true; }
            node=node.parentNode;
        }
        return false;
    }
    function nativeMutations(records) {
        records.forEach(function(record) {
            if (ownedNode(record.target)) { return; }
            if (record.type==='attributes') { discoverDirty=true; return; }
            var nodes=Array.prototype.slice.call(record.addedNodes).concat(Array.prototype.slice.call(record.removedNodes));
            if (nodes.some(function(node) { return !ownedNode(node); })) { discoverDirty=true; }
        });
    }
    function appearance(source) {
        if (!source || source===document.body) { return {opacity:1,visible:true}; }
        var index=appearanceNodes.indexOf(source);
        if (index>=0) { return appearanceValues[index]; }
        var parent=appearance(source.parentNode),style=computed(source,appearanceKeys);
        var result={opacity:parent.opacity*number(style.opacity,1),
            visible:parent.visible && style.display!=='none' && style.visibility!=='hidden'};
        appearanceNodes.push(source); appearanceValues.push(result); return result;
    }
    function nativeStamp(record,cfg,ally) {
        var values=[window.innerWidth,window.innerHeight,computed(document.documentElement,['fontSize']).fontSize];
        var view=appearance(record.element); values.push(view.opacity,view.visible);
        var side=ally?'Left':'Right',refs=record.refs;
        function textStamp(source,html,anchor) {
            if (!source || typeof html!=='string' || !html) { return; }
            var rect=bounds(anchor || source),style=computed(source,textStyleKeys),parent=appearance(source.parentNode);
            values.push(rect.left,rect.top,rect.width,rect.height,style.fontFamily,style.fontSize,
                style.fontWeight,style.fontStyle,style.color,style.lineHeight,style.opacity,style.display,
                parent.opacity,parent.visible);
        }
        textStamp(refs.UserInfo_userNameWrapper_,cfg['format'+side+'Nick'],refs.UserInfo_nickname_wrapper_);
        textStamp(refs.Player_vehicleName_,cfg['format'+side+'Vehicle']);
        textStamp(refs.Player_kills_,cfg['format'+side+'Frags']);
        // Hidden clan/empty fields have no overlay geometry. Extra fields are
        // the only consumers of row bounds and the vehicle icon anchor.
        if (cfg.fields && cfg.fields.length) {
            var rect=bounds(record.element),icon=refs.Player_vehicleContour_image_;
            values.push(rect.left,rect.top,rect.width,rect.height,computed(record.element,['fontFamily']).fontFamily);
            if (icon) { values.push(bounds(icon).left); }
        }
        return {key:JSON.stringify(values),visible:view.visible,opacity:view.opacity};
    }
    function prepareStyles(record,cfg,ally) {
        var side=ally?'Left':'Right',refs=record.refs;
        function read(token,key) { if (refs[token]) { computed(refs[token],[key]); } }
        if (Number(cfg['vehicleIconOffsetX'+side])) {
            read('Player_vehicleContour_image_','transform');
            read('Player_vehicleContour_level_','transform');
            read('Player_vehicleType_','transform');
        }
        if (Number(cfg['prestigeOffsetX'+side])) { read('Player_prestigeGrade_','transform'); }
        if (Number(cfg['squadIconOffsetX'+side])) { read('Player_platoon_wrapper_','transform'); }
        if (cfg.vehicleIconAlpha!==undefined) { read('Player_vehicleContour_image_','opacity'); }
    }
    function intact(record) {
        return record.fields.every(function(r) { return r.source.style.visibility==='hidden' &&
            (r.hiddenOnly || r.node && r.node.parentNode===document.body); }) &&
            record.styles.every(function(r) { return r.source.style[r.key]===r.after; }) &&
            record.extras.every(function(r) { return r.node.parentNode===document.body; });
    }
    function indexRows(data) {
        if (lookupData===data) { return; }
        lookupData=data; lookup={left:{ids:{},names:{}},right:{ids:{},names:{}}};
        data.rows.forEach(function(row) {
            var team=lookup[row.ally?'left':'right']; team.ids[row.id]=row;
            row._dkSignature=JSON.stringify(row.cfg);
            (row.aliases || []).forEach(function(alias) {
                var key='$'+alias.replace(/\s/g,'');
                if (!team.names[key]) { team.names[key]=[]; }
                if (team.names[key].indexOf(row)<0) { team.names[key].push(row); }
            });
        });
    }
    function clock() {
        return window.performance && typeof window.performance.now === 'function' ? window.performance.now() : Date.now();
    }
    function reportProfile(reason) {
        var sample=profile; profile=null;
        if (!sample || !sample.calls || !diagnosticModel || typeof diagnosticModel.onPerformance !== 'function') { return; }
        // The native subview may already be gone during unload. Diagnostics
        // must never interrupt restoration of the TAB's fields.
        try {
            diagnosticModel.onPerformance({calls:sample.calls,totalMs:sample.ms,maxMs:sample.max,
                windowMs:Math.max(0,clock()-sample.since),rows:sample.rows,reason:reason,
                rowsDrawn:sample.drawn,rowsReused:sample.reused,searches:sample.searches});
        } catch (error) {}
    }
    function flag(value) { return !(value === false || value === null || value === undefined || value === '' || value === 0 || value === '0' || value === 'false'); }
    function number(value, fallback) { var n=Number(value); return value === null || value === undefined || !isFinite(n) ? fallback : n; }
    function localImage(value) {
        value=String(value || '').replace(/^img:\/\//,'coui://');
        return /^coui:\/\/gui\/[a-z0-9_./-]+\.(png|dds|webp)$/i.test(value) && value.indexOf('..')<0 ? value : '';
    }
    function color(value) {
        if (typeof value === 'number') { return '#'+('000000'+value.toString(16)).slice(-6); }
        value=String(value || '').replace(/^0x/,'#');
        return /^#[a-f0-9]{6}$/i.test(value) ? value : 'transparent';
    }
    function extraFields(element, fields, ally, rowOpacity) {
        if (!fields || !fields.length) { return; }
        var unit=parseFloat(computed(document.documentElement,['fontSize']).fontSize)||1;
        var row=bounds(element), icon=findField(element,'Player_vehicleContour_image_');
        var edge=icon ? bounds(icon).left : (ally ? row.left : row.left+row.width);
        // Geometry was read before writes. Account for a newly applied offset
        // without forcing another layout pass between the two teams.
        var move=tabStyles.filter(function(r) { return r.source===icon && r.key==='transform'; })[0];
        if (move) {
            if (move.used) { edge+=move.delta*unit; }
            else if (icon.style.transform===move.after) { edge-=move.offset*unit; }
        }
        fields.forEach(function(cfg,index) {
            if (cfg.visible !== undefined && !flag(cfg.visible)) { return; }
            var record=tabExtras.filter(function(r) { return r.source===element && r.index===index; })[0];
            if (!record) {
                var node=document.createElement('div'); node.className='dk-tab-extra';
                node.style.cssText='position:fixed;pointer-events:none;overflow:hidden;display:flex;flex-wrap:nowrap;align-items:center;z-index:101;';
                record={source:element,index:index,node:node}; tabExtras.push(record);
            }
            record.used=true;
            var node=record.node, width=Math.max(0,number(cfg.width,350)), height=Math.max(0,number(cfg.height,25));
            queueOverlay(node);
            var align=cfg.align || (ally?'left':'right'), style=cfg.textFormat || {};
            node.style.left=((flag(cfg.bindToIcon)?edge:(ally?row.left:row.left+row.width))+(ally?1:-1)*number(cfg.x,0)*unit-(align==='right'?width:align==='center'?width/2:0)*unit)+'px';
            node.style.top=(row.top+(number(cfg.y,0)-(cfg.valign==='bottom'?height:cfg.valign==='center'?height/2:0))*unit)+'px';
            node.style.width=width*unit+'px'; node.style.height=height*unit+'px';
            node.style.opacity=rowOpacity*Math.max(0,Math.min(1,number(cfg.alpha,100)/100));
            var signature=JSON.stringify(cfg);
            node.style.fontFamily=style.font && style.font!=='$FieldFont' ? style.font : computed(element,['fontFamily']).fontFamily;
            if (record.signature!==signature) {
                node.style.fontSize=number(style.size,13)+'rem'; node.style.color=color(style.color || '#D9D9D9');
                node.style.fontWeight=flag(style.bold)?'bold':'normal'; node.style.fontStyle=flag(style.italic)?'italic':'normal';
                node.style.textDecoration=flag(style.underline)?'underline':'none';
                node.style.justifyContent=style.align==='right'?'flex-end':style.align==='center'?'center':'flex-start';
                node.style.flexWrap=flag(cfg.wordWrap)?'wrap':'nowrap';
                node.style.backgroundColor=color(cfg.bgColor); node.style.border=cfg.borderColor===undefined?'none':'1px solid '+color(cfg.borderColor);
                node.style.transform='rotate('+number(cfg.rotation,0)+'deg) scale('+number(cfg.scaleX,1)+','+number(cfg.scaleY,1)+')';
                node.style.transformOrigin='0 0';
                var shadow=cfg.shadow;
                node.style.textShadow=shadow && shadow.enabled!==false ? '0 0 '+number(shadow.blur,number(shadow.blurX,4))+'rem '+color(shadow.color || '#000000') : 'none';
                while(node.firstChild) { node.removeChild(node.firstChild); }
                if (cfg.src) {
                    var src=localImage(cfg.src);
                    if (src) { var image=document.createElement('img'); image.src=src; image.style.width='100%'; image.style.height='100%'; node.appendChild(image); }
                } else {
                    writeRuns(node,String(cfg.format || ''));
                }
                record.signature=signature;
            }
        });
    }

    function finishTab() {
        tabExtras=tabExtras.filter(function(record) {
            if (record.used && document.body.contains(record.source)) { return true; }
            if (record.node.parentNode) { record.node.parentNode.removeChild(record.node); } return false;
        });
        tabStyles = tabStyles.filter(function (record) {
            if (record.used && document.body.contains(record.source)) { return true; }
            if (record.source.style[record.key]===record.after) { record.source.style[record.key] = record.before; }
            return false;
        });
        tabFields = tabFields.filter(function (record) {
            if (record.used && document.body.contains(record.source)) { return true; }
            if (record.applied && record.source.style.visibility==='hidden') { record.source.style.visibility = record.visibility; }
            if (record.node && record.node.parentNode) { record.node.parentNode.removeChild(record.node); }
            return false;
        });
    }
    function tabStyle(source, key, value) {
        if (!source) { return; }
        var record = tabStyles.filter(function (r) { return r.source === source && r.key === key; })[0];
        if (!record) {
            record = {source: source, key: key, before: source.style[key], base: computed(source,[key])[key]};
            tabStyles.push(record);
        }
        var owned=record.after!==undefined && source.style[key]===record.after;
        if (record.after!==undefined && !owned) {
            record.before=source.style[key]; record.base=computed(source,[key])[key];
        }
        record.delta=key==='transform' ? value-(owned ? record.offset : 0) : 0;
        record.offset=value;
        record.used = true;
        var applied=key === 'transform' ? 'translateX(' + value + 'rem) ' + (record.base === 'none' ? '' : record.base || '') : value;
        if (source.style[key]!==applied) { source.style[key]=applied; }
        record.after=source.style[key];
    }
    function tabMove(element, token, offset) {
        if (offset) { tabStyle(findField(element,token), 'transform', offset); }
    }
    function tabHidden(source) {
        if (!source) { return; }
        var record = tabFields.filter(function (r) { return r.source === source; })[0];
        if (!record) {
            record = {source: source, node: null, visibility: source.style.visibility};
            tabFields.push(record);
        }
        if (!record.applied || source.style.visibility!=='hidden') { record.visibility=source.style.visibility; }
        if (record.node && record.node.parentNode) { record.node.parentNode.removeChild(record.node); }
        record.hiddenOnly=true; record.applied=true;
        record.used = true; source.style.visibility = 'hidden';
    }
    function tabText(source, html, cfg, prefix, side, anchor) {
        if (!source || typeof html !== 'string') { return; }
        if (!html) { tabHidden(source); return; }
        // A username's width depends on its text and clan. Anchor to the fixed
        // nickname column instead, so updates never move the enemy names.
        var rect = bounds(anchor || source);
        if (!rect.width || !rect.height) { return; }
        var record = tabFields.filter(function (r) { return r.source === source; })[0];
        if (!record) {
            record={source:source,node:null,visibility:source.style.visibility}; tabFields.push(record);
        }
        if (!record.node) {
            var overlay = document.createElement('div');
            overlay.className = 'dk-tab-roster-field';
            overlay.style.cssText = 'position:fixed;pointer-events:none;white-space:nowrap;overflow:hidden;z-index:100;display:flex;flex-direction:row;flex-wrap:nowrap;align-items:center;';
            record.node=overlay;
        }
        record.used = true;
        queueOverlay(record.node); record.hiddenOnly=false;
        if (!record.applied || source.style.visibility!=='hidden') { record.visibility=source.style.visibility; }
        record.applied=true;
        var unit = parseFloat(computed(document.documentElement,['fontSize']).fontSize) || 1;
        var style = computed(source,textStyleKeys), width = Number(cfg[prefix + 'FieldWidth' + side]) * unit || rect.width;
        var left = side === 'Left', x = rect.left + (left ? 1 : -1) * (Number(cfg[prefix + 'FieldOffsetX' + side]) || 0) * unit;
        if (prefix === 'vehicle' && left || prefix === 'name' && !left) { x += rect.width - width; }
        if (prefix === 'frags') { x += (rect.width - width) / 2; }
        var node = record.node;
        node.style.left = x + 'px'; node.style.top = rect.top + 'px';
        node.style.width = width + 'px'; node.style.height = Math.max(rect.height, 20 * unit) + 'px';
        // Coherent does not provide browser-style inline flow for nested spans.
        // Use a single flex row of styled text runs, like native FormatText.
        node.style.fontFamily = style.fontFamily; node.style.fontSize = style.fontSize;
        node.style.fontWeight = style.fontWeight; node.style.fontStyle = style.fontStyle;
        node.style.color = style.color; node.style.lineHeight = style.lineHeight;
        var ancestor = source, opacity = 1, visible = true;
        while (ancestor && ancestor !== document.body) {
            var ancestorStyle = computed(ancestor,ancestor===source ? ['opacity','display'] : appearanceKeys);
            if (ancestorStyle.opacity !== '') { var alpha = Number(ancestorStyle.opacity); if (isFinite(alpha)) { opacity *= alpha; } }
            if (ancestorStyle.display === 'none' || ancestor !== source && ancestorStyle.visibility === 'hidden') { visible = false; }
            ancestor = ancestor.parentNode;
        }
        node.style.opacity = opacity;
        node.style.visibility = visible ? 'visible' : 'hidden';
        var align = prefix === 'frags' ? 'center' : (prefix === 'name' ? (left ? 'left' : 'right') : (left ? 'right' : 'left'));
        node.style.justifyContent = align === 'center' ? 'center' : align === 'right' ? 'flex-end' : 'flex-start';
        node.style.border = cfg[prefix + 'FieldShowBorder'] ? '1px solid #ffffff' : 'none';
        if (record.html !== html) {
            while (node.firstChild) { node.removeChild(node.firstChild); }
            writeRuns(node, html); record.html = html;
        }
        source.style.visibility = 'hidden';
    }
    function renderTab(data) {
        cancelOpening();
        var measuring=!!(data && data.enabled && data.diagnostics);
        var started=measuring ? clock() : 0, matched=0, drawn=0, reused=0;
        if (measuring && !profile) { profile={calls:0,ms:0,max:0,since:started,rows:0,drawn:0,reused:0,searches:0}; }
        if (data && data.enabled && !data.diagnostics) { profile=null; }
        if (!data || !data.enabled) {
            if (data && !disposed) { suspendRoster(); } else { clearRoster(); }
            reportProfile(disposed ? 'dispose' : 'hidden'); return;
        }
        suspended=false; staged=[];
        readNodes=[]; readStyles=[]; rectNodes=[]; readRects=[]; appearanceNodes=[]; appearanceValues=[];
        var searched=discover(clock());
        indexRows(data);
        var counts={left:0,right:0}, pending=[], created=0, deferred=false;
        // Read all native layout before changing any styles, avoiding alternating
        // writes and forced layout reads for every player.
        roster.forEach(function(record) {
            var element=record.element;
            if (!document.body.contains(element)) { pending.push({record:record}); discoverDirty=true; return; }
            var parent=element,ally=true;
            while(parent && parent!==document.body) {
                if (String(parent.className).indexOf('Player_right_')>=0) { ally=false; break; }
                parent=parent.parentNode;
            }
            var team=ally?'left':'right', index=counts[team]++,source=record.refs.UserInfo_userNameWrapper_;
            if (!source) { pending.push({record:record}); return; }
            var candidates=lookup[team].names['$'+source.textContent.replace(/\s/g,'')] || [];
            var id=data.order && data.order[team] && data.order[team][index];
            var row=candidates.length===1 ? candidates[0] : lookup[team].ids[id];
            if (!row || !row.cfg.enabled) { pending.push({record:record}); return; }
            // Leave native content visible until this row can be prepared.
            // Bound initial construction without slowing existing row updates.
            if (!record.prepared && created>=OPENING_ROWS_PER_FRAME) { deferred=true; return; }
            var stamp=nativeStamp(record,row.cfg,ally);
            if (!stamp.visible) { pending.push({record:record}); return; }
            matched++;
            var key=[row.id,ally,row._dkSignature,stamp.key].join('|');
            if (key===record.stamp && intact(record)) { reused++; return; }
            prepareStyles(record,row.cfg,ally);
            if (!record.prepared) { created++; }
            pending.push({record:record,row:row,ally:ally,key:key,opacity:stamp.opacity});
        });
        pending.forEach(function(entry) {
            var record=entry.record;
            if (!entry.row) { if (record.stamp!==null || record.fields.length || record.extras.length || record.styles.length) { clearRow(record); } return; }
            selectRow(record);
            tabFields.concat(tabStyles,tabExtras).forEach(function(r) { r.used=false; });
            drawRow(entry.row,entry.ally,record.element,entry.opacity);
            finishTab(); saveRow(record); record.stamp=entry.key; record.prepared=true; drawn++;
        });
        attachOverlays();
        currentRow=null;
        if (measuring) {
            var duration=Math.max(0,clock()-started); profile.calls++; profile.ms+=duration;
            profile.max=Math.max(profile.max,duration); profile.rows+=matched;
            profile.drawn+=drawn; profile.reused+=reused; profile.searches+=searched?1:0;
            if (clock()-profile.since>=5000) { reportProfile('interval'); }
        }
        if (deferred) { continueOpening(); }
    }
    function drawRow(row,ally,element,rowOpacity) {
        var side=ally?'Left':'Right',source=findField(element,'UserInfo_userNameWrapper_');
        var sign = ally ? 1 : -1, iconOffset = sign * (Number(row.cfg['vehicleIconOffsetX' + side]) || 0);
        tabMove(element, 'Player_vehicleContour_image_', iconOffset);
        tabMove(element, 'Player_vehicleContour_level_', iconOffset);
        tabMove(element, 'Player_vehicleType_', iconOffset);
        tabMove(element, 'Player_prestigeGrade_', sign * (Number(row.cfg['prestigeOffsetX' + side]) || 0));
        tabMove(element, 'Player_platoon_wrapper_', sign * (Number(row.cfg['squadIconOffsetX' + side]) || 0));
        if (row.cfg.vehicleIconAlpha !== undefined) {
            tabStyle(findField(element,'Player_vehicleContour_image_'), 'opacity', Number(row.cfg.vehicleIconAlpha) / 100);
        }
        tabText(source, row.cfg['format' + side + 'Nick'], row.cfg, 'name', side,
            findField(element,'UserInfo_nickname_wrapper_'));
        var clan = findField(element,'UserInfo_clanTag_');
        if (clan) { tabText(clan, '', {}, 'clan', side); }
        tabText(findField(element,'Player_vehicleName_'), row.cfg['format' + side + 'Vehicle'], row.cfg, 'vehicle', side);
        tabText(findField(element,'Player_kills_'), row.cfg['format' + side + 'Frags'], row.cfg, 'frags', side);
        [['removePrestigeLevel','Player_prestigeGrade_'],['removePrestigeLevel','Player_prestigeLevel_'],
         ['removeVehicleLevel','Player_vehicleContour_level_'],['removeVehicleTypeIcon','Player_vehicleType_'],
         ['removeRankBadgeIcon','UserInfo_badge_'],['removeSquadIcon','Player_platoon_wrapper_'],
         ['removePlayerStatusIcon','Player_playerStatus_']].forEach(function (entry) {
            if (row.cfg[entry[0]]) { tabHidden(findField(element,entry[1])); }
        });
        extraFields(element,row.cfg.fields,ally,rowOpacity);
    }

    function writeRuns(target,html) {
        if (!html) { return; }
        if (!/[<&]/.test(html)) {
            var run=document.createElement('span'); run.style.flexShrink='0'; run.style.whiteSpace='pre';
            run.textContent=html; target.appendChild(run); return;
        }
        var parsed=document.createElement('div'); parsed.innerHTML=html; copyRuns(parsed,target,{});
    }
    function copyRuns(source, target, inherited) {
        for (var i = 0; i < source.childNodes.length; i++) {
            var child = source.childNodes[i];
            if (child.nodeType === 3) {
                if (inherited.hidden || !child.nodeValue) { continue; }
                var run = document.createElement('span');
                run.style.flexShrink = '0'; run.style.whiteSpace = 'pre';
                Object.keys(inherited).forEach(function (key) { if (key !== 'hidden') { run.style[key] = inherited[key]; } });
                run.textContent = child.nodeValue; target.appendChild(run);
                continue;
            }
            if (child.nodeType !== 1) { continue; }
            var tag = child.tagName.toLowerCase();
            if (/^(script|style|iframe|object)$/.test(tag)) { continue; }
            if (inherited.hidden) { continue; }
            if (tag==='img') {
                var src=localImage(child.getAttribute('src'));
                if (src) {
                    var image=document.createElement('img'); image.src=src; image.style.flexShrink='0';
                    image.style.width=Math.max(0,number(child.getAttribute('width'),22))+'rem';
                    image.style.height=Math.max(0,number(child.getAttribute('height'),22))+'rem';
                    target.appendChild(image);
                }
                continue;
            }
            if (tag==='br') {
                var line=document.createElement('span'); line.style.flexBasis='100%'; line.style.height='0'; target.appendChild(line); continue;
            }
            var style = {};
            Object.keys(inherited).forEach(function (key) { style[key] = inherited[key]; });
            if (tag === 'b') { style.fontWeight = 'bold'; }
            if (tag === 'i') { style.fontStyle = 'italic'; }
            if (tag === 'u') { style.textDecoration = 'underline'; }
            if (tag === 'font') {
                var color = child.getAttribute('color'), size = child.getAttribute('size');
                var face = child.getAttribute('face'), alpha = child.getAttribute('alpha');
                if (/^#[0-9a-f]{6}$/i.test(color)) { style.color = color; }
                if (size === '0') { style.hidden = true; }
                else if (Number(size) >= 8 && Number(size) <= 40) { style.fontSize = Number(size) + 'rem'; }
                // $FieldFont means the native font, not a wider Arial substitute.
                if (face === '$FieldFont') { delete style.fontFamily; }
                else if (face && /^[a-z0-9 _-]+$/i.test(face)) { style.fontFamily = face; }
                if (/^#[0-9a-f]{2}$/i.test(alpha)) { style.opacity = (inherited.opacity === undefined ? 1 : inherited.opacity) * parseInt(alpha.slice(1), 16) / 255; }
            }
            copyRuns(child, target, style);
        }
    }

    function copyText(source, target) {
        for (var i = 0; i < source.childNodes.length; i++) {
            var child = source.childNodes[i];
            if (child.nodeType === 3) { target.appendChild(document.createTextNode(child.nodeValue)); continue; }
            if (child.nodeType !== 1) { continue; }
            var tag = child.tagName.toLowerCase();
            if (tag === 'script' || tag === 'style' || tag === 'iframe') { continue; }
            var dest = document.createElement(/^(b|i|u|br|p)$/.test(tag) ? tag : 'span');
            if (tag === 'font') {
                var color = child.getAttribute('color'), size = Number(child.getAttribute('size'));
                var face = child.getAttribute('face'), alpha = child.getAttribute('alpha');
                if (face === '$FieldFont') { dest.style.fontFamily = 'Arial'; }
                else if (face && /^[a-z0-9 _-]+$/i.test(face)) { dest.style.fontFamily = face; }
                if (/^#[0-9a-f]{2}$/i.test(alpha)) { dest.style.opacity = parseInt(alpha.slice(1), 16) / 255; }
                if (/^#[0-9a-f]{6}$/i.test(color)) { dest.style.color = color; }
                if (child.getAttribute('size') === '0') { dest.style.display = 'none'; }
                else if (size >= 8 && size <= 40) { dest.style.fontSize = size + (tabData ? 'rem' : 'px'); }
            }
            copyText(child, dest); target.appendChild(dest);
        }
    }
    function applyLayout(node, style) {
        if (!style) { return; }
        if (style.useColor && /^#[0-9a-f]{6}$/i.test(style.color)) {
            node.style.color = style.color;
            var children = node.getElementsByTagName('*');
            for (var i = 0; i < children.length; i++) { children[i].style.color = style.color; }
        }
        if (/^(left|center|right)$/.test(style.align)) { node.style.textAlign = style.align; }
        var x = Number(style.dx) || 0, y = Number(style.dy) || 0, width = Number(style.width) || 0;
        node.style.position = 'relative';
        node.style.left = Math.max(-500, Math.min(500, x)) + 'px';
        node.style.top = Math.max(-500, Math.min(500, y)) + 'px';
        if (width > 0) { node.style.width = Math.min(1000, width) + 'px'; node.style.flex = 'none'; }
    }
    function hide() {
        tabData = null; renderTab(null);
        if (node && node.parentNode) { node.parentNode.removeChild(node); }
        node = null;
    }
    function render(payload) {
        var data;
        try { data = JSON.parse(payload || '{}'); } catch (e) { data = {}; }
        if (data.screen === 'tab') { tabData = data; renderTab(data); return; }
        if (!data.enabled || !data.rows || !data.rows.some(function (row) { return row.loadingEnabled && (typeof row.loadingNick === 'string' || typeof row.loadingVehicle === 'string'); })) { hide(); return; }
        if (!node) { node = document.createElement('div'); node.id = 'dk-player-ratings'; document.body.appendChild(node); }
        while (node.firstChild) { node.removeChild(node.firstChild); }
        var title = document.createElement('div'); title.textContent = 'Player statistics'; node.appendChild(title);
        var rows = data.rows.slice().sort(function (a, b) { return Number(b.ally) - Number(a.ally) || a.vehicleID - b.vehicleID; });
        rows.forEach(function (row) {
            if (!row.loadingEnabled || (typeof row.loadingNick !== 'string' && typeof row.loadingVehicle !== 'string')) { return; }
            var line = document.createElement('div'); line.className = 'dk-rating-row';
            var name = document.createElement('span');
            if (typeof row.loadingNick === 'string') {
                var nickMarkup = document.createElement('div'); nickMarkup.innerHTML = row.loadingNick;
                copyText(nickMarkup, name);
            } else { name.textContent = row.fullName; }
            var rating = document.createElement('span');
            var parsed = document.createElement('div'); parsed.innerHTML = typeof row.loadingVehicle === 'string' ? row.loadingVehicle : '';
            copyText(parsed, rating);
            if (/^#[0-9a-f]{6}$/i.test(row.color)) { rating.style.color = row.color; }
            applyLayout(name, row.loadingNickStyle); applyLayout(rating, row.loadingVehicleStyle);
            line.appendChild(name); line.appendChild(rating); node.appendChild(line);
        });
    }
    function refresh(pollLayout) {
        if (disposed || !window.subViews) { return; }
        var ids = window.subViews.ids();
        for (var i = 0; i < ids.length; i++) {
            var subview = window.subViews.get(ids[i]), model = subview && subview.model;
            if (!model || !model.DriftkingsUI || model.DriftkingsUI.name !== FEATURE) { continue; }
            if (resourceId !== ids[i]) {
                reportProfile('dispose');
                if (callbackId !== null) { viewEnv.removeDataChangedCallback(callbackId, resourceId); }
                resourceId = ids[i]; lastPayload = null;
                callbackId = viewEnv.addDataChangedCallback('model', resourceId, true);
            }
            diagnosticModel=model;
            if (lastPayload !== model.payload) { lastPayload = model.payload; render(lastPayload); }
            // Native model events include clocks, reserves and other TAB data.
            // They must not redraw every roster field when our payload is equal.
            else if (tabData && pollLayout === true) { renderTab(tabData); }
            return;
        }
        lastPayload = null; hide(); diagnosticModel=null;
    }
    function dispose() {
        disposed = true;
        if (observer) { observer.disconnect(); observer=null; }
        if (timer !== null) { clearInterval(timer); }
        engine.off('viewEnv.onDataChanged', refresh);
        engine.off('subViews.onAdded', refresh); engine.off('subViews.onRemoved', refresh);
        if (callbackId !== null) { viewEnv.removeDataChangedCallback(callbackId, resourceId); }
        window.removeEventListener('unload', dispose); hide(); diagnosticModel=null;
    }
    window.__dkPlayerRatings = {dispose: dispose};
    engine.whenReady.then(function () {
        if (disposed) { return; }
        engine.on('viewEnv.onDataChanged', refresh);
        engine.on('subViews.onAdded', refresh); engine.on('subViews.onRemoved', refresh);
        window.addEventListener('unload', dispose);
        if (typeof window.MutationObserver==='function') {
            observer=new window.MutationObserver(nativeMutations);
            observer.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['class']});
        }
        timer = setInterval(function () { refresh(true); }, 500); refresh();
    });
}());
