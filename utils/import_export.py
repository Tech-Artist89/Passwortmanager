#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Import- und Export-Funktionen für den Passwortmanager.
Ermöglicht das Importieren und Exportieren von Passwörtern in verschiedenen Formaten.
"""

import csv
import json
import os
import datetime
from typing import List, Dict, Any, Optional

from core.models import PasswordEntry, Category
from utils.helpers import create_filename


def export_to_csv(passwords: List[PasswordEntry], category_map: Dict[int, str], filepath: str) -> bool:
    """
    Exportiert Passwörter in eine CSV-Datei.
    
    Args:
        passwords (List[PasswordEntry]): Liste der zu exportierenden Passworteinträge
        category_map (Dict[int, str]): Zuordnung von Kategorie-IDs zu Namen
        filepath (str): Pfad zur Zieldatei
        
    Returns:
        bool: True, wenn erfolgreich exportiert, sonst False
    """
    try:
        fieldnames = [
            'Titel', 'Benutzername', 'Passwort', 'URL', 'Gerätetyp', 
            'Notizen', 'Kategorie', 'Favorit', 'Ablaufdatum', 'Erstellt', 'Aktualisiert'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for entry in passwords:
                # Formatiere die Daten für den Export
                category_name = category_map.get(entry.category_id, '')
                
                # Formatiere die Datumsangaben
                created_at = ""
                if entry.created_at:
                    created_at = entry.created_at.strftime('%d.%m.%Y %H:%M')
                
                updated_at = ""
                if entry.updated_at:
                    updated_at = entry.updated_at.strftime('%d.%m.%Y %H:%M')
                
                expiry_date = ""
                if entry.expiry_date:
                    expiry_date = entry.expiry_date.strftime('%d.%m.%Y')
                
                writer.writerow({
                    'Titel': entry.title,
                    'Benutzername': entry.username or '',
                    'Passwort': entry.password,  # Achtung: Hier werden unverschlüsselte Passwörter exportiert!
                    'URL': entry.url or '',
                    'Gerätetyp': entry.device_type or '',
                    'Notizen': entry.notes or '',
                    'Kategorie': category_name,
                    'Favorit': 'Ja' if entry.is_favorite else 'Nein',
                    'Ablaufdatum': expiry_date,
                    'Erstellt': created_at,
                    'Aktualisiert': updated_at
                })
                
        return True
    except Exception as e:
        print(f"Fehler beim Export nach CSV: {e}")
        return False


def import_from_csv(filepath: str, categories: List[Category]) -> Optional[List[Dict[str, Any]]]:
    """
    Importiert Passwörter aus einer CSV-Datei.
    
    Args:
        filepath (str): Pfad zur Quelldatei
        categories (List[Category]): Liste der verfügbaren Kategorien
        
    Returns:
        Optional[List[Dict[str, Any]]]: Liste der importierten Passworteinträge oder None bei Fehler
    """
    try:
        # Erstelle eine Kategorie-Map (Name -> ID)
        category_map = {cat.name: cat.id for cat in categories}
        
        imported_entries = []
        
        with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Überprüfe, ob die erforderlichen Spalten vorhanden sind
            required_fields = ['Titel', 'Passwort']
            for field in required_fields:
                if field not in reader.fieldnames:
                    raise ValueError(f"Erforderliches Feld '{field}' fehlt in der CSV-Datei")
            
            for row in reader:
                # Kategorie-ID ermitteln
                category_name = row.get('Kategorie', '')
                category_id = category_map.get(category_name, None)
                
                # Datumsangaben parsen
                created_at = datetime.datetime.now()
                if 'Erstellt' in row and row['Erstellt']:
                    try:
                        created_at = datetime.datetime.strptime(row['Erstellt'], '%d.%m.%Y %H:%M')
                    except ValueError:
                        pass
                
                updated_at = datetime.datetime.now()
                if 'Aktualisiert' in row and row['Aktualisiert']:
                    try:
                        updated_at = datetime.datetime.strptime(row['Aktualisiert'], '%d.%m.%Y %H:%M')
                    except ValueError:
                        pass
                
                expiry_date = None
                if 'Ablaufdatum' in row and row['Ablaufdatum']:
                    try:
                        expiry_date = datetime.datetime.strptime(row['Ablaufdatum'], '%d.%m.%Y')
                    except ValueError:
                        pass
                
                # Favoritenstatus ermitteln
                is_favorite = False
                if 'Favorit' in row:
                    is_favorite = row['Favorit'].lower() in ['ja', 'yes', 'true', '1']
                
                # Eintrag erstellen
                entry = {
                    'title': row['Titel'],
                    'username': row.get('Benutzername', ''),
                    'password': row['Passwort'],  # Hinweis: Wird später verschlüsselt
                    'url': row.get('URL', ''),
                    'device_type': row.get('Gerätetyp', ''),
                    'notes': row.get('Notizen', ''),
                    'category_id': category_id,
                    'is_favorite': is_favorite,
                    'expiry_date': expiry_date,
                    'created_at': created_at,
                    'updated_at': updated_at
                }
                
                imported_entries.append(entry)
        
        return imported_entries
    except Exception as e:
        print(f"Fehler beim Import aus CSV: {e}")
        return None


def export_to_json(passwords: List[PasswordEntry], category_map: Dict[int, str], filepath: str, encrypted: bool = False) -> bool:
    """
    Exportiert Passwörter in eine JSON-Datei.
    
    Args:
        passwords (List[PasswordEntry]): Liste der zu exportierenden Passworteinträge
        category_map (Dict[int, str]): Zuordnung von Kategorie-IDs zu Namen
        filepath (str): Pfad zur Zieldatei
        encrypted (bool): Ob die Passwörter verschlüsselt bleiben sollen
        
    Returns:
        bool: True, wenn erfolgreich exportiert, sonst False
    """
    try:
        data = []
        
        for entry in passwords:
            # Formatiere die Daten für den Export
            entry_dict = entry.to_dict()
            
            # Füge Kategorienamen hinzu
            entry_dict['category_name'] = category_map.get(entry.category_id, '')
            
            # Entferne die ID, wenn wir die Datei für den Import in eine andere Datenbank vorbereiten
            if not encrypted:
                entry_dict.pop('id', None)
            
            data.append(entry_dict)
        
        # Metadaten hinzufügen
        export_data = {
            'version': '1.0',
            'encrypted': encrypted,
            'created_at': datetime.datetime.now().isoformat(),
            'count': len(data),
            'entries': data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"Fehler beim Export nach JSON: {e}")
        return False


def import_from_json(filepath: str, categories: List[Category]) -> Optional[List[Dict[str, Any]]]:
    """
    Importiert Passwörter aus einer JSON-Datei.
    
    Args:
        filepath (str): Pfad zur Quelldatei
        categories (List[Category]): Liste der verfügbaren Kategorien
        
    Returns:
        Optional[List[Dict[str, Any]]]: Liste der importierten Passworteinträge oder None bei Fehler
    """
    try:
        # Erstelle eine Kategorie-Map (Name -> ID)
        category_map = {cat.name: cat.id for cat in categories}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Überprüfe das Format
        if not isinstance(data, dict) or 'entries' not in data:
            raise ValueError("Ungültiges JSON-Format: 'entries' fehlt")
        
        imported_entries = []
        
        for entry_data in data['entries']:
            # Kategorie-ID ermitteln
            category_name = entry_data.get('category_name', '')
            category_id = category_map.get(category_name, None)
            
            # ID entfernen, da eine neue generiert wird
            entry_data.pop('id', None)
            
            # Kategorie-ID aktualisieren
            entry_data['category_id'] = category_id
            
            imported_entries.append(entry_data)
        
        return imported_entries
    except Exception as e:
        print(f"Fehler beim Import aus JSON: {e}")
        return None