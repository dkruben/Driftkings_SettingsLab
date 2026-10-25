const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const context = {window:{},JSON,Math,Object,Array,String,Number};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../../mod/res/gui/gameface/mods/driftkings/settings_window/js/vehicle_markers_model.js'),'utf8'),context);
const model = context.window.DK.vehicleMarkerModel;
const sample = {group:'enemy',alt:false,blind:false,hp:50,name:'<b>unsafe</b>'};
const raw = {customFields:{enabled:true,enemy:{normal:[{format:'{{hp}}',x:12}],extended:[{format:'{{name}}'}]}}};
let state = model.state(raw,sample);
assert.strictEqual(state.fields[0].x,12);
assert.strictEqual(model.text('{{hp}}/{{maxHp}} {{hpPercent}}%',state.config,sample),'775/1550 50%');
assert.strictEqual(model.text('{{name}}',state.config,sample),'&lt;b&gt;unsafe&lt;/b&gt;');
assert.strictEqual(model.teamColor(state.config,sample),'#FF7777');
assert.strictEqual(model.teamColor(state.config,Object.assign({},sample,{blind:true})),'#C48CFF');
assert.strictEqual(model.hpColor(state.config,sample),'#FFDD66');
assert.strictEqual(model.text('{{hp}}',state.config,Object.assign({},sample,{group:'dead'})),'0');
assert.strictEqual(model.text('{{c:dmg}} -{{dmg}}',state.config,sample,310),'#FFDD66 -310');
assert.strictEqual(model.state(raw,Object.assign({},sample,{alt:true})).fields[0].format,'{{name}}');
assert.strictEqual(model.state(raw,Object.assign({},sample,{group:'ally'})).fields,null,'unconfigured mode preserves native text');
state.fields[0].x=90;
assert.strictEqual(raw.customFields.enemy.normal[0].x,12);
const palettes = [
    {name:'A',colors:model.clone(model.defaults.colors),damageColors:{player:'#111111'}},
    {name:'B',colors:model.clone(model.defaults.colors),damageColors:{player:'#222222'}}
];
palettes[1].colors.team.enemy='#123456';
palettes[1].colors.hp=[{value:10.4,color:'#010101'},{value:101,color:'#020202'}];
const linked = model.state({colorRating:1},sample,palettes).config;
assert.strictEqual(model.teamColor(linked,sample),'#123456');
assert.strictEqual(model.hpColor(linked,{hp:10.4}),'#020202');
assert.strictEqual(model.hpColor(linked,{hp:100}),'#020202');
assert.strictEqual(model.text('{{c:dmg}}',linked,sample,100),'#222222');
assert.strictEqual(model.state({colorRating:1,colors:{team:{enemy:'#ABCDEF'}}},sample,palettes).config.colors.team.enemy,'#ABCDEF');
console.log('Vehicle marker sample: macros, team/HP/colorblind colors and normal/ALT passed');
