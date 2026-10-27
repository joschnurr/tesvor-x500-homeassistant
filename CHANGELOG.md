# Änderungen

## v1.1.1 – 2026-10-27

- Richtungstasten: Richtung senden, einstellbare Zeit warten („Richtungsschritt", 0,3–5 s, Standard 1,5 s,
  neue Number-Entität), dann Neutral. Vorher kamen Richtung und Neutral in einem Paket, der Roboter
  ruckte nur kurz an.
- Protokoll: Saugstärke-Befehle werden im Stand und in Fahrt quittiert, der Statusrahmen enthält aber
  kein Byte für die Stufe — Rückmeldung bleibt unmöglich (Test 27.10.2026, docs/protokoll.md).

## v1.1.0 – 2026-10-22

Mehrgeräte-Fähigkeit und Beschriftung „Route".

- Firmware: `substitutions` für `name`, `friendly_name` und `topic_prefix`; die MQTT-Themen im
  Parser folgen dem Präfix. Je Roboter genügt eine Kopie mit drei geänderten Zeilen.
- Karten-Writer: bedient beliebig viele Roboter (`<TOPIC_ROOT>/+/…`), je Gerät ein Ordner mit
  `current.json`, `archive/` und Index, dazu `devices.json`; alte Einzelgerät-Daten werden beim
  Start automatisch nach `<DEFAULT_DEVICE>/` verschoben. Neue Variablen `TOPIC_ROOT`,
  `DEFAULT_DEVICE`, `DEVICE_NAMES`.
- Kartenseite: Geräteauswahl (nur sichtbar bei mehreren Geräten, `?device=` wählt vor),
  Beschriftung „Route Donnerstag 22.10. 19:59 (138 Punkte)" und „Aktuelle Route".
- Start-Skript: geräteunabhängig, das Gerät wird aus der Taste abgeleitet.

## v1.0.2 – 2026-10-22

- Kartenseite: Archivkarten heißen jetzt „Karte Montag 22.10. 15:00 (748 Punkte)" statt Dateiname.
- Writer: Index enthält Startzeit und Punktzahl je Archiv (Grundlage für die Beschriftung).
- Dashboard: Kantenreinigung mit Rahmen-Symbol (mdi:border-outside), „Orten"-Umleitung entfernt.

## v1.0.1 – 2026-10-22

Kartenseite (`docker/tesvor-map/app/map.html`):

- Statuszeile „Letzter Punkt" liegt nicht mehr über dem Canvas, sondern als normales Element unter der Karte.
- Vor dem Zeichnen wird die Bounding Box aller Punkte berechnet; einheitlicher Maßstab, ~5 % Rand, mittig.
- Canvas-Höhe folgt dem Container (ResizeObserver) statt fester Pixel- oder vh-Höhe; passt sich dem iframe an.
- Linien nur noch zwischen aufeinanderfolgenden Punkten gleichen Typs, keine Verbindung über Segmentgrenzen.

## v1.0.0 – 2026-10-22

Erste Veröffentlichung, Stand des laufenden Umbaus.

- Firmware: drei Varianten (ESP-12S-Originalmodul, NodeMCU-ESP32, ESP32-S3) mit gemeinsamem
  Parser. Gegenüber upstream: Zustand 0x07 (Station, Ladepause) als „docked", Akkuwert auch auf
  der Station, Optionen auf Deutsch, Logger-Level zur Laufzeit umschaltbar, Kartenpuffer 400 Punkte
  auf ESP32, OTA über den API-Schlüssel.
- Karten-Writer als Docker-Compose-Stack mit `.env`, Archiv auf 30 Fahrten begrenzt.
- Home Assistant: Template-`vacuum`, deutsche Klartext-Sensoren, Start-Skript (Stopp weckt den
  Roboter an der Station), Dashboard-Sektion mit vacuum-card und Routen-Karte.
- Doku: Hardware (ESP-12S-Pinbelegung mit Foto, ESP32-S3-Verdrahtung), Backup und Flashen,
  Protokoll inkl. eigener Befunde, Betrieb und Fallen.
