const CACHE_NAME="japan-halal-checker-shell-v7-halal-shopping";
const SHELL=["./","./index.html","./manifest.webmanifest","./icon.svg","./languages.js?v=38-r7","./product-data.js?v=38-r7","./locale-pack.js?v=38-r7","./app-config.js?v=38-r7","./manufacturer-records.js?v=38-r7","./store-records.js?v=38-r7","./halal-shopping-records.js?v=38-r7"];
self.addEventListener("install",event=>event.waitUntil(caches.open(CACHE_NAME).then(cache=>cache.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener("activate",event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith("japan-halal-checker-shell-")&&key!==CACHE_NAME).map(key=>caches.delete(key)))).then(()=>self.clients.claim())));
self.addEventListener("fetch",event=>{
 const request=event.request,url=new URL(request.url);
 if(request.method!=="GET"||url.origin!==self.location.origin||url.pathname.includes("/api/"))return;
 event.respondWith(fetch(request).then(response=>{
  if(response.ok){const copy=response.clone();event.waitUntil(caches.open(CACHE_NAME).then(cache=>cache.put(request,copy)));}
  return response;
 }).catch(async()=>{const cached=await caches.match(request);if(cached)return cached;if(request.mode==="navigate"){const fallback=await caches.match("./index.html");if(fallback)return fallback;}return Response.error();}));
});
