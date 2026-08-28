# VBB Realtime Archive

> **Typ:** DA &nbsp;|&nbsp; **Erstellt:** 2026-08-29 &nbsp;|&nbsp; **Version:** 0.1.0

Sammelt die Echtzeitdaten des Berliner und Brandenburger Nahverkehrs, damit sie später auswertbar sind. Der VBB veröffentlicht den aktuellen Netzzustand, archiviert ihn aber nicht. Was heute nicht mitgeschrieben wird, ist morgen weg.

---

## Warum es dieses Repo gibt

Der VBB stellt einen GTFS-Realtime-Feed bereit, der jede Fahrt mit ihren erwarteten Halten enthält. Der Feed zeigt immer nur den Jetzt-Zustand. Historische Ist-Daten gibt es nirgends, archiviert sind lediglich die Soll-Fahrpläne vergangener Jahre.

Ohne Ist-Daten lässt sich die eigentlich interessante Frage nicht beantworten: **Sind die Fahrpläne überhaupt haltbar?** Nicht wie viel Verspätung entsteht, sondern ob die geplanten Zeiten realistisch sind, wo Puffer systematisch falsch liegen und wie oft Fahrten ganz ausfallen.

Dieses Repo baut die Datenbasis dafür auf. Es läuft von allein und wächst täglich.

---

## Wie das Sammeln funktioniert

```
GTFS-RT Feed  ──►  collect.py  ──►  data/raw/YYYY-MM-DD/HHMMSS.parquet
  alle 15 Min      Zeitfenster        ein Snapshot je Lauf
                   ±30 Minuten
                                           │
                                           ▼  nachts 03:40 UTC
                                      compact.py
                                           │
                                           ▼
                                 data/interim/YYYY-MM-DD.parquet
                                    ein Halt = eine Zeile
```

**Warum ein Zeitfenster.** Ein Abruf liefert rund 89.000 Halt-Vorhersagen, aber nur etwa 17 Prozent betreffen Halte in der nächsten oder letzten halben Stunde. Alles andere ist Vorhersage, die vor der Ankunft ohnehin überschrieben wird. Der Filter senkt das Volumen von mehreren Megabyte auf rund 90 KB je Snapshot.

**Warum verdichtet wird.** Bei 15-Minuten-Takt und einem Fenster von einer Stunde wird jeder Halt mehrfach erfasst. Die Verdichtung behält je Halt die späteste Vorhersage, weil sie dem tatsächlichen Geschehen am nächsten kommt.

**Bewusste Einschränkung:** Damit beantwortet das Archiv, *was passiert ist*, nicht *wie früh eine Verspätung bekannt war*. Die Vorhersage-Historie geht bei der Verdichtung verloren.

### Datenfelder

| Feld | Bedeutung |
| :--- | :--- |
| `fetched_at` | Zeitpunkt des Abrufs, UTC |
| `trip_id`, `route_id`, `direction_id` | Fahrt und Linie |
| `start_date`, `start_time` | planmäßiger Fahrtbeginn |
| `trip_status` | 0 planmäßig, 3 gestrichen |
| `stop_id`, `stop_sequence` | Halt und Position in der Fahrt |
| `stop_status` | 0 planmäßig, 1 ausgelassen |
| `arrival_time`, `arrival_delay` | Ankunft und Abweichung in Sekunden |
| `departure_time`, `departure_delay` | Abfahrt und Abweichung in Sekunden |
| `vehicle_id` | Fahrzeug, sofern der Feed es liefert |

### Betrieb

Zwei GitHub-Actions-Workflows, beide kostenlos, weil das Repo öffentlich ist.

| Workflow | Takt | Aufgabe |
| :--- | :--- | :--- |
| `collect` | alle 15 Minuten | Snapshot holen und committen |
| `compact` | täglich 03:40 UTC | abgeschlossene Tage verdichten |

Zwei Eigenheiten der Plattform sind eingeplant:

- GitHub deaktiviert geplante Workflows nach **60 Tagen ohne Commit**. Weil jeder Lauf Daten committet, tritt dieser Fall nicht ein.
- Geplante Läufe werden unter Last **verzögert oder übersprungen**. Der Abstand zwischen Snapshots ist deshalb nicht exakt und darf bei der Auswertung nicht als festes Raster angenommen werden.

### Sammler lokal ausführen

```bash
pip install -r requirements-collect.txt
PYTHONPATH=src python -m vbb_realtime_archive.collect
PYTHONPATH=src python -m vbb_realtime_archive.compact
```

`compact` ohne Argument lässt den laufenden Tag unangetastet und ist mehrfach ausführbar, ohne Daten zu verlieren.

### Datenquelle und Lizenz

Daten aus dem [VBB GTFS-Realtime-Feed](https://production.gtfsrt.vbb.de/), lizenziert unter CC BY 4.0. Der Abruf erfolgt ohne Authentifizierung, mit einem Limit von 60 Anfragen pro Minute und einem User-Agent, der auf dieses Repo verweist.

**Hinweis des Betreibers:** Der Feed hat seit dem 04.06.2026 eine eingeschränkte Datenabdeckung, ohne Angabe, wann sie wiederhergestellt ist. Auswertungen aus diesem Archiv müssen das offenlegen.

---

## Schnellstart

### 1. Virtuelle Umgebung erstellen & aktivieren

```bash
uv venv
source .venv/bin/activate   # Mac/Linux
.venv\Scripts\activate      # Windows
```

### 2. Dependencies + Projektpaket installieren

```bash
uv pip install -e ".[da]"
```

### 3. Jupyter Kernel registrieren

```bash
python -m ipykernel install --user --name vbb_realtime_archive --display-name "Python (vbb_realtime_archive)"
```

Oder einfach: `make setup && make kernel`

### 4. Los geht's!

Oeffne `notebooks/00_introduction.ipynb` und fange an.

---

## Projektstruktur

```
vbb-realtime-archive/
|
+-- PROCESS_LOG.md          # Projektverlauf & AI-Kontext-Einstieg
+-- ROADMAP.md              # Phasen & offene Tasks
+-- CLAUDE.md               # Claude Code Anweisungen
+-- README.md
+-- pyproject.toml          # Paketkonfiguration & Dependencies
+-- Makefile                # Shortcuts (make setup, make kernel, ...)
+-- .gitignore
|
+-- data/                   # Ausnahme: raw + interim gehoeren hier INS Git
|   +-- raw/                # Snapshots je Lauf - NIEMALS veraendern!
|   +-- interim/            # verdichtete Tagesdateien
|   +-- processed/          # Finale, analysefertige Daten (nicht in Git)
|
+-- notebooks/
|   +-- 00_introduction.ipynb
|   +-- 01_exploration.ipynb
|   +-- 02_preparation.ipynb
|   +-- 03_analysis.ipynb
|   +-- 04_insights.ipynb
|
+-- src/vbb_realtime_archive/     # Python-Paket (importierbar nach uv install)
|   +-- config.py           # Zentrale Pfade & Konstanten
|   +-- settings.py         # Plot-Theme, Logging
|   +-- notebook.py         # Zentraler Import-Einstieg fuer Notebooks
|   +-- utils.py            # Hilfsfunktionen
|   +-- data/
|   +-- features/
|   +-- visualization/
|   +-- analytics/
|
+-- tests/
+-- public/
    +-- index.html
    +-- img/
    +-- md/
```

---

## Notebooks

In Lesereihenfolge:

| Notebook | Zweck |
| :--- | :--- |
| [`00_introduction`](notebooks/00_introduction.ipynb) | Projekt-Facts, Kontext, Workflow, Conventions |
| [`01_exploration`](notebooks/01_exploration.ipynb) | EDA + Discovery |
| [`02_preparation`](notebooks/02_preparation.ipynb) | Preparation + Preprocessing, Export |
| [`03_analysis`](notebooks/03_analysis.ipynb) | Import, Analysis + Analytics |
| [`04_insights`](notebooks/04_insights.ipynb) | Business Communication + Insights |

---

## Report

Öffentlicher Einstieg / Präsentation: [`public/index.html`](public/index.html) — Landing-Page mit Navigation zu den Report-Views.

> Start als Platzhalter, wird über `/project-case` mit Inhalt gefüllt (Story, Slides, Views).

---

## Konfiguration

### Pfade (`src/vbb_realtime_archive/config.py`)

```python
from vbb_realtime_archive.config import PATHS

PATHS["raw"]       # data/raw/
PATHS["processed"] # data/processed/
PATHS["figures"]   # public/img/
```

### Notebook-Einstieg

```python
from vbb_realtime_archive.notebook import *
setup_plotting()
```

---

## Tests ausfuehren

```bash
pytest
pytest --cov=src/vbb_realtime_archive --cov-report=term-missing
```

---

_Generiert mit dem wgnd-scaffolding Generator._
