#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Login-Dialog für den Passwortmanager.
Enthält Dialoge für die Anmeldung und das Erstellen eines neuen Masterpassworts.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QFormLayout, QMessageBox)
from PyQt5.QtCore import Qt

from core.password_generator import PasswordGenerator
from gui.widgets.strength_meter import StrengthMeter
from gui.styles.resources import IconManager


class LoginDialog(QDialog):
    """Dialog für die Eingabe des Masterpassworts"""
    
    def __init__(self, parent=None, title="Masterpasswort eingeben"):
        """
        Initialisiert den Login-Dialog
        
        Args:
            parent (QWidget): Übergeordnetes Widget
            title (str): Titel des Dialogs
        """
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setMinimumWidth(350)
        self.setWindowIcon(IconManager.get_icon('lock'))
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Richtet die Benutzeroberfläche ein"""
        # Hauptlayout
        layout = QVBoxLayout(self)
        
        # Icon und Hinweistext
        header_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(IconManager.get_pixmap('lock').scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(icon_label)
        
        info_label = QLabel("Bitte geben Sie Ihr Masterpasswort ein,\num auf Ihre gesicherten Passwörter zuzugreifen.")
        info_label.setWordWrap(True)
        header_layout.addWidget(info_label, 1)
        
        layout.addLayout(header_layout)
        layout.addSpacing(10)
        
        # Passwort-Eingabe
        form_layout = QFormLayout()
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Masterpasswort")
        self.password_input.setMinimumWidth(250)
        
        form_layout.addRow("Masterpasswort:", self.password_input)
        layout.addLayout(form_layout)
        
        # Show Password Checkbox
        show_password_layout = QHBoxLayout()
        self.show_password_btn = QPushButton("Passwort anzeigen")
        self.show_password_btn.setCheckable(True)
        self.show_password_btn.toggled.connect(self._toggle_password_visibility)
        self.show_password_btn.setIcon(IconManager.get_icon('view'))
        show_password_layout.addStretch()
        show_password_layout.addWidget(self.show_password_btn)
        
        layout.addLayout(show_password_layout)
        layout.addSpacing(15)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("Anmelden")
        self.ok_button.setIcon(IconManager.get_icon('unlock'))
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setProperty("class", "save")
        
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.setIcon(IconManager.get_icon('cancel'))
        self.cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.ok_button)
        
        layout.addLayout(buttons_layout)
    
    def _toggle_password_visibility(self, show):
        """
        Schaltet die Passwort-Sichtbarkeit um
        
        Args:
            show (bool): True, um das Passwort anzuzeigen, False, um es zu verbergen
        """
        self.password_input.setEchoMode(QLineEdit.Normal if show else QLineEdit.Password)
    
    def get_password(self):
        """
        Gibt das eingegebene Masterpasswort zurück
        
        Returns:
            str: Das eingegebene Masterpasswort
        """
        return self.password_input.text()


class NewMasterPasswordDialog(QDialog):
    """Dialog zum Erstellen eines neuen Masterpassworts"""
    
    def __init__(self, parent=None):
        """
        Initialisiert den Dialog zum Erstellen eines neuen Masterpassworts
        
        Args:
            parent (QWidget): Übergeordnetes Widget
        """
        super().__init__(parent)
        
        self.setWindowTitle("Masterpasswort festlegen")
        self.setMinimumWidth(400)
        self.setWindowIcon(IconManager.get_icon('lock'))
        
        self.password_generator = PasswordGenerator()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Richtet die Benutzeroberfläche ein"""
        # Hauptlayout
        layout = QVBoxLayout(self)
        
        # Icon und Hinweistext
        header_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(IconManager.get_pixmap('lock').scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(icon_label)
        
        info_label = QLabel(
            "Bitte wählen Sie ein sicheres Masterpasswort.\n"
            "Dieses Passwort schützt alle Ihre gespeicherten Zugangsdaten.\n"
            "Es sollte mindestens 8 Zeichen lang sein und Groß-/Kleinbuchstaben,\n"
            "Zahlen und Sonderzeichen enthalten."
        )
        info_label.setWordWrap(True)
        header_layout.addWidget(info_label, 1)
        
        layout.addLayout(header_layout)
        layout.addSpacing(10)
        
        # Passwort-Eingabebereich
        form_layout = QFormLayout()
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Neues Masterpasswort")
        self.password_input.textChanged.connect(self._update_password_strength)
        
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setPlaceholderText("Passwort wiederholen")
        
        form_layout.addRow("Neues Masterpasswort:", self.password_input)
        form_layout.addRow("Passwort bestätigen:", self.confirm_input)
        
        layout.addLayout(form_layout)
        
        # Show Password Checkbox
        show_password_layout = QHBoxLayout()
        self.show_password_btn = QPushButton("Passwort anzeigen")
        self.show_password_btn.setCheckable(True)
        self.show_password_btn.toggled.connect(self._toggle_password_visibility)
        self.show_password_btn.setIcon(IconManager.get_icon('view'))
        show_password_layout.addStretch()
        show_password_layout.addWidget(self.show_password_btn)
        
        layout.addLayout(show_password_layout)
        
        # Passwortstärke-Anzeige
        layout.addSpacing(10)
        strength_label = QLabel("Passwortstärke:")
        layout.addWidget(strength_label)
        
        self.strength_meter = StrengthMeter()
        layout.addWidget(self.strength_meter)
        
        layout.addSpacing(15)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.generate_button = QPushButton("Passwort generieren")
        self.generate_button.setIcon(IconManager.get_icon('generate'))
        self.generate_button.clicked.connect(self._generate_master_password)
        
        self.ok_button = QPushButton("Speichern")
        self.ok_button.setIcon(IconManager.get_icon('save'))
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self._check_and_accept)
        self.ok_button.setProperty("class", "save")
        
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.setIcon(IconManager.get_icon('cancel'))
        self.cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.generate_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.ok_button)
        
        layout.addLayout(buttons_layout)
    
    def _toggle_password_visibility(self, show):
        """
        Schaltet die Passwort-Sichtbarkeit um
        
        Args:
            show (bool): True, um das Passwort anzuzeigen, False, um es zu verbergen
        """
        self.password_input.setEchoMode(QLineEdit.Normal if show else QLineEdit.Password)
        self.confirm_input.setEchoMode(QLineEdit.Normal if show else QLineEdit.Password)
    
    def _generate_master_password(self):
        """Generiert ein sicheres Masterpasswort"""
        password = self.password_generator.generate_password(length=16)
        
        self.password_input.setText(password)
        self.confirm_input.setText(password)
        
        QMessageBox.information(
            self,
            "Passwort generiert",
            "Ein sicheres Masterpasswort wurde generiert.\n"
            "Bitte merken Sie sich dieses Passwort gut!\n\n"
            f"Passwort: {password}"
        )
    
    def _update_password_strength(self):
        """Aktualisiert die Anzeige der Passwortstärke"""
        password = self.password_input.text()
        self.strength_meter.update_strength(password)
    
    def _check_and_accept(self):
        """Überprüft die Eingaben und akzeptiert den Dialog"""
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        
        if not password:
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie ein Passwort ein.")
            return
        
        if password != confirm:
            QMessageBox.warning(self, "Fehler", "Die Passwörter stimmen nicht überein.")
            return
        
        if len(password) < 8:
            QMessageBox.warning(
                self,
                "Schwaches Passwort",
                "Das Passwort ist zu kurz. Es sollte mindestens 8 Zeichen enthalten."
            )
            return
        
        # Überprüfe die Passwortstärke
        strength_info = self.strength_meter.get_strength_info()
        if strength_info and strength_info["score"] < 50:
            reply = QMessageBox.question(
                self,
                "Schwaches Passwort",
                "Das gewählte Passwort scheint nicht sehr sicher zu sein.\n"
                "Es wird empfohlen, ein stärkeres Passwort zu wählen.\n\n"
                "Möchten Sie dennoch fortfahren?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
        
        self.accept()
    
    def get_password(self):
        """
        Gibt das eingegebene Masterpasswort zurück
        
        Returns:
            str: Das eingegebene Masterpasswort
        """
        return self.password_input.text()