#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Einstellungs-Dialog für den Passwortmanager.
Ermöglicht die Konfiguration verschiedener Anwendungseinstellungen.
"""

import os
from PyQt5.QtWidgets import (QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
                             QFormLayout, QLineEdit, QComboBox, QPushButton, QCheckBox,
                             QSpinBox, QLabel, QFileDialog, QListWidget, QAbstractItemView,
                             QGroupBox, QRadioButton, QMessageBox, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal

from core.models import AppSettings
from gui.styles.resources import IconManager


class SettingsDialog(QDialog):
    """Dialog für die Anwendungseinstellungen"""
    
    # Signal für Änderungen an den Einstellungen
    settings_changed = pyqtSignal(AppSettings)
    
    def __init__(self, parent=None, settings=None):
        """
        Initialisiert den Einstellungs-Dialog
        
        Args:
            parent (QWidget): Übergeordnetes Widget
            settings (AppSettings): Aktuelle Einstellungen
        """
        super().__init__(parent)
        
        self.setWindowTitle("Einstellungen")
        self.setMinimumWidth(600)
        self.setMinimumHeight(450)
        self.setWindowIcon(IconManager.get_icon('settings'))
        
        self.settings = settings or AppSettings()
        
        self.available_columns = [
            {"name": "title", "title": "Titel", "required": True},
            {"name": "username", "title": "Benutzername", "required": False},
            {"name": "url", "title": "URL/Gerät", "required": False},
            {"name": "category", "title": "Kategorie", "required": False},
            {"name": "favorite", "title": "Favorit", "required": False},
            {"name": "expiry", "title": "Ablaufdatum", "required": False},
            {"name": "updated_at", "title": "Geändert", "required": False},
            {"name": "actions", "title": "Aktionen", "required": True},
        ]
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        
        # Tabs für verschiedene Einstellungskategorien
        self.tabs = QTabWidget()
        
        # Aussehen-Tab
        appearance_tab = QWidget()
        appearance_layout = QVBoxLayout(appearance_tab)
        
        # Theme-Einstellungen
        theme_group = QGroupBox("Farbschema")
        theme_layout = QVBoxLayout(theme_group)
        
        self.light_theme_radio = QRadioButton("Helles Theme")
        self.dark_theme_radio = QRadioButton("Dunkles Theme")
        
        theme_layout.addWidget(self.light_theme_radio)
        theme_layout.addWidget(self.dark_theme_radio)
        
        appearance_layout.addWidget(theme_group)
        
        # Sprache
        language_group = QGroupBox("Sprache")
        language_layout = QFormLayout(language_group)
        
        self.language_combo = QComboBox()
        self.language_combo.addItem("Deutsch", "de")
        self.language_combo.addItem("Englisch", "en")
        
        language_layout.addRow("Sprache der Benutzeroberfläche:", self.language_combo)
        
        appearance_layout.addWidget(language_group)
        
        # Tabellenspalten-Einstellungen
        columns_group = QGroupBox("Sichtbare Tabellenspalten")
        columns_layout = QVBoxLayout(columns_group)
        
        self.columns_list = QListWidget()
        self.columns_list.setSelectionMode(QAbstractItemView.MultiSelection)
        
        for column in self.available_columns:
            item = self.columns_list.addItem(column["title"])
            # Markiere erforderliche Spalten als nicht auswählbar
            if column["required"]:
                self.columns_list.item(self.columns_list.count() - 1).setFlags(
                    self.columns_list.item(self.columns_list.count() - 1).flags() & ~Qt.ItemIsEnabled
                )
        
        columns_layout.addWidget(self.columns_list)
        
        appearance_layout.addWidget(columns_group)
        appearance_layout.addStretch()
        
        self.tabs.addTab(appearance_tab, "Aussehen")
        
        # Sicherheits-Tab
        security_tab = QWidget()
        security_layout = QVBoxLayout(security_tab)
        
        # Auto-Lock-Einstellungen
        lock_group = QGroupBox("Automatische Sperre")
        lock_layout = QVBoxLayout(lock_group)
        
        self.auto_lock_checkbox = QCheckBox("Automatisch sperren bei Inaktivität")
        self.auto_lock_checkbox.toggled.connect(self._toggle_auto_lock)
        lock_layout.addWidget(self.auto_lock_checkbox)
        
        time_layout = QHBoxLayout()
        self.auto_lock_time_spin = QSpinBox()
        self.auto_lock_time_spin.setMinimum(1)
        self.auto_lock_time_spin.setMaximum(60)
        self.auto_lock_time_spin.setValue(5)
        self.auto_lock_time_spin.setSuffix(" Minuten")
        time_layout.addWidget(QLabel("Zeit bis zur automatischen Sperre:"))
        time_layout.addWidget(self.auto_lock_time_spin)
        time_layout.addStretch()
        
        lock_layout.addLayout(time_layout)
        
        security_layout.addWidget(lock_group)
        
        # Datenbankeinstellungen
        db_group = QGroupBox("Datenbank")
        db_layout = QFormLayout(db_group)
        
        db_path_layout = QHBoxLayout()
        self.db_path_input = QLineEdit()
        self.db_path_input.setReadOnly(True)
        db_path_layout.addWidget(self.db_path_input, 1)
        
        self.db_path_button = QPushButton("Durchsuchen...")
        self.db_path_button.clicked.connect(self._browse_db_path)
        db_path_layout.addWidget(self.db_path_button)
        
        db_layout.addRow("Datenbankpfad:", db_path_layout)
        
        security_layout.addWidget(db_group)
        
        # Backup-Einstellungen
        backup_group = QGroupBox("Backup")
        backup_layout = QGridLayout(backup_group)
        
        self.auto_backup_checkbox = QCheckBox("Automatisches Backup beim Beenden erstellen")
        backup_layout.addWidget(self.auto_backup_checkbox, 0, 0, 1, 2)
        
        backup_layout.addWidget(QLabel("Maximale Anzahl Backups:"), 1, 0)
        self.max_backups_spin = QSpinBox()
        self.max_backups_spin.setMinimum(1)
        self.max_backups_spin.setMaximum(20)
        self.max_backups_spin.setValue(5)
        backup_layout.addWidget(self.max_backups_spin, 1, 1)
        
        self.backup_now_button = QPushButton("Jetzt sichern...")
        self.backup_now_button.clicked.connect(self._backup_now)
        backup_layout.addWidget(self.backup_now_button, 2, 0, 1, 2)
        
        security_layout.addWidget(backup_group)
        security_layout.addStretch()
        
        self.tabs.addTab(security_tab, "Sicherheit")
        
        # Füge die Tabs zum Layout hinzu
        layout.addWidget(self.tabs)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Speichern")
        self.save_button.setIcon(IconManager.get_icon('save'))
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setProperty("class", "save")
        
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.setIcon(IconManager.get_icon('cancel'))
        self.cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.save_button)
        
        layout.addLayout(buttons_layout)
    
    def _toggle_auto_lock(self, checked):
        """
        Aktiviert/deaktiviert die Auto-Lock-Zeit
        
        Args:
            checked (bool): Ob Auto-Lock aktiviert ist
        """
        self.auto_lock_time_spin.setEnabled(checked)
    
    def _browse_db_path(self):
        """Öffnet den Datei-Dialog zum Auswählen des Datenbankpfads"""
        current_path = self.db_path_input.text()
        current_dir = os.path.dirname(current_path) if current_path else ""
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Datenbank speichern unter",
            current_dir,
            "SQLite-Datenbank (*.db);;Alle Dateien (*.*)"
        )
        
        if file_path:
            # Stelle sicher, dass die Erweiterung .db angehängt wird
            if not file_path.endswith(".db"):
                file_path += ".db"
            
            self.db_path_input.setText(file_path)
    
    def _backup_now(self):
        """Erzeugt ein Backup der Datenbank"""
        # Diese Methode sendet nur ein Signal, die eigentliche Backup-Funktionalität
        # wird in der Hauptanwendung implementiert
        QMessageBox.information(
            self,
            "Backup",
            "Diese Funktion ist über den Einstellungsdialog noch nicht verfügbar.\n"
            "Bitte verwenden Sie stattdessen die Option 'Backup erstellen' im Datei-Menü."
        )
    
    def load_settings(self):
        """Lädt die aktuellen Einstellungen in die UI"""
        # Theme
        if self.settings.theme == "dark":
            self.dark_theme_radio.setChecked(True)
        else:
            self.light_theme_radio.setChecked(True)
        
        # Sprache
        index = self.language_combo.findData(self.settings.language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        
        # Sichtbare Spalten
        for i in range(self.columns_list.count()):
            item = self.columns_list.item(i)
            column_name = self.available_columns[i]["name"]
            
            # Markiere Spalten, die sichtbar sein sollen
            if column_name in self.settings.visible_columns:
                item.setSelected(True)
            
            # Deaktiviere Auswahl für erforderliche Spalten
            if self.available_columns[i]["required"]:
                item.setSelected(True)
        
        # Auto-Lock
        self.auto_lock_checkbox.setChecked(self.settings.auto_lock_enabled)
        self.auto_lock_time_spin.setValue(self.settings.auto_lock_time)
        self.auto_lock_time_spin.setEnabled(self.settings.auto_lock_enabled)
        
        # Datenbankpfad
        self.db_path_input.setText(self.settings.db_path)
    
    def save_settings(self):
        """Speichert die Einstellungen und akzeptiert den Dialog"""
        # Theme
        self.settings.theme = "dark" if self.dark_theme_radio.isChecked() else "light"
        
        # Sprache
        self.settings.language = self.language_combo.currentData()
        
        # Sichtbare Spalten
        visible_columns = []
        for i in range(self.columns_list.count()):
            item = self.columns_list.item(i)
            if item.isSelected():
                column_name = self.available_columns[i]["name"]
                visible_columns.append(column_name)
        
        # Stelle sicher, dass erforderliche Spalten immer sichtbar sind
        for column in self.available_columns:
            if column["required"] and column["name"] not in visible_columns:
                visible_columns.append(column["name"])
        
        self.settings.visible_columns = visible_columns
        
        # Auto-Lock
        self.settings.auto_lock_enabled = self.auto_lock_checkbox.isChecked()
        self.settings.auto_lock_time = self.auto_lock_time_spin.value()
        
        # Datenbankpfad
        self.settings.db_path = self.db_path_input.text()
        
        # Signal senden und Dialog schließen
        self.settings_changed.emit(self.settings)
        self.accept()
    
    def get_settings(self):
        """
        Gibt die aktualisierten Einstellungen zurück
        
        Returns:
            AppSettings: Die aktualisierten Einstellungen
        """
        return self.settings