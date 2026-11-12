// Optional private-test login. No backend credentials are sent to the browser.
import {SignJWT,jwtVerify} from 'jose';
const encoder=new TextEncoder();
async function equal(a,b){const hash=async s=>new Uint8Array(await crypto.subtle.digest('SHA-256',encoder.encode(s)));const [x,y]=await Promise.all([hash(a),hash(b)]);return x.reduce((v,c,i)=>v|(c^y[i]),0)===0;}
export async function passwordGate(request,env){
 const secret=env.MW_NV_VIEWER_PASSWORD;
 if(!secret||secret.length<16)return null;
 const url=new URL(request.url);const cookie=request.headers.get('cookie')?.match(/(?:^|;\s*)mw_nv_session=([^;]+)/)?.[1];
 if(cookie)try{await jwtVerify(cookie,encoder.encode(secret),{algorithms:['HS256'],issuer:'mw-nv',audience:url.origin});return true;}catch{}
 if(request.method==='POST'&&url.pathname==='/login'){
  if(request.headers.get('origin')!==url.origin)return new Response('Forbidden',{status:403});
  if(Number(request.headers.get('content-length')??0)>2048)return new Response('Too large',{status:413});
  const body=await request.text();if(body.length>2048)return new Response('Too large',{status:413});
  const password=new URLSearchParams(body).get('password')??'';
  if(await equal(password,secret)){
   const token=await new SignJWT({}).setProtectedHeader({alg:'HS256'}).setIssuer('mw-nv').setAudience(url.origin).setExpirationTime('8h').sign(encoder.encode(secret));
   return new Response(null,{status:303,headers:{Location:'/', 'Set-Cookie':`mw_nv_session=${token}; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=28800`,'Cache-Control':'no-store'}});
  }
  return new Response('비밀번호가 올바르지 않습니다.',{status:401,headers:{'Cache-Control':'no-store'}});
 }
 if(url.pathname.startsWith('/api/'))return new Response('Authentication required',{status:401,headers:{'Cache-Control':'no-store'}});
 return new Response('<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>MW-NV · 비공개 관전</title><body style="background:#FEF5EF;color:#07004D;font:18px system-ui;max-width:440px;margin:15vh auto;padding:24px"><h1>MW—NV</h1><p>비공개 테스트 관전</p><form method="post" action="/login"><label>접속 비밀번호<input name="password" type="password" autocomplete="current-password" required style="display:block;padding:12px;margin:16px 0;width:90%"></label><button style="padding:12px 24px">접속</button></form></body></html>',{status:200,headers:{'Content-Type':'text/html;charset=utf-8','Cache-Control':'no-store','Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'",'X-Content-Type-Options':'nosniff'}});
}
