/* Tank sample and structured marker editor. Drafts use the normal Apply/Save session. */
(function () {
    'use strict';
    var DK=window.DK=window.DK || {}, M=DK.vehicleMarkerModel;
    function create(parent, mod, context) {
        var labels=mod.preview.labels || {}, bindings=mod.preview.bindings, palettes=mod.preview.palettes, model={}, arrays={}, section='textFields', selected=0;
        // XVM files edited by this form: markers.json and the four state files.
        var ROOTS=['markers'].concat(M.STATE_KEYS);
        var FIELD={name:'',enabled:true,x:0,y:-36,alpha:100,align:'center',format:'{{vehicle}}',
            textFormat:{font:'$FieldFont',size:13,color:null,bold:false,italic:false},
            shadow:{enabled:true,distance:0,angle:45,color:'0x000000',alpha:100,blur:6,strength:2}};
        var sample={group:'enemy',state:'alive',alt:false,blind:false,hp:70,distance:350,damageSource:'player',explosion:false,name:'DriftKings'}, widgets=[], disposed=false, lastValues='';
        var root=DK.dom.el('div','dk-vm-editor',null,parent), tabs=DK.dom.el('div','dk-vm-tabs',null,root);
        var workspace=DK.dom.el('div','dk-vm-workspace',null,root), edit=DK.dom.el('div','dk-vm-edit',null,workspace);
        var form=DK.dom.el('div','dk-vm-properties',null,edit), preview=DK.dom.el('div','dk-vm-preview',null,workspace);
        function label(key) { return labels[key] || key; }
        function node(tag,cls,text,owner) { return DK.dom.el(tag,cls,text,owner); }
        function button(owner,title,action) { var value=node('button','dk-btn',title,owner); value.type='button'; value.addEventListener('click',action); return value; }
        node('div','dk-vm-title',label('title'),preview);
        var selectors=node('div','dk-vm-selectors',null,preview);
        var groupButtons={}, roleButtons={};
        ['ally','enemy'].forEach(function (key) {
            groupButtons[key]=button(selectors,label(key),function () {
                sample.group=key; selected=0;
                if (key==='enemy') {
                    ['player','squad'].forEach(function (role) { sample[role]=false; DK.dom.setClass(roleButtons[role],'is-active',false); });
                }
                Object.keys(groupButtons).forEach(function (name) { DK.dom.setClass(groupButtons[name],'is-active',name===key); });
                clearEffects(); buildForm(); draw();
            });
            DK.dom.setClass(groupButtons[key],'is-active',sample.group===key);
        });
        var life=button(selectors,label('alive'),function () { sample.state=sample.state==='alive'?'dead':'alive'; life.textContent=label(sample.state); selected=0; clearEffects(); buildForm(); draw(); });
        var mode=button(selectors,label('normal'),function () { sample.alt=!sample.alt; mode.textContent=label(sample.alt?'extended':'normal'); selected=0; clearEffects(); buildForm(); draw(); });
        var blind=button(selectors,label('colorBlind'),function () { sample.blind=!sample.blind; DK.dom.setClass(blind,'is-active',sample.blind); draw(); });
        var indicators=button(selectors,label('indicators'),function () { sample.indicators=!sample.indicators; DK.dom.setClass(indicators,'is-active',!!sample.indicators); draw(); });
        var turret=button(selectors,label('turretMarkers'),function () { var states=['','high','low','unknown']; sample.turret=states[(states.indexOf(sample.turret || '')+1)%states.length]; DK.dom.setClass(turret,'is-active',!!sample.turret); draw(); });
        var stats=button(selectors,label('ratingType'),function () { sample.statsAvailable=sample.statsAvailable===false; DK.dom.setClass(stats,'is-active',sample.statsAvailable); draw(); });
        DK.dom.setClass(stats,'is-active',true);
        ['player','squad','anonym'].forEach(function (key) {
            var toggle=button(selectors,label('role_'+key),function () {
                sample[key]=!sample[key]; DK.dom.setClass(toggle,'is-active',sample[key]);
                if (key!=='anonym' && sample[key]) {
                    sample.group='ally'; Object.keys(groupButtons).forEach(function (team) { DK.dom.setClass(groupButtons[team],'is-active',team==='ally'); }); buildForm();
                }
                draw();
            });
            roleButtons[key]=toggle;
        });
        // The sample sliders live in the preview column and are not part of the saved settings.
        function sampleSlider(id,title,max,field) {
            function change(key,value) { sample[field]=value; draw(); }
            var api=DK.controls.create({id:id,type:'slider',label:title,min:0,max:max,step:1,metadata:{}},{labels:context.labels,preview:change,commit:change});
            preview.appendChild(api.node); api.update(sample[field]); api.info({disabled:false,changed:false,values:{}});
            return api;
        }
        var hp=sampleSlider('sampleHp',label('health'),100,'hp'), distance=sampleSlider('sampleDistance',label('distance'),1500,'distance');
        var stage=node('div','dk-vm-stage',null,preview), tank=node('img','dk-vm-tank',null,stage);
        tank.src=mod.preview.tank; tank.alt='T32';
        var marker=node('div','dk-vm-marker',null,stage), effects=node('div','dk-vm-effects',null,stage);
        var actions=node('div','dk-vm-actions',null,preview), timers=[];
        function clearEffects() { timers.forEach(clearTimeout); timers=[]; effects.textContent=''; }
        button(actions,label('damage'),simulateDamage);
        button(actions,label('reset'),function () { sample.hp=100; sample.state='alive'; life.textContent=label('alive'); hp.update(100); clearEffects(); buildForm(); draw(); });
        var authors=node('div','dk-vm-selectors',null,preview), authorButtons={};
        ['player','squad','other'].forEach(function (source) {
            authorButtons[source]=button(authors,label(source),function () {
                sample.damageSource=source;
                Object.keys(authorButtons).forEach(function (key) { DK.dom.setClass(authorButtons[key],'is-active',key===source); });
                clearEffects(); buildForm(); draw();
            });
            authorButtons[source].setAttribute('data-damage-source',source);
            DK.dom.setClass(authorButtons[source],'is-active',source==='player');
        });
        var blowup=button(authors,label('blowup'),function () { sample.explosion=!sample.explosion; DK.dom.setClass(blowup,'is-active',sample.explosion); });
        var notice=node('div','dk-vm-hint',label('hint'),preview), error=node('div','dk-vm-error','',preview);
        ['general','textFields','healthBar','damageText','icons','vehicleDist','def'].forEach(function (key) {
            var value=button(tabs,label(key),function () { section=key; buildForm(); draw(); }); value.setAttribute('data-section',key);
        });
        function save(root) {
            if (!bindings[root]) { return; }
            context.commit(bindings[root],root==='enabled'?model.enabled:JSON.stringify(model[root]));
        }
        function link() { return M.wiring(model,sample.group,sample.state,sample.alt?'extended':'normal'); }
        function blockPath() { return link().path; }
        // A field written as "${def.name}" or {"$ref":{"path":"def.name"}} edits its shared template.
        function templateName(value) {
            var match=typeof value==='string' && /^\$\{def\.([A-Za-z0-9_-]+)\}$/.exec(value);
            if (match) { return match[1]; }
            if (value && typeof value==='object' && Object.keys(value).length===1 && value.$ref) {
                var path=typeof value.$ref==='string'?value.$ref:value.$ref.path;
                match=/^def\.([A-Za-z0-9_-]+)$/.exec(path || ''); return match?match[1]:null;
            }
            return null;
        }
        function editPath(path,value) {
            var name=templateName(value), current=link();
            return name && !current.inline ? [current.key,'def',name] : path;
        }
        function pathGet(path) { var value=model; path.forEach(function (key) { value=value && value[key]; }); return value; }
        function pathSet(path,value) {
            var target=model;
            path.slice(0,-1).forEach(function (key,index) {
                if (!target[key] || typeof target[key]!=='object') {
                    // A list shown from defaults must become a real array, not an object keyed by index.
                    var shown=arrays[path.slice(0,index+1).join('.')];
                    target[key]=shown?M.clone(shown):{};
                }
                target=target[key];
            });
            target[path[path.length-1]]=value;
        }
        function set(path,value,commit) {
            pathSet(path,value); error.textContent=''; if (commit) { save(path[0]); } draw();
        }
        function widget(owner,path,value) {
            var key=path[path.length-1], type=typeof value, def={id:'vm'+widgets.length,label:label(key),description:label(key),metadata:{}};
            if (type==='boolean') { def.type='checkbox'; }
            else if (type==='number' || value===null) {
                def.type='slider'; def.min=(key==='x' || key==='y' || key==='angle')?-500:0;
                def.max=(key==='alpha' || key==='deadAlpha')?100:(key==='scale'?3:(key==='duration' || key==='delay'?10:500));
                def.step=(key==='scale' || key==='duration' || key==='delay')?0.1:1;
                if (key==='scale') { def.min=0.25; def.step=0.05; }
                if (value===null) { def.type='text'; def.label += ' (auto)'; }
                if (key==='maxCount') { def.min=1; def.max=12; }
                // Paths start with the XVM file key (markersAliveNormal...), so containers are looked up anywhere in the path.
                // The limits below match the validation in core/vehicle_markers (healthbar.py, damage.py).
                var inBar=path.indexOf('healthBar')>=0, inBorder=path.indexOf('border')>=0;
                if (key==='size') { def.min=1; def.max=100; }
                if (key==='size' && inBorder) { def.min=0; def.max=10; }
                if (key==='value') { def.max=Math.max(101,value); def.step=0.1; }
                if (key==='rise' || key==='maxRange') { def.max=300; }
                // speed (damage text display time) and fade (health bar damage trail) are seconds.
                if (key==='speed') { def.min=0.1; def.max=10; def.step=0.1; }
                if (key==='fade') { def.min=0.1; def.max=5; def.step=0.1; }
                if (key==='duration') { def.min=0.1; def.max=inBar?5:10; }
                if (key==='delay') { def.max=5; }
                if (key==='blur' || key==='strength' || key==='distance') { def.max=100; }
                if (key==='angle') { def.min=-360; def.max=360; }
                if (key==='width' || key==='height') {
                    def.min=1; def.max=1000;
                    if (inBar) { def.min=key==='width'?4:2; def.max=key==='width'?500:100; }
                    if (inBorder) { def.min=0; def.max=10; }
                }
            } else {
                var long=key==='format' || key==='blowupMessage' || key==='damageMessage';
                def.type=long?'textarea':'text'; def.maxLength=long?2048:256;
                if (key==='align' || (key==='hp' && type==='string')) {
                    def.type='dropdown'; var choices=key==='align'?['left','center','right']:['percent','currentAndMax','current','hidden'];
                    def.options=choices.map(function (option) { return {value:option,label:label(option)}; });
                } else if (typeof value==='string' && /^(#|0x)[0-9a-f]{6}$/i.test(value)) {
                    def.type='color'; def.presets=[];
                }
            }
            if (key==='colorRating') {
                def.type='dropdown';
                def.options=(palettes || []).map(function (palette,index) { return {value:index,label:palette.name}; });
            }
            if (key==='ratingType') { def.type='dropdown'; def.options=['wn8','wnx','eff'].map(function (key) { return {value:key,label:key.toUpperCase()}; }); }
            function changed(next,commit) {
                if (value===null) {
                    next=next===''?null:(key==='color'?next:Number(next));
                    if (next!==null && key!=='color' && !isFinite(next)) { error.textContent=label('invalid'); return; }
                }
                if (def.type==='color' && typeof value==='string' && value.indexOf('0x')===0) { next='0x'+next.slice(1); }
                set(path,next,commit);
                if (key==='colorRating' && commit) { DK.layer.close(); buildForm(); }
            }
            var api=DK.controls.create(def,{labels:context.labels,commit:function (id,next) { changed(next,true); },preview:function (id,next) { changed(next,false); }});
            api.node.setAttribute('data-property',path.join('.'));
            owner.appendChild(api.node); api.update(value===null?'':value); api.info({disabled:false,changed:false,values:{}}); widgets.push(api);
            if (def.type==='textarea' || def.type==='text') {
                var input=api.node.querySelector(def.type==='textarea'?'textarea':'input');
                if (input) {
                    if (def.type==='textarea') { input.style.height='90rem'; input.style.minHeight='90rem'; input.rows=4; }
                    input.addEventListener('input',function () { changed(input.value,false); });
                }
            }
        }
        // XVM template keys (def.tankName...) shown with a translated name and the key itself.
        function templateTitle(key,value) {
            var title=labels['tpl_'+key] || (value && typeof value.name==='string' && value.name) || key;
            return title===key?key:title+' ('+key+')';
        }
        // A closed group with a title button; returns the element to fill.
        function collapsible(owner,title) {
            var details=node('div','dk-vm-details',null,owner), body;
            button(details,title,function () { body.style.display=body.style.display==='none'?'block':'none'; });
            body=node('div','',null,details); body.style.display='none';
            return body;
        }
        function objectForm(owner,path,object,defaults) {
            var source=M.merge(defaults || {},object || {});
            Object.keys(source).forEach(function (key) {
                var value=source[key], next=path.concat([key]);
                if (Array.isArray(value)) { arrayForm(owner,next,value); }
                else if (value && typeof value==='object') {
                    objectForm(collapsible(owner,path[path.length-1]==='def'?templateTitle(key,value):label(key)),next,value);
                } else { widget(owner,next,value); }
            });
        }
        // The shown list may come from defaults; the first edit or change copies it into the file.
        function bandList(path,items) {
            if (!Array.isArray(pathGet(path))) { pathSet(path,M.clone(items)); }
            return pathGet(path);
        }
        function arrayForm(owner,path,items) {
            arrays[path.join('.')]=items;
            items.forEach(function (item,index) { var box=node('div','dk-vm-array-item',null,owner); objectForm(box,path.concat([index]),item); });
            // Health colour bands are stored in markers.json as markers.colors.hp.
            if (path.length===3 && path[0]==='markers' && path[1]==='colors' && path[2]==='hp') {
                button(owner,label('addBand'),function () {
                    var bands=bandList(path,items), previous=bands.length>1?bands[bands.length-2].value:0;
                    if (bands.length>=20 || previous>=99) { return; }
                    bands.splice(bands.length-1,0,{value:Math.floor((previous+100)/2),color:'#FFDD66'}); save('markers'); buildForm(); draw();
                });
                if (items.length>1) { button(owner,label('remove'),function () { bandList(path,items).splice(items.length-2,1); save('markers'); buildForm(); draw(); }); }
            }
        }
        function textFields() {
            var block=pathGet(blockPath());
            if (!block.textFields) { block.textFields=[]; }
            return block.textFields;
        }
        function scoped(owner,key,defaults) {
            var path=blockPath().concat([key]), value=pathGet(path), target=editPath(path,value);
            if (target!==path) { node('div','dk-vm-hint',label('shared')+': def.'+target[2],owner); }
            objectForm(owner,target,pathGet(target),defaults);
        }
        // An invalid reference or a missing block is reported in the error box, like draw() does, and never thrown to the window.
        function buildForm() {
            try { renderForm(); } catch (problem) { error.textContent=problem.message; }
        }
        function renderForm() {
            widgets.forEach(function (api) { if (api.dispose) { api.dispose(); } }); widgets=[]; arrays={}; form.textContent='';
            var buttons=tabs.querySelectorAll('button'); for (var t=0;t<buttons.length;t++) { DK.dom.setClass(buttons[t],'is-active',buttons[t].getAttribute('data-section')===section); }
            if (!model.markers) { return; }
            var current;
            try { current=link(); } catch (problem) { error.textContent=problem.message; return; }
            if (section!=='general') {
                node('div','dk-vm-hint',label(sample.group)+' / '+label(sample.state)+' / '+label(sample.alt?'extended':'normal')+' \u2192 '+
                     (current.inline?'markers.json':current.key+'.json : '+current.part),form);
            }
            if (section==='general') {
                widget(form,['enabled'],model.enabled); widget(form,['markers','debug'],!!model.markers.debug);
                if (palettes) { widget(form,['markers','colorRating'],model.markers.colorRating || 0); }
                widget(form,['markers','ratingType'],model.markers.ratingType || 'wn8');
                objectForm(form,['markers','turretMarkers'],model.markers.turretMarkers,{highVulnerability:'*',lowVulnerability:"'"});
                objectForm(form,['markers','colors'],model.markers.colors,resolved().config.colors);
                return;
            }
            if (section==='def') {
                if (current.inline) { node('div','dk-vm-hint',label('empty'),form); return; }
                objectForm(form,[current.key,'def'],model[current.key].def || {});
                return;
            }
            if (section==='textFields') {
                var list=textFields(), bar=node('div','dk-vm-field-actions',null,form);
                selected=Math.max(0,Math.min(selected,list.length-1));
                var resolvedList=M.resolve(current.inline?pathGet(current.path):model[current.key]);
                resolvedList=(current.inline?resolvedList:resolvedList[current.part]).textFields || [];
                if (list.length) {
                    var select=DK.controls.create({id:'sampleField',type:'dropdown',label:label('fields'),metadata:{},options:list.map(function (item,index) {
                        var name=templateName(item); return {value:index,label:name?templateTitle(name,resolvedList[index]):((resolvedList[index] || {}).name || label('fields')+' '+(index+1))};
                    })}, {labels:context.labels,commit:function (id,value) { selected=value; buildForm(); draw(); }});
                    bar.appendChild(select.node); select.update(selected); select.info({disabled:false,changed:false,values:{}}); widgets.push(select);
                }
                function push(item) { if (list.length>=12) { return; } list.push(item); selected=list.length-1; save(blockPath()[0]); buildForm(); draw(); }
                var add=button(bar,label('add'),function () { push(M.clone(FIELD)); }); add.disabled=list.length>=12;
                var rating=button(bar,label('addRating'),function () {
                    push(sample.alt?M.merge(FIELD,{name:'Rating',y:-51,format:'{{r}}',textFormat:{color:'{{c:xr}}'}})
                                   :M.merge(FIELD,{name:'Rating',x:-32,y:-21,align:'right',alpha:'{{xvm-stat?100|0}}',format:'&#x115;',
                                                   textFormat:{font:'xvm',size:17,color:'{{c:xr|#999999}}'},shadow:{blur:2,strength:1}}));
                }); rating.disabled=list.length>=12;
                var templates=node('input','',null,bar); templates.type='text'; templates.placeholder=label('def');
                button(bar,label('saveTemplate'),function () {
                    var name=templates.value.trim();
                    if (current.inline || !/^[A-Za-z0-9_-]+$/.test(name) || !list.length || templateName(list[selected])) { return; }
                    model[current.key].def=model[current.key].def || {};
                    model[current.key].def[name]=M.clone(list[selected]); list[selected]='${def.'+name+'}';
                    save(current.key); buildForm(); draw();
                });
                if (!current.inline) {
                    Object.keys(model[current.key].def || {}).forEach(function (name) {
                        var value=model[current.key].def[name];
                        if (!value || typeof value.format!=='string' || name==='damageText') { return; }
                        var addTemplate=button(bar,labels['tpl_'+name] || name,function () { push('${def.'+name+'}'); }); addTemplate.disabled=list.length>=12;
                    });
                }
                var remove=button(bar,label('remove'),function () { list.splice(selected,1); selected=Math.max(0,selected-1); save(blockPath()[0]); buildForm(); draw(); }); remove.disabled=!list.length;
                if (!list.length) { node('div','dk-vm-hint',label('empty'),form); return; }
                var path=blockPath().concat(['textFields',selected]), target=editPath(path,list[selected]);
                if (target!==path) { node('div','dk-vm-hint',label('shared')+': def.'+target[2],form); }
                objectForm(form,target,pathGet(target),FIELD);
                return;
            }
            if (section==='damageText') {
                var author={player:'damageTextPlayer',squad:'damageTextSquadman',other:'damageText'}[sample.damageSource];
                node('div','dk-vm-hint',label(sample.damageSource),form);
                scoped(form,author,{enabled:true,x:0,y:-67,alpha:100,align:'center',textFormat:FIELD.textFormat,shadow:FIELD.shadow,
                                    speed:2,maxRange:40,damageMessage:'{{dmg}}',blowupMessage:'{{i18n:blownUp}}\n{{dmg}}'});
                return;
            }
            if (section==='icons') {
                ['vehicleIcon','levelIcon','contourIcon','actionMarker','hoverMarker','vehicleStatusMarker','damageIndicator'].forEach(function (key) {
                    scoped(collapsible(form,label(key)),key);
                });
                return;
            }
            scoped(form,section);
        }
        function resolved() { var state=M.state(model,sample,palettes); state.config.blownUp=label('blowup'); return state; }
        function styleField(element,options,config,event) {
            element.style.left=options.x+'rem'; element.style.top=options.y+'rem';
            element.style.width=options.width+'rem'; element.style.height=options.height+'rem';
            var alpha=Number(M.text(String(options.alpha),config,sample,event));
            element.style.opacity=isFinite(alpha)?Math.max(0,Math.min(100,alpha))/100:0; element.style.textAlign=options.align || 'center';
            var font=options.textFormat;
            if (font) {
                // Gameface only draws loaded fonts; this window loads Warhelios, the closest to $FieldFont.
                element.style.fontFamily=font.font && font.font!=='$FieldFont'?font.font+', Warhelios':'Warhelios';
                element.style.fontSize=font.size+'rem'; element.style.fontWeight=font.bold?'bold':'normal'; element.style.fontStyle=font.italic?'italic':'normal';
                element.style.color=font.color===null?(event?M.damageStyle(config,event.source).colors[event.source]:M.teamColor(config,sample)):M.text(String(font.color),config,sample,event);
            }
            var shadow=options.shadow;
            if (shadow && shadow.enabled) {
                var angle=shadow.angle*Math.PI/180, color=rgba(shadow.color,shadow.alpha);
                element.style.textShadow=(Math.cos(angle)*shadow.distance)+'rem '+(Math.sin(angle)*shadow.distance)+'rem '+shadow.blur+'rem '+color;
            }
        }
        function rgba(color,alpha) {
            var hex=String(color).replace(/^(#|0x)/,'');
            return 'rgba('+parseInt(hex.slice(0,2),16)+','+parseInt(hex.slice(2,4),16)+','+parseInt(hex.slice(4,6),16)+','+alpha/100+')';
        }
        function html(element,value) {
            var source=document.createElement('div'); source.innerHTML=value;
            if (window.DriftkingsFlashText) { window.DriftkingsFlashText.copy(source,element,{fontFamily:true,fieldFont:'Warhelios',hideZeroSize:true,sizeUnit:'rem'}); }
            else { element.textContent=source.textContent; }
        }
        function draw() {
            if (!model.markers || disposed) { return; }
            var state;
            try { state=resolved(); } catch (problem) { error.textContent=problem.message; return; }
            marker.textContent=''; var config=state.config;
            marker.style.opacity=state.shown?1:0.2; tank.style.opacity=sample.state==='dead'?0.45:1;
            if (state.fields) {
                state.fields.forEach(function (options,index) {
                    if (!options.enabled) { return; }
                    var field=node('div','dk-vm-text'+(section==='textFields' && index===selected?' is-selected':''),null,marker);
                    styleField(field,options,config); html(field,M.text(options.format,config,sample));
                    field.addEventListener('click',function () { section='textFields'; selected=index; buildForm(); draw(); });
                });
            } else {
                var nativeText=[]; if (state.native.vehicleName) { nativeText.push('T32'); } if (state.native.playerName) { nativeText.push(sample.name); }
                if (state.native.hp!=='hidden') { nativeText.push(state.native.hp==='percent'?sample.hp+'%':Math.round(1550*sample.hp/100)+' / 1550'); }
                var native=node('div','dk-vm-native-text',nativeText.join(' · '),marker); native.style.color=M.teamColor(config,sample);
            }
            var bar=config.healthBar;
            if ((bar.enabled || state.native.healthBar) && (sample.state!=='dead' || bar.showOnDead)) {
                var bg=node('div','dk-vm-bar',null,marker), fill=node('div','dk-vm-fill',null,bg);
                var style=bar.enabled?bar:{x:-35,y:-22,width:70,height:8,alpha:100,color:'{{c:team}}',background:{color:'#181818',alpha:80},border:{width:1,color:'#000000',alpha:100}};
                bg.style.left=style.x+'rem'; bg.style.top=style.y+'rem'; bg.style.width=style.width+'rem'; bg.style.height=style.height+'rem'; bg.style.opacity=style.alpha/100;
                bg.style.backgroundColor=rgba(style.background.color,style.background.alpha); bg.style.border=style.border.width+'rem solid '+rgba(style.border.color,style.border.alpha);
                if (style.shadow && style.shadow.enabled) {
                    var shadow=style.shadow, angle=shadow.angle*Math.PI/180;
                    bg.style.boxShadow=Math.cos(angle)*shadow.distance+'rem '+Math.sin(angle)*shadow.distance+'rem '+shadow.blur+'rem '+rgba(shadow.color,shadow.alpha);
                }
                fill.style.opacity=style.fill?style.fill.alpha/100:1;
                fill.style.width=(sample.state==='dead'?0:sample.hp)+'%'; fill.style.backgroundColor=style.color==='{{c:hp}}'?M.hpColor(config,{hp:sample.state==='dead'?0:sample.hp}):style.color==='{{c:team}}'?M.teamColor(config,sample):style.color;
            }
            if (bar.enabled && bar.gradient.enabled && fill) {
                fill.style.background='linear-gradient('+(90+bar.gradient.angle)+'deg, '+M.text(bar.color,config,sample)+', '+M.text(bar.gradient.color,config,sample)+')';
            }
            var iconOptions=config.icons;
            function icon(kind,text,x,y,visible) {
                var style=iconOptions.enabled?iconOptions[kind]:{enabled:true,scale:1,alpha:100,deadAlpha:40,x:null,y:null};
                if (!style.enabled || !visible) { return; }
                var value=node('div','dk-vm-icon dk-vm-icon-'+kind,text,marker);
                // XVM places the class icon through its container; native icons keep their default spot.
                if (style.containerX!==undefined && style.containerX!==null) { x=style.containerX; y=style.containerY+12; }
                value.style.left=(style.x===null || style.x===undefined?x:style.x)+'rem'; value.style.top=(style.y===null || style.y===undefined?y:style.y)+'rem';
                value.style.color=M.teamColor(config,sample); value.style.opacity=style.alpha/100*(sample.state==='dead'?style.deadAlpha/100:1);
                value.style.transform='translateX(-50%) scale('+style.scale+')';
            }
            icon('class','///',0,-4,true); icon('level','VIII',0,-37,state.native.levelIcon);
            icon('vehicle','▰',-55,-18,state.native.vehicleIcon);
            if (sample.indicators) {
                icon('actionMarker','!',0,-100,true); icon('hoverMarker','O',0,-20,true);
                icon('vehicleStatusMarker','+',35,-35,true); icon('damageIndicator','!',40,-70,true);
                icon('damageIndicatorText','-250',65,-70,true); icon('hitExplosion','*',-35,-70,true);
            }
        }
        function simulateDamage() {
            if (!model.markers) { return; }
            if (sample.hp<=0) { return; }
            var before=sample.hp; sample.hp=sample.explosion?0:Math.max(0,sample.hp-20);
            if (sample.hp<=0) { sample.state='dead'; life.textContent=label('dead'); buildForm(); }
            hp.update(sample.hp); draw();
            var current;
            try { current=resolved(); } catch (problem) { error.textContent=problem.message; return; }
            var config=current.config, damage=M.damageStyle(config,sample.damageSource), trail=config.healthBar.damage;
            if (trail.enabled && sample.state!=='dead' && before>sample.hp) {
                var bar=marker.querySelector('.dk-vm-bar');
                if (bar) {
                    var tail=node('div','dk-vm-trail',null,bar); tail.style.backgroundColor=trail.color==='{{c:dmg}}'?damage.colors[sample.damageSource]:trail.color; tail.style.opacity=trail.alpha/100; tail.style.left=sample.hp+'%'; tail.style.width=(before-sample.hp)+'%';
                    timers.push(setTimeout(function () { tail.style.transition='width '+trail.duration+'s linear'; tail.style.width='0%'; },trail.delay*1000));
                }
            }
            if (!damage.enabled || current.native.damage===false) { return; }
            var same=[];
            for (var i=0;i<effects.children.length;i++) { if (effects.children[i].getAttribute('data-source')===sample.damageSource) { same.push(effects.children[i]); } }
            while (same.length>=damage.maxCount) { effects.removeChild(same.shift()); }
            var event=M.damageEvent(Math.round((before-sample.hp)*1550/100),sample.damageSource,sample.explosion?'explosion':'shot',sample.explosion?-1:sample.hp);
            var text=node('div','dk-vm-text dk-vm-damage',null,effects); text.setAttribute('data-source',sample.damageSource);
            styleField(text,damage,config,event); html(text,M.text(sample.explosion?damage.blowupMessage:damage.format,config,sample,event));
            timers.push(setTimeout(function () { text.style.transition='transform '+damage.duration+'s linear, opacity '+damage.duration+'s linear'; text.style.transform='translateY(-'+damage.rise+'rem)'; text.style.opacity=0; },20));
            timers.push(setTimeout(function () { if (text.parentNode) { text.parentNode.removeChild(text); } },damage.duration*1000+30));
        }
        function update(values) {
            if (disposed) { return; }
            var signature=JSON.stringify(values);
            if (signature===lastValues) { return; }
            if (form.contains(document.activeElement)) { return; }
            var next={enabled:true};
            try {
                Object.keys(bindings).forEach(function (key) {
                    var raw=values[bindings[key]];
                    if (key==='enabled') { next.enabled=raw!==false; }
                    else if (ROOTS.indexOf(key)>=0) { next[key]=typeof raw==='string'?JSON.parse(raw):raw; }
                });
                if (!next.markers) { throw new Error('missing markers.json'); }
            } catch (_error) { error.textContent=label('invalid'); return; }
            model=next; lastValues=signature; error.textContent=''; buildForm(); draw();
        }
        return {update:update,dispose:function () {
            disposed=true; timers.forEach(clearTimeout); hp.dispose(); distance.dispose(); widgets.forEach(function (api) { if (api.dispose) { api.dispose(); } }); root.parentNode.removeChild(root);
        },node:root,notice:notice};
    }
    DK.vehicleMarkersEditor={create:create};
}());
