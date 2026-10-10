const text=html=>String(html||'').replace(/<[^>]*>/g,' ').replace(/&amp;/g,'&').replace(/&nbsp;/g,' ').replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/\s+/g,' ').trim();
export function parseSuntory(html,code){
 const jan=html.match(/<meta\s+name=["']p_jan["']\s+content=["'](\d+)["']/i)?.[1];
 if(jan!==code)return null;
 const name=text(html.match(/<div\s+id=["']product["'][^>]*>\s*<h2[^>]*>([\s\S]*?)<\/h2>/i)?.[1]);
 const ingredients=text(html.match(/<dt[^>]*>\s*原材料\s*<\/dt>\s*<dd[^>]*>([\s\S]*?)<\/dd>/i)?.[1]);
 if(!name||!ingredients)return null;
 const image=html.match(/<meta\s+property=["']og:image["']\s+content=["']([^"']+)["']/i)?.[1]||'';
 const alcohol=text(html.match(/<dt[^>]*>\s*アルコール度数\s*<\/dt>\s*<dd[^>]*>([\s\S]*?)<\/dd>/i)?.[1]);
 return {code,product_name:name,brands:'Suntory',ingredients_text:ingredients,lang:'ja',image_url:image,_alcoholPercent:parseFloat(alcohol)||0,_source:'Suntory official product information',_sourceUrl:'https://products.suntory.co.jp/d/'+code+'/'};
}
