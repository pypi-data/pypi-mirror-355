# Schlange 🐍

**Python auf Deutsch** - Ein Python-Package, das deutsche Schlüsselwörter für Python bereitstellt.

## Überblick

Schlange ermöglicht es, Python-Code mit deutschen Schlüsselwörtern zu schreiben. Anstatt `if`, `for`, `while` etc. können Sie deutsche Begriffe wie `wenn`, `für`, `solange` verwenden.

## Installation

```bash
pip install schlange
```

## Schnellstart

### Methode 1: Deutsche Funktionen direkt verwenden

```python
from schlange.functions import drucke, bereich, länge

drucke("Hallo Welt!")
for i in bereich(1, 6):
    drucke(f"Zahl: {i}")
```

### Methode 2: Deutsche Syntax mit Transformation

```python
from schlange.transformer import führe_aus

deutscher_code = """
funktion begrüße(name):
    drucke(f"Hallo {name}!")
    gib_zurück f"Begrüßung für {name}"

wenn 5 > 3:
    nachricht = begrüße("Welt")
    drucke(nachricht)
"""

führe_aus(deutscher_code)
```

### Methode 3: CLI-Tool für deutsche .py-Dateien

Erstellen Sie eine Datei `mein_programm.py`:
```python
von schlange importiere *

drucke("Deutsches Python!")
für i in bereich(5):
    drucke(f"Zahl {i}")
```

Führen Sie aus:
```bash
python -m schlange.cli mein_programm.py
```

## Verwendung

### Als Modul importieren

```python
from schlange import *

# Statt if/else
wenn x > 5:
    drucke("x ist größer als 5")
sonst:
    drucke("x ist kleiner oder gleich 5")

# Statt for-Loop
für i in bereich(10):
    drucke(i)

# Statt while-Loop
solange x < 100:
    x += 1
```

### Als Skript ausführen

```bash
schlange mein_programm.py
```

## Deutsche Schlüsselwörter

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
| `gib_zurück` | `return` | Rückgabewert |
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

## Funktionen

| Deutsch | English | Beschreibung |
|---------|---------|--------------|
| `drucke()` | `print()` | Ausgabe |
| `eingabe()` | `input()` | Benutzereingabe |
| `länge()` | `len()` | Länge ermitteln |
| `bereich()` | `range()` | Zahlenbereich |
| `typ()` | `type()` | Typ ermitteln |
| `liste()` | `list()` | Liste erstellen |
| `wörterbuch()` | `dict()` | Dictionary erstellen |

## Beispiele

### Einfaches Programm

```python
from schlange import *

name = eingabe("Wie heißt du? ")
drucke(f"Hallo {name}!")

wenn länge(name) > 10:
    drucke("Du hast einen langen Namen!")
sonst:
    drucke("Dein Name ist schön kurz.")
```

### Klasse definieren

```python
from schlange import *

klasse Person:
    funktion __init__(selbst, name, alter):
        selbst.name = name
        selbst.alter = alter
    
    funktion vorstellen(selbst):
        drucke(f"Ich bin {selbst.name} und {selbst.alter} Jahre alt.")

person = Person("Max", 25)
person.vorstellen()
```

## Lizenz

MIT License
