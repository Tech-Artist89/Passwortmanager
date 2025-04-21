#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ressourcen-Modul für den Passwortmanager.
Verwaltet Zugriff auf Icons und andere Ressourcen für die Anwendung.
"""

import os
from PyQt5.QtGui import QIcon, QPixmap
from utils.helpers import get_resource_path


class IconManager:
    """Klasse zur Verwaltung von Icons"""
    
    # Icon-Pfade relativ zum Ressourcenverzeichnis
    ICON_PATHS = {
        # Anwendungsicons
        'app': 'icons/app_icon.png',
        'lock': 'icons/lock.png',
        'unlock': 'icons/unlock.png',
        
        # Aktionsicons
        'add': 'icons/add.png',
        'edit': 'icons/edit.png',
        'delete': 'icons/delete.png',
        'save': 'icons/save.png',
        'cancel': 'icons/cancel.png',
        'view': 'icons/view.png',
        'copy': 'icons/copy.png',
        'search': 'icons/search.png',
        'generate': 'icons/generate.png',
        'favorite': 'icons/favorite.png',
        'favorite_off': 'icons/favorite_off.png',
        
        # Kategorieicons
        'category': 'icons/category.png',
        'category_add': 'icons/category_add.png',
        'category_edit': 'icons/category_edit.png',
        'category_delete': 'icons/category_delete.png',
        
        # Einstellungsicons
        'settings': 'icons/settings.png',
        'theme': 'icons/theme.png',
        'backup': 'icons/backup.png',
        'restore': 'icons/restore.png',
        'import': 'icons/import.png',
        'export': 'icons/export.png',
        
        # Geräteicons
        'device_phone': 'icons/device_phone.png',
        'device_laptop': 'icons/device_laptop.png',
        'device_desktop': 'icons/device_desktop.png',
        'device_other': 'icons/device_other.png',
        
        # Sonstige Icons
        'info': 'icons/info.png',
        'warning': 'icons/warning.png',
        'error': 'icons/error.png',
        'help': 'icons/help.png',
        'about': 'icons/about.png'
    }
    
    @classmethod
    def get_icon(cls, icon_name):
        """
        Gibt ein QIcon für den angegebenen Icon-Namen zurück
        
        Args:
            icon_name (str): Name des Icons
            
        Returns:
            QIcon: Das angeforderte Icon oder ein Standard-Icon, falls nicht gefunden
        """
        if icon_name not in cls.ICON_PATHS:
            print(f"Warnung: Icon '{icon_name}' nicht gefunden")
            return QIcon()
        
        icon_path = get_resource_path(os.path.join('resources', cls.ICON_PATHS[icon_name]))
        
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        else:
            print(f"Warnung: Icon-Datei nicht gefunden: {icon_path}")
            return QIcon()
    
    @classmethod
    def get_pixmap(cls, icon_name):
        """
        Gibt ein QPixmap für den angegebenen Icon-Namen zurück
        
        Args:
            icon_name (str): Name des Icons
            
        Returns:
            QPixmap: Das angeforderte Pixmap oder ein leeres Pixmap, falls nicht gefunden
        """
        if icon_name not in cls.ICON_PATHS:
            print(f"Warnung: Icon '{icon_name}' nicht gefunden")
            return QPixmap()
        
        icon_path = get_resource_path(os.path.join('resources', cls.ICON_PATHS[icon_name]))
        
        if os.path.exists(icon_path):
            return QPixmap(icon_path)
        else:
            print(f"Warnung: Icon-Datei nicht gefunden: {icon_path}")
            return QPixmap()
    
    @classmethod
    def get_category_icon(cls, category_name):
        """
        Gibt ein passendes Icon für eine Kategorie zurück
        
        Args:
            category_name (str): Name der Kategorie
            
        Returns:
            QIcon: Ein passendes Icon für die Kategorie
        """
        # Bestimmte Icons für bestimmte Kategorienamen
        category_mapping = {
            'banking': 'device_other',  # Später durch ein spezielles Banking-Icon ersetzen
            'email': 'device_other',    # Später durch ein spezielles Email-Icon ersetzen
            'social': 'device_other',   # Später durch ein spezielles Social-Icon ersetzen
            'shopping': 'device_other', # Später durch ein spezielles Shopping-Icon ersetzen
            'work': 'device_other',     # Später durch ein spezielles Work-Icon ersetzen
            'personal': 'device_other', # Später durch ein spezielles Personal-Icon ersetzen
        }
        
        # Standardisiere den Kategorienamen (Kleinbuchstaben)
        normalized_name = category_name.lower()
        
        # Suche nach passendem Icon
        for key, icon in category_mapping.items():
            if key in normalized_name:
                return cls.get_icon(icon)
        
        # Standardicon für Kategorien zurückgeben
        return cls.get_icon('category')
    
    @classmethod
    def get_device_icon(cls, device_type):
        """
        Gibt ein passendes Icon für einen Gerätetyp zurück
        
        Args:
            device_type (str): Typ des Geräts
            
        Returns:
            QIcon: Ein passendes Icon für den Gerätetyp
        """
        if not device_type:
            return cls.get_icon('device_other')
        
        device_type = device_type.lower()
        
        if 'handy' in device_type or 'phone' in device_type or 'smartphone' in device_type:
            return cls.get_icon('device_phone')
        elif 'laptop' in device_type or 'notebook' in device_type:
            return cls.get_icon('device_laptop')
        elif 'computer' in device_type or 'pc' in device_type or 'desktop' in device_type:
            return cls.get_icon('device_desktop')
        else:
            return cls.get_icon('device_other')