#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Passwortmanager - Haupteinstiegspunkt der Anwendung.
"""

import sys
import os
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QIcon

# Füge das aktuelle Verzeichnis zum Suchpfad hinzu
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Importiere MainWindow
from gui.main_window import MainWindow
from gui.styles.resources import IconManager

# Aktualisiere die __init__.py-Dateien, um MainWindow zu importieren
try:
    # gui/__init__.py aktualisieren
    init_path = os.path.join(current_dir, 'gui', '__init__.py')
    if os.path.exists(init_path):
        with open(init_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Kommentierte MainWindow-Zeilen aktivieren
        content = content.replace('# from gui.main_window import MainWindow', 'from gui.main_window import MainWindow')
        content = content.replace("    # 'MainWindow',", "    'MainWindow',")
        
        with open(init_path, 'w', encoding='utf-8') as f:
            f.write(content)
except Exception as e:
    print(f"Warnung: Konnte __init__.py nicht aktualisieren: {e}")

def exception_hook(exctype, value, tb):
    """
    Globaler Exception-Handler für unerwartete Fehler
    
    Args:
        exctype: Exception-Typ
        value: Exception-Wert
        tb: Traceback
    """
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    print(error_msg)
    
    # Zeige Dialog mit Fehlermeldung
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle("Fehler")
    msg_box.setText("Ein unerwarteter Fehler ist aufgetreten:")
    msg_box.setDetailedText(error_msg)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec_()

def main():
    """Hauptfunktion der Anwendung"""
    # Erstelle QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Passwortmanager")
    app.setApplicationDisplayName("Passwortmanager")
    
    # Icon-Pfad
    app_icon = IconManager.get_icon('app')
    app.setWindowIcon(app_icon)
    
    # Globalen Exception-Handler setzen
    sys.excepthook = exception_hook
    
    # Hauptfenster erstellen und anzeigen
    window = MainWindow()
    window.show()
    
    # Event-Loop starten
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()