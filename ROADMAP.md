# ROADMAP — vbb-realtime-archive

> Ausgangslage → Phasen → Ziel

---

## Ausgangslage

Der VBB veröffentlicht einen GTFS-Realtime-Feed mit dem aktuellen Netzzustand,
archiviert ihn aber nicht. Historische Ist-Daten existieren nirgends, nur die
Soll-Fahrpläne vergangener Jahre sind gespiegelt. Damit ist die Frage nach der
Haltbarkeit von Fahrplänen aus Bestandsdaten nicht beantwortbar.

Erkenntnis aus zh-tram-flow: dort stellte sich am Ende heraus, dass nicht der
Verkehr das Problem war, sondern die Fahrpläne. Dieses Projekt stellt diese
Frage von vornherein und baut die Datenbasis dafür selbst auf.

---

## Phasen

- [x] **Phase 1 — Sammler** (2026-08-29)
      Ingestion mit Zeitfenster-Filter, tägliche Verdichtung, zwei
      GitHub-Actions-Workflows. Läuft autonom, committet ins Repo.

- [ ] **Phase 2 — Datenbasis reift**
      Mindestens vier Wochen sammeln. Erst dann sind Wochentagsmuster
      belastbar, Saisonalität braucht Monate. In dieser Zeit keine Analyse,
      nur Betriebsüberwachung.

- [ ] **Phase 3 — Soll-Daten anbinden**
      Statische GTFS-Fahrpläne dazuholen (vbb-gtfs.jannisr.de). Erst der
      Abgleich Ist gegen Soll macht die eigentliche Frage beantwortbar.

- [ ] **Phase 4 — Analyse**
      Fahrplan-Haltbarkeit, systematische Pufferfehler, Ausfallquoten,
      Verspätungs-Propagation im Netz, Anschlusssicherheit an Knoten.

- [ ] **Phase 5 — Portfolio-Layer**
      `/project-case` für Hub und Views.

---

## Ziel

Ein Datensatz, den es sonst nicht gibt, und darauf aufbauend die Antwort auf
die Frage, ob die Fahrpläne des Berliner Nahverkehrs realistisch geplant sind.

Das Archiv selbst ist bereits ein Ergebnis: es wächst weiter, unabhängig davon,
wann die Analyse gebaut wird.

---

## Offene Entscheidungen

- **Speicherort ab etwa 3 GB.** Das Repo wächst um grob 5 bis 15 MB pro Tag.
  Nach rund einem Jahr ist ein Umzug nach Cloudflare R2 oder Hugging Face
  Datasets fällig.
- **Vorhersage-Historie.** Die Verdichtung behält nur den letzten Wert je Halt.
  Falls die Frage "wie früh war die Verspätung bekannt" relevant wird, muss die
  Verdichtungsregel vorher geändert werden. Rückwirkend geht das nicht.
