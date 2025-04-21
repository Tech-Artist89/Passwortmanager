#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Datenmodelle für den Passwortmanager.
Definiert die Datenstrukturen für Passwörter, Kategorien und andere Entitäten.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime


@dataclass
class Category:
    """Datenklasse für eine Kategorie"""
    id: int
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        """Wird nach der Initialisierung aufgerufen, um Standardwerte zu setzen"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    @classmethod
    def from_dict(cls, data):
        """
        Erstellt eine Category-Instanz aus einem Dictionary
        
        Args:
            data (dict): Dictionary mit den Daten für die Kategorie
            
        Returns:
            Category: Die erstellte Category-Instanz
        """
        # Konvertiere ISO-String zu datetime, falls vorhanden
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            
        return cls(**data)
    
    def to_dict(self) -> dict:
        """
        Konvertiert die Category-Instanz in ein Dictionary
        
        Returns:
            dict: Die Kategorie als Dictionary
        """
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'parent_id': self.parent_id,
            'icon': self.icon,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        return result


@dataclass
class PasswordEntry:
    """Datenklasse für einen Passwort-Eintrag"""
    id: Optional[int] = None
    title: str = ""
    username: Optional[str] = None
    password: str = ""
    url: Optional[str] = None
    device_type: Optional[str] = None
    notes: Optional[str] = None
    category_id: Optional[int] = None
    is_favorite: bool = False
    expiry_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Wird nach der Initialisierung aufgerufen, um Standardwerte zu setzen"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    @classmethod
    def from_dict(cls, data):
        """
        Erstellt eine PasswordEntry-Instanz aus einem Dictionary
        
        Args:
            data (dict): Dictionary mit den Daten für den Passwort-Eintrag
            
        Returns:
            PasswordEntry: Die erstellte PasswordEntry-Instanz
        """
        # Konvertiere ISO-String zu datetime, falls vorhanden
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if isinstance(data.get('expiry_date'), str) and data.get('expiry_date'):
            data['expiry_date'] = datetime.fromisoformat(data['expiry_date'])
            
        return cls(**data)
    
    def to_dict(self) -> dict:
        """
        Konvertiert die PasswordEntry-Instanz in ein Dictionary
        
        Returns:
            dict: Der Passwort-Eintrag als Dictionary
        """
        result = {
            'id': self.id,
            'title': self.title,
            'username': self.username,
            'password': self.password,
            'url': self.url,
            'device_type': self.device_type,
            'notes': self.notes,
            'category_id': self.category_id,
            'is_favorite': self.is_favorite,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        return result


@dataclass
class AppSettings:
    """Datenklasse für die Anwendungseinstellungen"""
    theme: str = "light"  # light oder dark
    language: str = "de"  # de oder en
    visible_columns: List[str] = None
    auto_lock_enabled: bool = False
    auto_lock_time: int = 5  # Minuten
    db_path: str = "passwortmanager.db"
    
    def __post_init__(self):
        """Wird nach der Initialisierung aufgerufen, um Standardwerte zu setzen"""
        if self.visible_columns is None:
            self.visible_columns = ["title", "username", "category", "updated_at"]
    
    @classmethod
    def from_dict(cls, data):
        """
        Erstellt eine AppSettings-Instanz aus einem Dictionary
        
        Args:
            data (dict): Dictionary mit den Daten für die Einstellungen
            
        Returns:
            AppSettings: Die erstellte AppSettings-Instanz
        """
        return cls(**data)
    
    def to_dict(self) -> dict:
        """
        Konvertiert die AppSettings-Instanz in ein Dictionary
        
        Returns:
            dict: Die Einstellungen als Dictionary
        """
        return {
            'theme': self.theme,
            'language': self.language,
            'visible_columns': self.visible_columns,
            'auto_lock_enabled': self.auto_lock_enabled,
            'auto_lock_time': self.auto_lock_time,
            'db_path': self.db_path
        }