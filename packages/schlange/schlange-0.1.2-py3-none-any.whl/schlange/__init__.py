"""
Schlange - Python auf Deutsch
Ein Package, das deutsche Schlüsselwörter für Python bereitstellt.
"""

from .keywords import transformiere_deutschen_code, Wahr, Falsch, Nichts
from .functions import *
from .transformer import DeutscherCodeTransformer, transformiere, führe_aus

__version__ = "0.1.2"
__author__ = "Konja Rehm"
__description__ = "Python auf Deutsch - Deutsche Schlüsselwörter für Python"

# Mache alle deutschen Begriffe verfügbar
__all__ = [
    # Kern-Funktionen
    'transformiere_deutschen_code',
    
    # Boolean-Werte
    'Wahr', 'Falsch', 'Nichts',
    
    # Deutsche Funktionen
    'drucke', 'eingabe', 'länge', 'bereich', 'typ', 'liste', 'wörterbuch',
    'zeichenkette', 'ganze_zahl', 'dezimal_zahl', 'offen', 'sortiere',
    'umkehren', 'summe', 'min', 'max', 'alle', 'irgendein',
    'aufzählen', 'zip_zusammen', 'filter_deutsche', 'karte',
    'hat_attribut', 'hole_attribut', 'setze_attribut', 'lösche_attribut',
    'format', 'repr', 'id', 'hilfe', 'abs', 'rund',
    
    # Transformer
    'DeutscherCodeTransformer', 'transformiere', 'führe_aus'
]
