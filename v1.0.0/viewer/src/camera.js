export function wheelFactor(event,height=800){const pixels=event.deltaY*(event.deltaMode===1?16:event.deltaMode===2?height:1);return Math.exp(Math.max(-.22,Math.min(.22,-pixels*.002)));}
export class Camera{
 constructor(host,world,width,height){
  Object.assign(this,{host,world,width,height,zoom:1,x:0,y:0,drag:null,moved:false});this.viewportWidth=host.clientWidth;this.viewportHeight=host.clientHeight;
  this.observer=new ResizeObserver(()=>{const w=host.clientWidth,h=host.clientHeight;if(w===this.viewportWidth&&h===this.viewportHeight)return;this.x+=(w-this.viewportWidth)/2;this.y+=(h-this.viewportHeight)/2;this.viewportWidth=w;this.viewportHeight=h;this.sync();});this.observer.observe(host);
  this.abort=new AbortController();const signal=this.abort.signal,listen=(name,fn,options={})=>host.addEventListener(name,fn,{...options,signal}),control=e=>e.target.closest('button,select,input,summary,details,#minimap');
  listen('wheel',e=>{if(control(e))return;e.preventDefault();this.onManual?.();const r=host.getBoundingClientRect();this.zoomAt(this.zoom*wheelFactor(e,host.clientHeight),e.clientX-r.left,e.clientY-r.top);},{passive:false});
  listen('pointerdown',e=>{if(control(e))return;this.moved=false;this.drag={id:e.pointerId,x:e.clientX,y:e.clientY,startX:e.clientX,startY:e.clientY};host.setPointerCapture(e.pointerId);host.focus({preventScroll:true});});
  listen('pointermove',e=>{const d=this.drag;if(d?.id!==e.pointerId)return;if(!this.moved&&Math.hypot(e.clientX-d.startX,e.clientY-d.startY)<5)return;this.moved=true;this.onManual?.();this.x+=e.clientX-d.x;this.y+=e.clientY-d.y;d.x=e.clientX;d.y=e.clientY;this.sync();});
  const stop=()=>this.drag=null;listen('pointerup',stop);listen('pointercancel',stop);listen('lostpointercapture',stop);
  listen('keydown',e=>{if(control(e))return;const delta={ArrowLeft:[60,0],ArrowRight:[-60,0],ArrowUp:[0,60],ArrowDown:[0,-60]}[e.key];if(delta){e.preventDefault();this.onManual?.();this.x+=delta[0];this.y+=delta[1];this.sync();}if(e.key==='Home'){e.preventDefault();this.onManual?.();this.fit();}});
 }
 sync(){const w=this.host.clientWidth,h=this.host.clientHeight,z=this.zoom;this.x=this.width*z<w?(w-this.width*z)/2:Math.min(24,Math.max(w-this.width*z-24,this.x));this.y=this.height*z<h?(h-this.height*z)/2:Math.min(24,Math.max(h-this.height*z-24,this.y));this.world.position.set(this.x,this.y);this.world.scale.set(z);const label=document.querySelector('#zoom-label');if(label)label.textContent=`${Math.round(z*100)}%`;}
 zoomAt(next,x=this.host.clientWidth/2,y=this.host.clientHeight/2){this.viewportWidth=this.host.clientWidth;this.viewportHeight=this.host.clientHeight;next=Math.round(Math.max(.035,Math.min(4,next))*1e6)/1e6;this.x=x-(x-this.x)*next/this.zoom;this.y=y-(y-this.y)*next/this.zoom;this.zoom=next;this.sync();}
 focus(x,y){this.viewportWidth=this.host.clientWidth;this.viewportHeight=this.host.clientHeight;this.x=this.host.clientWidth/2-x*this.zoom;this.y=this.host.clientHeight/2-y*this.zoom;this.sync();}
 fit(){this.zoom=Math.min(this.host.clientWidth/this.width,this.host.clientHeight/this.height)*.94;this.focus(this.width/2,this.height/2);}
 destroy(){this.abort.abort();this.observer.disconnect();}
}
