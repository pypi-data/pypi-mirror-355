# -*- coding: utf-8 -*-
"""
Vollständiges Beispiel für die Verwendung von .schlange Dateien
Demonstriert alle verfügbaren Features von Schlange v0.1.5
"""

import schlange

def main():
    print("🐍 Schlange v0.1.5 - .schlange Dateien Demo")
    print("=" * 60)
    
    # Zeige verfügbare Funktionen
    print(f"\n📦 Schlange Version: {schlange.__version__}")
    
    # Demo 1: Direkte Ausführung
    print("\n1️⃣ Direkte Ausführung einer .schlange Datei:")
    print("-" * 50)
    schlange.fuehre_schlange_aus('beispiele/einfach.schlange')
    
    # Demo 2: Namespace-Zugriff
    print("\n2️⃣ Namespace-Zugriff auf .schlange Datei:")
    print("-" * 50)
    namespace = schlange.lade_schlange_datei('beispiele/einfach.schlange')
    
    # Auf Variablen zugreifen
    print("🔍 Variablen aus der .schlange Datei:")
    for var_name in ['name', 'alter']:
        if var_name in namespace:
            print(f"   {var_name} = {namespace[var_name]}")
    
    # Auf Funktionen zugreifen
    print("\n🔍 Funktionen aus der .schlange Datei:")
    if 'sage_hallo' in namespace:
        hello_func = namespace['sage_hallo']
        result = hello_func("Python-Entwickler")
        print(f"   sage_hallo('Python-Entwickler') = {result}")
    
    # Demo 3: deutsch() Funktion zum Vergleich
    print("\n3️⃣ Vergleich: deutsch() Funktion:")
    print("-" * 50)
    schlange.deutsch('''
drucke("Das ist die deutsch() Funktion")
für i in bereich(2):
    drucke(f"  Iteration {i}")
    ''')
    
    # Demo 4: Deutsche Funktionen direkt
    print("\n4️⃣ Deutsche Funktionen direkt:")
    print("-" * 50)
    schlange.drucke("Direkte deutsche Funktionen:")
    for i in schlange.bereich(3):
        schlange.drucke(f"  Zahl: {i}")
    
    print("\n" + "=" * 60)
    print("✅ Alle Demos erfolgreich!")
    print("\n💡 Verwendung von .schlange Dateien:")
    print("   • Vollständig deutsche Syntax")
    print("   • Keine Wrapper-Funktionen nötig")
    print("   • Zugriff auf alle Variablen und Funktionen")
    print("   • Einfache Integration in bestehende Projekte")
    print("\n🚀 Bereit für die Veröffentlichung!")

if __name__ == "__main__":
    main()
