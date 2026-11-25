"""Sync index.html to GitHub repo and wait for Pages build.
Usage: python sync.py
"""
import base64, json, urllib.request, urllib.error, subprocess, os, time

PROXY = "http://127.0.0.1:7897"
TOKEN = subprocess.check_output(["gh", "auth", "token"], text=True).strip()
opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
)
H = {"Authorization": f"Bearer {TOKEN}", "User-Agent": "workbuddy-sync",
     "Accept": "application/vnd.github+json"}

base = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(base, "index.html"), "rb") as f:
    b64 = base64.b64encode(f.read()).decode("ascii")

API = "https://api.github.com/repos/wulv2017/anna-site/contents/index.html"
try:
    cur = json.loads(opener.open(urllib.request.Request(API, headers=H), timeout=20).read().decode())
    sha = cur.get("sha")
except Exception:
    sha = None

payload = {"message": "Update page content", "content": b64, "branch": "main"}
if sha:
    payload["sha"] = sha

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(API, data=data, method="PUT",
                             headers={**H, "Content-Type": "application/json"})
try:
    with opener.open(req, timeout=30) as resp:
        print("UPLOAD:", resp.status)
except urllib.error.HTTPError as e:
    print("UPLOAD ERROR:", e.code, e.read().decode()[:500])
    raise

for i in range(18):
    req = urllib.request.Request(
        "https://api.github.com/repos/wulv2017/anna-site/pages", headers=H)
    try:
        r = json.loads(opener.open(req, timeout=15).read().decode())
        if r.get("status") == "built":
            print("PAGES: built")
            break
    except Exception:
        pass
    time.sleep(5)

html = opener.open(urllib.request.Request(
    "https://wulv2017.github.io/anna-site/", headers={"User-Agent": "workbuddy-sync"}),
    timeout=20).read().decode("utf-8", "ignore")
print("LIVE OK" if "你好，我是Anna" in html else "LIVE STALE")
print("LEN:", len(html))
