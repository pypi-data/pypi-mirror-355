"""
Schlange - Python auf Deutsch
Ein Package, das deutsche Schlüsselwörter für Python bereitstellt.
"""

from .keywords import *
from .functions import *
from .transformer import transformiere, führe_aus

__version__ = "0.1.0"
__author__ = "Konja Rehm"
__description__ = "Python auf Deutsch - Deutsche Schlüsselwörter für Python"

# Mache alle deutschen Begriffe verfügbar
__all__ = [
    # Schlüsselwörter
    'wenn', 'sonst', 'sonstwenn', 'für', 'solange', 'funktion', 'klasse',
    'importiere', 'von', 'gib_zurück', 'versuche', 'außer', 'endlich',
    'Wahr', 'Falsch', 'Nichts', 'und', 'oder', 'nicht', 'in', 'ist',
    'durchbrechen', 'fortsetzen', 'bestehen',
    
    # Funktionen
    'drucke', 'eingabe', 'länge', 'bereich', 'typ', 'liste', 'wörterbuch',
    'zeichenkette', 'ganze_zahl', 'dezimal_zahl', 'offen', 'sortiere',
    'umkehren', 'summe', 'min', 'max', 'alle', 'irgendein',
    
    # Spezielle Wörter
    'selbst', 'als',
    
    # Transformer-Funktionen
    'transformiere', 'führe_aus'
]
