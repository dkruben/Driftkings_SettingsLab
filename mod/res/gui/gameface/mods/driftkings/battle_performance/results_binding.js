// Resource ID selects a layout; model reference and generation select its live instance.
export function createResultsBinding({root,engine,viewEnv,onPayload,onError}){
 let disposed=false,started=false,current=null,generation=0;const listeners=[];
 function clear(){generation++;const old=current;current=null;try{onPayload({enabled:false});}finally{if(old&&old.callback!==null)viewEnv.removeDataChangedCallback(old.callback,old.id);}}
 function reconcile(){if(disposed)return;try{
  const ids=root.subViews?root.subViews.ids():[];let selected=null;
  for(const id of ids){const child=root.subViews.get(id),model=child&&child.model;if(model&&model.DriftkingsUI&&model.DriftkingsUI.name==='driftkingsbattleEfficiency'){selected={id,child,model};break;}}
  if(!selected){if(current)clear();return;}
  if(!current||current.id!==selected.id||current.child!==selected.child||current.model!==selected.model){clear();const record={...selected,token:generation,callback:null,last:null};current=record;
   record.refresh=()=>{if(disposed||current!==record||generation!==record.token)return;const child=root.subViews&&root.subViews.get(record.id);if(child!==record.child||child.model!==record.model){reconcile();return;}
    if(record.last!==record.model.payload){const raw=record.model.payload;record.last=raw;let payload;try{payload=JSON.parse(raw||'{}');}catch{payload={enabled:false};}if(current===record&&record.token===generation)onPayload(payload);}};
   record.callback=viewEnv.addDataChangedCallback('model',record.id,true);
  }
  current.refresh();
 }catch(error){try{clear();}finally{onError(error);}}}
 function dispose(){if(disposed)return;disposed=true;let first;for(const name of listeners)try{engine.off(name,reconcile);}catch(error){first=first||error;}try{clear();}catch(error){first=first||error;}if(first)throw first;}
 function start(){if(started||disposed)return;started=true;try{for(const name of ['viewEnv.onDataChanged','subViews.onAdded','subViews.onRemoved']){listeners.push(name);engine.on(name,reconcile);}reconcile();}catch(error){dispose();throw error;}}
 return {start,dispose,refresh:reconcile,getCurrent:()=>current};
}
