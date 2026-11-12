import {adminRoute} from '../../../src/admin-server.js';export const onRequest=({request,env})=>adminRoute(request,env);
