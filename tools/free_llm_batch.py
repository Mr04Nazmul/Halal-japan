#!/usr/bin/env python3
"""20+ prompt batch over free-tier OpenAI-compatible LLM providers.
Requires your own provider API key in environment or GitHub Actions secrets.
"""
import argparse, concurrent.futures, json, os, time, random
import urllib.request, urllib.error
from pathlib import Path

PROVIDERS = {
  "groq": ("GROQ_API_KEY", "https://api.groq.com/openai/v1/chat/completions", "openai/gpt-oss-20b"),
  "openrouter": ("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1/chat/completions", "openrouter/free")
}

def request_one(item):
    i, prompt, endpoint, key, model = item
    payload = json.dumps({"model":model, "messages":[{"role":"user","content":prompt}], "max_tokens":256}).encode()
    for attempt in range(4):
        req = urllib.request.Request(endpoint, data=payload, headers={"Authorization":"Bearer "+key, "Content-Type":"application/json", "User-Agent":"HalalJapanBatch/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.load(response)
            return {"index":i,"prompt":prompt,"ok":True,"answer":result["choices"][0]["message"].get("content","")}
        except urllib.error.HTTPError as e:
            reason = e.read(250).decode("utf-8", "replace")
            if e.code in (429,500,502,503,504) and attempt < 3:
                time.sleep(min(30, 2**attempt * 4) + random.random())
                continue
            return {"index":i,"prompt":prompt,"ok":False,"error":f"HTTP {e.code}: {reason}"}
        except Exception as e:
            if attempt < 3:
                time.sleep(2**attempt)
                continue
            return {"index":i,"prompt":prompt,"ok":False,"error":str(e)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--provider",choices=PROVIDERS,default="groq")
    p.add_argument("--input",required=True)
    p.add_argument("--output",default="llm-results.json")
    p.add_argument("--workers",type=int,default=3)
    p.add_argument("--model")
    args=p.parse_args()
    keyname,endpoint,defaultmodel=PROVIDERS[args.provider]
    key=os.getenv(keyname)
    if not key: p.error(f"Missing {keyname}; use secret environment variable, never commit API keys.")
    prompts=json.loads(Path(args.input).read_text(encoding="utf-8"))
    if not isinstance(prompts,list) or not all(isinstance(t,str) and t.strip() for t in prompts):
        p.error("Input must be a JSON array of non-empty prompt strings")
    jobs=[(i,t,endpoint,key,args.model or defaultmodel) for i,t in enumerate(prompts)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,min(args.workers,5))) as pool:
        results=list(pool.map(request_one,jobs))
    Path(args.output).write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Completed {sum(x['ok'] for x in results)}/{len(results)} requests; output: {args.output}")
if __name__=="__main__":
    main()
