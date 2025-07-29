# Beispiel für Klassen und Funktionen auf Deutsch

von schlange importiere *

klasse Person:
    funktion __init__(selbst, name, alter):
        selbst.name = name
        selbst.alter = alter
        selbst.hobbys = []
    
    funktion vorstellen(selbst):
        drucke(f"Hallo! Ich bin {selbst.name} und {selbst.alter} Jahre alt.")
    
    funktion hobby_hinzufügen(selbst, hobby):
        selbst.hobbys.append(hobby)
        drucke(f"Hobby '{hobby}' wurde hinzugefügt.")
    
    funktion hobbys_zeigen(selbst):
        wenn länge(selbst.hobbys) > 0:
            drucke("Meine Hobbys sind:")
            für hobby in selbst.hobbys:
                drucke(f"- {hobby}")
        sonst:
            drucke("Ich habe noch keine Hobbys eingetragen.")

klasse Student(Person):
    funktion __init__(selbst, name, alter, studiengang):
        super().__init__(name, alter)
        selbst.studiengang = studiengang
        selbst.noten = []
    
    funktion vorstellen(selbst):
        drucke(f"Hallo! Ich bin {selbst.name}, {selbst.alter} Jahre alt und studiere {selbst.studiengang}.")
    
    funktion note_hinzufügen(selbst, note):
        selbst.noten.append(note)
        drucke(f"Note {note} wurde hinzugefügt.")
    
    funktion durchschnitt_berechnen(selbst):
        wenn länge(selbst.noten) > 0:
            durchschnitt = summe(selbst.noten) / länge(selbst.noten)
            gib_zurück rund(durchschnitt, 2)
        sonst:
            gib_zurück Nichts

# Beispiel verwenden
drucke("=== Personen-Beispiel ===")

person1 = Person("Max", 25)
person1.vorstellen()
person1.hobby_hinzufügen("Programmieren")
person1.hobby_hinzufügen("Lesen")
person1.hobbys_zeigen()

drucke()

student1 = Student("Anna", 22, "Informatik")
student1.vorstellen()
student1.note_hinzufügen(1.3)
student1.note_hinzufügen(1.7)
student1.note_hinzufügen(2.0)

durchschnitt = student1.durchschnitt_berechnen()
wenn durchschnitt ist nicht Nichts:
    drucke(f"Notendurchschnitt: {durchschnitt}")

student1.hobby_hinzufügen("Gaming")
student1.hobbys_zeigen()
