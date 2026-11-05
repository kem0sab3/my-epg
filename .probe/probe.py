import json, urllib.request, urllib.error, datetime
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:1500], flush=True)
def get(url, hdr=None, n=None):
    h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}; h.update(hdr or {})
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=40) as r:
            return r.status, r.read(n) if n else r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read(300)
    except Exception as e:
        return None, str(e).encode()
# Sky services (radio)
seen = {}
for bq, sub in [(4101, 1), (4097, 1), (4101, 2)]:
    st, body = get(f"https://awk.epgsky.com/hawk/linear/services/{bq}/{sub}")
    try: j = json.loads(body)
    except Exception: p("sky-err", {"bq": bq, "st": st, "b": body[:200].decode("utf-8", "replace")}); continue
    p("sky-keys", {"bq": bq, "keys": list(j.keys()), "n": len(j.get("services") or [])})
    for s in j.get("services") or []:
        if s.get("sid") in seen: continue
        seen[s.get("sid")] = 1
        t = s.get("t", ""); sg = s.get("sg")
        if sg in (7, "7") or "radio" in str(s.get("sg", "")).lower() or any(w in t for w in ("Radio", "Capital", "Heart", "Smooth", "Classic", "LBC", "Boom", "Times", "talk", "Gold", "Absolute", "Kiss", "KISS", "Magic", "Greatest", "Jazz", "Scala", "Virgin", "Premier", "BFBS", "Planet", "Union", "Country")):
            p("sky", {"sid": s.get("sid"), "t": t, "sg": sg, "c": s.get("c")})
d = datetime.date.today().strftime("%Y%m%d")
# Global extra streams
G = "https://media-ssl.musicradio.com/"
for m in ["CapitalDanceMP3", "CapitalChillMP3", "CapitalAnthemsMP3", "Heart70sMP3", "Heart00sMP3", "HeartXmasMP3", "SmoothChillMP3", "SmoothCountryMP3",
          "Smooth70sMP3", "SmoothRelaxMP3", "ClassicFMRelaxMP3", "ClassicFM-M-Relax", "ClassicFMMoviesMP3", "RadioXClassicRockMP3", "RadioXChillMP3", "GoldUKMP3", "LBCUKMP3"]:
    try:
        with urllib.request.urlopen(urllib.request.Request(G + m, headers={"User-Agent": "Mozilla/5.0"}), timeout=15) as r:
            p("gstream", {"m": m, "st": r.status, "ct": r.headers.get("Content-Type")})
    except urllib.error.HTTPError as e: p("gstream", {"m": m, "st": e.code})
    except Exception as e: p("gstream", {"m": m, "err": str(e)[:60]})
# Times / Boom streams
for u in ["https://timesradio.wireless.radio/stream", "https://stream.boomradio.com/stream", "https://boomradio.wireless.radio/stream", "https://radio.talksport.com/talksport2", "https://talksport2.wireless.radio/stream"]:
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=15) as r:
            p("tbstream", {"u": u, "st": r.status, "final": r.geturl()[:120], "ct": r.headers.get("Content-Type")})
    except urllib.error.HTTPError as e: p("tbstream", {"u": u, "st": e.code})
    except Exception as e: p("tbstream", {"u": u, "err": str(e)[:60]})
# LG Channels
for hdr in [{"x-device-country": "GB", "x-device-language": "en"},
            {"x-device-country": "GB", "x-device-language": "en", "x-device-type": "webOSTV", "x-device-platform": "webOS"},
            {"x-device-country": "GB", "x-device-language": "en", "x-device-model": "HE_DTV_W21A_AFADATAA", "x-device-sdk": "6.0.0", "x-device-type": "webOS", "x-device-platform": "webOS", "x-device-product": "webOSTV 6.0"}]:
    for path in ["schedulelist", "channellist", "channels"]:
        st, body = get(f"https://api.lgchannels.com/api/v1.0/{path}", hdr)
        p("lg", {"path": path, "hdr": list(hdr.keys()), "st": st, "head": body[:250].decode("utf-8", "replace")})
