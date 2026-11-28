const assert=require('assert');
const {createEnvironment}=require('../../support/frontend/dom_fixture');
const env=createEnvironment(), {DK}=env;
const vehicle={name:'My garage tank',nation:'usa',tank:'a12_t32',image:'img://gui/maps/icons/vehicle/custom.png',
    tier:8,level:'8',type:'heavyTank',selected:true,favorite:true,premium:false,xp:'x3',
    stats:{battles:42,winRate:55.5,avgDamage:1234,avgFrags:0,marksOnGun:2},colors:{winRate:'#123456'}};
assert.strictEqual(DK.carouselPreview,undefined,'the standalone carousel preview is removed');
assert.strictEqual(DK.carouselMacros.macros('{{v.winrate%.1f}} {{v.c:winrate}}',vehicle),'55.5 #123456');
assert.strictEqual(DK.carouselMacros.macros('{{v.c:tdb}} / {{v.c:wn8expd}}',
    Object.assign({},vehicle,{colors:{avgDamage:'#123456',wn8expd:'#654321'}})),'#123456 / #654321');
assert.strictEqual(DK.carouselMacros.macros('{{v.tfb?yes|no}}',vehicle),'no','zero frags is false like the live Python renderer');
assert.strictEqual(DK.carouselMacros.macros('{{icon:marksOnGun}}',vehicle),'gui/maps/icons/marksOnGun/95x85/usa_2_marks.png');
assert.strictEqual(DK.carouselMacros.macros('{{icon:marksOnGun}}',Object.assign({},vehicle,{stats:{marksOnGun:0}})),
    'gui/maps/driftkings/carroucel/mark_0.png');
DK.app.dispose();
console.log('Carousel inline macros: fictional data, rating colours and fallback passed');
