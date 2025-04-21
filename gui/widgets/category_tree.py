#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CategoryTree-Widget für den Passwortmanager.
Stellt eine Baumansicht für die Kategorien bereit.
"""

from PyQt5.QtWidgets import (QTreeWidget, QTreeWidgetItem, QMenu, QAction, 
                             QMessageBox, QInputDialog, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

from core.models import Category
from gui.styles.resources import IconManager


class CategoryTree(QTreeWidget):
    """Baumansicht für die Kategorien des Passwortmanagers"""
    
    # Signale für Aktionen
    category_selected = pyqtSignal(int)  # Kategorie ausgewählt
    category_added = pyqtSignal(str, int)  # Neue Kategorie (Name, Parent-ID)
    category_edited = pyqtSignal(int, str)  # Kategorie bearbeitet (ID, Neuer Name)
    category_deleted = pyqtSignal(int)  # Kategorie gelöscht (ID)
    all_entries_selected = pyqtSignal()  # Alle Einträge ausgewählt
    favorites_selected = pyqtSignal()  # Favoriten ausgewählt
    
    def __init__(self, parent=None):
        """
        Initialisiert die Kategorien-Baumansicht
        
        Args:
            parent (QWidget): Übergeordnetes Widget
        """
        super().__init__(parent)
        
        self.categories = {}  # Dictionary für Kategorien (ID -> Category)
        self.item_map = {}  # Zuordnung von Kategorie-IDs zu TreeWidgetItems
        
        self._setup_tree()
    
    def _setup_tree(self):
        """Richtet die Baumansicht ein"""
        # Einstellungen für die Baumansicht
        self.setHeaderHidden(True)
        self.setColumnCount(1)
        self.setIndentation(20)
        self.setAnimated(True)
        self.setSelectionMode(QTreeWidget.SingleSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # "Alle Einträge" und "Favoriten" als Spezialknoten
        all_item = QTreeWidgetItem(self)
        all_item.setText(0, "Alle Einträge")
        all_item.setIcon(0, IconManager.get_icon('lock'))
        all_item.setData(0, Qt.UserRole, "all")
        
        favorites_item = QTreeWidgetItem(self)
        favorites_item.setText(0, "Favoriten")
        favorites_item.setIcon(0, IconManager.get_icon('favorite'))
        favorites_item.setData(0, Qt.UserRole, "favorites")
        
        # Kategorie-Überschrift
        category_header = QTreeWidgetItem(self)
        category_header.setText(0, "Kategorien")
        category_header.setData(0, Qt.UserRole, "header")
        category_header.setIcon(0, IconManager.get_icon('category'))
        category_header.setFlags(category_header.flags() & ~Qt.ItemIsSelectable)
        
        # Verbinde Signal für Auswahl
        self.itemClicked.connect(self._on_item_selected)
    
    def _on_item_selected(self, item, column):
        """
        Wird aufgerufen, wenn ein Element in der Baumansicht ausgewählt wird
        
        Args:
            item (QTreeWidgetItem): Das ausgewählte Element
            column (int): Die ausgewählte Spalte
        """
        item_data = item.data(0, Qt.UserRole)
        
        if item_data == "all":
            self.all_entries_selected.emit()
        elif item_data == "favorites":
            self.favorites_selected.emit()
        elif isinstance(item_data, int):
            # Kategorie wurde ausgewählt
            self.category_selected.emit(item_data)
    
    def populate_tree(self, categories):
        """
        Füllt die Baumansicht mit Kategorien
        
        Args:
            categories (List[Category]): Liste der Kategorien
        """
        # Aktuelle Kategorie speichern
        self.categories = {category.id: category for category in categories}
        self.item_map = {}
        
        # Kategorie-Überschrift finden
        category_header = None
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.data(0, Qt.UserRole) == "header":
                category_header = item
                break
        
        if not category_header:
            # Sollte nicht vorkommen, aber für die Sicherheit
            return
        
        # Bestehende Kategorien entfernen
        while category_header.childCount() > 0:
            category_header.removeChild(category_header.child(0))
        
        # Root-Kategorien hinzufügen (ohne Parent)
        for category in categories:
            if category.parent_id is None:
                self._add_category_item(category, category_header)
        
        # Untergeordnete Kategorien hinzufügen
        for category in categories:
            if category.parent_id is not None and category.parent_id in self.item_map:
                parent_item = self.item_map[category.parent_id]
                self._add_category_item(category, parent_item)
        
        # Erste Ebene expandieren
        self.expandItem(category_header)
    
    def _add_category_item(self, category, parent_item):
        """
        Fügt ein Kategorie-Element zur Baumansicht hinzu
        
        Args:
            category (Category): Die Kategorie
            parent_item (QTreeWidgetItem): Das übergeordnete Element
        """
        item = QTreeWidgetItem(parent_item)
        item.setText(0, category.name)
        item.setData(0, Qt.UserRole, category.id)
        
        # Icon basierend auf Kategoriename
        item.setIcon(0, IconManager.get_category_icon(category.name))
        
        # Element in der Map speichern
        self.item_map[category.id] = item
    
    def _show_context_menu(self, position):
        """
        Zeigt ein Kontextmenü an der angegebenen Position
        
        Args:
            position (QPoint): Position für das Kontextmenü
        """
        item = self.itemAt(position)
        if not item:
            return
        
        # Daten des Elements
        item_data = item.data(0, Qt.UserRole)
        
        # Kontextmenü erstellen
        context_menu = QMenu(self)
        
        if item_data == "header":
            # Nur "Neue Kategorie" für die Überschrift
            add_action = QAction(IconManager.get_icon('category_add'), "Neue Kategorie", self)
            context_menu.addAction(add_action)
            
            action = context_menu.exec_(self.mapToGlobal(position))
            
            if action == add_action:
                self._add_category()
                
        elif isinstance(item_data, int):
            # Vollständiges Menü für Kategorien
            add_child_action = QAction(IconManager.get_icon('category_add'), "Neue Unterkategorie", self)
            edit_action = QAction(IconManager.get_icon('category_edit'), "Umbenennen", self)
            delete_action = QAction(IconManager.get_icon('category_delete'), "Löschen", self)
            
            context_menu.addAction(add_child_action)
            context_menu.addAction(edit_action)
            context_menu.addSeparator()
            context_menu.addAction(delete_action)
            
            action = context_menu.exec_(self.mapToGlobal(position))
            
            if action == add_child_action:
                self._add_category(item_data)
            elif action == edit_action:
                self._edit_category(item_data)
            elif action == delete_action:
                self._delete_category(item_data)
    
    def _add_category(self, parent_id=None):
        """
        Fügt eine neue Kategorie hinzu
        
        Args:
            parent_id (int, optional): ID der übergeordneten Kategorie
        """
        # Dialog für neuen Namen
        name, ok = QInputDialog.getText(
            self, 
            "Neue Kategorie", 
            "Kategoriename:", 
            text=""
        )
        
        if ok and name:
            # Signal senden
            self.category_added.emit(name, parent_id)
    
    def _edit_category(self, category_id):
        """
        Bearbeitet eine Kategorie
        
        Args:
            category_id (int): ID der Kategorie
        """
        if category_id not in self.categories:
            return
        
        category = self.categories[category_id]
        
        # Dialog für neuen Namen
        name, ok = QInputDialog.getText(
            self, 
            "Kategorie umbenennen", 
            "Neuer Name:", 
            text=category.name
        )
        
        if ok and name and name != category.name:
            # Signal senden
            self.category_edited.emit(category_id, name)
    
    def _delete_category(self, category_id):
        """
        Löscht eine Kategorie
        
        Args:
            category_id (int): ID der Kategorie
        """
        if category_id not in self.categories:
            return
        
        category = self.categories[category_id]
        
        # Bestätigung
        reply = QMessageBox.question(
            self,
            "Kategorie löschen",
            f"Möchten Sie die Kategorie '{category.name}' wirklich löschen?\n\n"
            "Die Passwörter in dieser Kategorie werden keiner Kategorie zugeordnet.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Signal senden
            self.category_deleted.emit(category_id)
    
    def select_all_entries(self):
        """Wählt den 'Alle Einträge' Knoten aus"""
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.data(0, Qt.UserRole) == "all":
                self.setCurrentItem(item)
                self.all_entries_selected.emit()
                break
    
    def select_favorites(self):
        """Wählt den 'Favoriten' Knoten aus"""
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.data(0, Qt.UserRole) == "favorites":
                self.setCurrentItem(item)
                self.favorites_selected.emit()
                break
    
    def select_category(self, category_id):
        """
        Wählt eine Kategorie aus
        
        Args:
            category_id (int): ID der Kategorie
        """
        if category_id in self.item_map:
            self.setCurrentItem(self.item_map[category_id])
            self.category_selected.emit(category_id)