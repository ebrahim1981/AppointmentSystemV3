# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QTextEdit, QComboBox, QDateEdit, 
                             QTimeEdit, QPushButton, QLabel, QGroupBox, QFrame, QGridLayout, QCheckBox)
from PyQt5.QtCore import Qt, QDate, QTime, pyqtSignal
from PyQt5.QtGui import QFont
import logging

class ControlsStatus(QWidget):
    """أزرار التحكم وشريط الحالة - منفصل ومتكامل"""
    
    # إشارات للتكامل
    save_requested = pyqtSignal()
    save_and_send_requested = pyqtSignal() 
    cancel_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """إعداد واجهة التحكم والحالة"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # شريط الحالة
        self.setup_status_bar(layout)
        
        # أزرار التحكم
        self.setup_control_buttons(layout)
        
    def setup_status_bar(self, parent_layout):
        """إعداد شريط الحالة"""
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #2C3E50;
                border-radius: 5px;
                padding: 6px;
            }
        """)
        status_layout = QHBoxLayout(status_frame)
        
        self.status_icon = QLabel("🟢")
        self.status_text = QLabel("جاهز")
        self.status_text.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        
        self.loading_label = QLabel("")
        self.loading_label.setStyleSheet("color: #3498DB; font-size: 11px;")
        
        status_layout.addWidget(self.status_icon)
        status_layout.addWidget(self.status_text)
        status_layout.addStretch()
        status_layout.addWidget(self.loading_label)
        
        parent_layout.addWidget(status_frame)
        
    def setup_control_buttons(self, parent_layout):
        """إعداد أزرار التحكم"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # زر الحفظ والإرسال
        self.save_send_button = QPushButton("💾📤 حفظ وإرسال رسالة")
        self.save_send_button.clicked.connect(self.on_save_send_clicked)
        self.save_send_button.setMinimumHeight(40)
        self.save_send_button.setStyleSheet(self.get_button_style("primary", True))
        
        # زر الحفظ الأساسي
        self.save_button = QPushButton("💾 حفظ الموعد")
        self.save_button.clicked.connect(self.on_save_clicked)
        self.save_button.setDefault(True)
        self.save_button.setMinimumHeight(40)
        self.save_button.setStyleSheet(self.get_button_style("success", True))
        
        # زر الإلغاء
        self.cancel_button = QPushButton("❌ إلغاء")
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.setStyleSheet(self.get_button_style("danger", True))
        
        button_layout.addWidget(self.save_send_button)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        
        parent_layout.addLayout(button_layout)
    
    def on_save_clicked(self):
        """عند النقر على حفظ"""
        self.save_requested.emit()
    
    def on_save_send_clicked(self):
        """عند النقر على حفظ وإرسال"""
        self.save_and_send_requested.emit()
    
    def on_cancel_clicked(self):
        """عند النقر على إلغاء"""
        self.cancel_requested.emit()
    
    def set_buttons_enabled(self, enabled):
        """تفعيل/تعطيل الأزرار"""
        self.save_button.setEnabled(enabled)
        self.save_send_button.setEnabled(enabled)
    
    def set_status(self, status_type, message, loading_text=""):
        """تعيين حالة النظام"""
        status_config = {
            "ready": {"icon": "🟢", "color": "#27AE60"},
            "loading": {"icon": "🟡", "color": "#F39C12"}, 
            "error": {"icon": "🔴", "color": "#E74C3C"},
            "warning": {"icon": "🟠", "color": "#E67E22"}
        }
        
        config = status_config.get(status_type, status_config["ready"])
        self.status_icon.setText(config["icon"])
        self.status_text.setText(message)
        self.status_text.setStyleSheet(f"color: {config['color']}; font-size: 12px; font-weight: bold;")
        self.loading_label.setText(loading_text)
    
    def get_button_style(self, button_type="primary", large=False):
        """أنماط الأزرار"""
        styles = {
            "primary": """
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #2980B9;
                }
            """,
            "success": """
                QPushButton {
                    background-color: #27AE60;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #219A52;
                }
            """,
            "danger": """
                QPushButton {
                    background-color: #E74C3C;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #C0392B;
                }
            """
        }
        
        style = styles.get(button_type, styles["primary"])
        if large:
            style = style.replace("8px 16px", "10px 20px")
        return style