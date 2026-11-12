import {illustratedFacility} from './illustrated-units.js';import {pixelUnit,pixelTurret} from './tactical-pixels.js';
import {Texture,Rectangle} from 'pixi.js';import {TYPES} from './catalog.js';
export const FIELD={ground:0xb9c4a3,grass:0xaebb9a,road:0x8d9791,forest:0x708c5d,water:0x739f9f,building:0x93968a,a:0x2f6fed,b:0xe27632,neutral:0xc39a35,ink:0x334155};
export const TILE_COLORS=[FIELD.ground,FIELD.road,FIELD.forest,FIELD.ink,FIELD.building,FIELD.water,0x88bbc9,0xb3a286,FIELD.grass,0x98a49b,0xb4b9a2];
const colors={ink:'#334155',shadow:'#b5bdba',paper:'#f1f2ec',glass:'#9bc8d4',steel:'#8798a0',light:'#c5d2d7'};
function rectangle(ctx,color,x,y,w,h){ctx.fillStyle=color;ctx.fillRect(Math.round(x),Math.round(y),Math.round(w),Math.round(h));}
export class PixelAtlas{
 constructor(){this.canvas=document.createElement('canvas');this.canvas.width=1024;this.canvas.height=1024;const ctx=this.canvas.getContext('2d');ctx.imageSmoothingEnabled=false;this.frames=new Map();this.textures=new Map();let y=2;for(const [type,profile] of Object.entries(TYPES)){const scale=profile.kind==='vehicle'?.5:1,[w,h]=profile.size.map(v=>Math.ceil(v*scale));for(let team=0;team<3;team++)for(let frame=0;frame<3;frame++){const x=2+(team*3+frame)*(w+2);ctx.save();ctx.translate(x,y);pixelUnit(ctx,type,team,frame,w,h);ctx.restore();this.frames.set(`${type}:${team}:${frame}`,new Rectangle(x,y,w,h));}y+=h+4;}this.base=Texture.from(this.canvas);this.base.source.scaleMode='nearest';for(const [key,frame] of this.frames){const profile=TYPES[key.split(':')[0]];this.textures.set(key,new Texture({source:this.base.source,frame,orig:new Rectangle(0,0,...profile.size)}));}}

 get(type,team,frame=0){return this.textures.get(`${type}:${team??2}:${frame}`)??this.textures.get(`INF:${team??2}:0`);}
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
export function facilityTexture(kind){const canvas=document.createElement('canvas');canvas.width=96;canvas.height=80;const c=canvas.getContext('2d');c.scale(.5,.5);illustratedFacility(c,kind);const d=c.getImageData(0,0,96,80);for(let i=0;i<d.data.length;i+=4){for(let k=0;k<3;k++)d.data[i+k]=Math.round(d.data[i+k]/24)*24;d.data[i+3]=d.data[i+3]>128?255:0;}c.putImageData(d,0,0);const t=Texture.from(canvas);t.source.scaleMode='nearest';return new Texture({source:t.source,frame:new Rectangle(0,0,96,80),orig:new Rectangle(0,0,192,160)});}
export function turretTexture(type,team){const canvas=document.createElement('canvas');canvas.width=54;canvas.height=30;pixelTurret(canvas.getContext('2d'),type,team,54,30);const t=Texture.from(canvas);t.source.scaleMode='nearest';return new Texture({source:t.source,frame:new Rectangle(0,0,54,30),orig:new Rectangle(0,0,108,60)});}
