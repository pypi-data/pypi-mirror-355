# -*- coding: utf-8 -*-
"""
Einfache deutsche Python-Funktionen und -Werte
"""

# Basis-Werte
Wahr = True
Falsch = False
Nichts = None

# Deutsche Funktionen (direkt verfügbar)
def drucke(*args, **kwargs):
    """Deutsche Version von print()"""
    print(*args, **kwargs)

def eingabe(prompt=''):
    """Deutsche Version von input()"""
    return input(prompt)

def länge(obj):
    """Deutsche Version von len()"""
    return len(obj)

def bereich(*args):
    """Deutsche Version von range()"""
    return range(*args)

def typ(obj):
    """Deutsche Version von type()"""
    return type(obj)

def liste(iterable=()):
    """Deutsche Version von list()"""
    return list(iterable)

def wörterbuch(*args, **kwargs):
    """Deutsche Version von dict()"""
    return dict(*args, **kwargs)

def zeichenkette(obj=''):
    """Deutsche Version von str()"""
    return str(obj)

def ganze_zahl(obj=0, basis=10):
    """Deutsche Version von int()"""
    if isinstance(obj, str):
        return int(obj, basis)
    return int(obj)

def dezimal_zahl(obj=0.0):
    """Deutsche Version von float()"""
    return float(obj)

# Vereinfachte deutsche Syntax-Funktionen
def wenn_dann(bedingung, dann_code, sonst_code=None):
    """Vereinfachte wenn-dann-sonst Logik"""
    if bedingung:
        return dann_code() if callable(dann_code) else dann_code
    elif sonst_code is not None:
        return sonst_code() if callable(sonst_code) else sonst_code
    return None

# Code-Evaluator für deutsche Syntax
def evaluiere_deutschen_code(code_string):
    """Evaluiert deutschen Python-Code"""
    import re
    
    # Einfache Ersetzungen
    transformations = {
        r'\bwenn\b': 'if',
        r'\bsonst\b': 'else',
        r'\bsonstwenn\b': 'elif',
        r'\bfür\b': 'for',
        r'\bsolange\b': 'while',
        r'\bfunktion\b': 'def',
        r'\bklasse\b': 'class',
        r'\bgib_zurück\b': 'return',
        r'\bWahr\b': 'True',
        r'\bFalsch\b': 'False',
        r'\bNichts\b': 'None',
        r'\bund\b': 'and',
        r'\boder\b': 'or',
        r'\bnicht\b': 'not',
        r'\bselbst\b': 'self',
        r'\bals\b': 'as',
        r'\bin\b': 'in',
        r'\bist\b': 'is',
        r'\bdurchbrechen\b': 'break',
        r'\bfortsetzen\b': 'continue',
        r'\bbestehen\b': 'pass'
    }
    
    transformed_code = code_string
    for german, english in transformations.items():
        transformed_code = re.sub(german, english, transformed_code)
    
    # Stelle deutsche Funktionen zur Verfügung
    exec_globals = {
        'drucke': drucke,
        'eingabe': eingabe,
        'länge': länge,
        'bereich': bereich,
        'typ': typ,
        'liste': liste,
        'wörterbuch': wörterbuch,
        'zeichenkette': zeichenkette,
        'ganze_zahl': ganze_zahl,
        'dezimal_zahl': dezimal_zahl,
        'Wahr': Wahr,
        'Falsch': Falsch,
        'Nichts': Nichts,
        'print': print,  # Fallback
        'input': input,
        'len': len,
        'range': range,
        'type': type,
        'list': list,
        'dict': dict,
        'str': str,
        'int': int,
        'float': float,
        'True': True,
        'False': False,
        'None': None
    }
    
    exec(transformed_code, exec_globals)
    return exec_globals

# Alle Symbole exportieren
__all__ = [
    'Wahr', 'Falsch', 'Nichts',
    'drucke', 'eingabe', 'länge', 'bereich', 'typ', 'liste', 'wörterbuch',
    'zeichenkette', 'ganze_zahl', 'dezimal_zahl',
    'wenn_dann', 'evaluiere_deutschen_code'
]
