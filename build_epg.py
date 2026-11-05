#!/usr/bin/env python3
"""Builds epg.xml.gz from the links in sources.txt.
Run by GitHub every day (see .github/workflows/update-epg.yml).
You shouldn't need to edit this file - change sources.txt / channels.txt / settings.txt instead."""
import datetime, gzip, os, shutil, sys, tempfile, urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))

def read_list(name):
    path = os.path.join(HERE, name)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]

def read_settings():
    s = {"name": "My EPG", "days_ahead": "7"}
    for line in read_list("settings.txt"):
        if "=" in line:
            k, v = line.split("=", 1)
            s[k.strip()] = v.strip()
    return s

def parse_time(t):
    t = (t or "").strip()
    try:
        if " " in t:
            d, tz = t.split(" ", 1)
            return datetime.datetime.strptime(d[:14] + tz.strip(), "%Y%m%d%H%M%S%z")
        return datetime.datetime.strptime(t[:14], "%Y%m%d%H%M%S").replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        return None

def fetch(src, tmpdir, i):
    """Download (or copy) a source and return a path to the plain XML."""
    raw = os.path.join(tmpdir, f"src{i}.raw")
    if os.path.exists(src):
        shutil.copy(src, raw)
    else:
        req = urllib.request.Request(src, headers={"User-Agent": "my-epg-builder/1.0"})
        with urllib.request.urlopen(req, timeout=300) as r, open(raw, "wb") as f:
            shutil.copyfileobj(r, f)
    with open(raw, "rb") as f:
        is_gz = f.read(2) == b"\x1f\x8b"
    if not is_gz:
        return raw
    plain = os.path.join(tmpdir, f"src{i}.xml")
    with gzip.open(raw, "rb") as g, open(plain, "wb") as f:
        shutil.copyfileobj(g, f)
    os.remove(raw)
    return plain

def update_playlist_header():
    """Point playlist.m3u's first line at this repo's own epg.xml.gz, so apps load the guide automatically."""
    repo, branch = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_REF_NAME") or "main"
    path = os.path.join(HERE, "playlist.m3u")
    if not repo or not os.path.exists(path):
        return
    link = f"https://raw.githubusercontent.com/{repo}/{branch}/epg.xml.gz"
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    header = f'#EXTM3U url-tvg="{link}" x-tvg-url="{link}"'
    if lines and lines[0].startswith("#EXTM3U"):
        lines[0] = header
    else:
        lines.insert(0, header)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"playlist.m3u now points to {link}")

def main():
    settings = read_settings()
    sources = read_list("sources.txt")
    wanted = set(read_list("channels.txt"))
    if not sources:
        sys.exit("sources.txt has no links in it.")
    now = datetime.datetime.now(datetime.timezone.utc)
    horizon = now + datetime.timedelta(days=float(settings.get("days_ahead", 7)))

    tmpdir = tempfile.mkdtemp()
    ch_out = open(os.path.join(tmpdir, "channels.part"), "w", encoding="utf-8")
    pr_out = open(os.path.join(tmpdir, "programmes.part"), "w", encoding="utf-8")
    channels_done = set()   # channel IDs already written
    owned = {}              # channel ID -> source number that supplies its listings
    total_prog = 0
    ok_sources = 0

    for i, src in enumerate(sources):
        print(f"[{i+1}/{len(sources)}] {src}", flush=True)
        try:
            path = fetch(src, tmpdir, i)
        except Exception as e:
            print(f"   !! could not download, skipping: {e}", flush=True)
            continue
        n_ch = n_pr = 0
        seen = set()
        try:
            for _, el in ET.iterparse(path, events=("end",)):
                if el.tag == "channel":
                    cid = el.get("id")
                    if cid and cid not in channels_done and (not wanted or cid in wanted):
                        names = set()
                        for dn in list(el.findall("display-name")):
                            key = (dn.text or "").strip()
                            if key in names:
                                el.remove(dn)
                            names.add(key)
                        el.tail = "\n"
                        ch_out.write(ET.tostring(el, encoding="unicode"))
                        channels_done.add(cid)
                        n_ch += 1
                    el.clear()
                elif el.tag == "programme":
                    cid = el.get("channel")
                    if (not wanted or cid in wanted) and owned.setdefault(cid, i) == i:
                        start, stop = parse_time(el.get("start")), parse_time(el.get("stop"))
                        key = (cid, el.get("start"))
                        if not (stop and stop < now) and not (start and start > horizon) and key not in seen:
                            seen.add(key)
                            el.tail = "\n"
                            pr_out.write(ET.tostring(el, encoding="unicode"))
                            n_pr += 1
                    el.clear()
            ok_sources += 1
        except ET.ParseError as e:
            print(f"   !! file is broken, kept what was read before the error: {e}", flush=True)
            ok_sources += 1
        os.remove(path)
        total_prog += n_pr
        print(f"   added {n_ch} channels, {n_pr} programmes", flush=True)

    ch_out.close(); pr_out.close()
    if ok_sources == 0 or total_prog == 0:
        sys.exit("Nothing could be downloaded - keeping the previous epg.xml.gz unchanged.")

    out_path = os.path.join(HERE, "epg.xml.gz")
    with gzip.open(out_path + ".tmp", "wt", encoding="utf-8", compresslevel=9) as out:
        name = settings["name"].replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
        out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        out.write(f'<tv generator-info-name="{name}">\n')
        for part in ("channels.part", "programmes.part"):
            with open(os.path.join(tmpdir, part), encoding="utf-8") as f:
                shutil.copyfileobj(f, out)
        out.write("</tv>\n")
    os.replace(out_path + ".tmp", out_path)
    shutil.rmtree(tmpdir, ignore_errors=True)
    update_playlist_header()
    mb = os.path.getsize(out_path) / 1e6
    print(f"Done: {len(channels_done)} channels, {total_prog} programmes, {mb:.1f} MB -> epg.xml.gz")

if __name__ == "__main__":
    main()
