# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QTextEdit, QComboBox, QDateEdit, 
                             QTimeEdit, QPushButton, QMessageBox, QLabel, 
                             QGroupBox, QFrame, QCheckBox, QTabWidget, QWidget,
                             QGridLayout, QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, QDate, QTime, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
import logging
from datetime import datetime, timedelta

# استيراد المكون المحسّن
from ui.dialogs.widgets.smart_search import SmartSearchComboBox

class AppointmentDialog(QDialog):
    # إشارة لإعلام النافذة الرئيسية بالتحديثات
    appointment_saved = pyqtSignal(dict)
    whatsapp_message_requested = pyqtSignal(dict)  # إشارة طلب إرسال واتساب
    
    def __init__(self, db_manager, whatsapp_manager=None, parent=None, appointment_data=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.whatsapp_manager = whatsapp_manager
        self.appointment_data = appointment_data
        self.is_edit_mode = appointment_data is not None
        self.selected_patient = None
        self.available_templates = []
        
        self.setup_ui()
        self.setWindowTitle("🔄 تعديل الموعد" if self.is_edit_mode else "➕ إضافة موعد جديد")
        self.setMinimumSize(900, 800)
        self.setModal(True)
        
        # تحميل القوالب المتاحة
        self.load_available_templates()
        
    def setup_ui(self):
        """إعداد واجهة الحوار - محسّنة بشكل احترافي"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # العنوان الرئيسي
        title = QLabel("🔄 تعديل الموعد" if self.is_edit_mode else "➕ إضافة موعد جديد")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(18)
        title.setFont(title_font)
        title.setStyleSheet("""
            QLabel {
                color: #2C3E50; 
                padding: 20px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498DB, stop:1 #2C3E50);
                color: white;
                border-radius: 12px;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(title)
        
        # تبويبات متعددة للتنظيم
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #BDC3C7;
                border-radius: 8px;
                background-color: #FFFFFF;
            }
            QTabBar::tab {
                background-color: #ECF0F1;
                color: #2C3E50;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: #3498DB;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #2980B9;
                color: white;
            }
        """)
        
        # تبويب المعلومات الأساسية
        self.setup_basic_info_tab()
        # تبويب إعدادات الواتساب
        self.setup_whatsapp_tab()
        # تبويب السجل والتاريخ
        self.setup_history_tab()
        
        layout.addWidget(self.tabs)
        
        # شريط الحالة السريع
        self.setup_status_bar(layout)
        
        # أزرار التحكم الرئيسية
        self.setup_control_buttons(layout)
        
        self.setLayout(layout)
        
        # تحميل البيانات الأولية
        self.load_initial_data()
        
        # إضافة قسم الجدولة الذكية
        self.setup_smart_scheduling_section()
        
        # إذا كان في وضع التعديل، تعبئة البيانات
        if self.is_edit_mode:
            QTimer.singleShot(100, self.fill_data)
    
    def setup_basic_info_tab(self):
        """إعداد تبويب المعلومات الأساسية"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # مجموعة معلومات المريض
        patient_group = QGroupBox("👤 معلومات المريض")
        patient_group.setStyleSheet(self.get_group_style())
        patient_layout = QFormLayout(patient_group)
        patient_layout.setLabelAlignment(Qt.AlignRight)
        patient_layout.setSpacing(12)
        
        # البحث الذكي عن المريض
        self.patient_search = SmartSearchComboBox()
        self.patient_search.selection_changed.connect(self.on_patient_selected)
        self.patient_search.setMinimumHeight(45)
        patient_layout.addRow("🔍 البحث عن المريض *:", self.patient_search)
        
        # معلومات المريض المحدد
        self.patient_info_frame = QFrame()
        self.patient_info_frame.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border: 2px dashed #BDC3C7;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        patient_info_layout = QGridLayout(self.patient_info_frame)
        
        self.patient_name_label = QLabel("الاسم: --")
        self.patient_phone_label = QLabel("الهاتف: --")
        self.patient_gender_label = QLabel("الجنس: --")
        self.patient_age_label = QLabel("العمر: --")
        
        for label in [self.patient_name_label, self.patient_phone_label, 
                     self.patient_gender_label, self.patient_age_label]:
            label.setStyleSheet("font-size: 13px; color: #2C3E50; padding: 5px;")
        
        patient_info_layout.addWidget(self.patient_name_label, 0, 0)
        patient_info_layout.addWidget(self.patient_phone_label, 0, 1)
        patient_info_layout.addWidget(self.patient_gender_label, 1, 0)
        patient_info_layout.addWidget(self.patient_age_label, 1, 1)
        
        patient_layout.addRow("معلومات المريض:", self.patient_info_frame)
        self.patient_info_frame.hide()
        
        layout.addWidget(patient_group)
        
        # مجموعة معلومات الموعد
        appointment_group = QGroupBox("📅 معلومات الموعد")
        appointment_group.setStyleSheet(self.get_group_style())
        appointment_layout = QFormLayout(appointment_group)
        appointment_layout.setLabelAlignment(Qt.AlignRight)
        appointment_layout.setSpacing(12)
        
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
        self.type_combo.addItems(["🩺 كشف", "📋 روتيني", "🚨 مستعجل", "🔄 متابعة", "💬 استشارة", "🔬 تحليل", "📷 أشعة"])
        self.setup_combo_style(self.type_combo)
        
        # حالة الموعد
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "🟡 مجدول", "🟢 مؤكد", "🔵 حاضر", "🟣 منتهي", 
            "🔴 ملغي", "🟠 مؤجل", "⚫ غائب"
        ])
        self.setup_combo_style(self.status_combo)
        
        # الملاحظات
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(120)
        self.notes_input.setPlaceholderText("📝 اكتب ملاحظات إضافية عن الموعد...")
        self.notes_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #BDC3C7;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                background-color: #FFFFFF;
                color: #2C3E50;
            }
            QTextEdit:focus {
                border-color: #3498DB;
                background-color: #F0F8FF;
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
        
        layout.addWidget(appointment_group)
        
        # ربط الأحداث
        self.clinic_combo.currentIndexChanged.connect(self.on_clinic_changed)
        self.department_combo.currentIndexChanged.connect(self.on_department_changed)
        
        self.tabs.addTab(tab, "📋 المعلومات الأساسية")
    
    def setup_whatsapp_tab(self):
        """إعداد تبويب إعدادات الواتساب"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # مجموعة إعدادات الواتساب
        whatsapp_group = QGroupBox("📱 إعدادات رسائل الواتساب")
        whatsapp_group.setStyleSheet(self.get_group_style())
        whatsapp_layout = QVBoxLayout(whatsapp_group)
        
        # التحكم في الإرسال التلقائي
        auto_send_layout = QHBoxLayout()
        
        self.auto_send_check = QCheckBox("إرسال رسالة ترحيب تلقائية")
        self.auto_send_check.setChecked(True)
        self.auto_send_check.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
                font-size: 14px;
                color: #2C3E50;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QCheckBox::indicator:checked {
                background-color: #27AE60;
                border: 2px solid #219A52;
            }
        """)
        
        self.auto_reminder_check = QCheckBox("تفعيل التذكيرات التلقائية")
        self.auto_reminder_check.setChecked(True)
        self.auto_reminder_check.setStyleSheet(self.auto_send_check.styleSheet())
        
        auto_send_layout.addWidget(self.auto_send_check)
        auto_send_layout.addWidget(self.auto_reminder_check)
        auto_send_layout.addStretch()
        
        whatsapp_layout.addLayout(auto_send_layout)
        
        # اختيار القالب
        template_layout = QFormLayout()
        template_layout.setLabelAlignment(Qt.AlignRight)
        
        self.template_combo = QComboBox()
        self.template_combo.setMinimumHeight(35)
        self.setup_combo_style(self.template_combo)
        template_layout.addRow("📝 اختر قالب الرسالة:", self.template_combo)
        
        # معاينة الرسالة
        self.message_preview = QTextEdit()
        self.message_preview.setMaximumHeight(150)
        self.message_preview.setReadOnly(True)
        self.message_preview.setStyleSheet("""
            QTextEdit {
                border: 2px solid #BDC3C7;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                background-color: #F8F9FA;
                color: #2C3E50;
                line-height: 1.5;
            }
        """)
        template_layout.addRow("👁️ معاينة الرسالة:", self.message_preview)
        
        # أزرار التحكم بالرسائل
        message_buttons_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("🔄 تحديث المعاينة")
        self.preview_btn.clicked.connect(self.update_message_preview)
        self.preview_btn.setStyleSheet(self.get_button_style("secondary"))
        
        self.test_send_btn = QPushButton("🧪 إرسال تجريبي")
        self.test_send_btn.clicked.connect(self.send_test_message)
        self.test_send_btn.setStyleSheet(self.get_button_style("info"))
        
        message_buttons_layout.addWidget(self.preview_btn)
        message_buttons_layout.addWidget(self.test_send_btn)
        message_buttons_layout.addStretch()
        
        template_layout.addRow("إجراءات سريعة:", message_buttons_layout)
        
        whatsapp_layout.addLayout(template_layout)
        layout.addWidget(whatsapp_group)
        
        # معلومات الإرسال
        send_info_group = QGroupBox("📊 معلومات الإرسال")
        send_info_group.setStyleSheet(self.get_group_style())
        send_info_layout = QGridLayout(send_info_group)
        
        self.send_status_label = QLabel("الحالة: في انتظار الإرسال")
        self.send_time_label = QLabel("الوقت: --")
        self.message_type_label = QLabel("نوع الرسالة: --")
        self.provider_label = QLabel("المزود: --")
        
        for label in [self.send_status_label, self.send_time_label, 
                     self.message_type_label, self.provider_label]:
            label.setStyleSheet("font-size: 13px; padding: 8px; background-color: #ECF0F1; border-radius: 5px;")
        
        send_info_layout.addWidget(QLabel("📤 حالة الإرسال:"), 0, 0)
        send_info_layout.addWidget(self.send_status_label, 0, 1)
        send_info_layout.addWidget(QLabel("⏰ وقت الإرسال:"), 1, 0)
        send_info_layout.addWidget(self.send_time_label, 1, 1)
        send_info_layout.addWidget(QLabel("📨 نوع الرسالة:"), 2, 0)
        send_info_layout.addWidget(self.message_type_label, 2, 1)
        send_info_layout.addWidget(QLabel("🌐 مزود الخدمة:"), 3, 0)
        send_info_layout.addWidget(self.provider_label, 3, 1)
        
        layout.addWidget(send_info_group)
        
        self.tabs.addTab(tab, "📱 رسائل الواتساب")
    
    def setup_history_tab(self):
        """إعداد تبويب السجل والتاريخ"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # سجل المواعيد السابقة
        history_group = QGroupBox("📋 سجل المواعيد السابقة")
        history_group.setStyleSheet(self.get_group_style())
        history_layout = QVBoxLayout(history_group)
        
        self.history_label = QLabel("سيظهر هنا سجل المواعيد السابقة للمريض...")
        self.history_label.setAlignment(Qt.AlignCenter)
        self.history_label.setStyleSheet("""
            QLabel {
                padding: 40px;
                background-color: #F8F9FA;
                border: 2px dashed #BDC3C7;
                border-radius: 8px;
                color: #7F8C8D;
                font-size: 14px;
            }
        """)
        history_layout.addWidget(self.history_label)
        
        layout.addWidget(history_group)
        
        # الإحصائيات السريعة
        stats_group = QGroupBox("📊 إحصائيات سريعة")
        stats_group.setStyleSheet(self.get_group_style())
        stats_layout = QGridLayout(stats_group)
        
        stats_data = [
            ("🟡 المواعيد المجدولة", "0"),
            ("🟢 المواعيد المؤكدة", "0"),
            ("🔵 المواعيد الحاضرة", "0"),
            ("🟣 المواعيد المنتهية", "0")
        ]
        
        for i, (title, value) in enumerate(stats_data):
            title_label = QLabel(title)
            value_label = QLabel(value)
            value_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    font-size: 16px;
                    color: #2C3E50;
                    padding: 5px;
                    background-color: #ECF0F1;
                    border-radius: 5px;
                    min-width: 60px;
                    text-align: center;
                }
            """)
            stats_layout.addWidget(title_label, i//2, (i%2)*2)
            stats_layout.addWidget(value_label, i//2, (i%2)*2+1)
        
        layout.addWidget(stats_group)
        
        self.tabs.addTab(tab, "📈 السجل والإحصائيات")
    
    def setup_status_bar(self, parent_layout):
        """إعداد شريط الحالة السريع"""
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #2C3E50;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        status_layout = QHBoxLayout(status_frame)
        
        self.status_icon = QLabel("🟢")
        self.status_text = QLabel("جاهز لإضافة موعد جديد")
        self.status_text.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")
        
        status_layout.addWidget(self.status_icon)
        status_layout.addWidget(self.status_text)
        status_layout.addStretch()
        
        # مؤشر التحميل
        self.loading_label = QLabel("")
        self.loading_label.setStyleSheet("color: #3498DB; font-size: 12px;")
        status_layout.addWidget(self.loading_label)
        
        parent_layout.addWidget(status_frame)
    
    def setup_control_buttons(self, parent_layout):
        """إعداد أزرار التحكم الرئيسية"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # زر الحفظ الأساسي
        self.save_button = QPushButton("💾 حفظ الموعد")
        self.save_button.clicked.connect(self.save_appointment)
        self.save_button.setDefault(True)
        self.save_button.setMinimumHeight(50)
        self.save_button.setStyleSheet(self.get_button_style("success", large=True))
        
        # زر الحفظ والإرسال
        self.save_send_button = QPushButton("💾📤 حفظ وإرسال رسالة")
        self.save_send_button.clicked.connect(lambda: self.save_appointment(send_message=True))
        self.save_send_button.setMinimumHeight(50)
        self.save_send_button.setStyleSheet(self.get_button_style("primary", large=True))
        
        # زر الإلغاء
        self.cancel_button = QPushButton("❌ إلغاء")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setMinimumHeight(50)
        self.cancel_button.setStyleSheet(self.get_button_style("danger", large=True))
        
        button_layout.addWidget(self.save_send_button)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        
        parent_layout.addLayout(button_layout)
    
    def get_group_style(self):
        """نمط المجموعات"""
        return """
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2C3E50;
                border: 2px solid #BDC3C7;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 15px 0 15px;
                background-color: #3498DB;
                color: white;
                border-radius: 5px;
            }
        """
    
    def setup_combo_style(self, combo):
        """إعداد نمط ComboBox"""
        combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 2px solid #BDC3C7;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
                color: #2C3E50;
                min-height: 25px;
            }
            QComboBox:focus {
                border-color: #3498DB;
                background-color: #F0F8FF;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left-width: 1px;
                border-left-color: #BDC3C7;
                border-left-style: solid;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #2C3E50;
                width: 0px;
                height: 0px;
            }
        """)
    
    def setup_date_style(self, date_edit):
        """إعداد نمط DateEdit"""
        date_edit.setStyleSheet("""
            QDateEdit {
                padding: 10px;
                border: 2px solid #BDC3C7;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
                color: #2C3E50;
                min-height: 25px;
            }
            QDateEdit:focus {
                border-color: #3498DB;
                background-color: #F0F8FF;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left-width: 1px;
                border-left-color: #BDC3C7;
                border-left-style: solid;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }
        """)
    
    def setup_time_style(self, time_edit):
        """إعداد نمط TimeEdit"""
        time_edit.setStyleSheet("""
            QTimeEdit {
                padding: 10px;
                border: 2px solid #BDC3C7;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
                color: #2C3E50;
                min-height: 25px;
            }
            QTimeEdit:focus {
                border-color: #3498DB;
                background-color: #F0F8FF;
            }
        """)
    
    def get_button_style(self, button_type="primary", large=False):
        """أنماط الأزرار"""
        styles = {
            "primary": """
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    padding: 15px 25px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 14px;
                    min-width: 150px;
                }
                QPushButton:hover {
                    background-color: #2980B9;
                }
                QPushButton:pressed {
                    background-color: #21618C;
                }
            """,
            "success": """
                QPushButton {
                    background-color: #27AE60;
                    color: white;
                    border: none;
                    padding: 15px 25px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 14px;
                    min-width: 150px;
                }
                QPushButton:hover {
                    background-color: #219A52;
                }
                QPushButton:pressed {
                    background-color: #1E8449;
                }
            """,
            "danger": """
                QPushButton {
                    background-color: #E74C3C;
                    color: white;
                    border: none;
                    padding: 15px 25px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 14px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #C0392B;
                }
                QPushButton:pressed {
                    background-color: #A93226;
                }
            """,
            "secondary": """
                QPushButton {
                    background-color: #95A5A6;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 13px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #7F8C8D;
                }
            """,
            "info": """
                QPushButton {
                    background-color: #17A2B8;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 13px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #138496;
                }
            """
        }
        
        style = styles.get(button_type, styles["primary"])
        if large:
            style = style.replace("padding: 10px 20px;", "padding: 15px 25px;")
            style = style.replace("font-size: 13px;", "font-size: 14px;")
        
        return style
    
    def load_initial_data(self):
        """تحميل البيانات الأولية"""
        try:
            self.set_loading_status("جاري تحميل البيانات...")
            
            # تحميل المرضى
            patients = self.db_manager.get_patients()
            if patients:
                self.patient_search.set_items(patients)
                logging.info(f"✅ تم تحميل {len(patients)} مريض")
            
            # تحميل العيادات
            clinics = self.db_manager.get_clinics()
            self.clinic_combo.clear()
            self.clinic_combo.addItem("-- اختر العيادة --", None)
            for clinic in clinics:
                display_text = f"{clinic['name']} ({clinic['type']}) - {clinic.get('country_code', '+966')}"
                self.clinic_combo.addItem(display_text, clinic['id'])
            
            # تحديث حالة المزود
            if self.whatsapp_manager:
                provider = self.whatsapp_manager.current_provider or "غير محدد"
                self.provider_label.setText(f"المزود: {provider}")
            
            self.set_ready_status()
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل البيانات: {e}")
            self.set_error_status(f"خطأ في تحميل البيانات: {e}")
    
    def load_available_templates(self):
        """تحميل القوالب المتاحة"""
        try:
            if self.whatsapp_manager:
                self.available_templates = self.db_manager.get_message_templates(1)  # clinic_id=1
                self.template_combo.clear()
                self.template_combo.addItem("-- اختر قالب --", None)
                
                for template in self.available_templates:
                    display_name = f"{template['template_name']} ({template['template_type']})"
                    self.template_combo.addItem(display_name, template)
                
                logging.info(f"✅ تم تحميل {len(self.available_templates)} قالب")
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل القوالب: {e}")
    
    def on_patient_selected(self, patient_data):
        """عند اختيار مريض من البحث"""
        try:
            if patient_data and 'id' in patient_data:
                self.selected_patient = patient_data
                
                # تحديث معلومات المريض
                self.patient_info_frame.show()
                self.patient_name_label.setText(f"الاسم: {patient_data.get('name', '--')}")
                self.patient_phone_label.setText(f"الهاتف: {patient_data.get('phone', '--')}")
                self.patient_gender_label.setText(f"الجنس: {patient_data.get('gender', '--')}")
                
                # حساب العمر
                dob = patient_data.get('date_of_birth')
                if dob:
                    birth_date = datetime.strptime(dob, '%Y-%m-%d').date()
                    today = datetime.now().date()
                    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                    self.patient_age_label.setText(f"العمر: {age} سنة")
                else:
                    self.patient_age_label.setText("العمر: --")
                
                self.update_message_preview()
                self.check_form_validity()
                
                logging.info(f"✅ تم اختيار المريض: {patient_data.get('name')}")
                
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
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل الأطباء: {e}")
    
    def update_message_preview(self):
        """تحديث معاينة الرسالة"""
        try:
            template_data = self.template_combo.currentData()
            if not template_data or not self.selected_patient:
                self.message_preview.setPlainText("⚠️ يرجى اختيار مريض و قالب أولاً")
                return
            
            # استبدال المتغيرات في القالب
            message_content = template_data['template_content']
            variables = {
                'patient_name': self.selected_patient.get('name', 'عزيزي/عزيزتي'),
                'patient_phone': self.selected_patient.get('phone', ''),
                'clinic_name': self.clinic_combo.currentText().split(' - ')[0] if self.clinic_combo.currentText() != "-- اختر العيادة --" else "العيادة",
                'doctor_name': self.doctor_combo.currentText() if self.doctor_combo.currentText() != "-- اختر الطبيب --" else "الطبيب",
                'appointment_date': self.appointment_date.date().toString("dd/MM/yyyy"),
                'appointment_time': self.appointment_time.time().toString("hh:mm AP"),
                'department_name': self.department_combo.currentText() if self.department_combo.currentText() != "-- اختر القسم --" else "القسم"
            }
            
            for key, value in variables.items():
                message_content = message_content.replace(f'{{{key}}}', str(value))
            
            self.message_preview.setPlainText(message_content)
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث المعاينة: {e}")
    
    def send_test_message(self):
        """إرسال رسالة تجريبية"""
        if not self.selected_patient or not self.whatsapp_manager:
            QMessageBox.warning(self, "تحذير", "⚠️ يرجى اختيار مريض أولاً والتأكد من إعدادات الواتساب")
            return
        
        try:
            phone = self.selected_patient.get('phone')
            country_code = self.selected_patient.get('country_code', '+966')
            
            if not phone:
                QMessageBox.warning(self, "تحذير", "⚠️ لا يوجد رقم هاتف للمريض المحدد")
                return
            
            message = self.message_preview.toPlainText()
            if not message or message.startswith("⚠️"):
                QMessageBox.warning(self, "تحذير", "⚠️ يرجى اختيار قالب صحيح أولاً")
                return
            
            # إرسال الرسالة
            success = self.whatsapp_manager.send_message(phone, message, "test")
            
            if success:
                QMessageBox.information(self, "نجاح", "✅ تم إرسال الرسالة التجريبية بنجاح!")
                self.send_status_label.setText("الحالة: ✅ تم الإرسال التجريبي")
                self.send_time_label.setText(f"الوقت: {datetime.now().strftime('%H:%M')}")
            else:
                QMessageBox.warning(self, "تحذير", "⚠️ فشل في إرسال الرسالة التجريبية")
                self.send_status_label.setText("الحالة: ❌ فشل الإرسال")
                
        except Exception as e:
            logging.error(f"❌ خطأ في الإرسال التجريبي: {e}")
            QMessageBox.critical(self, "خطأ", f"❌ حدث خطأ أثناء الإرسال: {e}")
    
    def check_form_validity(self):
        """التحقق من صحة النموذج"""
        is_valid = (
            self.selected_patient and 
            self.clinic_combo.currentData() and
            self.department_combo.currentData() and
            self.doctor_combo.currentData()
        )
        
        self.save_button.setEnabled(is_valid)
        self.save_send_button.setEnabled(is_valid)
        
        if is_valid:
            self.status_text.setText("✅ النموذج صالح للحفظ")
            self.status_icon.setText("🟢")
        else:
            self.status_text.setText("⚠️ يرجى إكمال البيانات المطلوبة")
            self.status_icon.setText("🟡")
        
        return is_valid
    
    def validate_inputs(self):
        """التحقق من صحة البيانات"""
        if not self.check_form_validity():
            QMessageBox.warning(self, "بيانات ناقصة", 
                "يرجى إكمال جميع الحقول المطلوبة:\n"
                "• اختيار المريض\n"
                "• اختيار العيادة\n" 
                "• اختيار القسم\n"
                "• اختيار الطبيب")
            return False
        
        # التحقق من التاريخ والوقت
        appointment_date = self.appointment_date.date()
        if appointment_date < QDate.currentDate():
            QMessageBox.warning(self, "تاريخ غير صحيح", "لا يمكن حجز موعد في تاريخ ماضي")
            return False
        
        return True
    
    def fill_data(self):
        """تعبئة البيانات الحالية للموعد"""
        if not self.appointment_data:
            return
        
        try:
            # تعبئة بيانات المريض
            patient_id = self.appointment_data.get('patient_id')
            if patient_id:
                patient_data = self.db_manager.get_patient_by_id(patient_id)
                if patient_data:
                    self.selected_patient = patient_data
                    self.patient_search.set_selected_patient(patient_data)
            
            # تعبئة باقي البيانات
            clinic_id = self.appointment_data.get('clinic_id')
            if clinic_id:
                index = self.clinic_combo.findData(clinic_id)
                if index >= 0:
                    self.clinic_combo.setCurrentIndex(index)
            
            # استخدام المؤقتات لضمان تحميل البيانات بالتسلسل
            QTimer.singleShot(100, self.fill_department_data)
            QTimer.singleShot(200, self.fill_doctor_data)
            QTimer.singleShot(300, self.fill_other_data)
            
        except Exception as e:
            logging.error(f"❌ خطأ في تعبئة البيانات: {e}")
    
    def fill_department_data(self):
        """تعبئة بيانات القسم"""
        department_id = self.appointment_data.get('department_id')
        if department_id:
            self.on_clinic_changed()
            QTimer.singleShot(50, lambda: self.set_department(department_id))
    
    def fill_doctor_data(self):
        """تعبئة بيانات الطبيب"""
        doctor_id = self.appointment_data.get('doctor_id')
        if doctor_id:
            QTimer.singleShot(100, lambda: self.set_doctor(doctor_id))
    
    def fill_other_data(self):
        """تعبئة البيانات الأخرى"""
        try:
            # التاريخ والوقت
            appointment_date = self.appointment_data.get('appointment_date')
            if appointment_date:
                self.appointment_date.setDate(QDate.fromString(appointment_date, 'yyyy-MM-dd'))
            
            appointment_time = self.appointment_data.get('appointment_time')
            if appointment_time:
                self.appointment_time.setTime(QTime.fromString(appointment_time, 'hh:mm'))
            
            # النوع والحالة
            appointment_type = self.appointment_data.get('type')
            if appointment_type:
                # إزالة الرموز التعبيرية للبحث
                clean_type = appointment_type.replace('🩺', '').replace('📋', '').replace('🚨', '').replace('🔄', '').replace('💬', '').replace('🔬', '').replace('📷', '').strip()
                index = self.type_combo.findText(clean_type, Qt.MatchContains)
                if index >= 0:
                    self.type_combo.setCurrentIndex(index)
            
            status = self.appointment_data.get('status')
            if status:
                clean_status = status.replace('🟡', '').replace('🟢', '').replace('🔵', '').replace('🟣', '').replace('🔴', '').replace('🟠', '').replace('⚫', '').strip()
                index = self.status_combo.findText(clean_status, Qt.MatchContains)
                if index >= 0:
                    self.status_combo.setCurrentIndex(index)
            
            self.notes_input.setPlainText(self.appointment_data.get('notes', ''))
            
            # تحديث حالة الواتساب إذا كان هناك إرسال سابق
            if self.appointment_data.get('whatsapp_sent'):
                self.send_status_label.setText("الحالة: ✅ تم الإرسال مسبقاً")
            
            logging.info("✅ تم تحميل بيانات الموعد بنجاح")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تعبئة البيانات الأخرى: {e}")
    
    def set_department(self, department_id):
        """تعيين القسم"""
        index = self.department_combo.findData(department_id)
        if index >= 0:
            self.department_combo.setCurrentIndex(index)
    
    def set_doctor(self, doctor_id):
        """تعيين الطبيب"""
        index = self.doctor_combo.findData(doctor_id)
        if index >= 0:
            self.doctor_combo.setCurrentIndex(index)
    
    def get_appointment_data(self):
        """استخراج بيانات الموعد من النموذج"""
        return {
            'patient_id': self.selected_patient['id'],
            'patient_name': self.selected_patient['name'],
            'patient_phone': self.selected_patient.get('phone'),
            'patient_country_code': self.selected_patient.get('country_code', '+966'),
            'doctor_id': self.doctor_combo.currentData(),
            'doctor_name': self.doctor_combo.currentText(),
            'department_id': self.department_combo.currentData(),
            'department_name': self.department_combo.currentText(),
            'clinic_id': self.clinic_combo.currentData(),
            'clinic_name': self.clinic_combo.currentText(),
            'appointment_date': self.appointment_date.date().toString('yyyy-MM-dd'),
            'appointment_time': self.appointment_time.time().toString('hh:mm'),
            'type': self.type_combo.currentText().split(' ', 1)[-1],  # إزالة الرمز
            'status': self.status_combo.currentText().split(' ', 1)[-1],  # إزالة الرمز
            'notes': self.notes_input.toPlainText().strip() or None,
            'whatsapp_data': {
                'send_message': self.auto_send_check.isChecked(),
                'send_reminders': self.auto_reminder_check.isChecked(),
                'template': self.template_combo.currentData(),
                'message_content': self.message_preview.toPlainText()
            } if self.whatsapp_manager else None
        }
    
    def save_appointment(self, send_message=False):
        """حفظ بيانات الموعد"""
        try:
            if not self.validate_inputs():
                return
            
            self.set_loading_status("جاري حفظ الموعد...")
            
            appointment_data = self.get_appointment_data()
            
            if self.is_edit_mode:
                # تحديث الموعد الحالي
                success = self.db_manager.update_appointment(self.appointment_data['id'], appointment_data)
                action = "تحديث"
                appointment_id = self.appointment_data['id']
            else:
                # إضافة موعد جديد
                appointment_id = self.db_manager.add_appointment(appointment_data)
                success = appointment_id is not None
                action = "إضافة"
            
            if success:
                appointment_data['id'] = appointment_id
                
                # إرسال رسالة واتساب إذا مطلوب
                if send_message and self.whatsapp_manager and self.auto_send_check.isChecked():
                    self.send_whatsapp_message(appointment_data)
                
                # إرسال إشارة الحفظ
                self.appointment_saved.emit(appointment_data)
                
                # عرض رسالة النجاح
                self.show_success_message(appointment_data, action)
                
                self.accept()
                
            else:
                self.set_error_status("فشل في حفظ الموعد")
                QMessageBox.critical(self, "خطأ", f"❌ فشل في {action} الموعد")
                
        except Exception as e:
            logging.error(f"❌ خطأ في حفظ الموعد: {e}")
            self.set_error_status(f"خطأ في الحفظ: {e}")
            QMessageBox.critical(self, "خطأ", f"❌ حدث خطأ غير متوقع: {e}")
    
    def send_whatsapp_message(self, appointment_data):
        """إرسال رسالة واتساب"""
        try:
            if not self.whatsapp_manager or not appointment_data.get('patient_phone'):
                return
            
            message_content = self.message_preview.toPlainText()
            if not message_content or message_content.startswith("⚠️"):
                logging.warning("⚠️ محتوى الرسالة غير صالح للإرسال")
                return
            
            # إرسال الرسالة
            success = self.whatsapp_manager.send_message(
                phone=appointment_data['patient_phone'],
                message=message_content,
                message_type="appointment_confirmation",
                appointment_id=appointment_data['id'],
                patient_id=appointment_data['patient_id']
            )
            
            if success:
                self.send_status_label.setText("الحالة: ✅ تم إرسال الرسالة")
                self.send_time_label.setText(f"الوقت: {datetime.now().strftime('%H:%M')}")
                logging.info(f"✅ تم إرسال رسالة واتساب للموعد {appointment_data['id']}")
            else:
                self.send_status_label.setText("الحالة: ❌ فشل إرسال الرسالة")
                logging.error(f"❌ فشل إرسال رسالة واتساب للموعد {appointment_data['id']}")
                
        except Exception as e:
            logging.error(f"❌ خطأ في إرسال رسالة واتساب: {e}")
            self.send_status_label.setText("الحالة: ❌ خطأ في الإرسال")
    
    def show_success_message(self, appointment_data, action):
        """عرض رسالة النجاح"""
        success_msg = f"""
        ✅ تم {action} الموعد بنجاح!

        📋 معلومات الموعد:
        • رقم الموعد: {appointment_data['id']}
        • المريض: {appointment_data['patient_name']}
        • الطبيب: {appointment_data['doctor_name']}
        • التاريخ: {appointment_data['appointment_date']}
        • الوقت: {appointment_data['appointment_time']}
        • الحالة: {appointment_data['status']}
        
        """
        
        if self.auto_send_check.isChecked() and self.whatsapp_manager:
            success_msg += "📱 تم إرسال رسالة الترحيب تلقائياً للمريف"
        
        QMessageBox.information(self, "نجاح", success_msg)
    
    def set_loading_status(self, message):
        """تعيين حالة التحميل"""
        self.status_icon.setText("🟡")
        self.status_text.setText(message)
        self.loading_label.setText("⏳")
        QApplication.processEvents()
    
    def set_ready_status(self, message=None):
        """تعيين حالة الجاهزية"""
        self.status_icon.setText("🟢")
        self.status_text.setText(message or "جاهز")
        self.loading_label.setText("")
    
    def set_error_status(self, message):
        """تعيين حالة الخطأ"""
        self.status_icon.setText("🔴")
        self.status_text.setText(message)
        self.loading_label.setText("❌")

    # ============================================================
    # ⭐⭐ نظام الجدولة الذكية المتكامل ⭐⭐
    # ============================================================

    def setup_smart_scheduling_section(self):
        """إضافة قسم الجدولة الذكية في تبويب المعلومات الأساسية"""
        try:
            # البحث عن تبويب المعلومات الأساسية
            basic_info_tab = self.tabs.widget(0)
            basic_info_layout = basic_info_tab.layout()
            
            # مجموعة الجدولة الذكية
            smart_scheduling_group = QGroupBox("🧠 الجدولة الذكية - الأوقات المتاحة")
            smart_scheduling_group.setStyleSheet(self.get_smart_scheduling_style())
            scheduling_layout = QVBoxLayout(smart_scheduling_group)
            
            # شريط حالة الجدولة
            self.scheduling_status_layout = QHBoxLayout()
            self.scheduling_status_icon = QLabel("🟡")
            self.scheduling_status_text = QLabel("اختر الطبيب والتاريخ لعرض الأوقات المتاحة")
            self.scheduling_status_text.setStyleSheet("color: #7F8C8D; font-size: 13px;")
            
            self.scheduling_status_layout.addWidget(self.scheduling_status_icon)
            self.scheduling_status_layout.addWidget(self.scheduling_status_text)
            self.scheduling_status_layout.addStretch()
            
            # زر تحديث الأوقات
            self.refresh_slots_btn = QPushButton("🔄 تحديث الأوقات")
            self.refresh_slots_btn.clicked.connect(self.refresh_available_slots)
            self.refresh_slots_btn.setStyleSheet(self.get_button_style("info"))
            self.refresh_slots_btn.setVisible(False)
            
            self.scheduling_status_layout.addWidget(self.refresh_slots_btn)
            scheduling_layout.addLayout(self.scheduling_status_layout)
            
            # عرض الأوقات المتاحة بطريقة احترافية
            self.setup_professional_slots_display(scheduling_layout)
            
            # إضافة المجموعة إلى الواجهة (في الأعلى بعد معلومات المريض)
            basic_info_layout.insertWidget(2, smart_scheduling_group)
            
            # ربط الأحداث للتحديث التلقائي
            self.setup_scheduling_connections()
            
            logging.info("✅ تم إضافة قسم الجدولة الذكية بنجاح")
            
        except Exception as e:
            logging.error(f"❌ خطأ في إعداد قسم الجدولة الذكية: {e}")

    def setup_professional_slots_display(self, parent_layout):
        """إعداد عرض احترافي للأوقات المتاحة"""
        try:
            # حاوية رئيسية للعرض
            slots_display_container = QFrame()
            slots_display_container.setStyleSheet("""
                QFrame {
                    background-color: #FFFFFF;
                    border: 2px solid #E0E0E0;
                    border-radius: 12px;
                    padding: 0px;
                }
            """)
            slots_main_layout = QVBoxLayout(slots_display_container)
            
            # رأس الجدول
            header_frame = QFrame()
            header_frame.setStyleSheet("""
                QFrame {
                    background-color: #3498DB;
                    border-top-left-radius: 10px;
                    border-top-right-radius: 10px;
                    padding: 12px;
                }
            """)
            header_layout = QHBoxLayout(header_frame)
            
            header_title = QLabel("⏰ الأوقات المتاحة")
            header_title.setStyleSheet("""
                QLabel {
                    color: white;
                    font-weight: bold;
                    font-size: 16px;
                }
            """)
            
            header_info = QLabel("انقر على الوقت المناسب")
            header_info.setStyleSheet("""
                QLabel {
                    color: #E3F2FD;
                    font-size: 13px;
                }
            """)
            
            header_layout.addWidget(header_title)
            header_layout.addStretch()
            header_layout.addWidget(header_info)
            
            slots_main_layout.addWidget(header_frame)
            
            # منطقة عرض الأوقات
            self.slots_scroll_area = QScrollArea()
            self.slots_scroll_area.setWidgetResizable(True)
            self.slots_scroll_area.setMinimumHeight(200)
            self.slots_scroll_area.setMaximumHeight(350)
            self.slots_scroll_area.setStyleSheet("""
                QScrollArea {
                    border: none;
                    background-color: #FAFAFA;
                }
                QScrollArea:disabled {
                    background-color: #F5F5F5;
                }
            """)
            
            self.slots_container = QWidget()
            self.slots_layout = QGridLayout(self.slots_container)
            self.slots_layout.setSpacing(10)
            self.slots_layout.setContentsMargins(15, 15, 15, 15)
            
            self.slots_scroll_area.setWidget(self.slots_container)
            slots_main_layout.addWidget(self.slots_scroll_area)
            
            # رسالة عندما لا توجد أوقات متاحة
            self.no_slots_label = QLabel("🎯 اختر الطبيب والتاريخ أولاً لعرض الأوقات المتاحة")
            self.no_slots_label.setAlignment(Qt.AlignCenter)
            self.no_slots_label.setStyleSheet("""
                QLabel {
                    padding: 50px 20px;
                    color: #7F8C8D;
                    font-size: 14px;
                    background-color: #F8F9FA;
                    border-radius: 8px;
                    margin: 10px;
                }
            """)
            slots_main_layout.addWidget(self.no_slots_label)
            
            # تذييل الجدول
            footer_frame = QFrame()
            footer_frame.setStyleSheet("""
                QFrame {
                    background-color: #F8F9FA;
                    border-bottom-left-radius: 10px;
                    border-bottom-right-radius: 10px;
                    padding: 8px 12px;
                    border-top: 1px solid #E0E0E0;
                }
            """)
            footer_layout = QHBoxLayout(footer_frame)
            
            self.selected_time_label = QLabel("⏱️ لم يتم اختيار وقت")
            self.selected_time_label.setStyleSheet("color: #7F8C8D; font-size: 13px;")
            
            footer_layout.addWidget(self.selected_time_label)
            footer_layout.addStretch()
            
            slots_main_layout.addWidget(footer_frame)
            
            parent_layout.addWidget(slots_display_container)
            
        except Exception as e:
            logging.error(f"❌ خطأ في إعداد العرض الاحترافي: {e}")

    def get_smart_scheduling_style(self):
        """نمط مجموعة الجدولة الذكية"""
        return """
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2C3E50;
                border: 2px solid #3498DB;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 15px 0 15px;
                background-color: #3498DB;
                color: white;
                border-radius: 5px;
            }
        """

    def setup_scheduling_connections(self):
        """ربط إشارات الجدولة الذكية"""
        try:
            # ربط تغيير الطبيب
            if hasattr(self, 'doctor_combo'):
                self.doctor_combo.currentIndexChanged.connect(self.on_doctor_or_date_changed)
            
            # ربط تغيير التاريخ
            if hasattr(self, 'appointment_date'):
                self.appointment_date.dateChanged.connect(self.on_doctor_or_date_changed)
                
            logging.info("✅ تم ربط إشارات الجدولة الذكية")
            
        except Exception as e:
            logging.error(f"❌ خطأ في ربط إشارات الجدولة: {e}")

    def on_doctor_or_date_changed(self):
        """عند تغيير الطبيب أو التاريخ - تحديث الأوقات المتاحة"""
        try:
            doctor_id = self.doctor_combo.currentData() if hasattr(self, 'doctor_combo') else None
            selected_date = self.appointment_date.date().toString("yyyy-MM-dd") if hasattr(self, 'appointment_date') else None
            
            if doctor_id and selected_date and doctor_id != "-- اختر الطبيب --":
                self.refresh_slots_btn.setVisible(True)
                self.load_available_slots(doctor_id, selected_date)
            else:
                self.clear_available_slots()
                self.refresh_slots_btn.setVisible(False)
                
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة تغيير الطبيب/التاريخ: {e}")

    def load_available_slots(self, doctor_id, date):
        """تحميل وعرض الأوقات المتاحة من قاعدة البيانات الحقيقية"""
        try:
            self.set_scheduling_status("loading", "جاري البحث عن الأوقات المتاحة...")
            
            # استخدام نظام الجدولة الذكية الحقيقي من قاعدة البيانات
            available_slots = self.db_manager.get_available_slots(doctor_id, date)
            
            if available_slots:
                self.display_available_slots(available_slots)
                self.set_scheduling_status("success", f"تم العثور على {len(available_slots)} وقت متاح")
            else:
                self.show_no_available_slots()
                self.set_scheduling_status("warning", "لا توجد أوقات متاحة للطبيب في هذا التاريخ")
                
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل الأوقات المتاحة: {e}")
            self.set_scheduling_status("error", f"خطأ في تحميل الأوقات: {e}")

    def display_available_slots(self, slots):
        """عرض الأوقات المتاحة بطريقة احترافية"""
        try:
            logging.info(f"🔍 جاري عرض {len(slots)} وقت متاح")
            
            # إخفاء رسالة عدم وجود أوقات
            self.no_slots_label.hide()
            
            # مسح الأوقات الحالية
            self.clear_slots_layout()
            
            # عرض الأوقات المتاحة
            row, col = 0, 0
            max_cols = 4  # 4 أعمدة لاستخدام أفضل للمساحة
            
            slots_added = 0
            for slot in slots:
                slot_btn = self.create_professional_slot_button(slot)
                if slot_btn:
                    self.slots_layout.addWidget(slot_btn, row, col)
                    slots_added += 1
                    
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
            
            if slots_added == 0:
                self.show_no_available_slots()
                logging.warning("⚠️ لم يتم إضافة أي أزرار رغم وجود بيانات")
            else:
                logging.info(f"✅ تم عرض {slots_added} زر بنجاح")
                self.slots_scroll_area.setVisible(True)
                self.slots_container.setVisible(True)
                    
        except Exception as e:
            logging.error(f"❌ خطأ في عرض الأوقات المتاحة: {e}")
            self.show_no_available_slots()

    def create_professional_slot_button(self, slot):
        """إنشاء زر وقت متاح بطريقة احترافية - الإصدار المصحح"""
        try:
            # استخراج البيانات الحقيقية من قاعدة البيانات
            start_time = slot.get('start_time', slot.get('time', ''))
            end_time = slot.get('end_time', '')
            duration = slot.get('duration', 30)
            
            # إنشاء الزر مع تصميم احترافي
            btn = QPushButton()
            btn.setMinimumSize(120, 80)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            # استخدام نص عادي مع محاذاة مركزية عبر CSS
            btn.setText(f"🕒 {start_time}\n→ {end_time}\n⏱ {duration} د")
            
            # تصميم احترافي للزر مع محاذاة النص في الوسط
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    border: 2px solid #E0E0E0;
                    border-radius: 8px;
                    padding: 8px;
                    margin: 2px;
                    font-size: 12px;
                    color: #2C3E50;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #E3F2FD;
                    border: 2px solid #3498DB;
                    color: #2980B9;
                }
                QPushButton:pressed {
                    background-color: #BBDEFB;
                    border: 2px solid #2980B9;
                    color: #21618C;
                }
            """)
            
            # إضافة تأثير عند التمرير
            btn.setCursor(Qt.PointingHandCursor)
            
            # معلومات إضافية في التلميح
            btn.setToolTip(f"• الوقت: {start_time} - {end_time}\n• المدة: {duration} دقيقة\n• انقر للاختيار")
            
            # ربط الحدث لاختيار الوقت
            btn.clicked.connect(lambda checked, s=slot: self.on_slot_selected(s))
            
            logging.info(f"✅ تم إنشاء زر للوقت: {start_time} - {end_time}")
            return btn
            
        except Exception as e:
            logging.error(f"❌ خطأ في إنشاء زر الوقت: {e}")
            # زر بديل في حالة الخطأ
            error_btn = QPushButton("❌ خطأ")
            error_btn.setEnabled(False)
            error_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFEBEE;
                    border: 2px solid #E57373;
                    border-radius: 8px;
                    color: #C62828;
                    padding: 8px;
                    font-size: 11px;
                }
            """)
            return error_btn

    def on_slot_selected(self, slot):
        """عند اختيار وقت من الأوقات المتاحة"""
        try:
            selected_time = slot.get('start_time', slot.get('time', ''))
            end_time = slot.get('end_time', '')
            
            if selected_time:
                # تعيين الوقت المختار في حقل الوقت
                time_obj = QTime.fromString(selected_time, 'HH:mm')
                if time_obj.isValid():
                    self.appointment_time.setTime(time_obj)
                    
                    # تحديث التذييل بالمعلومات
                    display_text = f"✅ تم اختيار الوقت: {selected_time} - {end_time}"
                    self.selected_time_label.setText(display_text)
                    self.selected_time_label.setStyleSheet("color: #27AE60; font-weight: bold; font-size: 13px;")
                    
                    # عرض رسالة نجاح
                    self.set_scheduling_status("success", f"تم اختيار الوقت: {selected_time}")
                    
                    # تسليط الضوء على الزر المختار
                    self.highlight_selected_slot(selected_time)
                    
                    logging.info(f"✅ تم اختيار الوقت: {selected_time}")
                else:
                    self.set_scheduling_status("error", "وقت غير صحيح")
            else:
                self.set_scheduling_status("warning", "لم يتم اختيار وقت")
                
        except Exception as e:
            logging.error(f"❌ خطأ في اختيار الوقت: {e}")
            self.set_scheduling_status("error", f"خطأ في الاختيار: {e}")

    def highlight_selected_slot(self, selected_time):
        """تسليط الضوء على الزر المختار"""
        try:
            for i in range(self.slots_layout.count()):
                widget = self.slots_layout.itemAt(i).widget()
                if isinstance(widget, QPushButton):
                    if selected_time in widget.text():
                        # تصميم مميز للزر المختار
                        widget.setStyleSheet("""
                            QPushButton {
                                background-color: #FFF3E0;
                                border: 2px solid #FF9800;
                                border-radius: 8px;
                                padding: 8px;
                                margin: 2px;
                                font-size: 12px;
                                color: #2C3E50;
                                font-weight: bold;
                            }
                            QPushButton:hover {
                                background-color: #FFE0B2;
                                border: 2px solid #F57C00;
                                color: #E65100;
                            }
                        """)
                    else:
                        # إعادة الزر إلى حالته الأصلية
                        widget.setStyleSheet("""
                            QPushButton {
                                background-color: #FFFFFF;
                                border: 2px solid #E0E0E0;
                                border-radius: 8px;
                                padding: 8px;
                                margin: 2px;
                                font-size: 12px;
                                color: #2C3E50;
                                font-weight: bold;
                            }
                            QPushButton:hover {
                                background-color: #E3F2FD;
                                border: 2px solid #3498DB;
                                color: #2980B9;
                            }
                        """)
                        
        except Exception as e:
            logging.error(f"❌ خطأ في تسليط الضوء: {e}")

    def clear_slots_layout(self):
        """مسح جميع الأزرار من التخطيط"""
        try:
            while self.slots_layout.count():
                child = self.slots_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        except Exception as e:
            logging.error(f"❌ خطأ في مسح التخطيط: {e}")

    def show_no_available_slots(self):
        """عرض رسالة عدم وجود أوقات متاحة"""
        try:
            self.clear_slots_layout()
            self.no_slots_label.show()
            self.no_slots_label.setText("😔 لا توجد أوقات متاحة للطبيب في هذا التاريخ")
            self.selected_time_label.setText("⏱️ لم يتم اختيار وقت")
            self.selected_time_label.setStyleSheet("color: #7F8C8D; font-size: 13px;")
        except Exception as e:
            logging.error(f"❌ خطأ في عرض رسالة عدم التوفر: {e}")

    def clear_available_slots(self):
        """مسح عرض الأوقات المتاحة"""
        try:
            self.clear_slots_layout()
            self.no_slots_label.show()
            self.no_slots_label.setText("🎯 اختر الطبيب والتاريخ أولاً لعرض الأوقات المتاحة")
            self.selected_time_label.setText("⏱️ لم يتم اختيار وقت")
            self.selected_time_label.setStyleSheet("color: #7F8C8D; font-size: 13px;")
            self.set_scheduling_status("info", "اختر الطبيب والتاريخ لعرض الأوقات المتاحة")
        except Exception as e:
            logging.error(f"❌ خطأ في مسح الأوقات: {e}")

    def refresh_available_slots(self):
        """تحديث الأوقات المتاحة يدوياً"""
        try:
            doctor_id = self.doctor_combo.currentData()
            selected_date = self.appointment_date.date().toString("yyyy-MM-dd")
            
            if doctor_id and selected_date:
                logging.info(f"🔄 تحديث الأوقات للطبيب {doctor_id} في {selected_date}")
                self.set_scheduling_status("loading", "جاري البحث عن الأوقات المتاحة...")
                QApplication.processEvents()
                self.load_available_slots(doctor_id, selected_date)
            else:
                self.set_scheduling_status("warning", "⚠️ يجب اختيار الطبيب والتاريخ أولاً")
                
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث الأوقات: {e}")
            self.set_scheduling_status("error", f"❌ خطأ في التحديث: {e}")

    def set_scheduling_status(self, status_type, message):
        """تعيين حالة نظام الجدولة"""
        try:
            status_config = {
                "loading": {"icon": "🟡", "color": "#F39C12"},
                "success": {"icon": "🟢", "color": "#27AE60"},
                "warning": {"icon": "🟠", "color": "#E67E22"},
                "error": {"icon": "🔴", "color": "#E74C3C"},
                "info": {"icon": "🔵", "color": "#3498DB"}
            }
            
            config = status_config.get(status_type, status_config["info"])
            
            self.scheduling_status_icon.setText(config["icon"])
            self.scheduling_status_text.setText(message)
            self.scheduling_status_text.setStyleSheet(f"color: {config['color']}; font-size: 13px; font-weight: bold;")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تعيين الحالة: {e}")

# استيراد ضروري
from PyQt5.QtWidgets import QApplication