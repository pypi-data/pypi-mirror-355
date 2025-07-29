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
    """Meta Path Finder für deutsche Python-Dateien und .schlange-Dateien"""
    
    def __init__(self):
        self.transformer = DeutscherCodeTransformer()
    
    def find_spec(self, fullname, path, target=None):
        """Findet deutsche Python-Module und .schlange-Dateien"""
        if path is None:
            path = sys.path
        
        for search_path in path:
            if not isinstance(search_path, str):
                continue
            
            # Suche zuerst nach .schlange-Dateien
            schlange_file = os.path.join(search_path, fullname + '.schlange')
            if os.path.exists(schlange_file):
                return importlib.util.spec_from_loader(
                    fullname, 
                    DeutscherLoader(schlange_file, self.transformer, is_schlange=True)
                )
                
            # Suche nach .py-Dateien mit deutschen Schlüsselwörtern
            module_file = os.path.join(search_path, fullname + '.py')
            if os.path.exists(module_file):
                # Prüfe, ob die Datei deutsche Schlüsselwörter enthält
                with open(module_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if self._contains_german_keywords(content):
                        return importlib.util.spec_from_loader(
                            fullname, 
                            DeutscherLoader(module_file, self.transformer, is_schlange=False)
                        )
        return None
    
    def _contains_german_keywords(self, content):
        """Prüft, ob Code deutsche Schlüsselwörter enthält"""
        german_keywords = ['wenn', 'sonst', 'für', 'solange', 'funktion', 'klasse', 'drucke']
        return any(keyword in content for keyword in german_keywords)

class DeutscherLoader:
    """Loader für deutsche Python-Module und .schlange-Dateien"""
    
    def __init__(self, filename, transformer, is_schlange=False):
        self.filename = filename
        self.transformer = transformer
        self.is_schlange = is_schlange
    
    def create_module(self, spec):
        """Erstellt das Modul"""
        return None  # Standard-Modul-Erstellung verwenden
    
    def exec_module(self, module):
        """Führt das Modul aus"""
        with open(self.filename, 'r', encoding='utf-8') as f:
            deutscher_code = f.read()
        
        # Transformiere deutschen Code zu Python
        # Bei .schlange-Dateien wird immer transformiert
        if self.is_schlange:
            python_code = self.transformer.transform_code(deutscher_code)
        else:
            # Bei .py-Dateien nur wenn nötig
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
        
        # Füge deutsche Funktionen hinzu
        module.__dict__.update(deutsche_funktionen)
        
        # Führe den transformierten Code aus
        exec(python_code, module.__dict__)

def install_import_hook():
    """Installiert den Import-Hook für deutsche Syntax und .schlange-Dateien"""
    if not any(isinstance(finder, DeutscherImportFinder) for finder in sys.meta_path):
        sys.meta_path.insert(0, DeutscherImportFinder())
        print("Deutscher Import-Hook für .py und .schlange Dateien installiert!")

def uninstall_import_hook():
    """Entfernt den Import-Hook"""
    sys.meta_path[:] = [finder for finder in sys.meta_path 
                       if not isinstance(finder, DeutscherImportFinder)]
    print("Deutscher Import-Hook entfernt!")

def lade_schlange_datei(dateipfad):
    """
    Lädt und führt eine .schlange-Datei direkt aus
    
    Args:
        dateipfad (str): Pfad zur .schlange-Datei
        
    Returns:
        dict: Namespace der ausgeführten Datei
    """
    if not os.path.exists(dateipfad):
        raise FileNotFoundError(f"Datei nicht gefunden: {dateipfad}")
    
    if not dateipfad.endswith('.schlange'):
        raise ValueError("Datei muss die Endung .schlange haben")
    
    # Lade den Code
    with open(dateipfad, 'r', encoding='utf-8') as f:
        deutscher_code = f.read()
    
    # Transformiere den Code
    transformer = DeutscherCodeTransformer()
    python_code = transformer.transform_code(deutscher_code)
    
    # Erstelle Namespace mit deutschen Funktionen
    from . import functions
    namespace = {
        'drucke': functions.drucke,
        'laenge': functions.laenge,
        'bereich': functions.bereich,
        'eingabe': functions.eingabe,
        'typ': functions.typ,
        'liste': functions.liste,
        'woerterbuch': functions.woerterbuch,
        'Wahr': True,
        'Falsch': False,
        'Nichts': None,
        '__file__': dateipfad,
        '__name__': '__main__'
    }
    
    # Führe den Code aus
    exec(python_code, namespace)
    
    return namespace

def fuehre_schlange_aus(dateipfad):
    """
    Führt eine .schlange-Datei aus (vereinfachte Version von lade_schlange_datei)
    
    Args:
        dateipfad (str): Pfad zur .schlange-Datei
    """
    lade_schlange_datei(dateipfad)
