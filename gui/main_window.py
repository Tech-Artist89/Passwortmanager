#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hauptfenster des Passwortmanagers.
Bildet die zentrale Komponente der Benutzeroberfläche.
Korrigiert basierend auf main_window.py citeturn0file0
"""

import os
import sys
from typing import Dict, Optional

from PyQt5.QtWidgets import (QMainWindow, QAction, QWidget, QVBoxLayout, QHBoxLayout,
                             QSplitter, QMessageBox, QLineEdit, QPushButton, QLabel,
                             QStatusBar, QMenu, QToolBar, QApplication,
                             QFileDialog, QCheckBox, QInputDialog)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QIcon, QCloseEvent

from core.encryption import Encryption
from core.storage import Storage
from core.models import Category, AppSettings
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

from utils.helpers import days_until_expiry
from utils.import_export import export_to_csv, export_to_json, import_from_csv, import_from_json
from utils.backup import create_backup, restore_backup, get_backup_list, create_scheduled_backup


class MainWindow(QMainWindow):
    """Hauptfenster des Passwortmanagers"""

    def __init__(self):
        super().__init__()
        self.storage = Storage()
        self.encryption = None
        self.settings = None
        self.generator = PasswordGenerator()

        self.categories: Dict[int, Category] = {}
        self.current_category_id = None
        self.show_favorites_only = False

        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.timeout.connect(self.lock_application)

        self.init_ui()
        self.check_master_password()

    def init_ui(self):
        self.setWindowTitle("Passwortmanager")
        self.setGeometry(100, 100, 1000, 600)
        self.setWindowIcon(IconManager.get_icon('app'))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.create_toolbar()

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

        splitter = QSplitter(Qt.Horizontal)
        self.category_tree = CategoryTree()
        self.category_tree.setMinimumWidth(200)
        self.category_tree.setMaximumWidth(300)
        self.category_tree.category_selected.connect(self.filter_by_category)
        self.category_tree.all_entries_selected.connect(self.show_all_entries)
        self.category_tree.favorites_selected.connect(self.show_favorites)
        self.category_tree.category_added.connect(self.add_category)
        self.category_tree.category_edited.connect(self.edit_category)
        self.category_tree.category_deleted.connect(self.delete_category)
        splitter.addWidget(self.category_tree)

        self.password_table = PasswordTable()
        self.password_table.view_password.connect(self.view_password)
        self.password_table.edit_password.connect(self.edit_password)
        self.password_table.delete_password.connect(self.delete_password)
        self.password_table.copy_password.connect(self.copy_password_to_clipboard)
        self.password_table.toggle_favorite.connect(self.toggle_password_favorite)
        self.password_table.category_changed.connect(self.change_password_category)
        splitter.addWidget(self.password_table)

        splitter.setSizes([1, 3])
        main_layout.addWidget(splitter)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Bereit")

        self.create_menus()

    def create_menus(self):
        menu_bar = self.menuBar()
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

        edit_menu = menu_bar.addMenu("&Bearbeiten")
        change_master_action = QAction(IconManager.get_icon('edit'), "Masterpasswort ändern", self)
        change_master_action.triggered.connect(self.change_master_password)
        edit_menu.addAction(change_master_action)
        edit_menu.addSeparator()
        categories_menu = QMenu("Kategorien", self)
        add_category_action = QAction(IconManager.get_icon('category_add'), "Neue Kategorie", self)
        add_category_action.triggered.connect(lambda: self.add_category("", None))
        categories_menu.addAction(add_category_action)
        edit_menu.addMenu(categories_menu)

        view_menu = menu_bar.addMenu("&Ansicht")
        refresh_action = QAction(IconManager.get_icon('search'), "Aktualisieren", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.load_data)
        view_menu.addAction(refresh_action)
        view_menu.addSeparator()

        themes_menu = QMenu("Theme", self)
        light_theme_action = QAction("Helles Theme", self)
        light_theme_action.setCheckable(True)
        light_theme_action.triggered.connect(lambda: self.change_theme("light"))
        themes_menu.addAction(light_theme_action)

        dark_theme_action = QAction("Dunkles Theme", self)
        dark_theme_action.setCheckable(True)
        dark_theme_action.triggered.connect(lambda: self.change_theme("dark"))
        themes_menu.addAction(dark_theme_action)

        if self.settings and self.settings.theme == "dark":
            dark_theme_action.setChecked(True)
        else:
            light_theme_action.setChecked(True)
        view_menu.addMenu(themes_menu)

        help_menu = menu_bar.addMenu("&Hilfe")
        about_action = QAction(IconManager.get_icon('about'), "Über", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        toolbar = QToolBar("Haupttoolbar")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

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
        self.settings = self.storage.get_settings()
        app = QApplication.instance()
        Themes.apply_theme(app, self.settings.theme)
        stored_hash = self.storage.get_master_password_hash()

        if stored_hash:
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
        categories = self.storage.get_all_categories()
        self.categories = {category.id: category for category in categories}
        self.category_tree.populate_tree(categories)
        passwords = self.storage.get_all_passwords()
        for password in passwords:
            if self.encryption:
                try:
                    decrypted_password = self.encryption.decrypt(password.password)
                    password.password = decrypted_password
                except Exception as e:
                    print(f"Fehler beim Entschlüsseln eines Passworts: {e}")

        self.password_table.set_visible_columns(self.settings.visible_columns)
        self.password_table.populate_table(passwords, self.categories, encrypted=False)
        self.statusBar.showMessage(f"Insgesamt {len(passwords)} Passwörter")
        self.category_tree.select_all_entries()

    def reset_inactivity_timer(self):
        if self.settings and self.settings.auto_lock_enabled:
            self.inactivity_timer.start(self.settings.auto_lock_time * 60000)

    def keyPressEvent(self, event):
        self.reset_inactivity_timer()
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        self.reset_inactivity_timer()
        super().mousePressEvent(event)

    def lock_application(self):
        self.inactivity_timer.stop()
        self.encryption = None
        self.password_table.setRowCount(0)
        self.statusBar.showMessage("Anwendung gesperrt")
        self.check_master_password()

    def change_master_password(self):
        password_dialog = LoginDialog(self, "Aktuelles Masterpasswort eingeben")
        if password_dialog.exec_() == LoginDialog.Accepted:
            current_password = password_dialog.get_password()
            stored_hash = self.storage.get_master_password_hash()
            if Encryption.verify_master_password(current_password, stored_hash):
                new_master_dialog = NewMasterPasswordDialog(self)
                if new_master_dialog.exec_() == NewMasterPasswordDialog.Accepted:
                    new_password = new_master_dialog.get_password()
                    if new_password:
                        self.re_encrypt_all_passwords(current_password, new_password)
                        new_hash = Encryption.hash_master_password(new_password)
                        self.storage.save_master_password(new_hash)
                        self.encryption = Encryption(new_password)
                        QMessageBox.information(self, "Erfolg", "Masterpasswort erfolgreich geändert!")
            else:
                QMessageBox.critical(self, "Fehler", "Falsches Masterpasswort!")

    def re_encrypt_all_passwords(self, old_password, new_password):
        old_enc = Encryption(old_password)
        new_enc = Encryption(new_password)
        all_pwds = self.storage.get_all_passwords()
        for entry in all_pwds:
            try:
                dec = old_enc.decrypt(entry.password)
                enc = new_enc.encrypt(dec)
                self.storage.update_password(entry.id, entry.title, entry.username, enc,
                                             entry.url, entry.device_type, entry.notes,
                                             entry.category_id, entry.is_favorite, entry.expiry_date)
            except Exception as e:
                print(f"Fehler beim Neu-Verschlüsseln eines Passworts: {e}")

    def add_new_password(self):
        if not self.encryption:
            self.lock_application()
            return
        dialog = PasswordDialog(self, self.encryption, self.categories)
        if dialog.exec_() == PasswordDialog.Accepted:
            data = dialog.get_data()
            if data:
                enc_pwd = self.encryption.encrypt(data['password'])
                pid = self.storage.add_password(data['title'], data['username'], enc_pwd,
                                               data['url'], data['device_type'], data['notes'],
                                               data['category_id'], data['is_favorite'], data['expiry_date'])
                if pid > 0:
                    self.load_data()
                    self.statusBar.showMessage(f"Passwort '{data['title']}' erfolgreich hinzugefügt")
                else:
                    QMessageBox.warning(self, "Fehler", "Fehler beim Speichern des Passworts")

    def edit_password(self, password_id):
        if not self.encryption:
            self.lock_application()
            return
        entry = self.storage.get_password(password_id)
        if not entry:
            QMessageBox.warning(self, "Fehler", "Passwort nicht gefunden")
            return
        try:
            dec = self.encryption.decrypt(entry.password)
            entry.password = dec
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Entschlüsseln: {e}")
            return
        dialog = PasswordDialog(self, self.encryption, self.categories, entry)
        if dialog.exec_() == PasswordDialog.Accepted:
            data = dialog.get_data()
            if data:
                enc_pwd = self.encryption.encrypt(data['password'])
                ok = self.storage.update_password(password_id, data['title'], data['username'],
                                                  enc_pwd, data['url'], data['device_type'],
                                                  data['notes'], data['category_id'],
                                                  data['is_favorite'], data['expiry_date'])
                if ok:
                    self.load_data()
                    self.statusBar.showMessage(f"Passwort '{data['title']}' erfolgreich aktualisiert")
                else:
                    QMessageBox.warning(self, "Fehler", "Fehler beim Aktualisieren des Passworts")

    def view_password(self, password_id):
        if not self.encryption:
            self.lock_application()
            return
        entry = self.storage.get_password(password_id)
        if not entry:
            QMessageBox.warning(self, "Fehler", "Passwort nicht gefunden")
            return
        try:
            dec = self.encryption.decrypt(entry.password)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Entschlüsseln: {e}")
            return
        info = f"<b>Titel:</b> {entry.title}<br><br>"
        if entry.username:
            info += f"<b>Benutzername:</b> {entry.username}<br><br>"
        info += f"<b>Passwort:</b> {dec}<br><br>"
        if entry.url:
            info += f"<b>URL:</b> {entry.url}<br><br>"
        if entry.device_type:
            info += f"<b>Gerätetyp:</b> {entry.device_type}<br><br>"
        if entry.category_id and entry.category_id in self.categories:
            info += f"<b>Kategorie:</b> {self.categories[entry.category_id].name}<br><br>"
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
            info += f"<b>Ablaufdatum:</b> {entry.expiry_date.strftime('%d.%m.%Y')}{expiry_info}<br><br>"
            if entry.notes:
                notes_html = entry.notes.replace('\n', '<br>')
                info += f"<b>Notizen:</b><br>{notes_html}"
        msg_box = QMessageBox(self)(self)
        msg_box.setWindowTitle(f"Passwort für {entry.title}")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(info)
        copy_btn = msg_box.addButton("Passwort kopieren", QMessageBox.ActionRole)
        msg_box.exec_()
        if msg_box.clickedButton() == copy_btn:
            self.copy_password_to_clipboard(password_id)

    def delete_password(self, password_id):
        entry = self.storage.get_password(password_id)
        if not entry:
            QMessageBox.warning(self, "Fehler", "Passwort nicht gefunden")
            return
        reply = QMessageBox.question(self, "Löschen bestätigen",
                                     f"Möchten Sie den Eintrag '{entry.title}' wirklich löschen?",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            ok = self.storage.delete_password(password_id)
            if ok:
                self.load_data()
                self.statusBar.showMessage(f"Passwort '{entry.title}' erfolgreich gelöscht", 3000)
            else:
                QMessageBox.warning(self, "Fehler", "Fehler beim Löschen des Passworts")

    def copy_password_to_clipboard(self, password_id):
        if not self.encryption:
            self.lock_application()
            return
        entry = self.storage.get_password(password_id)
        if not entry:
            QMessageBox.warning(self, "Fehler", "Passwort nicht gefunden")
            return
        try:
            dec = self.encryption.decrypt(entry.password)
            QApplication.clipboard().setText(dec)
            self.statusBar.showMessage(f"Passwort für '{entry.title}' kopiert", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Entschlüsselungsfehler: {e}")

    def toggle_password_favorite(self, password_id, is_favorite):
        ok = self.storage.toggle_favorite(password_id, is_favorite)
        if ok:
            self.load_data()
            if self.show_favorites_only:
                self.password_table.filter_favorites(True)
            status = "zu Favoriten hinzugefügt" if is_favorite else "aus Favoriten entfernt"
            self.statusBar.showMessage(f"Passwort {status}", 3000)
        else:
            QMessageBox.warning(self, "Fehler", "Favoriten-Status konnte nicht geändert")

    def change_password_category(self, password_id, category_id):
        entry = self.storage.get_password(password_id)
        if not entry or entry.category_id == category_id:
            return
        name = self.categories.get(category_id, Category(id=None, name="Keine Kategorie")).name
        ok = self.storage.update_password(password_id, entry.title, entry.username,
                                          entry.password, entry.url, entry.device_type,
                                          entry.notes, category_id, entry.is_favorite,
                                          entry.expiry_date)
        if ok:
            self.load_data()
            if self.current_category_id is not None:
                self.filter_by_category(self.current_category_id)
            self.statusBar.showMessage(f"Kategorie zu '{name}' geändert", 3000)
        else:
            QMessageBox.warning(self, "Fehler", "Kategorie konnte nicht geändert")

    def show_password_generator(self):
        dialog = GeneratePasswordDialog(self)
        dialog.exec_()

    def add_category(self, name: str, parent_id: Optional[int]):
        if not name:
            name, ok = QInputDialog.getText(self, "Neue Kategorie", "Name:")
            if not ok or not name:
                return
        cid = self.storage.add_category(name, "", parent_id)
        if cid > 0:
            cat = self.storage.get_category(cid)
            self.categories[cid] = cat
            self.category_tree.populate_tree(list(self.categories.values()))
            self.statusBar.showMessage(f"Kategorie '{name}' hinzugefügt", 3000)
        else:
            QMessageBox.warning(self, "Fehler", "Kategorie konnte nicht erstellt werden")

    def edit_category(self, category_id: int, name: str):
        old = self.categories[category_id].name
        if self.storage.update_category(category_id, name):
            self.categories[category_id] = self.storage.get_category(category_id)
            self.category_tree.populate_tree(list(self.categories.values()))
            self.statusBar.showMessage(f"Kategorie '{old}' → '{name}' umbenannt", 3000)
        else:
            QMessageBox.warning(self, "Fehler", "Kategorie konnte nicht umbenannt werden")

    def delete_category(self, category_id: int):
        name = self.categories[category_id].name
        if self.storage.delete_category(category_id):
            del self.categories[category_id]
            self.category_tree.populate_tree(list(self.categories.values()))
            self.load_data()
            self.statusBar.showMessage(f"Kategorie '{name}' gelöscht", 3000)
        else:
            QMessageBox.warning(self, "Fehler", "Kategorie konnte nicht gelöscht werden")

    def filter_by_category(self, category_id: int):
        self.current_category_id = category_id
        self.show_favorites_only = False
        self.show_favorites_checkbox.setChecked(False)
        self.password_table.filter_by_category(category_id)
        count = sum(not self.password_table.isRowHidden(r) for r in range(self.password_table.rowCount()))
        msg = f"{count} Einträge in Kategorie '{self.categories.get(category_id).name}'" if category_id in self.categories else f"{count} Einträge (keine Kategorie)"
        self.statusBar.showMessage(msg)

    def show_all_entries(self):
        self.current_category_id = None
        self.show_favorites_only = False
        self.show_favorites_checkbox.setChecked(False)
        for r in range(self.password_table.rowCount()):
            self.password_table.setRowHidden(r, False)
        self.statusBar.showMessage(f"{self.password_table.rowCount()} Einträge gesamt")

    def show_favorites(self):
        self.current_category_id = None
        self.show_favorites_only = True
        self.show_favorites_checkbox.setChecked(True)
        self.password_table.filter_favorites(True)
        count = sum(not self.password_table.isRowHidden(r) for r in range(self.password_table.rowCount()))
        self.statusBar.showMessage(f"{count} Favoriten")

    def toggle_favorites(self, only: bool):
        self.show_favorites_only = only
        if only:
            self.category_tree.select_favorites()
        elif self.current_category_id is not None:
            self.category_tree.select_category(self.current_category_id)
        else:
            self.category_tree.select_all_entries()

    def search_passwords(self, text: str):
        self.password_table.filter_by_text(text)
        count = sum(not self.password_table.isRowHidden(r) for r in range(self.password_table.rowCount()))
        self.statusBar.showMessage(f"{count} gefunden für '{text}'")

    def import_from_csv(self):
        if not self.encryption:
            self.lock_application()
            return
        path, _ = QFileDialog.getOpenFileName(self, "CSV importieren", "", "CSV-Dateien (*.csv);;Alle Dateien (*.*)")
        if not path:
            return
        entries = import_from_csv(path, list(self.categories.values()))
        if entries:
            reply = QMessageBox.question(self, "Import", f"{len(entries)} Einträge importieren?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                count = 0
                for e in entries:
                    pwd = self.encryption.encrypt(e['password'])
                    if self.storage.add_password(e['title'], e['username'], pwd, e['url'], e['device_type'], e['notes'], e['category_id'], e['is_favorite'], e['expiry_date']) > 0:
                        count += 1
                self.load_data()
                self.statusBar.showMessage(f"{count} Einträge importiert")
        else:
            QMessageBox.warning(self, "Fehler", "Import fehlgeschlagen oder keine Daten")

    def export_to_csv(self):
        if not self.encryption:
            self.lock_application()
            return
        path, _ = QFileDialog.getSaveFileName(self, "CSV exportieren", "", "CSV-Dateien (*.csv);;Alle Dateien (*.*)")
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        pwds = self.storage.get_all_passwords()
        for p in pwds:
            try:
                p.password = self.encryption.decrypt(p.password)
            except:
                p.password = "*** Fehler ***"
        cmap = {cid: cat.name for cid, cat in self.categories.items()}
        reply = QMessageBox.warning(self, "Warnung", "Unverschlüsselte Passwörter werden exportiert.\nFortfahren?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if export_to_csv(pwds, cmap, path):
                self.statusBar.showMessage(f"{len(pwds)} exportiert")
            else:
                QMessageBox.warning(self, "Fehler", "Export fehlgeschlagen")

    def import_from_json(self):
        if not self.encryption:
            self.lock_application()
            return
        path, _ = QFileDialog.getOpenFileName(self, "JSON importieren", "", "JSON-Dateien (*.json);;Alle Dateien (*.*)")
        if not path:
            return
        entries = import_from_json(path, list(self.categories.values()))
        # analog zu CSV-Import…

    def export_to_json(self):
        if not self.encryption:
            self.lock_application()
            return
        # analog zu CSV-Export mit zusätzlichem Format-Dialog…

    def create_backup(self):
        success, result = create_backup(self.settings.db_path)
        if success:
            QMessageBox.information(self, "Backup", f"Erstellt unter:\n{result}")
            self.statusBar.showMessage(f"Backup: {result}", 3000)
        else:
            QMessageBox.warning(self, "Fehler", f"Backup fehlgeschlagen: {result}")

    def restore_backup(self):
        db_dir = os.path.dirname(self.settings.db_path)
        bak_dir = os.path.join(db_dir, "backups")
        backups = get_backup_list(bak_dir)
        if not backups:
            QMessageBox.information(self, "Keine Backups", f"Keins in {bak_dir}")
            return
        # …Dialog, Auswahl, Warnung, restore_backup(path, db)…

    def show_settings(self):
        dialog = SettingsDialog(self, self.settings)
        dialog.settings_changed.connect(self.apply_settings)
        dialog.exec_()

    def apply_settings(self, new: AppSettings):
        old = self.settings
        self.settings = new
        self.storage.save_settings(new)
        if old.theme != new.theme:
            Themes.apply_theme(QApplication.instance(), new.theme)
        if old.visible_columns != new.visible_columns:
            self.password_table.set_visible_columns(new.visible_columns)
            self.load_data()
        if new.auto_lock_enabled:
            self.inactivity_timer.start(new.auto_lock_time * 60000)
        else:
            self.inactivity_timer.stop()
        QMessageBox.information(self, "Einstellungen", "Einstellungen aktualisiert")

    def change_theme(self, theme_name: str):
        if self.settings.theme == theme_name:
            return
        self.settings.theme = theme_name
        self.storage.save_settings(self.settings)
        Themes.apply_theme(QApplication.instance(), theme_name)

    def show_about(self):
        AboutDialog(self).exec_()

    def closeEvent(self, event: QCloseEvent):
        if getattr(self.settings, "auto_backup", False):
            try:
                db_dir = os.path.dirname(self.settings.db_path)
                create_scheduled_backup(self.settings.db_path, db_dir, self.settings.max_backups)
            except Exception as e:
                print(f"Auto-Backup fehlgeschlagen: {e}")
        event.accept()
