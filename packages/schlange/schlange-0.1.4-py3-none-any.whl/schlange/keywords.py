# -*- coding: utf-8 -*-
"""
Deutsche Schlüsselwörter für Python
"""

import builtins
import sys
import re

# Deutsche Schlüsselwörter-Mappings
DEUTSCHE_SCHLUESSELWOERTER = {
    'wenn': 'if',
    'sonst': 'else',
    'sonstwenn': 'elif',
    'für': 'for',
    'solange': 'while',
    'funktion': 'def',
    'klasse': 'class',
    'importiere': 'import',
    'von': 'from',
    'gib_zurück': 'return',
    'versuche': 'try',
    'außer': 'except',
    'endlich': 'finally',
    'Wahr': 'True',
    'Falsch': 'False',
    'Nichts': 'None',
    'und': 'and',
    'oder': 'or',
    'nicht': 'not',
    'durchbrechen': 'break',
    'fortsetzen': 'continue',
    'bestehen': 'pass',
    'selbst': 'self',
    'als': 'as',
    'in': 'in',
    'ist': 'is',
    'mit': 'with',
    'ergebe': 'yield',
    'bestätige': 'assert',
    'global': 'global',
    'nichtlokal': 'nonlocal',
    'lambda': 'lambda',
    'lösche': 'del',
    'erhebe': 'raise'
}

def transformiere_deutschen_code(code):
    """Transformiert deutschen Code in Python-Code"""
    transformed = code
    
    # Ersetze deutsche Schlüsselwörter durch englische
    for deutsch, englisch in DEUTSCHE_SCHLUESSELWOERTER.items():
        # Verwende Wortgrenzen, um Teilwörter zu vermeiden
        pattern = r'\b' + re.escape(deutsch) + r'\b'
        transformed = re.sub(pattern, englisch, transformed)
    
    return transformed

# Boolean-Werte für direkten Import
Wahr = True
Falsch = False
Nichts = None
