import {createResultsBinding} from './results_binding.js';
import {loadResultsAssets} from '../shared/native_assets.js';

export function create({React,scope,report,createFlashText}, environment){
 const env=environment||{root:window,document:window.document,engine:engine,viewEnv:viewEnv};
 const document=env.document;let dead=false;
 const shared=env.root.DriftkingsFlashText;
 const flashText=shared&&typeof shared.inert==='function'&&typeof shared.copy==='function'?shared:(createFlashText&&createFlashText(document));
    function formatSeparators(parent) {
        var children = Array.prototype.slice.call(parent.childNodes);
        for (var i = 0; i < children.length; i++) {
            var child = children[i];
            if (child.nodeType === 1) { formatSeparators(child); continue; }
            if (child.nodeType !== 3) { continue; }
            var value = child.nodeValue, pattern = / *\| *|\t/g, match, offset = 0;
            while ((match = pattern.exec(value)) !== null) {
                if (match.index > offset) {
                    parent.insertBefore(document.createTextNode(value.slice(offset, match.index)), child);
                }
                var spacer = document.createElement('span');
                spacer.className = match[0] === '\t' ? 'dk-results-tab' : 'dk-results-separator';
                parent.insertBefore(spacer, child);
                offset = pattern.lastIndex;
            }
            if (offset) {
                if (offset < value.length) { parent.insertBefore(document.createTextNode(value.slice(offset)), child); }
                parent.removeChild(child);
            }
        }
    }

    function render(node,data){
        while(node.firstChild)node.removeChild(node.firstChild);
        if(!data.enabled||!data.html)return;
        var parsed = document.createElement('div');
        parsed.innerHTML = flashText.inert(data.html.replace(/<tab\s*\/?\s*>/gi, '\t'));
        flashText.copy(parsed, node, {fontFamily: true, fontAlpha: true, sizeUnit: 'rem'});
        formatSeparators(node);
    }
 function Component(){
  const [payload,setPayload]=React.useState({enabled:false}),host=React.useRef(null);
  React.useEffect(()=>{let active=true;const binding=createResultsBinding({...env,onPayload:data=>{if(active&&!dead&&!scope.closed)setPayload(data);},onError:()=>{if(active)setPayload({enabled:false});report({phase:'binding',event:'BINDING_FAILED',success:false,errorClassification:'BINDING_ERROR'});}});
   scope.defer(()=>{active=false;binding.dispose();});binding.start();return()=>{active=false;void scope.dispose();};
  },[]);
  React.useLayoutEffect(()=>{const node=host.current;if(node&&!dead)render(node,payload);return()=>{if(node)while(node.firstChild)node.removeChild(node.firstChild);};},[payload]);
  return !dead&&payload.enabled&&payload.html?React.createElement('div',{id:'dk-battle-efficiency',ref:host}):null;
 }
 return {async init(){await env.engine.whenReady;if(scope.closed)return;if(!flashText||!flashText.inert||!flashText.copy)throw new Error('FlashText unavailable');await loadResultsAssets(scope,document,env.root);},Component,destroy(){dead=true;return scope.dispose();}};
}
