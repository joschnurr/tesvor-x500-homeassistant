# Werkzeuge

Alles reine Python-3-Standardbibliothek, läuft ohne Zusatzmodule. Adressen über
Umgebungsvariablen: `ESPHOME_HOST`/`ESPHOME_PORT` (Dashboard, Standard 127.0.0.1:6052),
`MQTT_HOST`/`MQTT_PORT` (Broker, Standard 127.0.0.1:1883).

| Datei | Zweck |
|---|---|
| `esphome_ws.py` | Roh-WebSocket-Client für den ESPHome Device Builder. Aufruf: `python3 esphome_ws.py <befehl> '<json-args>'`, z. B. `devices/get_config '{"configuration":"tesvor-x500-esp32s3.yaml"}'`. Befehle: `devices/update_config {configuration, content}`, `editor/validate_yaml {configuration, content}`, `firmware/compile {configuration}`, `firmware/install {configuration, port: "OTA"}`, `firmware/get_jobs`, `firmware/get_job {job_id}`, `firmware/get_binaries {configuration}`, `firmware/download_token {configuration, file}` → `GET /api/firmware/download?token=…`. |
| `jobs_watch.py` | Pollt `firmware/get_jobs` und meldet Statuswechsel von Compile- und Upload-Jobs. |
| `build_folgen.py` | Verfolgt einen Compile-Job (`JOB`-Umgebungsvariable) und lädt danach die Factory-/OTA-Binärdateien nach `OUT` (Standard `tools/firmware/`, in `.gitignore`). |
| `mqtt_rohlog.py` | Lauscht auf `tesvor/x500/#` und zeigt empfangene UART-Rahmen (`<<<`) und Statuswechsel. Braucht Logger-Level DEBUG, zur Laufzeit per `select.tesvor_x500_pro_logger_level` umschaltbar. |
