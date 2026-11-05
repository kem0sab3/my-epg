import json, urllib.request, urllib.error
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:600], flush=True)
G = "https://media-ssl.musicradio.com/"
cands = {
 "Capital": [G+"CapitalUKMP3", G+"CapitalMP3", G+"CapitalUK"],
 "Capital XTRA": [G+"CapitalXTRANationalMP3", G+"CapitalXTRALondonMP3", G+"CapitalXTRANational"],
 "Heart": [G+"HeartUKMP3", G+"HeartUK", G+"HeartLondonMP3"],
 "Heart 80s": [G+"Heart80sMP3"], "Heart 90s": [G+"Heart90sMP3"], "Heart Dance": [G+"HeartDanceMP3"],
 "Smooth": [G+"SmoothUKMP3", G+"SmoothUK", G+"SmoothLondonMP3"],
 "Classic FM": [G+"ClassicFMMP3", G+"ClassicFM"],
 "Gold": [G+"GoldMP3"], "LBC": [G+"LBCUKMP3", G+"LBCUK"], "LBC News": [G+"LBCNewsUKMP3", G+"LBCNewsUK"],
 "Radio X": [G+"RadioXUKMP3", G+"RadioXUK"],
 "talkSPORT": ["https://radio.talksport.com/stream"], "Virgin Radio": ["https://radio.virginradio.co.uk/stream"],
 "BFBS": ["https://listen-ssvcbfbs.sharp-stream.com/ssvcbfbs1.aac"], "Premier": ["https://pcr.streamguys1.com/pcrnational-96k.aac"],
 "Clyde 1": ["https://stream.apollo.audio/cl1/hi/aac/?direct=true"], "Forth 1": ["https://stream-al.hellorayo.co.uk/forth1.aac?direct=true"],
 "Northsound 1": ["https://stream-mz.hellorayo.co.uk/northsound1.aac?direct=true"], "Tay FM": ["https://stream-mz.hellorayo.co.uk/tayfm.aac?direct=true"],
 "MFR": ["https://stream-mz.hellorayo.co.uk/mfrfm.aac?direct=true"], "GHR": ["https://stream.apollo.audio/gh0/hi/aac/?direct=true"],
 "Hits Radio": ["https://stream.apollo.audio/hit/hi/aac/?direct=true"], "Absolute": ["https://stream-ar.hellorayo.co.uk/absoluteradiohigh.aac?direct=true"],
 "Absolute 80s": ["https://stream-ar.hellorayo.co.uk/absolute80shigh.aac?direct=true"], "Absolute 90s": ["https://stream-ar.hellorayo.co.uk/absolute90shigh.aac?direct=true"],
 "KISS": ["https://live-bauerkiss.sharp-stream.com/kissnational.aac?direct=true"], "KISSTORY": ["https://live-bauerkiss.sharp-stream.com/kisstory.aac?direct=true"],
 "Magic": ["https://stream.apollo.audio/mag/hi/aac/?direct=true"], "Jazz FM": ["https://stream-al.hellorayo.co.uk/jazzhigh.aac?direct=true"],
 "Kerrang": ["https://stream-al.hellorayo.co.uk/kerrang.aac?direct=true"], "Planet Rock": ["https://stream-mz.hellorayo.co.uk/planetrock.aac?direct=true"],
}
for name, urls in cands.items():
    for u in urls:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Icy-MetaData": "0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read(4096)
                p("s", {"name": name, "u": u, "status": r.status, "final": r.geturl(), "ct": r.headers.get("Content-Type"), "bytes": len(data)})
        except urllib.error.HTTPError as e:
            p("s", {"name": name, "u": u, "status": e.code})
        except Exception as e:
            p("s", {"name": name, "u": u, "err": str(e)[:120]})
