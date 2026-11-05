import json, urllib.request, urllib.error
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:400], flush=True)
q = "aw_0_1st.playerid=BMUK_TuneIn&aw_0_1st.skey=7374499933"
tests = ["https://stream-mz.hellorayo.co.uk/planetrock.aac?direct=true&" + q,
         "https://stream-mz.hellorayo.co.uk/planetrock.mp3?direct=true&" + q,
         "https://hls-mz.hellorayo.co.uk/planetrock.aac/playlist.m3u8",
         "https://stream.apollo.audio/cl1/hi/aac/?direct=true&" + q,
         "https://stream.apollo.audio/cl1/hi/hls/?direct=true",
         "https://stream-al.hellorayo.co.uk/clyde1.mp3?direct=true&" + q,
         "https://live-kiss.sharp-stream.com/kiss100.mp3"]
for u in tests:
    for ua in ("Mozilla/5.0", "VLC/3.0.20 LibVLC/3.0.20"):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": ua}), timeout=20) as r:
                d = r.read(2048); p("s", {"u": u, "ua": ua, "status": r.status, "final": r.geturl()[:150], "ct": r.headers.get("Content-Type"), "head": d[:60].decode("latin-1")})
        except urllib.error.HTTPError as e:
            p("s", {"u": u, "ua": ua, "status": e.code, "body": e.read(200).decode("utf-8", "replace")})
        except Exception as e:
            p("s", {"u": u, "ua": ua, "err": str(e)[:100]})
