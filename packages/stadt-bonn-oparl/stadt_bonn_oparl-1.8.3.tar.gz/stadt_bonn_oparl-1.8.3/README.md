# 🏛️ KRAken - Stadt Bonn Ratsinfo

**K**ommunaler **R**echerche-**A**ssistent für die Verarbeitung von Ratsinformationen der Stadt Bonn 🔍

## 📋 Beschreibung

KRAken ist ein Python-Projekt zur intelligenten Verarbeitung und Analyse von kommunalen Ratsinformationen aus der Stadt Bonn. Das Tool bietet eine vollständige Pipeline von der Datenextraktion über die KI-gestützte Analyse bis hin zur Bereitstellung über verschiedene APIs.

### ✨ Hauptfunktionen

- 📥 **Download**: Automatischer Abruf von Ratsdokumenten über die OParl-API
- 🔄 **Konvertierung**: Umwandlung von PDF-Dokumenten in maschinenlesbare Formate
- 🤖 **KI-Analyse**: Intelligente Klassifikation und Zusammenfassung mit LLMs
- 🔍 **Vektorsuche**: Semantische Suche in dokumentierten Inhalten
- 🌐 **API-Server**: FastAPI-basierte Schnittstelle für externe Anwendungen
- 📊 **Datenexploration**: Jupyter-Notebooks für interaktive Analysen

## 🚀 Installation

### uv installieren

Zunächst muss `uv` installiert werden, da es in diesem Projekt verwendet wird.

Installationsanweisungen finden Sie in der [`uv` Dokumentation](https://docs.astral.sh/uv/getting-started/installation/).

Falls Sie bereits eine ältere Version von `uv` installiert haben, aktualisieren Sie mit `uv self update`.

```bash
# Abhängigkeiten installieren
uv install

# Entwicklungsabhängigkeiten installieren
uv sync --group dev
```

## 💻 Nutzung

### 📥 Daten herunterladen und verarbeiten

```bash
# Ratspapiere herunterladen (begrenzt für Tests)
uv run oparl download paper --data-path data/ --max-pages 1

# Heruntergeladene Dokumente konvertieren
uv run oparl convert paper --data-path data/ --all

# Einzelnes Dokument klassifizieren
uv run oparl classify --data-path data/pfad/zum/dokument.md
```

### 🏛️ Sitzungsinformationen abrufen

Das `meeting get` Kommando ermöglicht den schnellen Zugriff auf detaillierte Informationen zu Ratssitzungen. Es eignet sich besonders für:

- **📋 Sitzungsübersicht**: Schnelle Orientierung über Termine, Status und Tagesordnung
- **🔍 Themenfindung**: Identifikation relevanter Beratungsgegenstände
- **📄 Dokumentenzugriff**: Automatischer Download von Einladungen und Protokollen
- **👥 Teilnehmeranalyse**: Überblick über beteiligte Personen und ihre Rollen
- **🔗 Vernetzung**: Verknüpfung zu zugehörigen Drucksachen und Anträgen

```bash
# Kompakte Übersicht (Standard) - zeigt nur wichtige Themen
uv run oparl meeting get --data-path meetings-test --meeting-id 2004507

# Mit Teilnehmer-Liste
uv run oparl meeting get --data-path meetings-test --meeting-id 2004507 --show-participants

# Vollständige Details aller Tagesordnungspunkte
uv run oparl meeting get --data-path meetings-test --meeting-id 2004507 --detailed

# Ohne automatischen Download von Dokumenten
uv run oparl meeting get --data-path meetings-test --meeting-id 2004507 --no-download-files
```

### 🔧 Filteroptionen

Die Filter können mit `uv run oparl filter` verwendet werden:

```bash
# Bestimmte Attribute aus analysis.json-Dateien extrahieren
uv run oparl filter analysis --data-path data-100-haiku --attributes summary tags
```

Die Attribute `title` und `date` sind immer in der Ausgabe enthalten.

### 🌐 Server starten

#### MCP Server (Model Context Protocol)
```bash
uv run fastmcp run src/stadt_bonn_oparl/mcp/server.py --transport sse
```

#### FastAPI Server
```bash
uv run fastapi run src/stadt_bonn_oparl/api/server.py --port 8000
```

### 🔍 Topic Scout testen

```bash
uv run scripts/test_topic_scout.py
```

### 🧪 Testing und Code-Qualität

```bash
# Tests ausführen
uv run pytest

# Tests mit Coverage
uv run pytest --cov

# Linting
uv run ruff check

# Code formatieren
uv run ruff format

# Typenprüfung
uv run mypy src/
```

## Datenexploration 📊

Im Notebook [explore analysis](./notebooks/explore_analysis.ipynb) finden Sie eine erste Analyse der Daten. Für eine umfassendere Datenexploration können Sie auch das Dataset auf Kaggle nutzen: [Stadt Bonn Allris Partial](https://www.kaggle.com/datasets/cgoern/stadt-bonn-allris-partial). Hier werden verschiedene Aspekte der Daten untersucht, um ein besseres Verständnis für die Struktur und den Inhalt der
Ratsinformationen zu gewinnen.

## Rechtliches

Die Daten stammen von der Stadt Bonn und unterliegen den jeweiligen Lizenzbedingungen. Bitte beachten Sie die Lizenzbedingungen, bevor Sie die Daten verwenden oder weitergeben. Die Dateien in diesem Repository unterliegen der GPL-3.0-Lizenz. Weitere Informationen finden Sie in der Datei `LICENSE`.

---

*Dieses Projekt fördert transparente, nachvollziehbare und partizipative Konsensbildung. Für Fragen oder Beiträge bitte die verlinkten Dokumente als Ausgangspunkt nutzen.*

### Mach!Den!Staat!  ❤️  Open Source AI
