#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Passwort-Dialog für den Passwortmanager.
Enthält Dialog zum Hinzufügen und Bearbeiten von Passwörtern.
"""

from PyQt5.QtWidgets import (QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
                             QFormLayout, QLineEdit, QTextEdit, QComboBox, QPushButton,
                             QCheckBox, QLabel, QDateEdit, QMessageBox, QGroupBox)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon

from core.models import PasswordEntry, Category
from gui.widgets.strength_meter import StrengthMeter
from gui.styles.resources import IconManager


class PasswordDialog(QDialog):
    """Dialog zum Hinzufügen und Bearbeiten von Passwörtern"""
    
    def __init__(self, parent=None, encryption=None, categories=None, entry_data=None):
        """
        Initialisiert den Passwort-Dialog
        
        Args:
            parent (QWidget): Übergeordnetes Widget
            encryption (Encryption): Verschlüsselungsobjekt
            categories (Dict[int, Category]): Dictionary mit Kategorien (ID -> Category)
            entry_data (PasswordEntry, optional): Daten eines existierenden Eintrags zum Bearbeiten
        """
        super().__init__(parent)
        
        self.encryption = encryption
        self.categories = categories or {}
        self.entry_data = entry_data
        self.is_edit_mode = entry_data is not None
        
        title = "Passwort bearbeiten" if self.is_edit_mode else "Neues Passwort hinzufügen"
        self.setWindowTitle(title)
        self.setMinimumWidth(550)
        self.setMinimumHeight(450)
        
        self.init_ui()
        
        if self.is_edit_mode:
            self.load_entry_data()
    
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        main_layout = QVBoxLayout(self)
        
        # Tabs für verschiedene Passworttypen
        self.tabs = QTabWidget()
        
        # Tab für Website-Passwörter
        website_tab = QWidget()
        website_layout = QVBoxLayout(website_tab)
        
        # Formular für Website-Tab
        website_form = QFormLayout()
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Titel des Eintrags")
        website_form.addRow("Titel:", self.title_input)
        
        # Kategorie-Auswahl
        self.category_combo = QComboBox()
        self.category_combo.addItem("Keine Kategorie", None)
        for category_id, category in self.categories.items():
            self.category_combo.addItem(category.name, category_id)
        website_form.addRow("Kategorie:", self.category_combo)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Benutzername oder E-Mail")
        website_form.addRow("Benutzername/E-Mail:", self.username_input)
        
        # Passwort-Feld mit Anzeigen/Generieren-Buttons
        password_layout = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Passwort")
        self.password_input.textChanged.connect(self._update_password_strength)
        password_layout.addWidget(self.password_input, 1)
        
        self.show_password_btn = QPushButton()
        self.show_password_btn.setIcon(IconManager.get_icon('view'))
        self.show_password_btn.setToolTip("Passwort anzeigen")
        self.show_password_btn.setCheckable(True)
        self.show_password_btn.toggled.connect(self._toggle_password_visibility)
        self.show_password_btn.setFixedSize(36, 36)
        password_layout.addWidget(self.show_password_btn)
        
        self.generate_password_btn = QPushButton()
        self.generate_password_btn.setIcon(IconManager.get_icon('generate'))
        self.generate_password_btn.setToolTip("Passwort generieren")
        self.generate_password_btn.clicked.connect(lambda: self._show_generator_dialog(is_for_website=True))
        self.generate_password_btn.setFixedSize(36, 36)
        password_layout.addWidget(self.generate_password_btn)
        
        website_form.addRow("Passwort:", password_layout)
        
        # Passwortstärke-Anzeige
        self.strength_meter = StrengthMeter()
        website_form.addRow("Stärke:", self.strength_meter)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://beispiel.de")
        website_form.addRow("URL:", self.url_input)
        
        # Ablaufdatum
        self.expiry_date_checkbox = QCheckBox("Ablaufdatum festlegen")
        self.expiry_date_checkbox.toggled.connect(self._toggle_expiry_date)
        website_form.addRow("", self.expiry_date_checkbox)
        
        self.expiry_date_edit = QDateEdit()
        self.expiry_date_edit.setCalendarPopup(True)
        self.expiry_date_edit.setMinimumDate(QDate.currentDate())
        self.expiry_date_edit.setDate(QDate.currentDate().addMonths(3))  # Standardmäßig 3 Monate
        self.expiry_date_edit.setEnabled(False)
        website_form.addRow("Ablaufdatum:", self.expiry_date_edit)
        
        # Favorit
        self.favorite_checkbox = QCheckBox("Als Favorit markieren")
        website_form.addRow("", self.favorite_checkbox)
        
        website_layout.addLayout(website_form)
        
        # Notizen
        notes_group = QGroupBox("Notizen")
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Zusätzliche Informationen zu diesem Eintrag...")
        notes_layout.addWidget(self.notes_input)
        
        website_layout.addWidget(notes_group)
        
        self.tabs.addTab(website_tab, "Webseite")
        
        # Tab für Geräte-PINs
        device_tab = QWidget()
        device_layout = QVBoxLayout(device_tab)
        
        # Formular für Geräte-Tab
        device_form = QFormLayout()
        
        self.device_title_input = QLineEdit()
        self.device_title_input.setPlaceholderText("Name des Geräts")
        device_form.addRow("Gerätename:", self.device_title_input)
        
        self.device_category_combo = QComboBox()
        self.device_category_combo.addItem("Keine Kategorie", None)
        for category_id, category in self.categories.items():
            self.device_category_combo.addItem(category.name, category_id)
        device_form.addRow("Kategorie:", self.device_category_combo)
        
        self.device_type_input = QComboBox()
        self.device_type_input.addItems(["Handy", "Laptop", "Computer", "Tablet", "Smart TV", "Sonstiges"])
        device_form.addRow("Gerätetyp:", self.device_type_input)
        
        device_pin_layout = QHBoxLayout()
        self.device_pin_input = QLineEdit()
        self.device_pin_input.setEchoMode(QLineEdit.Password)
        self.device_pin_input.setPlaceholderText("PIN oder Passwort")
        self.device_pin_input.textChanged.connect(self._update_pin_strength)
        device_pin_layout.addWidget(self.device_pin_input, 1)
        
        self.show_pin_btn = QPushButton()
        self.show_pin_btn.setIcon(IconManager.get_icon('view'))
        self.show_pin_btn.setToolTip("PIN anzeigen")
        self.show_pin_btn.setCheckable(True)
        self.show_pin_btn.toggled.connect(self._toggle_pin_visibility)
        self.show_pin_btn.setFixedSize(36, 36)
        device_pin_layout.addWidget(self.show_pin_btn)
        
        self.generate_pin_btn = QPushButton()
        self.generate_pin_btn.setIcon(IconManager.get_icon('generate'))
        self.generate_pin_btn.setToolTip("PIN generieren")
        self.generate_pin_btn.clicked.connect(lambda: self._show_generator_dialog(is_for_website=False))
        self.generate_pin_btn.setFixedSize(36, 36)
        device_pin_layout.addWidget(self.generate_pin_btn)
        
        device_form.addRow("PIN/Passwort:", device_pin_layout)
        
        self.pin_strength_meter = StrengthMeter()
        device_form.addRow("Stärke:", self.pin_strength_meter)
        
        self.device_expiry_checkbox = QCheckBox("Ablaufdatum festlegen")
        self.device_expiry_checkbox.toggled.connect(self._toggle_device_expiry_date)
        device_form.addRow("", self.device_expiry_checkbox)
        
        self.device_expiry_date = QDateEdit()
        self.device_expiry_date.setCalendarPopup(True)
        self.device_expiry_date.setMinimumDate(QDate.currentDate())
        self.device_expiry_date.setDate(QDate.currentDate().addMonths(6))  # Standardmäßig 6 Monate für Geräte
        self.device_expiry_date.setEnabled(False)
        device_form.addRow("Ablaufdatum:", self.device_expiry_date)
        
        self.device_favorite_checkbox = QCheckBox("Als Favorit markieren")
        device_form.addRow("", self.device_favorite_checkbox)
        
        device_layout.addLayout(device_form)
        
        device_notes_group = QGroupBox("Notizen")
        device_notes_layout = QVBoxLayout(device_notes_group)
        
        self.device_notes_input = QTextEdit()
        self.device_notes_input.setPlaceholderText("Zusätzliche Informationen zu diesem Gerät...")
        device_notes_layout.addWidget(self.device_notes_input)
        
        device_layout.addWidget(device_notes_group)
        
        self.tabs.addTab(device_tab, "Gerät")
        
        main_layout.addWidget(self.tabs)
        
        buttons_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Speichern")
        self.save_button.setIcon(IconManager.get_icon('save'))
        self.save_button.clicked.connect(self.accept)
        self.save_button.setProperty("class", "save")
        
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.setIcon(IconManager.get_icon('cancel'))
        self.cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.save_button)
        
        main_layout.addLayout(buttons_layout)
        
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _toggle_password_visibility(self, show):
        self.password_input.setEchoMode(QLineEdit.Normal if show else QLineEdit.Password)

    def _toggle_pin_visibility(self, show):
        self.device_pin_input.setEchoMode(QLineEdit.Normal if show else QLineEdit.Password)

    def _update_password_strength(self):
        password = self.password_input.text()
        self.strength_meter.update_strength(password)

    def _update_pin_strength(self):
        pin = self.device_pin_input.text()
        self.pin_strength_meter.update_strength(pin)

    def _toggle_expiry_date(self, checked):
        self.expiry_date_edit.setEnabled(checked)

    def _toggle_device_expiry_date(self, checked):
        self.device_expiry_date.setEnabled(checked)

    def _on_tab_changed(self, index):
        if index == 0:
            if self.device_title_input.text() and not self.title_input.text():
                self.title_input.setText(self.device_title_input.text())
            device_idx = self.device_category_combo.currentIndex()
            if device_idx >= 0:
                self.category_combo.setCurrentIndex(device_idx)
            if self.device_favorite_checkbox.isChecked():
                self.favorite_checkbox.setChecked(True)
        else:
            if self.title_input.text() and not self.device_title_input.text():
                self.device_title_input.setText(self.title_input.text())
            web_idx = self.category_combo.currentIndex()
            if web_idx >= 0:
                self.device_category_combo.setCurrentIndex(web_idx)
            if self.favorite_checkbox.isChecked():
                self.device_favorite_checkbox.setChecked(True)

    def _show_generator_dialog(self, is_for_website=True):
        from gui.dialogs.generator_dialog import GeneratePasswordDialog, GeneratePINDialog
        if is_for_website:
            dialog = GeneratePasswordDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                pwd = dialog.get_generated_password()
                if pwd:
                    self.password_input.setText(pwd)
                    self._update_password_strength()
        else:
            dialog = GeneratePINDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                pin = dialog.get_generated_pin()
                if pin:
                    self.device_pin_input.setText(pin)
                    self._update_pin_strength()

    def load_entry_data(self):
        if not self.entry_data:
            return
        if self.entry_data.url:
            self.tabs.setCurrentIndex(0)
            self.title_input.setText(self.entry_data.title)
            self.username_input.setText(self.entry_data.username or "")
            self.password_input.setText(self.entry_data.password)
            self.url_input.setText(self.entry_data.url)
            self.notes_input.setText(self.entry_data.notes or "")
            if self.entry_data.category_id is not None:
                for i in range(self.category_combo.count()):
                    if self.category_combo.itemData(i) == self.entry_data.category_id:
                        self.category_combo.setCurrentIndex(i)
                        break
            if self.entry_data.expiry_date:
                self.expiry_date_checkbox.setChecked(True)
                self.expiry_date_edit.setDate(QDate.fromString(self.entry_data.expiry_date.strftime('%Y-%m-%d'), 'yyyy-MM-dd'))
            self.favorite_checkbox.setChecked(self.entry_data.is_favorite)
        elif self.entry_data.device_type:
            self.tabs.setCurrentIndex(1)
            self.device_title_input.setText(self.entry_data.title)
            idx = self.device_type_input.findText(self.entry_data.device_type)
            if idx >= 0:
                self.device_type_input.setCurrentIndex(idx)
            self.device_pin_input.setText(self.entry_data.password)
            self.device_notes_input.setText(self.entry_data.notes or "")
            if self.entry_data.category_id is not None:
                for i in range(self.device_category_combo.count()):
                    if self.device_category_combo.itemData(i) == self.entry_data.category_id:
                        self.device_category_combo.setCurrentIndex(i)
                        break
            if self.entry_data.expiry_date:
                self.device_expiry_checkbox.setChecked(True)
                self.device_expiry_date.setDate(QDate.fromString(self.entry_data.expiry_date.strftime('%Y-%m-%d'), 'yyyy-MM-dd'))
            self.device_favorite_checkbox.setChecked(self.entry_data.is_favorite)
        else:
            self.tabs.setCurrentIndex(0)
            self.title_input.setText(self.entry_data.title)
            self.username_input.setText(self_entry_data.username or "")
            self.password_input.setText(self.entry_data.password)
            self.notes_input.setText(self.entry_data.notes or "")
            if self.entry_data.category_id is not None:
                for i in range(self.category_combo.count()):
                    if self.category_combo.itemData(i) == self.entry_data.category_id:
                        self.category_combo.setCurrentIndex(i)
                        break
            if self.entry_data.expiry_date:
                self.expiry_date_checkbox.setChecked(True)
                self.expiry_date_edit.setDate(QDate.fromString(self.entry_data.expiry_date.strftime('%Y-%m-%d'), 'yyyy-MM-dd'))
            self.favorite_checkbox.setChecked(self_entry_data.is_favorite)
        self._update_password_strength()
        self._update_pin_strength()

    def get_data(self):
        current_tab = self.tabs.currentIndex()
        if current_tab == 0:
            category_id = self.category_combo.currentData()
            expiry_date = None
            if self.expiry_date_checkbox.isChecked():
                expiry_date = self.expiry_date_edit.date().toPyDate()
            return {
                'title': self.title_input.text(),
                'username': self.username_input.text(),
                'password': self.password_input.text(),
                'url': self.url_input.text(),
                'device_type': None,
                'notes': self.notes_input.toPlainText(),
                'category_id': category_id,
                'is_favorite': self.favorite_checkbox.isChecked(),
                'expiry_date': expiry_date
            }
        else:
            category_id = self.device_category_combo.currentData()
            expiry_date = None
            if self.device_expiry_checkbox.isChecked():
                expiry_date = self.device_expiry_date.date().toPyDate()
            return {
                'title': self.device_title_input.text(),
                'username': None,
                'password': self.device_pin_input.text(),
                'url': None,
                'device_type': self.device_type_input.currentText(),
                'notes': self.device_notes_input.toPlainText(),
                'category_id': category_id,
                'is_favorite': self.device_favorite_checkbox.isChecked(),
                'expiry_date': expiry_date
            }

    def accept(self):
        """Überprüft die Eingaben und akzeptiert den Dialog"""
        data = self.get_data()
        if not data['title']:
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie einen Titel ein.")
            return
        if not data['password']:
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie ein Passwort ein.")
            return
        if self.tabs.currentIndex() == 0 and not data['username'] and not data['url']:
            reply = QMessageBox.question(
                self,
                "Bestätigung",
                "Es wurde kein Benutzername und keine URL eingegeben. Möchten Sie fortfahren?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        super().accept()
