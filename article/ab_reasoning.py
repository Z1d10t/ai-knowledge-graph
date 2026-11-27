import json
import os
import re
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
OUT = r"C:\Users\admin\Desktop\工作区\06-横向项目\知识库项目\ai-knowledge-graph-main\article\extracted\semiconductor_pilot"

md = OUT + r"\md\001_Chen_2024_Improved-charge-extraction-in-inverted-perovskit.md"
text = open(md, encoding="utf-8").read()
chunk = chunk_text(text, 450, 60)[0]
user = MAIN_USER_PROMPT + f"```\n{chunk}```\n"


def call(extra, max_tokens=32000):
    body = {"model": "deepseek-flash", "max_tokens": max_tokens, "temperature": 0.2,
            "messages": [{"role": "system", "content": MAIN_SYSTEM_PROMPT.strip()},
                         {"role": "user", "content": user}]}
    body.update(extra)
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=300, context=CTX) as r:
        d = json.loads(r.read())
    ch = d["choices"][0]
    u = d.get("usage") or {}
    return ch["message"].get("content") or "", ch.get("finish_reason"), u, time.time() - t0


def parse(s):
    s = re.sub(r"^```(?:json)?|```$", "", s.strip(), flags=re.M).strip()
    i, j = s.find("["), s.rfind("]")
    try:
        return json.loads(s[i:j + 1])
    except Exception:
        return []


res = {}
for label, extra in (("off", {"thinking": {"type": "disabled"}}), ("low", {"reasoning_effort": "low"})):
    content, fin, u, secs = call(extra)
    items = parse(content)
    res[label] = items
    open(f"{OUT}\\ab_{label}.json", "w", encoding="utf-8").write(json.dumps(items, ensure_ascii=False, indent=1))
    print(f"{label}: {secs:.0f}s finish={fin} triples={len(items)} out_tokens={u.get('completion_tokens')}")

a = {(x.get("subject", "").lower(), x.get("predicate", "").lower(), x.get("object", "").lower()) for x in res["off"]}
b = {(x.get("subject", "").lower(), x.get("predicate", "").lower(), x.get("object", "").lower()) for x in res["low"]}
print(f"\nexact overlap: {len(a & b)} | off-only {len(a - b)} | low-only {len(b - a)}")

print("\n--- sample 'off' (8) ---")
for x in res["off"][:8]:
    print(" ", x.get("subject"), "|", x.get("predicate"), "|", x.get("object"), "|", x.get("subject_type"), x.get("object_type"))
print("\n--- sample 'low' (8) ---")
for x in res["low"][:8]:
    print(" ", x.get("subject"), "|", x.get("predicate"), "|", x.get("object"), "|", x.get("subject_type"), x.get("object_type"))

print("\n--- predicate length check (off) ---")
bad = [x for x in res["off"] if len(str(x.get("predicate", "")).split()) > 3]
print("over 3 words:", len(bad), bad[:3])
types = {}
for x in res["off"]:
    for k in ("subject_type", "object_type"):
        types[x.get(k)] = types.get(x.get(k), 0) + 1
print("types:", sorted(types.items(), key=lambda kv: -kv[1]))
