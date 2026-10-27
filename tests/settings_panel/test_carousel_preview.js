const assert=require('assert');
const {createEnvironment}=require('./dom_fixture');
const data=require('./schema_fixture');
const env=createEnvironment(), {DK,document}=env;
const mod=data.schema.mods.find(item=>item.id==='legacy.CarouselStats');
const host=document.createElement('div'), preview=DK.carouselPreview.create(host,mod);
const vehicle={name:'My garage tank',nation:'usa',tank:'a12_t32',image:'img://gui/maps/icons/vehicle/custom.png',
    tier:8,level:'8',type:'heavyTank',selected:true,favorite:true,premium:false,xp:'x3',
    stats:{battles:42,winRate:55.5,avgDamage:1234,avgFrags:0,marksOnGun:2},colors:{winRate:'#123456'}};
preview.update(data.state.values[mod.id],{}, {source:'examples',vehicles:[vehicle]});
assert.strictEqual(host.querySelectorAll('.dk-car-card').length,1,'real cards are not duplicated');
assert.strictEqual(host.querySelector('.dk-car-name').textContent,vehicle.name);
assert.strictEqual(host.querySelector('.dk-car-tank-img').src,'coui://gui/maps/icons/vehicle/custom.png');
assert.strictEqual(host.querySelector('.dk-car-favorite-img').style.left,'100%');
assert.strictEqual(host.querySelector('.dk-car-tank-img').style.left,'50%');
assert.strictEqual(host.querySelector('.dk-live-note').textContent,DK.t('car.note'));
assert.strictEqual(DK.carouselPreview.macros('{{v.winrate%.1f}} {{v.c_winrate}}',vehicle),'55.5 #123456');
assert.strictEqual(DK.carouselPreview.macros('{{v.tfb?yes|no}}',vehicle),'no','zero frags is false like the live Python renderer');
assert.strictEqual(DK.carouselPreview.macros('{{icon:marksOnGun}}',vehicle),'gui/maps/icons/marksOnGun/95x85/usa_2_marks.png');
preview.update(data.state.values[mod.id],{},null);
assert(host.querySelectorAll('.dk-car-card').length>1,'standalone tools retain labeled examples');
preview.dispose();DK.app.dispose();
// Base field properties follow core.carousel.build_profile / carousel_layout.mount.
const next=createEnvironment(), id=next.DK.minimapPreview.fieldId;
const fieldPath='carousel.normal.extraFields.0.';
const fieldHost=next.document.createElement('div');
const fields=next.DK.carouselPreview.create(fieldHost,{id:'legacy.CarouselStats',controls:[{id:id(fieldPath+'x')}]});
fields.update({[id('carousel.cellType')]:1,[id(fieldPath+'color')]:'#123456',
    [id(fieldPath+'fontSize')]:21,[id(fieldPath+'iconSize')]:25,[id(fieldPath+'src')]:'gui/maps/test.png',
    [id(fieldPath+'width')]:80,[id(fieldPath+'height')]:30,[id(fieldPath+'align')]:2,
    [id(fieldPath+'shadow.enabled')]:false});
const field=fieldHost.querySelector('.dk-car-field');
assert.strictEqual(field.style.fontSize,'21rem');assert.strictEqual(field.style.color,'#123456');
assert.strictEqual(field.style.justifyContent,'flex-end');
assert.strictEqual(field.querySelector('img').style.width,'25rem','icon size is independent of field width');
assert(!field.style.textShadow,'disabled field shadows stay disabled');
fields.dispose();next.DK.app.dispose();
console.log('Carousel fictional data, native anchors, rating colours and fallback passed');
