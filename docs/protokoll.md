# Tesvor X500 UART-Protokoll

## Frame-Grundstruktur

Viele Befehle folgen diesem Muster:

```text
AA LEN CMD GROUP VALUE CHECKSUM
```

Die bekannten Steuerkommandos haben `LEN = 03`.

## Reinigungskommandos

| Funktion | Frame | Stand |
|---|---|---|
| Edge Cleaning | `AA 03 02 22 00 24` | bestätigt |
| Spot Cleaning | `AA 03 02 22 01 25` | bestätigt |
| Smart Cleaning | `AA 03 02 22 02 26` | bestätigt |
| Go Charge | `AA 03 02 22 03 27` | bestätigt |
| Zickzack / Wischen | `AA 03 02 22 04 28` | bestätigt, Status `0x0B` |
| Mop Cleaning Test | `AA 03 02 22 05 29` | ACK, aber nicht als zuverlässiger Startmodus bestätigt |

## Stop

| Funktion | Frame |
|---|---|
| Stop | `AA 03 02 26 00 28` |

## Richtungsbefehle

Die Richtungsbefehle senden erst die Richtung und anschließend Stop/Neutral:

| Funktion | Frame |
|---|---|
| Vorwärts | `AA 03 02 21 00 23` + `AA 03 02 21 04 27` |
| Links | `AA 03 02 21 01 24` + `AA 03 02 21 04 27` |
| Rechts | `AA 03 02 21 02 25` + `AA 03 02 21 04 27` |
| Rückwärts | `AA 03 02 21 03 26` + `AA 03 02 21 04 27` |

## Wischintensität

| Option | Frame | Stand |
|---|---|---|
| Low | `AA 03 02 24 00 26` | ACK bestätigt |
| Default | `AA 03 02 24 01 27` | Muster plausibel |
| High | `AA 03 02 24 02 28` | ACK bestätigt |
| Off | `AA 03 02 24 03 29` | Muster plausibel |

## Saugstärke / Fan

Die Original-Firmware enthält Fan-Kommandos. Die Befehle werden per UART mit ACK quittiert; eine zuverlässige Rückmeldung über den normalen Statusframe wurde bisher nicht bestätigt.

| Option | Frame | Stand |
|---|---|---|
| Normal | `AA 03 02 25 01 28` | ACK |
| Strong | `AA 03 02 25 02 29` | ACK |
| Pause | `AA 03 02 25 03 2A` | ACK |
| Quiet | `AA 03 02 25 04 2B` | ACK |

## Statusframes

Statusframes:

```text
AA 1C 06 ...
```

Checksumme: additive Summe über Payload-Bytes `bytes[2..29]`.

| Statusbyte | Bedeutung |
|---|---|
| `0x00` | edge cleaning |
| `0x01` | spot cleaning |
| `0x02` | cleaning |
| `0x03` | returning |
| `0x04` | idle |
| `0x05` | hibernated |
| `0x06` | charging |
| `0x08` | docked |
| `0x09` | error |
| `0x0A` | setting |
| `0x0B` | zmode cleaning |

## Mapframes

Mapframes beginnen mit:

```text
AA LL 03 01 40 00 00 NN
```

Danach folgen `NN` Punkte à 8 Byte:

```text
seq_hi seq_lo x_hi x_lo y_hi y_lo type reserved
```

Der ESP veröffentlicht daraus MQTT-Batches:

```json
{"p":[[seq,x,y,type]]}
```

---

# Eigene Befunde (Oktober 2026, ESP32-S3 an einem X500 Pro)

Mitschnitte über den Logger (Level DEBUG, Rohbytes `>>>`/`<<<` auch auf MQTT `tesvor/x500/debug`).

## Statusrahmen `AA 1C 06 …`

Kommt alle ~6 s, 31 Bytes, Prüfsumme = Summe der Bytes 2–29. Zustandsbyte an Index 6:

| Wert | Bedeutung | Firmware-Zustand |
|---|---|---|
| 0x00 | Kantenreinigung | cleaning |
| 0x01 | Spot-Reinigung | cleaning |
| 0x02 | Smart-Reinigung | cleaning |
| 0x03 | Rückfahrt zur Station | returning |
| 0x04 | Bereit / gestoppt | idle |
| 0x05 | Ruhezustand | idle |
| 0x06 | Lädt | docked |
| **0x07** | Station, Ladepause (wechselt mit 0x08; eigener Fund) | docked |
| 0x08 | In der Station, voll | docked |
| 0x09 | Störung, Fehlerbyte an Index 28 | error |
| 0x0A | Handsteuerung / Fernbedienung (laut Tasmota-Diskussion) | idle („setting") |
| 0x0B | Zickzack / Wischen | cleaning |

Akkustand an Index 29 (0x64 = 100 %), bei mir auch auf der Station gültig.

## Quittungen und Ereignisse

- Jeder Befehl `AA 03 02 …` wird mit `AA 01 02 02` quittiert. Bleibt die Quittung aus, obwohl
  Statusrahmen ankommen, ist die Sendeleitung (ESP TX → Roboter RX) unterbrochen.
- Auf der Ladestation (0x06) ignoriert der Roboter Startbefehle ohne Quittung. Ein Stopp
  (`AA 03 02 26 00 28`) vorab weckt ihn, danach wird der Start angenommen. Das Skript
  `homeassistant/scripts/tesvor_starten.yaml` macht genau das.
- Ereignistelegramm `AA 03 07 01 01 09` taucht gelegentlich auf (vermutlich Ladeereignis) und
  wird vom Parser überlesen. Mini-Rahmen `AA 02 03 05 08` markiert den Beginn einer Karten-Sitzung.

## Kartenrahmen `AA LL 03 01 40 00 00 NN`

NN Punkte à 8 Byte (seq_hi, seq_lo, x_hi, x_lo, y_hi, y_lo, Typ, reserviert). Die Firmware
sendet sie gebündelt als `{"p":[[seq,x,y,typ],…]}` auf `tesvor/x500/map/points`; der Writer
baut daraus die Karte.

## Abgleich mit der Tasmota-Diskussion (arendst/Tasmota #19554, „Dealdig Robot Vacuum 8")

Gleiche Plattform: Richtungen `AA 03 02 21 0x` + Neutral `… 21 04 27`, Modi `AA 03 02 22 0x`,
Stop `AA 03 02 26 00 28` sind byteidentisch. Unterschiede im Statusrahmen: dort Bytes 3/4
`FF 00`, hier `00 01`; die Zustände 0x07/0x08 (voll auf der Station) fehlen dort.

## Noch offen

Opcodes 0x10, 0x28, 0x32, 0x33, 0x41, 0x43, 0x45 aus den upstream „PROTOCOL_LEADS" sind nicht
zugeordnet (Vermutung: Sprache an/aus, DND, Teppich-Boost, Suchen). Nur auf der Werkbank testen.

## Saugstärke – Test 27.10.2026

Alle Fan-Befehle (`AA 03 02 25 0x`) werden sowohl auf der Station als auch während einer laufenden
Smart-Reinigung innerhalb von ~130 ms mit `AA 01 02 02` quittiert. 26 Statusrahmen aus den Phasen
Station/Leise/Normal/Stark/Reinigung/Rückfahrt sind bis auf Zustands-, Fehler- und Akkubyte
byteidentisch: **die Stufe wird nicht zurückgemeldet.** Ob der Motor sie umsetzt, ist nur hörbar
prüfbar. Richtungsbefehle: Der Roboter fährt, bis Neutral kommt; deshalb seit v1.1.1 die einstellbare
Wartezeit zwischen Richtung und Neutral.
