import random
import string
import cv2
import numpy as np
import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QTextEdit, 
                            QFileDialog, QVBoxLayout, QHBoxLayout, QGroupBox, 
                            QSplitter, QFrame, QStatusBar, QMainWindow)
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QPixmap, QLinearGradient, QBrush, QGradient, QPainter, QPen
from PyQt6.QtCore import Qt, QSize, QPoint, QRect
from stegano import SanskritSteganoSystem  # Import the class from the correct module

class CustomButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(40)
        self.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: #2C3E50;
                color: #ECF0F1;
                border: 2px solid #34495E;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #34495E;
                border: 2px solid #3498DB;
            }
            QPushButton:pressed {
                background-color: #1A2530;
            }
        """)


class HeaderFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)
        self.setStyleSheet("background-color: #0B1622; border-radius: 8px;")
        
        # Create SVG backgrounds for header
        self.binary_pattern = """
            <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
                <text x="5" y="15" fill="#1a3050" font-family="monospace" font-size="10px">10110101</text>
                <text x="35" y="25" fill="#1a3050" font-family="monospace" font-size="10px">01101100</text>
                <text x="15" y="35" fill="#1a3050" font-family="monospace" font-size="10px">11001010</text>
                <text x="45" y="45" fill="#1a3050" font-family="monospace" font-size="10px">00110110</text>
                <text x="25" y="55" fill="#1a3050" font-family="monospace" font-size="10px">10101101</text>
                <text x="55" y="65" fill="#1a3050" font-family="monospace" font-size="10px">01011010</text>
                <text x="35" y="75" fill="#1a3050" font-family="monospace" font-size="10px">11010101</text>
                <text x="15" y="85" fill="#1a3050" font-family="monospace" font-size="10px">00101101</text>
                <text x="45" y="95" fill="#1a3050" font-family="monospace" font-size="10px">10110010</text>
            </svg>
        """
        
        self.sanskrit_pattern = """
            <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
                <text x="5" y="15" fill="#1a3050" font-family="serif" font-size="12px">अ आ इ ई</text>
                <text x="35" y="30" fill="#1a3050" font-family="serif" font-size="12px">उ ऊ ऋ ॠ</text>
                <text x="10" y="45" fill="#1a3050" font-family="serif" font-size="12px">ऌ ॡ ए ऐ</text>
                <text x="40" y="60" fill="#1a3050" font-family="serif" font-size="12px">ओ औ अं अः</text>
                <text x="15" y="75" fill="#1a3050" font-family="serif" font-size="12px">क ख ग घ</text>
                <text x="25" y="90" fill="#1a3050" font-family="serif" font-size="12px">ङ च छ ज</text>
            </svg>
        """

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background gradient
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor("#0B1622"))
        gradient.setColorAt(1, QColor("#162436"))
        painter.fillRect(self.rect(), gradient)
        
        # Draw binary and Sanskrit patterns as background elements
        for i in range(0, self.width(), 100):
            for j in range(0, self.height(), 100):
                pattern = self.binary_pattern if (i//100 + j//100) % 2 == 0 else self.sanskrit_pattern
                if i < self.width() - 100 and j < self.height() - 100:
                    painter.drawPixmap(QPoint(i, j), QPixmap.fromImage(QPixmap.loadFromData(bytes(pattern, 'utf-8')).toImage()))
        
        # Draw a translucent overlay to make the background subtle
        painter.fillRect(self.rect(), QColor(11, 22, 34, 200))
        
        # Draw a decorative line at the bottom
        painter.setPen(QColor("#3498DB"))
        painter.drawLine(20, self.height()-2, self.width()-20, self.height()-2)
        
        # Draw circle decorations
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#1A5276"))
        painter.drawEllipse(15, 15, 12, 12)
        painter.drawEllipse(self.width()-27, 15, 12, 12)
        painter.setBrush(QColor("#3498DB"))
        painter.drawEllipse(18, 18, 6, 6)
        painter.drawEllipse(self.width()-24, 18, 6, 6)


class LockIcon(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw padlock body
        painter.setPen(QColor("#3498DB"))
        painter.setBrush(QColor("#1A5276"))
        painter.drawRoundedRect(10, 25, 40, 30, 5, 5)
        
        # Draw padlock arc
        pen = QPen(QColor("#3498DB"), 3)
        painter.setPen(pen)
        painter.drawArc(15, 5, 30, 40, 0*16, 180*16)
        
        # Draw keyhole
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#0B1622"))
        painter.drawEllipse(25, 35, 10, 10)
        painter.drawRect(29, 40, 2, 7)


class DevanagariIcon(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set font for Devanagari script
        font = QFont("Arial Unicode MS", 30)
        painter.setFont(font)
        painter.setPen(QColor("#3498DB"))
        
        # Draw a Devanagari character (ka)
        painter.drawText(QRect(0, 0, 60, 60), Qt.AlignmentFlag.AlignCenter, "क")
        
        # Draw decorative circle
        pen = QPen(QColor("#1A5276"), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(5, 5, 50, 50)


class SteganoGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.system = SanskritSteganoSystem()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("CipherVeil: Katapayadi System")
        self.setGeometry(200, 200, 900, 650)
        
        # Set theme colors
        main_palette = QPalette()
        main_palette.setColor(QPalette.ColorRole.Window, QColor(15, 25, 35))
        main_palette.setColor(QPalette.ColorRole.WindowText, QColor(236, 240, 241))
        main_palette.setColor(QPalette.ColorRole.Base, QColor(30, 40, 50))
        main_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 55, 65))
        main_palette.setColor(QPalette.ColorRole.Text, QColor(236, 240, 241))
        main_palette.setColor(QPalette.ColorRole.Button, QColor(44, 62, 80))
        main_palette.setColor(QPalette.ColorRole.ButtonText, QColor(236, 240, 241))
        main_palette.setColor(QPalette.ColorRole.Highlight, QColor(52, 152, 219))
        self.setPalette(main_palette)
        
        # Try to set app icon (create a path that works on both dev and packaged app)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cipherveil_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Main widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        
        # Enhanced Header with logo and title
        header_frame = HeaderFrame()
        header_layout = QHBoxLayout(header_frame)
        
        # Left icon - lock
        lock_icon = LockIcon()
        header_layout.addWidget(lock_icon)
        
        # Center title with special styling
        title_container = QVBoxLayout()
        title_container.setSpacing(5)
        
        main_title = QLabel("CipherVeil")
        main_title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        main_title.setStyleSheet("color: #3498DB; font-weight: bold;")
        
        subtitle = QLabel("Katapayadi System")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setStyleSheet("color: #7FB3D5;")
        
        title_container.addWidget(main_title, alignment=Qt.AlignmentFlag.AlignCenter)
        title_container.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)
        header_layout.addLayout(title_container)
        
        # Right icon - Devanagari
        devanagari_icon = DevanagariIcon()
        header_layout.addWidget(devanagari_icon)
        
        main_layout.addWidget(header_frame)
        
        # Description text
        description_label = QLabel("Ancient Sanskrit cryptography meets modern steganography. Hide your secrets in plain sight.")
        description_label.setFont(QFont("Arial", 10, QFont.Weight.Normal))
        description_label.setStyleSheet("color: #BDC3C7; font-style: italic;")
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(description_label)
        
        # Splitter to allow resizing sections
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # Left panel - Encoding
        encode_panel = QGroupBox("Encode Secret Message")
        encode_panel.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        encode_panel.setStyleSheet("""
            QGroupBox {
                border: 2px solid #34495E;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                color: #3498DB;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                background-color: #0F1923;
            }
        """)
        
        encode_layout = QVBoxLayout(encode_panel)
        
        # Instructions
        encode_instructions = QLabel("Enter your secret message to hide it within an image:")
        encode_instructions.setFont(QFont("Arial", 10))
        encode_instructions.setWordWrap(True)
        encode_layout.addWidget(encode_instructions)
        
        # Text input with styling
        self.input_text = QTextEdit()
        self.input_text.setFont(QFont("Consolas", 10))
        self.input_text.setPlaceholderText("Type your secret message here...")
        self.input_text.setStyleSheet("""
            QTextEdit {
                background-color: #1C2833;
                color: #ECF0F1;
                border: 2px solid #2C3E50;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        encode_layout.addWidget(self.input_text)
        
        # Encode button
        self.encode_button = CustomButton("Encrypt & Hide Message in Image")
        encode_layout.addWidget(self.encode_button)
        
        # Right panel - Decoding
        decode_panel = QGroupBox("Reveal Hidden Message")
        decode_panel.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        decode_panel.setStyleSheet("""
            QGroupBox {
                border: 2px solid #34495E;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                color: #E74C3C;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                background-color: #0F1923;
            }
        """)
        
        decode_layout = QVBoxLayout(decode_panel)
        
        # Decoded message display
        decode_instructions = QLabel("Extract hidden messages from steganographic images:")
        decode_instructions.setFont(QFont("Arial", 10))
        decode_instructions.setWordWrap(True)
        decode_layout.addWidget(decode_instructions)
        
        # Result display
        result_frame = QFrame()
        result_frame.setStyleSheet("""
            QFrame {
                background-color: #1C2833;
                border: 2px solid #2C3E50;
                border-radius: 8px;
            }
        """)
        result_layout = QVBoxLayout(result_frame)
        
        result_title = QLabel("Decoded Message:")
        result_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        result_layout.addWidget(result_title)
        
        self.result_text = QTextEdit()
        self.result_text.setFont(QFont("Consolas", 10))
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("""
            QTextEdit {
                background-color: #1C2833;
                color: #2ECC71;
                border: none;
                border-radius: 4px;
            }
        """)
        result_layout.addWidget(self.result_text)
        
        decode_layout.addWidget(result_frame)
        
        # Decode button
        self.decode_button = CustomButton("Decrypt Hidden Message from Image")
        self.decode_button.setStyleSheet("""
            QPushButton {
                background-color: #641E16;
                color: #ECF0F1;
                border: 2px solid #922B21;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #922B21;
                border: 2px solid #E74C3C;
            }
            QPushButton:pressed {
                background-color: #4A0F09;
            }
        """)
        decode_layout.addWidget(self.decode_button)
        
        # Add panels to splitter
        splitter.addWidget(encode_panel)
        splitter.addWidget(decode_panel)
        main_layout.addWidget(splitter)
        
        # Information footer
        info_frame = QFrame()
        info_frame.setMaximumHeight(40)
        info_frame.setStyleSheet("background-color: #162436; border-radius: 5px;")
        info_layout = QHBoxLayout(info_frame)
        
        info_text = QLabel("Katapayadi System: An ancient Sanskrit numerical notation system used for cryptography")
        info_text.setFont(QFont("Arial", 8))
        info_text.setStyleSheet("color: #7FB3D5;")
        info_layout.addWidget(info_text, alignment=Qt.AlignmentFlag.AlignCenter)
        
        main_layout.addWidget(info_frame)
        
        # Status bar at bottom
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #0B1622;
                color: #3498DB;
                border-top: 1px solid #34495E;
            }
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready to encode or decode messages...")
        
        # Connect event handlers
        self.encode_button.clicked.connect(self.encode_message)
        self.decode_button.clicked.connect(self.decode_message)
    
    def encode_message(self):
        message = self.input_text.toPlainText()
        if not message:
            self.status_bar.showMessage("Please enter a message to encode", 3000)
            return
        
        image_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Base Image for Steganography",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if not image_path:
            return
        
        output_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Steganographic Image", 
            "", 
            "PNG Files (*.png)"
        )
        if not output_path:
            return
        
        try:
            self.system.encode_message_to_image(message, image_path, output_path)
            self.status_bar.showMessage("Message successfully encrypted and hidden in image!", 5000)
        except Exception as e:
            self.status_bar.showMessage(f"Error encoding message: {str(e)}", 5000)
    
    def decode_message(self):
        image_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Steganographic Image to Decode",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if not image_path:
            return
        
        try:
            decoded_message = self.system.decode_message_from_image(image_path)
            self.result_text.setText(decoded_message)
            self.status_bar.showMessage("Message successfully decoded!", 5000)
        except Exception as e:
            self.status_bar.showMessage(f"Error decoding message: {str(e)}", 5000)
            self.result_text.setText("Failed to decode. This might not be a valid steganographic image.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Set application-wide font
    app.setFont(QFont("Arial", 10))
    
    # Set stylesheet for file dialogs
    app.setStyleSheet("""
        QFileDialog {
            background-color: #1A2530;
            color: #ECF0F1;
        }
        QFileDialog QListView, QFileDialog QTreeView, QFileDialog QComboBox, 
        QFileDialog QLineEdit, QFileDialog QAbstractItemView {
            background-color: #1C2833;
            color: #ECF0F1;
            border: 1px solid #2C3E50;
        }
        QFileDialog QPushButton {
            background-color: #2C3E50;
            color: #ECF0F1;
            border: 1px solid #34495E;
            border-radius: 4px;
            padding: 5px;
            min-width: 80px;
        }
        QFileDialog QPushButton:hover {
            background-color: #34495E;
        }
    """)
    
    gui = SteganoGUI()
    gui.show()
    sys.exit(app.exec())