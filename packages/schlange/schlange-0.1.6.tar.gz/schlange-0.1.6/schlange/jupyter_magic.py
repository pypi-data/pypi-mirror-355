# -*- coding: utf-8 -*-
"""
Jupyter Magic für deutsche Python-Syntax
Ermöglicht %%deutsch magic in Jupyter Notebooks
"""

try:
    from IPython.core.magic import Magics, magics_class, cell_magic
    from IPython.core.magic_parser import MagicArgumentParser
    from .transformer import fuehre_aus
    
    @magics_class
    class DeutscheMagics(Magics):
        """Deutsche Magic Commands für Jupyter"""
        
        @cell_magic
        def deutsch(self, line, cell):
            """
            %%deutsch
            
            Führt deutschen Python-Code in einer Zelle aus
            
            Beispiel:
            %%deutsch
            x = 10
            wenn x > 5:
                drucke("x ist groß")
            """
            try:
                return fuehre_aus(cell)
            except Exception as e:
                print(f"Fehler beim Ausführen des deutschen Codes: {e}")
                import traceback
                traceback.print_exc()
        
        @cell_magic  
        def de(self, line, cell):
            """Kurze Version von %%deutsch"""
            return self.deutsch(line, cell)
    
    def load_jupyter_magic():
        """Lädt die Jupyter Magic"""
        try:
            from IPython import get_ipython
            ip = get_ipython()
            if ip:
                ip.register_magic_function(DeutscheMagics)
                print("Deutsche Jupyter Magic geladen! Verwende %%deutsch oder %%de")
                return True
        except ImportError:
            pass
        return False

except ImportError:
    # IPython nicht verfügbar
    def load_jupyter_magic():
        print("Jupyter/IPython nicht verfügbar - Magic nicht geladen")
        return False
