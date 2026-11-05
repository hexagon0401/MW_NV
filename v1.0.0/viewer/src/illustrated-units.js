/** Four-times-resolution cel illustration. Geometry stays in original world units. */
function shape(c,points,fill,stroke='#344540',width=.65){c.beginPath();points.forEach(([x,y],i)=>i?c.lineTo(x,y):c.moveTo(x,y));c.closePath();c.fillStyle=fill;c.fill();if(stroke){c.strokeStyle=stroke;c.lineWidth=width;c.stroke();}}
function oval(c,x,y,rx,ry,fill){c.beginPath();c.ellipse(x,y,rx,ry,0,0,Math.PI*2);c.fillStyle=fill;c.fill();}
function panel(c,x,y,w,h,fill,r=2){c.beginPath();c.roundRect(x,y,w,h,r);c.fillStyle=fill;c.fill();c.strokeStyle='#384943';c.lineWidth=.6;c.stroke();}
function coat(c,x,y,w,h,team){const g=c.createLinearGradient(x,y,x+w,y+h);g.addColorStop(0,team===0?'#b2cbd0':'#e0c19b');g.addColorStop(.43,team===0?'#6e969f':'#b78e67');g.addColorStop(.45,team===0?'#60838b':'#a17c59');g.addColorStop(1,team===0?'#3e606a':'#795e49');return g;}
export function illustrate(c,type,team,frame,w,h){
 const marker=team===0?'#277ec8':'#d87e3e';
 if(['INF','REC','SUP','AT','MED','ENG'].includes(type)){
  const x=w/2,step=frame===1?1.2:frame===2?-1.2:0;
  panel(c,x-3.4,12,2.7,5+step,'#424d43',1);panel(c,x+.7,12,2.7,5-step,'#424d43',1);oval(c,x-2,17.6+step,1.7,1,'#283932');oval(c,x+2,17.6-step,1.7,1,'#283932');
  panel(c,x-4.5,6.5,9,7.8,coat(c,x-4,6,9,9,team),3);panel(c,x-3,10,6,4,'#596a50',1);c.fillStyle='#a0a482';c.fillRect(x-2.5,10.5,5,.7);
  oval(c,x-4.4,9,1.4,2.8,'#aeb492');oval(c,x+4.2,8,1.3,2.8,'#aeb492');panel(c,x+2.8,.5,1.4,10.5,'#35433d',.4);c.fillStyle='#b3bba6';c.fillRect(x+3,.7,.6,6);
  oval(c,x,5,3.5,2.7,'#c6ad84');oval(c,x,4,4.2,3.2,'#344a3d');oval(c,x-.3,3.3,3.6,2.8,'#7e9670');oval(c,x-1.3,2.4,2,.9,'#b5c19a');c.fillStyle=marker;c.fillRect(x-3,5.5,6,1.2);
  if(type==='MED'){panel(c,x-2,8,4,3,'#eee4cf',.5);c.fillStyle='#875f4c';c.fillRect(x-.5,8,1,3);c.fillRect(x-1.6,9,3.2,1);}
  if(type==='AT'||type==='SUP'){panel(c,x-6.4,2,2.7,12,type==='AT'?'#72815b':'#59685d',.6);panel(c,x-6.8,2,3.5,2,'#b4ad83',.4);}
  if(type==='ENG')panel(c,x-2,8,4,3,'#b9a575',.5);return;
 }
 if(type==='HEL'){
  shape(c,[[9,44],[17,38],[73,38],[87,44],[90,49],[81,56],[18,56],[9,51]],coat(c,12,38,76,19,team));panel(c,77,42,8,11,'#477481',2);c.fillStyle='#b3d9da';c.fillRect(78,43,2,8);
  for(let x=26;x<73;x+=10){panel(c,x,39,5,3,'#2c4c52',.6);panel(c,x,52,5,3,'#2c4c52',.6);}panel(c,40,43,20,9,'#698278',1);c.fillStyle=marker;c.fillRect(37,45,25,3);
  for(const x of [23,73]){oval(c,x,48,24,24,'rgba(71,88,78,.05)');c.save();c.translate(x,48);c.rotate(frame*1.05);for(let i=0;i<3;i++){c.rotate(Math.PI*2/3);shape(c,[[0,-1],[24,-1],[24,1],[4,2]],'#485b54',null);}c.restore();oval(c,x,48,3,3,'#b0b8a2');}return;
 }
 const tank=type==='MBT'||type==='SPH',wheelY=tank?8:7;
 for(const yy of [wheelY,h-wheelY]){if(tank){panel(c,5,yy-5,w-10,10,'#303e39',2);for(let x=9;x<w-7;x+=5){c.fillStyle='#748278';c.fillRect(x,yy-4,1.6,8);}}else for(const xx of [13,w-20])panel(c,xx-5,yy-4,11,8,'#2d3a35',2);}
 shape(c,[[6,14],[13,8],[w-18,8],[w-7,15],[w-5,h-16],[w-15,h-8],[12,h-8],[6,h-14]],coat(c,6,8,w-11,h-16,team));
 shape(c,[[10,13],[w-19,11],[w-12,15],[12,15]],'#c3d0b3',null);shape(c,[[10,h-14],[w-9,h-17],[w-15,h-9],[14,h-9]],'#435b4e',null);
 panel(c,w-24,13,10,h-26,'#35555a',1);c.fillStyle='#a1c7cb';c.fillRect(w-23,14,2,h-28);
 if(type==='LUV'){panel(c,15,11,23,h-22,'#566960',2);panel(c,19,12,7,h-24,'#8fb3b5',.6);panel(c,30,12,6,h-24,'#718e8c',.6);}
 else if(type==='TRK'){panel(c,10,11,w*.57,h-22,'#a6a081',2);for(let x=14;x<w*.63;x+=10){panel(c,x,14,8,h-28,'#b7ad86',.5);c.fillStyle='#d5c9a6';c.fillRect(x+1,15,6,1);}}
 else{for(const x of [22,43]){panel(c,x,16,13,h-32,'#627b69',2);c.fillStyle='#b0bd9f';c.fillRect(x+2,17,8,1);}if(type==='SPH'&&frame===2)for(const x of [10,w-20])for(const y of [1,h-5])panel(c,x,y,13,4,'#536657',.5);}
 c.fillStyle=marker;c.fillRect(w-38,h/2-3,10,6);c.fillStyle='#d8d9bc';c.fillRect(w-10,16,2,3);c.fillStyle='#cf9a60';c.fillRect(9,h-17,2,3);
}
export function illustratedTurret(c,type,team){
 const sph=type==='SPH',ifv=type==='IFV',x=sph?24:ifv?43:35,y=sph?13:ifv?20:16,w=sph?34:ifv?23:38,h=sph?34:ifv?20:28;
 shape(c,[[x,y+5],[x+7,y],[x+w-6,y],[x+w,y+7],[x+w,y+h-6],[x+w-8,y+h],[x+5,y+h],[x,y+h-5]],coat(c,x,y,w,h,team));
 panel(c,x+7,y+6,12,h-12,'#6e846e',3);oval(c,x+12,y+10,3,2,'#bcc6a7');panel(c,x+w-2,27,sph?51:ifv?27:35,5,'#445d4f',1);c.fillStyle='#b0bca1';c.fillRect(x+w,27.7,sph?47:ifv?23:31,1);panel(c,sph?103:ifv?90:104,26,3,7,'#344b40',.4);
}
export function illustratedFacility(c,kind){
 c.fillStyle='#b2bca3';c.fillRect(6,7,180,146);c.strokeStyle='#8c9d85';c.lineWidth=1;c.strokeRect(9,10,174,140);
 if(kind==='HELIPAD'){panel(c,18,19,156,122,'#81958a',8);c.strokeStyle='#d4d8bb';c.lineWidth=2;c.beginPath();c.ellipse(96,80,49,46,0,0,Math.PI*2);c.stroke();c.fillStyle='#d4d8bb';c.fillRect(74,55,7,50);c.fillRect(111,55,7,50);c.fillRect(79,76,34,7);return;}
 if(kind==='PLAZA'){panel(c,21,19,150,122,'#b4bba6',4);for(let x=25;x<166;x+=14){c.strokeStyle='rgba(236,235,207,.32)';c.beginPath();c.moveTo(x,23);c.lineTo(x,137);c.stroke();}panel(c,70,47,52,61,'#758f84',5);oval(c,95,76,19,22,'#8db6b5');oval(c,94,74,14,17,'#b6d0c3');for(const x of [36,143])for(const y of [40,116])panel(c,x-10,y-3,20,6,'#8b856a',1);return;}
 if(kind==='TOWER'){shape(c,[[85,27],[126,48],[117,137],[72,117]],'rgba(44,67,49,.17)',null);panel(c,62,21,66,112,'#a2afa0',3);for(let y=35;y<126;y+=20){c.strokeStyle='#6c8272';c.lineWidth=4;c.beginPath();c.moveTo(71,y);c.lineTo(120,y+16);c.moveTo(120,y);c.lineTo(71,y+16);c.stroke();}panel(c,71,14,50,29,'#6d897a',4);panel(c,77,17,39,13,'#bdc9aa',2);return;}
 shape(c,[[29,38],[177,39],[185,138],[34,141]],'rgba(44,62,48,.2)',null);panel(c,20,32,148,97,'#647d70',2);panel(c,18,23,149,91,'#aebba6',3);
 const roof=c.createLinearGradient(20,24,165,109);roof.addColorStop(0,'#d2d6b8');roof.addColorStop(.48,'#a9b99f');roof.addColorStop(.5,'#91a88f');roof.addColorStop(1,'#6e8b79');shape(c,[[19,25],[162,25],[169,71],[166,113],[20,113],[15,71]],roof);
 for(let x=30;x<162;x+=17){c.strokeStyle='rgba(53,78,61,.17)';c.lineWidth=.7;c.beginPath();c.moveTo(x,30);c.lineTo(x,109);c.stroke();}c.fillStyle='#d5dcc0';c.fillRect(20,25,142,2);c.fillStyle='#6c8576';c.fillRect(19,112,148,4);
 if(kind==='GARAGE'||kind==='DEPOT'){for(let x=29;x<150;x+=45){panel(c,x,95,31,33,'#405e53',1);for(let y=99;y<126;y+=5){c.fillStyle='#82998a';c.fillRect(x+2,y,27,1);}}}
 else{for(let x=32;x<160;x+=29)panel(c,x,117,14,8,'#739da0',.5);panel(c,88,112,17,20,'#4b7069',1);}
 if(kind==='HOSPITAL'){panel(c,72,45,50,27,'#e5e4c9',3);c.fillStyle='#9d6658';c.fillRect(92,48,9,21);c.fillRect(82,54,29,8);}
 else{panel(c,69,45,48,22,'#809b88',2);panel(c,74,48,36,12,'#c5d2b3',1);}if(kind==='DEPOT')for(const x of [5,160])panel(c,x,124,25,20,'#b8ac81',2);
}
