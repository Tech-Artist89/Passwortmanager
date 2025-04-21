#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
StrengthMeter-Widget für den Passwortmanager.
Stellt eine visuelle Anzeige der Passwortstärke bereit.
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QColor

from core.password_generator import PasswordGenerator


class StrengthMeter(QWidget):
    """Widget zur Anzeige der Passwortstärke"""
    
    def __init__(self, parent=None):
        """
        Initialisiert das StrengthMeter-Widget
        
        Args:
            parent (QWidget): Übergeordnetes Widget
        """
        super().__init__(parent)
        
        self.password_generator = PasswordGenerator()
        self.strength_info = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Richtet die Benutzeroberfläche ein"""
        # Hauptlayout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Fortschrittsanzeige
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        layout.addWidget(self.progress_bar)
        
        # Informationen
        info_layout = QHBoxLayout()
        
        self.rating_label = QLabel("Keine Bewertung")
        self.rating_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        info_layout.addWidget(self.rating_label)
        
        self.score_label = QLabel("")
        self.score_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        info_layout.addWidget(self.score_label)
        
        layout.addLayout(info_layout)
        
        # Feedback-Text
        self.feedback_label = QLabel("")
        self.feedback_label.setWordWrap(True)
        layout.addWidget(self.feedback_label)
        
        # Stylesheet anwenden
        self._apply_stylesheet()
    
    def _apply_stylesheet(self):
        """Wendet Stylesheet auf das Widget an"""
        self.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                background-color: #f5f5f5;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: green;
                border-radius: 2px;
            }
            QLabel {
                color: #333;
            }
        """)
    
    @pyqtSlot(str)
    def update_strength(self, password):
        """
        Aktualisiert die Anzeige der Passwortstärke
        
        Args:
            password (str): Das zu bewertende Passwort
        """
        # Bewertung der Passwortstärke
        self.strength_info = self.password_generator.calculate_password_strength(password)
        
        # Fortschrittsanzeige aktualisieren
        self.progress_bar.setValue(self.strength_info["score"])
        
        # Farbe basierend auf Bewertung
        self._update_progress_color(self.strength_info["color"])
        
        # Labels aktualisieren
        self.rating_label.setText(self.strength_info["rating"])
        self.score_label.setText(f"{self.strength_info['score']}%")
        
        # Feedback anzeigen
        if "feedback" in self.strength_info and self.strength_info["feedback"]:
            self.feedback_label.setText(", ".join(self.strength_info["feedback"]))
        else:
            self.feedback_label.setText("")
    
    def _update_progress_color(self, color_name):
        """
        Aktualisiert die Farbe der Fortschrittsanzeige
        
        Args:
            color_name (str): Name der Farbe (red, orange, green, etc.)
        """
        # Stylesheet für die Fortschrittsanzeige
        self.progress_bar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color_name};
                border-radius: 2px;
            }}
        """)
    
    def get_strength_info(self):
        """
        Gibt die aktuelle Stärke-Information zurück
        
        Returns:
            dict: Informationen zur Passwortstärke oder None, wenn nicht verfügbar
        """
        return self.strength_info
    
    def clear(self):
        """Setzt die Anzeige zurück"""
        self.progress_bar.setValue(0)
        self.rating_label.setText("Keine Bewertung")
        self.score_label.setText("")
        self.feedback_label.setText("")
        self.strength_info = None
        self._update_progress_color("gray")