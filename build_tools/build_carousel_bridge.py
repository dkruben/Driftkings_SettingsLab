"""Patch verified EU carousel integration points, reading game resources only."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RESOURCE = 'gui/gameface/_dist/production/mono/hangar/views/main/main.html/bundle.js'


def patch_bundle(source):
    if 'function dkCarouselConfig' in source:
        raise ValueError('Carousel bridge already applied')
    if 'o as e,s as t,e as a,p as s,r as n,q as i,L as r' not in source:
        raise ValueError('Unsupported Gameface vendor bindings')
    changes = []
    def replace(old, new, count=1):
        nonlocal source
        actual = source.count(old)
        if actual != count:
            raise ValueError('Unsupported hangar bundle: expected %d occurrence(s), found %d: %s' % (count, actual, old[:100]))
        source = source.replace(old, new)
        changes.append(old[:100])
    bridge = '''const dkCarouselRevision=e.box(0);
window.addEventListener("dk-carousel-config",()=>i(()=>dkCarouselRevision.set(dkCarouselRevision.get()+1)));
function dkCarouselConfig(){dkCarouselRevision.get();return window.DKCarouselNative?window.DKCarouselNative.config():null;}
'''
    replace('const[ui,mi]=S("HeroTankModelProvider")',bridge+'const[ui,mi]=S("HeroTankModelProvider")')
    replace('function Hi(e,t,a,s){','function Hi(e,t,a,s){const dk=dkCarouselConfig();if(dk){const value=window.DKCarouselNative.compare(a,s,e);if(value!==null)return value;}')
    replace('h=q.primitive(()=>{const e=[...m.getAll()]','h=q.primitive(()=>{dkCarouselConfig();const e=[...m.getAll()]')
    old='Hh=(e,t)=>({left:[...t!=sr?[Oh.rentTank]:[]],right:[Oh.buyTank,...e>0?[Oh.restoreTank]:[],Oh.buySlot]})'
    new='Hh=(e,t)=>{const dk=dkCarouselConfig(),allow=key=>!dk||window.DKCarouselNative.actionAllowed(key);return{left:[...t!=sr?[Oh.rentTank]:[]].filter(allow),right:[Oh.buyTank,...e>0?[Oh.restoreTank]:[],Oh.buySlot].filter(allow)}}'
    replace(old,new)
    replace('function(e,t,a,s){return n.useMemo(()=>{if(!t)return{activeSlotsAmount:0', 'function(e,t,a,s){const dk=dkCarouselConfig();return n.useMemo(()=>{if(!t)return{activeSlotsAmount:0')
    replace('}},[a,e,t,s])}(u,y,f,d)', '}},[a,e,t,s,dk])}(u,y,f,d)')
    replace('o.jsx("div",{className:l(_y.base,a),children:', 'o.jsx("div",{onWheelCapture:event=>{if(dkCarouselConfig())window.DKCarouselNative.wheel(e,event)},className:l(_y.base,a),children:')
    replace('const a=function(e){const t=We(ny.default,ny.breakpoints);return jt(2===e?t.double:t.single)}(t)', 'const dk=dkCarouselConfig(),dkNativeWidth=function(e){const t=We(ny.default,ny.breakpoints);return jt(2===e?t.double:t.single)}(t),a=dk?window.DKCarouselNative.footprint(t):dkNativeWidth')
    replace('function wy({api:e,carouselRows:t}){', 'function wy({api:e,carouselRows:t}){if(dkCarouselConfig())t=window.DKCarouselNative.rowCount(t);')
    replace('s&&i(2!==t?{visibleSlots:', 's&&i(t<=1?{visibleSlots:')
    replace('N=(j=w,n.useMemo(()=>{const e=[];for(let t=0;t<j.length;t+=2)e.push(j.slice(t,t+2));return 1===e.at(-1)?.length&&e.at(-1)?.push(Yx),e},[j]))',
            'N=(j=w,n.useMemo(()=>{if(dkCarouselConfig())return window.DKCarouselNative.groupColumns(j,v,Yx);const e=[];for(let t=0;t<j.length;t+=2)e.push(j.slice(t,t+2));return 1===e.at(-1)?.length&&e.at(-1)?.push(Yx),e},[j,v]))')
    replace('function(e,t,a,s,n){const i=2===s;function r(s)', 'function(e,t,a,s,n){const i=s>1;function r(s)')
    replace('totalElements:2===v?N.length:w.length', 'totalElements:v>1?N.length:w.length')
    replace('return 2===v?o.jsx(Dt,', 'return v>1?o.jsx(Dt,')
    replace('elementWidth:t-jt(1),direction:"horizontal"','elementWidth:dkCarouselConfig()?t:t-jt(1),direction:"horizontal"')
    replace('function oy({slotId:e,width:t,currentVehicleId:a,double:s,className:n}){','function oy({slotId:e,width:t,currentVehicleId:a,double:s,className:n}){if(dkCarouselConfig())t-=window.DKCarouselNative.gap(s?2:1);')
    replace('children:Ii.map(e=>o.jsx(sx,','children:(dkCarouselConfig()?window.DKCarouselNative.vehicleTypes(Ii):Ii).map(e=>o.jsx(sx,')
    replace('u=a.filter(e=>(0!==i.length||"rented"!==e)', 'u=a.filter(e=>(!dkCarouselConfig()||window.DKCarouselNative.filterAllowed(e))&&(0!==i.length||"rented"!==e)')
    replace('fg=r(function({type:e}){const t=ir()', 'fg=r(function({type:e}){const dk=dkCarouselConfig(),extra=dk?window.DKCarouselNative.counts(e):"";const t=ir()')
    # Extra counts accompany prices; no purchase price or available-slot model is changed.
    replace('children:s})})});if(e===Oh.rentTank)', 'children:extra?o.jsxs(o.Fragment,{children:[s,o.jsx("span",{style:{marginLeft:"6px"},children:extra})]}):s})})});if(e===Oh.rentTank)')
    replace('params:{count:n}}),e===Oh.restoreTank', 'params:{count:n}}),extra&&e===Oh.buyTank&&o.jsx("span",{style:{marginLeft:"6px"},children:extra}),e===Oh.restoreTank')
    return source, changes


def build():
    cfg = json.loads((ROOT/'build_data/build_config.json').read_text())
    game = Path(cfg['game_root'])
    package = game/'res/packages/gui-part3.pkg'
    with zipfile.ZipFile(package) as archive:
        original = archive.read(RESOURCE)
    result, changes = patch_bundle(original.decode('utf-8'))
    folder = ROOT/'build/gameface/carousel';folder.mkdir(parents=True,exist_ok=True)
    (folder/'bundle.js').write_text(result,encoding='utf-8')
    (folder/'patch-report.json').write_text(json.dumps({'game_version':cfg['game_version'],
        'source':str(package),'sha256':hashlib.sha256(original).hexdigest(),'hooks':changes},indent=2))
    print('Gameface carousel bridge: %d verified hooks' % len(changes))


if __name__ == '__main__':build()
