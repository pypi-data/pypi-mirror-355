"""
Deutsche Funktionen für Python
Stellt deutsche Aliase für häufig verwendete Python-Funktionen bereit.
"""

import builtins
import sys

# Grundlegende Ein-/Ausgabe-Funktionen
def drucke(*args, sep=' ', end='\n', file=None, flush=False):
    """Deutsche Version von print()"""
    return builtins.print(*args, sep=sep, end=end, file=file, flush=flush)

def eingabe(prompt=''):
    """Deutsche Version von input()"""
    return builtins.input(prompt)

# Datentyp-Funktionen
def länge(obj):
    """Deutsche Version von len()"""
    return builtins.len(obj)

def typ(obj):
    """Deutsche Version von type()"""
    return builtins.type(obj)

def zeichenkette(obj=''):
    """Deutsche Version von str()"""
    return builtins.str(obj)

def ganze_zahl(obj=0, basis=10):
    """Deutsche Version von int()"""
    if isinstance(obj, str):
        return builtins.int(obj, basis)
    return builtins.int(obj)

def dezimal_zahl(obj=0.0):
    """Deutsche Version von float()"""
    return builtins.float(obj)

def liste(iterable=()):
    """Deutsche Version von list()"""
    return builtins.list(iterable)

def wörterbuch(*args, **kwargs):
    """Deutsche Version von dict()"""
    return builtins.dict(*args, **kwargs)

# Bereichs- und Iterationsfunktionen
def bereich(*args):
    """Deutsche Version von range()"""
    return builtins.range(*args)

def aufzählen(iterable, start=0):
    """Deutsche Version von enumerate()"""
    return builtins.enumerate(iterable, start)

def zip_zusammen(*iterables):
    """Deutsche Version von zip()"""
    return builtins.zip(*iterables)

# Datei-Operationen
def offen(datei, modus='r', pufferung=-1, kodierung=None, fehler=None, neue_zeile=None, closefd=True, opener=None):
    """Deutsche Version von open()"""
    return builtins.open(datei, modus, pufferung, kodierung, fehler, neue_zeile, closefd, opener)

# Sortier- und Organisationsfunktionen
def sortiere(iterable, schlüssel=None, umkehren=False):
    """Deutsche Version von sorted()"""
    return builtins.sorted(iterable, key=schlüssel, reverse=umkehren)

def umkehren(seq):
    """Deutsche Version von reversed()"""
    return builtins.reversed(seq)

# Mathematische Funktionen
def summe(iterable, start=0):
    """Deutsche Version von sum()"""
    return builtins.sum(iterable, start)

def min(*args, schlüssel=None, standard=None):
    """Deutsche Version von min()"""
    if len(args) == 1:
        if standard is not None:
            return builtins.min(args[0], key=schlüssel, default=standard)
        return builtins.min(args[0], key=schlüssel)
    return builtins.min(*args, key=schlüssel)

def max(*args, schlüssel=None, standard=None):
    """Deutsche Version von max()"""
    if len(args) == 1:
        if standard is not None:
            return builtins.max(args[0], key=schlüssel, default=standard)
        return builtins.max(args[0], key=schlüssel)
    return builtins.max(*args, key=schlüssel)

def abs(x):
    """Deutsche Version von abs()"""
    return builtins.abs(x)

def rund(zahl, nstellen=None):
    """Deutsche Version von round()"""
    if nstellen is None:
        return builtins.round(zahl)
    return builtins.round(zahl, nstellen)

# Logische Funktionen
def alle(iterable):
    """Deutsche Version von all()"""
    return builtins.all(iterable)

def irgendein(iterable):
    """Deutsche Version von any()"""
    return builtins.any(iterable)

# Filter- und Map-Funktionen
def filter_deutsche(funktion, iterable):
    """Deutsche Version von filter()"""
    return builtins.filter(funktion, iterable)

def karte(funktion, *iterables):
    """Deutsche Version von map()"""
    return builtins.map(funktion, *iterables)

# Attribut-Funktionen
def hat_attribut(obj, name):
    """Deutsche Version von hasattr()"""
    return builtins.hasattr(obj, name)

def hole_attribut(obj, name, standard=None):
    """Deutsche Version von getattr()"""
    if standard is None:
        return builtins.getattr(obj, name)
    return builtins.getattr(obj, name, standard)

def setze_attribut(obj, name, wert):
    """Deutsche Version von setattr()"""
    return builtins.setattr(obj, name, wert)

def lösche_attribut(obj, name):
    """Deutsche Version von delattr()"""
    return builtins.delattr(obj, name)

# Format-Funktionen
def format(wert, format_spec=''):
    """Deutsche Version von format()"""
    return builtins.format(wert, format_spec)

def repr(obj):
    """Deutsche Version von repr()"""
    return builtins.repr(obj)

# ID-Funktion
def id(obj):
    """Deutsche Version von id()"""
    return builtins.id(obj)

# Hilfe-Funktion
def hilfe(obj=None):
    """Deutsche Version von help()"""
    return builtins.help(obj)

# Alle deutschen Funktionen verfügbar machen
__all__ = [
    'drucke', 'eingabe', 'länge', 'typ', 'zeichenkette', 'ganze_zahl', 
    'dezimal_zahl', 'liste', 'wörterbuch', 'bereich', 'aufzählen', 
    'zip_zusammen', 'offen', 'sortiere', 'umkehren', 'summe', 'min', 
    'max', 'abs', 'rund', 'alle', 'irgendein', 'filter_deutsche', 
    'karte', 'hat_attribut', 'hole_attribut', 'setze_attribut', 
    'lösche_attribut', 'format', 'repr', 'id', 'hilfe'
]
