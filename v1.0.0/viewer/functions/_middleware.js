import {passwordGate} from '../src/password.js';
import {authorize} from '../src/access.js';
export async function onRequest(context){
 const publicViewer=context.env.PUBLIC_VIEWER==='true';
 const gate=publicViewer?true:await passwordGate(context.request,context.env);
 if(gate instanceof Response)return gate;
 if(gate!==true&&!await authorize(context.request,context.env))return new Response('Private viewer: access denied',{status:401,headers:{'Cache-Control':'no-store'}});
 const res=await context.next();const result=new Response(res.body,res);result.headers.set('Cache-Control','private, no-store');return result;
}
