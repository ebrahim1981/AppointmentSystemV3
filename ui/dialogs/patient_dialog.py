# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QTextEdit, QComboBox, QDateEdit,
                             QPushButton, QMessageBox, QLabel, QGroupBox, QCheckBox)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
import logging

class PatientDialog(QDialog):
    def __init__(self, db_manager, parent=None, patient_data=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.patient_data = patient_data
        self.is_edit_mode = patient_data is not None
        
        # التحقق من بيانات المريض في وضع التعديل
        if self.is_edit_mode:
            if not self.validate_patient_data():
                logging.error(f"بيانات المريض غير صالحة: {patient_data}")
                QMessageBox.critical(self, "خطأ", "بيانات المريض غير صالحة للتعديل")
                return
        
        self.setup_ui()
        self.setWindowTitle("تعديل بيانات المريض" if self.is_edit_mode else "إضافة مريض جديد")
        self.setMinimumWidth(600)
        self.setModal(True)
        
    def validate_patient_data(self):
        """التحقق من صحة بيانات المريض في وضع التعديل"""
        if not self.patient_data:
            return False
        
        required_fields = ['id', 'name', 'phone']
        for field in required_fields:
            if field not in self.patient_data or self.patient_data[field] is None:
                logging.error(f"حقل {field} مفقود أو None في بيانات المريض")
                return False
        
        # التحقق من أن ID هو رقم صحيح
        try:
            patient_id = int(self.patient_data['id'])
            if patient_id <= 0:
                logging.error(f"ID المريض غير صالح: {patient_id}")
                return False
        except (ValueError, TypeError):
            logging.error(f"ID المريض ليس رقماً صحيحاً: {self.patient_data['id']}")
            return False
        
        return True
    
    def setup_ui(self):
        """إعداد واجهة الحوار"""
        layout = QVBoxLayout()
        
        # العنوان
        title = QLabel("تعديل بيانات المريض" if self.is_edit_mode else "إضافة مريض جديد")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title.setFont(title_font)
        title.setStyleSheet("color: #2C3E50; padding: 10px;")
        layout.addWidget(title)
        
        # المعلومات الأساسية
        basic_group = QGroupBox("المعلومات الأساسية")
        basic_layout = QFormLayout(basic_group)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("الاسم الكامل للمريض")
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("رقم الجوال")
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("البريد الإلكتروني")
        
        self.date_of_birth = QDateEdit()
        self.date_of_birth.setDate(QDate(2000, 1, 1))
        self.date_of_birth.setCalendarPopup(True)
        self.date_of_birth.setMaximumDate(QDate.currentDate())
        
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["", "ذكر", "أنثى"])
        
        basic_layout.addRow("👤 الاسم الكامل *:", self.name_input)
        basic_layout.addRow("📞 رقم الجوال *:", self.phone_input)
        basic_layout.addRow("📧 البريد الإلكتروني:", self.email_input)
        basic_layout.addRow("📅 تاريخ الميلاد:", self.date_of_birth)
        basic_layout.addRow("⚧ الجنس:", self.gender_combo)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # المعلومات الإضافية
        additional_group = QGroupBox("معلومات إضافية")
        additional_layout = QFormLayout(additional_group)
        
        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(60)
        self.address_input.setPlaceholderText("عنوان السكن")
        
        self.emergency_contact = QLineEdit()
        self.emergency_contact.setPlaceholderText("رقم هاتف للطوارئ")
        
        self.insurance_info = QLineEdit()
        self.insurance_info.setPlaceholderText("معلومات التأمين الصحي")
        
        self.medical_history = QTextEdit()
        self.medical_history.setMaximumHeight(80)
        self.medical_history.setPlaceholderText("التاريخ المرضي والأدوية...")
        
        self.whatsapp_consent = QCheckBox("موافقة على التواصل عبر الواتساب")
        
        additional_layout.addRow("🏠 العنوان:", self.address_input)
        additional_layout.addRow("📞 جهة اتصال للطوارئ:", self.emergency_contact)
        additional_layout.addRow("🏥 معلومات التأمين:", self.insurance_info)
        additional_layout.addRow("📝 التاريخ المرضي:", self.medical_history)
        additional_layout.addRow("", self.whatsapp_consent)
        
        additional_group.setLayout(additional_layout)
        layout.addWidget(additional_group)
        
        # أزرار الحفظ والإلغاء
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("💾 حفظ")
        self.save_button.clicked.connect(self.save_patient)
        self.save_button.setDefault(True)
        
        self.cancel_button = QPushButton("❌ إلغاء")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # إذا كان في وضع التعديل، تعبئة البيانات
        if self.is_edit_mode and self.validate_patient_data():
            self.fill_data()
    
    def fill_data(self):
        """تعبئة البيانات الحالية للمريض"""
        if self.patient_data and self.validate_patient_data():
            self.name_input.setText(self.patient_data.get('name', ''))
            self.phone_input.setText(self.patient_data.get('phone', ''))
            self.email_input.setText(self.patient_data.get('email', ''))
            
            # تاريخ الميلاد
            dob = self.patient_data.get('date_of_birth')
            if dob:
                try:
                    date = QDate.fromString(dob, 'yyyy-MM-dd')
                    if date.isValid():
                        self.date_of_birth.setDate(date)
                except:
                    pass
            
            # الجنس
            gender = self.patient_data.get('gender', '')
            if gender:
                index = self.gender_combo.findText(gender)
                if index >= 0:
                    self.gender_combo.setCurrentIndex(index)
            
            self.address_input.setPlainText(self.patient_data.get('address', ''))
            self.emergency_contact.setText(self.patient_data.get('emergency_contact', ''))
            self.insurance_info.setText(self.patient_data.get('insurance_info', ''))
            self.medical_history.setPlainText(self.patient_data.get('medical_history', ''))
            
            # موافقة الواتساب
            whatsapp_consent = self.patient_data.get('whatsapp_consent', 0)
            self.whatsapp_consent.setChecked(bool(whatsapp_consent))
    
    def validate_inputs(self):
        """التحقق من صحة البيانات"""
        # التحقق من الاسم
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "بيانات ناقصة", "الاسم الكامل مطلوب")
            self.name_input.setFocus()
            return False
        
        # التحقق من رقم الجوال
        phone = self.phone_input.text().strip()
        if not phone:
            QMessageBox.warning(self, "بيانات ناقصة", "رقم الجوال مطلوب")
            self.phone_input.setFocus()
            return False
        
        # التحقق من صحة رقم الجوال (رقم سعودي نموذجي)
        if not phone.startswith('+966') and len(phone) < 10:
            QMessageBox.warning(self, "بيانات غير صحيحة", "يرجى إدخال رقم جوال صحيح")
            self.phone_input.setFocus()
            return False
        
        return True
    
    def get_patient_data(self):
        """استخراج بيانات المريض من النموذج"""
        return {
            'name': self.name_input.text().strip(),
            'phone': self.phone_input.text().strip(),
            'email': self.email_input.text().strip() or None,
            'date_of_birth': self.date_of_birth.date().toString('yyyy-MM-dd'),
            'gender': self.gender_combo.currentText() or None,
            'address': self.address_input.toPlainText().strip() or None,
            'emergency_contact': self.emergency_contact.text().strip() or None,
            'insurance_info': self.insurance_info.text().strip() or None,
            'medical_history': self.medical_history.toPlainText().strip() or None,
            'whatsapp_consent': 1 if self.whatsapp_consent.isChecked() else 0
        }
    
    def save_patient(self):
        """حفظ بيانات المريض"""
        if not self.validate_inputs():
            return
        
        patient_data = self.get_patient_data()
        
        try:
            if self.is_edit_mode:
                # في وضع التعديل - مع التحقق الإضافي
                if not self.patient_data or 'id' not in self.patient_data:
                    logging.error("بيانات المريض غير كافية للتعديل")
                    QMessageBox.critical(self, "خطأ", "بيانات المريض غير صالحة للتعديل")
                    return
                
                patient_id = self.patient_data['id']
                success = self.db_manager.update_patient(patient_id, patient_data)
                if success:
                    QMessageBox.information(self, "نجاح", "تم تحديث بيانات المريض بنجاح")
                    self.accept()
                else:
                    QMessageBox.critical(self, "خطأ", "فشل في تحديث بيانات المريض")
            else:
                # في وضع الإضافة
                patient_id = self.db_manager.add_patient(patient_data)
                if patient_id:
                    QMessageBox.information(self, "نجاح", f"تم إضافة المريض بنجاح")
                    self.accept()
                else:
                    QMessageBox.critical(self, "خطأ", "فشل في إضافة المريض")
                    
        except Exception as e:
            logging.error(f"خطأ في حفظ بيانات المريض: {e}")
            QMessageBox.critical(self, "خطأ", f"حدث خطأ غير متوقع: {str(e)}")