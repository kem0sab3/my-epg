#!/usr/bin/env python3
"""Keeps the Bauer radio links (Clyde 1, Forth 1, KISS, Magic, Absolute, Greatest Hits Radio...) working.
Bauer's streams only play when the link carries a session number close to the current time (it expires after
roughly 6-10 hours), so this rewrites it to "now + 3 hours" in playlist.m3u. GitHub runs it every 2 hours."""
import os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))

def refresh(path=os.path.join(HERE, "playlist.m3u"), ahead=3 * 3600):
    if not os.path.exists(path):
        return False
    with open(path, encoding="utf-8") as f:
        text = f.read()
    new = re.sub(r"(aw_0_1st\.skey=)\d+", lambda m: m.group(1) + str(int(time.time()) + ahead), text)
    if new != text:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new)
        print(f"Bauer radio links refreshed ({len(re.findall(r'aw_0_1st\\.skey=', new))} links)")
        return True
    return False

if __name__ == "__main__":
    refresh()
