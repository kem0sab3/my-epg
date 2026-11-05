import json, urllib.request, urllib.error
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:900], flush=True)
def get(u, n=3000, hdr=None):
    h = {"User-Agent": "Mozilla/5.0"}; h.update(hdr or {})
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=25) as r:
            return r.status, r.geturl(), r.headers.get("Content-Type"), r.read(n)
    except urllib.error.HTTPError as e:
        return e.code, u, None, e.read(300)
    except Exception as e:
        return None, u, None, str(e).encode()
cid = "64305451fc3be5947773c339-68dcbb869beaa3a402966dba"   # Plex: The Graham Norton Show (GB)
for u in ["https://i.mjh.nz/Plex/all.m3u8", "https://i.mjh.nz/Plex/gb.m3u8", "https://i.mjh.nz/Plex/.channels.json.gz",
          f"https://jmp2.uk/plex-{cid}.m3u8", f"https://jmp2.uk/plex-{cid}", "https://i.mjh.nz/Plex/",
          f"https://epg.provider.plex.tv/library/parts/{cid}?X-Plex-Token=x2QCJ1uZ-Jsp4nttuEKa"]:
    st, fu, ct, b = get(u)
    p("try", {"u": u[:110], "st": st, "final": fu[:150], "ct": ct, "head": b[:400].decode("utf-8", "replace")})
