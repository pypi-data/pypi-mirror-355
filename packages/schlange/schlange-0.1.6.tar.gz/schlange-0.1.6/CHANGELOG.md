# Changelog

## Version 0.1.6 (2025-06-13)

### 🔧 Kritische Bugfixes
- ✅ **BEHOBEN:** Import-Syntax Fehler `import os als betriebssystem` 
- ✅ **BEHOBEN:** Fälschliche Rück-Transformation von `as` zu `als` in `_additional_transforms`
- ✅ **BEHOBEN:** Syntaxfehler bei deutschen Import-Statements
- ✅ **VERBESSERT:** Vollständige Kompatibilität mit allen Python-Packages

### 🧹 Projekt-Bereinigung
- ✅ **ENTFERNT:** `beispiele/` Verzeichnis
- ✅ **ENTFERNT:** `tests/` Verzeichnis  
- ✅ **ENTFERNT:** Build-Artefakte (`build/`, `dist/`, `*.egg-info/`)
- ✅ **HINZUGEFÜGT:** `.gitignore` für saubere Entwicklung
- ✅ **OPTIMIERT:** Projektstruktur für Produktion

### ✨ Verbesserungen
- ✅ **ERWEITERT:** `pyproject.toml` mit besseren Metadaten
- ✅ **ERWEITERT:** Keywords und Klassifikatoren für PyPI
- ✅ **DOKUMENTIERT:** Umfassende Release-Notes

### 📦 Package-Kompatibilität
Jetzt funktionieren ALLE Python-Packages perfekt in `.schlange` Dateien:
```python
importiere os als system
importiere math als mathe  
von datetime importiere datetime als zeit
von requests importiere get als hole
```

## Version 0.1.5 (2025-06-13)

### 🆕 Major New Feature: .schlange Dateien
- ✅ **Neu:** Vollständige Unterstützung für `.schlange` Dateien
- ✅ **Neu:** `schlange.fuehre_schlange_aus(dateipfad)` - Direkte Ausführung von .schlange Dateien
- ✅ **Neu:** `schlange.lade_schlange_datei(dateipfad)` - Laden mit Namespace-Zugriff
- ✅ **Neu:** Erweiterte Import-Hook-Unterstützung für .schlange Dateien
- ✅ **Neu:** `zurückgeben` als Alias für `return` hinzugefügt
- ✅ **Dokumentation:** Umfassende Anleitung in `SCHLANGE_DATEIEN.md`
- ✅ **Beispiele:** Vollständige .schlange Beispiele im `beispiele/` Ordner

### Technische Verbesserungen:
- Erweiterte Transformer-Engine für bessere deutsche Keyword-Erkennung
- Verbesserte Import-Hook-Architektur
- Stabilere UTF-8 Behandlung in allen Code-Pfaden
- Bessere Fehlerbehandlung bei Datei-Operationen

### Features:
- **Direkte Ausführung:** .schlange Dateien können ohne Wrapper ausgeführt werden
- **Namespace-Zugriff:** Zugriff auf Variablen und Funktionen aus .schlange Dateien
- **Vollständig deutsche Syntax:** Keine Mischung aus deutsch/englisch mehr nötig
- **Integration:** Einfache Einbindung in bestehende Python-Projekte

## Version 0.1.4 (2025-06-13)

### Neue Features:
- ✅ **Neu:** `deutsch()` Funktion für direkte Ausführung deutschen Codes
- ✅ Beispiel: `deutsch("wenn x > 5: drucke('groß')")`
- ✅ Vereinfachte API für einfache deutsche Code-Snippets

## Version 0.1.3 (2025-06-13)

### Kritische Bugfixes:
- ✅ Behoben: Encoding-Probleme mit deutschen Umlauten in Python-Dateien
- ✅ Behoben: SyntaxError durch UTF-8 Zeichen in Funktionsnamen
- ✅ Hinzugefügt: Proper encoding declarations (# -*- coding: utf-8 -*-)
- ✅ Verbessert: ASCII-kompatible Funktionsnamen mit Umlauten-Aliassen
- ✅ Behoben: Python 2/3 Kompatibilitätsprobleme

### Neue Features:
- ASCII-kompatible Funktionsnamen: `laenge()` (mit Alias `länge()`)
- ASCII-kompatible Funktionsnamen: `woerterbuch()` (mit Alias `wörterbuch()`)
- ASCII-kompatible Funktionsnamen: `aufzaehlen()` (mit Alias `aufzählen()`)
- ASCII-kompatible Funktionsnamen: `loesche_attribut()` (mit Alias `lösche_attribut()`)
- ASCII-kompatible Transformer-Funktion: `fuehre_aus()` (mit Alias `führe_aus()`)

### Technische Verbesserungen:
- Entfernt: Type hints für bessere Python-Versions-Kompatibilität
- Vereinfacht: Funktionsdefinitionen für stabilere Ausführung
- Verbessert: Import-System funktioniert jetzt zuverlässig
- Getestet: CLI-Tool funktioniert vollständig

### Erfolgreiche Tests:
- ✅ `import schlange` funktioniert ohne Fehler
- ✅ Deutsche Funktionen (`drucke`, `laenge`, `bereich`) funktionieren
- ✅ Code-Transformation funktioniert korrekt
- ✅ CLI-Tool funktioniert: `python3 -m schlange.cli datei.py`
- ✅ Alle Beispiele laufen erfolgreich

## Version 0.1.1 (2025-06-13)

### Verbesserte Funktionen:
- ✅ Verbesserte Code-Transformation für deutsche Syntax
- ✅ Bessere Behandlung von deutschen Operatoren ('ist', 'als')
- ✅ Stabileres CLI-Tool für deutsche .py-Dateien
- ✅ Erweiterte Fehlerbehandlung im Transformer
- ✅ Vollständige Dokumentation und Beispiele

### Neue Features:
- Deutsche Schlüsselwörter funktionieren zuverlässig
- Verbesserter Import-Hook für deutsche Syntax
- Umfassende Beispielsammlung
- Detaillierte Verwendungsanleitung

### Bugfixes:
- Korrigierte Transformation von 'ist' vs 'is'
- Korrigierte Transformation von 'als' vs 'as'
- Bessere Behandlung von f-strings mit deutschen Begriffen
- Stabilere Ausführung von deutschem Code

### Technische Verbesserungen:
- Optimierter Code-Transformer
- Bessere Regex-Patterns für deutsche Begriffe
- Erweiterte Funktionsmappings
- Verbesserte Fehlerbehandlung

## Version 0.1.0 (2025-06-13)

### Erste Veröffentlichung:
- Grundlegende deutsche Python-Funktionen
- Code-Transformation für deutsche Syntax
- CLI-Tool für deutsche .py-Dateien
- PyPI-Veröffentlichung
