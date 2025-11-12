# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QLineEdit, QPushButton, QColorDialog, QMessageBox,
                             QDialogButtonBox, QLabel, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
import logging

class PatientTagsManager(QDialog):
    def __init__(self, db_manager, patient_id, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.patient_id = patient_id
        self.setup_ui()
        self.load_tags()
        
    def setup_ui(self):
        self.setWindowTitle("إدارة علامات المريض")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # عنوان
        title = QLabel("علامات المريض")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # قائمة العلامات الحالية
        self.tags_list = QListWidget()
        layout.addWidget(QLabel("العلامات الحالية:"))
        layout.addWidget(self.tags_list)
        
        # إضافة علامة جديدة
        add_layout = QHBoxLayout()
        self.new_tag_input = QLineEdit()
        self.new_tag_input.setPlaceholderText("اسم العلامة الجديدة")
        self.add_button = QPushButton("إضافة")
        self.add_button.clicked.connect(self.add_tag)
        
        add_layout.addWidget(self.new_tag_input)
        add_layout.addWidget(self.add_button)
        layout.addLayout(add_layout)
        
        # أزرار
        button_layout = QHBoxLayout()
        self.remove_button = QPushButton("إزالة المحدد")
        self.remove_button.clicked.connect(self.remove_tag)
        self.clear_button = QPushButton("مسح الكل")
        self.clear_button.clicked.connect(self.clear_tags)
        
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.clear_button)
        layout.addLayout(button_layout)
        
        # أزرار الحوار
        dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dialog_buttons.accepted.connect(self.accept)
        dialog_buttons.rejected.connect(self.reject)
        layout.addWidget(dialog_buttons)
        
        self.setLayout(layout)
    
    def load_tags(self):
        """تحميل العلامات الحالية للمريض"""
        try:
            tags = self.db_manager.get_patient_tags(self.patient_id)
            self.tags_list.clear()
            self.tags_list.addItems(tags)
        except Exception as e:
            logging.error(f"خطأ في تحميل العلامات: {e}")
    
    def add_tag(self):
        """إضافة علامة جديدة"""
        tag_name = self.new_tag_input.text().strip()
        if not tag_name:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال اسم العلامة")
            return
        
        try:
            success = self.db_manager.add_patient_tag(self.patient_id, tag_name)
            if success:
                self.new_tag_input.clear()
                self.load_tags()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في إضافة العلامة")
        except Exception as e:
            logging.error(f"خطأ في إضافة علامة: {e}")
            QMessageBox.critical(self, "خطأ", f"حدث خطأ: {str(e)}")
    
    def remove_tag(self):
        """إزالة العلامة المحددة"""
        current_item = self.tags_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار علامة لإزالتها")
            return
        
        tag_name = current_item.text()
        try:
            success = self.db_manager.remove_patient_tag(self.patient_id, tag_name)
            if success:
                self.load_tags()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في إزالة العلامة")
        except Exception as e:
            logging.error(f"خطأ في إزالة علامة: {e}")
            QMessageBox.critical(self, "خطأ", f"حدث خطأ: {str(e)}")
    
    def clear_tags(self):
        """مسح جميع العلامات"""
        reply = QMessageBox.question(
            self, 
            "تأكيد المسح", 
            "هل أنت متأكد من مسح جميع العلامات؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                tags = self.db_manager.get_patient_tags(self.patient_id)
                for tag in tags:
                    self.db_manager.remove_patient_tag(self.patient_id, tag)
                self.load_tags()
            except Exception as e:
                logging.error(f"خطأ في مسح العلامات: {e}")
                QMessageBox.critical(self, "خطأ", f"حدث خطأ: {str(e)}")