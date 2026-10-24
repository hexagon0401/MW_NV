import {authorize} from '../src/access.js';
export async function onRequest(context){
 if(!await authorize(context.request,context.env))return new Response('Private viewer: access denied',{status:401,headers:{'Cache-Control':'no-store'}});
 const res=await context.next();const result=new Response(res.body,res);result.headers.set('Cache-Control','private, no-store');return result;
}
