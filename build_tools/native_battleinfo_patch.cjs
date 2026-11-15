// Build-time only: pinned AST insertion, in memory. Never shipped to the client.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),acorn=require('./javascript/node_modules/acorn');
const ROOT=path.resolve(__dirname,'..'),MARK='/* DRIFTKINGS_NATIVE_BATTLEINFO */';
const sha=value=>crypto.createHash('sha256').update(value).digest('hex');
function locate(source){const ast=acorn.parse(source,{ecmaVersion:'latest',sourceType:'module'}),hits=[];
 function walk(node){if(!node||typeof node!=='object')return;if(node.type==='CallExpression'&&node.arguments?.[1]?.type==='ObjectExpression'){
 const array=node.arguments[1].properties.find(p=>p.key?.name==='children')?.value;
 if(array?.type==='ArrayExpression'&&array.elements.length===5&&JSON.stringify(array.elements.map(n=>n?.arguments?.[0]?.property?.name))===JSON.stringify(['Arena','StartTime','Player','PlayerStatus','CommendationScore'])){
 const owner=node.arguments[0]?.name;if(owner&&array.elements.every(n=>n.arguments[0].object?.name===owner))hits.push({node,array});}}
 for(const value of Object.values(node))if(Array.isArray(value))value.forEach(walk);else if(value&&typeof value==='object')walk(value);
 }walk(ast);if(hits.length!==1)throw Error('BattleInfo anchor count: '+hits.length);return hits[0];}
function transform(raw,manifest,{verifyOutput=true}={}){
 if(manifest.schema_version!==1||manifest.realm!=='CT'||manifest.client_build!=='995'||manifest.runtime_normalization!=='lf'||manifest.resource!=='gui/gameface/_dist/production/mono/post_battle/random/bundle.js')throw Error('Unsupported BattleInfo manifest');
 const source=Buffer.isBuffer(raw)?raw.toString('utf8'):raw;
 if(source.includes(MARK)||source.includes('__dkBattleInfoZone'))throw Error('BattleInfo already applied or collision');
 if(sha(Buffer.from(source))!==manifest.source_sha256)throw Error('Unsupported BattleInfo source hash');
 if(manifest.parser_version!==acorn.version)throw Error('Unsupported AST parser version');
 const anchor=locate(source),react=source.match(/var ([\w$]+)=e\(\$\(\)\),[^;]*"BattleInfo_/),point='var $f=';
 if(!react||source.split(point).length!==2)throw Error('Unsupported BattleInfo context');
 const runtime=manifest.runtime_inputs.map(input=>{const file=path.resolve(ROOT,input.path);if(!file.startsWith(ROOT+path.sep))throw Error('Invalid runtime path');const text=fs.readFileSync(file,'utf8').replace(/\r\n/g,'\n');if(sha(Buffer.from(text))!==input.sha256)throw Error('Runtime input hash mismatch: '+input.path);if(input.mode==='isolated_flash_text')return 'function __dkCreateFlashText(document){const window={};'+text+';return window.DriftkingsFlashText;}';return text.replace(/^import .*?;\r?\n/gm,'').replace(/^export /gm,'');}).join('\n');
 const inserted=MARK+'var __dkBattleInfoZone=(()=>{'+runtime+';return createBattleInfoZone('+react[1]+',[{id:"driftkings.results.efficiency",load:()=>import("'+manifest.entrypoint+'") }],undefined,__dkCreateFlashText);})();';
 const callee=source.slice(anchor.node.callee.start,anchor.node.callee.end),child=',('+callee+')(__dkBattleInfoZone,{})';
 let output=source.slice(0,anchor.array.end-1)+child+source.slice(anchor.array.end-1);output=output.replace(point,inserted+point);acorn.parse(output,{ecmaVersion:'latest',sourceType:'module'});
 if(output.replace(inserted,'').replace(child,'')!==source)throw Error('Non-reversible AST insertion');
 const outputHash=sha(Buffer.from(output));if(verifyOutput&&outputHash!==manifest.output_sha256)throw Error('BattleInfo output hash mismatch');
 return {output,sha256:outputHash,inserted,child,expression:source.slice(anchor.node.start,anchor.array.end-1)+child+source.slice(anchor.array.end-1,anchor.node.end)};
}
module.exports={transform,locate,sha};
if(require.main===module){try{const job=JSON.parse(fs.readFileSync(0,'utf8'));const result=transform(Buffer.from(job.input,'base64'),job.manifest);process.stdout.write(JSON.stringify({output:Buffer.from(result.output).toString('base64'),sha256:result.sha256}));}catch(error){process.stderr.write(String(error));process.exitCode=1;}}
