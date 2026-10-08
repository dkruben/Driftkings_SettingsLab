(function (root, factory) {
    if (typeof module === 'object' && module.exports) { module.exports = factory(); }
    else { root.DKCarouselLayout = factory(); }
}(this, function () {
    'use strict';
    var selectors = {
        flag:'[class*="Background_flag_"]', tankIcon:'[class*="Background_vehicle_"]',
        tankType:'[class*="Information_identifierIcon_"]', level:'[class*="Information_text__level_"]',
        xp:'[class*="Background_multiplier_"]', tankName:'[class*="Information_truncatedText_"]',
        info:'[class*="Information_info_"]', favorite:'[class*="Background_favorite_"]',
        progressionPoints:'[class*="Information_battlePass_"]'
    };
    function color(value, fallback) {
        value = String(value || '').replace(/^0x/i,'#');
        if (/^[0-9a-f]{6}$/i.test(value)) { value = '#'+value; }
        return /^#[0-9a-f]{6}$/i.test(value) ? value : fallback;
    }
    function localIcon(value, images) {
        if (typeof value !== 'string' || value.indexOf('..') !== -1) return '';
        if (/^mods\/Driftkings\/Carroucel\/[#a-zA-Z0-9_-]+\.png$/.test(value)) {
            var image = images && images[value];
            return typeof image === 'string' && /^data:image\/png;base64,[A-Za-z0-9+/=]+$/.test(image) ? image : '';
        }
        value = value.replace(/^img:\/\//,'coui://');
        if (/^gui\/[a-zA-Z0-9_./-]+\.(png|dds|webp)$/i.test(value)) value='coui://'+value;
        return /^coui:\/\/gui\/[a-zA-Z0-9_./-]+\.(png|dds|webp)$/i.test(value) ? value : '';
    }
    function profileName(type, doubled) { return type === 'normal' || type === 'small' ? type : doubled ? 'small' : 'normal'; }
    function rgba(value, alpha) {
        var hex=color(value,'#000000').slice(1), n=parseInt(hex,16);
        return 'rgba('+[(n>>16)&255,(n>>8)&255,n&255,alpha/100].join(',')+')';
    }
    function richText(parent, value, document, images, showIcons) {
        // Only formatting tags are interpreted. No user HTML is inserted into DOM.
        var current=parent, stack=[parent], parts=String(value || '').split(/(<[^>]*>)/g);
        parts.forEach(function (part) {
            if (!part) return;
            var close=/^<\/(b|i|u|font)>$/i.exec(part), open=/^<(b|i|u|font)(\s[^>]*)?>$/i.exec(part);
            if (close) { if(stack.length>1) stack.pop(); current=stack[stack.length-1]; return; }
            if (/^<br\s*\/?>$/i.test(part)) { current.appendChild(document.createElement('br')); return; }
            if (/^<img\s[^>]*>$/i.test(part)) {
                if (showIcons === false) return;
                var attrsImage={}, pair, attrPattern=/(src|width|height)\s*=\s*(['"])(.*?)\2/gi;
                while ((pair=attrPattern.exec(part))) attrsImage[pair[1].toLowerCase()]=pair[3];
                var source=localIcon(attrsImage.src,images);
                if (source) {
                    var image=document.createElement('img'); image.src=source; image.alt='';
                    ['width','height'].forEach(function (key) {
                        var size=Number(attrsImage[key]);
                        if (isFinite(size) && size>0) image.style[key]=Math.min(600,size)+'px';
                    });
                    image.onerror=function () { this.style.display='none'; };
                    current.appendChild(image);
                }
                return;
            }
            if (open) {
                var node=document.createElement('span'), tag=open[1].toLowerCase();
                if(tag==='b') node.style.fontWeight='bold';
                if(tag==='i') node.style.fontStyle='italic';
                if(tag==='u') node.style.textDecoration='underline';
                var attrs=open[2] || '', match, regex=/(color|size|face|alpha)\s*=\s*(['"])(.*?)\2/gi;
                while((match=regex.exec(attrs))) {
                    var key=match[1].toLowerCase(), val=match[3];
                    if(key==='color') node.style.color=color(val,'#FFFFFF');
                    if(key==='size' && /^\d{1,2}$/.test(val)) node.style.fontSize=Math.max(8,Math.min(40,Number(val)))+'px';
                    // Flash's default font alias inherits the native Gameface font.
                    if(key==='face' && val!=='$FieldFont' && /^[\w $,-]{1,60}$/.test(val)) node.style.fontFamily=val==='mono'?'Consolas,monospace':val;
                    if(key==='alpha' && /^#[0-9a-f]{2}$/i.test(val)) node.style.opacity=parseInt(val.slice(1),16)/255;
                    else if(key==='alpha' && /^\d{1,3}$/.test(val)) node.style.opacity=Math.min(100,Number(val))/100;
                }
                current.appendChild(node); stack.push(node); current=node; return;
            }
            if(part.charAt(0)==='<') return;
            current.appendChild(document.createTextNode(part.replace(/&#(x[0-9a-f]+|\d+);/gi,function (_,number) {
                var code=number.charAt(0).toLowerCase()==='x'?parseInt(number.slice(1),16):parseInt(number,10);
                return code>0 && code<=65535 ? String.fromCharCode(code) : '';
            }).replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&amp;/g,'&')));
        });
    }
    function mount(card, profile, document, images) {
        var changes=[], layers=[];
        function change(node,key,value) {
            var before=node.style[key]; node.style[key]=value;
            changes.push({node:node,key:key,before:before,after:node.style[key]});
        }
        if(getComputedStyle(card).position==='static') change(card,'position','relative');
        Object.keys(profile.fields || {}).forEach(function (key) {
            if(!selectors[key]) return;
            var setting=profile.fields[key], nodes=card.querySelectorAll(selectors[key]);
            for(var i=0;i<nodes.length;i++) {
                var node=nodes[i];
                if(setting.enabled===false) change(node,'visibility','hidden');
                if(setting.alpha!==100) change(node,'opacity',String(setting.alpha/100));
                if(setting.dx || setting.dy || setting.scale!==1) {
                    var base=getComputedStyle(node).transform;
                    change(node,'transform',(base==='none'?'':base+' ')+'translate('+setting.dx+'rem,'+setting.dy+'rem) scale('+setting.scale+')');
                }
            }
        });
        var width=card.clientWidth, height=card.clientHeight;
        ['substrate','top'].forEach(function (level) {
            var layer=document.createElement('div'); layer.className='dk-carousel-stats';
            layer.style.width=profile.width+'px'; layer.style.height=profile.height+'px';
            layer.style.transform='scale('+(width/profile.width)+','+(height/profile.height)+')';
            layer.style.transformOrigin='0 0'; layer.style.zIndex=level==='top'?'10':'0';
            profile.extraFields.forEach(function (field) {
                if(field.layer!==level) return;
                var node=document.createElement('div'); node.className='dk-carousel-field';
                node.style.left=field.x+'px'; node.style.top=field.y+'px'; node.style.fontSize=field.fontSize+'px';
                node.style.color=color(field.color,'#FFFFFF'); node.style.opacity=field.alpha/100;
                node.style.transform=field.align==='right'?'translateX(-100%)':field.align==='center'?'translateX(-50%)':'';
                if(field.width) node.style.width=field.width+'px';
                if(field.height) node.style.height=field.height+'px';
                if(field.bgColor) node.style.backgroundColor=color(field.bgColor,'transparent');
                var shadow=field.shadow;
                var angle=(shadow.angle===undefined?45:shadow.angle)*Math.PI/180;
                var effect=(shadow.distance*Math.cos(angle))+'px '+(shadow.distance*Math.sin(angle))+'px '+shadow.blur+'px '+rgba(shadow.color,shadow.alpha);
                var repeats=Math.max(1,Math.min(5,Math.round(shadow.strength || 1))), effects=[];
                while(repeats--) effects.push(effect);
                node.style.textShadow=shadow.enabled ? effects.join(',') : 'none';
                var icon=field.showIcons===false?'':localIcon(field.src,images);
                if(icon) {
                    var img=document.createElement('img'); img.src=icon; img.alt='';
                    img.style.width=(field.format ? field.iconSize : field.width || field.iconSize)+'px';
                    img.style.height=(field.format ? field.iconSize : field.height || field.iconSize)+'px';
                    img.onerror=function () { this.style.display='none'; }; node.appendChild(img);
                }
                var span=document.createElement('span'); richText(span,field.format,document,images,field.showIcons); node.appendChild(span);
                layer.appendChild(node);
            });
            if(level==='substrate') card.insertBefore(layer,card.firstChild);
            else card.appendChild(layer);
            layers.push(layer);
        });
        return function () {
            layers.forEach(function (layer) { if(layer.parentNode) layer.parentNode.removeChild(layer); });
            changes.reverse().forEach(function (entry) { if(entry.node.style[entry.key]===entry.after) entry.node.style[entry.key]=entry.before; });
        };
    }
    return {color:color,localIcon:localIcon,profileName:profileName,richText:richText,mount:mount};
}));
