#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hilfsfunktionen für den Passwortmanager.
Enthält allgemeine Utility-Funktionen, die in verschiedenen Modulen verwendet werden.
"""

import os
import datetime
import json
import random
import string
import sys


def generate_salt(length=16):
    """
    Generiert einen zufälligen Salt für die Passwort-Hashing-Funktion.
    
    Args:
        length (int): Länge des Salts in Bytes
        
    Returns:
        bytes: Ein zufälliger Salt als Bytes-Objekt
    """
    return os.urandom(length)


def create_filename(base_name, extension):
    """
    Erstellt einen Dateinamen mit Zeitstempel.
    
    Args:
        base_name (str): Grundname der Datei
        extension (str): Dateierweiterung
        
    Returns:
        str: Ein Dateiname mit Zeitstempel
    """
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{base_name}_{timestamp}.{extension}"


def format_date(iso_date_string):
    """
    Formatiert einen ISO-Datums-String in ein lesbares Format.
    
    Args:
        iso_date_string (str): Datum im ISO-Format
        
    Returns:
        str: Formatiertes Datum als String
    """
    try:
        date_obj = datetime.datetime.fromisoformat(iso_date_string)
        return date_obj.strftime('%d.%m.%Y %H:%M')
    except (ValueError, TypeError):
        return iso_date_string or ""


def truncate_string(text, max_length=30):
    """
    Kürzt einen String auf eine maximale Länge und fügt '...' hinzu.
    
    Args:
        text (str): Der zu kürzende String
        max_length (int): Maximale Länge
        
    Returns:
        str: Gekürzter String
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."


def get_resource_path(relative_path):
    """
    Gibt den absoluten Pfad zu einer Ressourcendatei zurück.
    Funktioniert sowohl im Entwicklungsmodus als auch in der kompilierten Anwendung.
    
    Args:
        relative_path (str): Relativer Pfad zur Ressourcendatei
        
    Returns:
        str: Absoluter Pfad zur Ressourcendatei
    """
    try:
        # Prüfen, ob wir in einer PyInstaller-Umgebung sind
        base_path = sys._MEIPASS
    except AttributeError:
        # Entwicklungsmodus
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def get_non_empty_fields(data_dict):
    """
    Filtert ein Dictionary und entfernt leere Werte.
    
    Args:
        data_dict (dict): Das zu filternde Dictionary
        
    Returns:
        dict: Dictionary ohne leere Werte
    """
    return {k: v for k, v in data_dict.items() if v}


def is_expired(expiry_date):
    """
    Prüft, ob ein Datum abgelaufen ist.
    
    Args:
        expiry_date (datetime.datetime or str): Das zu prüfende Datum
        
    Returns:
        bool: True, wenn das Datum abgelaufen ist, sonst False
    """
    if not expiry_date:
        return False
    
    # Konvertiere String zu datetime, falls notwendig
    if isinstance(expiry_date, str):
        try:
            expiry_date = datetime.datetime.fromisoformat(expiry_date)
        except ValueError:
            return False
    
    # Vergleiche mit aktuellem Datum
    return expiry_date < datetime.datetime.now()


def days_until_expiry(expiry_date):
    """
    Berechnet die Anzahl der Tage bis zum Ablauf eines Datums.
    
    Args:
        expiry_date (datetime.datetime or str): Das Ablaufdatum
        
    Returns:
        int: Anzahl der Tage bis zum Ablauf oder -1, wenn das Datum bereits abgelaufen ist
    """
    if not expiry_date:
        return None
    
    # Konvertiere String zu datetime, falls notwendig
    if isinstance(expiry_date, str):
        try:
            expiry_date = datetime.datetime.fromisoformat(expiry_date)
        except ValueError:
            return None
    
    # Berechne Differenz
    delta = expiry_date - datetime.datetime.now()
    
    if delta.total_seconds() < 0:
        return -1
    
    return delta.days