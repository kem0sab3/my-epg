import json, urllib.request, urllib.error, urllib.parse, time
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:500], flush=True)
def fetch(u, n=2048, ua="Mozilla/5.0"):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": ua}), timeout=20) as r:
            return r.status, r.geturl(), r.headers.get("Content-Type"), r.read(n)
    except urllib.error.HTTPError as e:
        return e.code, u, None, e.read(200)
    except Exception as e:
        return None, u, None, str(e).encode()
hls = {"Clyde 1": "https://stream.apollo.audio/cl1/hi/hls/?direct=true", "Forth 1": "https://hls-al.hellorayo.co.uk/forth1.aac/playlist.m3u8",
       "Northsound 1": "https://hls-mz.hellorayo.co.uk/northsound1.aac/playlist.m3u8", "Tay FM": "https://hls-mz.hellorayo.co.uk/tayfm.aac/playlist.m3u8",
       "MFR": "https://hls-mz.hellorayo.co.uk/mfrfm.aac/playlist.m3u8", "KISS": "https://hls-kiss.hellorayo.co.uk/kissnational.aac/playlist.m3u8",
       "Planet Rock": "https://hls-mz.hellorayo.co.uk/planetrock.aac/playlist.m3u8"}
for name, u in hls.items():
    st, final, ct, body = fetch(u, 4000)
    txt = body.decode("utf-8", "replace")
    p("master", {"name": name, "st": st, "final": final, "body": txt[:300]})
    lines = [l for l in txt.splitlines() if l and not l.startswith("#")]
    if st == 200 and lines:
        v = urllib.parse.urljoin(final, lines[0]); st2, f2, ct2, b2 = fetch(v, 4000); t2 = b2.decode("utf-8", "replace")
        p("variant", {"name": name, "st": st2, "url": v[:160], "body": t2[:300]})
        segs = [l for l in t2.splitlines() if l and not l.startswith("#")]
        if st2 == 200 and segs:
            s = urllib.parse.urljoin(f2, segs[-1]); st3, f3, ct3, b3 = fetch(s, 1000)
            p("segment", {"name": name, "st": st3, "ct": ct3, "url": s[:160], "len": len(b3)})
# direct streams: which query params are needed?
for base in ["https://stream-al.hellorayo.co.uk/clyde1.aac", "https://stream-al.hellorayo.co.uk/forth1.aac", "https://stream-mz.hellorayo.co.uk/tayfm.aac"]:
    for q in ["", "?direct=true", "?direct=true&aw_0_1st.skey=1700000000", "?direct=true&aw_0_1st.playerid=my-epg",
              "?direct=true&aw_0_1st.playerid=BMUK_TuneIn&aw_0_1st.skey=7374499933"]:
        st, final, ct, body = fetch(base + q, 1000)
        p("direct", {"u": base + q, "st": st, "ct": ct, "final": final[:120] if final else None, "len": len(body)})
