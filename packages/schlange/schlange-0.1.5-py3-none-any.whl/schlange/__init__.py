# -*- coding: utf-8 -*-
"""
Schlange - Python auf Deutsch
Ein Package, das deutsche Schlüsselwörter für Python bereitstellt.
"""

from .keywords import transformiere_deutschen_code, Wahr, Falsch, Nichts
from .functions import *
from .transformer import DeutscherCodeTransformer, transformiere, fuehre_aus

# Auto-Transformation Function
def deutsch(code_string):
    """
    Führt deutschen Python-Code direkt aus
    
    Beispiel:
    deutsch('''
    x = 10
    wenn x > 5:
        drucke("x ist groß")
    ''')
    """
    return fuehre_aus(code_string)

# Erweiterte Import-Systeme
try:
    from .import_hook import (
        install_import_hook, 
        uninstall_import_hook, 
        lade_schlange_datei, 
        fuehre_schlange_aus
    )
    from .magic import aktiviere_deutsche_syntax, deaktiviere_deutsche_syntax, deutsche_syntax
    ERWEITERTE_FEATURES = True
except ImportError:
    ERWEITERTE_FEATURES = False

__version__ = "0.1.5"
__author__ = "Konja Rehm"
__description__ = "Python auf Deutsch - Deutsche Schlüsselwörter für Python"

# Auto-Transformation Function
def deutsch(code_string):
    """
    Führt deutschen Python-Code direkt aus
    
    Beispiel:
    deutsch('''
    x = 10
    wenn x > 5:
        drucke("x ist groß")
    ''')
    """
    from .transformer import fuehre_aus
    return fuehre_aus(code_string)

# Convenience-Funktion für direkten deutschen Code
def code(deutscher_code):
    """Alias für deutsch() - führt deutschen Code aus"""
    return deutsch(deutscher_code)

# Mache alle deutschen Begriffe verfügbar
__all__ = [
    # Kern-Funktionen
    'transformiere_deutschen_code',
    
    # Boolean-Werte
    'Wahr', 'Falsch', 'Nichts',
    
    # Deutsche Funktionen
    'drucke', 'eingabe', 'laenge', 'länge', 'bereich', 'typ', 'liste', 'woerterbuch', 'wörterbuch',
    'zeichenkette', 'ganze_zahl', 'dezimal_zahl', 'offen', 'sortiere',
    'umkehren', 'summe', 'min', 'max', 'alle', 'irgendein',
    'aufzaehlen', 'aufzählen', 'zip_zusammen', 'filter_deutsche', 'karte',
    'hat_attribut', 'hole_attribut', 'setze_attribut', 'loesche_attribut', 'lösche_attribut',
    'format', 'repr', 'id', 'hilfe', 'abs', 'rund',
    
    # Transformer
    'DeutscherCodeTransformer', 'transformiere', 'fuehre_aus',
    
    # Convenience-Funktionen
    'deutsch',
    
    # Auto-Transformation
    'deutsch', 'code'
]

# Erweiterte Features falls verfügbar
if ERWEITERTE_FEATURES:
    __all__.extend([
        'install_import_hook', 'uninstall_import_hook',
        'aktiviere_deutsche_syntax', 'deaktiviere_deutsche_syntax', 'deutsche_syntax',
        'deutsch', 'code'
    ])
else:
    __all__.extend(['deutsch', 'code'])
