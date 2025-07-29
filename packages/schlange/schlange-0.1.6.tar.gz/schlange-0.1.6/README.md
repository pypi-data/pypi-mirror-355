# Schlange 🐍

**Python auf Deutsch** - Ein Python-Package, das deutsche Schlüsselwörter für Python bereitstellt.

[![PyPI version](https://badge.fury.io/py/schlange.svg)](https://badge.fury.io/py/schlange)
[![Downloads](https://pepy.tech/badge/schlange)](https://pepy.tech/project/schlange)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Überblick

**Schlange** ermöglicht es, Python-Code vollständig in deutscher Sprache zu schreiben. Mit **Version 0.1.5** wurden **.schlange Dateien** eingeführt - eine revolutionäre neue Art, komplett deutsche Python-Programme zu erstellen!

## 🚀 Neue Features in v0.1.5

- **🆕 .schlange Dateien** - Vollständig deutsche Python-Programme ohne Wrapper
- **🔄 Erweiterte Import-Hooks** - Automatischer Import von .schlange Dateien  
- **📝 Neues Schlüsselwort** - `zurückgeben` als Alternative zu `return`
- **🔧 Verbesserte Transformation** - Robustere deutsche Code-Konvertierung

## Installation

```bash
pip install schlange
```

## 🌟 Vier Wege für deutschen Python-Code

### 1️⃣ Deutsche Funktionen direkt verwenden

```python
from schlange import drucke, bereich, laenge

drucke("Hallo Welt!")
für i in bereich(1, 6):
    drucke(f"Zahl: {i}")

meine_liste = [1, 2, 3, 4, 5]
drucke(f"Liste hat {laenge(meine_liste)} Elemente")
```

### 2️⃣ Deutsche Syntax mit deutsch() Funktion

```python
from schlange import deutsch

deutsch("""
funktion begrüße(name):
    drucke(f"Hallo {name}!")
    zurückgeben f"Begrüßung für {name}"

wenn 5 > 3:
    nachricht = begrüße("Welt")
    drucke(nachricht)
""")
```

### 3️⃣ CLI-Tool für deutsche .py-Dateien

**Datei: `mein_programm.py`**
```python
drucke("Deutsches Python!")
für i in bereich(5):
    drucke(f"Zahl {i}")
```

**Ausführung:**
```bash
python -m schlange.cli mein_programm.py
```
```

### 4️⃣ 🆕 .schlange Dateien (NEU in v0.1.5!)

**Das Highlight: Vollständig deutsche Python-Programme!**

**Datei: `mein_programm.schlange`**
```python
# -*- coding: utf-8 -*-
drucke("Hallo aus einer .schlange Datei!")

# Variablen
mein_name = "Python Entwickler"
alter = 28
hobbies = ["Programmieren", "Lesen", "Sport"]

# Bedingte Anweisungen
wenn alter >= 18:
    drucke(f"{mein_name} ist erwachsen!")
    
    # Schleifen
    drucke("Meine Hobbies:")
    für hobby in hobbies:
        drucke(f"  • {hobby}")

# Funktionen definieren
funktion berechne_quadrat(zahl):
    ergebnis = zahl * zahl
    zurückgeben ergebnis

# Funktion verwenden
für i in bereich(1, 4):
    quadrat = berechne_quadrat(i)
    drucke(f"{i}² = {quadrat}")
```

**Verwendung in Python:**
```python
import schlange

# Methode A: Direkte Ausführung
schlange.fuehre_schlange_aus("mein_programm.schlange")

# Methode B: Mit Namespace-Zugriff
namespace = schlange.lade_schlange_datei("mein_programm.schlange")

# Auf Variablen zugreifen
print("Name:", namespace['mein_name'])
print("Alter:", namespace['alter'])

# Funktionen aufrufen
quadrat_func = namespace['berechne_quadrat']
result = quadrat_func(5)
print(f"5² = {result}")
```

### ✨ Warum .schlange Dateien?

- ✅ **100% deutsche Syntax** - Keine englischen Schlüsselwörter
- ✅ **Keine Wrapper nötig** - Direkte Ausführung ohne `deutsch()` Funktion
- ✅ **Vollständiger Namespace-Zugriff** - Alle Variablen und Funktionen verfügbar
- ✅ **Bessere Lesbarkeit** - Ideal für deutsche Entwickler und Lernende
- ✅ **Einfache Integration** - Nahtlose Einbindung in bestehende Projekte

## 📚 Deutsche Schlüsselwörter

| Deutsch | English | Beschreibung |
|---------|---------|--------------|
| `wenn` | `if` | Bedingte Anweisung |
| `sonst` | `else` | Alternative Anweisung |
| `sonstwenn` | `elif` | Weitere Bedingung |
| `für` | `for` | Schleife |
| `solange` | `while` | Bedingte Schleife |
| `funktion` | `def` | Funktionsdefinition |
| `klasse` | `class` | Klassendefinition |
| `importiere` | `import` | Modul importieren |
| `von` | `from` | Import von spezifischen Elementen |
| `zurückgeben` | `return` | Rückgabewert 🆕 |
| `gib_zurück` | `return` | Rückgabewert (Alternative) |
| `versuche` | `try` | Fehlerbehandlung |
| `außer` | `except` | Ausnahmebehandlung |
| `endlich` | `finally` | Abschlussblock |
| `Wahr` | `True` | Boolean True |
| `Falsch` | `False` | Boolean False |
| `Nichts` | `None` | None-Wert |
| `und` | `and` | Logisches UND |
| `oder` | `or` | Logisches ODER |
| `nicht` | `not` | Logisches NICHT |
| `in` | `in` | Enthaltensein-Operator |
| `ist` | `is` | Identitäts-Operator |
| `durchbrechen` | `break` | Schleife verlassen |
| `fortsetzen` | `continue` | Nächste Iteration |
| `bestehen` | `pass` | Leere Anweisung |

## 🔧 Deutsche Funktionen

| Deutsch | English | Beschreibung |
|---------|---------|--------------|
| `drucke()` | `print()` | Text ausgeben |
| `eingabe()` | `input()` | Benutzereingabe |
| `laenge()` | `len()` | Länge/Anzahl ermitteln |
| `bereich()` | `range()` | Zahlenbereich erstellen |
| `typ()` | `type()` | Datentyp ermitteln |
| `liste()` | `list()` | Liste erstellen |
| `woerterbuch()` | `dict()` | Dictionary erstellen |

## 💡 Praxisbeispiele

### Einfaches Programm

```python
from schlange import drucke, eingabe, laenge

name = eingabe("Wie heißt du? ")
drucke(f"Hallo {name}!")

wenn laenge(name) > 10:
    drucke("Du hast einen langen Namen!")
sonst:
    drucke("Dein Name ist schön kurz.")
```

### Klassen-Beispiel (.schlange Datei)

**Datei: `person.schlange`**
```python
klasse Person:
    funktion __init__(selbst, name, alter):
        selbst.name = name
        selbst.alter = alter
    
    funktion vorstellen(selbst):
        drucke(f"Ich bin {selbst.name} und {selbst.alter} Jahre alt.")
    
    funktion geburtstag(selbst):
        selbst.alter += 1
        drucke(f"Herzlichen Glückwunsch! Jetzt bin ich {selbst.alter}!")

# Person erstellen
max = Person("Max Mustermann", 30)
max.vorstellen()
max.geburtstag()
```

**Verwendung:**
```python
import schlange

# .schlange Datei ausführen
namespace = schlange.lade_schlange_datei("person.schlange")

# Klasse aus .schlange Datei verwenden
Person = namespace['Person']
anna = Person("Anna Schmidt", 25)
anna.vorstellen()
```

📖 **Weitere Informationen:** Siehe [SCHLANGE_DATEIEN.md](SCHLANGE_DATEIEN.md) für eine detaillierte Anleitung.
| `ist` | `is` | Identitäts-Operator |
| `durchbrechen` | `break` | Schleife verlassen |
| `fortsetzen` | `continue` | Nächste Iteration |
## 🎯 Anwendungsfälle

### 🎓 Bildung
- **Deutschsprachiger Programmierunterricht** - Lernen ohne Sprachbarrieren
- **Universitäten und Schulen** - Deutsche Informatik-Kurse
- **Coding-Bootcamps** - Schnellerer Einstieg für deutsche Muttersprachler

### 👥 Entwicklerteams
- **Prototyping** - Schnelle Entwicklung in der Muttersprache
- **Dokumentation** - Deutsche Codebeispiele und Tutorials
- **Teamkommunikation** - Bessere Verständlichkeit im deutschen Team

### 🔬 Wissenschaft
- **Forschungsprojekte** - Deutsche Algorithmus-Beschreibungen
- **Datenanalyse** - Verständliche Scripts für Wissenschaftler
- **Simulation** - Deutsche Modellbeschreibungen

## 🌟 Erweiterte Features

### Import-Hook System (Experimentell)
```python
import schlange

# Import-Hook aktivieren
schlange.install_import_hook()

# Jetzt können .schlange Dateien wie normale Module importiert werden
# import mein_modul  # würde mein_modul.schlange laden

# Import-Hook deaktivieren
schlange.uninstall_import_hook()
```

### Jupyter Notebook Integration (Experimentell)
```python
# In Jupyter Notebook
%load_ext schlange.jupyter_magic

%%deutsch
funktion fibonacci(n):
    wenn n <= 1:
        zurückgeben n
    sonst:
        zurückgeben fibonacci(n-1) + fibonacci(n-2)

drucke(fibonacci(10))
```

## 📖 Dokumentation

- **[SCHLANGE_DATEIEN.md](SCHLANGE_DATEIEN.md)** - Vollständige Anleitung für .schlange Dateien
- **[CHANGELOG.md](CHANGELOG.md)** - Versionshistorie und Updates
- **[Beispiele/](beispiele/)** - Praktische Codebeispiele

## 🤝 Beitragen

Schlange ist ein Open-Source-Projekt! Beiträge sind willkommen:

1. **Issues melden** - Bugs oder Feature-Wünsche
2. **Pull Requests** - Code-Verbesserungen
3. **Dokumentation** - Beispiele und Anleitungen
4. **Tests** - Qualitätssicherung

## 📜 Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei für Details.

## 🔗 Links

- **PyPI:** https://pypi.org/project/schlange/
- **GitHub:** (Repository-Link)
- **Dokumentation:** [SCHLANGE_DATEIEN.md](SCHLANGE_DATEIEN.md)

---

**Entwickelt mit ❤️ für die deutsche Python-Community**

*Schlange v0.1.5 - Wo Python Deutsch spricht! 🐍🇩🇪*
