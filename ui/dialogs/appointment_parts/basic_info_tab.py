# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QTextEdit, QComboBox, QDateEdit, 
                             QTimeEdit, QPushButton, QLabel, QGroupBox, QFrame, QGridLayout, QCheckBox)
from PyQt5.QtCore import Qt, QDate, QTime, pyqtSignal
from PyQt5.QtGui import QFont
import logging

from ui.dialogs.widgets.smart_search import SmartSearchComboBox

class BasicInfoTab(QWidget):
    """تبويب المعلومات الأساسية - منفصل ومتكامل"""
    
    # إشارات للتكامل
    patient_selected = pyqtSignal(object)
    clinic_changed = pyqtSignal()
    department_changed = pyqtSignal()
    doctor_changed = pyqtSignal()  # ⭐ جديد
    date_changed = pyqtSignal()    # ⭐ جديد
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.selected_patient = None
        
        self.setup_ui()
        self.load_initial_data()
        self.connect_signals()  # ⭐ جديد
        
    def setup_ui(self):
        """إعداد واجهة التبويب الأساسي"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # مجموعة معلومات المريض
        self.setup_patient_section(layout)
        
        # مجموعة معلومات الموعد
        self.setup_appointment_section(layout)
        
    def connect_signals(self):
        """ربط الإشارات الداخلية"""  # ⭐ جديد
        self.doctor_combo.currentIndexChanged.connect(self.on_doctor_changed)
        self.appointment_date.dateChanged.connect(self.on_date_changed)
        
    def setup_patient_section(self, parent_layout):
        """إعداد قسم معلومات المريض"""
        patient_group = QGroupBox("👤 معلومات المريض")
        patient_group.setStyleSheet(self.get_group_style())
        patient_layout = QFormLayout(patient_group)
        patient_layout.setLabelAlignment(Qt.AlignRight)
        patient_layout.setSpacing(8)
        
        # البحث الذكي عن المريض
        self.patient_search = SmartSearchComboBox()
        self.patient_search.selection_changed.connect(self.on_patient_selected)
        self.patient_search.setMinimumHeight(35)
        patient_layout.addRow("🔍 البحث عن المريض *:", self.patient_search)
        
        # معلومات المريض المحدد
        self.patient_info_frame = QFrame()
        self.patient_info_frame.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border: 1px dashed #BDC3C7;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        patient_info_layout = QGridLayout(self.patient_info_frame)
        
        self.patient_name_label = QLabel("الاسم: --")
        self.patient_phone_label = QLabel("الهاتف: --")
        self.patient_gender_label = QLabel("الجنس: --")
        self.patient_age_label = QLabel("العمر: --")
        
        for label in [self.patient_name_label, self.patient_phone_label, 
                     self.patient_gender_label, self.patient_age_label]:
            label.setStyleSheet("font-size: 12px; color: #2C3E50; padding: 3px;")
        
        patient_info_layout.addWidget(self.patient_name_label, 0, 0)
        patient_info_layout.addWidget(self.patient_phone_label, 0, 1)
        patient_info_layout.addWidget(self.patient_gender_label, 1, 0)
        patient_info_layout.addWidget(self.patient_age_label, 1, 1)
        
        patient_layout.addRow("معلومات المريض:", self.patient_info_frame)
        self.patient_info_frame.hide()
        
        parent_layout.addWidget(patient_group)
        
    def setup_appointment_section(self, parent_layout):
        """إعداد قسم معلومات الموعد"""
        appointment_group = QGroupBox("📅 معلومات الموعد")
        appointment_group.setStyleSheet(self.get_group_style())
        appointment_layout = QFormLayout(appointment_group)
        appointment_layout.setLabelAlignment(Qt.AlignRight)
        appointment_layout.setSpacing(8)
        
        # العيادة
        self.clinic_combo = QComboBox()
        self.setup_combo_style(self.clinic_combo)
        
        # القسم
        self.department_combo = QComboBox()
        self.setup_combo_style(self.department_combo)
        
        # الطبيب
        self.doctor_combo = QComboBox()
        self.setup_combo_style(self.doctor_combo)
        
        # التاريخ والوقت
        date_time_layout = QHBoxLayout()
        
        self.appointment_date = QDateEdit()
        self.appointment_date.setDate(QDate.currentDate())
        self.appointment_date.setCalendarPopup(True)
        self.appointment_date.setMinimumDate(QDate.currentDate())
        self.appointment_date.setDisplayFormat("dd/MM/yyyy")
        self.setup_date_style(self.appointment_date)
        
        self.appointment_time = QTimeEdit()
        self.appointment_time.setTime(QTime.currentTime())
        self.appointment_time.setDisplayFormat("hh:mm AP")
        self.setup_time_style(self.appointment_time)
        
        date_time_layout.addWidget(self.appointment_date)
        date_time_layout.addWidget(QLabel(" - "))
        date_time_layout.addWidget(self.appointment_time)
        
        # نوع الموعد
        self.type_combo = QComboBox()
        self.type_combo.addItems(["🩺 كشف", "📋 روتيني", "🚨 مستعجل", "🔄 متابعة", "💬 استشارة"])
        self.setup_combo_style(self.type_combo)
        
        # حالة الموعد
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "🟡 مجدول", "🟢 مؤكد", "🔵 حاضر", "🟣 منتهي", 
            "🔴 ملغي", "🟠 مؤجل"
        ])
        self.setup_combo_style(self.status_combo)
        
        # الملاحظات
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("📝 اكتب ملاحظات إضافية...")
        self.notes_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
            }
        """)
        
        # إضافة الحقول
        appointment_layout.addRow("🏥 العيادة *:", self.clinic_combo)
        appointment_layout.addRow("📋 القسم *:", self.department_combo)
        appointment_layout.addRow("👨‍⚕️ الطبيب *:", self.doctor_combo)
        appointment_layout.addRow("📅 التاريخ والوقت *:", date_time_layout)
        appointment_layout.addRow("🎯 نوع الموعد:", self.type_combo)
        appointment_layout.addRow("📊 حالة الموعد:", self.status_combo)
        appointment_layout.addRow("💭 ملاحظات:", self.notes_input)
        
        parent_layout.addWidget(appointment_group)
        
        # ربط الأحداث
        self.clinic_combo.currentIndexChanged.connect(self.on_clinic_changed)
        self.department_combo.currentIndexChanged.connect(self.on_department_changed)
        
    def load_initial_data(self):
        """تحميل البيانات الأولية"""
        try:
            # تحميل المرضى
            patients = self.db_manager.get_patients()
            if patients:
                self.patient_search.set_items(patients)
            
            # تحميل العيادات
            clinics = self.db_manager.get_clinics()
            self.clinic_combo.clear()
            self.clinic_combo.addItem("-- اختر العيادة --", None)
            for clinic in clinics:
                display_text = f"{clinic['name']} ({clinic['type']})"
                self.clinic_combo.addItem(display_text, clinic['id'])
                
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل البيانات: {e}")
    
    def on_patient_selected(self, patient_data):
        """عند اختيار مريض"""
        try:
            if patient_data and 'id' in patient_data:
                self.selected_patient = patient_data
                
                # تحديث معلومات المريض
                self.patient_info_frame.show()
                self.patient_name_label.setText(f"الاسم: {patient_data.get('name', '--')}")
                self.patient_phone_label.setText(f"الهاتف: {patient_data.get('phone', '--')}")
                self.patient_gender_label.setText(f"الجنس: {patient_data.get('gender', '--')}")
                
                # إرسال إشارة
                self.patient_selected.emit(patient_data)
                
        except Exception as e:
            logging.error(f"❌ خطأ في اختيار المريض: {e}")
    
    def on_clinic_changed(self):
        """عند تغيير العيادة"""
        try:
            clinic_id = self.clinic_combo.currentData()
            self.department_combo.clear()
            self.doctor_combo.clear()
            
            if clinic_id:
                departments = self.db_manager.get_departments(clinic_id=clinic_id)
                self.department_combo.addItem("-- اختر القسم --", None)
                for dept in departments:
                    self.department_combo.addItem(dept['name'], dept['id'])
                    
            self.clinic_changed.emit()
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل الأقسام: {e}")
    
    def on_department_changed(self):
        """عند تغيير القسم"""
        try:
            department_id = self.department_combo.currentData()
            self.doctor_combo.clear()
            
            if department_id:
                doctors = self.db_manager.get_doctors(department_id=department_id)
                self.doctor_combo.addItem("-- اختر الطبيب --", None)
                for doctor in doctors:
                    self.doctor_combo.addItem(doctor['name'], doctor['id'])
                    
            self.department_changed.emit()
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل الأطباء: {e}")
    
    def on_doctor_changed(self):  # ⭐ جديد
        """عند تغيير الطبيب"""
        self.doctor_changed.emit()
    
    def on_date_changed(self):  # ⭐ جديد
        """عند تغيير التاريخ"""
        self.date_changed.emit()
    
    def get_form_data(self):
        """الحصول على بيانات النموذج"""
        return {
            'patient': self.selected_patient,
            'clinic_id': self.clinic_combo.currentData(),
            'department_id': self.department_combo.currentData(),
            'doctor_id': self.doctor_combo.currentData(),
            'date': self.appointment_date.date().toString('yyyy-MM-dd'),
            'time': self.appointment_time.time().toString('hh:mm'),
            'type': self.type_combo.currentText(),
            'status': self.status_combo.currentText(),
            'notes': self.notes_input.toPlainText()
        }
    
    def set_form_data(self, appointment_data):
        """تعبئة البيانات في النموذج"""
        try:
            # تعبئة بيانات المريض
            patient_id = appointment_data.get('patient_id')
            if patient_id:
                patient_data = self.db_manager.get_patient_by_id(patient_id)
                if patient_data:
                    self.selected_patient = patient_data
                    self.patient_search.set_selected_patient(patient_data)
            
            # تعبئة باقي البيانات
            clinic_id = appointment_data.get('clinic_id')
            if clinic_id:
                index = self.clinic_combo.findData(clinic_id)
                if index >= 0:
                    self.clinic_combo.setCurrentIndex(index)
                    
        except Exception as e:
            logging.error(f"❌ خطأ في تعبئة البيانات: {e}")
    
    def setup_combo_style(self, combo):
        """إعداد نمط ComboBox"""
        combo.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                font-size: 13px;
                min-height: 20px;
            }
        """)
    
    def setup_date_style(self, date_edit):
        """إعداد نمط DateEdit"""
        date_edit.setStyleSheet("""
            QDateEdit {
                padding: 6px;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                font-size: 13px;
                min-height: 20px;
            }
        """)
    
    def setup_time_style(self, time_edit):
        """إعداد نمط TimeEdit"""
        time_edit.setStyleSheet("""
            QTimeEdit {
                padding: 6px;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                font-size: 13px;
                min-height: 20px;
            }
        """)
    
    def get_group_style(self):
        """نمط المجموعات"""
        return """
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                color: #2C3E50;
                border: 1px solid #BDC3C7;
                border-radius: 6px;
                margin-top: 5px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #3498DB;
                color: white;
                border-radius: 3px;
            }
        """