import {adminRoute} from '../src/admin-server.js';
import {passwordGate} from '../src/password.js';
import {authorize} from '../src/access.js';
export async function onRequest(context){
 const path=new URL(context.request.url).pathname;
 if(path.startsWith('/api/admin/'))return adminRoute(context.request,context.env);
 const publicViewer=context.env.PUBLIC_VIEWER==='true';
 const gate=publicViewer?true:await passwordGate(context.request,context.env);
 if(gate instanceof Response)return gate;
 if(gate!==true&&!await authorize(context.request,context.env))return new Response('Private viewer: access denied',{status:401,headers:{'Cache-Control':'no-store'}});
 const res=await context.next();const result=new Response(res.body,res);result.headers.set('Cache-Control','private, no-store');result.headers.set('X-Content-Type-Options','nosniff');result.headers.set('Referrer-Policy','same-origin');if(path.startsWith('/dashboard'))result.headers.set('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'");return result;
}
