# Deutsches Python-Beispiel

von schlange importiere *

drucke("Hallo Welt!")

def addiere(x, y):
    wenn x > y:
        drucke(f"{x} ist größer als {y}")
    sonst:
        drucke(f"{y} ist größer oder gleich {x}")
    
    gib_zurück x + y

ergebnis = addiere(10, 5)
drucke(f"Das Ergebnis ist: {ergebnis}")

# Schleife
drucke("Zähle von 1 bis 5:")
für i in bereich(1, 6):
    drucke(f"Zahl: {i}")
