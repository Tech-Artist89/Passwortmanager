#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
About-Dialog für den Passwortmanager.
Zeigt Informationen über die Anwendung.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTabWidget, QTextBrowser, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont

from gui.styles.resources import IconManager


class AboutDialog(QDialog):
    """Dialog mit Informationen über den Passwortmanager"""
    
    def __init__(self, parent=None):
        """
        Initialisiert den About-Dialog
        
        Args:
            parent (QWidget): Übergeordnetes Widget
        """
        super().__init__(parent)
        
        self.setWindowTitle("Über Passwortmanager")
        self.setMinimumWidth(550)
        self.setMinimumHeight(400)
        self.setWindowIcon(IconManager.get_icon('about'))
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Richtet die Benutzeroberfläche ein"""
        layout = QVBoxLayout(self)
        
        # Header mit Logo und Titel
        header_layout = QHBoxLayout()
        
        logo_label = QLabel()
        logo_pixmap = IconManager.get_pixmap('app').scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        header_layout.addWidget(logo_label)
        
        title_layout = QVBoxLayout()
        
        title_label = QLabel("Passwortmanager")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(16)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        
        version_label = QLabel("Version 2.0")
        version_font = QFont()
        version_font.setPointSize(10)
        version_label.setFont(version_font)
        title_layout.addWidget(version_label)
        
        title_layout.addStretch()
        header_layout.addLayout(title_layout)
        header_layout.addStretch(1)
        
        layout.addLayout(header_layout)
        
        # Tabs für verschiedene Informationen
        tabs = QTabWidget()
        
        # Über-Tab
        about_tab = QWidget()
        about_layout = QVBoxLayout(about_tab)
        
        about_text = QTextBrowser()
        about_text.setOpenExternalLinks(True)
        about_text.setHtml("""
        <p style="font-size: 10pt;">
        Ein sicherer und benutzerfreundlicher Passwortmanager zum Verwalten von Passwörtern und PINs für Websites und Geräte.
        </p>
        
        <p><b>Funktionen:</b></p>
        <ul>
        <li>Sichere AES-256 Verschlüsselung</li>
        <li>Passwort- und PIN-Generator</li>
        <li>Kategorien zur Organisation der Passwörter</li>
        <li>Favoriten-Funktion</li>
        <li>Automatische Sperre bei Inaktivität</li>
        <li>Hell- und Dunkelthema</li>
        <li>Backup- und Wiederherstellungsfunktionen</li>
        </ul>
        
        <p>
        Copyright &copy; 2025 - Alle Rechte vorbehalten.
        </p>
        """)
        
        about_layout.addWidget(about_text)
        tabs.addTab(about_tab, "Über")
        
        # Lizenz-Tab
        license_tab = QWidget()
        license_layout = QVBoxLayout(license_tab)
        
        license_text = QTextBrowser()
        license_text.setHtml("""
        <h3>MIT Lizenz</h3>
        
        <p>Copyright (c) 2025</p>
        
        <p>Hiermit wird unentgeltlich jeder Person, die eine Kopie der Software und der zugehörigen
        Dokumentationen (die "Software") erhält, die Erlaubnis erteilt, sie uneingeschränkt zu nutzen,
        inklusive und ohne Ausnahme mit dem Recht, sie zu verwenden, zu kopieren, zu verändern, zusammenzuführen,
        zu veröffentlichen, zu verbreiten und/oder zu unterlizenzieren, und Personen, denen diese
        Software überlassen wird, diese Rechte zu verschaffen, unter den folgenden Bedingungen:</p>
        
        <p>Der obige Urheberrechtsvermerk und dieser Erlaubnisvermerk sind in allen Kopien oder Teilkopien
        der Software beizulegen.</p>
        
        <p>DIE SOFTWARE WIRD OHNE JEDE AUSDRÜCKLICHE ODER IMPLIZIERTE GARANTIE BEREITGESTELLT, EINSCHLIESSLICH
        DER GARANTIE ZUR BENUTZUNG FÜR DEN VORGESEHENEN ODER EINEM BESTIMMTEN ZWECK SOWIE JEGLICHER
        RECHTSVERLETZUNG, JEDOCH NICHT DARAUF BESCHRÄNKT. IN KEINEM FALL SIND DIE AUTOREN ODER COPYRIGHTINHABER
        FÜR JEGLICHEN SCHADEN ODER SONSTIGE ANSPRÜCHE HAFTBAR ZU MACHEN, OB INFOLGE DER ERFÜLLUNG EINES
        VERTRAGES, EINES DELIKTES ODER ANDERS IM ZUSAMMENHANG MIT DER SOFTWARE ODER SONSTIGER VERWENDUNG
        DER SOFTWARE ENTSTANDEN.</p>
        """)
        
        license_layout.addWidget(license_text)
        tabs.addTab(license_tab, "Lizenz")
        
        # Bibliotheken-Tab
        libraries_tab = QWidget()
        libraries_layout = QVBoxLayout(libraries_tab)
        
        libraries_text = QTextBrowser()
        libraries_text.setOpenExternalLinks(True)
        libraries_text.setHtml("""
        <h3>Verwendete Bibliotheken</h3>
        
        <p><b>PyQt5</b><br>
        Version: 5.15.x<br>
        Lizenz: GPL v3<br>
        <a href="https://www.riverbankcomputing.com/software/pyqt/">https://www.riverbankcomputing.com/software/pyqt/</a></p>
        
        <p><b>cryptography</b><br>
        Version: 41.x<br>
        Lizenz: Apache License 2.0<br>
        <a href="https://cryptography.io/">https://cryptography.io/</a></p>
        
        <p><b>SQLite</b><br>
        Version: 3.x<br>
        Lizenz: Public Domain<br>
        <a href="https://www.sqlite.org/">https://www.sqlite.org/</a></p>
        """)
        
        libraries_layout.addWidget(libraries_text)
        tabs.addTab(libraries_tab, "Bibliotheken")
        
        layout.addWidget(tabs)
        
        # Schließen-Button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("Schließen")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)