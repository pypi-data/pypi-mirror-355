# -*- coding: utf-8 -*-
"""
Command Line Interface für Schlange
Ermöglicht die Ausführung von deutschen Python-Dateien über die Kommandozeile.
"""

import sys
import os
import argparse
from pathlib import Path
from .transformer import DeutscherCodeTransformer

def main():
    """Hauptfunktion für das CLI"""
    parser = argparse.ArgumentParser(
        description='Schlange - Python auf Deutsch',
        prog='schlange'
    )
    
    parser.add_argument(
        'datei',
        help='Deutsche Python-Datei zum Ausführen'
    )
    
    parser.add_argument(
        '--transform', '-t',
        action='store_true',
        help='Nur transformieren, nicht ausführen (zeigt transformierten Code an)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Ausgabedatei für transformierten Code'
    )
    
    parser.add_argument(
        '--encoding', '-e',
        default='utf-8',
        help='Zeichenkodierung der Datei (Standard: utf-8)'
    )
    
    args = parser.parse_args()
    
    # Prüfe, ob die Datei existiert
    if not os.path.exists(args.datei):
        print(f"Fehler: Datei '{args.datei}' nicht gefunden.", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Lese die deutsche Python-Datei
        with open(args.datei, 'r', encoding=args.encoding) as f:
            deutscher_code = f.read()
        
        # Erstelle Transformer
        transformer = DeutscherCodeTransformer()
        
        if args.transform:
            # Nur transformieren
            transformierter_code = transformer.transform_code(deutscher_code)
            
            if args.output:
                # In Datei schreiben
                with open(args.output, 'w', encoding=args.encoding) as f:
                    f.write(transformierter_code)
                print(f"Transformierter Code wurde in '{args.output}' gespeichert.")
            else:
                # Auf Konsole ausgeben
                print(transformierter_code)
        else:
            # Code ausführen
            globals_dict = {'__file__': os.path.abspath(args.datei)}
            
            # Füge das Verzeichnis der Datei zum Python-Pfad hinzu
            datei_verzeichnis = os.path.dirname(os.path.abspath(args.datei))
            if datei_verzeichnis not in sys.path:
                sys.path.insert(0, datei_verzeichnis)
            
            try:
                transformer.execute_german_code(deutscher_code, globals_dict)
            except SystemExit:
                # Normales Programmende
                pass
            except KeyboardInterrupt:
                print("\nProgramm durch Benutzer abgebrochen.", file=sys.stderr)
                sys.exit(1)
            except Exception as e:
                import traceback
                print(f"Fehler beim Ausführen: {e}", file=sys.stderr)
                print("\nDetailierte Fehlermeldung:", file=sys.stderr)
                traceback.print_exc()
                sys.exit(1)
    
    except UnicodeDecodeError:
        print(f"Fehler: Kann Datei '{args.datei}' nicht mit Kodierung '{args.encoding}' lesen.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Fehler: {e}", file=sys.stderr)
        sys.exit(1)

def interaktive_shell():
    """Startet eine interaktive deutsche Python-Shell"""
    print("Schlange - Python auf Deutsch")
    print("Interaktive Shell - Beenden mit 'exit()' oder Ctrl+D")
    print()
    
    transformer = DeutscherCodeTransformer()
    globals_dict = {}
    
    while True:
        try:
            # Eingabe vom Benutzer
            zeile = input(">>> ")
            
            if zeile.strip() in ['exit()', 'quit()', 'exit', 'quit']:
                break
            
            if zeile.strip() == '':
                continue
            
            # Führe den deutschen Code aus
            try:
                result = transformer.execute_german_code(zeile, globals_dict)
                
                # Zeige Ergebnis, falls vorhanden
                if result and len(result) > 0:
                    for key, value in result.items():
                        if not key.startswith('_'):
                            globals_dict[key] = value
            
            except Exception as e:
                print(f"Fehler: {e}")
        
        except (EOFError, KeyboardInterrupt):
            print("\nAuf Wiedersehen!")
            break

if __name__ == '__main__':
    if len(sys.argv) == 1:
        # Keine Argumente - starte interaktive Shell
        interaktive_shell()
    else:
        main()
