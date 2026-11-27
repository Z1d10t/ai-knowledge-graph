import json
import os
import sys
import time
import urllib.request
import ssl

sys.path.insert(0, r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main\src")
from knowledge_graph.prompts.main_prompts import MAIN_SYSTEM_PROMPT, MAIN_USER_PROMPT  # noqa: E402
from knowledge_graph.text_utils import chunk_text  # noqa: E402

KEY = os.environ.get("DEEPSEEK_API_KEY", "")
URL = "https://api.deepseek.com/chat/completions"
CTX = ssl._create_unverified_context()

md = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main\article\extracted\semiconductor_pilot\md\001_Chen_2024_Improved-charge-extraction-in-inverted-perovskit.md"
text = open(md, encoding="utf-8").read()
chunk = chunk_text(text, 450, 60)[0]
user = MAIN_USER_PROMPT + f"```\n{chunk}```\n"

BODY_BASE = {
    "model": "deepseek-flash",
    "messages": [{"role": "system", "content": MAIN_SYSTEM_PROMPT.strip()},
                 {"role": "user", "content": user}],
    "temperature": 0.2,
}


def call(label, extra, max_tokens=32000):
    body = dict(BODY_BASE)
    body["max_tokens"] = max_tokens
    body.update(extra)
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + KEY,
                                          "Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=300, context=CTX) as r:
            d = json.loads(r.read())
    except Exception as e:
        print(f"{label:34} FAIL {type(e).__name__}: {str(e)[:90]}  ({time.time()-t0:.0f}s)")
        return
    ch = d["choices"][0]
    u = d.get("usage") or {}
    det = u.get("completion_tokens_details") or {}
    content = ch["message"].get("content") or ""
    n_json = content.count('"subject"')
    print(f"{label:34} {time.time()-t0:5.0f}s finish={ch.get('finish_reason'):8} "
          f"out={u.get('completion_tokens'):>6} reasoning={det.get('reasoning_tokens')} "
          f"triples≈{n_json} len={len(content)}")


call("baseline 32k", {})
call("reasoning_effort=low", {"reasoning_effort": "low"})
call("reasoning_effort=minimal", {"reasoning_effort": "minimal"})
call("thinking disabled (anthropic)", {"thinking": {"type": "disabled"}})
call("enable_thinking=false (qwen)", {"enable_thinking": False})
