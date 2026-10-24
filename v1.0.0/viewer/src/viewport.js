import {PX_PER_M} from './catalog.js';
export function visibleChunks(x,y,zoom,width,height,mapWidth=1024,mapHeight=mapWidth){
 if(!Number.isFinite(zoom)||zoom<=0)return [];
 const size=128*PX_PER_M,result=[],startX=Math.max(0,Math.floor(-x/zoom/size)),startY=Math.max(0,Math.floor(-y/zoom/size)),endX=Math.min(Math.ceil(mapWidth/128),Math.ceil((width-x)/zoom/size)),endY=Math.min(Math.ceil(mapHeight/128),Math.ceil((height-y)/zoom/size));
 for(let row=startY;row<endY;row++)for(let col=startX;col<endX;col++)result.push([col,row]);return result;
}
