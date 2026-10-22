#!/usr/bin/env python3
"""MQTT map writer for the Tesvor X500 ESPHome project — Fassung für ein oder mehrere Roboter.

Grundlage: hannes813/tesvor-x500-pro-esphome-vacuum (MIT). Die ESPHome-Firmware veröffentlicht je
Roboter unter einem eigenen Topic-Präfix (Substitution topic_prefix, z. B. tesvor/x500, tesvor/x500-2):
  <präfix>/map/points   Punktpakete {"p":[[seq,x,y,typ],…]}
  <präfix>/state        Zustand (cleaning, docked, charging, …)

Der Writer abonniert <TESVOR_TOPIC_ROOT>/+/map/points und <TESVOR_TOPIC_ROOT>/+/state, erkennt das
Gerät am zweiten Topic-Segment und führt je Gerät einen eigenen Ordner:
  <TESVOR_MAP_DIR>/<gerät>/current.json         laufende Fahrt
  <TESVOR_MAP_DIR>/<gerät>/archive/*.json       archivierte Fahrten
  <TESVOR_MAP_DIR>/<gerät>/archive_index.json   Index mit Startzeit und Punktzahl
  <TESVOR_MAP_DIR>/devices.json                 Liste aller gesehenen Geräte (für die Geräteauswahl)
Ältere Einzelgerät-Daten direkt in <TESVOR_MAP_DIR> werden beim Start nach <TESVOR_DEFAULT_DEVICE>/
verschoben. Anzeigenamen: TESVOR_DEVICE_NAMES="x500=Erdgeschoss,x500-2=Keller".
"""

import json
import os
import re
import shutil
from pathlib import Path
from datetime import datetime

import paho.mqtt.client as mqtt


MQTT_HOST = os.getenv("TESVOR_MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.getenv("TESVOR_MQTT_PORT", "1883"))
MQTT_USER = os.getenv("TESVOR_MQTT_USER", "")
MQTT_PASSWORD = os.getenv("TESVOR_MQTT_PASSWORD", "")

BASE_DIR = Path(os.getenv("TESVOR_MAP_DIR", "/data"))
TOPIC_ROOT = os.getenv("TESVOR_TOPIC_ROOT", "tesvor").strip("/")
DEFAULT_DEVICE = os.getenv("TESVOR_DEFAULT_DEVICE", "x500")
DEVICES_FILE = BASE_DIR / "devices.json"

MIN_POINTS_TO_ARCHIVE = int(os.getenv("TESVOR_MIN_POINTS_TO_ARCHIVE", "5"))
# höchstens so viele Archivrouten je Gerät behalten, ältere löschen (0 = unbegrenzt)
ARCHIVE_KEEP = int(os.getenv("TESVOR_ARCHIVE_KEEP", "30"))

DEVICE_NAMES = {}
for teil in os.getenv("TESVOR_DEVICE_NAMES", "").split(","):
    if "=" in teil:
        k, v = teil.split("=", 1)
        DEVICE_NAMES[k.strip()] = v.strip()

CLEANING_STATES = ("cleaning", "spot_cleaning", "edge_cleaning", "zmode_cleaning")
DOCKED_STATES = ("charging", "docked")
DEVICE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,40}$")

BASE_DIR.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def save_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(path)


class Device:
    """Zustand und Dateien eines Roboters."""

    def __init__(self, device_id: str):
        self.id = device_id
        self.name = DEVICE_NAMES.get(device_id, device_id)
        self.dir = BASE_DIR / device_id
        self.current_file = self.dir / "current.json"
        self.archive_dir = self.dir / "archive"
        self.index_file = self.dir / "archive_index.json"
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.points_by_seq = {}
        self.session_started = None
        self.last_state = None
        self.last_seen = None
        self.archived_this_session = False
        self.write_archive_index()

    # --- laufende Fahrt ---------------------------------------------------------------
    def current_payload(self) -> dict:
        ordered = [self.points_by_seq[k] for k in sorted(self.points_by_seq.keys())]
        return {
            "device": self.id,
            "name": self.name,
            "updated": now_iso(),
            "started": self.session_started,
            "point_count": len(ordered),
            "points": ordered,
        }

    def save_current(self) -> None:
        save_json_atomic(self.current_file, self.current_payload())

    def reset_session(self) -> None:
        self.points_by_seq = {}
        self.session_started = now_iso()
        self.archived_this_session = False
        self.save_current()
        print(f"[{self.id}] [SESSION] reset", flush=True)

    # --- Archiv -----------------------------------------------------------------------
    def archive_index_payload(self) -> dict:
        files = []
        for f in sorted(self.archive_dir.glob("*.json"), reverse=True):
            try:
                stat = f.stat()
                eintrag = {
                    "name": f.name,
                    "path": f"archive/{f.name}",
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                }
                try:  # Startzeit und Punktzahl für die Beschriftung "Route Montag 22.10. 15:00 (748 Punkte)"
                    inhalt = json.loads(f.read_text(encoding="utf-8"))
                    eintrag["started"] = inhalt.get("started")
                    eintrag["point_count"] = inhalt.get("point_count", len(inhalt.get("points", [])))
                except (OSError, ValueError):
                    pass
                files.append(eintrag)
            except OSError:
                pass
        return {"device": self.id, "name": self.name, "updated": now_iso(), "files": files}

    def prune_archive(self) -> None:
        if ARCHIVE_KEEP <= 0:
            return
        # Dateinamen tragen den Zeitstempel (tesvor_map_YYYY-MM-DD_HH-MM-SS_*.json) -> Namenssortierung = Alter
        for f in sorted(self.archive_dir.glob("*.json"), reverse=True)[ARCHIVE_KEEP:]:
            try:
                f.unlink()
                print(f"[{self.id}] [PRUNE] {f.name}", flush=True)
            except OSError as e:
                print(f"[{self.id}] [PRUNE] {f.name}: {e}", flush=True)

    def write_archive_index(self) -> None:
        self.prune_archive()
        save_json_atomic(self.index_file, self.archive_index_payload())

    def archive_current(self, reason: str) -> None:
        if self.archived_this_session or not self.current_file.exists():
            return
        if len(self.points_by_seq) < MIN_POINTS_TO_ARCHIVE:
            return
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        archive_file = self.archive_dir / f"tesvor_map_{ts}_{reason}.json"
        shutil.copy2(self.current_file, archive_file)
        self.archived_this_session = True
        self.write_archive_index()
        print(f"[{self.id}] [ARCHIVE] {archive_file.name}", flush=True)

    # --- Nachrichten ------------------------------------------------------------------
    def on_state(self, state: str) -> None:
        self.last_seen = now_iso()
        if state != self.last_state:
            print(f"[{self.id}] [STATE] {state}", flush=True)
            self.last_state = state
        if state in CLEANING_STATES and (self.session_started is None or self.archived_this_session):
            self.reset_session()
        if state in DOCKED_STATES:
            self.archive_current(state)
        if self.session_started is not None:
            self.save_current()

    def on_points(self, text: str) -> None:
        self.last_seen = now_iso()
        if self.session_started is None:
            self.reset_session()
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            print(f"[{self.id}] [WARN] invalid json: {e}: {text}", flush=True)
            return
        added = 0
        for p in data.get("p", []):
            if not isinstance(p, list) or len(p) != 4:
                continue
            seq, x, y, kind = p
            seq = int(seq)
            if seq not in self.points_by_seq:
                self.points_by_seq[seq] = {"seq": seq, "x": int(x), "y": int(y), "type": int(kind)}
                added += 1
        if added:
            print(f"[{self.id}] [POINTS] +{added}, total={len(self.points_by_seq)}", flush=True)
            self.save_current()


devices: dict[str, Device] = {}


def write_devices_file() -> None:
    save_json_atomic(DEVICES_FILE, {
        "updated": now_iso(),
        "devices": [
            {"id": d.id, "name": d.name, "state": d.last_state, "last_seen": d.last_seen,
             "current": f"{d.id}/current.json", "index": f"{d.id}/archive_index.json"}
            for d in sorted(devices.values(), key=lambda d: d.id)
        ],
    })


def get_device(device_id: str) -> Device:
    if device_id not in devices:
        devices[device_id] = Device(device_id)
        print(f"[{device_id}] neues Gerät", flush=True)
        write_devices_file()
    return devices[device_id]


def migrate_legacy_layout() -> None:
    """Einzelgerät-Dateien direkt in BASE_DIR (Stand bis v1.0.x) in den Geräteordner verschieben."""
    alt_current = BASE_DIR / "current.json"
    alt_archive = BASE_DIR / "archive"
    if not alt_current.exists() and not alt_archive.exists():
        return
    ziel = BASE_DIR / DEFAULT_DEVICE
    ziel.mkdir(parents=True, exist_ok=True)
    if alt_current.exists():
        shutil.move(str(alt_current), str(ziel / "current.json"))
    if alt_archive.exists():
        (ziel / "archive").mkdir(exist_ok=True)
        for f in alt_archive.glob("*.json"):
            shutil.move(str(f), str(ziel / "archive" / f.name))
        try:
            alt_archive.rmdir()
        except OSError:
            pass
    alt_index = BASE_DIR / "archive_index.json"
    if alt_index.exists():
        alt_index.unlink()
    print(f"[MIGRATION] alte Dateien nach {ziel} verschoben", flush=True)


def discover_existing_devices() -> None:
    """Geräteordner, die schon auf der Platte liegen, sofort in devices.json aufnehmen."""
    for d in sorted(BASE_DIR.iterdir()):
        if d.is_dir() and (d / "archive").is_dir() and DEVICE_ID_RE.match(d.name):
            get_device(d.name)


def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] connected rc={rc}", flush=True)
    client.subscribe(f"{TOPIC_ROOT}/+/map/points")
    client.subscribe(f"{TOPIC_ROOT}/+/state")


def on_message(client, userdata, msg):
    teile = msg.topic.split("/")
    # <root>/<gerät>/state  bzw.  <root>/<gerät>/map/points  (root darf selbst "/" enthalten)
    root_len = len(TOPIC_ROOT.split("/"))
    if len(teile) < root_len + 2 or "/".join(teile[:root_len]) != TOPIC_ROOT:
        return
    device_id = teile[root_len]
    rest = "/".join(teile[root_len + 1:])
    if not DEVICE_ID_RE.match(device_id):
        return
    text = msg.payload.decode("utf-8", errors="replace").strip()
    dev = get_device(device_id)
    if rest == "state":
        dev.on_state(text)
        write_devices_file()
    elif rest == "map/points":
        dev.on_points(text)


def main() -> None:
    migrate_legacy_layout()
    discover_existing_devices()
    write_devices_file()

    client = mqtt.Client()
    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()
