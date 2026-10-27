/* Existing spectrum picker, adapted to the redesigned panel's modal lifetime. */
(function () {
    'use strict';
    var DK=window.DK;
    var normalizeHex=DK.colors.normalizeColor;
    function el(tag,classes,text,parent){return DK.h(tag+(classes?'.'+classes.split(' ').join('.'):''),null,text,parent);}
    function label(key,fallback){return DK.t(key,fallback);}
    function textInput(type,def){return DK.h('input.dk-field',{type:type,maxLength:def.maxLength});}
    function handled(event){DK.stop(event);}
    function flashInvalid(node){DK.toggle(node,'is-invalid',true);}
    function onCommit(node,fn){
        node.addEventListener('blur',fn);
        node.addEventListener('keydown',function(event){if(event.keyCode===13){DK.stop(event);fn();}});
    }
    function open(options,done){
        var value=normalizeHex(options.value)||'#FFFFFF';
        var hasAlpha=options.alpha!==null&&options.alpha!==undefined;
        var alpha=hasAlpha?options.alpha:100;
    var draft = value, draftAlpha = alpha, position = DK.colors.spectrumPosition(value), x = position.x, y = position.y;
    var panel = el('div', 'dk-color-picker');
    el('div','dk-dialog-title',options.title||label('color.pick','Color'),panel);
    var area = el('div', 'dk-spectrum', null, panel);
    area.tabIndex = 0; area.setAttribute('aria-label', label('color.area', 'Color spectrum'));
    // Hue runs down the area; the left half darkens it to black and the right half lightens it to white,
    // the same blend DK.colors.spectrum computes. Gradient layers avoid canvas pixel writes, which Gameface lacks.
    el('div', 'dk-spectrum-dark', null, area); el('div', 'dk-spectrum-light', null, area);
    var cursor = el('div', 'dk-spectrum-cursor', null, area);
    var previews = el('div', 'dk-color-comparison', null, panel);
    function preview(label) {
        var box=el('div', '', null, previews); el('div','dk-color-title',label,box);
        return el('div','dk-color-preview dk-checker',null,box);
    }
    var current=preview(label('color.current', 'Current')), next=preview(label('color.new', 'New'));
    var currentFill=el('div','dk-preview-fill',null,current), nextFill=el('div','dk-preview-fill',null,next);
    currentFill.style.backgroundColor=value; currentFill.style.opacity=alpha/100;
    el('div','dk-color-title','HEX',panel);
    var hexInput=textInput('text',{maxLength:8}); panel.appendChild(hexInput);
    var alphaWidget=null, alphaLabel=null;
    function render() {
        cursor.style.left=(x*100)+'%'; cursor.style.top=(y*100)+'%';
        nextFill.style.backgroundColor=draft; nextFill.style.opacity=draftAlpha/100;
        hexInput.value=draft;
        if (alphaLabel) { alphaLabel.textContent=Math.round(draftAlpha)+'%'; }
    }
    function select(e) {
        var rect=area.getBoundingClientRect(); x=Math.max(0,Math.min(1,(e.clientX-rect.left)/Math.max(1,rect.width)));
        y=Math.max(0,Math.min(1,(e.clientY-rect.top)/Math.max(1,rect.height))); draft=DK.colors.spectrum(x,y); render();
    }
    function stop() { document.removeEventListener('mousemove',select); document.removeEventListener('mouseup',stop); }
    area.addEventListener('mousedown',function(e) { handled(e); DK.focus(area); select(e); document.addEventListener('mousemove',select); document.addEventListener('mouseup',stop); });
    area.addEventListener('keydown',function(e) {
        if ([37,38,39,40].indexOf(e.keyCode)<0) { return; } handled(e);
        var step=e.shiftKey ? 0.05 : 0.005;
        x=Math.max(0,Math.min(1,x+(e.keyCode===37?-step:e.keyCode===39?step:0)));
        y=Math.max(0,Math.min(1,y+(e.keyCode===38?-step:e.keyCode===40?step:0)));
        draft=DK.colors.spectrum(x,y); render();
    });
    function readHex() { var hex=normalizeHex(hexInput.value); if (!hex) { flashInvalid(hexInput); return false; } DK.toggle(hexInput,'is-invalid',false); draft=hex; position=DK.colors.spectrumPosition(draft); x=position.x; y=position.y; render(); return true; }
    onCommit(hexInput,readHex);
    if (hasAlpha) {
        el('div','dk-color-title',label('color.alpha','Alpha'),panel);
        var alphaHost=el('div','dk-alpha dk-checker',null,panel);
        alphaWidget=DK.controls.create({id:'alpha',type:'slider',label:label('color.alpha','Alpha'),min:0,max:100,step:1}, {
            commit:function(id,n){draftAlpha=n; alphaWidget.set(n); render();},
            preview:function(id,n){draftAlpha=n; render();}
        });
        alphaHost.appendChild(alphaWidget.node);
        alphaLabel=el('div','dk-alpha-value',null,panel);
        alphaWidget.set(draftAlpha);
    }
    if (options.presets) {
        var presets=el('div','dk-presets',null,panel);
        options.presets.forEach(function(p) { var btn=el('button','dk-preset',null,presets); btn.style.backgroundColor=p.value; btn.title=p.label;
            btn.addEventListener('click',function(){ draft=normalizeHex(p.value); position=DK.colors.spectrumPosition(draft); x=position.x; y=position.y; render(); }); });
    }
    var actions=el('div','dk-modal-actions',null,panel);
    el('button','dk-button',label('cancel', 'Cancel'),actions).addEventListener('click',function(){modal.close('cancel');});
    el('button','dk-button is-primary',label('apply', 'Apply'),actions).addEventListener('click',function(){if(readHex()){modal.close('apply');}});
    render();
    var modal=DK.modal.open(panel,{origin:options.origin,className:'dk-modal-spectrum',onClose:function(reason){
        stop();
        if(alphaWidget){alphaWidget.dispose();}
        if(reason==='apply'){done(draft,hasAlpha?draftAlpha:null);}
    }});
    return modal;
    }
    DK.colorPicker={open:open,toScale:DK.colors.alphaFromUi,fromScale:function(value,scale){
        var result=DK.colors.alphaToUi(value,scale);return result===null?100:result;
    }};
}());
