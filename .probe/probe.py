import json, urllib.request, urllib.error, urllib.parse
U = {"Swerve Women's Sports": 'https://jmp2.uk/plex-64305451fc3be5947773c339-6a109508cd23e9639dc7e94a.m3u8', 'GUSTOTV': 'https://jmp2.uk/plex-64305451fc3be5947773c339-5f8746eabd529300418246d9.m3u8', "Today's K-Pop": 'https://jmp2.uk/plex-64305451fc3be5947773c339-62ee6eae271f393d2d9f7096.m3u8', 'Dr. G: Medical Examiner': 'https://jmp2.uk/plex-64305451fc3be5947773c339-6449369eb3ff17382cae5807.m3u8', 'Remember the ‘80s': 'https://jmp2.uk/plex-64305451fc3be5947773c339-61aa9f50784a2161d3caf7fb.m3u8', 'Stars Central': 'https://jmp2.uk/plex-64305451fc3be5947773c339-68645e804051ba2be659baac.m3u8', 'Nomad Travel': 'https://jmp2.uk/plex-64305451fc3be5947773c339-6aaa2279083227098739435f.m3u8', 'Little Women: LA': 'https://jmp2.uk/plex-64305451fc3be5947773c339-69aed745e657bab5f7a9b7f2.m3u8', 'Bon Voyage': 'https://jmp2.uk/plex-64305451fc3be5947773c339-666e10bece73ed6023b55a0d.m3u8', 'The World Poker Tour': 'https://jmp2.uk/plex-64305451fc3be5947773c339-656fa24bdbcce28c3a417415.m3u8', 'Pointless': 'https://jmp2.uk/plex-64305451fc3be5947773c339-671ab1dc79fce66281154344.m3u8', 'Man City 24/7': 'https://jmp2.uk/plex-64305451fc3be5947773c339-6aa9c4a3083227098739435b.m3u8', 'Dragons’ Den': 'https://jmp2.uk/plex-64305451fc3be5947773c339-6920db3650fe592fd6d5b7d5.m3u8', 'TNA Wrestling Channel': 'https://jmp2.uk/plex-64305451fc3be5947773c339-606605549dbfca002d2ae873.m3u8'}
for n, u in U.items():
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=25) as r:
            body = r.read(20000).decode("utf-8", "replace"); final = r.geturl()
        variants = [l for l in body.splitlines() if l and not l.startswith("#")]
        seg = None
        if variants:
            v = urllib.parse.urljoin(final, variants[0])
            with urllib.request.urlopen(urllib.request.Request(v, headers={"User-Agent": "Mozilla/5.0"}), timeout=25) as r2:
                vb = r2.read(20000).decode("utf-8", "replace")
            segs = [l for l in vb.splitlines() if l and not l.startswith("#")]
            seg = len(segs)
        print("P|s|" + json.dumps({"name": n, "ok": True, "variants": len(variants), "segments": seg}), flush=True)
    except urllib.error.HTTPError as e:
        print("P|s|" + json.dumps({"name": n, "st": e.code}), flush=True)
    except Exception as e:
        print("P|s|" + json.dumps({"name": n, "err": str(e)[:80]}), flush=True)
