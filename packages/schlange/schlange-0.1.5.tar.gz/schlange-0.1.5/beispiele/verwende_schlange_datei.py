# -*- coding: utf-8 -*-
"""
Beispiel: Verwendung von .schlange Dateien
"""

import schlange

# Methode 1: .schlange Datei direkt ausführen
print("=== Methode 1: Direkte Ausführung ===")
schlange.fuehre_schlange_aus("beispiele/test.schlange")

print("\n" + "="*50 + "\n")

# Methode 2: .schlange Datei laden und Namespace erhalten
print("=== Methode 2: Laden mit Namespace ===")
namespace = schlange.lade_schlange_datei("beispiele/test.schlange")

# Auf Variablen aus der .schlange Datei zugreifen
print(f"Variable 'mein_name' aus .schlange Datei: {namespace.get('mein_name')}")
print(f"Variable 'alter' aus .schlange Datei: {namespace.get('alter')}")

# Funktion aus der .schlange Datei aufrufen
if 'grüße' in namespace:
    grüße_funktion = namespace['grüße']
    resultat = grüße_funktion("Python Programmierer")
    print(f"Funktion aus .schlange Datei aufgerufen: {resultat}")

print("\n" + "="*50 + "\n")

# Methode 3: Import-Hook aktivieren für automatischen Import
print("=== Methode 3: Import-Hook (experimentell) ===")
schlange.install_import_hook()

# Jetzt könnten wir theoretisch 'import test' machen, wenn test.schlange im Python-Pfad ist
# Das ist aber noch experimentell

schlange.uninstall_import_hook()

print("Alle Methoden demonstriert!")
