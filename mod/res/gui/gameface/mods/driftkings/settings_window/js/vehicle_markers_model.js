/* Pure marker preview policy; shared by the visual editor and its regression tests. */
(function () {
    'use strict';
    var DK = window.DK = window.DK || {};
    function clone(value) { return JSON.parse(JSON.stringify(value)); }
    function merge(base, value) {
        var result = clone(base);
        Object.keys(value || {}).forEach(function (key) {
            result[key] = result[key] && value[key] && !Array.isArray(value[key]) && typeof value[key] === 'object' ? merge(result[key], value[key]) : clone(value[key]);
        });
        return result;
    }
    function resolve(document) {
        var budget=100000;
        function target(path,trail,depth) {
            if (typeof path!=='string' || !/^def(?:\.[A-Za-z0-9_-]+)+$/.test(path) || trail.indexOf(path)>=0) { throw new Error('Invalid or circular reference: '+path); }
            var item=document;
            path.split('.').forEach(function (key) {
                if (!item || typeof item!=='object' || !Object.prototype.hasOwnProperty.call(item,key)) { throw new Error('Unknown reference: '+path); }
                item=item[key];
            });
            return visit(item,trail.concat([path]),depth+1);
        }
        function visit(item,trail,depth) {
            budget--; if (budget<0 || depth>48) { throw new Error('Reference expansion exceeds limits'); }
            if (Array.isArray(item)) { return item.map(function (child) { return visit(child,trail,depth+1); }); }
            if (item && typeof item==='object') {
                var result={}, pointer=item.$ref;
                Object.keys(item).forEach(function (key) { if (key!=='$ref') { result[key]=visit(item[key],trail,depth+1); } });
                if (pointer!==undefined) {
                    if (typeof pointer==='object') {
                        if (!pointer || Object.keys(pointer).join()!=='path') { throw new Error('Invalid reference path'); }
                        pointer=pointer.path;
                    }
                    var base=target(pointer,trail,depth);
                    if (Object.keys(result).length && (!base || typeof base!=='object' || Array.isArray(base))) { throw new Error('Reference overrides require an object'); }
                    return Object.keys(result).length?merge(base,result):clone(base);
                }
                return result;
            }
            if (typeof item==='string' && item.slice(0,2)==='${' && item.slice(-1)==='}') { return target(item.slice(2,-1),trail,depth); }
            return item;
        }
        return visit(document,[],0);
    }
    function migrate(raw) {
        var result=clone(raw);
        if (result.schemaVersion===2) { return result; }
        ['markers','customFields'].forEach(function (key) {
            var source=result[key] || {}, converted={enabled:!!source.enabled};
            ['ally','enemy'].forEach(function (team) {
                var value=source[team] || {};
                converted[team]=value.alive || value.dead ? clone(value) : {alive:clone(value),dead:clone(source.dead || {})};
            });
            result[key]=converted;
        });
        result.schemaVersion=2; return result;
    }
    function scoped(source,sample) {
        var team=sample.group==='dead'?'enemy':sample.group, state=sample.state || (sample.group==='dead'?'dead':'alive');
        return ((source[team] || {})[state] || {})[sample.alt?'extended':'normal'];
    }
    function style(base,source,sample) {
        var common={};
        Object.keys(source || {}).forEach(function (key) { if (key!=='ally' && key!=='enemy') { common[key]=source[key]; } });
        return merge(merge(base,common),scoped(source || {},sample));
    }
    var shadow = {enabled:true,distance:0,angle:0,color:'#000000',alpha:80,blur:3,strength:2};
    var font = {font:'$FieldFont',size:13,color:null,bold:false,italic:false};
    var field = {name:'',textFormat:font,enabled:true,format:'<font size="13" color="{{c:team}}">{{vehicle}}</font>',x:-100,y:-65,width:200,height:25,alpha:100,align:'center',shadow:shadow};
    function ratingField(alt) {
        return merge(field,{name:'Rating',format:alt?'{{r}}':'\u2022',x:alt?-100:-65,y:alt?-115:-25,width:alt?200:28,height:25,
            alpha:alt?100:'{{stat-available?100|0}}',align:alt?'center':'right',textFormat:{font:'$FieldFont',size:alt?13:17,color:'{{c:xr}}'}});
    }
    var defaults = {
        enabled:true,debug:false,markers:{enabled:true},customFields:{enabled:true,ally:{},enemy:{},dead:{}},
        colors:{team:{ally:'#99CC66',enemy:'#FF7777',squad:'#FFCC66',teamKiller:'#66CCFF',dead:'#AAAAAA',unknown:'#CCCCCC'},hp:[{value:25,color:'#FF5555'},{value:50,color:'#FFAA44'},{value:75,color:'#FFDD66'},{value:100,color:'#99CC66'}],colorBlind:{enabled:true,team:{enemy:'#C48CFF',teamKiller:'#66CCFF'}}},
        def:{},turretMarkers:{highVulnerability:'*',lowVulnerability:"'",unknown:'?'},
        healthBar:{enabled:false,x:-35,y:-22,width:70,height:8,alpha:100,color:'{{c:team}}',showOnDead:false,fill:{alpha:100},gradient:{enabled:false,color:'{{c:hp}}',angle:0},background:{color:'#181818',alpha:80},border:{color:'#000000',alpha:100,width:1},shadow:shadow,damage:{enabled:false,color:'#FFDD66',alpha:65,delay:0.25,duration:0.75}},
        damageText:{enabled:false,format:'<font size="18" color="{{c:dmg}}"><b>-{{dmg}}</b></font>',blowupMessage:'<font size="18" color="{{c:dmg}}"><b>{{i18n:blownUp}}\n-{{dmg}}</b></font>',sources:{player:{},squad:{},other:{}},textFormat:font,x:-100,y:-100,width:200,height:30,alpha:100,align:'center',shadow:shadow,duration:2,rise:40,maxCount:4,colors:{player:'#FFDD66',squad:'#FFAA44',other:'#FFFFFF'}},
        icons:{enabled:false,'class':{enabled:true,x:null,y:null,scale:1,alpha:100,deadAlpha:40},level:{enabled:true,x:null,y:null,scale:1,alpha:100,deadAlpha:40},vehicle:{enabled:false,x:-55,y:-18,scale:1,alpha:100,deadAlpha:40}}
    };
    ['actionMarker','hoverMarker','vehicleStatusMarker','damageIndicator','damageIndicatorText','hitExplosion'].forEach(function (key) { defaults.icons[key]={enabled:true,x:null,y:null,scale:1,alpha:100,deadAlpha:100}; });
    function teamColor(config, sample) {
        var colors = config.colors, teams = colors.team;
        if (sample.blind && colors.colorBlind.enabled) { teams = merge(teams, colors.colorBlind.team); }
        if (sample.state==='dead') { return teams[sample.group+'Dead'] || teams.dead; }
        return teams[sample.group] || teams.unknown;
    }
    function hpColor(config, sample) {
        var percent = Math.max(0, Math.min(100, sample.hp));
        for (var i=0;i<config.colors.hp.length;i++) { if (percent < config.colors.hp[i].value) { return config.colors.hp[i].color; } }
        return config.colors.hp[config.colors.hp.length-1].color;
    }
    // The preview's sample vehicle when the panel sends none (T32 from the client's vehicle definitions);
    // the class abbreviations are the ones the battle markers use (VMText.formatText).
    var SAMPLE_VEHICLE = {vehicle:'T32',level:8,vtype:'heavyTank',maxHp:1650};
    var VEHICLE_CLASSES = {lightTank:'LT',mediumTank:'MT',heavyTank:'HT','AT-SPG':'TD',SPG:'SPG'};
    function escape(value) { return String(value).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;'); }
    function damageStyle(config,source) {
        var root=config.damageText, base={};
        Object.keys(root).forEach(function (key) { if (key!=='sources') { base[key]=root[key]; } });
        return merge(base,(root.sources || {})[source] || {});
    }
    function damageEvent(amount,source,kind,health) { return {amount:amount,source:source,kind:health<0 || kind==='explosion'?'explosion':kind,blowup:health<0 || kind==='explosion'}; }
    function token(text,values) {
        text=text.trim();
        if (text==='true' || text==='false') { return text==='true'; }
        if (/^-?\d+(?:\.\d+)?$/.test(text)) { return Number(text); }
        if (text.length>=2 && (text.charAt(0)==='\'' || text.charAt(0)==='"') && text.charAt(text.length-1)===text.charAt(0)) { return text.slice(1,-1); }
        return values[text];
    }
    function truth(value) { return value!==null && value!==undefined && value!==false && value!==0 && value!=='' && value!=='--' && value!=='false' && value!=='0'; }
    function condition(expression,values) {
        return expression.split('||').some(function (group) {
            return group.split('&&').every(function (part) {
                part=part.trim(); var negate=false;
                while (part.charAt(0)==='!' && part.slice(0,2)!=='!=') { negate=!negate; part=part.slice(1).trim(); }
                var match=/^(.*?)\s*(<=|>=|==|!=|<|>)\s*(.*?)$/.exec(part), result;
                if (!match) { result=truth(token(part,values)); }
                else {
                    var left=token(match[1],values), right=token(match[3],values), op=match[2];
                    if (left===null || left===undefined || right===null || right===undefined) { result=false; }
                    else if (op==='==') { result=left===right; }
                    else if (op==='!=') { result=left!==right; }
                    else if (!isFinite(Number(left)) || !isFinite(Number(right))) { result=false; }
                    else if (op==='<=') { result=Number(left)<=Number(right); }
                    else if (op==='>=') { result=Number(left)>=Number(right); }
                    else if (op==='<') { result=Number(left)<Number(right); }
                    else { result=Number(left)>Number(right); }
                }
                return negate?!result:result;
            });
        });
    }
    function text(template, config, sample, damage) {
        var vehicle = merge(SAMPLE_VEHICLE, sample.vehicle || {}), maxHp = vehicle.maxHp;
        var hp = sample.state === 'dead' || sample.group === 'dead' ? 0 : Math.round(maxHp*sample.hp/100);
        var values = {vehicle:vehicle.vehicle,name:sample.name || 'DriftKings',hp:hp,maxHp:maxHp,hpPercent:Math.round(hp/maxHp*100),level:vehicle.level,'c:team':teamColor(config,sample),'c:hp':hpColor(config,{hp:hp/maxHp*100})};
        var ratings=config.ratingValues || {wn8:2000,wnx:1800,eff:1400,xwn8:75,xeff:65,battles:15000,winrate:55,'stat-available':true};
        Object.keys(ratings).forEach(function (key) { values[key]=ratings[key]; });
        if (!config.ratingValues) {
            var selected=config.ratingType || 'wn8'; values.r=values[selected]; values.xr=values['x'+selected];
            ['wn8','wnx','eff','r','xr','xwn8','xeff','battles','winrate'].forEach(function (key) { values['c:'+key]='#02C9B3'; });
        }
        if (sample.statsAvailable===false || sample.anonym) {
            ['wn8','wnx','eff','xwn8','xeff','wgr','winrate','battles','kb','r','xr'].forEach(function (key) { values[key]=null; values['c:'+key]=config.colors.team.unknown; });
            values['stat-available']=false;
        }
        values['stock-turret']=!!sample.turret; values['turret-vulnerability']=sample.turret || 'none';
        values.turret=sample.turret==='high'?config.turretMarkers.highVulnerability:sample.turret==='low'?config.turretMarkers.lowVulnerability:sample.turret==='unknown'?config.turretMarkers.unknown:'';
        values['a:r']=values['stat-available']?100:0;
        values['xvm-stat']=values['stat-available']; // Legacy profile macro.
        values.nick=sample.name || 'DriftKings'; values.clan='[DK]';
        values['hp-max']=values.maxHp; values['hp-ratio']=values.hpPercent; values['c:system']=values['c:team'];
        values.distance=values.dist=sample.distance===undefined?350:sample.distance;
        values.alive=sample.state!=='dead' && sample.group!=='dead'; values.dead=!values.alive;
        values.ally=sample.group==='ally'; values.enemy=sample.group==='enemy';
        values.player=!!sample.player; values.squad=!!sample.squad; values.anonym=!!sample.anonym; values.vtype=VEHICLE_CLASSES[vehicle.vtype] || '';
        // Battle macros as a regular random battle reports them: no bonus type name, the place in the team list.
        values.battletype=sample.battletype===undefined?'':sample.battletype; values.position=sample.position===undefined?1:sample.position;
        values.blownUp=values['i18n:blownUp']=values['l10n:blownUp']=config.blownUp || 'Ammo rack';
        if (damage !== undefined) {
            var event=typeof damage==='number'?{amount:damage,source:'player',kind:'shot'}:damage;
            var style=damageStyle(config,event.source || 'player');
            values.dmg=event.amount; values['c:dmg']=style.colors[event.source || 'player'];
            values['dmg-ratio']=Math.round(event.amount/maxHp*100); values['dmg-source']=event.source || 'player';
            values['dmg-kind']=event.blowup?'explosion':event.kind || 'shot';
        }
        var result=String(template);
        for (var iteration=0;iteration<12 && result.indexOf('{{')>=0;iteration++) {
            var previous=result;
            result=result.replace(/\{\{([^{}]*)\}\}/g,function (all,expression) {
                var question=expression.indexOf('?'), pipe=expression.indexOf('|');
                if (question>=0) {
                    var branches=expression.slice(question+1).split('|');
                    return condition(expression.slice(0,question),values)?branches[0]:(branches[1] || '');
                }
                var fallback=pipe>=0?expression.slice(pipe+1):'--', body=pipe>=0?expression.slice(0,pipe):expression;
                var parts=body.split('%'), value=values[parts[0]];
                if (value===null || value===undefined) { return fallback; }
                if (parts[1]==='d') { value=String(Math.round(Number(value))); }
                else if (parts[1] && /^0?\.[0-3]f$/.test(parts[1])) { value=Number(value).toFixed(Number(parts[1].charAt(parts[1].length-2))); }
                return escape(value);
            });
            if (previous===result) { break; }
        }
        return result;
    }
    /* marker files (markers.json wiring + four state files), mirrored from core/vehicle_markers/schema.py. */
    var STATE_KEYS=['markersAliveNormal','markersAliveExtended','markersDeadNormal','markersDeadExtended'];
    var WIRING=/^\$\{(markers(?:Alive|Dead)(?:Normal|Extended))\.json:(ally|enemy)\}$/;
    function wiring(raw,team,state,mode) {
        var value=(((raw.markers || {})[team] || {})[state] || {})[mode];
        if (value && typeof value==='object') { return {inline:true,path:['markers',team,state,mode]}; }
        var match=typeof value==='string' ? WIRING.exec(value) : null;
        if (!match) { throw new Error('Invalid marker wiring: '+team+'.'+state+'.'+mode); }
        return {key:match[1],part:match[2],path:[match[1],match[2]]};
    }
    function markerBlock(raw,documents,team,state,mode) {
        var link=wiring(raw,team,state,mode);
        if (link.inline) { return resolve(raw.markers[team][state][mode]); }
        if (!documents[link.key]) {
            if (!raw[link.key] || typeof raw[link.key]!=='object') { throw new Error('Missing marker state file: '+link.key); }
            documents[link.key]=resolve(raw[link.key]);
        }
        var block=documents[link.key][link.part];
        if (!block || typeof block!=='object') { throw new Error('Missing marker block: '+link.key+':'+link.part); }
        return block;
    }
    function pick(options,keys) { var result={}; keys.forEach(function (key) { if (options && options[key]!==undefined) { result[key]=clone(options[key]); } }); return result; }
    function get(options,key,fallback) { return options && options[key]!==undefined && options[key]!==null ? options[key] : fallback; }
    function textField(options,size,defaultFormat) {
        var width=get(options,'width',size[0]), height=get(options,'height',size[1]), align=get(options,'align','center');
        var x=get(options,'x',0), y=get(options,'y',0), valign=options.valign;
        if (align==='right') { x-=width; } else if (align==='center') { x-=width/2; }
        if (valign==='bottom') { y-=height; } else if (valign==='center') { y-=height/2; }
        var textFormat=pick(options.textFormat || {},['font','size','color','bold','italic']), format=get(options,'format',defaultFormat || '');

        var result={name:get(options,'name',''),enabled:get(options,'enabled',true),format:format,x:x,y:y,width:width,height:height,
            alpha:get(options,'alpha',100),align:align,textFormat:textFormat};
        if (options.shadow) { result.shadow=pick(options.shadow,['enabled','distance','angle','color','alpha','blur','strength']); }
        return result;
    }
    function damageText(options) {
        options=options || {};
        var result=textField(options,[200,100],get(options,'damageMessage','{{dmg}}'));
        delete result.name;
        if (result.textFormat.color===undefined || result.textFormat.color===null) { result.textFormat.color='{{c:dmg}}'; }
        result.duration=get(options,'speed',2); result.rise=get(options,'maxRange',40); result.maxCount=4;
        result.blowupMessage=get(options,'blowupMessage','{{i18n:blownUp}}\n{{dmg}}');
        return result;
    }
    function healthBar(options,dead) {
        options=options || {};
        var border=options.border || {}, damage=options.damage || {}, lcolor=options.lcolor, enabled=get(options,'enabled',true);
        return {enabled:enabled,showOnDead:!!(dead && enabled),x:get(options,'x',-36),y:get(options,'y',-33),
            width:get(options,'width',70),height:get(options,'height',12),alpha:get(options,'alpha',100),
            color:get(options,'color','{{c:team}}'),fill:{alpha:get(options.fill,'alpha',100)},
            gradient:{enabled:lcolor!==null && lcolor!==undefined,color:get(options,'lcolor','{{c:hp}}'),angle:0},
            background:{color:get(border,'color','#000000'),alpha:get(border,'alpha',35)},
            border:{color:get(border,'color','#000000'),alpha:get(border,'alpha',35),width:get(border,'size',1)},
            damage:{enabled:true,color:get(damage,'color','{{c:dmg}}'),alpha:get(damage,'alpha',80),delay:0,duration:get(damage,'fade',1)},
            shadow:{enabled:false}};
    }
    function iconPosition(options,extra) {
        options=options || {};
        return merge({enabled:get(options,'enabled',true),x:get(options,'x',null),y:get(options,'y',null),scale:1,alpha:get(options,'alpha',100),deadAlpha:100},extra || {});
    }
    function icons(options) {
        var vehicle=options.vehicleIcon || {}, contour=options.contourIcon || {}, hover=options.hoverMarker || {}, indicator=options.damageIndicator || {};
        var x=get(indicator,'x',53), y=get(indicator,'y',-27);
        return {enabled:true,
            'class':{enabled:get(vehicle,'enabled',true),x:null,y:null,scale:1,alpha:get(vehicle,'alpha',100),deadAlpha:100,
                containerX:get(vehicle,'x',0)+get(vehicle,'offsetX',0),containerY:get(vehicle,'y',-16)+get(vehicle,'offsetY',0),showSpeaker:!!vehicle.showSpeaker},
            level:iconPosition(options.levelIcon || {enabled:false}),
            vehicle:iconPosition(contour,{enabled:get(contour,'enabled',false),tint:{color:contour.color || '{{c:system}}',amount:get(contour,'amount',0)}}),
            actionMarker:iconPosition(options.actionMarker),hoverMarker:iconPosition(hover,{glow:clone(hover.glow || {enabled:true})}),
            vehicleStatusMarker:iconPosition(options.vehicleStatusMarker),damageIndicator:iconPosition(indicator),hitExplosion:iconPosition(indicator),
            damageIndicatorText:iconPosition(indicator,{enabled:!!(get(indicator,'enabled',true) && get(indicator,'showText',true)),x:x+14,y:y-14})};
    }
    function adapt(raw) {
        var markers=raw.markers || {}, enabled=raw.enabled!==false, documents={};
        var result={enabled:enabled,debug:!!markers.debug,colorRating:get(markers,'colorRating',0),ratingType:get(markers,'ratingType','wn8'),
            turretMarkers:merge({highVulnerability:'*',lowVulnerability:"'",unknown:'?'},markers.turretMarkers || {}),colors:clone(markers.colors || {}),
            def:{},schemaVersion:2,markers:{enabled:enabled},customFields:{enabled:enabled},healthBar:{enabled:enabled},damageText:{enabled:enabled},icons:{enabled:enabled}};
        ['ally','enemy'].forEach(function (team) {
            ['markers','customFields','healthBar','damageText','icons'].forEach(function (name) { result[name][team]={alive:{},dead:{}}; });
            ['alive','dead'].forEach(function (state) {
                ['normal','extended'].forEach(function (mode) {
                    var options=markerBlock(raw,documents,team,state,mode);
                    result.markers[team][state][mode]={vehicleName:false,playerName:false,hp:'hidden',healthBar:false,
                        vehicleIcon:!!(options.contourIcon || {}).enabled,levelIcon:!!(options.levelIcon || {}).enabled,damage:true};
                    if (!enabled) { return; }
                    var fields=(options.textFields || []).filter(function (item) { return item && typeof item==='object'; }).map(function (item) { return textField(item,[140,100]); });
                    if ((options.vehicleDist || {}).enabled) {
                        var distance=textField(options.vehicleDist,[100,100],'{{alive&&distance?{{distance}}m|}}'); distance.name='Vehicle distance'; fields.push(distance);
                    }
                    result.customFields[team][state][mode]=fields;
                    result.healthBar[team][state][mode]=healthBar(options.healthBar,state==='dead');
                    var other=damageText(options.damageText);
                    other.sources={player:damageText(options.damageTextPlayer || options.damageText),squad:damageText(options.damageTextSquadman || options.damageText),other:{}};
                    result.damageText[team][state][mode]=other;
                    result.icons[team][state][mode]=icons(options);
                });
            });
        });
        return result;
    }
    function state(raw, sample, palettes) {
        if (raw && raw[STATE_KEYS[0]]) { raw=adapt(raw); }
        raw=migrate(resolve(raw));
        var config=merge(defaults,raw);
        ['healthBar','damageText','icons'].forEach(function (key) { config[key]=style(defaults[key],raw[key],sample); });
        var palette=palettes && palettes[raw.colorRating || 0];
        if (palette) {
            config.colors=merge(palette.colors,raw.colors);
            config.damageText.colors=merge(merge(palette.damageColors,(raw.damageText || {}).colors),(scoped(raw.damageText || {},sample) || {}).colors);
            config.ratingValues=(palette.ratings || {})[raw.ratingType || 'wn8'];
        }
        var native=merge({vehicleName:true,playerName:true,hp:'currentAndMax',healthBar:true,vehicleIcon:false,levelIcon:true,damage:true},scoped(config.markers,sample) || {});
        var fields=scoped(config.customFields,sample);
        return {config:config,native:native,fields:config.customFields.enabled && fields ? fields.map(function (item) { return merge(field,item); }) : null,shown:config.enabled && config.markers.enabled};
    }
    function validColor(value) { return /^#[0-9a-f]{6}$/i.test(value) || value === '{{c:dmg}}' || value === '{{c:hp}}' || value === '{{c:team}}'; }
    DK.vehicleMarkerModel = {resolve:resolve,clone:clone,merge:merge,migrate:migrate,defaults:defaults,field:field,ratingField:ratingField,damageStyle:damageStyle,damageEvent:damageEvent,condition:condition,state:state,text:text,teamColor:teamColor,hpColor:hpColor,validColor:validColor,
        STATE_KEYS:STATE_KEYS,wiring:wiring,adapt:adapt};
}());
