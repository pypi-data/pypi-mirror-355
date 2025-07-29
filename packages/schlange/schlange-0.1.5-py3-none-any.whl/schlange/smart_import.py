# -*- coding: utf-8 -*-
"""
Smart Import für deutsche Syntax
Ermöglicht direktes Schreiben von deutschen Schlüsselwörtern
"""

import sys
import traceback
from .transformer import fuehre_aus

class DeutscherWrapper:
    """Wrapper-Klasse für deutsche Syntax"""
    
    def __init__(self):
        self.deutsche_funktionen = {}
        self._load_functions()
    
    def _load_functions(self):
        """Lädt alle deutschen Funktionen"""
        from . import functions
        self.deutsche_funktionen = {
            'drucke': functions.drucke,
            'laenge': functions.laenge,
            'bereich': functions.bereich,
            'eingabe': functions.eingabe,
            'typ': functions.typ,
            'liste': functions.liste,
            'woerterbuch': functions.woerterbuch,
            'aufzaehlen': functions.aufzaehlen,
            'Wahr': True,
            'Falsch': False,
            'Nichts': None,
            'int': int,
            'input': input,
            'str': str,
            'len': len,
            'range': range,
            'print': print
        }
    
    def execute_file(self, filename):
        """Führt eine deutsche Python-Datei aus"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                deutscher_code = f.read()
            
            # Führe deutschen Code aus
            fuehre_aus(deutscher_code)
            
        except FileNotFoundError:
            print(f"Datei '{filename}' nicht gefunden.")
        except Exception as e:
            print(f"Fehler beim Ausführen: {e}")
            traceback.print_exc()
    
    def run_interactive(self):
        """Startet interaktive deutsche Python-Shell"""
        print("Deutsche Python-Shell")
        print("Beenden mit 'exit' oder Ctrl+C")
        print()
        
        while True:
            try:
                # Multi-line Input
                lines = []
                while True:
                    if not lines:
                        prompt = ">>> "
                    else:
                        prompt = "... "
                    
                    line = input(prompt)
                    
                    if line.strip() == "":
                        if lines:
                            break
                        continue
                    
                    if line.strip() in ['exit', 'quit', 'exit()', 'quit()']:
                        print("Auf Wiedersehen!")
                        return
                    
                    lines.append(line)
                    
                    # Einfache Heuristik: Wenn Zeile nicht mit : endet und nicht eingerückt ist
                    if not line.rstrip().endswith(':') and not line.startswith(' ') and not line.startswith('\t'):
                        break
                
                if lines:
                    deutscher_code = '\n'.join(lines)
                    fuehre_aus(deutscher_code)
                    
            except (EOFError, KeyboardInterrupt):
                print("\nAuf Wiedersehen!")
                break
            except Exception as e:
                print(f"Fehler: {e}")

# Globale Instanz
_wrapper = DeutscherWrapper()

def deutsche_datei(filename):
    """Führt eine deutsche Python-Datei aus"""
    _wrapper.execute_file(filename)

def deutsche_shell():
    """Startet deutsche Python-Shell"""
    _wrapper.run_interactive()

def deutsche_exec(code):
    """Führt deutschen Code aus"""
    return fuehre_aus(code)
