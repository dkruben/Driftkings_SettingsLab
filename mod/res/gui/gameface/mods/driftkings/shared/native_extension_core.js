// Context-independent experimental lifecycle. No React, DOM, Wulf or game URLs.
let nextGeneration=0;
export class ResourceScope {
 constructor(report=()=>{}){this.report=report;this.entries=[];this.closed=false;this.promise=null;this.failures=0;}
 defer(dispose){if(typeof dispose!=='function')throw Error('invalid disposer');if(this.closed)throw Error('closed scope');this.entries.push(dispose);return dispose;}
 dispose(){if(this.promise)return this.promise;this.closed=true;const entries=this.entries.splice(0).reverse();
  this.promise=Promise.resolve().then(async()=>{for(const dispose of entries)try{await dispose();}catch(error){this.failures++;this.report('CLEANUP_FAILED',error);}return {failures:this.failures};});return this.promise;}
}
export class CoreSession {
 constructor({id,load,create,scope=new ResourceScope(),report=()=>{}}){this.id=id;this.identity=id;this.generation=++nextGeneration;this.load=load;this.create=create;this.scope=scope;this.sink=report;this.state='UNINITIALIZED';this.trace=['UNINITIALIZED'];this.dead=false;this.valid=true;this.owner=null;this.pending=null;this.destroyPromise=null;this.retirements=new WeakMap();this.cleanupFailures=0;this.cleanupStatus='not-started';this.scope.report=(event,error)=>this.report('cleanup',event,false,'DISPOSER_REJECTED');}
 set(state){this.state=state;this.trace.push(state);}
 report(phase,event,success=true,errorClassification=null){const entry={extensionId:this.id,generationId:this.generation,phase,event,success,errorClassification};try{this.sink(entry);}catch{}return entry;}
 start(){if(this.pending)return this.pending;if(this.dead)return Promise.resolve(null);this.set('LOADING');this.report('import','IMPORT_STARTED');
  this.pending=Promise.resolve().then(async()=>{let phase='import';try{const mod=await this.load();if(this.dead||!this.valid){this.trace.push('STALE');this.report('import','LATE_IMPORT_IGNORED',false,'STALE_GENERATION');return null;}
   phase='factory';const owner=this.create(mod,this.scope);if(!owner||!['object','function'].includes(typeof owner)||typeof owner.init!=='function'||typeof owner.destroy!=='function')throw Error('invalid owner');this.owner=owner;
   phase='init';await this.owner.init();if(this.dead||!this.valid){this.trace.push('STALE');this.report('init','GENERATION_STALE',false,'STALE_GENERATION');await this.retireOwner();return null;}
   this.set('READY');this.report('init','INIT_COMPLETED');return this.owner;
  }catch(error){if(!this.dead){await this.fail(error,phase);}else this.report(phase,'CANCELLED_OPERATION',false,'STALE_GENERATION');return null;}});return this.pending;
 }
 retireOwner(){const owner=this.owner;if(!owner)return this.scope.dispose();if(this.retirements.has(owner))return this.retirements.get(owner);
  const retirement=Promise.resolve().then(async()=>{this.cleanupStatus='pending';this.report('cleanup','OWNER_RETIRING');
   const ownerCleanup=Promise.resolve().then(()=>owner.destroy()).catch(error=>{this.cleanupFailures++;this.report('cleanup','OWNER_CLEANUP_FAILED',false,'OWNER_DESTROY_REJECTED');});
   await Promise.all([ownerCleanup,this.scope.dispose()]);this.cleanupStatus=this.cleanupFailures+this.scope.failures?'failed':'complete';return {status:this.cleanupStatus,failures:this.cleanupFailures+this.scope.failures};
  });this.retirements.set(owner,retirement);return retirement;
 }
 fail(error,phase='render'){if(this.dead){this.report(phase,'STALE_CALLBACK_IGNORED',false,'STALE_GENERATION');return this.retireOwner();}this.valid=false;this.set('FAILED');this.report(phase,phase.toUpperCase()+'_FAILED',false,phase.toUpperCase()+'_ERROR');return this.retireOwner();}
 guard(callback){return(...args)=>{if(this.dead||!this.valid){this.report('callback','STALE_CALLBACK_IGNORED',false,'STALE_GENERATION');return;}return callback(...args);};}
 markMounted(){if(!this.dead&&this.valid&&this.state==='READY'){this.set('MOUNTED');this.report('mount','MOUNT_COMPLETED');}}
 destroy(){if(this.destroyPromise)return this.destroyPromise;this.dead=true;this.valid=false;if(this.state==='LOADING'){this.trace.push('CANCELLED');this.report('import','GENERATION_CANCELLED',false,'CANCELLED');}this.set('RETIRING');this.report('cleanup','DESTROY_PENDING');
  this.destroyPromise=Promise.resolve().then(()=>this.retireOwner()).then(()=>{const failures=this.cleanupFailures+this.scope.failures;this.cleanupStatus=failures?'failed':'complete';this.set(failures?'CLEANUP_FAILED':'DESTROYED');this.report('cleanup',failures?'DESTROY_ATTEMPTS_COMPLETED_WITH_ERRORS':'DESTROY_COMPLETED',!failures,failures?'CLEANUP_ERROR':null);return {status:this.cleanupStatus,failures};});return this.destroyPromise;}
}
