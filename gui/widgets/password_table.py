#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PasswordTable-Widget für den Passwortmanager.
Stellt eine angepasste Tabelle für die Anzeige von Passworteinträgen bereit.
"""

from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QPushButton, 
                             QHBoxLayout, QWidget, QHeaderView, QAbstractItemView,
                             QMenu, QAction)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QColor

from core.models import PasswordEntry, Category
from gui.styles.resources import IconManager
from utils.helpers import format_date, truncate_string, is_expired, days_until_expiry


class PasswordTable(QTableWidget):
    """Angepasste Tabelle für Passworteinträge"""
    
    # Signale für Aktionen
    view_password = pyqtSignal(int)
    edit_password = pyqtSignal(int)
    delete_password = pyqtSignal(int)
    copy_password = pyqtSignal(int)
    toggle_favorite = pyqtSignal(int, bool)
    category_changed = pyqtSignal(int, int)
    
    # Liste der verfügbaren Spalten
    AVAILABLE_COLUMNS = [
        {"name": "title", "title": "Titel", "width": 150},
        {"name": "username", "title": "Benutzername", "width": 120},
        {"name": "url", "title": "URL/Gerät", "width": 150},
        {"name": "category", "title": "Kategorie", "width": 100},
        {"name": "favorite", "title": "Favorit", "width": 50},
        {"name": "expiry", "title": "Ablaufdatum", "width": 100},
        {"name": "updated_at", "title": "Geändert", "width": 120},
        {"name": "actions", "title": "Aktionen", "width": 180},
    ]
    
    def __init__(self, parent=None, visible_columns=None):
        """
        Initialisiert die Passwort-Tabelle
        
        Args:
            parent (QWidget): Übergeordnetes Widget
            visible_columns (List[str], optional): Liste der sichtbaren Spalten
        """
        super().__init__(parent)
        
        self.entries = []
        self.categories = {}
        self.encrypted = True
        
        # Konfiguration der sichtbaren Spalten
        if visible_columns is None:
            self.visible_columns = ["title", "username", "category", "updated_at", "actions"]
        else:
            self.visible_columns = visible_columns
        
        self._setup_table()
    
    def _setup_table(self):
        """Richtet die Tabelle ein"""
        # Anzahl der Spalten basierend auf den sichtbaren Spalten
        self.setColumnCount(len(self.visible_columns))
        
        # Spaltentitel setzen
        header_labels = []
        for column_name in self.visible_columns:
            for column_info in self.AVAILABLE_COLUMNS:
                if column_info["name"] == column_name:
                    header_labels.append(column_info["title"])
                    break
        
        self.setHorizontalHeaderLabels(header_labels)
        
        # Tabelleneigenschaften
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.setShowGrid(True)
        
        # Header-Einstellungen
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        
        # Spaltenbreiten
        for i, column_name in enumerate(self.visible_columns):
            for column_info in self.AVAILABLE_COLUMNS:
                if column_info["name"] == column_name:
                    if "width" in column_info:
                        self.setColumnWidth(i, column_info["width"])
                    break
    
    def set_visible_columns(self, visible_columns):
        """
        Ändert die sichtbaren Spalten
        
        Args:
            visible_columns (List[str]): Liste der sichtbaren Spalten
        """
        self.visible_columns = visible_columns
        self._setup_table()
        
        # Aktualisiere die Tabelle mit den vorhandenen Daten
        if self.entries:
            self.populate_table(self.entries, self.categories, self.encrypted)
    
    def populate_table(self, entries, categories=None, encrypted=True):
        """
        Füllt die Tabelle mit Passworteinträgen
        
        Args:
            entries (List[PasswordEntry]): Liste der Passworteinträge
            categories (Dict[int, Category], optional): Dictionary der Kategorien (ID -> Category)
            encrypted (bool): Ob die Passwörter verschlüsselt sind
        """
        self.entries = entries
        self.categories = categories or {}
        self.encrypted = encrypted
        
        # Tabelle leeren
        self.setRowCount(0)
        
        # Einträge hinzufügen
        for row, entry in enumerate(entries):
            self.insertRow(row)
            
            # Daten für die einzelnen Spalten einfügen
            for col, column_name in enumerate(self.visible_columns):
                if column_name == "title":
                    # Titel
                    item = QTableWidgetItem(entry.title)
                    # ID als verstecktes Attribut speichern
                    item.setData(Qt.UserRole, entry.id)
                    self.setItem(row, col, item)
                    
                elif column_name == "username":
                    # Benutzername
                    username = entry.username or ""
                    self.setItem(row, col, QTableWidgetItem(username))
                    
                elif column_name == "url":
                    # URL oder Gerätetyp
                    url_device = entry.url if entry.url else entry.device_type if entry.device_type else ""
                    self.setItem(row, col, QTableWidgetItem(url_device))
                    
                elif column_name == "category":
                    # Kategorie
                    category_name = ""
                    if entry.category_id and entry.category_id in self.categories:
                        category_name = self.categories[entry.category_id].name
                    self.setItem(row, col, QTableWidgetItem(category_name))
                    
                elif column_name == "favorite":
                    # Favorit
                    favorite_widget = QWidget()
                    layout = QHBoxLayout(favorite_widget)
                    layout.setContentsMargins(2, 2, 2, 2)
                    layout.setAlignment(Qt.AlignCenter)
                    
                    favorite_btn = QPushButton()
                    favorite_btn.setCheckable(True)
                    favorite_btn.setChecked(entry.is_favorite)
                    favorite_btn.setFixedSize(24, 24)
                    favorite_btn.setIcon(IconManager.get_icon('favorite' if entry.is_favorite else 'favorite_off'))
                    favorite_btn.clicked.connect(lambda checked, e_id=entry.id: self.toggle_favorite.emit(e_id, checked))
                    layout.addWidget(favorite_btn)
                    
                    self.setCellWidget(row, col, favorite_widget)
                    
                elif column_name == "expiry":
                    # Ablaufdatum
                    expiry_text = ""
                    item = QTableWidgetItem()
                    
                    if entry.expiry_date:
                        expiry_text = format_date(entry.expiry_date.isoformat()).split()[0]  # Nur Datum
                        days = days_until_expiry(entry.expiry_date)
                        
                        if days is not None:
                            if days < 0:
                                # Abgelaufen
                                item.setForeground(QColor(255, 0, 0))  # Rot
                            elif days < 7:
                                # Läuft bald ab
                                item.setForeground(QColor(255, 165, 0))  # Orange
                    
                    item.setText(expiry_text)
                    self.setItem(row, col, item)
                    
                elif column_name == "updated_at":
                    # Änderungsdatum
                    updated_at = ""
                    if entry.updated_at:
                        updated_at = format_date(entry.updated_at.isoformat())
                    self.setItem(row, col, QTableWidgetItem(updated_at))
                    
                elif column_name == "actions":
                    # Aktionen (Buttons)
                    actions_widget = QWidget()
                    layout = QHBoxLayout(actions_widget)
                    layout.setContentsMargins(2, 2, 2, 2)
                    
                    # Button zum Anzeigen
                    view_button = QPushButton()
                    view_button.setIcon(IconManager.get_icon('view'))
                    view_button.setFixedSize(28, 28)
                    view_button.setToolTip("Anzeigen")
                    view_button.setProperty("class", "view")
                    view_button.clicked.connect(lambda _, e_id=entry.id: self.view_password.emit(e_id))
                    layout.addWidget(view_button)
                    
                    # Button zum Bearbeiten
                    edit_button = QPushButton()
                    edit_button.setIcon(IconManager.get_icon('edit'))
                    edit_button.setFixedSize(28, 28)
                    edit_button.setToolTip("Bearbeiten")
                    edit_button.setProperty("class", "edit")
                    edit_button.clicked.connect(lambda _, e_id=entry.id: self.edit_password.emit(e_id))
                    layout.addWidget(edit_button)
                    
                    # Button zum Kopieren des Passworts
                    copy_button = QPushButton()
                    copy_button.setIcon(IconManager.get_icon('copy'))
                    copy_button.setFixedSize(28, 28)
                    copy_button.setToolTip("Passwort kopieren")
                    copy_button.clicked.connect(lambda _, e_id=entry.id: self.copy_password.emit(e_id))
                    layout.addWidget(copy_button)
                    
                    # Button zum Löschen
                    delete_button = QPushButton()
                    delete_button.setIcon(IconManager.get_icon('delete'))
                    delete_button.setFixedSize(28, 28)
                    delete_button.setToolTip("Löschen")
                    delete_button.setProperty("class", "delete")
                    delete_button.clicked.connect(lambda _, e_id=entry.id: self.delete_password.emit(e_id))
                    layout.addWidget(delete_button)
                    
                    self.setCellWidget(row, col, actions_widget)
        
        # Zeilen mit abgelaufenen Passwörtern hervorheben
        for row in range(self.rowCount()):
            entry = entries[row]
            if entry.expiry_date and is_expired(entry.expiry_date):
                # Markiere die Zeile mit abgelaufenem Passwort
                for col in range(self.columnCount()):
                    item = self.item(row, col)
                    if item:
                        item.setBackground(QColor(255, 200, 200))  # Helles Rot
    
    def _show_context_menu(self, position):
        """
        Zeigt ein Kontextmenü an der angegebenen Position
        
        Args:
            position (QPoint): Position für das Kontextmenü
        """
        row = self.rowAt(position.y())
        if row < 0:
            return
        
        entry_id = self.item(row, 0).data(Qt.UserRole)
        
        # Kontextmenü erstellen
        context_menu = QMenu(self)
        
        view_action = QAction(IconManager.get_icon('view'), "Anzeigen", self)
        edit_action = QAction(IconManager.get_icon('edit'), "Bearbeiten", self)
        copy_action = QAction(IconManager.get_icon('copy'), "Passwort kopieren", self)
        delete_action = QAction(IconManager.get_icon('delete'), "Löschen", self)
        
        is_favorite = False
        for entry in self.entries:
            if entry.id == entry_id:
                is_favorite = entry.is_favorite
                break
        
        favorite_action = QAction(
            IconManager.get_icon('favorite_off' if is_favorite else 'favorite'),
            "Aus Favoriten entfernen" if is_favorite else "Zu Favoriten hinzufügen", 
            self
        )
        
        # Aktionen hinzufügen
        context_menu.addAction(view_action)
        context_menu.addAction(edit_action)
        context_menu.addAction(copy_action)
        context_menu.addSeparator()
        context_menu.addAction(favorite_action)
        context_menu.addSeparator()
        context_menu.addAction(delete_action)
        
        # Kategorien-Untermenü hinzufügen, wenn Kategorien vorhanden sind
        if self.categories:
            category_menu = QMenu("Kategorie ändern", self)
            context_menu.addSeparator()
            context_menu.addMenu(category_menu)
            
            # Aktuelle Kategorie-ID des Eintrags ermitteln
            current_category_id = None
            for entry in self.entries:
                if entry.id == entry_id:
                    current_category_id = entry.category_id
                    break
            
            # Keine Kategorie Option
            none_action = QAction("Keine Kategorie", self)
            none_action.setCheckable(True)
            none_action.setChecked(current_category_id is None)
            none_action.triggered.connect(lambda: self.category_changed.emit(entry_id, None))
            category_menu.addAction(none_action)
            
            category_menu.addSeparator()
            
            # Kategorie-Aktionen hinzufügen
            for category_id, category in self.categories.items():
                category_action = QAction(category.name, self)
                category_action.setCheckable(True)
                category_action.setChecked(current_category_id == category_id)
                category_action.triggered.connect(
                    lambda checked, c_id=category_id: self.category_changed.emit(entry_id, c_id)
                )
                category_menu.addAction(category_action)
        
        # Menü anzeigen und Aktion ausführen
        action = context_menu.exec_(self.mapToGlobal(position))
        
        if action == view_action:
            self.view_password.emit(entry_id)
        elif action == edit_action:
            self.edit_password.emit(entry_id)
        elif action == copy_action:
            self.copy_password.emit(entry_id)
        elif action == delete_action:
            self.delete_password.emit(entry_id)
        elif action == favorite_action:
            self.toggle_favorite.emit(entry_id, not is_favorite)
    
    def filter_by_category(self, category_id=None):
        """
        Filtert die Tabelle nach Kategorie
        
        Args:
            category_id (int, optional): ID der Kategorie oder None für alle Einträge
        """
        if category_id is None:
            # Alle Einträge anzeigen
            for row in range(self.rowCount()):
                self.setRowHidden(row, False)
            return
        
        # Einträge filtern
        for row in range(self.rowCount()):
            entry_id = self.item(row, 0).data(Qt.UserRole)
            
            show_row = False
            for entry in self.entries:
                if entry.id == entry_id and entry.category_id == category_id:
                    show_row = True
                    break
            
            self.setRowHidden(row, not show_row)
    
    def filter_by_text(self, search_text):
        """
        Filtert die Tabelle nach Suchtext
        
        Args:
            search_text (str): Suchtext
        """
        if not search_text:
            # Alle Einträge anzeigen
            for row in range(self.rowCount()):
                self.setRowHidden(row, False)
            return
        
        search_text = search_text.lower()
        
        # Einträge filtern
        for row in range(self.rowCount()):
            entry_id = self.item(row, 0).data(Qt.UserRole)
            
            # Suche nach Entry mit passender ID
            show_row = False
            for entry in self.entries:
                if entry.id == entry_id:
                    # Suche in verschiedenen Feldern
                    if (search_text in entry.title.lower() or 
                        (entry.username and search_text in entry.username.lower()) or
                        (entry.url and search_text in entry.url.lower()) or
                        (entry.device_type and search_text in entry.device_type.lower()) or
                        (entry.notes and search_text in entry.notes.lower())):
                        show_row = True
                        break
                    
                    # Suche in Kategoriename
                    if entry.category_id and entry.category_id in self.categories:
                        if search_text in self.categories[entry.category_id].name.lower():
                            show_row = True
                            break
            
            self.setRowHidden(row, not show_row)
    
    def filter_favorites(self, show_only_favorites=False):
        """
        Filtert die Tabelle nach Favoriten
        
        Args:
            show_only_favorites (bool): Wenn True, werden nur Favoriten angezeigt
        """
        if not show_only_favorites:
            # Alle Einträge anzeigen
            for row in range(self.rowCount()):
                self.setRowHidden(row, False)
            return
        
        # Nur Favoriten anzeigen
        for row in range(self.rowCount()):
            entry_id = self.item(row, 0).data(Qt.UserRole)
            
            show_row = False
            for entry in self.entries:
                if entry.id == entry_id and entry.is_favorite:
                    show_row = True
                    break
            
            self.setRowHidden(row, not show_row)