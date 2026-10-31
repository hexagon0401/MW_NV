/** Native pixel clusters, a fixed five-tone ramp and ordered dithering. No gradients. */
const INK='#2f4038',DARK='#506559',MID='#7d9075',LIGHT='#a9b69a',SUN='#d1d0ad';
function rect(c,color,x,y,w,h){c.fillStyle=color;c.fillRect(Math.round(x),Math.round(y),Math.round(w),Math.round(h));}
function poly(c,points,color){ // rasterize scanlines: no anti-aliased Canvas paths
 const min=Math.floor(Math.min(...points.map(p=>p[1]))),max=Math.ceil(Math.max(...points.map(p=>p[1])));c.fillStyle=color;
 for(let y=min;y<max;y++){const hits=[];for(let i=0;i<points.length;i++){const a=points[i],b=points[(i+1)%points.length];if((a[1]<=y+.5&&b[1]>y+.5)||(b[1]<=y+.5&&a[1]>y+.5))hits.push(a[0]+(y+.5-a[1])*(b[0]-a[0])/(b[1]-a[1]));}hits.sort((a,b)=>a-b);for(let i=0;i+1<hits.length;i+=2)c.fillRect(Math.ceil(hits[i]),y,Math.ceil(hits[i+1])-Math.ceil(hits[i]),1);}
}
function dither(c,x,y,w,h,a,b){rect(c,a,x,y,w,h);for(let yy=y;yy<y+h;yy++)for(let xx=x;xx<x+w;xx++)if((xx+yy)%2===0)rect(c,b,xx,yy,1,1);}
export function pixelUnit(c,type,team,frame,w,h){const r=(color,x,y,ww,hh)=>rect(c,color,x,y,ww,hh),stripe=team==null||team===2?'#b3ad86':team===0?'#4489cb':'#d78c48';
 if(['INF','REC','AT','SUP','MED','ENG'].includes(type)){const x=Math.floor(w/2),step=frame===1?1:frame===2?-1:0;r(INK,x-3,12,2,6+step);r(INK,x+1,12,2,6-step);r(DARK,x-4,7,8,7);r(MID,x-3,7,6,5);r(LIGHT,x-3,7,5,1);r(DARK,x-2,10,4,4);r(INK,x-5,2,9,5);r(MID,x-4,1,7,5);r(LIGHT,x-3,1,4,2);r(SUN,x-2,1,2,1);r(stripe,x-3,5,6,1);r(INK,x+3,0,2,12);r(LIGHT,x+3,3,1,6);r(LIGHT,x-5,8,2,4);if(type==='AT'){r(INK,0,1,3,14);r(MID,1,3,2,9);}if(type==='MED'){r('#e2dcc0',x-2,8,4,4);r('#a25442',x-1,8,1,4);r('#a25442',x-2,9,4,1);}if(type==='SUP')r(INK,w-2,0,2,14);if(type==='REC')r(DARK,x-4,3,7,1);return;}
 if(['BH','LB'].includes(type)){const cx=w/2,cy=h/2,bh=type==='BH';r(INK,3,cy-1,cx-2,3);poly(c,[[cx-5,cy-4],[cx+6,cy-4],[cx+10,cy-1],[cx+10,cy+2],[cx+5,cy+5],[cx-5,cy+4]],INK);r(MID,cx-4,cy-3,11,6);r(LIGHT,cx-3,cy-3,8,1);r('#89b8bd',cx+5,cy-2,4,4);r(stripe,cx-3,cy-1,5,2);r(INK,3,cy-5,2,11);r(LIGHT,2,cy-4,4,1);for(const yy of [-6,6])r(INK,cx-3,cy+yy,bh?13:10,1);if(!bh){r(INK,cx+3,cy-6,9,2);r(INK,cx+3,cy+5,9,2);}if(frame===2){for(let k=-Math.floor(w*.38);k<=w*.38;k++){r(INK,cx+k,cy+k,2,1);r(INK,cx+k,cy-k,2,1);}}else{r(INK,3,cy,w-6,1);r(INK,cx,3,1,h-6);}r(SUN,cx-1,cy-1,3,3);return;}
 if(type==='AA_SITE'){r(DARK,2,2,w-4,h-4);r(LIGHT,3,3,w-6,2);for(const [x,y] of [[2,2],[w-8,2],[2,h-8],[w-8,h-8]]){r(INK,x,y,6,6);r(MID,x+1,y+1,4,3);}r(INK,w/2-5,h/2-5,10,10);r(MID,w/2-4,h/2-4,8,8);r(stripe,w/2-3,h/2-2,6,2);for(const yy of [-2,2])r(INK,w/2,h/2+yy,w/2-2,1);r(LIGHT,w/2-3,h/2-4,5,1);return;}
 if(type==='HEL'){poly(c,[[3,h/2-3],[10,h/2-6],[w-10,h/2-6],[w-3,h/2-2],[w-3,h/2+3],[w-10,h/2+6],[9,h/2+6],[3,h/2+2]],INK);r(MID,8,h/2-4,w-17,8);r(LIGHT,10,h/2-4,w-21,2);r(DARK,8,h/2+3,w-17,2);r('#88b2b7',w-8,h/2-2,4,5);r(stripe,w/2-6,h/2-1,12,2);for(const x of [12,w-12]){if(frame===2){for(let k=-10;k<=10;k++){r(INK,x+k,h/2+k,2,1);r(INK,x+k,h/2-k,2,1);}}else{r(INK,x-11,h/2,23,1);r(INK,x,h/2-11,1,23);}r(LIGHT,x-1,h/2-1,3,3);}return;}
 const tracked=['MBT','SPH','IFV'].includes(type),truck=['APC','TRK'].includes(type),front=w-8;
 if(tracked){r(INK,2,1,w-4,5);r(INK,2,h-6,w-4,5);for(let x=3;x<w-3;x+=3){r('#69745d',x,2,1,3);r('#69745d',x,h-5,1,3);}}
 else{const axles=type==='TRK'?[5,12,w-16,w-9]:truck?[6,14,w-9]:[8,w-9];for(const x of axles){r(INK,x,1,5,4);r(INK,x,h-5,5,4);r('#687160',x+1,1,3,1);}}
 poly(c,[[3,7],[7,4],[w-8,4],[w-3,7],[w-3,h-7],[w-7,h-4],[6,h-4],[3,h-8]],INK);r(MID,5,5,w-10,h-10);r(LIGHT,6,5,w-13,2);r(DARK,5,h-8,w-10,3);
 if(truck){r(INK,front-5,5,9,h-10);r(MID,front-4,6,7,h-12);r('#83a6aa',front,7,3,h-14);r('#bbd0be',front,7,1,h-14);r(INK,6,6,w-23,h-12);r('#a49b72',7,7,w-25,h-14);dither(c,8,h-12,w-27,3,'#a49b72','#7c805d');for(let x=10;x<w-20;x+=7)r('#ccc199',x,7,1,h-14);if(type==='TRK')for(let x=9;x<w-20;x+=7){r(DARK,x,9,5,h-18);r(LIGHT,x,9,5,1);}}
 else if(type==='LUV'){r(INK,10,5,12,h-10);r('#809f9f',12,6,3,h-12);r(DARK,16,6,5,h-12);r(LIGHT,17,7,3,h-14);r(DARK,w-12,6,5,h-12);}
 else {r(DARK,9,7,11,h-14);r(LIGHT,10,7,9,1);for(let x=w-19;x<w-9;x+=3)r(INK,x,7,1,h-14);if(type==='SPH'&&frame===2)for(const x of [5,w-10]){r(INK,x,0,5,3);r(INK,x,h-3,5,3);}}
 if(type==='MBT'){for(let xx=7;xx<18;xx+=3){r(INK,xx,8,1,h-16);r(LIGHT,xx+1,8,1,h-16);}r(LIGHT,w-13,6,6,1);r(DARK,w-8,9,2,h-18);}
 if(type==='AA'){r(DARK,8,7,14,h-14);r(INK,w-17,5,11,h-10);r(LIGHT,w-16,6,8,1);for(const yy of [h/2-3,h/2+2])r(INK,w-14,yy,14,2);r(stripe,10,h/2-2,8,4);}
 if(type==='IFV'){r(INK,8,8,6,6);r(LIGHT,9,8,4,1);r(DARK,w-14,h/2-3,5,6);}
 if(type==='SPH'){r(INK,7,8,8,8);r(LIGHT,8,8,5,1);}
 if(type==='TRK')for(let xx=9;xx<w-23;xx+=8){r('#647868',xx,9,6,h-18);r('#bbb99a',xx,9,6,1);}
 r(stripe,w-17,h/2-2,6,4);r(SUN,w-5,6,1,2);
}
export function pixelTurret(c,type,team,w,h){const r=(color,x,y,ww,hh)=>rect(c,color,x,y,ww,hh),x=type==='SPH'?11:type==='IFV'?20:16,y=type==='SPH'?5:8,ww=type==='SPH'?18:type==='IFV'?12:20,hh=type==='SPH'?20:14;
 poly(c,[[x,y+3],[x+4,y],[x+ww-4,y],[x+ww,y+3],[x+ww,y+hh-3],[x+ww-4,y+hh],[x+3,y+hh],[x,y+hh-3]],INK);r(MID,x+2,y+2,ww-4,hh-4);r(LIGHT,x+3,y+1,ww-7,2);dither(c,x+2,y+hh-5,ww-4,2,MID,DARK);r(DARK,x+5,y+5,6,5);r(LIGHT,x+5,y+5,4,1);r(INK,x+ww-2,13,type==='SPH'?27:type==='IFV'?13:19,4);r(LIGHT,x+ww,14,type==='SPH'?24:type==='IFV'?10:16,1);r(INK,type==='IFV'?43:51,12,2,6);
}
