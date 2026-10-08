'use strict';
const assert=require('assert');
const api=require('../../res/gui/gameface/mods/Driftkings/CarouselStats/carousel_native.js');
const c=require('../../res/configs/Driftkings/default/carousel_stats/carousel.json');
c.visible=true;c.cellType='default';c.effectiveRows=2;c.normal={width:160,height:100,gap:10};c.small={width:160,height:35,gap:10};
let stats={1:{winRate:40},2:{winRate:60}};
function apply(){api.setData({config:c,sortValues:stats});}
apply();assert.equal(api.footprint(2),170);assert.equal(api.gap(2),10);
assert(api.styles(c).includes('height:80px'));
for (const rows of [1,2,3,4]) {
 c.effectiveRows=rows;apply();assert.equal(api.rowCount(1),rows);
 const height=rows===1?100:35*rows+10*(rows-1);
 assert(api.styles(c).includes('height:'+height+'px'));
 for (const count of [0,1,rows,rows+1,17]) {
  const slots=Array.from({length:count},(_,index)=>index+1);
  const groups=api.groupColumns(slots,rows,'empty');
  assert.equal(groups.length,Math.ceil(count/rows));
  assert(groups.every(group=>group.length===rows));
  assert.deepEqual(groups.flat().filter(id=>id!=='empty'),slots);
  assert.equal(slots.length,count);
 }
}
c.cellType='normal';c.effectiveRows=4;apply();assert(api.styles(c).includes('height:430px'));
c.cellType='default';c.effectiveRows=2;apply();
c.hideBuyTank=true;apply();assert(!api.actionAllowed('buyTank'));assert(api.actionAllowed('rentTank'));
c.filters.premium.enabled=false;apply();assert(!api.filterAllowed('premium'));
assert.deepEqual(api.ordered(['a','b','c'],['c']),['c','a','b']);
c.sorting_criteria=['-winRate'];apply();
const a={id:1,favorite:false},b={id:2,favorite:false};
assert(api.compare(a,b)<0===false);assert(api.compare(b,a)<0);
assert(api.compare({id:3,favorite:false},a)>0);
assert(api.compare({id:3,favorite:true},a)<0);
c.sorting_criteria=['nation'];c.nations_order=['usa','ussr'];apply();
assert(api.compare({id:1,nationId:2},{id:2,nationId:0})<0);
c.totalSlots=100;c.freeSlots=20;c.usedSlots=80;c.showTotalSlots=true;apply();
assert.equal(api.counts('buyTank'),'100 / 20');assert.equal(api.counts('buySlot'),'80 / 100');
let position=null,prevented=false;
const scroll={animationScroll:{scrollPosition:{get:()=>10}},applyScroll:v=>position=v,getWrapperSize:()=>200};
const event={deltaY:3,deltaMode:1,preventDefault:()=>prevented=true,stopPropagation:()=>{}};
api.wheel(scroll,event);assert.equal(position,null);
c.scrollingSpeed=2;apply();api.wheel(scroll,event);assert.equal(position,106);assert(prevented);
api.dispose();assert.equal(api.config(),null);assert.equal(api.compare(a,b),null);assert(api.actionAllowed('buyTank'));assert.equal(api.styles(null),'');
assert.equal(api.rowCount(2),2);
console.log('Carousel native sorting, geometry, filters, slots, wheel and disable: OK');
