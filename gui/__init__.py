#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GUI-Modul des Passwortmanagers.
Enthält die Komponenten für die grafische Benutzeroberfläche.
"""

# Importiere Untermodule
from gui.widgets import *
from gui.dialogs import *
from gui.styles import *

# Diese Datei wird aktualisiert, sobald die MainWindow-Klasse implementiert ist
from gui.main_window import MainWindow

__all__ = [
    # MainWindow wird später hinzugefügt
    'MainWindow',
    
    # Widgets
    'PasswordTable',
    'CategoryTree',
    'StrengthMeter',
    
    # Dialoge
    'LoginDialog',
    'NewMasterPasswordDialog',
    'PasswordDialog',
    'GeneratePasswordDialog',
    'GeneratePINDialog',
    'SettingsDialog',
    'AboutDialog',
    
    # Styles
    'Themes',
    'IconManager'
]