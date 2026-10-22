# Änderungen

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
