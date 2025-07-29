"""
Deutsche Schlüsselwörter für Python
"""

import builtins
import sys
import ast
import types
import re
from typing import Any, Dict

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

def transformiere_deutschen_code(code: str) -> str:
    """Transformiert deutschen Code in Python-Code"""
    transformed = code
    
    # Ersetze deutsche Schlüsselwörter durch englische
    for deutsch, englisch in DEUTSCHE_SCHLUESSELWOERTER.items():
        # Verwende Wortgrenzen, um Teilwörter zu vermeiden
        pattern = r'\b' + re.escape(deutsch) + r'\b'
        transformed = re.sub(pattern, englisch, transformed)
    
    return transformed

# Import-Hook für deutsche Syntax
class DeutscherImportHook:
    """Import-Hook für deutsche Python-Syntax"""
    
    def __init__(self):
        self.original_compile = compile
        
    def install(self):
        """Installiert den Import-Hook"""
        # Ersetze compile-Funktion
        builtins.compile = self.deutsche_compile
        
    def uninstall(self):
        """Deinstalliert den Import-Hook"""
        builtins.compile = self.original_compile
        
    def deutsche_compile(self, source, filename, mode, flags=0, dont_inherit=False, optimize=-1):
        """Deutsche compile-Funktion"""
        if isinstance(source, str):
            # Transformiere deutschen Code
            transformed_source = transformiere_deutschen_code(source)
            return self.original_compile(transformed_source, filename, mode, flags, dont_inherit, optimize)
        else:
            return self.original_compile(source, filename, mode, flags, dont_inherit, optimize)

# Globaler Import-Hook
_import_hook = DeutscherImportHook()

def aktiviere_deutsche_syntax():
    """Aktiviert deutsche Python-Syntax"""
    _import_hook.install()
    print("Deutsche Python-Syntax aktiviert!")

def deaktiviere_deutsche_syntax():
    """Deaktiviert deutsche Python-Syntax"""
    _import_hook.uninstall()
    print("Deutsche Python-Syntax deaktiviert!")

"""
Deutsche Schlüsselwörter für Python
"""

import builtins
import sys
import ast
import types
import re
from typing import Any, Dict

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

def transformiere_deutschen_code(code: str) -> str:
    """Transformiert deutschen Code in Python-Code"""
    transformed = code
    
    # Ersetze deutsche Schlüsselwörter durch englische
    for deutsch, englisch in DEUTSCHE_SCHLUESSELWOERTER.items():
        # Verwende Wortgrenzen, um Teilwörter zu vermeiden
        pattern = r'\b' + re.escape(deutsch) + r'\b'
        transformed = re.sub(pattern, englisch, transformed)
    
    return transformed

# Import-Hook für deutsche Syntax
class DeutscherImportHook:
    """Import-Hook für deutsche Python-Syntax"""
    
    def __init__(self):
        self.original_compile = compile
        
    def install(self):
        """Installiert den Import-Hook"""
        # Ersetze compile-Funktion
        builtins.compile = self.deutsche_compile
        
    def uninstall(self):
        """Deinstalliert den Import-Hook"""
        builtins.compile = self.original_compile
        
    def deutsche_compile(self, source, filename, mode, flags=0, dont_inherit=False, optimize=-1):
        """Deutsche compile-Funktion"""
        if isinstance(source, str):
            # Transformiere deutschen Code
            transformed_source = transformiere_deutschen_code(source)
            return self.original_compile(transformed_source, filename, mode, flags, dont_inherit, optimize)
        else:
            return self.original_compile(source, filename, mode, flags, dont_inherit, optimize)

# Globaler Import-Hook
_import_hook = DeutscherImportHook()

def aktiviere_deutsche_syntax():
    """Aktiviert deutsche Python-Syntax"""
    _import_hook.install()
    print("Deutsche Python-Syntax aktiviert!")

def deaktiviere_deutsche_syntax():
    """Deaktiviert deutsche Python-Syntax"""
    _import_hook.uninstall()
    print("Deutsche Python-Syntax deaktiviert!")

# Boolean-Werte für direkten Import
Wahr = True
Falsch = False
Nichts = None
