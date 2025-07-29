# -*- coding: utf-8 -*-
"""
Magic Import System für deutsche Syntax
Ermöglicht `import deutsch` für deutsche Schlüsselwörter
"""

import sys
import builtins
from .transformer import DeutscherCodeTransformer

class DeutscheMagic:
    """Magic-Klasse für deutsche Python-Syntax"""
    
    def __init__(self):
        self.transformer = DeutscherCodeTransformer()
        self.original_exec = builtins.exec
        self.original_eval = builtins.eval
        self._installed = False
    
    def install(self):
        """Installiert das Magic-System"""
        if self._installed:
            return
            
        # Überschreibe exec und eval
        builtins.exec = self._magic_exec
        builtins.eval = self._magic_eval
        
        # Füge deutsche Funktionen zu builtins hinzu
        from . import functions
        builtins.drucke = functions.drucke
        builtins.laenge = functions.laenge
        builtins.bereich = functions.bereich
        builtins.eingabe = functions.eingabe
        builtins.typ = functions.typ
        builtins.liste = functions.liste
        builtins.woerterbuch = functions.woerterbuch
        
        # Deutsche Konstanten
        builtins.Wahr = True
        builtins.Falsch = False
        builtins.Nichts = None
        
        self._installed = True
        print("Deutsche Magic aktiviert!")
    
    def uninstall(self):
        """Deinstalliert das Magic-System"""
        if not self._installed:
            return
            
        # Stelle original exec/eval wieder her
        builtins.exec = self.original_exec
        builtins.eval = self.original_eval
        
        # Entferne deutsche Funktionen
        deutsche_namen = ['drucke', 'laenge', 'bereich', 'eingabe', 'typ', 
                         'liste', 'woerterbuch', 'Wahr', 'Falsch', 'Nichts']
        for name in deutsche_namen:
            if hasattr(builtins, name):
                delattr(builtins, name)
        
        self._installed = False
        print("Deutsche Magic deaktiviert!")
    
    def _magic_exec(self, code, globals=None, locals=None):
        """Magic exec, die deutschen Code transformiert"""
        if isinstance(code, str):
            # Prüfe, ob Code deutsche Schlüsselwörter enthält
            if self._contains_german_keywords(code):
                code = self.transformer.transform_code(code)
        
        return self.original_exec(code, globals, locals)
    
    def _magic_eval(self, expression, globals=None, locals=None):
        """Magic eval, die deutschen Code transformiert"""
        if isinstance(expression, str):
            if self._contains_german_keywords(expression):
                expression = self.transformer.transform_code(expression)
        
        return self.original_eval(expression, globals, locals)
    
    def _contains_german_keywords(self, code):
        """Prüft, ob Code deutsche Schlüsselwörter enthält"""
        german_keywords = ['wenn', 'sonst', 'sonstwenn', 'für', 'solange', 
                          'funktion', 'klasse', 'gib_zurück']
        return any(f'\\b{keyword}\\b' in code for keyword in german_keywords)

# Globale Instanz
_magic = DeutscheMagic()

def aktiviere_deutsche_syntax():
    """Aktiviert deutsche Syntax global"""
    _magic.install()

def deaktiviere_deutsche_syntax():
    """Deaktiviert deutsche Syntax"""
    _magic.uninstall()

# Context Manager für temporäre deutsche Syntax
class deutsche_syntax:
    """Context Manager für deutsche Syntax"""
    
    def __enter__(self):
        aktiviere_deutsche_syntax()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        deaktiviere_deutsche_syntax()
