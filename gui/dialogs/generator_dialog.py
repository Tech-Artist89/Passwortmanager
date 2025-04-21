#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generator-Dialog für den Passwortmanager.
Enthält Dialoge zum Generieren von Passwörtern und PINs.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QComboBox, QCheckBox,
                            QSpinBox, QGroupBox, QRadioButton, QApplication,
                            QMessageBox, QSlider)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.password_generator import PasswordGenerator
from gui.widgets.strength_meter import StrengthMeter
from gui.styles.resources import IconManager


class GeneratePasswordDialog(QDialog):
    """Dialog zum Generieren von Passwörtern"""
    
    def __init__(self, parent=None):
        """
        Initialisiert den Passwort-Generator-Dialog
        
        Args:
            parent (QWidget): Übergeordnetes Widget
        """
        super().__init__(parent)
        
        self.setWindowTitle("Passwort generieren")
        self.setMinimumWidth(500)
        self.setWindowIcon(IconManager.get_icon('generate'))
        
        self.generator = PasswordGenerator()
        self.generated_password = ""
        
        self.init_ui()
    
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        
        # Passworttyp auswählen
        type_group = QGroupBox("Passworttyp")
        type_layout = QVBoxLayout(type_group)
        
        self.complex_radio = QRadioButton("Komplexes Passwort (schwer zu merken, sehr sicher)")
        self.complex_radio.setChecked(True)
        self.complex_radio.toggled.connect(self._toggle_password_type)
        
        self.memorable_radio = QRadioButton("Merkbares Passwort (leichter zu merken, trotzdem sicher)")
        self.memorable_radio.toggled.connect(self._toggle_password_type)
        
        type_layout.addWidget(self.complex_radio)
        type_layout.addWidget(self.memorable_radio)
        layout.addWidget(type_group)
        
        # Optionen für komplexes Passwort
        self.complex_options = QGroupBox("Optionen für komplexes Passwort")
        complex_layout = QVBoxLayout(self.complex_options)
        
        length_layout = QHBoxLayout()
        length_label = QLabel("Passwortlänge:")
        length_layout.addWidget(length_label)
        
        self.length_combo = QComboBox()
        self.length_combo.addItems(["8", "12", "16", "32"])
        self.length_combo.setCurrentIndex(2)  # Default: 16
        self.length_combo.currentTextChanged.connect(self.generate)
        length_layout.addWidget(self.length_combo)
        
        complex_layout.addLayout(length_layout)
        
        self.uppercase_check = QCheckBox("Großbuchstaben verwenden (A-Z)")
        self.uppercase_check.setChecked(True)
        self.uppercase_check.toggled.connect(self.generate)
        complex_layout.addWidget(self.uppercase_check)
        
        self.special_check = QCheckBox("Sonderzeichen verwenden (!@#$%&*)")
        self.special_check.setChecked(True)
        self.special_check.toggled.connect(self.generate)
        complex_layout.addWidget(self.special_check)
        
        layout.addWidget(self.complex_options)
        
        # Optionen für merkbares Passwort
        self.memorable_options = QGroupBox("Optionen für merkbares Passwort")
        memorable_layout = QVBoxLayout(self.memorable_options)
        
        word_count_layout = QHBoxLayout()
        word_count_label = QLabel("Anzahl der Wörter:")
        word_count_layout.addWidget(word_count_label)
        
        self.word_count_combo = QComboBox()
        self.word_count_combo.addItems(["2", "3", "4"])
        self.word_count_combo.setCurrentIndex(1)  # Default: 3
        self.word_count_combo.currentTextChanged.connect(self.generate)
        word_count_layout.addWidget(self.word_count_combo)
        
        memorable_layout.addLayout(word_count_layout)
        
        separator_layout = QHBoxLayout()
        separator_label = QLabel("Trennzeichen:")
        separator_layout.addWidget(separator_label)
        
        self.separator_combo = QComboBox()
        self.separator_combo.addItems(["-", "_", ".", ",", " ", "+"])
        self.separator_combo.currentTextChanged.connect(self.generate)
        separator_layout.addWidget(self.separator_combo)
        
        memorable_layout.addLayout(separator_layout)
        
        self.capitalize_check = QCheckBox("Wörter großschreiben")
        self.capitalize_check.setChecked(True)
        self.capitalize_check.toggled.connect(self.generate)
        memorable_layout.addWidget(self.capitalize_check)
        
        self.add_number_check = QCheckBox("Zahl am Ende hinzufügen")
        self.add_number_check.setChecked(True)
        self.add_number_check.toggled.connect(self.generate)
        memorable_layout.addWidget(self.add_number_check)
        
        self.memorable_options.setVisible(False)
        layout.addWidget(self.memorable_options)
        
        # Passwort-Anzeige
        password_group = QGroupBox("Generiertes Passwort")
        password_layout = QVBoxLayout(password_group)
        
        self.password_display = QLineEdit()
        self.password_display.setReadOnly(True)
        font = QFont("Courier New", 12)
        self.password_display.setFont(font)
        self.password_display.setAlignment(Qt.AlignCenter)
        password_layout.addWidget(self.password_display)
        
        # Stärkeanzeige
        self.strength_meter = StrengthMeter()
        password_layout.addWidget(self.strength_meter)
        
        # Buttons für das generierte Passwort
        password_buttons = QHBoxLayout()
        
        generate_button = QPushButton("Neu generieren")
        generate_button.setIcon(IconManager.get_icon('generate'))
        generate_button.clicked.connect(self.generate)
        password_buttons.addWidget(generate_button)
        
        copy_button = QPushButton("Kopieren")
        copy_button.setIcon(IconManager.get_icon('copy'))
        copy_button.clicked.connect(self.copy_to_clipboard)
        password_buttons.addWidget(copy_button)
        
        password_layout.addLayout(password_buttons)
        layout.addWidget(password_group)
        
        # Dialog-Buttons
        buttons_layout = QHBoxLayout()
        
        use_button = QPushButton("Verwenden")
        use_button.setIcon(IconManager.get_icon('save'))
        use_button.clicked.connect(self.accept)
        use_button.setProperty("class", "save")
        
        cancel_button = QPushButton("Abbrechen")
        cancel_button.setIcon(IconManager.get_icon('cancel'))
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(use_button)
        
        layout.addLayout(buttons_layout)
        
        # Initial ein Passwort generieren
        self.generate()
    
    def _toggle_password_type(self, checked):
        """
        Schaltet zwischen komplexem und merkbarem Passwort um
        
        Args:
            checked (bool): Ob der Radio-Button aktiv ist
        """
        if self.complex_radio.isChecked():
            self.complex_options.setVisible(True)
            self.memorable_options.setVisible(False)
        else:
            self.complex_options.setVisible(False)
            self.memorable_options.setVisible(True)
        
        self.generate()
    
    def generate(self):
        """Generiert ein neues Passwort basierend auf den gewählten Optionen"""
        if self.complex_radio.isChecked():
            # Komplexes Passwort generieren
            length = int(self.length_combo.currentText())
            use_uppercase = self.uppercase_check.isChecked()
            use_special = self.special_check.isChecked()
            
            self.generated_password = self.generator.generate_password(
                length=length,
                use_uppercase=use_uppercase,
                use_special=use_special
            )
        else:
            # Merkbares Passwort generieren
            word_count = int(self.word_count_combo.currentText())
            separator = self.separator_combo.currentText()
            capitalize = self.capitalize_check.isChecked()
            add_number = self.add_number_check.isChecked()
            
            self.generated_password = self.generator.generate_memorable_password(
                word_count=word_count,
                separator=separator,
                capitalize=capitalize,
                add_number=add_number
            )
        
        # Passwort anzeigen
        self.password_display.setText(self.generated_password)
        
        # Stärke aktualisieren
        self.strength_meter.update_strength(self.generated_password)
    
    def copy_to_clipboard(self):
        """Kopiert das generierte Passwort in die Zwischenablage"""
        if not self.generated_password:
            return
            
        QApplication.clipboard().setText(self.generated_password)
        QMessageBox.information(self, "Info", "Passwort in die Zwischenablage kopiert!")
    
    def get_generated_password(self):
        """
        Gibt das generierte Passwort zurück
        
        Returns:
            str: Das generierte Passwort
        """
        return self.generated_password


class GeneratePINDialog(QDialog):
    """Dialog zum Generieren von PINs"""
    
    def __init__(self, parent=None):
        """
        Initialisiert den PIN-Generator-Dialog
        
        Args:
            parent (QWidget): Übergeordnetes Widget
        """
        super().__init__(parent)
        
        self.setWindowTitle("PIN generieren")
        self.setMinimumWidth(400)
        self.setWindowIcon(IconManager.get_icon('generate'))
        
        self.generator = PasswordGenerator()
        self.generated_pin = ""
        
        self.init_ui()
    
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        
        # Optionen
        options_group = QGroupBox("PIN-Optionen")
        options_layout = QVBoxLayout(options_group)
        
        # PIN-Länge
        length_layout = QHBoxLayout()
        length_label = QLabel("PIN-Länge:")
        length_layout.addWidget(length_label)
        
        self.length_slider = QSlider(Qt.Horizontal)
        self.length_slider.setRange(4, 8)
        self.length_slider.setValue(4)
        self.length_slider.setTickPosition(QSlider.TicksBelow)
        self.length_slider.setTickInterval(1)
        self.length_slider.valueChanged.connect(self._update_length_label)
        self.length_slider.valueChanged.connect(self.generate)
        length_layout.addWidget(self.length_slider)
        
        self.length_value_label = QLabel("4")
        length_layout.addWidget(self.length_value_label)
        
        options_layout.addLayout(length_layout)
        
        # Buchstaben verwenden
        self.letters_check = QCheckBox("Auch Buchstaben verwenden (nicht nur Zahlen)")
        self.letters_check.toggled.connect(self.generate)
        options_layout.addWidget(self.letters_check)
        
        layout.addWidget(options_group)
        
        # PIN-Anzeige
        pin_group = QGroupBox("Generierte PIN")
        pin_layout = QVBoxLayout(pin_group)
        
        self.pin_display = QLineEdit()
        self.pin_display.setReadOnly(True)
        font = QFont("Courier New", 14)
        self.pin_display.setFont(font)
        self.pin_display.setAlignment(Qt.AlignCenter)
        pin_layout.addWidget(self.pin_display)
        
        # Stärkeanzeige
        self.strength_meter = StrengthMeter()
        pin_layout.addWidget(self.strength_meter)
        
        # Buttons für die generierte PIN
        pin_buttons = QHBoxLayout()
        
        generate_button = QPushButton("Neu generieren")
        generate_button.setIcon(IconManager.get_icon('generate'))
        generate_button.clicked.connect(self.generate)
        pin_buttons.addWidget(generate_button)
        
        copy_button = QPushButton("Kopieren")
        copy_button.setIcon(IconManager.get_icon('copy'))
        copy_button.clicked.connect(self.copy_to_clipboard)
        pin_buttons.addWidget(copy_button)
        
        pin_layout.addLayout(pin_buttons)
        layout.addWidget(pin_group)
        
        # Dialog-Buttons
        buttons_layout = QHBoxLayout()
        
        use_button = QPushButton("Verwenden")
        use_button.setIcon(IconManager.get_icon('save'))
        use_button.clicked.connect(self.accept)
        use_button.setProperty("class", "save")
        
        cancel_button = QPushButton("Abbrechen")
        cancel_button.setIcon(IconManager.get_icon('cancel'))
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(use_button)
        
        layout.addLayout(buttons_layout)
        
        # Initial eine PIN generieren
        self.generate()
    
    def _update_length_label(self, value):
        """
        Aktualisiert das Label für die PIN-Länge
        
        Args:
            value (int): Neue Länge
        """
        self.length_value_label.setText(str(value))
    
    def generate(self):
        """Generiert eine neue PIN basierend auf den gewählten Optionen"""
        length = self.length_slider.value()
        use_letters = self.letters_check.isChecked()
        
        self.generated_pin = self.generator.generate_pin(
            length=length,
            use_letters=use_letters
        )
        
        # PIN anzeigen
        self.pin_display.setText(self.generated_pin)
        
        # Stärke aktualisieren
        self.strength_meter.update_strength(self.generated_pin)
    
    def copy_to_clipboard(self):
        """Kopiert die generierte PIN in die Zwischenablage"""
        if not self.generated_pin:
            return
            
        QApplication.clipboard().setText(self.generated_pin)
        QMessageBox.information(self, "Info", "PIN in die Zwischenablage kopiert!")
    
    def get_generated_pin(self):
        """
        Gibt die generierte PIN zurück
        
        Returns:
            str: Die generierte PIN
        """
        return self.generated_pin