# Änderungen

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
