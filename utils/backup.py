#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Backup-Funktionen für den Passwortmanager.
Ermöglicht das Erstellen und Wiederherstellen von Datenbank-Backups.
"""

import os
import shutil
import sqlite3
import datetime
import json
from typing import List, Optional, Tuple

from utils.helpers import create_filename


def create_backup(db_path: str, backup_dir: str = None) -> Tuple[bool, str]:
    """
    Erstellt ein Backup der Datenbank.
    
    Args:
        db_path (str): Pfad zur Datenbank
        backup_dir (str, optional): Verzeichnis für das Backup
        
    Returns:
        Tuple[bool, str]: (Erfolg, Pfad zum Backup oder Fehlermeldung)
    """
    try:
        # Standard-Backup-Verzeichnis ist ein Unterordner 'backups' im gleichen Verzeichnis wie die Datenbank
        if not backup_dir:
            db_dir = os.path.dirname(os.path.abspath(db_path))
            backup_dir = os.path.join(db_dir, 'backups')
        
        # Erstelle das Backup-Verzeichnis, falls es nicht existiert
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generiere einen Dateinamen mit Zeitstempel
        backup_filename = create_filename('backup', 'db')
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Kopiere die Datenbank
        shutil.copy2(db_path, backup_path)
        
        # Erstelle eine Metadatendatei
        metadata = {
            'original_db': db_path,
            'backup_date': datetime.datetime.now().isoformat(),
            'description': f'Automatisches Backup vom {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}'
        }
        
        metadata_path = backup_path + '.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return True, backup_path
    except Exception as e:
        return False, f"Fehler beim Erstellen des Backups: {e}"


def restore_backup(backup_path: str, target_path: str = None) -> Tuple[bool, str]:
    """
    Stellt ein Backup der Datenbank wieder her.
    
    Args:
        backup_path (str): Pfad zum Backup
        target_path (str, optional): Zielort für die wiederhergestellte Datenbank
        
    Returns:
        Tuple[bool, str]: (Erfolg, Meldung)
    """
    try:
        # Überprüfe, ob das Backup existiert
        if not os.path.exists(backup_path):
            return False, f"Backup-Datei '{backup_path}' nicht gefunden."
        
        # Überprüfe die Integrität der Datenbank
        try:
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()
            
            if result[0] != 'ok':
                return False, "Die Backup-Datei ist beschädigt und kann nicht wiederhergestellt werden."
        except sqlite3.Error:
            return False, "Die Backup-Datei ist keine gültige SQLite-Datenbank."
        
        # Bestimme den Zielort
        if not target_path:
            # Verwende den ursprünglichen Pfad aus den Metadaten, falls vorhanden
            metadata_path = backup_path + '.json'
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        target_path = metadata.get('original_db')
                except (json.JSONDecodeError, KeyError):
                    pass
        
        if not target_path:
            return False, "Kein Zielort für die Wiederherstellung angegeben."
        
        # Erstelle ein Backup der aktuellen Datenbank, falls vorhanden
        if os.path.exists(target_path):
            backup_filename = create_filename('pre_restore', 'db')
            backup_dir = os.path.dirname(os.path.abspath(target_path))
            pre_restore_backup = os.path.join(backup_dir, backup_filename)
            shutil.copy2(target_path, pre_restore_backup)
        
        # Kopiere das Backup an den Zielort
        shutil.copy2(backup_path, target_path)
        
        return True, f"Backup erfolgreich wiederhergestellt nach '{target_path}'."
    except Exception as e:
        return False, f"Fehler bei der Wiederherstellung des Backups: {e}"


def get_backup_list(backup_dir: str) -> List[dict]:
    """
    Listet alle verfügbaren Backups in einem Verzeichnis auf.
    
    Args:
        backup_dir (str): Verzeichnis mit den Backups
        
    Returns:
        List[dict]: Liste der Backups mit Metadaten
    """
    try:
        backups = []
        
        # Erstelle das Verzeichnis, falls es nicht existiert
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
            return backups
        
        for filename in os.listdir(backup_dir):
            if filename.endswith('.db'):
                filepath = os.path.join(backup_dir, filename)
                metadata_path = filepath + '.json'
                
                # Standardwerte
                backup_info = {
                    'path': filepath,
                    'filename': filename,
                    'date': datetime.datetime.fromtimestamp(os.path.getmtime(filepath)),
                    'size': os.path.getsize(filepath),
                    'description': ''
                }
                
                # Lade Metadaten, falls vorhanden
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            
                            if 'backup_date' in metadata:
                                try:
                                    backup_info['date'] = datetime.datetime.fromisoformat(metadata['backup_date'])
                                except ValueError:
                                    pass
                            
                            if 'description' in metadata:
                                backup_info['description'] = metadata['description']
                    except (json.JSONDecodeError, FileNotFoundError):
                        pass
                
                backups.append(backup_info)
        
        # Sortiere nach Datum (neueste zuerst)
        backups.sort(key=lambda x: x['date'], reverse=True)
        
        return backups
    except Exception as e:
        print(f"Fehler beim Abrufen der Backup-Liste: {e}")
        return []


def delete_backup(backup_path: str) -> Tuple[bool, str]:
    """
    Löscht ein Backup und die zugehörige Metadatendatei.
    
    Args:
        backup_path (str): Pfad zum Backup
        
    Returns:
        Tuple[bool, str]: (Erfolg, Meldung)
    """
    try:
        # Überprüfe, ob das Backup existiert
        if not os.path.exists(backup_path):
            return False, f"Backup-Datei '{backup_path}' nicht gefunden."
        
        # Lösche die Datei
        os.remove(backup_path)
        
        # Lösche die Metadatendatei, falls vorhanden
        metadata_path = backup_path + '.json'
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
        
        return True, "Backup erfolgreich gelöscht."
    except Exception as e:
        return False, f"Fehler beim Löschen des Backups: {e}"


def create_scheduled_backup(db_path: str, backup_dir: str = None, max_backups: int = 5) -> Tuple[bool, str]:
    """
    Erstellt ein geplantes Backup und begrenzt die Anzahl der Backups.
    
    Args:
        db_path (str): Pfad zur Datenbank
        backup_dir (str, optional): Verzeichnis für das Backup
        max_backups (int): Maximale Anzahl aufzubewahrender Backups
        
    Returns:
        Tuple[bool, str]: (Erfolg, Meldung)
    """
    # Bestimme das Backup-Verzeichnis
    if not backup_dir:
        db_dir = os.path.dirname(os.path.abspath(db_path))
        backup_dir = os.path.join(db_dir, 'backups')
    
    # Erstelle das neue Backup
    success, result = create_backup(db_path, backup_dir)
    
    if not success:
        return success, result
    
    # Begrenze die Anzahl der Backups
    try:
        backups = get_backup_list(backup_dir)
        
        # Lösche ältere Backups, wenn die maximale Anzahl überschritten wird
        if len(backups) > max_backups:
            for backup in backups[max_backups:]:
                delete_backup(backup['path'])
            
            return True, f"Backup erstellt und ältere Backups bereinigt. {max_backups} Backups behalten."
        
        return True, "Backup erfolgreich erstellt."
    except Exception as e:
        return False, f"Backup erstellt, aber Fehler bei der Bereinigung älterer Backups: {e}"