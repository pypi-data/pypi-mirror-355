# Mathematisches Beispiel auf Deutsch

von schlange importiere *

funktion ist_primzahl(n):
    """Prüft, ob eine Zahl eine Primzahl ist"""
    wenn n < 2:
        gib_zurück Falsch
    
    für i in bereich(2, ganze_zahl(n ** 0.5) + 1):
        wenn n % i == 0:
            gib_zurück Falsch
    
    gib_zurück Wahr

funktion fibonacci(n):
    """Berechnet die n-te Fibonacci-Zahl"""
    wenn n <= 1:
        gib_zurück n
    sonst:
        gib_zurück fibonacci(n-1) + fibonacci(n-2)

funktion fakultät(n):
    """Berechnet die Fakultät einer Zahl"""
    wenn n <= 1:
        gib_zurück 1
    sonst:
        gib_zurück n * fakultät(n-1)

# Hauptprogramm
drucke("=== Mathematische Beispiele ===")

# Primzahlen finden
drucke("Primzahlen bis 20:")
primzahlen = []
für zahl in bereich(2, 21):
    wenn ist_primzahl(zahl):
        primzahlen.append(zahl)

drucke(f"Gefundene Primzahlen: {primzahlen}")

# Fibonacci-Folge
drucke("\nFibonacci-Folge (erste 10 Zahlen):")
für i in bereich(10):
    drucke(f"F({i}) = {fibonacci(i)}")

# Fakultäten
drucke("\nFakultäten:")
für i in bereich(1, 6):
    drucke(f"{i}! = {fakultät(i)}")

# Listen-Operationen
zahlen = [1, 5, 2, 8, 3, 9, 4, 7, 6]
drucke(f"\nOriginal-Liste: {zahlen}")
drucke(f"Sortiert: {sortiere(zahlen)}")
drucke(f"Umgekehrt: {liste(umkehren(zahlen))}")
drucke(f"Summe: {summe(zahlen)}")
drucke(f"Minimum: {min(zahlen)}")
drucke(f"Maximum: {max(zahlen)}")
drucke(f"Durchschnitt: {rund(summe(zahlen) / länge(zahlen), 2)}")

# Bedingte Operationen
drucke("\nGerade Zahlen aus der Liste:")
gerade_zahlen = [zahl für zahl in zahlen wenn zahl % 2 == 0]
drucke(gerade_zahlen)

drucke("\nUngerade Zahlen aus der Liste:")
ungerade_zahlen = [zahl für zahl in zahlen wenn zahl % 2 != 0]
drucke(ungerade_zahlen)
