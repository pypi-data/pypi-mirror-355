# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
Code-Transformer für deutsche Python-Syntax
Wandelt deutschen Python-Code in Standard-Python-Code um.
"""

import ast
import re
import sys

class DeutscherCodeTransformer:
    """Transformiert deutschen Python-Code in Standard-Python-Code"""
    
    def __init__(self):
        # Mapping von deutschen zu englischen Schlüsselwörtern
        self.keyword_mapping = {
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
            'zurückgeben': 'return',
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
        
        # Mapping von deutschen zu englischen Funktionsnamen
        self.function_mapping = {
            'drucke': 'print',
            'eingabe': 'input',
            'laenge': 'len',
            'länge': 'len',
            'typ': 'type',
            'zeichenkette': 'str',
            'ganze_zahl': 'int',
            'dezimal_zahl': 'float',
            'liste': 'list',
            'woerterbuch': 'dict',
            'wörterbuch': 'dict',
            'bereich': 'range',
            'aufzaehlen': 'enumerate',
            'aufzählen': 'enumerate',
            'zip_zusammen': 'zip',
            'offen': 'open',
            'sortiere': 'sorted',
            'umkehren': 'reversed',
            'summe': 'sum',
            'abs': 'abs',
            'rund': 'round',
            'alle': 'all',
            'irgendein': 'any',
            'filter_deutsche': 'filter',
            'karte': 'map',
            'hat_attribut': 'hasattr',
            'hole_attribut': 'getattr',
            'setze_attribut': 'setattr',
            'lösche_attribut': 'delattr',
            'format': 'format',
            'repr': 'repr',
            'id': 'id',
            'hilfe': 'help'
        }
    
    def transform_code(self, deutscher_code):
        """Transformiert deutschen Code in Standard-Python-Code"""
        
        # Ersetze deutsche Schlüsselwörter durch englische
        transformierter_code = deutscher_code
        
        # Spezielle Behandlung für Kontrollstrukturen ZUERST
        transformierter_code = self._transform_control_structures(transformierter_code)
        
        # Dann ersetze einfache Schlüsselwörter
        for deutsch, englisch in self.keyword_mapping.items():
            # Verwende Wortgrenzen, um Teilwörter zu vermeiden
            pattern = r'\b' + re.escape(deutsch) + r'\b'
            transformierter_code = re.sub(pattern, englisch, transformierter_code)
        
        # Ersetze Funktionsnamen
        for deutsch, englisch in self.function_mapping.items():
            pattern = r'\b' + re.escape(deutsch) + r'\('
            replacement = englisch + '('
            transformierter_code = re.sub(pattern, replacement, transformierter_code)
        
        # Zusätzliche spezielle Ersetzungen
        transformierter_code = self._additional_transforms(transformierter_code)
        
        return transformierter_code
    
    def _additional_transforms(self, code):
        """Zusätzliche spezielle Transformationen"""
        
        # Korrigiere häufige Probleme
        # "is" zurück zu "ist" falls es fälschlicherweise ersetzt wurde in f-strings
        code = re.sub(r'ist größer as', 'ist größer als', code)
        code = re.sub(r'(\w+) is (\w+)', r'\1 ist \2', code)
        # Entfernt: code = re.sub(r' as ', ' als ', code)  # Das war der Fehler!
        
        return code
    
    def _transform_control_structures(self, code):
        """Spezielle Behandlung für Kontrollstrukturen"""
        
        # Transformiere 'für ... in ...:' zu 'for ... in ...:'
        code = re.sub(r'\bfür\s+(\w+)\s+in\s+', r'for \1 in ', code)
        
        # Transformiere 'solange ... :' zu 'while ... :'
        code = re.sub(r'\bsolange\s+', r'while ', code)
        
        # Transformiere 'wenn ... :' zu 'if ... :'
        code = re.sub(r'\bwenn\s+', r'if ', code)
        
        # Transformiere 'funktion name(...)' zu 'def name(...)'
        code = re.sub(r'\bfunktion\s+(\w+)\s*\(', r'def \1(', code)
        
        # Transformiere 'klasse Name:' zu 'class Name:'
        code = re.sub(r'\bklasse\s+(\w+)', r'class \1', code)
        
        return code
    
    def execute_german_code(self, deutscher_code: str, globals_dict=None, locals_dict=None):
        """Führt deutschen Python-Code aus"""
        if globals_dict is None:
            globals_dict = {}
        if locals_dict is None:
            locals_dict = {}
        
        # Füge deutsche Funktionen zum Namespace hinzu
        from . import functions
        
        # Alle deutschen Funktionen hinzufügen
        deutsche_funktionen = {
            'drucke': functions.drucke,
            'eingabe': functions.eingabe,
            'laenge': functions.laenge,
            'länge': functions.laenge,
            'typ': functions.typ,
            'zeichenkette': functions.zeichenkette,
            'ganze_zahl': functions.ganze_zahl,
            'dezimal_zahl': functions.dezimal_zahl,
            'liste': functions.liste,
            'woerterbuch': functions.woerterbuch,
            'wörterbuch': functions.woerterbuch,
            'bereich': functions.bereich,
            'aufzaehlen': functions.aufzaehlen,
            'aufzählen': functions.aufzaehlen,
            'zip_zusammen': functions.zip_zusammen,
            'offen': functions.offen,
            'sortiere': functions.sortiere,
            'umkehren': functions.umkehren,
            'summe': functions.summe,
            'min': functions.min,
            'max': functions.max,
            'abs': functions.abs,
            'rund': functions.rund,
            'alle': functions.alle,
            'irgendein': functions.irgendein,
            'filter_deutsche': functions.filter_deutsche,
            'karte': functions.karte,
            'hat_attribut': functions.hat_attribut,
            'hole_attribut': functions.hole_attribut,
            'setze_attribut': functions.setze_attribut,
            'loesche_attribut': functions.loesche_attribut,
            'lösche_attribut': functions.loesche_attribut,
            'format': functions.format,
            'repr': functions.repr,
            'id': functions.id,
            'hilfe': functions.hilfe,
            # Boolean-Werte
            'Wahr': True,
            'Falsch': False,
            'Nichts': None
        }
        
        globals_dict.update(deutsche_funktionen)
        
        # Transformiere den Code
        transformierter_code = self.transform_code(deutscher_code)
        
        # Debug: Zeige transformierten Code
        # print("Transformierter Code:")
        # print(transformierter_code)
        
        # Führe den transformierten Code aus
        exec(transformierter_code, globals_dict, locals_dict)
        
        return locals_dict

# Globaler Transformer
_transformer = DeutscherCodeTransformer()

def transformiere(deutscher_code):
    """Transformiert deutschen Code in Standard-Python-Code"""
    return _transformer.transform_code(deutscher_code)

def fuehre_aus(deutscher_code, globals_dict=None, locals_dict=None):
    """Führt deutschen Python-Code aus"""
    return _transformer.execute_german_code(deutscher_code, globals_dict, locals_dict)

# Alias für Kompatibilität
führe_aus = fuehre_aus
