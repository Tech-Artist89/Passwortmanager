#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dialogs-Modul des Passwortmanagers.
Enthält die verschiedenen Dialog-Fenster der Anwendung.
"""

from gui.dialogs.login_dialog import LoginDialog, NewMasterPasswordDialog
from gui.dialogs.password_dialog import PasswordDialog
from gui.dialogs.generator_dialog import GeneratePasswordDialog, GeneratePINDialog
from gui.dialogs.settings_dialog import SettingsDialog
from gui.dialogs.about_dialog import AboutDialog

__all__ = [
    'LoginDialog',
    'NewMasterPasswordDialog',
    'PasswordDialog',
    'GeneratePasswordDialog',
    'GeneratePINDialog',
    'SettingsDialog',
    'AboutDialog'
]