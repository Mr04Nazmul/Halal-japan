/**
 * Yahoo! Shopping 商品検索 (v3) proxy.
 * Deploy as a serverless function; set YAHOO_CLIENT_ID as a server-side secret.
 * Do not place the Client ID in the public Android bundle or GitHub.
 * No product listing is evidence of halal certification.
 */
const ENDPOINT = 'https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch';
let lastCall = 0;
export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'private, max-age=60');
  if (req.method !== 'GET') return res.status(405).json({error:'Method not allowed'});
  const code = String(req.query.jan_code || '');
  if (!/^(\d{8}|\d{12,14})$/.test(code)) return res.status(400).json({error:'Invalid barcode'});
  const appid = process.env.YAHOO_CLIENT_ID;
  if (!appid) return res.status(503).json({error:'Yahoo API not configured'});
  const now = Date.now();
  if (now-lastCall < 1000) return res.status(429).json({error:'Please retry in a moment'});
  lastCall=now;
  const url = new URL(ENDPOINT);
  url.searchParams.set('appid', appid);
  url.searchParams.set('jan_code', code);
  url.searchParams.set('results','5');
  try {
    const response = await fetch(url.toString(), {signal:AbortSignal.timeout(8000)});
    if (!response.ok) return res.status(response.status).json({error:'Yahoo lookup unavailable'});
    const json = await response.json();
    const hits = (json.hits || []).filter(x=>x.janCode===code).map(x=>({
      name:x.name||'', janCode:x.janCode, brand:x.brand?.name||'',
      seller:x.seller?.name||'', productUrl:x.url||'', source:'Yahoo! Shopping Japan'
    }));
    return res.status(200).json({products:hits, source:'Yahoo! Shopping Japan', halalVerified:false, ingredientsVerified:false});
  } catch (_) {return res.status(502).json({error:'Yahoo lookup failed'});}
}
