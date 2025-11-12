# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QTextEdit, QComboBox, QPushButton, 
                             QMessageBox, QLabel, QGroupBox, QDoubleSpinBox,
                             QCheckBox, QFrame, QSpinBox, QTimeEdit, 
                             QWidget, QProgressDialog, QTabWidget, QTableWidget,
                             QTableWidgetItem, QHeaderView, QScrollArea)
from PyQt5.QtCore import Qt, QTime, QTimer
from PyQt5.QtGui import QFont
import logging
import json
from datetime import datetime

class DoctorDialog(QDialog):
    def __init__(self, db_manager, parent=None, doctor_data=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.doctor_data = doctor_data
        self.is_edit_mode = doctor_data is not None
        self.work_periods_data = []
        
        self.setup_ui()
        self.setWindowTitle("تعديل بيانات الطبيب" if self.is_edit_mode else "إضافة طبيب جديد")
        self.setMinimumWidth(1000)
        self.setModal(True)
        
    def setup_ui(self):
        """إعداد واجهة الحوار المتكاملة مع إعدادات واقعية"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # العنوان الرئيسي
        title = QLabel("تعديل بيانات الطبيب" if self.is_edit_mode else "إضافة طبيب جديد")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(16)
        title.setFont(title_font)
        title.setStyleSheet("""
            QLabel {
                color: #2C3E50; 
                padding: 15px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498DB, stop:1 #2980B9);
                color: white;
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }
        """)
        layout.addWidget(title)
        
        # نظام التبويبات
        self.tabs = QTabWidget()
        
        # تبويب المعلومات الأساسية
        basic_tab = self.create_basic_info_tab()
        self.tabs.addTab(basic_tab, "👤 المعلومات الأساسية")
        
        # تبويب إعدادات الجدولة المتقدمة
        scheduling_tab = self.create_advanced_scheduling_tab()
        self.tabs.addTab(scheduling_tab, "📅 إعدادات الجدولة المتقدمة")
        
        # تبويب الجداول الدورية
        periodic_tab = self.create_periodic_scheduling_tab()
        self.tabs.addTab(periodic_tab, "🔄 الجداول الدورية")
        
        layout.addWidget(self.tabs)
        
        # أزرار الحفظ والإلغاء
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("💾 حفظ البيانات والجدول")
        self.save_button.clicked.connect(self.save_doctor)
        self.save_button.setDefault(True)
        self.save_button.setStyleSheet(self.get_button_style("success", large=True))
        
        self.cancel_button = QPushButton("❌ إلغاء")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet(self.get_button_style("danger", large=True))
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # تحميل البيانات
        self.load_data()
        
        # إذا كان في وضع التعديل، تعبئة البيانات
        if self.is_edit_mode:
            self.fill_data()

    def create_basic_info_tab(self):
        """إنشاء تبويب المعلومات الأساسية"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # مجموعة المعلومات الشخصية
        personal_group = QGroupBox("المعلومات الشخصية")
        personal_group.setStyleSheet(self.get_group_style())
        personal_layout = QFormLayout(personal_group)
        personal_layout.setLabelAlignment(Qt.AlignRight)
        personal_layout.setVerticalSpacing(12)
        personal_layout.setHorizontalSpacing(15)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("الاسم الكامل للطبيب")
        self.name_input.setStyleSheet(self.get_input_style())
        
        self.specialty_input = QLineEdit()
        self.specialty_input.setPlaceholderText("التخصص الطبي")
        self.specialty_input.setStyleSheet(self.get_input_style())
        
        personal_layout.addRow("اسم الطبيب *:", self.name_input)
        personal_layout.addRow("التخصص *:", self.specialty_input)
        
        # مجموعة معلومات الاتصال
        contact_group = QGroupBox("معلومات الاتصال")
        contact_group.setStyleSheet(self.get_group_style())
        contact_layout = QFormLayout(contact_group)
        contact_layout.setLabelAlignment(Qt.AlignRight)
        contact_layout.setVerticalSpacing(12)
        contact_layout.setHorizontalSpacing(15)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("رقم الجوال")
        self.phone_input.setStyleSheet(self.get_input_style())
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("البريد الإلكتروني")
        self.email_input.setStyleSheet(self.get_input_style())
        
        self.clinic_combo = QComboBox()
        self.clinic_combo.setStyleSheet(self.get_combo_style())
        self.clinic_combo.currentIndexChanged.connect(self.on_clinic_changed)
        
        self.department_combo = QComboBox()
        self.department_combo.setStyleSheet(self.get_combo_style())
        
        contact_layout.addRow("رقم الجوال:", self.phone_input)
        contact_layout.addRow("البريد الإلكتروني:", self.email_input)
        contact_layout.addRow("العيادة *:", self.clinic_combo)
        contact_layout.addRow("القسم *:", self.department_combo)
        
        # مجموعة المعلومات المهنية
        professional_group = QGroupBox("المعلومات المهنية")
        professional_group.setStyleSheet(self.get_group_style())
        professional_layout = QFormLayout(professional_group)
        professional_layout.setLabelAlignment(Qt.AlignRight)
        professional_layout.setVerticalSpacing(12)
        professional_layout.setHorizontalSpacing(15)
        
        self.national_id_input = QLineEdit()
        self.national_id_input.setPlaceholderText("الرقم الوطني")
        self.national_id_input.setStyleSheet(self.get_input_style())
        
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("رقم الترخيص الطبي")
        self.license_input.setStyleSheet(self.get_input_style())
        
        self.fee_spinbox = QDoubleSpinBox()
        self.fee_spinbox.setRange(0, 10000)
        self.fee_spinbox.setValue(100)
        self.fee_spinbox.setSuffix(" ريال")
        self.fee_spinbox.setStyleSheet(self.get_input_style())
        
        self.active_checkbox = QCheckBox("طبيب نشط")
        self.active_checkbox.setChecked(True)
        self.active_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
                color: #27ae60;
                padding: 8px;
            }
        """)
        
        professional_layout.addRow("الرقم الوطني:", self.national_id_input)
        professional_layout.addRow("رقم الترخيص:", self.license_input)
        professional_layout.addRow("رسوم الكشف:", self.fee_spinbox)
        professional_layout.addRow("الحالة:", self.active_checkbox)
        
        # الملاحظات
        notes_group = QGroupBox("📝 ملاحظات إضافية")
        notes_group.setStyleSheet(self.get_group_style())
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("ملاحظات إضافية حول الطبيب أو الجدول...")
        self.notes_input.setStyleSheet("""
            QTextEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 13px;
            }
            QTextEdit:focus {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
        """)
        notes_layout.addWidget(self.notes_input)
        
        layout.addWidget(personal_group)
        layout.addWidget(contact_group)
        layout.addWidget(professional_group)
        layout.addWidget(notes_group)
        layout.addStretch()
        
        return widget

    def create_advanced_scheduling_tab(self):
        """إنشاء تبويب إعدادات الجدولة المتقدمة"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # إعدادات الموعد الأساسية
        basic_settings_group = QGroupBox("⚙️ إعدادات الموعد الأساسية")
        basic_settings_group.setStyleSheet(self.get_group_style())
        basic_layout = QFormLayout(basic_settings_group)
        basic_layout.setLabelAlignment(Qt.AlignRight)
        basic_layout.setVerticalSpacing(12)
        basic_layout.setHorizontalSpacing(15)
        
        self.appointment_duration_spin = QSpinBox()
        self.appointment_duration_spin.setRange(10, 120)
        self.appointment_duration_spin.setValue(30)
        self.appointment_duration_spin.setSuffix(" دقيقة")
        self.appointment_duration_spin.setStyleSheet(self.get_input_style())
        
        self.buffer_time_spin = QSpinBox()
        self.buffer_time_spin.setRange(0, 30)
        self.buffer_time_spin.setValue(5)
        self.buffer_time_spin.setSuffix(" دقيقة")
        self.buffer_time_spin.setToolTip("الوقت بين المواعيد للتنظيف والاستعداد")
        self.buffer_time_spin.setStyleSheet(self.get_input_style())
        
        self.max_daily_spin = QSpinBox()
        self.max_daily_spin.setRange(1, 100)
        self.max_daily_spin.setValue(20)
        self.max_daily_spin.setSuffix(" مريض")
        self.max_daily_spin.setStyleSheet(self.get_input_style())
        
        basic_layout.addRow("مدة الموعد الافتراضية:", self.appointment_duration_spin)
        basic_layout.addRow("وقت الاستراحة بين المواعيد:", self.buffer_time_spin)
        basic_layout.addRow("أقصى عدد مرضى يومياً:", self.max_daily_spin)
        
        # أيام العمل
        work_days_group = QGroupBox("📅 أيام العمل")
        work_days_group.setStyleSheet(self.get_group_style())
        work_days_layout = QVBoxLayout(work_days_group)
        
        self.work_days_layout = QHBoxLayout()
        self.work_days_checkboxes = {}
        
        days = [
            ("sunday", "الأحد"),
            ("monday", "الإثنين"), 
            ("tuesday", "الثلاثاء"),
            ("wednesday", "الأربعاء"),
            ("thursday", "الخميس"),
            ("friday", "الجمعة"),
            ("saturday", "السبت")
        ]
        
        for day_key, day_name in days:
            checkbox = QCheckBox(day_name)
            checkbox.setChecked(day_key in ["sunday", "monday", "tuesday", "wednesday", "thursday"])
            self.work_days_checkboxes[day_key] = checkbox
            self.work_days_layout.addWidget(checkbox)
        
        work_days_widget = QWidget()
        work_days_widget.setLayout(self.work_days_layout)
        work_days_layout.addWidget(work_days_widget)
        
        # فترات العمل المتعددة
        work_periods_group = QGroupBox("⏰ فترات العمل المتعددة (مثال: دوام صباحي ومسائي)")
        work_periods_group.setStyleSheet(self.get_group_style())
        work_periods_layout = QVBoxLayout(work_periods_group)
        
        # جدول فترات العمل
        self.work_periods_table = QTableWidget()
        self.work_periods_table.setColumnCount(5)
        self.work_periods_table.setHorizontalHeaderLabels([
            "نوع الفترة", "وقت البدء", "وقت الانتهاء", "مفعل", "الإجراءات"
        ])
        self.work_periods_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # أزرار إدارة فترات العمل
        periods_buttons_layout = QHBoxLayout()
        
        add_main_period_btn = QPushButton("➕ فترة دوام رئيسية")
        add_main_period_btn.clicked.connect(lambda: self.add_work_period("main"))
        add_main_period_btn.setStyleSheet(self.get_button_style("primary"))
        
        add_evening_btn = QPushButton("🌙 فترة مسائية")
        add_evening_btn.clicked.connect(lambda: self.add_work_period("evening"))
        add_evening_btn.setStyleSheet(self.get_button_style("info"))
        
        add_custom_btn = QPushButton("⚙️ فترة مخصصة")
        add_custom_btn.clicked.connect(lambda: self.add_work_period("custom"))
        add_custom_btn.setStyleSheet(self.get_button_style("primary"))
        
        periods_buttons_layout.addWidget(add_main_period_btn)
        periods_buttons_layout.addWidget(add_evening_btn)
        periods_buttons_layout.addWidget(add_custom_btn)
        periods_buttons_layout.addStretch()
        
        work_periods_layout.addWidget(self.work_periods_table)
        work_periods_layout.addLayout(periods_buttons_layout)
        
        # أوقات الراحة
        breaks_group = QGroupBox("☕ أوقات الراحة والإجازات")
        breaks_group.setStyleSheet(self.get_group_style())
        breaks_layout = QVBoxLayout(breaks_group)
        
        self.breaks_table = QTableWidget()
        self.breaks_table.setColumnCount(4)
        self.breaks_table.setHorizontalHeaderLabels([
            "بداية الراحة", "نهاية الراحة", "السبب", "الإجراءات"
        ])
        self.breaks_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        breaks_buttons_layout = QHBoxLayout()
        add_break_btn = QPushButton("➕ إضافة وقت راحة")
        add_break_btn.clicked.connect(self.add_break_time)
        add_break_btn.setStyleSheet(self.get_button_style("primary"))
        
        breaks_buttons_layout.addWidget(add_break_btn)
        breaks_buttons_layout.addStretch()
        
        breaks_layout.addWidget(self.breaks_table)
        breaks_layout.addLayout(breaks_buttons_layout)
        
        layout.addWidget(basic_settings_group)
        layout.addWidget(work_days_group)
        layout.addWidget(work_periods_group)
        layout.addWidget(breaks_group)
        
        return widget

    def create_periodic_scheduling_tab(self):
        """إنشاء تبويب الجداول الدورية مع زر التحقق"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # إعدادات الجدولة الدورية
        periodic_group = QGroupBox("🔄 إعدادات الجداول الدورية (نظام مشابه لشركات الطيران)")
        periodic_group.setStyleSheet(self.get_group_style())
        periodic_layout = QFormLayout(periodic_group)
        periodic_layout.setLabelAlignment(Qt.AlignRight)
        periodic_layout.setVerticalSpacing(12)
        periodic_layout.setHorizontalSpacing(15)
        
        self.schedule_period_spin = QSpinBox()
        self.schedule_period_spin.setRange(7, 365)
        self.schedule_period_spin.setValue(30)
        self.schedule_period_spin.setSuffix(" يوم")
        self.schedule_period_spin.setStyleSheet(self.get_input_style())
        self.schedule_period_spin.setToolTip("مدة الجدول المسبق المنشأ (مثال: 30 يوم مثل شركات الطيران)")
        
        self.auto_renew_checkbox = QCheckBox("التجديد التلقائي للجداول")
        self.auto_renew_checkbox.setChecked(True)
        self.auto_renew_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
                color: #27ae60;
                padding: 8px;
            }
        """)
        self.auto_renew_checkbox.setToolTip("تجديد الجدول تلقائياً قبل انتهاء مدته")
        
        self.renewal_advance_spin = QSpinBox()
        self.renewal_advance_spin.setRange(1, 30)
        self.renewal_advance_spin.setValue(7)
        self.renewal_advance_spin.setSuffix(" يوم")
        self.renewal_advance_spin.setStyleSheet(self.get_input_style())
        self.renewal_advance_spin.setToolTip("عدد الأيام للإشعار قبل انتهاء الجدول الحالي")
        
        periodic_layout.addRow("مدة الجدول المسبق:", self.schedule_period_spin)
        periodic_layout.addRow("التجديد التلقائي:", self.auto_renew_checkbox)
        periodic_layout.addRow("التنبيه قبل التجديد:", self.renewal_advance_spin)
        
        # أزرار التحكم
        control_buttons_layout = QHBoxLayout()
        
        self.create_schedule_btn = QPushButton("📊 إنشاء الجدول الدوري")
        self.create_schedule_btn.clicked.connect(self.create_periodic_schedule)
        self.create_schedule_btn.setStyleSheet(self.get_button_style("primary"))
        self.create_schedule_btn.setToolTip("إنشاء جدول دوري كامل لمدة محددة")
        
        self.view_schedule_btn = QPushButton("👁️ عرض الجدول الحالي")
        self.view_schedule_btn.clicked.connect(self.view_current_periodic_schedule)
        self.view_schedule_btn.setStyleSheet(self.get_button_style("info"))
        
        self.quick_setup_btn = QPushButton("⚡ إعداد سريع")
        self.quick_setup_btn.clicked.connect(self.quick_setup_schedule)
        self.quick_setup_btn.setStyleSheet(self.get_button_style("success"))
        self.quick_setup_btn.setToolTip("إعداد سريع للجدول الدوري بالإعدادات الافتراضية")
        
        control_buttons_layout.addWidget(self.create_schedule_btn)
        control_buttons_layout.addWidget(self.view_schedule_btn)
        control_buttons_layout.addWidget(self.quick_setup_btn)
        control_buttons_layout.addStretch()
        
        periodic_layout.addRow("الإجراءات:", control_buttons_layout)
        
        # إضافة زر التحقق
        verify_layout = QHBoxLayout()
        
        self.verify_schedule_btn = QPushButton("🔍 التحقق من إنشاء الجدول")
        self.verify_schedule_btn.clicked.connect(self.verify_schedule_creation)
        self.verify_schedule_btn.setStyleSheet(self.get_button_style("info"))
        
        verify_layout.addWidget(self.verify_schedule_btn)
        verify_layout.addStretch()
        
        periodic_layout.addRow("التحقق:", verify_layout)
        
        # معلومات الجدول الحالي
        self.current_schedule_info = QLabel("لم يتم إنشاء جدول دوري بعد")
        self.current_schedule_info.setStyleSheet("""
            QLabel {
                padding: 15px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                color: #6c757d;
            }
        """)
        
        layout.addWidget(periodic_group)
        layout.addWidget(self.current_schedule_info)
        layout.addStretch()
        
        return widget

    def add_work_period(self, period_type):
        """إضافة فترة عمل جديدة"""
        try:
            row = self.work_periods_table.rowCount()
            self.work_periods_table.insertRow(row)
            
            # نوع الفترة
            type_combo = QComboBox()
            type_combo.addItems(["دوام رئيسي", "دوام مسائي", "نصف دوام", "فترة مخصصة"])
            type_combo.setCurrentText({
                "main": "دوام رئيسي",
                "evening": "دوام مسائي", 
                "custom": "فترة مخصصة"
            }.get(period_type, "فترة مخصصة"))
            type_combo.setStyleSheet(self.get_combo_style())
            
            # وقت البدء
            start_time = QTimeEdit()
            if period_type == "main":
                start_time.setTime(QTime(8, 0))
            elif period_type == "evening":
                start_time.setTime(QTime(16, 0))
            else:
                start_time.setTime(QTime(9, 0))
            start_time.setDisplayFormat("hh:mm")
            start_time.setStyleSheet(self.get_input_style())
            
            # وقت الانتهاء
            end_time = QTimeEdit()
            if period_type == "main":
                end_time.setTime(QTime(14, 0))
            elif period_type == "evening":
                end_time.setTime(QTime(20, 0))
            else:
                end_time.setTime(QTime(17, 0))
            end_time.setDisplayFormat("hh:mm")
            end_time.setStyleSheet(self.get_input_style())
            
            # مفعل
            active_checkbox = QCheckBox()
            active_checkbox.setChecked(True)
            
            # زر الحذف
            delete_btn = QPushButton("🗑️")
            delete_btn.clicked.connect(lambda: self.delete_work_period(row))
            delete_btn.setStyleSheet(self.get_button_style("danger"))
            
            self.work_periods_table.setCellWidget(row, 0, type_combo)
            self.work_periods_table.setCellWidget(row, 1, start_time)
            self.work_periods_table.setCellWidget(row, 2, end_time)
            self.work_periods_table.setCellWidget(row, 3, active_checkbox)
            self.work_periods_table.setCellWidget(row, 4, delete_btn)
            
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة فترة عمل: {e}")
            QMessageBox.critical(self, "خطأ", f"❌ حدث خطأ أثناء إضافة فترة العمل:\n{str(e)}")

    def add_break_time(self):
        """إضافة وقت راحة"""
        try:
            row = self.breaks_table.rowCount()
            self.breaks_table.insertRow(row)
            
            # وقت البدء
            start_time = QTimeEdit()
            start_time.setTime(QTime(12, 0))
            start_time.setDisplayFormat("hh:mm")
            start_time.setStyleSheet(self.get_input_style())
            
            # وقت الانتهاء  
            end_time = QTimeEdit()
            end_time.setTime(QTime(13, 0))
            end_time.setDisplayFormat("hh:mm")
            end_time.setStyleSheet(self.get_input_style())
            
            # السبب
            reason_input = QLineEdit()
            reason_input.setText("استراحة غداء")
            reason_input.setStyleSheet(self.get_input_style())
            
            # زر الحذف
            delete_btn = QPushButton("🗑️")
            delete_btn.clicked.connect(lambda: self.delete_break_time(row))
            delete_btn.setStyleSheet(self.get_button_style("danger"))
            
            self.breaks_table.setCellWidget(row, 0, start_time)
            self.breaks_table.setCellWidget(row, 1, end_time)
            self.breaks_table.setCellWidget(row, 2, reason_input)
            self.breaks_table.setCellWidget(row, 3, delete_btn)
            
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة وقت راحة: {e}")
            QMessageBox.critical(self, "خطأ", f"❌ حدث خطأ أثناء إضافة وقت الراحة:\n{str(e)}")

    def delete_work_period(self, row):
        """حذف فترة عمل"""
        try:
            self.work_periods_table.removeRow(row)
        except Exception as e:
            logging.error(f"❌ خطأ في حذف فترة العمل: {e}")

    def delete_break_time(self, row):
        """حذف وقت راحة"""
        try:
            self.breaks_table.removeRow(row)
        except Exception as e:
            logging.error(f"❌ خطأ في حذف وقت الراحة: {e}")

    def get_work_periods_data(self):
        """استخراج بيانات فترات العمل من الجدول"""
        periods = []
        for row in range(self.work_periods_table.rowCount()):
            type_combo = self.work_periods_table.cellWidget(row, 0)
            start_time = self.work_periods_table.cellWidget(row, 1)
            end_time = self.work_periods_table.cellWidget(row, 2)
            active_checkbox = self.work_periods_table.cellWidget(row, 3)
            
            if all([type_combo, start_time, end_time, active_checkbox]):
                period_type_map = {
                    "دوام رئيسي": "main",
                    "دوام مسائي": "evening", 
                    "نصف دوام": "part_time",
                    "فترة مخصصة": "custom"
                }
                
                periods.append({
                    'type': period_type_map.get(type_combo.currentText(), 'custom'),
                    'start': start_time.time().toString('hh:mm'),
                    'end': end_time.time().toString('hh:mm'),
                    'is_active': active_checkbox.isChecked()
                })
        
        return periods

    def get_breaks_data(self):
        """استخراج بيانات أوقات الراحة من الجدول"""
        breaks = []
        for row in range(self.breaks_table.rowCount()):
            start_time = self.breaks_table.cellWidget(row, 0)
            end_time = self.breaks_table.cellWidget(row, 1)
            reason_input = self.breaks_table.cellWidget(row, 2)
            
            if all([start_time, end_time, reason_input]):
                breaks.append({
                    'start': start_time.time().toString('hh:mm'),
                    'end': end_time.time().toString('hh:mm'),
                    'reason': reason_input.text()
                })
        
        return breaks

    def load_data(self):
        """تحميل قوائم البيانات"""
        try:
            # تحميل العيادات
            clinics = self.db_manager.get_clinics()
            self.clinic_combo.clear()
            self.clinic_combo.addItem("-- اختر العيادة --", None)
            for clinic in clinics:
                self.clinic_combo.addItem(f"{clinic['name']} ({clinic['type']})", clinic['id'])
            
            # تحميل الأقسام للعيادة الافتراضية
            self.on_clinic_changed()
            
        except Exception as e:
            logging.error(f"خطأ في تحميل البيانات: {e}")
            QMessageBox.warning(self, "تحذير", f"خطأ في تحميل البيانات: {e}")
    
    def on_clinic_changed(self):
        """عند تغيير العيادة"""
        try:
            clinic_id = self.clinic_combo.currentData()
            self.department_combo.clear()
            
            if clinic_id:
                # تحميل أقسام العيادة المحددة
                departments = self.db_manager.get_departments(clinic_id=clinic_id)
                self.department_combo.addItem("-- اختر القسم --", None)
                for dept in departments:
                    self.department_combo.addItem(dept['name'], dept['id'])
            else:
                self.department_combo.addItem("-- اختر القسم --", None)
                
        except Exception as e:
            logging.error(f"خطأ في تحميل الأقسام: {e}")
    
    def fill_data(self):
        """تعبئة البيانات الحالية للطبيب"""
        if self.doctor_data:
            try:
                self.name_input.setText(self.doctor_data.get('name', ''))
                self.specialty_input.setText(self.doctor_data.get('specialty', ''))
                
                # تعيين العيادة
                clinic_id = self.doctor_data.get('clinic_id')
                if clinic_id:
                    index = self.clinic_combo.findData(clinic_id)
                    if index >= 0:
                        self.clinic_combo.setCurrentIndex(index)
                
                # تعيين القسم بعد تحميل الأقسام
                QTimer.singleShot(100, lambda: self.set_department(self.doctor_data.get('department_id')))
                
                self.phone_input.setText(self.doctor_data.get('phone', ''))
                self.email_input.setText(self.doctor_data.get('email', ''))
                self.national_id_input.setText(self.doctor_data.get('national_id', ''))
                self.license_input.setText(self.doctor_data.get('license_number', ''))
                
                fee = self.doctor_data.get('consultation_fee', 100)
                self.fee_spinbox.setValue(float(fee))
                
                self.notes_input.setPlainText(self.doctor_data.get('notes', ''))
                
                # تعيين حالة التفعيل
                is_active = self.doctor_data.get('is_active', True)
                self.active_checkbox.setChecked(bool(is_active))
                
                # تحميل إعدادات الجدولة إذا كانت موجودة
                self.load_schedule_settings()
                
                # تحديث معلومات الجدول الحالي
                self.update_current_schedule_info()
                
            except Exception as e:
                logging.error(f"❌ خطأ في تعبئة البيانات: {e}")
                QMessageBox.warning(self, "تحذير", f"حدث خطأ في تحميل بيانات الطبيب: {e}")
    
    def load_schedule_settings(self):
        """تحميل إعدادات الجدولة الحالية للطبيب"""
        if not self.is_edit_mode:
            return
            
        try:
            doctor_id = self.doctor_data.get('id')
            if doctor_id:
                schedule_settings = self.db_manager.get_doctor_schedule_settings(doctor_id)
                
                if schedule_settings:
                    # تعيين مدة الموعد
                    duration = schedule_settings.get('appointment_duration', 30)
                    self.appointment_duration_spin.setValue(duration)
                    
                    # تعيين وقت الاستراحة
                    buffer_time = schedule_settings.get('buffer_time', 5)
                    self.buffer_time_spin.setValue(buffer_time)
                    
                    # تعيين الحد الأقصى للمواعيد
                    max_daily = schedule_settings.get('max_patients_per_day', 20)
                    self.max_daily_spin.setValue(max_daily)
                    
                    # تعيين أيام العمل
                    work_days = schedule_settings.get('work_days', [])
                    for day_key, checkbox in self.work_days_checkboxes.items():
                        checkbox.setChecked(day_key in work_days)
                    
                    # تعيين فترات العمل (إذا كانت موجودة)
                    work_periods = schedule_settings.get('work_periods', [])
                    if work_periods:
                        for period in work_periods:
                            self.add_work_period_from_data(period)
                    
                    # تعيين أوقات الراحة (إذا كانت موجودة)
                    break_times = schedule_settings.get('break_times', [])
                    if break_times:
                        for break_time in break_times:
                            self.add_break_time_from_data(break_time)
                        
        except Exception as e:
            logging.error(f"خطأ في تحميل إعدادات الجدولة: {e}")
    
    def add_work_period_from_data(self, period_data):
        """إضافة فترة عمل من البيانات المحفوظة"""
        try:
            row = self.work_periods_table.rowCount()
            self.work_periods_table.insertRow(row)
            
            # نوع الفترة
            type_combo = QComboBox()
            type_combo.addItems(["دوام رئيسي", "دوام مسائي", "نصف دوام", "فترة مخصصة"])
            
            period_type_map = {
                "main": "دوام رئيسي",
                "evening": "دوام مسائي",
                "part_time": "نصف دوام", 
                "custom": "فترة مخصصة"
            }
            
            type_combo.setCurrentText(period_type_map.get(period_data.get('type', 'custom'), 'فترة مخصصة'))
            type_combo.setStyleSheet(self.get_combo_style())
            
            # وقت البدء
            start_time = QTimeEdit()
            start_time_str = period_data.get('start', '08:00')
            start_time.setTime(QTime.fromString(start_time_str, 'hh:mm'))
            start_time.setDisplayFormat("hh:mm")
            start_time.setStyleSheet(self.get_input_style())
            
            # وقت الانتهاء
            end_time = QTimeEdit()
            end_time_str = period_data.get('end', '17:00')
            end_time.setTime(QTime.fromString(end_time_str, 'hh:mm'))
            end_time.setDisplayFormat("hh:mm")
            end_time.setStyleSheet(self.get_input_style())
            
            # مفعل
            active_checkbox = QCheckBox()
            active_checkbox.setChecked(period_data.get('is_active', True))
            
            # زر الحذف
            delete_btn = QPushButton("🗑️")
            delete_btn.clicked.connect(lambda: self.delete_work_period(row))
            delete_btn.setStyleSheet(self.get_button_style("danger"))
            
            self.work_periods_table.setCellWidget(row, 0, type_combo)
            self.work_periods_table.setCellWidget(row, 1, start_time)
            self.work_periods_table.setCellWidget(row, 2, end_time)
            self.work_periods_table.setCellWidget(row, 3, active_checkbox)
            self.work_periods_table.setCellWidget(row, 4, delete_btn)
            
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة فترة عمل من البيانات: {e}")

    def add_break_time_from_data(self, break_data):
        """إضافة وقت راحة من البيانات المحفوظة"""
        try:
            row = self.breaks_table.rowCount()
            self.breaks_table.insertRow(row)
            
            # وقت البدء
            start_time = QTimeEdit()
            start_time_str = break_data.get('start', '12:00')
            start_time.setTime(QTime.fromString(start_time_str, 'hh:mm'))
            start_time.setDisplayFormat("hh:mm")
            start_time.setStyleSheet(self.get_input_style())
            
            # وقت الانتهاء  
            end_time = QTimeEdit()
            end_time_str = break_data.get('end', '13:00')
            end_time.setTime(QTime.fromString(end_time_str, 'hh:mm'))
            end_time.setDisplayFormat("hh:mm")
            end_time.setStyleSheet(self.get_input_style())
            
            # السبب
            reason_input = QLineEdit()
            reason_input.setText(break_data.get('reason', 'استراحة غداء'))
            reason_input.setStyleSheet(self.get_input_style())
            
            # زر الحذف
            delete_btn = QPushButton("🗑️")
            delete_btn.clicked.connect(lambda: self.delete_break_time(row))
            delete_btn.setStyleSheet(self.get_button_style("danger"))
            
            self.breaks_table.setCellWidget(row, 0, start_time)
            self.breaks_table.setCellWidget(row, 1, end_time)
            self.breaks_table.setCellWidget(row, 2, reason_input)
            self.breaks_table.setCellWidget(row, 3, delete_btn)
            
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة وقت راحة من البيانات: {e}")
    
    def load_periodic_schedule_settings(self):
        """تحميل إعدادات الجدولة الدورية"""
        try:
            if not self.is_edit_mode:
                return

            doctor_id = self.doctor_data.get('id')
            cursor = self.db_manager.conn.cursor()
            
            cursor.execute('''
                SELECT * FROM periodic_schedule_settings WHERE doctor_id = ?
            ''', (doctor_id,))
            
            settings = cursor.fetchone()
            if settings:
                self.schedule_period_spin.setValue(settings['schedule_period_days'])
                self.auto_renew_checkbox.setChecked(bool(settings['auto_renew_enabled']))
                self.renewal_advance_spin.setValue(settings['renewal_advance_days'])

        except Exception as e:
            logging.error(f"خطأ في تحميل إعدادات الجدولة الدورية: {e}")
    
    def set_department(self, department_id):
        """تعيين القسم بعد تحميل البيانات"""
        if department_id:
            index = self.department_combo.findData(department_id)
            if index >= 0:
                self.department_combo.setCurrentIndex(index)
    
    def validate_inputs(self):
        """التحقق من صحة البيانات"""
        # التحقق من الاسم
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "بيانات ناقصة", "اسم الطبيب مطلوب")
            self.name_input.setFocus()
            return False
        
        # التحقق من التخصص
        specialty = self.specialty_input.text().strip()
        if not specialty:
            QMessageBox.warning(self, "بيانات ناقصة", "التخصص مطلوب")
            self.specialty_input.setFocus()
            return False
        
        # التحقق من العيادة
        if not self.clinic_combo.currentData():
            QMessageBox.warning(self, "بيانات ناقصة", "يرجى اختيار عيادة")
            self.clinic_combo.setFocus()
            return False
        
        # التحقق من القسم
        if not self.department_combo.currentData():
            QMessageBox.warning(self, "بيانات ناقصة", "يرجى اختيار قسم")
            self.department_combo.setFocus()
            return False
        
        # التحقق من أيام العمل (يجب اختيار يوم واحد على الأقل)
        work_days = self.get_selected_work_days()
        if not work_days:
            QMessageBox.warning(self, "بيانات ناقصة", "يرجى اختيار يوم عمل واحد على الأقل")
            return False
        
        return True
    
    def get_selected_work_days(self):
        """الحصول على أيام العمل المحددة"""
        selected_days = []
        for day_key, checkbox in self.work_days_checkboxes.items():
            if checkbox.isChecked():
                selected_days.append(day_key)
        return selected_days
    
    def get_doctor_data(self):
        """استخراج بيانات الطبيب من النموذج"""
        return {
            'name': self.name_input.text().strip(),
            'specialty': self.specialty_input.text().strip(),
            'department_id': self.department_combo.currentData(),
            'clinic_id': self.clinic_combo.currentData(),
            'phone': self.phone_input.text().strip() or None,
            'email': self.email_input.text().strip() or None,
            'national_id': self.national_id_input.text().strip() or None,
            'license_number': self.license_input.text().strip() or None,
            'consultation_fee': self.fee_spinbox.value(),
            'notes': self.notes_input.toPlainText().strip() or None,
            'is_active': self.active_checkbox.isChecked()
        }
    
    def get_schedule_data(self):
        """استخراج بيانات الجدولة من النموذج"""
        return {
            'appointment_duration': self.appointment_duration_spin.value(),
            'buffer_time': self.buffer_time_spin.value(),
            'max_daily_appointments': self.max_daily_spin.value(),
            'work_days': self.get_selected_work_days(),
            'work_periods': self.get_work_periods_data(),
            'break_times': self.get_breaks_data()
        }
    
    def get_periodic_schedule_data(self):
        """استخراج بيانات الجدولة الدورية"""
        return {
            'schedule_period_days': self.schedule_period_spin.value(),
            'auto_renew_enabled': self.auto_renew_checkbox.isChecked(),
            'renewal_advance_days': self.renewal_advance_spin.value()
        }

    def create_periodic_schedule(self):
        """إنشاء الجدول الدوري للطبيب - الإصدار المصحح"""
        try:
            if not self.is_edit_mode:
                QMessageBox.warning(self, "تحذير", "يرجى حفظ بيانات الطبيب أولاً قبل إنشاء الجدول الدوري")
                return

            doctor_id = self.doctor_data.get('id')
            period_days = self.schedule_period_spin.value()

            # التحقق من صحة إعدادات الجدولة
            if not self.validate_schedule_settings():
                return

            # عرض تقدم العمل
            progress = QProgressDialog("جاري إنشاء الجدول الدوري...", "إلغاء", 0, 100, self)
            progress.setWindowTitle("إنشاء الجدول الدوري")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()

            # محاكاة التقدم
            for i in range(101):
                progress.setValue(i)
                QApplication.processEvents()  # تحديث الواجهة - تم إصلاحه
                if progress.wasCanceled():
                    break

            # إنشاء الجدول الدوري
            success = self.db_manager.setup_doctor_periodic_schedule(doctor_id, period_days)

            progress.close()

            if success:
                # حفظ إعدادات الجدولة الدورية
                self.save_periodic_schedule_settings()
                
                QMessageBox.information(self, "نجاح", 
                                      f"✅ تم إنشاء الجدول الدوري بنجاح!\n\n"
                                      f"• المدة: {period_days} يوم\n"
                                      f"• التجديد التلقائي: {'مفعل' if self.auto_renew_checkbox.isChecked() else 'معطل'}\n"
                                      f"• التنبيه قبل: {self.renewal_advance_spin.value()} يوم\n\n"
                                      f"يمكنك الآن عرض الجدول وحجز المواعيد للمرضى.")
                
                # تحديث معلومات الجدول الحالي
                self.update_current_schedule_info()
            else:
                QMessageBox.critical(self, "خطأ", "❌ فشل في إنشاء الجدول الدوري")

        except Exception as e:
            logging.error(f"خطأ في إنشاء الجدول الدوري: {e}")
            QMessageBox.critical(self, "خطأ", f"❌ حدث خطأ أثناء إنشاء الجدول:\n{str(e)}")

    def validate_schedule_settings(self):
        """التحقق من صحة إعدادات الجدولة"""
        work_periods = self.get_work_periods_data()
        active_periods = [p for p in work_periods if p['is_active']]
        
        if not active_periods:
            QMessageBox.warning(self, "تحذير", "يرجى إضافة فترة عمل واحدة على الأقل")
            self.tabs.setCurrentIndex(1)
            return False
            
        # التحقق من تعارض أوقات العمل
        for i, period1 in enumerate(active_periods):
            for j, period2 in enumerate(active_periods):
                if i != j:
                    start1 = QTime.fromString(period1['start'], 'hh:mm')
                    end1 = QTime.fromString(period1['end'], 'hh:mm')
                    start2 = QTime.fromString(period2['start'], 'hh:mm')
                    end2 = QTime.fromString(period2['end'], 'hh:mm')
                    
                    if start1 < end2 and start2 < end1:
                        QMessageBox.warning(self, "تحذير", 
                                          f"تعارض في أوقات العمل:\n"
                                          f"الفترة {period1['type']} ({period1['start']}-{period1['end']})\n"
                                          f"تتعارض مع الفترة {period2['type']} ({period2['start']}-{period2['end']})")
                        self.tabs.setCurrentIndex(1)
                        return False
        
        return True

    def view_current_periodic_schedule(self):
        """عرض الجدول الدوري الحالي"""
        try:
            if not self.is_edit_mode:
                QMessageBox.warning(self, "تحذير", "لا يوجد جدول دوري للطبيب الجديد")
                return

            doctor_id = self.doctor_data.get('id')
            
            # الحصول على الجدول الدوري
            schedule_data = self.db_manager.get_periodic_schedule(doctor_id)

            if not schedule_data:
                QMessageBox.information(self, "معلومات", "📋 لا يوجد جدول دوري لهذا الطبيب.\n\nيرجى إنشاء جدول أولاً باستخدام زر 'إنشاء الجدول الدوري'")
                return

            # حساب الإحصائيات
            total_slots = 0
            available_slots = 0
            booked_slots = 0
            total_days = len(schedule_data)

            for date_data in schedule_data.values():
                total_slots += date_data['total_count']
                available_slots += date_data['available_count']
                booked_slots += date_data['booked_count']

            occupancy_rate = (booked_slots / total_slots * 100) if total_slots > 0 else 0

            message = f"""
📊 ملخص الجدول الدوري الحالي:

• عدد الأيام في الجدول: {total_days} يوم
• إجمالي المواعيد: {total_slots} موعد
• المواعيد المتاحة: {available_slots} موعد
• المواعيد المحجوزة: {booked_slots} موعد
• نسبة الإشغال: {occupancy_rate:.1f}%

🗓️ الجدول يشمل الفترة من:
{min(schedule_data.keys())} إلى {max(schedule_data.keys())}

💡 يمكنك عرض التفاصيل الكاملة في واجهة الجدولة الذكية.
"""

            QMessageBox.information(self, "الجدول الدوري الحالي", message.strip())

        except Exception as e:
            logging.error(f"خطأ في عرض الجدول الدوري: {e}")
            QMessageBox.critical(self, "خطأ", f"❌ حدث خطأ أثناء عرض الجدول:\n{str(e)}")

    def quick_setup_schedule(self):
        """الإعداد السريع للجدول الدوري"""
        try:
            if not self.is_edit_mode:
                QMessageBox.warning(self, "تحذير", "يرجى حفظ بيانات الطبيب أولاً")
                return

            doctor_id = self.doctor_data.get('id')
            
            # استخدام الإعدادات الافتراضية
            self.schedule_period_spin.setValue(30)
            self.auto_renew_checkbox.setChecked(True)
            self.renewal_advance_spin.setValue(7)
            
            # إضافة فترة عمل افتراضية إذا لم تكن موجودة
            if self.work_periods_table.rowCount() == 0:
                self.add_work_period("main")
            
            # إنشاء الجدول
            success = self.db_manager.setup_doctor_periodic_schedule(doctor_id, 30)
            
            if success:
                # حفظ الإعدادات
                self.save_periodic_schedule_settings()
                
                QMessageBox.information(self, "نجاح", 
                                      "✅ تم الإعداد السريع بنجاح!\n\n"
                                      "• تم إنشاء جدول لمدة 30 يوم\n"
                                      "• تم تفعيل التجديد التلقائي\n"
                                      "• تم ضبط التنبيه قبل 7 أيام\n\n"
                                      "النظام جاهز الآن لاستقبال الحجوزات.")
                
                # تحديث معلومات الجدول الحالي
                self.update_current_schedule_info()
            else:
                QMessageBox.critical(self, "خطأ", "❌ فشل في الإعداد السريع")

        except Exception as e:
            logging.error(f"خطأ في الإعداد السريع: {e}")
            QMessageBox.critical(self, "خطأ", f"❌ حدث خطأ أثناء الإعداد السريع:\n{str(e)}")

    def verify_schedule_creation(self):
        """التحقق من إنشاء الجدول وعرض النتائج"""
        if not self.is_edit_mode:
            QMessageBox.warning(self, "تحذير", "يرجى حفظ بيانات الطبيب أولاً")
            return
            
        doctor_id = self.doctor_data.get('id')
        
        try:
            # استخدام الدالة المحدثة من database_manager
            result = self.db_manager.verify_doctor_schedule(doctor_id)
            
            if result['success']:
                message = f"""
✅ تم إنشاء الجدول الدوري بنجاح!

• عدد المواعيد المنشأة: {result['slot_count']}
• عدد الأيام المغطاة: {result['date_count']}
• إعدادات الجدولة: {'مكتملة' if result['has_schedule_settings'] else 'ناقصة'}
• التجديد القادم: {result.get('next_renewal', 'غير محدد')}

{result['message']}
"""
                QMessageBox.information(self, "✅ التحقق الناجح", message.strip())
            else:
                QMessageBox.warning(self, "⚠️ تحتاج إلى إصلاح", 
                                  f"لم يتم إنشاء الجدول بشكل صحيح:\n\n{result['message']}\n\n"
                                  f"يرجى استخدام زر 'إنشاء الجدول الدوري' لإصلاح المشكلة.")
                                  
        except Exception as e:
            logging.error(f"❌ خطأ في التحقق من الجدول: {e}")
            QMessageBox.critical(self, "❌ خطأ", f"حدث خطأ أثناء التحقق:\n{str(e)}")

    def update_current_schedule_info(self):
        """تحديث معلومات الجدول الحالي"""
        try:
            if not self.is_edit_mode:
                return

            doctor_id = self.doctor_data.get('id')
            schedule_data = self.db_manager.get_periodic_schedule(doctor_id)

            if not schedule_data:
                self.current_schedule_info.setText("لم يتم إنشاء جدول دوري بعد")
                return

            # حساب الإحصائيات
            total_slots = 0
            available_slots = 0
            booked_slots = 0
            total_days = len(schedule_data)

            for date_data in schedule_data.values():
                total_slots += date_data['total_count']
                available_slots += date_data['available_count']
                booked_slots += date_data['booked_count']

            occupancy_rate = (booked_slots / total_slots * 100) if total_slots > 0 else 0

            info_text = f"""
📊 الجدول الدوري الحالي:

• عدد الأيام: {total_days} يوم
• إجمالي المواعيد: {total_slots} موعد
• المتاحة: {available_slots} • المحجوزة: {booked_slots}
• نسبة الإشغال: {occupancy_rate:.1f}%

🗓️ الفترة: {min(schedule_data.keys())} إلى {max(schedule_data.keys())}
"""

            self.current_schedule_info.setText(info_text.strip())

        except Exception as e:
            logging.error(f"خطأ في تحديث معلومات الجدول: {e}")
            self.current_schedule_info.setText("خطأ في تحميل معلومات الجدول")

    def save_periodic_schedule_settings(self):
        """حفظ إعدادات الجدولة الدورية"""
        try:
            if not self.is_edit_mode:
                return

            doctor_id = self.doctor_data.get('id')
            periodic_data = self.get_periodic_schedule_data()

            # حفظ الإعدادات في الجدول الجديد
            cursor = self.db_manager.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO periodic_schedule_settings 
                (doctor_id, schedule_period_days, auto_renew_enabled, renewal_advance_days)
                VALUES (?, ?, ?, ?)
            ''', (
                doctor_id, 
                periodic_data['schedule_period_days'],
                periodic_data['auto_renew_enabled'],
                periodic_data['renewal_advance_days']
            ))

            self.db_manager.conn.commit()
            logging.info(f"✅ تم حفظ إعدادات الجدولة الدورية للطبيب {doctor_id}")

        except Exception as e:
            logging.error(f"❌ خطأ في حفظ إعدادات الجدولة الدورية: {e}")

    def save_doctor(self):
        """حفظ بيانات الطبيب مع إعدادات الجدولة"""
        if not self.validate_inputs():
            return
        
        doctor_data = self.get_doctor_data()
        
        try:
            if self.is_edit_mode:
                # في وضع التعديل
                success = self.db_manager.update_doctor(self.doctor_data['id'], doctor_data)
                if success:
                    # حفظ إعدادات الجدولة الأساسية
                    self.save_schedule_settings()
                    # حفظ إعدادات الجدولة الدورية
                    self.save_periodic_schedule_settings()
                    
                    QMessageBox.information(self, "نجاح", "✅ تم تحديث بيانات الطبيب وإعدادات الجدولة بنجاح")
                    self.accept()
                else:
                    QMessageBox.critical(self, "خطأ", "❌ فشل في تحديث بيانات الطبيب")
            else:
                # في وضع الإضافة
                doctor_id = self.db_manager.add_doctor(doctor_data)
                if doctor_id:
                    # حفظ إعدادات الجدولة للطبيب الجديد
                    self.doctor_data = {'id': doctor_id}
                    self.save_schedule_settings()
                    self.save_periodic_schedule_settings()
                    
                    QMessageBox.information(self, "نجاح", f"✅ تم إضافة الطبيب بنجاح\n\nرقم الطبيب: {doctor_id}")
                    self.accept()
                else:
                    QMessageBox.critical(self, "خطأ", "❌ فشل في إضافة الطبيب")
                    
        except Exception as e:
            logging.error(f"❌ خطأ في حفظ بيانات الطبيب: {e}")
            QMessageBox.critical(self, "خطأ", f"❌ حدث خطأ غير متوقع:\n{str(e)}")
    
    def save_schedule_settings(self):
        """حفظ إعدادات الجدولة الأساسية"""
        try:
            if not self.is_edit_mode:
                return
                
            doctor_id = self.doctor_data.get('id')
            schedule_data = self.get_schedule_data()
            
            # حفظ في جدول إعدادات الجدولة
            success = self.db_manager.setup_doctor_schedule(
                doctor_id=doctor_id,
                appointment_duration=schedule_data['appointment_duration'],
                work_days=schedule_data['work_days'],
                work_start="08:00",  # سيتم تجاهلها إذا كانت هناك فترات عمل
                work_end="17:00",    # سيتم تجاهلها إذا كانت هناك فترات عمل
                breaks=schedule_data['break_times'],
                buffer_time=schedule_data['buffer_time'],
                work_periods=schedule_data['work_periods']
            )
            
            if success:
                logging.info(f"✅ تم حفظ إعدادات الجدولة للطبيب {doctor_id}")
            else:
                logging.error(f"❌ فشل في حفظ إعدادات الجدولة للطبيب {doctor_id}")
                    
        except Exception as e:
            logging.error(f"❌ خطأ في حفظ إعدادات الجدولة: {e}")

    def get_group_style(self):
        """نمط المجموعات"""
        return """
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2C3E50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }
        """
    
    def get_input_style(self):
        """نمط حقول الإدخال"""
        return """
            QLineEdit, QSpinBox, QDoubleSpinBox, QTimeEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 13px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTimeEdit:focus {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
        """
    
    def get_combo_style(self):
        """نمط القوائم المنسدلة"""
        return """
            QComboBox {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 13px;
                min-width: 200px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
        """
    
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
            "info": """
                QPushButton {
                    background-color: #17A2B8;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #138496;
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
            style = style.replace("8px 16px", "12px 25px").replace("12px", "14px")
        return style