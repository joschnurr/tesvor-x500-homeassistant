# Backup und Flashen

## 1. Originalfirmware sichern (nur Weg A, Originalmodul)

Bevor das ESP-12S überschrieben wird, die kompletten 4 MB sichern. Damit kommt die
WeBack-Firmware jederzeit zurück. Auf einem PC mit Python:

```
python -m pip install esptool
python -m esptool --port COM8 --baud 115200 read-flash 0x00000 0x400000 tesvor_x500_original_4mb.bin
```

GPIO0 muss beim Einstecken auf GND liegen (siehe [hardware.md](hardware.md)). Findet esptool
nichts: `python -m esptool --port COM8 chip-id` muss „ESP8266EX" melden, sonst RX/TX tauschen
oder GPIO0 war nicht auf GND. Die Datei an zwei Orten aufheben.

Rückweg: `python -m esptool --port COM8 write-flash 0x0 tesvor_x500_original_4mb.bin`.

## 2. ESPHome vorbereiten

Im ESPHome-Dashboard ein neues Gerät anlegen und die passende Datei aus `esphome/` als
Konfiguration übernehmen. `secrets.yaml` nach `esphome/secrets.yaml.example` ausfüllen, den
API-Schlüssel mit `openssl rand -base64 32` erzeugen. Derselbe Schlüssel sichert die
OTA-Updates (`ota: encryption`), ein OTA-Passwort ist nicht nötig.

Dann „Validate" und „Install". Der erste ESP-IDF-Build für ESP32-S3 dauert auf einem kleinen
Server bis zu 30 Minuten, spätere Builds sind schneller.

## 3. Erstes Flashen

**Originalmodul (Weg A):** Im Dashboard „Manual download", Legacy-Format wählen, dann

```
python -m esptool --port COM8 --baud 460800 write-flash --flash-size 4MB 0x0 tesvor-x500-esp8266.bin
```

(oder NodeMCU-PyFlasher, Adresse 0x0, Erase an). GPIO0 wieder auf GND beim Einstecken, danach
Brücke entfernen.

**ESP32 / ESP32-S3 (Weg B/C):** Board per USB an den PC, im Dashboard „Install → Plug into this
computer" oder ESPHome Web, oder die Factory-Datei mit esptool an 0x0. Beim S3 BOOT halten und
RESET tippen, falls der Bootloader nicht automatisch anspringt. Die rote 3,3-V-Leitung vom
Roboter ist dabei abgeklemmt.

Danach Modul oder Board in den Roboter, Akku anstecken, Roboter einschalten. Der ESP meldet sich
im 2,4-GHz-WLAN; findet er es nicht, öffnet er den Hotspot „Tesvor X500 Fallback".

## 4. Ab jetzt drahtlos

Alle weiteren Updates laufen über das ESPHome-Dashboard („Install → Wirelessly"). Wer das
Dashboard skripten will: `tools/esphome_ws.py` spricht die WebSocket-Schnittstelle des
Device-Builders an (kompilieren, installieren, Binärdateien holen), siehe `tools/README.md`.

## Firmware-Dateien

Kompilierte `.bin`-Dateien enthalten WLAN-Zugangsdaten und den API-Schlüssel. Sie gehören
weder ins Repository noch in einen öffentlichen Ordner, deshalb stehen `*.bin` und `firmware/`
in `.gitignore`.
