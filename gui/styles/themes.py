#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Theme-Definitionen für den Passwortmanager.
Definiert verschiedene visuelle Themes für die Anwendung.
"""

from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication


class Themes:
    """Klasse für die Verwaltung verschiedener Themes"""
    
    @staticmethod
    def apply_theme(app, theme_name="light"):
        """
        Wendet ein bestimmtes Theme auf die Anwendung an
        
        Args:
            app (QApplication): Die QApplication-Instanz
            theme_name (str): Name des Themes ('light' oder 'dark')
        """
        if theme_name.lower() == "dark":
            Themes.apply_dark_theme(app)
        else:
            Themes.apply_light_theme(app)
    
    @staticmethod
    def apply_light_theme(app):
        """
        Wendet das helle Theme auf die Anwendung an
        
        Args:
            app (QApplication): Die QApplication-Instanz
        """
        app.setStyle("Fusion")
        
        # Standardfarben wiederherstellen
        app.setPalette(QApplication.style().standardPalette())
        
        # Benutzerdefinierte Stylesheet-Anpassungen
        app.setStyleSheet("""
            QMainWindow, QDialog {
                background-color: #F5F5F5;
            }
            
            QTabWidget::pane {
                border: 1px solid #C0C0C0;
                background-color: white;
            }
            
            QTabBar::tab {
                background-color: #E0E0E0;
                border: 1px solid #C0C0C0;
                padding: 5px 10px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
            }
            
            QPushButton {
                background-color: #E0E0E0;
                border: 1px solid #C0C0C0;
                padding: 5px 10px;
                border-radius: 3px;
            }
            
            QPushButton:hover {
                background-color: #D0D0D0;
            }
            
            QPushButton:pressed {
                background-color: #B0B0B0;
            }
            
            /* Farbliche Gestaltung der Aktionsbuttons */
            QPushButton[class="delete"] {
                background-color: #F5A9A9;
                border: 1px solid #F56E6E;
                color: #9C0000;
            }
            
            QPushButton[class="delete"]:hover {
                background-color: #F56E6E;
                color: white;
            }
            
            QPushButton[class="edit"] {
                background-color: #F5DA81;
                border: 1px solid #F5C16E;
                color: #9C6500;
            }
            
            QPushButton[class="edit"]:hover {
                background-color: #F5C16E;
                color: #704800;
            }
            
            QPushButton[class="save"] {
                background-color: #A9F5A9;
                border: 1px solid #6EF56E;
                color: #006E00;
            }
            
            QPushButton[class="save"]:hover {
                background-color: #6EF56E;
                color: #004F00;
            }
            
            QPushButton[class="view"] {
                background-color: #A9D2F5;
                border: 1px solid #6EA9F5;
                color: #00509C;
            }
            
            QPushButton[class="view"]:hover {
                background-color: #6EA9F5;
                color: #003F78;
            }
            
            QLineEdit, QTextEdit, QComboBox {
                border: 1px solid #C0C0C0;
                background-color: white;
                selection-background-color: #B5D3FF;
                selection-color: black;
                padding: 2px;
            }
            
            QTableWidget {
                gridline-color: #E0E0E0;
                selection-background-color: #B5D3FF;
                selection-color: black;
            }
            
            QHeaderView::section {
                background-color: #E0E0E0;
                padding: 4px;
                border: 1px solid #C0C0C0;
                font-weight: bold;
            }
            
            QStatusBar {
                background-color: #E0E0E0;
                color: #333333;
            }
        """)
    
    @staticmethod
    def apply_dark_theme(app):
        """
        Wendet das dunkle Theme auf die Anwendung an
        
        Args:
            app (QApplication): Die QApplication-Instanz
        """
        app.setStyle("Fusion")
        
        # Dunkle Palette erstellen
        dark_palette = QPalette()
        
        # Farben definieren
        dark_color = QColor(45, 45, 45)
        disabled_color = QColor(127, 127, 127)
        text_color = QColor(255, 255, 255)
        highlight_color = QColor(42, 130, 218)
        window_color = QColor(53, 53, 53)
        background_color = QColor(66, 66, 66)
        
        # Farben auf Palette anwenden
        dark_palette.setColor(QPalette.Window, window_color)
        dark_palette.setColor(QPalette.WindowText, text_color)
        dark_palette.setColor(QPalette.Base, background_color)
        dark_palette.setColor(QPalette.AlternateBase, window_color)
        dark_palette.setColor(QPalette.ToolTipBase, window_color)
        dark_palette.setColor(QPalette.ToolTipText, text_color)
        dark_palette.setColor(QPalette.Text, text_color)
        dark_palette.setColor(QPalette.Button, dark_color)
        dark_palette.setColor(QPalette.ButtonText, text_color)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, highlight_color)
        dark_palette.setColor(QPalette.Highlight, highlight_color)
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        
        # Disabled-Farben
        dark_palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled_color)
        dark_palette.setColor(QPalette.Disabled, QPalette.Text, disabled_color)
        dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_color)
        
        # Palette anwenden
        app.setPalette(dark_palette)
        
        # Weitere Anpassungen über Stylesheet
        app.setStyleSheet("""
            QToolTip {
                color: #ffffff;
                background-color: #2a82da;
                border: 1px solid #53585c;
            }
            
            QTabWidget::pane {
                border: 1px solid #444;
                background-color: #333;
            }
            
            QTabBar::tab {
                background-color: #333;
                border: 1px solid #444;
                padding: 5px 10px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background-color: #444;
                border-bottom-color: #444;
            }
            
            QPushButton {
                background-color: #555;
                border: 1px solid #777;
                padding: 5px 10px;
                border-radius: 3px;
                color: #ddd;
            }
            
            QPushButton:hover {
                background-color: #666;
            }
            
            QPushButton:pressed {
                background-color: #777;
            }
            
            /* Farbliche Gestaltung der Aktionsbuttons im Dark Mode */
            QPushButton[class="delete"] {
                background-color: #8B0000;
                border: 1px solid #A70000;
                color: #FFD0D0;
            }
            
            QPushButton[class="delete"]:hover {
                background-color: #A70000;
                color: white;
            }
            
            QPushButton[class="edit"] {
                background-color: #8B6914;
                border: 1px solid #A78500;
                color: #FFE8A0;
            }
            
            QPushButton[class="edit"]:hover {
                background-color: #A78500;
                color: white;
            }
            
            QPushButton[class="save"] {
                background-color: #006400;
                border: 1px solid #008000;
                color: #D0FFD0;
            }
            
            QPushButton[class="save"]:hover {
                background-color: #008000;
                color: white;
            }
            
            QPushButton[class="view"] {
                background-color: #00008B;
                border: 1px solid #0000A7;
                color: #D0D0FF;
            }
            
            QPushButton[class="view"]:hover {
                background-color: #0000A7;
                color: white;
            }
            
            QLineEdit, QTextEdit, QComboBox {
                background-color: #444;
                border: 1px solid #555;
                color: #ddd;
                selection-background-color: #2a82da;
                selection-color: white;
            }
            
            QTableWidget {
                gridline-color: #555;
                background-color: #333;
                color: #ddd;
                selection-background-color: #2a82da;
                selection-color: white;
            }
            
            QHeaderView::section {
                background-color: #444;
                color: #ddd;
                padding: 4px;
                border: 1px solid #666;
            }
            
            QStatusBar {
                background-color: #444;
                color: #ddd;
            }
        """)