#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Passwortgenerator-Modul für den Passwortmanager.
Stellt Funktionen zum Generieren sicherer Passwörter und PINs bereit.
"""

import random
import string
import re


class PasswordGenerator:
    """Klasse für die Generierung von Passwörtern und PINs"""
    
    def __init__(self):
        """Initialisiert den PasswordGenerator"""
        self.lowercase_letters = string.ascii_lowercase
        self.uppercase_letters = string.ascii_uppercase
        self.digits = string.digits
        self.special_chars = "!@#$%&*()-_=+[]{}|;:,.<>?"
    
    def generate_pin(self, length=4, use_letters=False):
        """
        Generiert eine PIN.
        
        Args:
            length (int): Länge der PIN (4-8 Zeichen)
            use_letters (bool): Wenn True, werden auch Buchstaben verwendet
            
        Returns:
            str: Generierte PIN
            
        Raises:
            ValueError: Wenn die Länge ungültig ist
        """
        if not (4 <= length <= 8):
            raise ValueError("PIN-Länge muss zwischen 4 und 8 liegen")
        
        if use_letters:
            # PIN mit Buchstaben und Zahlen
            chars = self.digits + self.lowercase_letters + self.uppercase_letters
        else:
            # Nur Zahlen (Standard für PINs)
            chars = self.digits
        
        return ''.join(random.choice(chars) for _ in range(length))
    
    def generate_password(self, length=16, use_uppercase=True, use_special=True):
        """
        Generiert ein komplexes Passwort.
        
        Args:
            length (int): Länge des Passworts (8, 12, 16 oder 32 Zeichen)
            use_uppercase (bool): Wenn True, werden Großbuchstaben verwendet
            use_special (bool): Wenn True, werden Sonderzeichen verwendet
            
        Returns:
            str: Generiertes Passwort
            
        Raises:
            ValueError: Wenn die Länge ungültig ist
        """
        if length not in [8, 12, 16, 32]:
            raise ValueError("Passwortlänge muss 8, 12, 16 oder 32 sein")
        
        # Maximale Anzahl von Sonderzeichen basierend auf der Passwortlänge
        max_special_chars = {
            8: 2,
            12: 3,
            16: 4,
            32: 8
        }
        
        # Verfügbare Zeichentypen basierend auf den gewählten Optionen
        char_types = [self.lowercase_letters, self.digits]
        if use_uppercase:
            char_types.append(self.uppercase_letters)
        
        # Erstelle Liste der Zeichen für das Passwort
        password_chars = []
        
        # Füge mindestens ein Zeichen von jedem Typ hinzu
        for char_type in char_types:
            password_chars.append(random.choice(char_type))
        
        # Füge Sonderzeichen hinzu, wenn gewünscht
        if use_special:
            num_special = min(max_special_chars[length], length // 4)
            for _ in range(num_special):
                password_chars.append(random.choice(self.special_chars))
        
        # Fülle den Rest mit zufälligen Zeichen aus den verfügbaren Typen
        remaining_chars = length - len(password_chars)
        all_chars = ''.join(char_types)
        if use_special:
            all_chars += self.special_chars
            
        password_chars.extend(random.choice(all_chars) for _ in range(remaining_chars))
        
        # Mische die Zeichen, um eine gleichmäßige Verteilung zu gewährleisten
        random.shuffle(password_chars)
        
        # Stelle sicher, dass keine Sonderzeichen direkt aufeinanderfolgen
        if use_special:
            i = 1
            while i < len(password_chars):
                if (password_chars[i] in self.special_chars and 
                    password_chars[i-1] in self.special_chars):
                    # Tausche mit einem zufälligen nicht-speziellen Zeichen
                    swap_indices = [j for j in range(len(password_chars)) 
                                  if password_chars[j] not in self.special_chars]
                    if swap_indices:
                        swap_idx = random.choice(swap_indices)
                        password_chars[i], password_chars[swap_idx] = password_chars[swap_idx], password_chars[i]
                i += 1
        
        return ''.join(password_chars)
    
    def generate_memorable_password(self, word_count=3, separator="-", capitalize=True, add_number=True):
        """
        Generiert ein leicht zu merkendes Passwort aus Wörtern und Zahlen.
        
        Args:
            word_count (int): Anzahl der zu verwendenden Wörter (2-4)
            separator (str): Trennzeichen zwischen den Wörtern
            capitalize (bool): Wenn True, werden die Wörter großgeschrieben
            add_number (bool): Wenn True, wird eine Zahl am Ende hinzugefügt
            
        Returns:
            str: Generiertes merkbares Passwort
        """
        # Einfache Liste von Wörtern
        common_words = [
            "apfel", "baum", "computer", "daten", "elefant", "farbe", "garten", "haus",
            "internet", "jahr", "kaffee", "lampe", "maus", "netz", "orange", "papier",
            "qualität", "raum", "sonne", "tisch", "uhr", "vogel", "wasser", "xylophon",
            "yoga", "zeit", "brief", "buch", "fenster", "gabel", "katze", "löffel",
            "messer", "nadel", "schere", "tasse", "teller", "wolke", "blatt", "blume",
            "berg", "fluss", "meer", "stern", "mond", "himmel", "wind", "feuer",
            "erde", "wasser", "luft", "licht", "schatten", "regen", "schnee", "wüste"
        ]
        
        # Wähle zufällige Wörter
        if not (2 <= word_count <= 4):
            word_count = 3
            
        selected_words = random.sample(common_words, word_count)
        
        # Optional: Großschreibung
        if capitalize:
            selected_words = [word.capitalize() for word in selected_words]
        
        # Optional: Füge Zahl hinzu
        if add_number:
            selected_words.append(str(random.randint(10, 999)))
        
        # Verbinde Wörter mit Trennzeichen
        return separator.join(selected_words)
    
    def calculate_password_strength(self, password):
        """
        Berechnet die Stärke eines Passworts
        
        Args:
            password (str): Das zu bewertende Passwort
            
        Returns:
            dict: Dictionary mit Stärkewert (0-100) und Bewertung
        """
        if not password:
            return {"score": 0, "rating": "Sehr schwach", "color": "red"}
        
        score = 0
        feedback = []
        
        # Länge
        length = len(password)
        if length >= 12:
            score += 25
            feedback.append("Gute Länge")
        elif length >= 8:
            score += 15
            feedback.append("Ausreichende Länge")
        else:
            feedback.append("Zu kurz")
        
        # Komplexität
        has_lower = bool(re.search(r'[a-z]', password))
        has_upper = bool(re.search(r'[A-Z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[^a-zA-Z\d\s]', password))
        
        complexity_score = 0
        if has_lower:
            complexity_score += 10
        if has_upper:
            complexity_score += 10
        if has_digit:
            complexity_score += 10
        if has_special:
            complexity_score += 20
            
        score += complexity_score
        
        if complexity_score < 20:
            feedback.append("Mehr Zeichenarten verwenden")
        
        # Wiederholungen
        repeated_chars = 0
        for i in range(1, length):
            if password[i] == password[i-1]:
                repeated_chars += 1
        
        if repeated_chars > 0:
            score -= min(repeated_chars * 5, 20)
            feedback.append("Wiederholte Zeichen vermeiden")
        
        # Sequenzen
        sequences = ["abcdefghijklmnopqrstuvwxyz", "0123456789"]
        seq_found = False
        
        for seq in sequences:
            for i in range(len(seq) - 2):
                if seq[i:i+3].lower() in password.lower():
                    seq_found = True
                    break
        
        if seq_found:
            score -= 15
            feedback.append("Sequenzen vermeiden")
        
        # Berechne die endgültige Bewertung
        score = max(0, min(score, 100))
        
        # Bestimme die Bewertungsstufe
        if score < 30:
            rating = "Sehr schwach"
            color = "red"
        elif score < 50:
            rating = "Schwach"
            color = "orangered"
        elif score < 70:
            rating = "Mittel"
            color = "orange"
        elif score < 90:
            rating = "Stark"
            color = "yellowgreen"
        else:
            rating = "Sehr stark"
            color = "green"
        
        return {
            "score": score,
            "rating": rating,
            "color": color,
            "feedback": feedback
        }