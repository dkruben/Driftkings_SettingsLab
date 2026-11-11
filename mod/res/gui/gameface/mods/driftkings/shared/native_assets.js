// Document-local stylesheet leases; pre-existing foreign links are borrowed, never removed.
const documents=new WeakMap();
function acquireStyle(scope,doc,url){
 if(scope.closed)throw new Error('Closed asset scope');
 let records=documents.get(doc);if(!records){records=new Map();documents.set(doc,records);}
 let record=records.get(url);
 if(!record){
  if(Array.from(doc.getElementsByTagName('link')).some(node=>node.href===url))return Promise.resolve();
  const node=doc.createElement('link');record={node,refs:0,pending:true,append:true};records.set(url,record);node.rel='stylesheet';node.href=url;
  record.promise=new Promise((resolve,reject)=>{record.reject=reject;node.onload=()=>{record.pending=false;node.onload=node.onerror=null;resolve();};node.onerror=()=>{record.pending=false;node.onload=node.onerror=null;if(node.parentNode)node.parentNode.removeChild(node);if(records.get(url)===record)records.delete(url);reject(new Error('Stylesheet unavailable'));};});
 }
 record.refs++;let released=false;
 scope.defer(()=>{if(released)return;released=true;if(--record.refs===0){if(record.node.parentNode)record.node.parentNode.removeChild(record.node);if(record.pending){record.pending=false;record.node.onload=record.node.onerror=null;record.reject(new Error('Retired stylesheet'));}if(records.get(url)===record)records.delete(url);}});
 if(record.append){record.append=false;try{doc.head.appendChild(record.node);}catch(error){record.node.onerror();throw error;}}
 return record.promise;
}
export async function loadResultsAssets(scope,doc){
 await Promise.all(['shared/fonts.css','battle_performance/results.css'].map(path=>acquireStyle(scope,doc,'coui://gui/gameface/mods/driftkings/'+path)));
 if(scope.closed)throw new Error('Retired assets');
}
