#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Datenbankmodul für den Passwortmanager.
Stellt Funktionen zum Speichern und Abrufen von Passwörtern und Kategorien bereit.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any

from core.models import PasswordEntry, Category, AppSettings


class Storage:
    """Klasse für die Datenbankoperationen des Passwortmanagers"""
    
    def __init__(self, db_path="passwortmanager.db"):
        """
        Initialisiert das Storage-Objekt mit einem Pfad zur Datenbank
        
        Args:
            db_path (str): Pfad zur SQLite-Datenbank
        """
        self.db_path = db_path
        self._create_tables()
    
    def _create_tables(self):
        """Erstellt die notwendigen Tabellen in der Datenbank, falls sie nicht existieren"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabelle für das Masterpasswort (nur Hash wird gespeichert)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS master (
                id INTEGER PRIMARY KEY,
                password_hash TEXT NOT NULL,
                created_at DATETIME NOT NULL
            )
            ''')
            
            # Tabelle für Kategorien
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                parent_id INTEGER,
                icon TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (parent_id) REFERENCES categories (id) ON DELETE SET NULL
            )
            ''')
            
            # Tabelle für die Passwörter/PINs mit Kategorie-Referenz
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS passwords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                username TEXT,
                password TEXT NOT NULL,
                url TEXT,
                device_type TEXT,
                notes TEXT,
                category_id INTEGER,
                is_favorite INTEGER DEFAULT 0,
                expiry_date DATETIME,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL
            )
            ''')
            
            # Tabelle für Anwendungseinstellungen
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                theme TEXT NOT NULL DEFAULT 'light',
                language TEXT NOT NULL DEFAULT 'de',
                visible_columns TEXT NOT NULL,
                auto_lock_enabled INTEGER NOT NULL DEFAULT 0,
                auto_lock_time INTEGER NOT NULL DEFAULT 5,
                db_path TEXT NOT NULL DEFAULT 'passwortmanager.db'
            )
            ''')
            
            # Erstelle eine Standardkategorie, falls keine existiert
            cursor.execute("SELECT COUNT(*) FROM categories")
            if cursor.fetchone()[0] == 0:
                now = datetime.now().isoformat()
                cursor.execute('''
                INSERT INTO categories (name, description, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ''', ('Allgemein', 'Standardkategorie für alle Passwörter', now, now))
            
            # Erstelle Standardeinstellungen, falls keine existieren
            cursor.execute("SELECT COUNT(*) FROM settings")
            if cursor.fetchone()[0] == 0:
                default_settings = AppSettings()
                cursor.execute('''
                INSERT INTO settings 
                (theme, language, visible_columns, auto_lock_enabled, auto_lock_time, db_path)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    default_settings.theme,
                    default_settings.language,
                    json.dumps(default_settings.visible_columns),
                    int(default_settings.auto_lock_enabled),
                    default_settings.auto_lock_time,
                    default_settings.db_path
                ))
            
            conn.commit()
    
    # -------------------------------------------------------------------------
    # Masterpasswort-Funktionen
    # -------------------------------------------------------------------------
    
    def save_master_password(self, password_hash):
        """
        Speichert den Hash des Masterpassworts in der Datenbank
        
        Args:
            password_hash (str): Der Hash des Masterpassworts
            
        Returns:
            bool: True, wenn erfolgreich gespeichert, sonst False
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                # Prüfen, ob bereits ein Masterpasswort existiert
                cursor.execute("SELECT COUNT(*) FROM master")
                if cursor.fetchone()[0] > 0:
                    # Aktualisiere das bestehende Masterpasswort
                    cursor.execute("UPDATE master SET password_hash = ?, created_at = ?", 
                                (password_hash, now))
                else:
                    # Füge neues Masterpasswort ein
                    cursor.execute("INSERT INTO master (password_hash, created_at) VALUES (?, ?)", 
                                (password_hash, now))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Fehler beim Speichern des Masterpassworts: {e}")
            return False
    
    def get_master_password_hash(self):
        """
        Ruft den Hash des Masterpassworts aus der Datenbank ab
        
        Returns:
            str: Der Hash des Masterpassworts oder None, wenn keiner gefunden wurde
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT password_hash FROM master")
                result = cursor.fetchone()
                
                if result:
                    return result[0]
                return None
        except Exception as e:
            print(f"Fehler beim Abrufen des Masterpassworts: {e}")
            return None
    
    # -------------------------------------------------------------------------
    # Kategorie-Funktionen
    # -------------------------------------------------------------------------
    
    def add_category(self, name, description=None, parent_id=None, icon=None) -> int:
        """
        Fügt eine neue Kategorie hinzu
        
        Args:
            name (str): Name der Kategorie
            description (str, optional): Beschreibung der Kategorie
            parent_id (int, optional): ID der übergeordneten Kategorie
            icon (str, optional): Icon der Kategorie
            
        Returns:
            int: ID der neuen Kategorie oder -1 bei Fehler
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                cursor.execute('''
                INSERT INTO categories (name, description, parent_id, icon, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, description, parent_id, icon, now, now))
                
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Fehler beim Hinzufügen der Kategorie: {e}")
            return -1
    
    def update_category(self, category_id, name, description=None, parent_id=None, icon=None) -> bool:
        """
        Aktualisiert eine bestehende Kategorie
        
        Args:
            category_id (int): ID der zu aktualisierenden Kategorie
            name (str): Neuer Name der Kategorie
            description (str, optional): Neue Beschreibung der Kategorie
            parent_id (int, optional): Neue übergeordnete Kategorie
            icon (str, optional): Neues Icon der Kategorie
            
        Returns:
            bool: True, wenn erfolgreich aktualisiert, sonst False
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                cursor.execute('''
                UPDATE categories 
                SET name = ?, description = ?, parent_id = ?, icon = ?, updated_at = ?
                WHERE id = ?
                ''', (name, description, parent_id, icon, now, category_id))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Kategorie: {e}")
            return False
    
    def delete_category(self, category_id) -> bool:
        """
        Löscht eine Kategorie
        
        Args:
            category_id (int): ID der zu löschenden Kategorie
            
        Returns:
            bool: True, wenn erfolgreich gelöscht, sonst False
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Setze category_id auf NULL für alle Passwörter in dieser Kategorie
                cursor.execute("UPDATE passwords SET category_id = NULL WHERE category_id = ?", (category_id,))
                
                # Setze parent_id auf NULL für alle Unterkategorien
                cursor.execute("UPDATE categories SET parent_id = NULL WHERE parent_id = ?", (category_id,))
                
                # Lösche die Kategorie
                cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Fehler beim Löschen der Kategorie: {e}")
            return False
    
    def get_category(self, category_id) -> Optional[Category]:
        """
        Ruft eine Kategorie anhand ihrer ID ab
        
        Args:
            category_id (int): ID der abzurufenden Kategorie
            
        Returns:
            Category: Die abgerufene Kategorie oder None, wenn keine gefunden wurde
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
                result = cursor.fetchone()
                
                if result:
                    return Category.from_dict(dict(result))
                return None
        except Exception as e:
            print(f"Fehler beim Abrufen der Kategorie: {e}")
            return None
    
    def get_all_categories(self) -> List[Category]:
        """
        Ruft alle Kategorien ab
        
        Returns:
            List[Category]: Liste aller Kategorien
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM categories ORDER BY name")
                
                return [Category.from_dict(dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Fehler beim Abrufen aller Kategorien: {e}")
            return []
    
    def get_category_hierarchy(self) -> List[Dict]:
        """
        Ruft die Kategoriehierarchie ab (mit Unterkategorien)
        
        Returns:
            List[Dict]: Liste von Kategorien mit Unterkategorien
        """
        categories = self.get_all_categories()
        
        # Erstelle ein Dictionary für schnellen Zugriff
        category_dict = {cat.id: {"category": cat, "children": []} for cat in categories}
        
        # Erstelle die Hierarchie
        root_categories = []
        for cat_id, cat_data in category_dict.items():
            category = cat_data["category"]
            if category.parent_id is None:
                # Root-Kategorie
                root_categories.append(cat_data)
            else:
                # Füge zu übergeordneter Kategorie hinzu
                if category.parent_id in category_dict:
                    category_dict[category.parent_id]["children"].append(cat_data)
        
        return root_categories
    
    # -------------------------------------------------------------------------
    # Passwort-Funktionen
    # -------------------------------------------------------------------------
    
    def add_password(self, title, username, password, url=None, device_type=None, 
                     notes=None, category_id=None, is_favorite=False, expiry_date=None) -> int:
        """
        Fügt ein neues Passwort hinzu
        
        Args:
            title (str): Titel des Passworteintrags
            username (str): Benutzername
            password (str): Passwort (verschlüsselt)
            url (str, optional): URL der Website
            device_type (str, optional): Gerätetyp
            notes (str, optional): Notizen
            category_id (int, optional): ID der Kategorie
            is_favorite (bool, optional): Ob der Eintrag ein Favorit ist
            expiry_date (datetime, optional): Ablaufdatum des Passworts
            
        Returns:
            int: ID des neuen Passworteintrags oder -1 bei Fehler
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                expiry_date_str = None
                if expiry_date:
                    expiry_date_str = expiry_date.isoformat() if isinstance(expiry_date, datetime) else expiry_date
                
                cursor.execute('''
                INSERT INTO passwords 
                (title, username, password, url, device_type, notes, category_id, is_favorite, expiry_date, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    title, username, password, url, device_type, notes, 
                    category_id, int(is_favorite), expiry_date_str, now, now
                ))
                
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Fehler beim Hinzufügen des Passworts: {e}")
            return -1
    
    def update_password(self, password_id, title, username, password, url=None, 
                        device_type=None, notes=None, category_id=None, 
                        is_favorite=False, expiry_date=None) -> bool:
        """
        Aktualisiert ein bestehendes Passwort
        
        Args:
            password_id (int): ID des zu aktualisierenden Passworteintrags
            title (str): Neuer Titel
            username (str): Neuer Benutzername
            password (str): Neues Passwort (verschlüsselt)
            url (str, optional): Neue URL
            device_type (str, optional): Neuer Gerätetyp
            notes (str, optional): Neue Notizen
            category_id (int, optional): Neue Kategorie-ID
            is_favorite (bool, optional): Neuer Favoritenstatus
            expiry_date (datetime, optional): Neues Ablaufdatum
            
        Returns:
            bool: True, wenn erfolgreich aktualisiert, sonst False
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                expiry_date_str = None
                if expiry_date:
                    expiry_date_str = expiry_date.isoformat() if isinstance(expiry_date, datetime) else expiry_date
                
                cursor.execute('''
                UPDATE passwords 
                SET title = ?, username = ?, password = ?, url = ?, device_type = ?, 
                    notes = ?, category_id = ?, is_favorite = ?, expiry_date = ?, updated_at = ?
                WHERE id = ?
                ''', (
                    title, username, password, url, device_type, notes, 
                    category_id, int(is_favorite), expiry_date_str, now, password_id
                ))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Fehler beim Aktualisieren des Passworts: {e}")
            return False
    
    def delete_password(self, password_id) -> bool:
        """
        Löscht ein Passwort
        
        Args:
            password_id (int): ID des zu löschenden Passworteintrags
            
        Returns:
            bool: True, wenn erfolgreich gelöscht, sonst False
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM passwords WHERE id = ?", (password_id,))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Fehler beim Löschen des Passworts: {e}")
            return False
    
    def get_password(self, password_id) -> Optional[PasswordEntry]:
        """
        Ruft ein Passwort anhand seiner ID ab
        
        Args:
            password_id (int): ID des abzurufenden Passworteintrags
            
        Returns:
            PasswordEntry: Der abgerufene Passworteintrag oder None, wenn keiner gefunden wurde
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM passwords WHERE id = ?", (password_id,))
                result = cursor.fetchone()
                
                if result:
                    return PasswordEntry.from_dict(dict(result))
                return None
        except Exception as e:
            print(f"Fehler beim Abrufen des Passworts: {e}")
            return None
    
    def get_all_passwords(self) -> List[PasswordEntry]:
        """
        Ruft alle Passwörter ab
        
        Returns:
            List[PasswordEntry]: Liste aller Passworteinträge
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM passwords ORDER BY title")
                
                return [PasswordEntry.from_dict(dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Fehler beim Abrufen aller Passwörter: {e}")
            return []
    
    def get_passwords_by_category(self, category_id) -> List[PasswordEntry]:
        """
        Ruft alle Passwörter einer bestimmten Kategorie ab
        
        Args:
            category_id (int): ID der Kategorie
            
        Returns:
            List[PasswordEntry]: Liste der Passworteinträge in der Kategorie
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM passwords WHERE category_id = ? ORDER BY title", (category_id,))
                
                return [PasswordEntry.from_dict(dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Fehler beim Abrufen der Passwörter nach Kategorie: {e}")
            return []
    
    def search_passwords(self, query) -> List[PasswordEntry]:
        """
        Sucht nach Passwörtern
        
        Args:
            query (str): Suchbegriff
            
        Returns:
            List[PasswordEntry]: Liste der gefundenen Passworteinträge
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Suche in Titel, Benutzername, URL und Notizen
                cursor.execute('''
                SELECT * FROM passwords 
                WHERE title LIKE ? OR username LIKE ? OR url LIKE ? OR notes LIKE ?
                ORDER BY title
                ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
                
                return [PasswordEntry.from_dict(dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Fehler bei der Passwortsuche: {e}")
            return []
    
    def get_favorite_passwords(self) -> List[PasswordEntry]:
        """
        Ruft alle als Favorit markierten Passwörter ab
        
        Returns:
            List[PasswordEntry]: Liste der Favoriten-Passworteinträge
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM passwords WHERE is_favorite = 1 ORDER BY title")
                
                return [PasswordEntry.from_dict(dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Fehler beim Abrufen der Favoriten: {e}")
            return []
    
    def toggle_favorite(self, password_id, is_favorite) -> bool:
        """
        Ändert den Favoritenstatus eines Passworts
        
        Args:
            password_id (int): ID des Passworteintrags
            is_favorite (bool): Neuer Favoritenstatus
            
        Returns:
            bool: True, wenn erfolgreich aktualisiert, sonst False
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "UPDATE passwords SET is_favorite = ? WHERE id = ?", 
                    (int(is_favorite), password_id)
                )
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Fehler beim Ändern des Favoritenstatus: {e}")
            return False
    
    # -------------------------------------------------------------------------
    # Einstellungs-Funktionen
    # -------------------------------------------------------------------------
    
    def get_settings(self) -> AppSettings:
        """
        Ruft die aktuellen Anwendungseinstellungen ab
        
        Returns:
            AppSettings: Die aktuellen Einstellungen
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM settings LIMIT 1")
                result = cursor.fetchone()
                
                if result:
                    # Konvertiere das JSON-Feld zurück in eine Liste
                    result_dict = dict(result)
                    result_dict['visible_columns'] = json.loads(result_dict['visible_columns'])
                    result_dict['auto_lock_enabled'] = bool(result_dict['auto_lock_enabled'])
                    
                    return AppSettings.from_dict(result_dict)
                
                # Wenn keine Einstellungen gefunden wurden, erstelle Standardeinstellungen
                default_settings = AppSettings()
                self.save_settings(default_settings)
                return default_settings
        except Exception as e:
            print(f"Fehler beim Abrufen der Einstellungen: {e}")
            return AppSettings()
    
    def save_settings(self, settings: AppSettings) -> bool:
        """
        Speichert die Anwendungseinstellungen
        
        Args:
            settings (AppSettings): Die zu speichernden Einstellungen
            
        Returns:
            bool: True, wenn erfolgreich gespeichert, sonst False
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Konvertiere die Liste in JSON
                visible_columns_json = json.dumps(settings.visible_columns)
                
                cursor.execute("SELECT COUNT(*) FROM settings")
                if cursor.fetchone()[0] > 0:
                    # Aktualisiere bestehende Einstellungen
                    cursor.execute('''
                    UPDATE settings 
                    SET theme = ?, language = ?, visible_columns = ?, 
                        auto_lock_enabled = ?, auto_lock_time = ?, db_path = ?
                    ''', (
                        settings.theme,
                        settings.language,
                        visible_columns_json,
                        int(settings.auto_lock_enabled),
                        settings.auto_lock_time,
                        settings.db_path
                    ))
                else:
                    # Füge neue Einstellungen ein
                    cursor.execute('''
                    INSERT INTO settings 
                    (theme, language, visible_columns, auto_lock_enabled, auto_lock_time, db_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        settings.theme,
                        settings.language,
                        visible_columns_json,
                        int(settings.auto_lock_enabled),
                        settings.auto_lock_time,
                        settings.db_path
                    ))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Fehler beim Speichern der Einstellungen: {e}")
            return False