# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QComboBox, QPushButton, QMessageBox, 
                             QLabel, QGroupBox, QTextEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import logging

class ClinicDialog(QDialog):
    def __init__(self, db_manager, parent=None, clinic_data=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.clinic_data = clinic_data
        self.is_edit_mode = clinic_data is not None
        
        self.setup_ui()
        self.setWindowTitle("تعديل العيادة" if self.is_edit_mode else "إضافة عيادة جديدة")
        self.setMinimumWidth(500)
        self.setModal(True)
        
    def setup_ui(self):
        """إعداد واجهة الحوار"""
        layout = QVBoxLayout()
        
        # العنوان
        title = QLabel("تعديل العيادة" if self.is_edit_mode else "إضافة عيادة جديدة")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title.setFont(title_font)
        title.setStyleSheet("color: #2C3E50; padding: 10px;")
        layout.addWidget(title)
        
        # معلومات العيادة
        info_group = QGroupBox("معلومات العيادة/المستشفى")
        info_layout = QFormLayout(info_group)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم العيادة أو المستشفى")
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["مستشفى", "مجمع عيادات", "عيادة خاصة"])
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+966500000000")
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@example.com")
        
        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(60)
        self.address_input.setPlaceholderText("عنوان العيادة")
        
        self.website_input = QLineEdit()
        self.website_input.setPlaceholderText("https://www.example.com")
        
        info_layout.addRow("اسم المؤسسة *:", self.name_input)
        info_layout.addRow("نوع المؤسسة *:", self.type_combo)
        info_layout.addRow("الهاتف الرئيسي:", self.phone_input)
        info_layout.addRow("البريد الإلكتروني:", self.email_input)
        info_layout.addRow("العنوان:", self.address_input)
        info_layout.addRow("الموقع الإلكتروني:", self.website_input)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # أزرار الحفظ والإلغاء
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("💾 حفظ")
        self.save_button.clicked.connect(self.save_clinic)
        self.save_button.setDefault(True)
        
        self.cancel_button = QPushButton("❌ إلغاء")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # إذا كان في وضع التعديل، تعبئة البيانات
        if self.is_edit_mode:
            self.fill_data()
    
    def fill_data(self):
        """تعبئة البيانات الحالية للعيادة"""
        if self.clinic_data:
            self.name_input.setText(self.clinic_data.get('name', ''))
            
            # تعيين نوع المؤسسة
            clinic_type = self.clinic_data.get('type', '')
            if clinic_type:
                index = self.type_combo.findText(clinic_type)
                if index >= 0:
                    self.type_combo.setCurrentIndex(index)
            
            self.phone_input.setText(self.clinic_data.get('main_phone', ''))
            self.email_input.setText(self.clinic_data.get('email', ''))
            self.address_input.setPlainText(self.clinic_data.get('address', ''))
            self.website_input.setText(self.clinic_data.get('website', ''))
    
    def validate_inputs(self):
        """التحقق من صحة البيانات"""
        # التحقق من الاسم
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "بيانات ناقصة", "اسم المؤسسة مطلوب")
            self.name_input.setFocus()
            return False
        
        return True
    
    def get_clinic_data(self):
        """استخراج بيانات العيادة من النموذج"""
        return {
            'name': self.name_input.text().strip(),
            'type': self.type_combo.currentText(),
            'main_phone': self.phone_input.text().strip() or None,
            'email': self.email_input.text().strip() or None,
            'address': self.address_input.toPlainText().strip() or None,
            'website': self.website_input.text().strip() or None
        }
    
    def save_clinic(self):
        """حفظ بيانات العيادة"""
        if not self.validate_inputs():
            return
        
        clinic_data = self.get_clinic_data()
        
        try:
            if self.is_edit_mode:
                # في وضع التعديل
                success = self.db_manager.update_clinic(self.clinic_data['id'], clinic_data)
                if success:
                    QMessageBox.information(self, "نجاح", "تم تحديث بيانات العيادة بنجاح")
                    self.accept()
                else:
                    QMessageBox.critical(self, "خطأ", "فشل في تحديث بيانات العيادة")
            else:
                # في وضع الإضافة
                clinic_id = self.db_manager.add_clinic(clinic_data)
                if clinic_id:
                    QMessageBox.information(self, "نجاح", f"تم إضافة العيادة بنجاح")
                    self.accept()
                else:
                    QMessageBox.critical(self, "خطأ", "فشل في إضافة العيادة")
                    
        except Exception as e:
            logging.error(f"خطأ في حفظ بيانات العيادة: {e}")
            QMessageBox.critical(self, "خطأ", f"حدث خطأ غير متوقع: {str(e)}")