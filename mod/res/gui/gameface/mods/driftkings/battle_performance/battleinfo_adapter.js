import {CoreSession,ResourceScope} from '../shared/native_extension_core.js';
// This adapter is embedded in the pinned document; no registry or Mission Progress API.
export function createBattleInfoZone(React,consumers,report,createFlashText){
 const output=report||function(entry){console[entry.success?'info':'error']('[Driftkings.NativeResults] '+JSON.stringify(entry));};
 class Boundary extends React.Component {constructor(props){super(props);this.state={failed:false};}static getDerivedStateFromError(){return {failed:true};}componentDidCatch(error){void this.props.session.fail(error,'render');}render(){return this.state.failed?null:this.props.children;}}
 function Instance({spec,identity,payload}){
  const [loaded,setLoaded]=React.useState(null);
  React.useEffect(()=>{const scope=new ResourceScope();let active=true,session;
   session=new CoreSession({id:spec.id,scope,load:spec.load,report:output,create:(mod)=>{
    if(typeof mod.create!=='function')throw new Error('Invalid results entrypoint');
    const owner=mod.create({React,scope,createFlashText,identity,generation:session.generation,report:entry=>session.report(entry.phase,entry.event,entry.success,entry.errorClassification)});
    if(typeof owner.Component!=='function')throw new Error('Invalid results component');return owner;
   }});
   session.start().then(owner=>{if(active&&session.valid&&!session.dead&&owner){session.markMounted();setLoaded({owner,session});}});
   return()=>{active=false;void session.destroy();};
  },[identity,spec]);
  return loaded?React.createElement(Boundary,{session:loaded.session},React.createElement(loaded.owner.Component,{payload})):null;
 }
 const slots=consumers.map((spec,index)=>({spec,index}));
 return function Zone({identity='results-document',payloads={},enabledIds}){return React.createElement(React.Fragment,null,...slots.filter(slot=>!enabledIds||enabledIds.includes(slot.spec.id)).map(slot=>React.createElement(Instance,{key:slot.spec.id+':'+identity,spec:slot.spec,identity,payload:payloads[slot.spec.id]})));};
}
