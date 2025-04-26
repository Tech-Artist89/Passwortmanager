#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hauptfenster des Passwortmanagers.
Bildet die zentrale Komponente der Benutzeroberfläche.
"""

import os
import datetime
import sys
from typing import Dict, List, Optional

from PyQt5.QtWidgets import (QMainWindow, QAction, QWidget, QVBoxLayout, QHBoxLayout,
                            QSplitter, QMessageBox, QLineEdit, QPushButton, QLabel,
                            QStatusBar, QMenu, QToolBar, QComboBox, QApplication,
                            QFileDialog, QCheckBox)
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSlot
from PyQt5.QtGui import QIcon, QCloseEvent

from core.encryption import Encryption
from core.storage import Storage
from core.models import PasswordEntry, Category, AppSettings
from core.password_generator import PasswordGenerator

from gui.widgets.password_table import PasswordTable
from gui.widgets.category_tree import CategoryTree
from gui.dialogs.login_dialog import LoginDialog, NewMasterPasswordDialog
from gui.dialogs.password_dialog import PasswordDialog
from gui.dialogs.generator_dialog import GeneratePasswordDialog, GeneratePINDialog
from gui.dialogs.settings_dialog import SettingsDialog
from gui.dialogs.about_dialog import AboutDialog
from gui.styles.themes import Themes
from gui.styles.resources import IconManager

from utils.helpers import (format_date, get_resource_path, is_expired, days_until_expiry,
                         get_non_empty_fields)
from utils.import_export import export_to_csv, export_to_json, import_from_csv, import_from_json
from utils.backup import create_backup, restore_backup, get_backup_list, create_scheduled_backup


class MainWindow(QMainWindow):
    """Hauptfenster des Passwortmanagers"""
    
    def __init__(self):
        """Initialisiert das Hauptfenster"""
        super().__init__()
        
        # Anwendungsstatus
        self.storage = Storage()
        self.encryption = None
        self.settings = None
        self.generator = PasswordGenerator()
        
        # Daten
        self.categories: Dict[int, Category] = {}
        self.current_category_id = None
        self.show_favorites_only = False
        
        # Inaktivitäts-Timer
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.timeout.connect(self.lock_application)
        
        # UI initialisieren
        self.init_ui()
        
        # Masterpasswort überprüfen
        self.check_master_password()
    
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        self.setWindowTitle("Passwortmanager")
        self.setGeometry(100, 100, 1000, 600)
        self.setWindowIcon(IconManager.get_icon('app'))
        
        # Hauptwidget und Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Toolbar
        self.create_toolbar()
        
        # Suchleiste
        search_layout = QHBoxLayout()
        
        search_label = QLabel("Suche:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Suchbegriff eingeben...")
        self.search_input.textChanged.connect(self.search_passwords)
        
        search_button = QPushButton()
        search_button.setIcon(IconManager.get_icon('search'))
        search_button.setToolTip("Suchen")
        search_button.clicked.connect(lambda: self.search_passwords(self.search_input.text()))
        
        self.show_favorites_checkbox = QCheckBox("Nur Favoriten anzeigen")
        self.show_favorites_checkbox.toggled.connect(self.toggle_favorites)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(search_button)
        search_layout.addWidget(self.show_favorites_checkbox)
        
        main_layout.addLayout(search_layout)
        
        # Splitter für Kategorien und Passwörter
        splitter = QSplitter(Qt.Horizontal)
        
        # Kategorien-Bereich
        self.category_tree = CategoryTree()
        self.category_tree.setMinimumWidth(200)
        self.category_tree.setMaximumWidth(300)
        
        # Verbinde Kategorie-Signale
        self.category_tree.category_selected.connect(self.filter_by_category)
        self.category_tree.all_entries_selected.connect(self.show_all_entries)
        self.category_tree.favorites_selected.connect(self.show_favorites)
        self.category_tree.category_added.connect(self.add_category)
        self.category_tree.category_edited.connect(self.edit_category)
        self.category_tree.category_deleted.connect(self.delete_category)
        
        splitter.addWidget(self.category_tree)
        
        # Passwort-Tabelle
        self.password_table = PasswordTable()
        
        # Verbinde Passwort-Signale
        self.password_table.view_password.connect(self.view_password)
        self.password_table.edit_password.connect(self.edit_password)
        self.password_table.delete_password.connect(self.delete_password)
        self.password_table.copy_password.connect(self.copy_password_to_clipboard)
        self.password_table.toggle_favorite.connect(self.toggle_password_favorite)
        self.password_table.category_changed.connect(self.change_password_category)
        
        splitter.addWidget(self.password_table)
        
        # Größenverhältnis festlegen
        splitter.setSizes([1, 3])
        
        main_layout.addWidget(splitter)
        
        # Statusleiste
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Bereit")
        
        # Menüs erstellen
        self.create_menus()
    
    def create_menus(self):
        """Erstellt die Menüs der Anwendung"""
        # Hauptmenü
        menu_bar = self.menuBar()
        
        # Datei-Menü
        file_menu = menu_bar.addMenu("&Datei")
        
        new_password_action = QAction(IconManager.get_icon('add'), "Neues Passwort", self)
        new_password_action.setShortcut("Ctrl+N")
        new_password_action.triggered.connect(self.add_new_password)
        file_menu.addAction(new_password_action)
        
        generate_password_action = QAction(IconManager.get_icon('generate'), "Passwort generieren", self)
        generate_password_action.setShortcut("Ctrl+G")
        generate_password_action.triggered.connect(self.show_password_generator)
        file_menu.addAction(generate_password_action)
        
        file_menu.addSeparator()
        
        # Import/Export Untermenü
        import_export_menu = QMenu("Import/Export", self)
        
        import_csv_action = QAction(IconManager.get_icon('import'), "Aus CSV importieren", self)
        import_csv_action.triggered.connect(self.import_from_csv)
        import_export_menu.addAction(import_csv_action)
        
        export_csv_action = QAction(IconManager.get_icon('export'), "Nach CSV exportieren", self)
        export_csv_action.triggered.connect(self.export_to_csv)
        import_export_menu.addAction(export_csv_action)
        
        import_export_menu.addSeparator()
        
        import_json_action = QAction(IconManager.get_icon('import'), "Aus JSON importieren", self)
        import_json_action.triggered.connect(self.import_from_json)
        import_export_menu.addAction(import_json_action)
        
        export_json_action = QAction(IconManager.get_icon('export'), "Nach JSON exportieren", self)
        export_json_action.triggered.connect(self.export_to_json)
        import_export_menu.addAction(export_json_action)
        
        file_menu.addMenu(import_export_menu)
        
        # Backup Untermenü
        backup_menu = QMenu("Backup", self)
        
        create_backup_action = QAction(IconManager.get_icon('backup'), "Backup erstellen", self)
        create_backup_action.triggered.connect(self.create_backup)
        backup_menu.addAction(create_backup_action)
        
        restore_backup_action = QAction(IconManager.get_icon('restore'), "Backup wiederherstellen", self)
        restore_backup_action.triggered.connect(self.restore_backup)
        backup_menu.addAction(restore_backup_action)
        
        file_menu.addMenu(backup_menu)
        
        file_menu.addSeparator()
        
        settings_action = QAction(IconManager.get_icon('settings'), "Einstellungen", self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        lock_action = QAction(IconManager.get_icon('lock'), "Sperren", self)
        lock_action.setShortcut("Ctrl+L")
        lock_action.triggered.connect(self.lock_application)
        file_menu.addAction(lock_action)
        
        exit_action = QAction(IconManager.get_icon('cancel'), "Beenden", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Bearbeiten-Menü
        edit_menu = menu_bar.addMenu("&Bearbeiten")
        
        change_master_action = QAction(IconManager.get_icon('edit'), "Masterpasswort ändern", self)
        change_master_action.triggered.connect(self.change_master_password)
        edit_menu.addAction(change_master_action)
        
        edit_menu.addSeparator()
        
        # Kategorien-Untermenü
        categories_menu = QMenu("Kategorien", self)
        
        add_category_action = QAction(IconManager.get_icon('category_add'), "Neue Kategorie", self)
        add_category_action.triggered.connect(lambda: self.add_category("", None))
        categories_menu.addAction(add_category_action)
        
        edit_menu.addMenu(categories_menu)
        
        # Ansicht-Menü
        view_menu = menu_bar.addMenu("&Ansicht")
        
        refresh_action = QAction(IconManager.get_icon('search'), "Aktualisieren", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.load_data)
        view_menu.addAction(refresh_action)
        
        view_menu.addSeparator()
        
        # Themes Untermenü
        themes_menu = QMenu("Theme", self)
        
        light_theme_action = QAction("Helles Theme", self)
        light_theme_action.setCheckable(True)
        light_theme_action.triggered.connect(lambda: self.change_theme("light"))
        themes_menu.addAction(light_theme_action)
        
        dark_theme_action = QAction("Dunkles Theme", self)
        dark_theme_action.setCheckable(True)
        dark_theme_action.triggered.connect(lambda: self.change_theme("dark"))
        themes_menu.addAction(dark_theme_action)
        
        # Aktives Theme markieren
        if self.settings and self.settings.theme == "dark":
            dark_theme_action.setChecked(True)
        else:
            light_theme_action.setChecked(True)
        
        view_menu.addMenu(themes_menu)
        
        # Hilfe-Menü
        help_menu = menu_bar.addMenu("&Hilfe")
        
        about_action = QAction(IconManager.get_icon('about'), "Über", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Erstellt die Toolbar der Anwendung"""
        toolbar = QToolBar("Haupttoolbar")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Aktionen hinzufügen
        new_action = QAction(IconManager.get_icon('add'), "Neues Passwort", self)
        new_action.setStatusTip("Neues Passwort hinzufügen")
        new_action.triggered.connect(self.add_new_password)
        toolbar.addAction(new_action)
        
        generate_action = QAction(IconManager.get_icon('generate'), "Generieren", self)
        generate_action.setStatusTip("Passwort generieren")
        generate_action.triggered.connect(self.show_password_generator)
        toolbar.addAction(generate_action)
        
        toolbar.addSeparator()
        
        category_action = QAction(IconManager.get_icon('category_add'), "Neue Kategorie", self)
        category_action.setStatusTip("Neue Kategorie hinzufügen")
        category_action.triggered.connect(lambda: self.add_category("", None))
        toolbar.addAction(category_action)
        
        toolbar.addSeparator()
        
        settings_action = QAction(IconManager.get_icon('settings'), "Einstellungen", self)
        settings_action.setStatusTip("Einstellungen öffnen")
        settings_action.triggered.connect(self.show_settings)
        toolbar.addAction(settings_action)
        
        toolbar.addSeparator()
        
        lock_action = QAction(IconManager.get_icon('lock'), "Sperren", self)
        lock_action.setStatusTip("Anwendung sperren")
        lock_action.triggered.connect(self.lock_application)
        toolbar.addAction(lock_action)
    
    def check_master_password(self):
        """Überprüft das Masterpasswort und initialisiert die Anwendung"""
        # Lade die Einstellungen
        self.settings = self.storage.get_settings()
        
        # Wende das Theme an
        app = QApplication.instance()
        Themes.apply_theme(app, self.settings.theme)
        
        # Überprüfe, ob ein Masterpasswort existiert
        stored_hash = self.storage.get_master_password_hash()
        
        if stored_hash:
            # Login-Dialog anzeigen
            login_dialog = LoginDialog(self)
            if login_dialog.exec_() == LoginDialog.Accepted:
                master_password = login_dialog.get_password()
                
                if Encryption.verify_master_password(master_password, stored_hash):
                    self.encryption = Encryption(master_password)
                    self.load_data()
                    self.reset_inactivity_timer()
                else:
                    QMessageBox.critical(self, "Fehler", "Falsches Masterpasswort!")
                    self.close()
            else:
                self.close()
        else:
            # Neues Masterpasswort erstellen
            QMessageBox.information(self, "Willkommen", 
                                 "Willkommen beim Passwortmanager!\n\n"
                                 "Bitte erstellen Sie ein sicheres Masterpasswort.\n"
                                 "Dieses Passwort schützt alle Ihre gespeicherten Passwörter.")
            
            new_master_dialog = NewMasterPasswordDialog(self)
            
            if new_master_dialog.exec_() == NewMasterPasswordDialog.Accepted:
                master_password = new_master_dialog.get_password()
                
                if master_password:
                    password_hash = Encryption.hash_master_password(master_password)
                    self.storage.save_master_password(password_hash)
                    self.encryption = Encryption(master_password)
                    self.load_data()
                    self.reset_inactivity_timer()
                else:
                    QMessageBox.critical(self, "Fehler", "Kein Masterpasswort gesetzt!")
                    self.close()
            else:
                self.close()
    
    def load_data(self):
        """Lädt alle Daten aus der Datenbank"""
        # Lade Kategorien
        categories = self.storage.get_all_categories()
        self.categories = {category.id: category for category in categories}
        
        # Aktualisiere die Kategorie-Baumansicht
        self.category_tree.populate_tree(categories)
        
        # Lade Passwörter
        passwords = self.storage.get_all_passwords()
        
        # Entschlüssle die Passwörter
        for password in passwords:
            if self.encryption:
                try:
                    # Entschlüssle das Passwort
                    decrypted_password = self.encryption.decrypt(password.password)
                    password.password = decrypted_password
                except Exception as e:
                    print(f"Fehler beim Entschlüsseln eines Passworts: {e}")
        
        # Befülle die Passwort-Tabelle
        self.password_table.set_visible_columns(self.settings.visible_columns)
        self.password_table.populate_table(passwords, self.categories, encrypted=False)
        
        # Zeige die Gesamtanzahl der Passwörter in der Statusleiste
        self.statusBar.showMessage(f"Insgesamt {len(passwords)} Passwörter")
        
        # Wähle die "Alle Einträge" Kategorie aus
        self.category_tree.select_all_entries()
    
    def reset_inactivity_timer(self):
        """Setzt den Inaktivitäts-Timer zurück"""
        if self.settings and self.settings.auto_lock_enabled:
            # Timer aktivieren (in Minuten × 60000 Millisekunden)
            self.inactivity_timer.start(self.settings.auto_lock_time * 60000)
    
    def keyPressEvent(self, event):
        """
        Behandelt Tastatureingaben
        
        Args:
            event (QKeyEvent): Tastatur-Event
        """
        self.reset_inactivity_timer()
        super().keyPressEvent(event)
    
    def mousePressEvent(self, event):
        """
        Behandelt Mauseingaben
        
        Args:
            event (QMouseEvent): Maus-Event
        """
        self.reset_inactivity_timer()
        super().mousePressEvent(event)
    
    def lock_application(self):
        """Sperrt die Anwendung und erfordert erneute Eingabe des Masterpassworts"""
        # Inaktivitäts-Timer stoppen
        self.inactivity_timer.stop()
        
        # Verschlüsselungsobjekt zurücksetzen
        self.encryption = None
        
        # Tabellen leeren
        self.password_table.setRowCount(0)
        
        # Statusleiste aktualisieren
        self.statusBar.showMessage("Anwendung gesperrt")
        
        # Masterpasswort erneut abfragen
        self.check_master_password()
    
    def change_master_password(self):
        """Ändert das Masterpasswort"""
        # Aktuelles Passwort bestätigen
        password_dialog = LoginDialog(self, "Aktuelles Masterpasswort eingeben")
        
        if password_dialog.exec_() == LoginDialog.Accepted:
            current_password = password_dialog.get_password()
            stored_hash = self.storage.get_master_password_hash()
            
            if Encryption.verify_master_password(current_password, stored_hash):
                # Neues Passwort setzen
                new_master_dialog = NewMasterPasswordDialog(self)
                
                if new_master_dialog.exec_() == NewMasterPasswordDialog.Accepted:
                    new_password = new_master_dialog.get_password()
                    
                    if new_password:
                        # Alle Passwörter neu verschlüsseln
                        self.re_encrypt_all_passwords(current_password, new_password)
                        
                        # Neues Masterpasswort speichern
                        new_hash = Encryption.hash_master_password(new_password)
                        self.storage.save_master_password(new_hash)
                        
                        # Aktualisiere Verschlüsselungsobjekt
                        self.encryption = Encryption(new_password)
                        
                        QMessageBox.information(self, "Erfolg", 
                                            "Masterpasswort erfolgreich geändert!")
            else:
                QMessageBox.critical(self, "Fehler", "Falsches Masterpasswort!")
    
    def re_encrypt_all_passwords(self, old_password, new_password):
        """
        Verschlüsselt alle Passwörter neu mit dem neuen Masterpasswort
        
        Args:
            old_password (str): Altes Masterpasswort
            new_password (str): Neues Masterpasswort
        """
        # Erstellt neue Verschlüsselungsinstanzen
        old_encryption = Encryption(old_password)
        new_encryption = Encryption(new_password)
        
        # Alle Passwörter laden
        all_passwords = self.storage.get_all_passwords()
        
        # Jedes Passwort neu verschlüsseln
        for entry in all_passwords:
            try:
                decrypted_password = old_encryption.decrypt(entry.password)
                encrypted_password = new_encryption.encrypt(decrypted_password)
                
                self.storage.update_password(
                    entry.id,
                    entry.title,
                    entry.username,
                    encrypted_password,
                    entry.url,
                    entry.device_type,
                    entry.notes,
                    entry.category_id,
                    entry.is_favorite,
                    entry.expiry_date
                )
            except Exception as e:
                print(f"Fehler beim Neu-Verschlüsseln eines Passworts: {e}")
    
    def add_new_password(self):
        """Fügt ein neues Passwort hinzu"""
        if not self.encryption:
            self.lock_application()
            return
        
        # Dialog zum Hinzufügen eines neuen Passworts
        dialog = PasswordDialog(self, self.encryption, self.categories)
        
        if dialog.exec_() == PasswordDialog.Accepted:
            data = dialog.get_data()
            
            if data:
                # Passwort verschlüsseln
                encrypted_password = self.encryption.encrypt(data['password'])
                
                # In Datenbank speichern
                password_id = self.storage.add_password(
                    data['title'],
                    data['username'],
                    encrypted_password,
                    data['url'],
                    data['device_type'],
                    data['notes'],
                    data['category_id'],
                    data['is_favorite'],
                    data['expiry_date']
                )
                
                if password_id > 0:
                    # Tabelle aktualisieren
                    self.load_data()
                    
                    # Statusleiste aktualisieren
                    self.statusBar.showMessage(f"Passwort '{data['title']}' erfolgreich hinzugefügt")
                else:
                    QMessageBox.warning(self, "Fehler", "Fehler beim Speichern des Passworts")
    
    def edit_password(self, password_id):
        """
        Bearbeitet ein Passwort
        
        Args:
            password_id (int): ID des zu bearbeitenden Passworts
        """
        if not self.encryption:
            self.lock_application()
            return
        
        # Passwort aus Datenbank laden
        entry = self.storage.get_password(password_id)
        
        if not entry:
            QMessageBox.warning(self, "Fehler", "Passwort nicht gefunden")
            return
        
        # Passwort entschlüsseln
        try:
            decrypted_password = self.encryption.decrypt(entry.password)
            entry.password = decrypted_password
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Entschlüsseln des Passworts: {e}")
            return
        
        # Dialog zum Bearbeiten des Passworts
        dialog = PasswordDialog(self, self.encryption, self.categories, entry)
        
        if dialog.exec_() == PasswordDialog.Accepted:
            data = dialog.get_data()
            
            if data:
                # Passwort verschlüsseln
                encrypted_password = self.encryption.encrypt(data['password'])
                
                # In Datenbank aktualisieren
                success = self.storage.update_password(
                    password_id,
                    data['title'],
                    data['username'],
                    encrypted_password,
                    data['url'],
                    data['device_type'],
                    data['notes'],
                    data['category_id'],
                    data['is_favorite'],
                    data['expiry_date']
                )
                
                if success:
                    # Tabelle aktualisieren
                    self.load_data()
                    
                    # Statusleiste aktualisieren
                    self.statusBar.showMessage(f"Passwort '{data['title']}' erfolgreich aktualisiert")
                else:
                    QMessageBox.warning(self, "Fehler", "Fehler beim Aktualisieren des Passworts")
    
    def view_password(self, password_id):
        """
        Zeigt ein Passwort an
        
        Args:
            password_id (int): ID des anzuzeigenden Passworts
        """
        if not self.encryption:
            self.lock_application()
            return
        
        # Passwort aus Datenbank laden
        entry = self.storage.get_password(password_id)
        
        if not entry:
            QMessageBox.warning(self, "Fehler", "Passwort nicht gefunden")
            return
        
        # Passwort entschlüsseln
        try:
            decrypted_password = self.encryption.decrypt(entry.password)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Entschlüsseln des Passworts: {e}")
            return
        
        # Informationen für die Anzeige vorbereiten
        info_text = f"<b>Titel:</b> {entry.title}<br><br>"
        
        # Nur Felder mit Inhalt anzeigen
        if entry.username:
            info_text += f"<b>Benutzername:</b> {entry.username}<br><br>"
        
        info_text += f"<b>Passwort:</b> {decrypted_password}<br><br>"
        
        if entry.url:
            info_text += f"<b>URL:</b> {entry.url}<br><br>"
        
        if entry.device_type:
            info_text += f"<b>Gerätetyp:</b> {entry.device_type}<br><br>"
        
        if entry.category_id and entry.category_id in self.categories:
            info_text += f"<b>Kategorie:</b> {self.categories[entry.category_id].name}<br><br>"
        
        if entry.expiry_date:
            days = days_until_expiry(entry.expiry_date)
            expiry_info = ""
            
            if days is not None:
                if days < 0:
                    expiry_info = " <span style='color: red;'>(abgelaufen)</span>"
                elif days < 7:
                    expiry_info = f" <span style='color: orange;'>(läuft in {days} Tagen ab)</span>"
                else:
                    expiry_info = f" (läuft in {days} Tagen ab)"
                    
            info_text += f"<b>Ablaufdatum:</b> {entry.expiry_date.strftime('%d.%m.%Y')}{expiry_info}<br><br>"
        
        if entry.notes:
            info_text += f"<b>Notizen:</b><br>{entry.notes.replace('n', '<br>')}"
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f"Passwort für {entry.title}")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(info_text)
        msg_box.setStandardButtons(QMessageBox.Ok)
        
        # Kopieren-Button hinzufügen
        copy_button = msg_box.addButton("Passwort kopieren", QMessageBox.ActionRole)
        
        msg_box.exec_()
        
        # Wenn Kopieren-Button geklickt wurde
        if msg_box.clickedButton() == copy_button:
            self.copy_password_to_clipboard(password_id)
    
    def delete_password(self, password_id):
        """
        Löscht ein Passwort
        
        Args:
            password_id (int): ID des zu löschenden Passworts
        """
        # Passwort aus Datenbank laden
        entry = self.storage.get_password(password_id)
        
        if not entry:
            QMessageBox.warning(self, "Fehler", "Passwort nicht gefunden")
            return
        
        # Bestätigung
        reply = QMessageBox.question(
            self,
            "Löschen bestätigen",
            f"Möchten Sie den Eintrag '{entry.title}' wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Passwort löschen
            success = self.storage.delete_password(password_id)
            
            if success:
                # Tabelle aktualisieren
                self.load_data()
                
                # Statusleiste aktualisieren
                self.statusBar.show
                
                self.statusBar.showMessage(f"Passwort '{entry.title}' erfolgreich gelöscht")
            else:
                QMessageBox.warning(self, "Fehler", "Fehler beim Löschen des Passworts")
    
    def copy_password_to_clipboard(self, password_id):
        """
        Kopiert ein Passwort in die Zwischenablage
        
        Args:
            password_id (int): ID des zu kopierenden Passworts
        """
        if not self.encryption:
            self.lock_application()
            return
        
        # Passwort aus Datenbank laden
        entry = self.storage.get_password(password_id)
        
        if not entry:
            QMessageBox.warning(self, "Fehler", "Passwort nicht gefunden")
            return
        
        # Passwort entschlüsseln
        try:
            decrypted_password = self.encryption.decrypt(entry.password)
            
            # In Zwischenablage kopieren
            QApplication.clipboard().setText(decrypted_password)
            
            # Statusleiste aktualisieren
            self.statusBar.showMessage(f"Passwort für '{entry.title}' in die Zwischenablage kopiert", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Entschlüsseln des Passworts: {e}")
    
    def toggle_password_favorite(self, password_id, is_favorite):
        """
        Ändert den Favoriten-Status eines Passworts
        
        Args:
            password_id (int): ID des Passworts
            is_favorite (bool): Neuer Favoriten-Status
        """
        # Favoriten-Status ändern
        success = self.storage.toggle_favorite(password_id, is_favorite)
        
        if success:
            # Tabelle aktualisieren
            self.load_data()
            
            # Filter anwenden, falls aktuell Favoriten angezeigt werden
            if self.show_favorites_only:
                self.password_table.filter_favorites(True)
            
            # Status aktualisieren
            status = "hinzugefügt zu" if is_favorite else "entfernt aus"
            self.statusBar.showMessage(f"Passwort {status} Favoriten", 3000)
        else:
            QMessageBox.warning(self, "Fehler", "Fehler beim Ändern des Favoriten-Status")
    
    def change_password_category(self, password_id, category_id):
        """
        Ändert die Kategorie eines Passworts
        
        Args:
            password_id (int): ID des Passworts
            category_id (int or None): ID der neuen Kategorie
        """
        # Passwort aus Datenbank laden
        entry = self.storage.get_password(password_id)
        
        if not entry:
            QMessageBox.warning(self, "Fehler", "Passwort nicht gefunden")
            return
        
        if entry.category_id == category_id:
            return  # Keine Änderung
        
        # Kategorie-Name ermitteln
        category_name = "Keine Kategorie"
        if category_id is not None and category_id in self.categories:
            category_name = self.categories[category_id].name
        
        try:
            # In Datenbank aktualisieren
            success = self.storage.update_password(
                password_id,
                entry.title,
                entry.username,
                entry.password,  # Hier bleibt das Passwort verschlüsselt!
                entry.url,
                entry.device_type,
                entry.notes,
                category_id,
                entry.is_favorite,
                entry.expiry_date
            )
            
            if success:
                # Tabelle aktualisieren
                self.load_data()
                
                # Filter anwenden, falls aktuell nach Kategorie gefiltert wird
                if self.current_category_id is not None:
                    self.filter_by_category(self.current_category_id)
                
                # Statusleiste aktualisieren
                self.statusBar.showMessage(f"Kategorie für '{entry.title}' zu '{category_name}' geändert", 3000)
            else:
                QMessageBox.warning(self, "Fehler", "Fehler beim Ändern der Kategorie")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Aktualisieren des Passworts: {e}")
    
    def show_password_generator(self):
        """Zeigt den Passwort-Generator-Dialog an"""
        dialog = GeneratePasswordDialog(self)
        dialog.exec_()
    
    def add_category(self, name, parent_id):
        """
        Fügt eine neue Kategorie hinzu
        
        Args:
            name (str): Name der Kategorie
            parent_id (int or None): ID der übergeordneten Kategorie
        """
        # Kategorie hinzufügen
        if not name:
            # Dialog für den Namen anzeigen
            from PyQt5.QtWidgets import QInputDialog
            name, ok = QInputDialog.getText(self, "Neue Kategorie", "Kategoriename:")
            if not ok or not name:
                return
        
        category_id = self.storage.add_category(name, "", parent_id)
        
        if category_id > 0:
            # Kategorie zur Liste hinzufügen
            category = self.storage.get_category(category_id)
            if category:
                self.categories[category_id] = category
                
                # Kategorien-Baum aktualisieren
                self.category_tree.populate_tree(list(self.categories.values()))
                
                # Statusleiste aktualisieren
                self.statusBar.showMessage(f"Kategorie '{name}' erfolgreich hinzugefügt", 3000)
        else:
            QMessageBox.warning(self, "Fehler", "Fehler beim Erstellen der Kategorie")
    
    def edit_category(self, category_id, name):
        """
        Bearbeitet eine Kategorie
        
        Args:
            category_id (int): ID der Kategorie
            name (str): Neuer Name der Kategorie
        """
        # Kategorie aktualisieren
        if category_id in self.categories:
            old_name = self.categories[category_id].name
            
            success = self.storage.update_category(category_id, name)
            
            if success:
                # Kategorie in Liste aktualisieren
                category = self.storage.get_category(category_id)
                if category:
                    self.categories[category_id] = category
                    
                    # Kategorien-Baum aktualisieren
                    self.category_tree.populate_tree(list(self.categories.values()))
                    
                    # Statusleiste aktualisieren
                    self.statusBar.showMessage(f"Kategorie von '{old_name}' zu '{name}' umbenannt", 3000)
            else:
                QMessageBox.warning(self, "Fehler", "Fehler beim Umbenennen der Kategorie")
    
    def delete_category(self, category_id):
        """
        Löscht eine Kategorie
        
        Args:
            category_id (int): ID der zu löschenden Kategorie
        """
        # Kategorie löschen
        if category_id in self.categories:
            category_name = self.categories[category_id].name
            
            success = self.storage.delete_category(category_id)
            
            if success:
                # Kategorie aus Liste entfernen
                if category_id in self.categories:
                    del self.categories[category_id]
                
                # Kategorien-Baum aktualisieren
                self.category_tree.populate_tree(list(self.categories.values()))
                
                # Passwörter neu laden
                self.load_data()
                
                # Statusleiste aktualisieren
                self.statusBar.showMessage(f"Kategorie '{category_name}' erfolgreich gelöscht", 3000)
            else:
                QMessageBox.warning(self, "Fehler", "Fehler beim Löschen der Kategorie")
    
    def filter_by_category(self, category_id):
        """
        Filtert die Passwort-Tabelle nach Kategorie
        
        Args:
            category_id (int): ID der Kategorie
        """
        self.current_category_id = category_id
        self.show_favorites_only = False
        self.show_favorites_checkbox.setChecked(False)
        
        # Filter auf die Tabelle anwenden
        self.password_table.filter_by_category(category_id)
        
        # Statusleiste aktualisieren
        visible_rows = sum(1 for i in range(self.password_table.rowCount()) if not self.password_table.isRowHidden(i))
        
        if category_id in self.categories:
            self.statusBar.showMessage(f"{visible_rows} Passwörter in Kategorie '{self.categories[category_id].name}'")
        else:
            self.statusBar.showMessage(f"{visible_rows} Passwörter (keine Kategorie)")
    
    def show_all_entries(self):
        """Zeigt alle Passwörter an"""
        self.current_category_id = None
        self.show_favorites_only = False
        self.show_favorites_checkbox.setChecked(False)
        
        # Alle Zeilen anzeigen
        for row in range(self.password_table.rowCount()):
            self.password_table.setRowHidden(row, False)
        
        # Statusleiste aktualisieren
        self.statusBar.showMessage(f"{self.password_table.rowCount()} Passwörter insgesamt")
    
    def show_favorites(self):
        """Zeigt nur Favoriten-Passwörter an"""
        self.current_category_id = None
        self.show_favorites_only = True
        self.show_favorites_checkbox.setChecked(True)
        
        # Filter auf die Tabelle anwenden
        self.password_table.filter_favorites(True)
        
        # Statusleiste aktualisieren
        visible_rows = sum(1 for i in range(self.password_table.rowCount()) if not self.password_table.isRowHidden(i))
        self.statusBar.showMessage(f"{visible_rows} Passwörter in Favoriten")
    
    def toggle_favorites(self, show_only_favorites):
        """
        Schaltet den Favoriten-Filter um
        
        Args:
            show_only_favorites (bool): Ob nur Favoriten angezeigt werden sollen
        """
        self.show_favorites_only = show_only_favorites
        
        if show_only_favorites:
            # Nur Favoriten anzeigen
            self.category_tree.select_favorites()
        else:
            # Aktuelle Kategorie auswählen oder alle anzeigen
            if self.current_category_id is not None:
                self.category_tree.select_category(self.current_category_id)
            else:
                self.category_tree.select_all_entries()
    
    def search_passwords(self, search_text):
        """
        Sucht nach Passwörtern
        
        Args:
            search_text (str): Suchtext
        """
        # Filter auf die Tabelle anwenden
        self.password_table.filter_by_text(search_text)
        
        # Statusleiste aktualisieren
        visible_rows = sum(1 for i in range(self.password_table.rowCount()) if not self.password_table.isRowHidden(i))
        self.statusBar.showMessage(f"{visible_rows} Passwörter gefunden für '{search_text}'")
    
    def import_from_csv(self):
        """Importiert Passwörter aus einer CSV-Datei"""
        if not self.encryption:
            self.lock_application()
            return
        
        # Datei auswählen
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "CSV-Datei importieren",
            "",
            "CSV-Dateien (*.csv);;Alle Dateien (*.*)"
        )
        
        if not file_path:
            return
        
        # Daten importieren
        imported_entries = import_from_csv(file_path, list(self.categories.values()))
        
        if imported_entries:
            # Bestätigung
            reply = QMessageBox.question(
                self,
                "Import bestätigen",
                f"Möchten Sie {len(imported_entries)} Passwörter importieren?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Passwörter in Datenbank speichern
                count = 0
                for entry in imported_entries:
                    # Passwort verschlüsseln
                    encrypted_password = self.encryption.encrypt(entry['password'])
                    
                    # In Datenbank speichern
                    password_id = self.storage.add_password(
                        entry['title'],
                        entry['username'],
                        encrypted_password,
                        entry['url'],
                        entry['device_type'],
                        entry['notes'],
                        entry['category_id'],
                        entry['is_favorite'],
                        entry['expiry_date']
                    )
                    
                    if password_id > 0:
                        count += 1
                
                # Tabelle aktualisieren
                self.load_data()
                
                # Statusleiste aktualisieren
                self.statusBar.showMessage(f"{count} Passwörter erfolgreich importiert")
        else:
            QMessageBox.warning(self, "Fehler", "Fehler beim Import der CSV-Datei oder keine Daten gefunden")
    
    def export_to_csv(self):
        """Exportiert Passwörter in eine CSV-Datei"""
        if not self.encryption:
            self.lock_application()
            return
        
        # Datei auswählen
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "CSV-Datei exportieren",
            "",
            "CSV-Dateien (*.csv);;Alle Dateien (*.*)"
        )
        
        if not file_path:
            return
        
        # Stelle sicher, dass die Datei die Erweiterung .csv hat
        if not file_path.lower().endswith(".csv"):
            file_path += ".csv"
        
        # Passwörter aus Datenbank laden
        passwords = self.storage.get_all_passwords()
        
        # Passwörter entschlüsseln
        for password in passwords:
            try:
                password.password = self.encryption.decrypt(password.password)
            except Exception as e:
                print(f"Fehler beim Entschlüsseln eines Passworts: {e}")
                password.password = "*** Fehler beim Entschlüsseln ***"
        
        # Kategorie-Map erstellen
        category_map = {cat_id: cat.name for cat_id, cat in self.categories.items()}
        
        # Warnung anzeigen
        reply = QMessageBox.warning(
            self,
            "Warnung",
            "Die CSV-Datei wird unverschlüsselte Passwörter enthalten. "
            "Stellen Sie sicher, dass die Datei sicher gespeichert wird.\n\n"
            "Möchten Sie fortfahren?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Daten exportieren
            success = export_to_csv(passwords, category_map, file_path)
            
            if success:
                # Statusleiste aktualisieren
                self.statusBar.showMessage(f"{len(passwords)} Passwörter erfolgreich nach {file_path} exportiert")
            else:
                QMessageBox.warning(self, "Fehler", "Fehler beim Export in die CSV-Datei")
    
    def import_from_json(self):
        """Importiert Passwörter aus einer JSON-Datei"""
        if not self.encryption:
            self.lock_application()
            return
        
        # Datei auswählen
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "JSON-Datei importieren",
            "",
            "JSON-Dateien (*.json);;Alle Dateien (*.*)"
        )
        
        if not file_path:
            return
        
        # Daten importieren
        imported_entries = import_from_json(file_path, list(self.categories.values()))
        
        if imported_entries:
            # Bestätigung
            reply = QMessageBox.question(
                self,
                "Import bestätigen",
                f"Möchten Sie {len(imported_entries)} Passwörter importieren?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Passwörter in Datenbank speichern
                count = 0
                for entry in imported_entries:
                    # Prüfen, ob das Passwort bereits verschlüsselt ist
                    if 'encrypted' in entry and entry['encrypted']:
                        encrypted_password = entry['password']
                    else:
                        # Passwort verschlüsseln
                        encrypted_password = self.encryption.encrypt(entry['password'])
                    
                    # In Datenbank speichern
                    password_id = self.storage.add_password(
                        entry['title'],
                        entry['username'],
                        encrypted_password,
                        entry['url'],
                        entry['device_type'],
                        entry['notes'],
                        entry['category_id'],
                        entry['is_favorite'],
                        entry['expiry_date']
                    )
                    
                    if password_id > 0:
                        count += 1
                
                # Tabelle aktualisieren
                self.load_data()
                
                # Statusleiste aktualisieren
                self.statusBar.showMessage(f"{count} Passwörter erfolgreich importiert")
        else:
            QMessageBox.warning(self, "Fehler", "Fehler beim Import der JSON-Datei oder keine Daten gefunden")
    
    def export_to_json(self):
        """Exportiert Passwörter in eine JSON-Datei"""
        if not self.encryption:
            self.lock_application()
            return
        
        # Datei auswählen
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "JSON-Datei exportieren",
            "",
            "JSON-Dateien (*.json);;Alle Dateien (*.*)"
        )
        
        if not file_path:
            return
        
        # Stelle sicher, dass die Datei die Erweiterung .json hat
        if not file_path.lower().endswith(".json"):
            file_path += ".json"
        
        # Passwörter aus Datenbank laden
        passwords = self.storage.get_all_passwords()
        
        # Frage, ob die Passwörter verschlüsselt oder entschlüsselt exportiert werden sollen
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Export-Format")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout(dialog)
        
        encrypted_radio = QRadioButton("Verschlüsselt (sicherer, nur für Backup)")
        encrypted_radio.setChecked(True)
        layout.addWidget(encrypted_radio)
        
        decrypted_radio = QRadioButton("Entschlüsselt (für Import in andere Anwendungen)")
        layout.addWidget(decrypted_radio)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec_() != QDialog.Accepted:
            return
        
        # Format bestimmen
        encrypted = encrypted_radio.isChecked()
        
        # Wenn entschlüsselt, dann entschlüssle die Passwörter
        if not encrypted:
            # Warnung anzeigen
            reply = QMessageBox.warning(
                self,
                "Warnung",
                "Die JSON-Datei wird unverschlüsselte Passwörter enthalten. "
                "Stellen Sie sicher, dass die Datei sicher gespeichert wird.\n\n"
                "Möchten Sie fortfahren?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Passwörter entschlüsseln
            for password in passwords:
                try:
                    password.password = self.encryption.decrypt(password.password)
                except Exception as e:
                    print(f"Fehler beim Entschlüsseln eines Passworts: {e}")
                    password.password = "*** Fehler beim Entschlüsseln ***"
        
        # Kategorie-Map erstellen
        category_map = {cat_id: cat.name for cat_id, cat in self.categories.items()}
        
        # Daten exportieren
        success = export_to_json(passwords, category_map, file_path, encrypted)
        
        if success:
            # Statusleiste aktualisieren
            self.statusBar.showMessage(f"{len(passwords)} Passwörter erfolgreich nach {file_path} exportiert")
        else:
            QMessageBox.warning(self, "Fehler", "Fehler beim Export in die JSON-Datei")
    
    def create_backup(self):
        """Erstellt ein Backup der Datenbank"""
        # Backup erstellen
        success, result = create_backup(self.settings.db_path)
        
        if success:
            QMessageBox.information(
                self,
                "Backup erstellt",
                f"Backup erfolgreich erstellt unter:\n{result}"
            )
            
            # Statusleiste aktualisieren
            self.statusBar.showMessage(f"Backup erfolgreich erstellt: {result}")
        else:
            QMessageBox.warning(self, "Fehler", f"Fehler beim Erstellen des Backups: {result}")
    
    def restore_backup(self):
        """Stellt ein Backup der Datenbank wieder her"""
        # Backup-Verzeichnis ermitteln
        db_dir = os.path.dirname(os.path.abspath(self.settings.db_path))
        backup_dir = os.path.join(db_dir, 'backups')
        
        # Verfügbare Backups abrufen
        backups = get_backup_list(backup_dir)
        
        if not backups:
            QMessageBox.information(
                self,
                "Keine Backups",
                f"Es wurden keine Backups im Verzeichnis {backup_dir} gefunden."
            )
            return
        
        # Backup-Dialog
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Backup wiederherstellen")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(300)
        
        layout = QVBoxLayout(dialog)
        
        backup_list = QListWidget()
        for backup in backups:
            date_str = backup['date'].strftime('%d.%m.%Y %H:%M:%S')
            size_mb = backup['size'] / (1024 * 1024)
            item_text = f"{date_str} - {size_mb:.2f} MB"
            if backup['description']:
                item_text += f" - {backup['description']}"
            
            backup_list.addItem(item_text)
            backup_list.item(backup_list.count() - 1).setData(Qt.UserRole, backup['path'])
        
        layout.addWidget(QLabel("Bitte wählen Sie ein Backup aus:"))
        layout.addWidget(backup_list)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec_() != QDialog.Accepted:
            return
        
        # Ausgewähltes Backup ermitteln
        selected_items = backup_list.selectedItems()
        if not selected_items:
            return
        
        backup_path = selected_items[0].data(Qt.UserRole)
        
        # Warnung anzeigen
        reply = QMessageBox.warning(
            self,
            "Warnung",
            "Beim Wiederherstellen eines Backups werden alle aktuellen Daten überschrieben.\n\n"
            "Möchten Sie fortfahren?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Anwendung sperren
        self.lock_application()
        
        # Backup wiederherstellen
        success, message = restore_backup(backup_path, self.settings.db_path)
        
        if success:
            QMessageBox.information(
                self,
                "Backup wiederhergestellt",
                f"Backup erfolgreich wiederhergestellt.\n\n{message}"
            )
            
            # Anwendung neu starten
            self.check_master_password()
        else:
            QMessageBox.warning(self, "Fehler", f"Fehler bei der Wiederherstellung des Backups: {message}")
    
    def show_settings(self):
        """Zeigt den Einstellungsdialog an"""
        dialog = SettingsDialog(self, self.settings)
        dialog.settings_changed.connect(self.apply_settings)
        
        if dialog.exec_() == SettingsDialog.Accepted:
            # Einstellungen wurden bereits durch das Signal aktualisiert
            pass
    
    def apply_settings(self, new_settings):
        """
        Wendet neue Einstellungen an
        
        Args:
            new_settings (AppSettings): Die neuen Einstellungen
        """
        old_settings = self.settings
        self.settings = new_settings
        
        # Einstellungen in der Datenbank speichern
        self.storage.save_settings(new_settings)
        
        # Theme anwenden, falls geändert
        if old_settings.theme != new_settings.theme:
            app = QApplication.instance()
            Themes.apply_theme(app, new_settings.theme)
        
        # Tabellenspalten aktualisieren, falls geändert
        if old_settings.visible_columns != new_settings.visible_columns:
            self.password_table.set_visible_columns(new_settings.visible_columns)
            self.load_data()
        
        # Inaktivitäts-Timer aktualisieren
        if new_settings.auto_lock_enabled:
            self.inactivity_timer.start(new_settings.auto_lock_time * 60000)
        else:
            self.inactivity_timer.stop()
        
        # Datenbankpfad aktualisieren (erfordert Neustart, falls geändert)
        if old_settings.db_path != new_settings.db_path and os.path.exists(new_settings.db_path):
            reply = QMessageBox.information(
                self,
                "Datenbank geändert",
                "Der Datenbankpfad wurde geändert. Die Anwendung muss neu gestartet werden, "
                "um die Änderung zu übernehmen.\n\n"
                "Möchten Sie jetzt neu starten?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.lock_application()
                self.check_master_password()
    
    def change_theme(self, theme_name):
        """
        Ändert das Theme der Anwendung
        
        Args:
            theme_name (str): Name des Themes ('light' oder 'dark')
        """
        if self.settings.theme == theme_name:
            return
        
        # Theme in den Einstellungen ändern
        self.settings.theme = theme_name
        
        # Einstellungen speichern
        self.storage.save_settings(self.settings)
        
        # Theme anwenden
        app = QApplication.instance()
        Themes.apply_theme(app, theme_name)
    
    def show_about(self):
        """Zeigt den Über-Dialog an"""
        dialog = AboutDialog(self)
        dialog.exec_()
    
    def closeEvent(self, event):
        """
        Wird beim Schließen der Anwendung aufgerufen
        
        Args:
            event (QCloseEvent): Das Close-Event
        """
        # Automatisches Backup erstellen, falls konfiguriert
        if hasattr(self, 'settings') and self.settings:
            if hasattr(self.settings, 'auto_backup') and self.settings.auto_backup:
                try:
                    db_dir = os.path.dirname(os.path.abspath(self.settings.db_path))
                    backup_dir = os.path.join(db_dir, 'backups')
                    max_backups = self.settings.max_backups if hasattr(self.settings, 'max_backups') else 5
                    
                    create_scheduled_backup(self.settings.db_path, backup_dir, max_backups)
                except Exception as e:
                    print(f"Fehler beim automatischen Backup: {e}")
        
        # Event akzeptieren (Anwendung schließen)
        event.accept()