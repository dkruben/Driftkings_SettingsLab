/* Tank sample and structured marker editor. Drafts use the normal Apply/Save session. */
(function () {
    'use strict';
    var DK=window.DK=window.DK || {}, M=DK.vehicleMarkerModel;
    function create(parent, mod, context) {
        var labels=mod.preview.labels || {}, bindings=mod.preview.bindings, palettes=mod.preview.palettes, model={}, section='customFields', selected=0;
        var sample={group:'enemy',alt:false,blind:false,hp:70,name:'DriftKings'}, widgets=[], disposed=false, lastValues='';
        var root=DK.dom.el('div','dk-vm-editor',null,parent), tabs=DK.dom.el('div','dk-vm-tabs',null,root);
        var workspace=DK.dom.el('div','dk-vm-workspace',null,root), edit=DK.dom.el('div','dk-vm-edit',null,workspace);
        var form=DK.dom.el('div','dk-vm-properties',null,edit), preview=DK.dom.el('div','dk-vm-preview',null,workspace);
        function label(key) { return labels[key] || key; }
        function node(tag,cls,text,owner) { return DK.dom.el(tag,cls,text,owner); }
        function button(owner,title,action) { var value=node('button','dk-btn',title,owner); value.type='button'; value.addEventListener('click',action); return value; }
        node('div','dk-vm-title',label('title'),preview);
        var selectors=node('div','dk-vm-selectors',null,preview);
        var groupButtons={};
        ['ally','enemy','dead'].forEach(function (key) {
            groupButtons[key]=button(selectors,label(key),function () {
                sample.group=key; selected=0;
                Object.keys(groupButtons).forEach(function (name) { DK.dom.setClass(groupButtons[name],'is-active',name===key); });
                buildForm(); draw();
            });
            DK.dom.setClass(groupButtons[key],'is-active',sample.group===key);
        });
        var mode=button(selectors,label('normal'),function () { sample.alt=!sample.alt; mode.textContent=label(sample.alt?'extended':'normal'); selected=0; buildForm(); draw(); });
        var blind=button(selectors,label('colorBlind'),function () { sample.blind=!sample.blind; DK.dom.setClass(blind,'is-active',sample.blind); draw(); });
        function sampleHealth(key,value) { sample.hp=value; draw(); }
        var hp=DK.controls.create({id:'sampleHp',type:'slider',label:label('health'),min:0,max:100,step:1,metadata:{}},
                                 {labels:context.labels,preview:sampleHealth,commit:sampleHealth});
        preview.appendChild(hp.node); hp.update(sample.hp); hp.info({disabled:false,changed:false,values:{}});
        var stage=node('div','dk-vm-stage',null,preview), tank=node('img','dk-vm-tank',null,stage);
        tank.src=mod.preview.tank; tank.alt='T32';
        var marker=node('div','dk-vm-marker',null,stage), effects=node('div','dk-vm-effects',null,stage);
        var actions=node('div','dk-vm-actions',null,preview), timers=[];
        button(actions,label('damage'),simulateDamage);
        button(actions,label('reset'),function () { sample.hp=100; hp.update(100); draw(); });
        var notice=node('div','dk-vm-hint',label('hint'),preview), error=node('div','dk-vm-error','',preview);
        ['general','customFields','healthBar','damageText','icons','colors','markers'].forEach(function (key) {
            var value=button(tabs,label(key),function () { section=key; buildForm(); draw(); }); value.setAttribute('data-section',key);
        });
        function save(block) {
            if (!bindings[block]) { return; }
            var value=(block==='enabled' || block==='debug' || block==='colorRating') ? model[block] : JSON.stringify(model[block]);
            context.commit(bindings[block],value);
        }
        function pathGet(path) { var value=model; path.forEach(function (key) { value=value && value[key]; }); return value; }
        function pathSet(path,value) { var target=model; path.slice(0,-1).forEach(function (key) { if (!target[key] || typeof target[key]!=='object') { target[key]={}; } target=target[key]; }); target[path[path.length-1]]=value; }
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
                if (key==='value') { def.max=Math.max(101,value); def.step=0.1; }
                if (key==='rise') { def.max=300; }
                if (key==='duration') { def.min=0.1; def.max=path[0]==='healthBar'?5:10; }
                if (key==='delay') { def.max=5; }
                if (key==='blur' || key==='strength' || key==='distance') { def.max=100; }
                if (key==='angle') { def.min=-360; def.max=360; }
                if (key==='width' || key==='height') {
                    def.min=1; def.max=1000;
                    if (path[0]==='healthBar') { def.min=key==='width'?4:2; def.max=key==='width'?500:100; }
                    if (path.indexOf('border')>=0) { def.min=0; def.max=10; }
                }
            } else {
                def.type=key==='format'?'textarea':'text'; def.maxLength=key==='format'?2048:256;
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
            function changed(next,commit) {
                if (value===null) { next=next===''?null:Number(next); if (next!==null && !isFinite(next)) { error.textContent=label('invalid'); return; } }
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
        function objectForm(owner,path,object,defaults) {
            var source=M.merge(defaults || {},object || {});
            Object.keys(source).forEach(function (key) {
                var value=source[key], next=path.concat([key]);
                if (Array.isArray(value)) { arrayForm(owner,next,value); }
                else if (value && typeof value==='object') {
                    var details=node('div','dk-vm-details',null,owner), body;
                    button(details,label(key),function () { body.style.display=body.style.display==='none'?'block':'none'; });
                    body=node('div','',null,details); body.style.display='none'; objectForm(body,next,value);
                } else { widget(owner,next,value); }
            });
        }
        function arrayForm(owner,path,items) {
            items.forEach(function (item,index) { var box=node('div','dk-vm-array-item',null,owner); objectForm(box,path.concat([index]),item); });
            if (path[0]==='colors' && path[1]==='hp') {
                button(owner,label('addBand'),function () {
                    var bands=pathGet(path), previous=bands.length>1?bands[bands.length-2].value:0;
                    if (bands.length>=20 || previous>=99) { return; }
                    bands.splice(bands.length-1,0,{value:Math.floor((previous+100)/2),color:'#FFDD66'}); save('colors'); buildForm(); draw();
                });
                if (items.length>1) { button(owner,label('remove'),function () { pathGet(path).splice(items.length-2,1); save('colors'); buildForm(); draw(); }); }
            }
        }
        function fields() {
            if (!model.customFields[sample.group]) { model.customFields[sample.group]={}; }
            var modeKey=sample.alt?'extended':'normal';
            if (!model.customFields[sample.group][modeKey]) { model.customFields[sample.group][modeKey]=[]; }
            return model.customFields[sample.group][modeKey];
        }
        function buildForm() {
            widgets.forEach(function (api) { if (api.dispose) { api.dispose(); } }); widgets=[]; form.textContent='';
            var buttons=tabs.querySelectorAll('button'); for (var t=0;t<buttons.length;t++) { DK.dom.setClass(buttons[t],'is-active',buttons[t].getAttribute('data-section')===section); }
            if (!model.customFields) { return; }
            if (section==='general') {
                widget(form,['enabled'],model.enabled); widget(form,['debug'],model.debug);
                if (palettes) { widget(form,['colorRating'],model.colorRating || 0); }
                return;
            }
            if (section==='customFields') {
                widget(form,['customFields','enabled'],model.customFields.enabled);
                var list=fields(), bar=node('div','dk-vm-field-actions',null,form);
                selected=Math.max(0,Math.min(selected,list.length-1));
                if (list.length) {
                    var select=DK.controls.create({id:'sampleField',type:'dropdown',label:label('fields'),metadata:{},options:list.map(function (item,index) { return {value:index,label:label('fields')+' '+(index+1)}; })},
                        {labels:context.labels,commit:function (id,value) { selected=value; buildForm(); draw(); }});
                    bar.appendChild(select.node); select.update(selected); select.info({disabled:false,changed:false,values:{}}); widgets.push(select);
                }
                var add=button(bar,label('add'),function () { if (list.length>=12) { return; } list.push(M.clone(M.field)); selected=list.length-1; save('customFields'); buildForm(); draw(); }); add.disabled=list.length>=12;
                var remove=button(bar,label('remove'),function () { list.splice(selected,1); selected=Math.max(0,selected-1); save('customFields'); buildForm(); draw(); }); remove.disabled=!list.length;
                if (!list.length) { node('div','dk-vm-hint',label('empty'),form); }
                else { objectForm(form,['customFields',sample.group,sample.alt?'extended':'normal',selected],list[selected],M.field); }
            } else if (section==='markers') {
                var modeKey=sample.alt?'extended':'normal';
                objectForm(form,['markers',sample.group,modeKey],(model.markers[sample.group] || {})[modeKey],{vehicleName:true,playerName:true,hp:'currentAndMax',healthBar:true,vehicleIcon:false,levelIcon:true,damage:true});
            } else {
                if (section==='colors' && palettes) { widget(form,['colorRating'],model.colorRating || 0); }
                objectForm(form,[section],model[section],resolved().config[section]);
            }
        }
        function resolved() { return M.state(model,sample,palettes); }
        function styleField(element,options) {
            element.style.left=options.x+'rem'; element.style.top=options.y+'rem';
            element.style.width=options.width+'rem'; element.style.height=options.height+'rem';
            element.style.opacity=options.alpha/100; element.style.textAlign=options.align || 'center';
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
            if (window.DriftkingsFlashText) { window.DriftkingsFlashText.copy(source,element,{fontFamily:true,sizeUnit:'rem'}); }
            else { element.textContent=source.textContent; }
        }
        function draw() {
            if (!model.customFields || disposed) { return; }
            marker.textContent=''; var state=resolved(), config=state.config;
            marker.style.opacity=state.shown?1:0.2; tank.style.opacity=sample.group==='dead'?0.45:1;
            if (state.fields) {
                state.fields.forEach(function (options,index) {
                    if (!options.enabled) { return; }
                    var field=node('div','dk-vm-text'+(section==='customFields' && index===selected?' is-selected':''),null,marker);
                    styleField(field,options); html(field,M.text(options.format,config,sample));
                    field.addEventListener('click',function () { section='customFields'; selected=index; buildForm(); draw(); });
                });
            } else {
                var nativeText=[]; if (state.native.vehicleName) { nativeText.push('T32'); } if (state.native.playerName) { nativeText.push(sample.name); }
                if (state.native.hp!=='hidden') { nativeText.push(state.native.hp==='percent'?sample.hp+'%':Math.round(1550*sample.hp/100)+' / 1550'); }
                var native=node('div','dk-vm-native-text',nativeText.join(' · '),marker); native.style.color=M.teamColor(config,sample);
            }
            var bar=config.healthBar;
            if ((bar.enabled || state.native.healthBar) && (sample.group!=='dead' || bar.showOnDead)) {
                var bg=node('div','dk-vm-bar',null,marker), fill=node('div','dk-vm-fill',null,bg);
                var style=bar.enabled?bar:{x:-35,y:-22,width:70,height:8,alpha:100,color:'{{c:team}}',background:{color:'#181818',alpha:80},border:{width:1,color:'#000000',alpha:100}};
                bg.style.left=style.x+'rem'; bg.style.top=style.y+'rem'; bg.style.width=style.width+'rem'; bg.style.height=style.height+'rem'; bg.style.opacity=style.alpha/100;
                bg.style.backgroundColor=rgba(style.background.color,style.background.alpha); bg.style.border=style.border.width+'rem solid '+rgba(style.border.color,style.border.alpha);
                if (style.shadow && style.shadow.enabled) {
                    var shadow=style.shadow, angle=shadow.angle*Math.PI/180;
                    bg.style.boxShadow=Math.cos(angle)*shadow.distance+'rem '+Math.sin(angle)*shadow.distance+'rem '+shadow.blur+'rem '+rgba(shadow.color,shadow.alpha);
                }
                fill.style.width=(sample.group==='dead'?0:sample.hp)+'%'; fill.style.backgroundColor=style.color==='{{c:hp}}'?M.hpColor(config,sample):style.color==='{{c:team}}'?M.teamColor(config,sample):style.color;
            }
            var iconOptions=config.icons;
            function icon(kind,text,x,y,visible) {
                var style=iconOptions.enabled?iconOptions[kind]:{enabled:true,scale:1,alpha:100,deadAlpha:40,x:null,y:null};
                if (!style.enabled || !visible) { return; }
                var value=node('div','dk-vm-icon dk-vm-icon-'+kind,text,marker);
                value.style.left=(style.x===null?x:style.x)+'rem'; value.style.top=(style.y===null?y:style.y)+'rem';
                value.style.color=M.teamColor(config,sample); value.style.opacity=style.alpha/100*(sample.group==='dead'?style.deadAlpha/100:1);
                value.style.transform='translateX(-50%) scale('+style.scale+')';
            }
            icon('class','///',0,-4,true); icon('level','VIII',0,-37,state.native.levelIcon);
            icon('vehicle','▰',-55,-18,state.native.vehicleIcon);
        }
        function simulateDamage() {
            if (!model.customFields) { return; }
            var before=sample.hp; sample.hp=Math.max(0,sample.hp-20); hp.update(sample.hp); draw();
            var config=resolved().config, damage=config.damageText, trail=config.healthBar.damage;
            if (trail.enabled && sample.group!=='dead' && before>sample.hp) {
                var bar=marker.querySelector('.dk-vm-bar');
                if (bar) {
                    var tail=node('div','dk-vm-trail',null,bar); tail.style.backgroundColor=trail.color; tail.style.opacity=trail.alpha/100; tail.style.left=sample.hp+'%'; tail.style.width=(before-sample.hp)+'%';
                    timers.push(setTimeout(function () { tail.style.transition='width '+trail.duration+'s linear'; tail.style.width='0%'; },trail.delay*1000));
                }
            }
            if (!damage.enabled) { return; }
            while (effects.children.length>=damage.maxCount) { effects.removeChild(effects.firstChild); }
            var text=node('div','dk-vm-text dk-vm-damage',null,effects); styleField(text,damage); html(text,M.text(damage.format,config,sample,Math.round((before-sample.hp)*1550/100)));
            timers.push(setTimeout(function () { text.style.transition='transform '+damage.duration+'s linear, opacity '+damage.duration+'s linear'; text.style.transform='translateY(-'+damage.rise+'rem)'; text.style.opacity=0; },20));
            timers.push(setTimeout(function () { if (text.parentNode) { text.parentNode.removeChild(text); } },damage.duration*1000+30));
        }
        function update(values) {
            if (disposed) { return; }
            var signature=JSON.stringify(values);
            if (signature===lastValues) { return; }
            if (form.contains(document.activeElement)) { return; }
            var next={};
            try {
                Object.keys(bindings).forEach(function (key) { var raw=values[bindings[key]]; next[key]=(key==='enabled' || key==='debug' || key==='colorRating')?raw:JSON.parse(raw); });
            } catch (_error) { error.textContent=label('invalid'); return; }
            model=next; lastValues=signature; buildForm(); draw();
        }
        return {update:update,dispose:function () {
            disposed=true; timers.forEach(clearTimeout); hp.dispose(); widgets.forEach(function (api) { if (api.dispose) { api.dispose(); } }); root.parentNode.removeChild(root);
        },node:root,notice:notice};
    }
    DK.vehicleMarkersEditor={create:create};
}());
