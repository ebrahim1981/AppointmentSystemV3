# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QTextEdit, QComboBox, QPushButton, 
                             QMessageBox, QLabel, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import logging

class DepartmentDialog(QDialog):
    def __init__(self, db_manager, parent=None, department_data=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.department_data = department_data
        self.is_edit_mode = department_data is not None
        
        self.setup_ui()
        self.setWindowTitle("تعديل القسم" if self.is_edit_mode else "إضافة قسم جديد")
        self.setMinimumWidth(500)
        self.setModal(True)
        
    def setup_ui(self):
        """إعداد واجهة الحوار"""
        layout = QVBoxLayout()
        
        # العنوان
        title = QLabel("تعديل القسم" if self.is_edit_mode else "إضافة قسم جديد")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title.setFont(title_font)
        title.setStyleSheet("color: #2C3E50; padding: 10px;")
        layout.addWidget(title)
        
        # معلومات القسم
        info_group = QGroupBox("معلومات القسم")
        info_layout = QFormLayout(info_group)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم القسم")
        
        self.clinic_combo = QComboBox()
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("وصف القسم والخدمات المقدمة...")
        
        info_layout.addRow("📋 اسم القسم *:", self.name_input)
        info_layout.addRow("🏥 العيادة *:", self.clinic_combo)
        info_layout.addRow("📝 الوصف:", self.description_input)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # أزرار الحفظ والإلغاء
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("💾 حفظ")
        self.save_button.clicked.connect(self.save_department)
        self.save_button.setDefault(True)
        
        self.cancel_button = QPushButton("❌ إلغاء")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # تحميل البيانات
        self.load_data()
        
        # إذا كان في وضع التعديل، تعبئة البيانات
        if self.is_edit_mode:
            self.fill_data()
    
    def load_data(self):
        """تحميل قوائم البيانات"""
        try:
            # تحميل العيادات
            clinics = self.db_manager.get_clinics()
            self.clinic_combo.clear()
            self.clinic_combo.addItem("-- اختر العيادة --", None)
            for clinic in clinics:
                self.clinic_combo.addItem(f"{clinic['name']} ({clinic['type']})", clinic['id'])
            
        except Exception as e:
            logging.error(f"خطأ في تحميل البيانات: {e}")
            QMessageBox.warning(self, "تحذير", f"خطأ في تحميل البيانات: {e}")
    
    def fill_data(self):
        """تعبئة البيانات الحالية للقسم"""
        if self.department_data:
            self.name_input.setText(self.department_data.get('name', ''))
            
            # تعيين العيادة
            clinic_id = self.department_data.get('clinic_id')
            if clinic_id:
                index = self.clinic_combo.findData(clinic_id)
                if index >= 0:
                    self.clinic_combo.setCurrentIndex(index)
            
            self.description_input.setPlainText(self.department_data.get('description', ''))
    
    def validate_inputs(self):
        """التحقق من صحة البيانات"""
        # التحقق من الاسم
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "بيانات ناقصة", "اسم القسم مطلوب")
            self.name_input.setFocus()
            return False
        
        # التحقق من العيادة
        if not self.clinic_combo.currentData():
            QMessageBox.warning(self, "بيانات ناقصة", "يرجى اختيار عيادة")
            self.clinic_combo.setFocus()
            return False
        
        return True
    
    def get_department_data(self):
        """استخراج بيانات القسم من النموذج"""
        return {
            'name': self.name_input.text().strip(),
            'clinic_id': self.clinic_combo.currentData(),
            'description': self.description_input.toPlainText().strip() or None
        }
    
    def save_department(self):
        """حفظ بيانات القسم"""
        if not self.validate_inputs():
            return
        
        department_data = self.get_department_data()
        
        try:
            if self.is_edit_mode:
                # في وضع التعديل
                success = self.db_manager.update_department(self.department_data['id'], department_data)
                if success:
                    QMessageBox.information(self, "نجاح", "تم تحديث بيانات القسم بنجاح")
                    self.accept()
                else:
                    QMessageBox.critical(self, "خطأ", "فشل في تحديث بيانات القسم")
            else:
                # في وضع الإضافة
                department_id = self.db_manager.add_department(department_data)
                if department_id:
                    QMessageBox.information(self, "نجاح", f"تم إضافة القسم بنجاح")
                    self.accept()
                else:
                    QMessageBox.critical(self, "خطأ", "فشل في إضافة القسم")
                    
        except Exception as e:
            logging.error(f"خطأ في حفظ بيانات القسم: {e}")
            QMessageBox.critical(self, "خطأ", f"حدث خطأ غير متوقع: {str(e)}")