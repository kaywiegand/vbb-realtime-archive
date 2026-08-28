# PROCESS_LOG.md – VBB Realtime Archive

> Projektverlauf und AI-Kontext-Einstieg.
> Dieses File ist der Einstiegspunkt für neue Claude-Sessions.

---

## Projekt-Übersicht

| Feld | Inhalt |
| :--- | :--- |
| Projektname | VBB Realtime Archive |
| Erstellt | 2026-08-29 |
| Status | 🔜 Setup |
| Nächster Schritt | EDA starten |

---

## Verlauf

### 2026-08-29 – Projekt aufgesetzt

- Projektstruktur mit wgnd-scaffolding generiert.
- Nächste Schritte: Daten laden, erste EDA.

---

## 2026-08-29 — Sammler gebaut, läuft autonom

**Kontext:** Ausgründung aus der Portfolio-Qualitätsanalyse. Der VBB archiviert
seine Echtzeitdaten nicht, deshalb muss das Sammeln beginnen, bevor die Analyse
geplant ist. Jeder Tag Verzögerung ist ein Tag Daten, der nicht nachholbar ist.

**Gemessen statt geschätzt** (Feed am 2026-08-28):
- 4.704 Fahrten und 88.718 Halt-Vorhersagen je Abruf, 4,5 MB Protobuf
- nur 16,8 % der Halte liegen im Fenster ±30 Minuten
- nach Filter und zstd-Kompression rund 90 KB je Snapshot, grob 9 MB pro Tag
- Ausfälle sind erfasst: `stop_status=1` und `trip_status=3` kommen im Feed vor

**Entscheidungen:**
- *Zeitfenster ±30 Min beim Ingest.* Ohne Filter wäre das Archiv sechsmal so
  groß, ohne Erkenntnisgewinn. Die verworfenen Zeilen sind Vorhersagen, die vor
  der Ankunft ohnehin überschrieben werden.
- *Verdichtung behält den spätesten Wert je Halt.* Nächste an der Realität.
  Preis: die Vorhersage-Historie geht verloren, siehe ROADMAP.
- *Daten gehören ins Git*, abweichend vom Scaffold-Standard. Zweifacher Nutzen:
  das Archiv ist das Produkt, und jeder Commit verhindert die automatische
  Abschaltung geplanter Workflows nach 60 Tagen Inaktivität.
- *Eigene requirements-collect.txt* statt pyproject. Die CI läuft 96-mal am Tag
  und soll weder pandas noch Jupyter noch das Toolkit aus Git installieren.

**Im Test gefunden und behoben:** Die Verdichtung war nicht idempotent. Ein
zweiter Lauf auf denselben Tag hätte die bestehende Tagesdatei durch die Reste
der verbliebenen Snapshots ersetzt und damit Daten verloren. Jetzt wird eine
vorhandene Tagesdatei als zusätzliche Quelle eingelesen und über eine
Staging-Datei atomar ersetzt.

**Nächster Schritt:** Repo auf GitHub anlegen, pushen, Actions aktivieren.
Danach vier Wochen nur laufen lassen. Analyse erst ab Phase 3.
