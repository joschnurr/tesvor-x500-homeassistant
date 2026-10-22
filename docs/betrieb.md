# Betrieb, Fallen, Diagnose

## Entitäten

Nach dem Anlegen des ESPHome-Geräts (Name `tesvor-x500`, friendly name „Tesvor X500 Pro")
liefert die Firmware: Textsensoren `state`, `vacuum state`, `error state`, `map path json`;
Sensoren `battery`, `Reinigungsdauer`, `Status Byte 7 Rohwert`; Auswahl `Wischintensität`
(Niedrig/Standard/Hoch/Aus), `Saugstärke Test experimentell` (Normal/Stark/Pause/Leise),
`Logger Level`; Tasten Smart/Spot/Edge Cleaning, Stop, Go Charge, Move Front/Back/Left/Right,
Zickzack Wischen, Mop Cleaning Test, Map Reset.

Die Entitätsnamen in der Firmware sind bewusst englisch geblieben: ESPHome leitet die
`unique_id` vom Namen ab, ein Umbenennen in der YAML erzeugt neue Entitäten und verwaist die
alten. Deutsche Namen vergibt man in Home Assistant in der Entitäten-Registry oder nutzt die
Klartext-Sensoren aus `homeassistant/templates/tesvor.yaml`.

## Start klappt nicht

Lädt der Roboter auf der Station (Zustand `charging`), nimmt er Startbefehle nicht an und
quittiert sie auch nicht. Lösung: erst Stopp, 3 s warten, dann Start. Das Skript
`tesvor_starten` und die Template-`vacuum` machen das automatisch.

## Befehle kommen gar nicht an

Diagnose-Muster: Stopp senden. Kommt im Rohlog kein `<<< AA 01 02 02`, obwohl Statusrahmen
`<<< AA 1C 06 …` weiter eintreffen, ist die Sendeleitung unterbrochen (bei mir ein Dupont-Stecker
an GPIO17 nach Fahrten mit Anstoßen). Kommen gar keine Rahmen, ist es die Empfangsleitung oder
die Versorgung. Nach dem Nachstecken sofort wieder quittiert.

## Rohlog einschalten

Die Firmware ist bis DEBUG kompiliert, startet aber auf INFO. Zur Laufzeit über
`select.tesvor_x500_pro_logger_level` auf DEBUG stellen: Dann erscheinen `>>>` (gesendet) und
`<<<` (empfangen) im Dashboard-Log und auf MQTT `tesvor/x500/debug`. Nach einem Neustart gilt
wieder INFO. `tools/mqtt_rohlog.py` filtert das MQTT-Debug-Thema auf Rahmen und Statuswechsel.

Die Stufe von `uart_debug` darf nicht feiner sein als das globale Level, sonst ist das Log leer.

## MQTT direkt

Tasten: `tesvor/x500/button/<objekt_id>/command` mit Payload `PRESS` (smart_cleaning,
spot_cleaning, edge_cleaning, stop, go_charge, move_front/back/left/right, zickzack_wischen,
map_reset). Auswahl: `tesvor/x500/select/wischintensit__t/command` (Niedrig/Standard/Hoch/Aus),
`tesvor/x500/select/saugst__rke_test_experimentell/command` (Normal/Stark/Pause/Leise).
Status: `tesvor/x500/state`, Verfügbarkeit: `tesvor/x500/status` (online/offline).

## Karte

Der Writer legt `current.json` für die laufende Fahrt an und archiviert sie, sobald der Roboter
wieder `charging`/`docked` meldet (mindestens 5 Punkte). `TESVOR_ARCHIVE_KEEP` begrenzt die
Zahl der Archive (Standard 30). Die Kartenseite liest beide relativ, deshalb muss `map.html`
im selben Ordner liegen wie die JSON-Dateien. Vor der ersten Fahrt zeigt sie „0 Punkte"; wer
die Fehlermeldung vermeiden will, legt eine leere `current.json` an:
`{"device":"tesvor_x500","updated":"","started":null,"point_count":0,"points":[]}`.

## ESPHome-Dashboard ohne Browser

Der Device-Builder hat eine WebSocket-Schnittstelle (`ws://<host>:6052/ws`). Nachrichten sind
`{command, message_id, args}`, `message_id` muss ein String sein. Nützliche Befehle:
`devices/get_config`, `devices/update_config {configuration, content}`, `editor/validate_yaml`,
`firmware/compile`, `firmware/install {configuration, port: "OTA"}`, `firmware/get_jobs`,
`firmware/get_job {job_id}`, `firmware/get_binaries`, `firmware/download_token` →
`GET /api/firmware/download?token=…`. Klicks im Browser-Dashboard brechen laufende Jobs ab.
Siehe `tools/`.

## Zurück zur Cloud

Beim Originalmodul das 4-MB-Backup mit `esptool write-flash 0x0` zurückspielen und die
WeBack-App neu koppeln. Beim ESP32-Umbau das Originalmodul wieder einstecken.
