import {Texture,Rectangle} from 'pixi.js';import {TYPES} from './catalog.js';
export const FIELD={ground:0xcdd3c3,grass:0xbacbaa,road:0xcacfd5,forest:0x76966d,water:0xa9d9e7,building:0xb4b1c4,a:0x2f6fed,b:0xe27632,neutral:0xc39a35,ink:0x334155};
export const TILE_COLORS=[FIELD.ground,FIELD.road,FIELD.forest,FIELD.ink,FIELD.building,FIELD.water,0x88bbc9,0xb3a286,FIELD.grass,0x98a49b];
const colors={ink:'#334155',shadow:'#b5bdba',paper:'#f1f2ec',glass:'#9bc8d4',steel:'#8798a0',light:'#c5d2d7'};
function rectangle(ctx,color,x,y,w,h){ctx.fillStyle=color;ctx.fillRect(Math.round(x),Math.round(y),Math.round(w),Math.round(h));}
function dotLine(ctx,color,x,y,dx,dy,length){for(let i=0;i<length;i++)rectangle(ctx,color,x+dx*i,y+dy*i,2,2);}
function soldier(ctx,type,team,frame,w){const x=(w-12)/2,c=team===0?'#2f6fed':'#e27632',r=(color,a,b,ww,hh)=>rectangle(ctx,color,x+a,b,ww,hh);const step=frame===1?1:frame===2?-1:0;
 // Top-down helmet, shoulder silhouette and long forward rifle: nose points up.
 r('#334155',2,6,8,10);r(c,3,7,6,7);r('#334155',2,14,3,4+step);r('#334155',7,14,3,4-step);
 r('#334155',1,3,10,6);r(c,2,3,8,5);r('#b7c9ae',3,6,6,2);r('#334155',8,0,2,12);r('#e2ce9c',7,9,3,2);
 if(type==='MED'){r('#eee9d9',3,9,5,4);r('#657b52',5,9,1,4);r('#657b52',3,10,5,1);}
 if(type==='AT'){r('#334155',0,0,3,15);r('#a7b29b',0,3,3,8);r('#d1bc76',0,1,3,2);}
 if(type==='SUP')r('#334155',10,0,2,14);if(type==='REC')r('#eee9d9',3,4,6,1);
}
function vehicle(ctx,type,team,frame,w,h){const c=team===0?'#2f6fed':'#e27632',trim=team===0?'#7e9ece':'#c58e6b',r=(color,x,y,ww,hh)=>rectangle(ctx,color,x,y,ww,hh);
 if(type==='MBT'||type==='SPH'){r(colors.shadow,6,5,w-9,h-7);for(const y of [3,h-13]){r(colors.ink,5,y,w-10,10);for(let x=8;x<w-8;x+=6)r('#7f8c8d',x,y+2,3,6);}r(colors.ink,11,12,w-25,h-24);r(trim,13,13,w-29,h-26);r(c,18,16,w-40,h-32);r('#aabcb2',17,15,21,3);r(colors.ink,25,19,15,h-38);r(colors.steel,27,21,11,h-42);r(colors.glass,w-23,18,6,h-36);if(type==='SPH'&&frame===2){for(const y of [0,h-5])for(const x of [8,w-22])r(colors.ink,x,y,17,5);}r(colors.paper,39,h/2-4,9,8);r(c,41,h/2-2,5,4);return;}
 if(type==='HEL'){r(colors.shadow,10,44,80,18);r(colors.ink,12,39,70,18);r(colors.ink,8,43,80,10);r(trim,14,40,65,14);r(c,20,42,53,10);r(colors.paper,24,45,38,3);r(colors.glass,77,43,7,9);r(colors.ink,35,40,2,15);r(colors.ink,59,40,2,15);for(const cx of [23,73]){for(let y=-23;y<=23;y++)for(let x=-23;x<=23;x++)if(Math.abs(Math.hypot(x,y)-22)<.65)r('#b7c4c4',cx+x,48+y,1,1);if(frame===2){dotLine(ctx,colors.ink,cx-17,31,1,1,35);dotLine(ctx,colors.ink,cx-17,65,1,-1,35);}else{r(colors.ink,cx-22,47,45,2);r(colors.ink,cx-1,26,2,45);}r(colors.light,cx-2,46,5,5);r(colors.ink,cx,48,1,1);}return;}
 r(colors.shadow,4,h-6,w-8,5);for(const xx of [10,w-22]){r(colors.ink,xx,2,12,7);r(colors.ink,xx,h-9,12,7);r('#64737a',xx+2,3,8,2);r('#64737a',xx+2,h-7,8,2);}r(colors.ink,7,7,w-19,h-14);r(colors.ink,4,12,w-10,h-24);r(trim,8,8,w-21,h-16);r(c,12,10,w-29,h-20);r('#c2cdd0',8,h-10,w-20,2);r(colors.ink,w-13,11,6,h-22);r(colors.glass,w-14,13,5,h-26);r(colors.paper,w-7,12,2,4);r('#d3b86e',w-7,h-16,2,4);
 if(type==='TRK'){r(colors.ink,8,10,w*.58,h-20);r('#baad88',10,12,w*.55,h-24);for(let x=13;x<w*.6;x+=14){r('#8f8167',x,13,11,h-26);r('#d3c7a6',x+1,14,9,3);r('#b5a47d',x+5,15,2,h-30);}r(c,w*.7,12,w*.13,h-24);}else if(type==='LUV'){r(colors.ink,12,9,24,h-18);r(colors.glass,15,11,7,h-22);r(colors.glass,26,11,7,h-22);r(trim,34,10,12,h-20);}else{for(const xx of (type==='IFV'?[17,37,57]:[18,42])){r(colors.ink,xx,13,14,h-26);r(colors.steel,xx+2,15,10,h-30);}r(c,w-29,12,10,h-24);}
 r(colors.paper,w-27,h/2-4,8,8);r(c,w-25,h/2-2,4,4);if(team===1){r(colors.ink,12,11,2,h-22);r(colors.ink,17,11,2,h-22);}else r(colors.light,12,11,2,h-22);
}
export class PixelAtlas{
 constructor(){this.canvas=document.createElement('canvas');this.canvas.width=1024;this.canvas.height=1024;const ctx=this.canvas.getContext('2d');ctx.imageSmoothingEnabled=false;this.frames=new Map();let y=2;for(const [type,profile] of Object.entries(TYPES)){const [w,h]=profile.size;for(let team=0;team<2;team++)for(let frame=0;frame<3;frame++){const x=2+(team*3+frame)*(w+2);ctx.save();ctx.translate(x,y);if(profile.kind==='infantry')soldier(ctx,type,team,frame,w);else vehicle(ctx,type,team,frame,w,h);ctx.restore();this.frames.set(`${type}:${team}:${frame}`,new Rectangle(x,y,w,h));}y+=h+4;}this.base=Texture.from(this.canvas);this.base.source.scaleMode='nearest';this.textures=new Map();for(const [key,frame] of this.frames)this.textures.set(key,new Texture({source:this.base.source,frame}));}
 get(type,team,frame=0){return this.textures.get(`${type}:${team}:${frame}`)??this.textures.get(`INF:${team}:0`);}
 destroy(){for(const texture of this.textures.values())texture.destroy(false);this.base.destroy(true);}
}
export function tileAtlas(){const canvas=document.createElement('canvas');canvas.width=48*10;canvas.height=48*4;const ctx=canvas.getContext('2d');for(let type=0;type<10;type++)for(let variant=0;variant<4;variant++){ctx.save();ctx.translate(type*48,variant*48);const r=(color,x,y,w,h)=>rectangle(ctx,color,x,y,w,h),hex='#'+TILE_COLORS[type].toString(16).padStart(6,'0');r(type===2?'#dfe8d7':hex,0,0,48,48);
 if(type===0||type===8){for(let i=0;i<7;i++){const x=(i*17+variant*11)%47,y=(i*13+variant*7)%47;r('#bdc6b2',x,y,2,1);}if(variant===2)r('#c7cebc',8,14,19,9);}
 if(type===1){r('#b9c1c8',0,0,48,3);r('#dbe0e3',0,45,48,3);r('#e9e9db',variant%2?25:3,23,15,2);}
 if(type===2){for(const [x,y] of [[8+variant%2*5,7],[25,23]]){r('#9aa58c',x+5,y+20,10,4);r('#8b7f70',x+8,y+15,3,8);r('#597955',x+2,y+6,17,12);r('#76966d',x,y+5,21,9);r('#8ca77f',x+4,y,13,15);r('#9bb38c',x+6,y+2,7,3);}}
 if(type===3||type===4){r('#a6a6b2',2,2,44,44);for(let yy=3;yy<46;yy+=10){r('#d3d2d8',2,yy,44,1);for(let xx=(yy%20?3:12);xx<46;xx+=16)r('#c5c4cd',xx,yy+1,1,9);}}
 if(type===5||type===6){for(let i=0;i<4;i++){r(type===5?'#c5e5ea':'#a9d9e7',(i*13+variant*7)%35,i*11+4,10,1);}}
 if(type===7){r('#7d827e',0,0,48,4);r('#7d827e',0,44,48,4);for(let xx=3;xx<48;xx+=8)r('#d0c4a6',xx,6,6,36);}
 if(type===9){r('#acb7af',11,19,28,19);r('#85948e',7,17,29,15);r('#b8c2b7',12,12,17,12);r('#cbd2c8',14,12,12,3);}ctx.restore();}
 const base=Texture.from(canvas);base.source.scaleMode='nearest';const textures=new Map();for(let type=0;type<10;type++)for(let variant=0;variant<4;variant++)textures.set(`${type}:${variant}`,new Texture({source:base.source,frame:new Rectangle(type*48,variant*48,48,48)}));return {get:(type,variant)=>textures.get(`${type}:${variant}`),destroy:()=>{for(const t of textures.values())t.destroy(false);base.destroy(true);}};
}
export function facilityTexture(kind){const canvas=document.createElement('canvas');canvas.width=192;canvas.height=160;const ctx=canvas.getContext('2d'),r=(color,x,y,w,h)=>rectangle(ctx,color,x,y,w,h);r('#dce1da',3,8,186,144);r('#c8d1ca',8,14,176,132);
 if(kind==='HELIPAD'){r('#c7cfce',12,12,168,136);r('#8d9b9e',20,20,152,120);for(let i=0;i<10;i++){r('#e9ece3',22+i*15,23,8,3);r('#e9ece3',22+i*15,134,8,3);}r('#f1f2ec',64,48,12,64);r('#f1f2ec',116,48,12,64);r('#f1f2ec',76,74,40,12);}
 else if(kind==='TOWER'){r('#aab7b5',60,24,72,112);r(colors.ink,92,7,8,121);for(let y=25;y<126;y+=18)r('#647d83',73,y,46,4);r('#c6d3ce',84,0,25,6);r('#8ba6a5',76,10,40,5);r('#e2e8df',83,8,27,3);}
 else if(kind==='PLAZA'){r('#d3d7cf',18,18,156,124);for(let x=23;x<174;x+=16)r('#eaebe2',x,18,1,124);for(let y=22;y<142;y+=16)r('#eaebe2',18,y,156,1);r('#a9b6b5',70,47,52,60);r('#b9d4d7',76,53,40,48);for(const [x,y] of [[35,36],[137,36],[35,112],[137,112]]){r('#8a8472',x,y,23,7);r('#b3a68b',x,y,23,3);}}
 else{const garage=kind==='GARAGE'||kind==='DEPOT';r('#b1b9b6',20,32,156,103);r(colors.ink,17,24,156,100);r('#b4b1c4',20,24,150,92);r('#d2cfda',24,28,142,37);r('#9c9eaf',24,69,142,44);r('#e6e4e8',28,28,134,3);for(let x=31;x<165;x+=18)r('#c3c0cc',x,30,2,81);r('#798a91',27,115,135,11);
 if(garage){for(const x of [32,80,128]){r(colors.ink,x,78,30,45);r('#84959b',x+3,81,24,37);for(let y=84;y<117;y+=7)r('#b0bdbe',x+3,y,24,1);}if(kind==='DEPOT')for(const [x,y] of [[7,119],[163,119]]){r('#9c9275',x,y,22,19);r('#ccbc91',x+2,y+2,18,4);}}
 else{for(const x of [34,67,117,148]){r(colors.ink,x,88,16,19);r(colors.glass,x+2,90,12,12);}r(colors.ink,90,89,18,35);r('#94b4b9',93,92,12,29);if(kind==='HOSPITAL'){r('#f1f2ec',70,42,53,27);r('#71966c',91,43,10,24);r('#71966c',80,50,32,9);}else{r('#dde3d9',70,43,53,26);r('#6c8790',76,50,41,9);r(colors.ink,94,45,3,24);}}}
 const texture=Texture.from(canvas);texture.source.scaleMode='nearest';return texture;}

export function turretTexture(type,team){const canvas=document.createElement('canvas');canvas.width=108;canvas.height=60;const ctx=canvas.getContext('2d'),r=(color,x,y,w,h)=>rectangle(ctx,color,x,y,w,h),c=team===0?'#2f6fed':'#e27632';
 if(type==='MBT'){ctx.fillStyle='#334155';ctx.beginPath();ctx.moveTo(33,22);ctx.lineTo(43,15);ctx.lineTo(64,15);ctx.lineTo(74,23);ctx.lineTo(74,37);ctx.lineTo(64,45);ctx.lineTo(43,45);ctx.lineTo(33,38);ctx.fill();r(c,39,19,29,22);r('#8c9d98',43,22,14,15);r('#c9d1bf',44,22,10,3);r('#334155',64,27,41,6);r('#aebbb1',65,28,40,3);r('#334155',101,25,6,10);}
 else if(type==='SPH'){r('#334155',21,11,38,38);r(c,24,14,32,32);r('#94a496',26,16,27,5);r('#334155',48,26,59,8);r('#aebbb1',50,28,57,3);r('#65776c',24,39,31,5);}
 else{r('#334155',42,20,24,20);r(c,44,22,20,16);r('#a5b6a9',47,24,10,9);r('#334155',62,28,27,4);r('#aebbb1',64,28,25,2);}
 const texture=Texture.from(canvas);texture.source.scaleMode='nearest';return texture;}
