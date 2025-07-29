# -*- coding: utf-8 -*-
"""
Import Hook für deutsche Python-Syntax
Ermöglicht direkten Import von deutschen .py-Dateien
"""

import sys
import importlib.util
import os
from .transformer import DeutscherCodeTransformer

class DeutscherImportFinder:
    """Meta Path Finder für deutsche Python-Dateien"""
    
    def __init__(self):
        self.transformer = DeutscherCodeTransformer()
    
    def find_spec(self, fullname, path, target=None):
        """Findet deutsche Python-Module"""
        if path is None:
            path = sys.path
        
        for search_path in path:
            if not isinstance(search_path, str):
                continue
                
            # Suche nach .py-Dateien mit deutschen Schlüsselwörtern
            module_file = os.path.join(search_path, fullname + '.py')
            if os.path.exists(module_file):
                # Prüfe, ob die Datei deutsche Schlüsselwörter enthält
                with open(module_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if self._contains_german_keywords(content):
                        return importlib.util.spec_from_loader(
                            fullname, 
                            DeutscherLoader(module_file, self.transformer)
                        )
        return None
    
    def _contains_german_keywords(self, content):
        """Prüft, ob Code deutsche Schlüsselwörter enthält"""
        german_keywords = ['wenn', 'sonst', 'für', 'solange', 'funktion', 'klasse', 'drucke']
        return any(keyword in content for keyword in german_keywords)

class DeutscherLoader:
    """Loader für deutsche Python-Module"""
    
    def __init__(self, filename, transformer):
        self.filename = filename
        self.transformer = transformer
    
    def create_module(self, spec):
        """Erstellt das Modul"""
        return None  # Standard-Modul-Erstellung verwenden
    
    def exec_module(self, module):
        """Führt das Modul aus"""
        with open(self.filename, 'r', encoding='utf-8') as f:
            deutscher_code = f.read()
        
        # Transformiere deutschen Code zu Python
        python_code = self.transformer.transform_code(deutscher_code)
        
        # Füge deutsche Funktionen zum Namespace hinzu
        from . import functions
        deutsche_funktionen = {
            'drucke': functions.drucke,
            'laenge': functions.laenge,
            'bereich': functions.bereich,
            'eingabe': functions.eingabe,
            'typ': functions.typ,
            'liste': functions.liste,
            'woerterbuch': functions.woerterbuch,
            'Wahr': True,
            'Falsch': False,
            'Nichts': None
        }
        
        # Führe den transformierten Code aus
        exec(python_code, module.__dict__)
        
        # Füge deutsche Funktionen hinzu
        module.__dict__.update(deutsche_funktionen)

def install_import_hook():
    """Installiert den Import-Hook für deutsche Syntax"""
    if not any(isinstance(finder, DeutscherImportFinder) for finder in sys.meta_path):
        sys.meta_path.insert(0, DeutscherImportFinder())
        print("Deutscher Import-Hook installiert!")

def uninstall_import_hook():
    """Entfernt den Import-Hook"""
    sys.meta_path[:] = [finder for finder in sys.meta_path 
                       if not isinstance(finder, DeutscherImportFinder)]
    print("Deutscher Import-Hook entfernt!")
