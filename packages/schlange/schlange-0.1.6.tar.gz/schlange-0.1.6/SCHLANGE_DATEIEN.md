# .schlange Dateien - Vollständige Anleitung

## Überblick

Mit **Schlange v0.1.5** wurde Unterstützung für `.schlange` Dateien hinzugefügt. Diese ermöglichen es, vollständig deutsche Python-Programme zu schreiben, ohne Wrapper-Funktionen oder Mischungen aus deutschen und englischen Schlüsselwörtern.

## Was sind .schlange Dateien?

`.schlange` Dateien sind Textdateien mit deutscher Python-Syntax, die automatisch in Standard-Python-Code transformiert und ausgeführt werden.

### Vorteile:
- ✅ **100% deutsche Syntax** - keine englischen Schlüsselwörter
- ✅ **Keine Wrapper nötig** - direkte Ausführung
- ✅ **Vollständiger Namespace-Zugriff** - auf alle Variablen und Funktionen
- ✅ **Einfache Integration** - in bestehende Python-Projekte
- ✅ **Bessere Lesbarkeit** - für deutsche Entwickler und Lernende

## Verwendung

### 1. .schlange Datei erstellen

**Datei: `mein_programm.schlange`**
```python
# -*- coding: utf-8 -*-
# Mein erstes deutsches Python-Programm

drucke("Hallo Welt!")

# Variablen
name = "Python Programmierer"
alter = 25
hobbies = ["Programmieren", "Lesen", "Sport"]

# Bedingte Anweisungen
wenn alter >= 18:
    drucke(f"{name} ist erwachsen!")
    
    # Schleifen
    drucke("Hobbies:")
    für hobby in hobbies:
        drucke(f"  - {hobby}")

# Funktionen definieren
funktion berechne_quadrat(zahl):
    ergebnis = zahl * zahl
    zurückgeben ergebnis

# Funktion verwenden
für i in bereich(1, 4):
    quadrat = berechne_quadrat(i)
    drucke(f"{i}² = {quadrat}")
```

### 2. .schlange Datei ausführen

```python
import schlange

# Methode 1: Direkte Ausführung
schlange.fuehre_schlange_aus("mein_programm.schlange")
```

### 3. Mit Namespace-Zugriff

```python
import schlange

# Datei laden und Namespace erhalten
namespace = schlange.lade_schlange_datei("mein_programm.schlange")

# Auf Variablen zugreifen
print("Name:", namespace['name'])
print("Alter:", namespace['alter'])
print("Hobbies:", namespace['hobbies'])

# Funktionen aufrufen
quadrat_func = namespace['berechne_quadrat']
result = quadrat_func(5)
print(f"5² = {result}")
```

## Verwendung von .schlange Dateien

### Methode 1: Direkte Ausführung

```python
import schlange

# Führt die .schlange Datei direkt aus
schlange.fuehre_schlange_aus("mein_programm.schlange")
```

### Methode 2: Laden mit Namespace-Zugriff

```python
import schlange

# Lädt die .schlange Datei und gibt den Namespace zurück
namespace = schlange.lade_schlange_datei("mein_programm.schlange")

# Zugriff auf Variablen aus der .schlange Datei
print("Name aus .schlange Datei:", namespace['mein_name'])
print("Alter aus .schlange Datei:", namespace['alter'])

# Funktionen aus der .schlange Datei aufrufen
if 'begrüße' in namespace:
    greet_func = namespace['begrüße']
    result = greet_func("Entwickler")
    print("Ergebnis:", result)
```

### Methode 3: Import-Hook (Experimentell)

```python
import schlange

# Import-Hook aktivieren
schlange.install_import_hook()

# Jetzt können .schlange Dateien wie normale Module importiert werden
# (noch experimentell)

# Hook wieder deaktivieren
schlange.uninstall_import_hook()
```

## Verfügbare deutsche Schlüsselwörter in .schlange Dateien

| Deutsch | Python | Beispiel |
|---------|--------|----------|
| `wenn` | `if` | `wenn x > 5:` |
| `sonst` | `else` | `sonst:` |
| `sonstwenn` | `elif` | `sonstwenn x == 3:` |
| `für` | `for` | `für i in bereich(10):` |
| `solange` | `while` | `solange x < 100:` |
| `funktion` | `def` | `funktion meine_func():` |
| `klasse` | `class` | `klasse MeineKlasse:` |
| `zurückgeben` | `return` | `zurückgeben ergebnis` |
| `importiere` | `import` | `importiere math` |
| `von` | `from` | `von math importiere pi` |
| `Wahr` | `True` | `ist_fertig = Wahr` |
| `Falsch` | `False` | `ist_aktiv = Falsch` |
| `Nichts` | `None` | `wert = Nichts` |
| `und` | `and` | `wenn a und b:` |
| `oder` | `or` | `wenn a oder b:` |
| `nicht` | `not` | `wenn nicht fertig:` |

## Verfügbare deutsche Funktionen in .schlange Dateien

Alle deutschen Funktionen sind automatisch verfügbar:

- `drucke()` - statt `print()`
- `eingabe()` - statt `input()`
- `laenge()` - statt `len()`
- `bereich()` - statt `range()`
- `typ()` - statt `type()`
- `liste()` - statt `list()`
- `woerterbuch()` - statt `dict()`

## Beispiele

### Einfaches Beispiel

```python
# beispiel.schlange
name = eingabe("Wie heißt du? ")
drucke(f"Hallo {name}!")

wenn laenge(name) > 5:
    drucke("Du hast einen langen Namen!")
```

### Erweiteres Beispiel

```python
# mathematik.schlange
funktion addiere(a, b):
    zurückgeben a + b

funktion multipliziere(a, b):
    zurückgeben a * b

# Listen und Schleifen
zahlen = liste([1, 2, 3, 4, 5])
drucke(f"Liste hat {laenge(zahlen)} Elemente")

für zahl in zahlen:
    resultat = multipliziere(zahl, 2)
    drucke(f"{zahl} * 2 = {resultat}")
```

## Vorteile von .schlange Dateien

1. **Vollständig deutsche Syntax** - Keine Mischung aus deutsch und englisch
2. **Bessere Lesbarkeit** - Code ist für deutsche Sprecher natürlicher
3. **Einfache Integration** - Kann in bestehende Python-Projekte integriert werden
4. **Namespace-Zugriff** - Variablen und Funktionen können aus Python heraus verwendet werden
5. **Keine spezielle IDE nötig** - Funktioniert mit jedem Texteditor

## Technische Details

- `.schlange` Dateien werden zur Laufzeit in Python-Code transformiert
- UTF-8 Encoding wird automatisch verwendet
- Fehlermeldungen beziehen sich auf den transformierten Python-Code
- Der Import-Hook ist experimentell und könnte in zukünftigen Versionen verbessert werden
