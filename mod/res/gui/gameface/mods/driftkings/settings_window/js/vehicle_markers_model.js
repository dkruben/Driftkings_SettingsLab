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
    var shadow = {enabled:true,distance:0,angle:0,color:'0x000000',alpha:80,blur:3,strength:2};
    var field = {enabled:true,format:'<font size="13" color="{{c:team}}">{{vehicle}}</font>',x:-100,y:-65,width:200,height:25,alpha:100,align:'center',shadow:shadow};
    var defaults = {
        enabled:true,debug:false,markers:{enabled:true},customFields:{enabled:true,ally:{},enemy:{},dead:{}},
        colors:{team:{ally:'#99CC66',enemy:'#FF7777',squad:'#FFCC66',teamKiller:'#66CCFF',dead:'#AAAAAA',unknown:'#CCCCCC'},hp:[{value:25,color:'#FF5555'},{value:50,color:'#FFAA44'},{value:75,color:'#FFDD66'},{value:100,color:'#99CC66'}],colorBlind:{enabled:true,team:{enemy:'#C48CFF',teamKiller:'#66CCFF'}}},
        healthBar:{enabled:false,x:-35,y:-22,width:70,height:8,alpha:100,color:'{{c:team}}',showOnDead:false,background:{color:'#181818',alpha:80},border:{color:'#000000',alpha:100,width:1},shadow:shadow,damage:{enabled:false,color:'#FFDD66',alpha:65,delay:0.25,duration:0.75}},
        damageText:{enabled:false,format:'<font size="18" color="{{c:dmg}}"><b>-{{dmg}}</b></font>',x:-100,y:-100,width:200,height:30,alpha:100,align:'center',shadow:shadow,duration:2,rise:40,maxCount:4,colors:{player:'#FFDD66',squad:'#FFAA44',other:'#FFFFFF'}},
        icons:{enabled:false,'class':{enabled:true,x:null,y:null,scale:1,alpha:100,deadAlpha:40},level:{enabled:true,x:null,y:null,scale:1,alpha:100,deadAlpha:40},vehicle:{enabled:false,x:-55,y:-18,scale:1,alpha:100,deadAlpha:40}}
    };
    function teamColor(config, sample) {
        var colors = config.colors, teams = colors.team;
        if (sample.blind && colors.colorBlind.enabled) { teams = merge(teams, colors.colorBlind.team); }
        return teams[sample.group] || teams.unknown;
    }
    function hpColor(config, sample) {
        var percent = Math.max(0, Math.min(100, sample.hp));
        for (var i=0;i<config.colors.hp.length;i++) { if (percent < config.colors.hp[i].value) { return config.colors.hp[i].color; } }
        return config.colors.hp[config.colors.hp.length-1].color;
    }
    function escape(value) { return String(value).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;'); }
    function text(template, config, sample, damage) {
        var hp = sample.group === 'dead' ? 0 : Math.round(1550*sample.hp/100);
        var values = {vehicle:'T32',name:sample.name || 'DriftKings',hp:hp,maxHp:1550,hpPercent:Math.round(hp/1550*100),level:8,'c:team':teamColor(config,sample),'c:hp':hpColor(config,{hp:hp/1550*100})};
        if (damage !== undefined) { values.dmg = damage; values['c:dmg'] = config.damageText.colors.player; }
        return String(template).replace(/\{\{(.*?)\}\}/g,function (all,key) { return Object.prototype.hasOwnProperty.call(values,key) ? escape(values[key]) : all; });
    }
    function state(raw, sample, palettes) {
        var config=merge(defaults,raw), group=sample.group, mode=sample.alt?'extended':'normal';
        var palette=palettes && palettes[raw.colorRating || 0];
        if (palette) {
            config.colors=merge(palette.colors,raw.colors);
            config.damageText.colors=merge(palette.damageColors,(raw.damageText || {}).colors);
        }
        var native=merge({vehicleName:true,playerName:true,hp:'currentAndMax',healthBar:true,vehicleIcon:false,levelIcon:true,damage:true},(config.markers[group] || {})[mode] || {});
        var fields=(config.customFields[group] || {})[mode];
        return {config:config,native:native,fields:config.customFields.enabled && fields ? fields.map(function (item) { return merge(field,item); }) : null,shown:config.enabled && config.markers.enabled};
    }
    function validColor(value) { return /^(?:#|0x)[0-9a-f]{6}$/i.test(value) || value === '{{c:hp}}' || value === '{{c:team}}'; }
    DK.vehicleMarkerModel = {clone:clone,merge:merge,defaults:defaults,field:field,state:state,text:text,teamColor:teamColor,hpColor:hpColor,validColor:validColor};
}());
