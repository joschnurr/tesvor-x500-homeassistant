import sys, json, time, urllib.request, urllib.parse, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esphome_ws import WS
CFG = os.getenv("CFG", "tesvor-x500-esp32s3.yaml"); JOB = os.getenv("JOB", "")   # JOB = Job-ID aus firmware/compile
OUT = os.getenv("OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "firmware"))
def call(cmd, **a):
    ws = WS(); ws.recv(); r = ws.call(cmd, **a)["result"]; ws.s.close(); return r
t0 = time.time(); last = None; nout = 0
while time.time() - t0 < 3300:
    try:
        j = call("firmware/get_job", job_id=JOB)
    except Exception as e:
        print("Abfrage fehlgeschlagen:", e, flush=True); time.sleep(20); continue
    st = j.get("status"); out = j.get("output") or []
    for line in out[nout:]:
        s = line if isinstance(line, str) else json.dumps(line)
        if any(k in s for k in ("error:", "Error", "RAM:", "Flash:", "Successfully", "Toolchain", "Installing", "failed", "FAILED")):
            print(s.rstrip()[:200], flush=True)
    nout = len(out)
    if st != last: print(f"[{time.strftime('%H:%M:%S')}] Status: {st} (Ausgabezeilen {nout}, Fortschritt {j.get('progress')})", flush=True); last = st
    if st in ("completed", "success", "failed", "error", "cancelled"):
        print("RESULT: exit_code", j.get("exit_code"), "error", j.get("error"), flush=True)
        if j.get("exit_code") not in (0, None) or st in ("failed", "error", "cancelled"): sys.exit(1)
        break
    time.sleep(20)
else:
    sys.exit("kein Ergebnis in 55 min")
bins = call("firmware/get_binaries", configuration=CFG)
print("Binaries:", json.dumps(bins)[:600], flush=True)
os.makedirs(OUT, exist_ok=True)
items = bins if isinstance(bins, list) else (bins.get("binaries") or bins.get("files") or [])
for b in items:
    fname = b.get("file") or b.get("filename") or b.get("name") if isinstance(b, dict) else b
    tok = call("firmware/download_token", configuration=CFG, file=fname)
    url = f"http://" + os.getenv("ESPHOME_HOST", "127.0.0.1") + ":6052/api/firmware/download?token={urllib.parse.quote(tok['token'])}"
    dest = os.path.join(OUT, tok.get("filename") or os.path.basename(fname))
    urllib.request.urlretrieve(url, dest)
    print("heruntergeladen:", dest, os.path.getsize(dest), "B", flush=True)
