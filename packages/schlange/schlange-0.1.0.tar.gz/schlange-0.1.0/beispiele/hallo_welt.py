# Einfaches Hallo-Welt-Programm auf Deutsch

von schlange importiere *

drucke("Hallo Welt!")

name = eingabe("Wie heißt du? ")
drucke(f"Hallo {name}!")

wenn länge(name) > 5:
    drucke("Du hast einen langen Namen!")
sonst:
    drucke("Dein Name ist schön kurz.")

# Zähle von 1 bis 10
drucke("Zähle von 1 bis 10:")
für i in bereich(1, 11):
    drucke(i)

# Einfache Schleife
x = 1
solange x <= 5:
    drucke(f"x ist {x}")
    x += 1

drucke("Programm beendet!")
