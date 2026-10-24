import {jwtVerify,createRemoteJWKSet} from 'jose';
const resolvers=new Map();
export async function authorize(request,env,key){
 if(!/^[a-z0-9-]+\.cloudflareaccess\.com$/.test(env.ACCESS_TEAM_DOMAIN??'')||!env.ACCESS_AUDIENCE)return false;
 const token=request.headers.get('Cf-Access-Jwt-Assertion');if(!token)return false;
 const issuer=`https://${env.ACCESS_TEAM_DOMAIN}`;
 if(!key){if(!resolvers.has(issuer))resolvers.set(issuer,createRemoteJWKSet(new URL(`${issuer}/cdn-cgi/access/certs`)));key=resolvers.get(issuer);}
 try{await jwtVerify(token,key,{issuer,audience:env.ACCESS_AUDIENCE,algorithms:['RS256']});return true;}catch{return false;}
}
