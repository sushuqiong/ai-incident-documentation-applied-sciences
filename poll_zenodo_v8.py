import json, time, urllib.request, sys
API = "https://zenodo.org/api/records/22845069/versions?size=50&sort=mostrecent"
seen = {"22845069"}
for i in range(60):
    try:
        with urllib.request.urlopen(API, timeout=25) as r:
            d = json.load(r)
        for h in d.get("hits", {}).get("hits", []):
            rid = str(h.get("id"))
            if rid not in seen:
                m = h.get("metadata", {})
                print("NEW_VERSION recid=%s version=%s doi=%s created=%s"
                      % (rid, m.get("version"), m.get("doi"), h.get("created")), flush=True)
                seen.add(rid)
        if len(seen) > 1:
            print("DONE", flush=True)
            sys.exit(0)
    except Exception as e:
        print("poll error:", e, flush=True)
    time.sleep(20)
print("TIMEOUT no new version after 20 min", flush=True)
