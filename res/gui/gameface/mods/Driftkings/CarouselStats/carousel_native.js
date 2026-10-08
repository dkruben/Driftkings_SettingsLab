(function (root, factory) {
    if (typeof module === 'object' && module.exports) { module.exports = factory(null); }
    else { root.DKCarouselNative = factory(root); }
}(this, function (root) {
    'use strict';
    var data = null, signature = '', sheet = null;
    var nations = ['ussr','germany','usa','china','france','uk','japan','czech','sweden','poland','italy'];
    var types = ['lightTank','mediumTank','heavyTank','AT-SPG','SPG'];
    function config() { return data && data.config && data.config.visible ? data.config : null; }
    function bounded(value, lo, hi, fallback) { value=Number(value);return isFinite(value)?Math.max(lo,Math.min(hi,value)):fallback; }
    function rowCount(nativeRows) { var c=config();return Math.round(bounded(c?c.effectiveRows:nativeRows,1,4,1)); }
    function groupColumns(slots, rows, empty) {
        rows=Math.round(bounded(rows,1,4,1));
        var columns=[];
        for(var i=0;i<slots.length;i+=rows) {
            var column=slots.slice(i,i+rows);
            while(column.length<rows) column.push(empty);
            columns.push(column);
        }
        return columns;
    }
    function profile(rows) { var c=config();return c && c[c.cellType==='normal'||c.cellType==='small'?c.cellType:rows>1?'small':'normal']; }
    function footprint(rows) { var p=profile(rows);return p ? p.width+p.gap : null; }
    function gap(rows) { var p=profile(rows);return p?p.gap:0; }
    function actionAllowed(name) {
        var c=config(), key={buyTank:'hideBuyTank',buySlot:'hideBuySlot',restoreTank:'hideRestoreTank'}[name];
        return !c || !key || !c[key];
    }
    function filterAllowed(name) { var c=config();return !c || !c.filters[name] || c.filters[name].enabled!==false; }
    function ordered(values, custom) {
        return (custom||[]).filter(function (value) { return values.indexOf(value)!==-1; }).concat(values.filter(function (value) { return (custom||[]).indexOf(value)===-1; }));
    }
    function vehicleTypes(values) { var c=config();return c?ordered(values,c.types_order):values; }
    function value(vehicle, key, nativeNations) {
        var c=config(), stats=(data.sortValues||{})[String(vehicle.id)]||{};
        if(key==='nation') {
            var name=nations[vehicle.nationId], order=c.nations_order||[];
            if(order.length) return ordered(nations,order).indexOf(name);
            return nativeNations && nativeNations[name]!==undefined?nativeNations[name]:vehicle.nationId;
        }
        if(key==='type') return ordered(types,c.types_order).indexOf(vehicle.type);
        if(key==='premium') return vehicle.premium?0:1;
        if(key==='level') return vehicle.level;
        return stats[key];
    }
    function compare(a,b,nativeNations) {
        var c=config();if(!c||!c.sorting_criteria.length)return null;
        if(a.favorite!==b.favorite)return a.favorite?-1:1;
        for(var i=0;i<c.sorting_criteria.length;i++) {
            var token=c.sorting_criteria[i], reverse=token.charAt(0)==='-', key=reverse?token.slice(1):token;
            var x=value(a,key,nativeNations),y=value(b,key,nativeNations);
            var absentX=x===null||x===undefined, absentY=y===null||y===undefined;
            if(absentX!==absentY)return absentX?1:-1;
            if(!absentX&&x!==y)return (x<y?-1:1)*(reverse?-1:1);
        }
        var name=String(a.shortName||'').localeCompare(String(b.shortName||''));
        return name || Number(a.id)-Number(b.id);
    }
    function wheel(api,event) {
        var c=config();if(!c||c.scrollingSpeed===1||api.disabled)return;
        var delta=event.deltaX||event.deltaY;
        if(!delta)return;
        var units=event.deltaMode===1?16:event.deltaMode===2?api.getWrapperSize():1;
        event.preventDefault();event.stopPropagation();
        api.applyScroll(api.animationScroll.scrollPosition.get()+delta*units*c.scrollingSpeed);
    }
    function counts(name) {
        var c=config();if(!c)return '';
        if(name==='buyTank'&&c.showTotalSlots)return String(c.totalSlots)+' / '+String(c.freeSlots);
        if(name==='buySlot'&&c.showUsedSlots)return String(c.usedSlots)+' / '+String(c.totalSlots);
        return '';
    }
    function styles(c) {
        if(!c)return '';
        var rows=rowCount(c.effectiveRows),p=profile(rows), prefix='[class*="Page_carousel_"] ';
        var out=prefix+'{height:'+(p.height*rows+p.gap*(rows-1))+'px!important;background:rgba(0,0,0,'+(c.backgroundAlpha/100*.6)+');}';
        out+=prefix+'[data-name="Slot"]{height:'+p.height+'px!important;}';
        out+=prefix+'[class*="ActiveSlots_doubleSlots_"]{display:flex;flex-direction:column;gap:'+p.gap+'px;}';
        out+=prefix+'[class*="Background_1089"],'+prefix+'[class*="ActionCards_wrapper_"]{background-color:rgba(10,10,10,'+(c.slotBackgroundAlpha/100*.3)+')!important;}';
        // Gameface has no :not selector; the following border rule overrides this one.
        out+=prefix+'[class*="Slot_selected_"]{opacity:'+(c.slotBorderAlpha/100)+';}';
        out+=prefix+'[class*="Slot_selected__border"]{opacity:'+(c.slotSelectedBorderAlpha/100)+';}';
        if(!c.enableLockBackground)out+=prefix+'[class*="Content_disabledOverlay_"]{background-image:none!important;}';
        var a=(1-c.edgeFadeAlpha/100).toFixed(3), edge='rgba(0,0,0,'+a+')';
        out+=prefix+'[class*="CarouselNavButtons_mask_"]{mask:linear-gradient(to left,'+edge+',#000 4%)!important;}';
        out+=prefix+'[class*="CarouselNavButtons_mask__both"]{mask:linear-gradient(to right,'+edge+',#000 4%,#000 96%,'+edge+')!important;}';
        out+=prefix+'[class*="CarouselNavButtons_mask__left"]{mask:linear-gradient(to right,'+edge+',#000 4%)!important;}';
        if(!c.filters.params.enabled)out+='[class*="Page_filterTrigger_"]{display:none!important;}';
        out+='[class*="FilterPopover_toggleContainer_"]{column-gap:'+c.filtersPadding.horizontal+'px;row-gap:'+c.filtersPadding.vertical+'px;margin-left:0!important;}';
        out+='[class*="FilterPopover_toggle_"]{margin:0!important;}';
        return out;
    }
    function setData(next) {
        var nextSignature=JSON.stringify([next.config,next.sortValues]);
        if(nextSignature===signature)return;
        signature=nextSignature;data=next;
        if(root) {
            if(!sheet){sheet=root.document.createElement('style');sheet.id='dk-carousel-options';root.document.head.appendChild(sheet);}
            sheet.textContent=styles(config());
            root.dispatchEvent(new root.Event('dk-carousel-config'));
        }
    }
    function dispose(){setData({});if(sheet&&sheet.parentNode)sheet.parentNode.removeChild(sheet);sheet=null;}
    return {config:config,setData:setData,dispose:dispose,compare:compare,ordered:ordered,actionAllowed:actionAllowed,
            rowCount:rowCount,groupColumns:groupColumns,
            filterAllowed:filterAllowed,vehicleTypes:vehicleTypes,footprint:footprint,gap:gap,wheel:wheel,counts:counts,styles:styles};
}));
