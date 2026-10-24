export class Camera{
 constructor(host,world,width,height){Object.assign(this,{host,world,width,height,zoom:1,x:0,y:0,drag:null});this.viewportWidth=host.clientWidth;this.viewportHeight=host.clientHeight;this.observer=new ResizeObserver(()=>{const w=host.clientWidth,h=host.clientHeight;if(w===this.viewportWidth&&h===this.viewportHeight)return;this.x+=(w-this.viewportWidth)/2;this.y+=(h-this.viewportHeight)/2;this.viewportWidth=w;this.viewportHeight=h;this.sync();});this.observer.observe(host);this.abort=new AbortController();const signal=this.abort.signal,listen=(name,fn,options={})=>host.addEventListener(name,fn,{...options,signal});
  listen('wheel',e=>{if(e.target.closest('button,select,input,#minimap'))return;e.preventDefault();if(e.ctrlKey||e.metaKey)this.zoomAt(this.zoom*Math.exp(-e.deltaY*.002),e.offsetX,e.offsetY);else{this.x-=e.shiftKey?e.deltaY:e.deltaX;this.y-=e.shiftKey?0:e.deltaY;this.sync();}},{passive:false});
  listen('pointerdown',e=>{if(e.target.closest('button,select,input,#minimap'))return;this.drag={id:e.pointerId,x:e.clientX,y:e.clientY};host.setPointerCapture(e.pointerId);host.focus({preventScroll:true});});
  listen('pointermove',e=>{if(this.drag?.id!==e.pointerId)return;this.x+=e.clientX-this.drag.x;this.y+=e.clientY-this.drag.y;this.drag.x=e.clientX;this.drag.y=e.clientY;this.sync();});
  const stop=()=>this.drag=null;listen('pointerup',stop);listen('pointercancel',stop);listen('lostpointercapture',stop);
  listen('keydown',e=>{const delta={ArrowLeft:[60,0],ArrowRight:[-60,0],ArrowUp:[0,60],ArrowDown:[0,-60]}[e.key];if(delta){e.preventDefault();this.x+=delta[0];this.y+=delta[1];this.sync();}if(e.key==='Home'){e.preventDefault();this.fit();}});
 }
 sync(){const w=this.host.clientWidth,h=this.host.clientHeight,z=this.zoom;this.x=this.width*z<w?(w-this.width*z)/2:Math.min(24,Math.max(w-this.width*z-24,this.x));this.y=this.height*z<h?(h-this.height*z)/2:Math.min(24,Math.max(h-this.height*z-24,this.y));this.world.position.set(this.x,this.y);this.world.scale.set(z);document.querySelector('#zoom-label').textContent=`${Math.round(z*100)}%`;}
 zoomAt(next,x=this.host.clientWidth/2,y=this.host.clientHeight/2){this.viewportWidth=this.host.clientWidth;this.viewportHeight=this.host.clientHeight;next=Math.max(.035,Math.min(4,next));this.x=x-(x-this.x)*next/this.zoom;this.y=y-(y-this.y)*next/this.zoom;this.zoom=next;this.sync();}
 focus(x,y){this.viewportWidth=this.host.clientWidth;this.viewportHeight=this.host.clientHeight;this.x=this.host.clientWidth/2-x*this.zoom;this.y=this.host.clientHeight/2-y*this.zoom;this.sync();}
 fit(){this.zoom=Math.min(this.host.clientWidth/this.width,this.host.clientHeight/this.height)*.94;this.focus(this.width/2,this.height/2);}
 destroy(){this.abort.abort();this.observer.disconnect();}
}
