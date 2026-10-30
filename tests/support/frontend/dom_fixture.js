/* Minimal DOM for frontend contract and lifecycle regressions. */
const assert=require('assert'), fs=require('fs'), path=require('path'), vm=require('vm');
const root=path.resolve(__dirname,'../../..');
const jsRoot=path.join(root,'mod/res/gui/gameface/mods/driftkings/settings_window/js');
class Node {
    constructor(tag) {
        this.tagName = String(tag).toUpperCase(); this.childNodes = []; this.parentNode = null;
        this.style = {}; this.className = ''; this.attributes = {}; this.listeners = {};
        this._text = ''; this.nodeType=1; this.scrollTop=0; this.clientHeight=800; this.scrollHeight=800; this.clientWidth=1280; this.disabled = false; this.value = '';
    }
    set innerHTML(value){
        const text=String(value).replace(/&#x([0-9a-f]+);/gi,(_,n)=>String.fromCodePoint(parseInt(n,16)))
            .replace(/&#(\d+);/g,(_,n)=>String.fromCodePoint(Number(n)))
            .replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&apos;/g,"'").replace(/&amp;/g,'&');
        this.textContent=text;if(this.tagName==='TEXTAREA'){this.value=text;}
    }
    get children() { return this.childNodes.filter(n=>n.nodeType===1); }
    get firstChild() { return this.childNodes[0] || null; }
    get lastChild() { return this.childNodes[this.childNodes.length - 1] || null; }
    contains(other) { return other === this || this.childNodes.some(child => child.contains(other)); }
    remove() { if (this.parentNode) { this.parentNode.removeChild(this); } }
    querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
    get textContent() { return this._text + this.childNodes.map(child => child.textContent).join(''); }
    set textContent(value) { this._text = String(value); this.childNodes.forEach(child => { child.parentNode = null; }); this.childNodes = []; }
    get tabIndex() { return this._tabIndex === undefined ? (/^(BUTTON|INPUT|TEXTAREA)$/.test(this.tagName) ? 0 : -1) : this._tabIndex; }
    set tabIndex(value) { this._tabIndex = value; }
    appendChild(child) {
        if (child.isFragment) { child.childNodes.slice().forEach(node => this.appendChild(node)); return child; }
        if (child.parentNode) { child.parentNode.removeChild(child); }
        child.parentNode = this; this.childNodes.push(child); return child;
    }
    removeChild(child) { this.childNodes = this.childNodes.filter(node => node !== child); child.parentNode = null; return child; }
    addEventListener(type, handler) { (this.listeners[type] = this.listeners[type] || []).push(handler); }
    removeEventListener(type, handler) { this.listeners[type] = (this.listeners[type] || []).filter(h => h !== handler); }
    fire(type, extra) {
        const event = Object.assign({type, target: this, button: 0, clientX: 10, clientY: 10, preventDefault() {}, stopPropagation() {}}, extra);
        (this.listeners[type] || []).slice().forEach(handler => handler.call(this, event));
    }
    setAttribute(name, value) { this.attributes[name] = String(value); }
    getAttribute(name) { return name in this.attributes ? this.attributes[name] : null; }
    getBoundingClientRect() { return {left: 0, top: 0, right: 100, bottom: 20, width: 100, height: 20}; }
    focus() { this.ownerDocument.activeElement = this; }
    blur() { if(this.ownerDocument.activeElement===this){this.ownerDocument.activeElement=null;} this.fire('blur'); }
    insertBefore(child,before){if(!before){return this.appendChild(child);} if(child.parentNode){child.parentNode.removeChild(child);} child.parentNode=this;this.childNodes.splice(this.childNodes.indexOf(before),0,child);return child;}
    getContext() { return null; }
    matches(selector) {
        return selector.split(',').some(part => {
            part = part.trim();
            if(part==='[data-property]'){return this.getAttribute('data-property')!==null;}
            if (part === '[tabindex]') { return this._tabIndex !== undefined; }
            if (part[0] === '.') { return this.className.split(' ').indexOf(part.slice(1)) >= 0; }
            return this.tagName === part.toUpperCase();
        });
    }
    querySelectorAll(selector) {
        const found = [];
        const walk = node => node.childNodes.forEach(child => { if (child.matches(selector)) { found.push(child); } walk(child); });
        walk(this); return found;
    }
    get offsetWidth() { return 100; }
    get offsetHeight() { return 20; }
}


function createEnvironment(){
    const timers=new Map();let timerId=0, callbacks=null;
    const document={listeners:{},activeElement:null,
        createElement(tag){const n=new Node(tag);n.ownerDocument=document;return n;},
        createTextNode(text){const n=this.createElement('#text');n.nodeType=3;n.textContent=text;n.nodeValue=text;return n;},
        createDocumentFragment(){return Object.assign(this.createElement('fragment'),{isFragment:true});},
        getElementById(id){return {'dk-app':app,'dk-theme':themeStyle}[id];},
        addEventListener(type,fn){(this.listeners[type]=this.listeners[type]||[]).push(fn);},
        removeEventListener(type,fn){this.listeners[type]=(this.listeners[type]||[]).filter(f=>f!==fn);}
    };
    document.body=document.createElement('body');document.documentElement=document.createElement('html');
    const app=document.createElement('main'),themeStyle=document.createElement('style');document.body.appendChild(app);
    const window={innerWidth:1920,innerHeight:1080,addEventListener(){},removeEventListener(){}};
    const sent=[];
    const context={window,document,console,JSON,Math,Date,Object,Array,String,Number,isFinite,parseFloat,parseInt,
        setTimeout(fn){timers.set(++timerId,fn);return timerId;},clearTimeout(id){timers.delete(id);}};
    vm.createContext(context);
    function load(name){vm.runInContext(fs.readFileSync(path.join(jsRoot,name),'utf8'),context,{filename:name});}
    const html=fs.readFileSync(path.join(jsRoot,'../window.html'),'utf8');
    const scripts=html.match(/js\/[a-z_]+\.js/g).map(s=>s.slice(3));
    const catalog=fs.readFileSync(path.join(root,'mod/res/scripts/client/driftkings/interface_catalog.py'),'utf8');
    assert.deepStrictEqual(catalog.match(/settings_window\/js\/[a-z_]+\.js/g).map(s=>s.split('/').pop()),scripts);
    scripts.forEach(name=>{
        if(name==='bridge.js'){
            window.DK.bridge={start(next){callbacks=next;},send(action,data){sent.push([action,data||{}]);},unit:()=>1,
                clientRem:()=>({width:window.innerWidth,height:window.innerHeight}),dispose(){}};
        }else{load(name);}
    });
    return {DK:window.DK,window,document,app,themeStyle,sent,context,timers,load,get callbacks(){return callbacks;},
        flush(){const pending=Array.from(timers.values());timers.clear();pending.forEach(fn=>fn());}};
}
module.exports={createEnvironment,Node,root,jsRoot};
