#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Verschlüsselungsmodul für den Passwortmanager.
Stellt Funktionen zur sicheren Verschlüsselung und Entschlüsselung von Passwörtern bereit.
"""

import os
import base64
import hashlib
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


class Encryption:
    """Klasse für die Verschlüsselung und Entschlüsselung von Passwörtern"""
    
    def __init__(self, master_password):
        """
        Initialisiert das Encryption-Objekt mit einem Masterpasswort
        
        Args:
            master_password (str): Das Masterpasswort zur Ableitung des Schlüssels
        """
        self.backend = default_backend()
        # Ableiten des Schlüssels aus dem Masterpasswort
        self.key = self._derive_key(master_password)
    
    def _derive_key(self, master_password):
        """
        Leitet einen sicheren Schlüssel aus dem Masterpasswort ab
        
        Args:
            master_password (str): Das Masterpasswort
            
        Returns:
            bytes: Der abgeleitete Schlüssel
        """
        # Generiere einen sicheren Schlüssel aus dem Masterpasswort mit PBKDF2
        salt = b"passwortmanager_salt"  # In einer Produktionsumgebung sollte dies sicher gespeichert werden
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 32 Bytes für AES-256
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        return kdf.derive(master_password.encode())
    
    def encrypt(self, plaintext):
        """
        Verschlüsselt einen Klartext
        
        Args:
            plaintext (str): Der zu verschlüsselnde Text
            
        Returns:
            str: Der verschlüsselte Text als Base64-String
        """
        # Generiere einen zufälligen Initialisierungsvektor (IV)
        iv = os.urandom(16)
        
        # Erstelle Cipher-Objekt mit AES-256 im CBC-Modus
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        
        # Padding hinzufügen (PKCS#7 Padding)
        padder = lambda s: s + bytes([16 - (len(s) % 16)] * (16 - (len(s) % 16)))
        padded_data = padder(plaintext.encode())
        
        # Verschlüsseln
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # IV und Ciphertext zusammenführen und Base64-kodieren
        encrypted_data = base64.b64encode(iv + ciphertext).decode('utf-8')
        return encrypted_data
    
    def decrypt(self, encrypted_data):
        """
        Entschlüsselt einen verschlüsselten Text
        
        Args:
            encrypted_data (str): Der verschlüsselte Text als Base64-String
            
        Returns:
            str: Der entschlüsselte Klartext
        """
        try:
            # Base64-dekodieren
            raw_data = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # IV extrahieren (erste 16 Bytes)
            iv = raw_data[:16]
            ciphertext = raw_data[16:]
            
            # Cipher-Objekt erstellen
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=self.backend)
            decryptor = cipher.decryptor()
            
            # Entschlüsseln
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Padding entfernen
            padding_length = padded_plaintext[-1]
            plaintext = padded_plaintext[:-padding_length].decode('utf-8')
            
            return plaintext
        except Exception as e:
            # Bei Fehlern während der Entschlüsselung
            print(f"Fehler bei der Entschlüsselung: {e}")
            return ""

    @staticmethod
    def hash_master_password(master_password):
        """
        Erstellt einen Hash des Masterpassworts zur sicheren Speicherung
        
        Args:
            master_password (str): Das Masterpasswort
            
        Returns:
            str: Der Hash des Masterpassworts als Base64-String
        """
        # Erzeuge einen sicheren Hash des Masterpassworts zur Speicherung/Verifizierung
        salt = b"passwortmanager_masterpassword_salt"  # In der Produktion sollte dies sicher gespeichert werden
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return base64.b64encode(kdf.derive(master_password.encode())).decode('utf-8')

    @staticmethod
    def verify_master_password(master_password, stored_hash):
        """
        Überprüft, ob ein Masterpasswort mit dem gespeicherten Hash übereinstimmt
        
        Args:
            master_password (str): Das zu überprüfende Masterpasswort
            stored_hash (str): Der gespeicherte Hash
            
        Returns:
            bool: True, wenn das Passwort korrekt ist, sonst False
        """
        hashed_password = Encryption.hash_master_password(master_password)
        return hashed_password == stored_hash