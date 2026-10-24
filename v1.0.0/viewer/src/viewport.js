export function visibleChunks(x,y,zoom,width,height,mapSize=1024){
 const result=[];const size=384;
 for(let row=0;row<Math.ceil(mapSize/128);row++)for(let col=0;col<Math.ceil(mapSize/128);col++){
  const left=x+col*size*zoom,top=y+row*size*zoom;
  if(left<width&&top<height&&left+size*zoom>0&&top+size*zoom>0)result.push([col,row]);
 }
 return result;
}
