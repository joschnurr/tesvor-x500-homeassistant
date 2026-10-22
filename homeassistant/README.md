# Home-Assistant-Teile

## Gerät anlegen

Einstellungen → Geräte & Dienste: Home Assistant findet den ESPHome-Knoten `tesvor-x500` per
mDNS. Beim Hinzufügen den API-Schlüssel aus der ESPHome-`secrets.yaml` eintragen. Ohne
Meldung: Integration ESPHome → Hinzufügen → Host `tesvor-x500.local`.

## Dateien

| Datei | Wohin | Zweck |
|---|---|---|
| `templates/tesvor.yaml` | `template:`-Verzeichnis (z. B. `templates/`, per `!include_dir_merge_list`) | `vacuum.tesvor_x500_pro` als echte Saugroboter-Entität mit deutschem Status, Klartext-Sensoren für Zustand und Fehler, gerundete Reinigungsdauer |
| `scripts/tesvor_starten.yaml` | `scripts.yaml` | Start mit Aufwecken (Stopp, 3 s, Starttaste); Parameter `taste` = gewünschte ESPHome-Taste |
| `dashboard/saugroboter.yaml` | Dashboard-Sektion (YAML-Editor der Sektion) | vacuum-card mit Shortcuts und Routen-Karte als iframe |

Die Dashboard-Sektion nutzt die HACS-Karte
[denysdovhan/vacuum-card](https://github.com/denysdovhan/vacuum-card). Ohne HACS reicht eine
`tile`-Karte auf `vacuum.tesvor_x500_pro` plus `button`-Karten auf die ESPHome-Tasten.

`vacuum.battery_level` gibt es seit Home Assistant 2026.8 nicht mehr; die Karte bekommt den
Akkustand deshalb über `battery_entity: sensor.tesvor_x500_pro_battery`.

## Karte

`docker/tesvor-map` schreibt in den Ordner `www/tesvor-map` des HA-Konfigverzeichnisses, dort
liegt auch `map.html` (aus `docker/tesvor-map/app/`). Home Assistant liefert den Ordner unter
`/local/tesvor-map/` aus, die iframe-Karte zeigt `/local/tesvor-map/map.html`. Das funktioniert
auch in der Companion-App, weil kein eigener Webserver nötig ist.
