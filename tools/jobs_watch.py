import sys, json, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esphome_ws import WS
CFG="tesvor-x500-esp32s3.yaml"; last={}
t0=time.time()
while time.time()-t0<3000:
    try:
        ws=WS(); ws.recv(); jobs=ws.call("firmware/get_jobs")["result"] or []; ws.s.close()
    except Exception as e:
        print("Abfrage:", str(e)[:80], flush=True); time.sleep(20); continue
    mine=[j for j in jobs if j.get("configuration")==CFG and (j.get("created_at") or "")>="2026-10-20T20:25"]
    done=False
    for j in sorted(mine, key=lambda j:j.get("created_at") or ""):
        k=(j["job_id"], j.get("status"))
        if last.get(j["job_id"])!=j.get("status"):
            print(f"[{time.strftime('%H:%M:%S')}] {j['job_type']} {j['job_id']}: {j.get('status')} exit={j.get('exit_code')} err={j.get('error')}", flush=True)
            last[j["job_id"]]=j.get("status")
        if j["job_type"]=="upload" and j.get("status") in ("completed","failed","cancelled","error"): done=True
        if j["job_type"]=="compile" and j.get("status") in ("failed","cancelled","error"): done=True
    if done: break
    time.sleep(15)
