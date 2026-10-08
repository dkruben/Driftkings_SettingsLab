'use strict';
const assert=require('assert');
const layout=require('../../res/gui/gameface/mods/Driftkings/CarouselStats/carousel_layout.js');
class Node {
 constructor(tag) {this.tag=tag;this.style={};this.children=[];this.parentNode=null;this.clientWidth=320;this.clientHeight=200;this.matches={};}
 appendChild(node) {this.children.push(node);node.parentNode=this;}
 insertBefore(node,before) {let index=this.children.indexOf(before);if(index<0)index=this.children.length;this.children.splice(index,0,node);node.parentNode=this;}
 get firstChild() {return this.children[0] || null;}
 removeChild(node) {this.children.splice(this.children.indexOf(node),1);node.parentNode=null;}
 querySelectorAll(selector) {return this.matches[selector] || [];}
}
const document={createElement:tag=>new Node(tag),createTextNode:text=>({text:text})};
global.getComputedStyle=node=>({position:node.style.position||'static',transform:node.style.transform||'none'});
assert.equal(layout.profileName('default',true),'small');assert.equal(layout.profileName('normal',true),'normal');
assert.equal(layout.color('0xAABBCC'),'#AABBCC');
assert.equal(layout.localIcon('https://example.com/x.png'),'');
assert.equal(layout.localIcon('img://gui/maps/icon.png'),'coui://gui/maps/icon.png');
assert.equal(layout.localIcon('gui/../icon.png'),'');
let rich=new Node('span');layout.richText(rich,'<font color="#ABCDEF" size="12">WN8</font><img src="https://example.com/x" onerror="bad()">',document);
assert.equal(rich.children[0].style.color,'#ABCDEF');assert.equal(rich.children.length,1);
rich=new Node('span');
layout.richText(rich,'<font face="$FieldFont" size="12" color="#ABCDEF">Stats</font>',document);
assert.equal(rich.children[0].style.fontFamily,undefined);
assert.equal(rich.children[0].style.fontSize,'12px');
assert.equal(rich.children[0].style.color,'#ABCDEF');
assert.equal(rich.children[0].children[0].text,'Stats');
const external='mods/Driftkings/Carroucel/#957D5B.png', images={[external]:'data:image/png;base64,aGVsbG8='};
assert.equal(layout.localIcon(external,images),images[external]);
assert.equal(layout.localIcon(external,{}),'');
assert.equal(layout.localIcon(external,{[external]:'https://example.com/a.png'}),'');
rich=new Node('span');
layout.richText(rich,"<img src='"+external+"' width='154' height='94'><font alpha='85' face='mono'>&#x25CE;</font>",document,images,true);
assert.equal(rich.children[0].tag,'img');assert.equal(rich.children[0].src,images[external]);
assert.equal(rich.children[0].style.width,'154px');assert.equal(rich.children[0].style.height,'94px');
assert.equal(rich.children[1].style.opacity,0.85);assert.equal(rich.children[1].children[0].text,'\u25CE');
rich=new Node('span');layout.richText(rich,"<img src='img://gui/a.png'>text",document,images,false);
assert.equal(rich.children.length,1);assert.equal(rich.children[0].text,'text');
let card=new Node('card'),flag=new Node('flag');flag.style.opacity='0.7';
card.matches['[class*="Background_flag_"]']=[flag];
let profile={width:160,height:100,fields:{flag:{enabled:false,alpha:40,dx:0,dy:0,scale:1}},extraFields:[{layer:'top',x:3,y:4,fontSize:12,color:'#AABBCC',alpha:100,align:'right',shadow:{enabled:false},format:'Text'}]};
let dispose=layout.mount(card,profile,document);
assert.equal(flag.style.visibility,'hidden');assert.equal(flag.style.opacity,'0.4');
assert.equal(card.children.length,2);assert.equal(card.children[1].style.transform,'scale(2,2)');
assert.equal(card.children[1].children[0].style.transform,'translateX(-100%)');
flag.style.opacity='0.9';dispose();
assert.equal(flag.style.opacity,'0.9');assert.equal(flag.style.visibility,undefined);
assert.equal(card.children.length,0);assert.equal(card.style.position,undefined);
console.log('Carousel rendering, profiles, safe formatting and cleanup: OK');
