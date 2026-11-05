import json, time, urllib.request, urllib.error, urllib.parse, uuid
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:600], flush=True)
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None
nr = urllib.request.build_opener(NoRedirect)
def head_chain(u, hdr):
    try:
        r = nr.open(urllib.request.Request(u, headers=hdr), timeout=25); return r.status, None
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location")
def get(u, hdr, n=20000):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=hdr), timeout=25) as r:
            return r.status, r.read(n).decode("utf-8", "replace"), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.read(300).decode("utf-8", "replace"), u
ids = {"Pointless": None, "Dragons’ Den": None, "Man City 24/7": None, "GUSTOTV": None, "Little Women: LA": None, "TNA Wrestling Channel": None}
for c in json.load(open(".probe/plex_sample.json")):
    if c["name"] in ids: ids[c["name"]] = c["id"]
UK = {"User-Agent": "Mozilla/5.0", "X-Forwarded-For": "193.62.157.66"}
# 1) jmp2 redirect target, slowly
for n, cid in ids.items():
    st, loc = head_chain(f"https://jmp2.uk/plex-{cid}.m3u8", {"User-Agent": "Mozilla/5.0"})
    p("jmp2", {"name": n, "st": st, "loc": (loc or "")[:140]}); time.sleep(4)
# 2) Plex guest (anonymous) token, as used by Plex's own web player
cid_hdr = {"X-Plex-Product": "Plex Web", "X-Plex-Client-Identifier": str(uuid.uuid4()), "X-Plex-Version": "4.145.0", "X-Plex-Platform": "Chrome", "Accept": "application/json", "User-Agent": "Mozilla/5.0"}
try:
    req = urllib.request.Request("https://plex.tv/api/v2/users/anonymous", data=b"", headers=cid_hdr, method="POST")
    with urllib.request.urlopen(req, timeout=25) as r: tok = json.load(r).get("authToken")
    p("anon", {"ok": bool(tok)})
except urllib.error.HTTPError as e:
    tok = None; p("anon", {"st": e.code, "b": e.read(200).decode("utf-8", "replace")})
if tok:
    for n, cid in ids.items():
        for label, hdr in (("plain", {"User-Agent": "Mozilla/5.0"}), ("ukip", UK)):
            st, body, final = get(f"https://epg.provider.plex.tv/library/parts/{cid}.m3u8?X-Plex-Token={tok}", hdr)
            ok = st == 200 and "#EXTM3U" in body
            seg = None
            if ok:
                v = [l for l in body.splitlines() if l and not l.startswith("#")]
                if v:
                    st2, vb, _ = get(urllib.parse.urljoin(final, v[0]), hdr); seg = (st2, sum(1 for l in vb.splitlines() if l and not l.startswith("#")))
            p("anon-stream", {"name": n, "how": label, "st": st, "ok": ok, "variant": seg, "b": "" if ok else body[:120]})
            time.sleep(2)
