# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QTextEdit, QComboBox, QDateEdit, 
                             QTimeEdit, QPushButton, QLabel, QGroupBox, QFrame, QGridLayout, QCheckBox)
from PyQt5.QtCore import Qt, QDate, QTime, pyqtSignal
from PyQt5.QtGui import QFont
import logging

class WhatsAppManager(QWidget):
    """مدير الواتساب - منفصل ومتكامل"""
    
    # إشارات للتكامل
    test_message_requested = pyqtSignal(str, str)  # رقم الهاتف، الرسالة
    template_changed = pyqtSignal(object)
    
    def __init__(self, db_manager, whatsapp_manager=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.whatsapp_manager = whatsapp_manager
        self.available_templates = []
        self.current_patient = None
        
        self.setup_ui()
        self.load_templates()
        
    def setup_ui(self):
        """إعداد واجهة مدير الواتساب"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # مجموعة إعدادات الواتساب
        whatsapp_group = QGroupBox("📱 إعدادات رسائل الواتساب")
        whatsapp_group.setStyleSheet(self.get_group_style())
        whatsapp_layout = QVBoxLayout(whatsapp_group)
        
        # خيارات الإرسال
        self.setup_send_options(whatsapp_layout)
        
        # اختيار القالب
        self.setup_template_section(whatsapp_layout)
        
        # معاينة الرسالة
        self.setup_preview_section(whatsapp_layout)
        
        # معلومات الإرسال
        self.setup_send_info(whatsapp_layout)
        
        layout.addWidget(whatsapp_group)
        
    def setup_send_options(self, parent_layout):
        """إعداد خيارات الإرسال"""
        options_layout = QHBoxLayout()
        
        self.auto_send_check = QCheckBox("إرسال رسالة ترحيب تلقائية")
        self.auto_send_check.setChecked(True)
        self.auto_send_check.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
                font-size: 12px;
                color: #2C3E50;
                spacing: 6px;
            }
        """)
        
        self.auto_reminder_check = QCheckBox("تفعيل التذكيرات التلقائية")
        self.auto_reminder_check.setChecked(True)
        self.auto_reminder_check.setStyleSheet(self.auto_send_check.styleSheet())
        
        options_layout.addWidget(self.auto_send_check)
        options_layout.addWidget(self.auto_reminder_check)
        options_layout.addStretch()
        
        parent_layout.addLayout(options_layout)
        
    def setup_template_section(self, parent_layout):
        """إعداد قسم القوالب"""
        template_layout = QFormLayout()
        template_layout.setLabelAlignment(Qt.AlignRight)
        template_layout.setSpacing(6)
        
        self.template_combo = QComboBox()
        self.template_combo.setMinimumHeight(30)
        self.setup_combo_style(self.template_combo)
        self.template_combo.currentIndexChanged.connect(self.on_template_changed)
        template_layout.addRow("📝 اختر قالب الرسالة:", self.template_combo)
        
        parent_layout.addLayout(template_layout)
        
    def setup_preview_section(self, parent_layout):
        """إعداد قسم المعاينة"""
        preview_layout = QFormLayout()
        preview_layout.setLabelAlignment(Qt.AlignRight)
        preview_layout.setSpacing(6)
        
        self.message_preview = QTextEdit()
        self.message_preview.setMaximumHeight(100)
        self.message_preview.setReadOnly(True)
        self.message_preview.setStyleSheet("""
            QTextEdit {
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
                background-color: #F8F9FA;
            }
        """)
        preview_layout.addRow("👁️ معاينة الرسالة:", self.message_preview)
        
        # أزرار التحكم
        buttons_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("🔄 تحديث المعاينة")
        self.preview_btn.clicked.connect(self.update_preview)
        self.preview_btn.setStyleSheet(self.get_button_style("secondary"))
        
        self.test_send_btn = QPushButton("🧪 إرسال تجريبي")
        self.test_send_btn.clicked.connect(self.send_test_message)
        self.test_send_btn.setStyleSheet(self.get_button_style("info"))
        
        buttons_layout.addWidget(self.preview_btn)
        buttons_layout.addWidget(self.test_send_btn)
        buttons_layout.addStretch()
        
        preview_layout.addRow("إجراءات سريعة:", buttons_layout)
        
        parent_layout.addLayout(preview_layout)
        
    def setup_send_info(self, parent_layout):
        """إعداد معلومات الإرسال"""
        info_group = QGroupBox("📊 معلومات الإرسال")
        info_group.setStyleSheet(self.get_group_style())
        info_layout = QGridLayout(info_group)
        
        self.send_status_label = QLabel("الحالة: في انتظار الإرسال")
        self.send_time_label = QLabel("الوقت: --")
        self.message_type_label = QLabel("نوع الرسالة: --")
        self.provider_label = QLabel("المزود: --")
        
        for label in [self.send_status_label, self.send_time_label, 
                     self.message_type_label, self.provider_label]:
            label.setStyleSheet("font-size: 11px; padding: 5px; background-color: #ECF0F1; border-radius: 3px;")
        
        info_layout.addWidget(QLabel("📤 حالة الإرسال:"), 0, 0)
        info_layout.addWidget(self.send_status_label, 0, 1)
        info_layout.addWidget(QLabel("⏰ وقت الإرسال:"), 1, 0)
        info_layout.addWidget(self.send_time_label, 1, 1)
        info_layout.addWidget(QLabel("📨 نوع الرسالة:"), 2, 0)
        info_layout.addWidget(self.message_type_label, 2, 1)
        info_layout.addWidget(QLabel("🌐 مزود الخدمة:"), 3, 0)
        info_layout.addWidget(self.provider_label, 3, 1)
        
        parent_layout.addWidget(info_group)
        
    def load_templates(self):
        """تحميل القوالب المتاحة"""
        try:
            if self.db_manager:
                self.available_templates = self.db_manager.get_message_templates(1)  # clinic_id=1
                self.template_combo.clear()
                self.template_combo.addItem("-- اختر قالب --", None)
                
                for template in self.available_templates:
                    display_name = f"{template['template_name']} ({template['template_type']})"
                    self.template_combo.addItem(display_name, template)
                
                logging.info(f"✅ تم تحميل {len(self.available_templates)} قالب")
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل القوالب: {e}")
    
    def set_patient_data(self, patient_data, appointment_data=None):
        """تعيين بيانات المريض للمعاينة"""
        self.current_patient = patient_data
        self.current_appointment = appointment_data
        self.update_preview()
        
    def on_template_changed(self):
        """عند تغيير القالب"""
        template_data = self.template_combo.currentData()
        if template_data:
            self.template_changed.emit(template_data)
        self.update_preview()
    
    def update_preview(self):
        """تحديث معاينة الرسالة"""
        try:
            template_data = self.template_combo.currentData()
            if not template_data or not self.current_patient:
                self.message_preview.setPlainText("⚠️ يرجى اختيار مريض و قالب أولاً")
                return
            
            # استبدال المتغيرات في القالب
            message_content = template_data['template_content']
            variables = self.get_template_variables()
            
            for key, value in variables.items():
                message_content = message_content.replace(f'{{{key}}}', str(value))
            
            self.message_preview.setPlainText(message_content)
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث المعاينة: {e}")
    
    def get_template_variables(self):
        """الحصول على متغيرات القالب"""
        variables = {
                'patient_name': self.current_patient.get('name', 'عزيزي/عزيزتي'),
                'patient_phone': self.current_patient.get('phone', ''),
            }
            
        if self.current_appointment:
            variables.update({
                'clinic_name': self.current_appointment.get('clinic_name', 'العيادة'),
                'doctor_name': self.current_appointment.get('doctor_name', 'الطبيب'),
                'appointment_date': self.current_appointment.get('appointment_date', ''),
                'appointment_time': self.current_appointment.get('appointment_time', ''),
                'department_name': self.current_appointment.get('department_name', 'القسم')
            })
            
        return variables
    
    def send_test_message(self):
        """إرسال رسالة تجريبية"""
        if not self.current_patient or not self.whatsapp_manager:
            logging.warning("⚠️ يرجى اختيار مريض أولاً والتأكد من إعدادات الواتساب")
            return False
        
        try:
            phone = self.current_patient.get('phone')
            message = self.message_preview.toPlainText()
            
            if not phone:
                logging.warning("⚠️ لا يوجد رقم هاتف للمريض المحدد")
                return False
            
            if not message or message.startswith("⚠️"):
                logging.warning("⚠️ يرجى اختيار قالب صحيح أولاً")
                return False
            
            # إرسال الإشارة للملف الرئيسي
            self.test_message_requested.emit(phone, message)
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في الإرسال التجريبي: {e}")
            return False
    
    def update_send_status(self, success, message_type="test"):
        """تحديث حالة الإرسال"""
        if success:
            self.send_status_label.setText("الحالة: ✅ تم الإرسال")
            self.send_time_label.setText(f"الوقت: {datetime.now().strftime('%H:%M')}")
            self.message_type_label.setText(f"نوع الرسالة: {message_type}")
        else:
            self.send_status_label.setText("الحالة: ❌ فشل الإرسال")
    
    def get_whatsapp_data(self):
        """الحصول على بيانات الواتساب"""
        return {
            'send_message': self.auto_send_check.isChecked(),
            'send_reminders': self.auto_reminder_check.isChecked(),
            'template': self.template_combo.currentData(),
            'message_content': self.message_preview.toPlainText()
        }
    
    def setup_combo_style(self, combo):
        """إعداد نمط ComboBox"""
        combo.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                font-size: 12px;
            }
        """)
    
    def get_group_style(self):
        """نمط المجموعات"""
        return """
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #2C3E50;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 6px 0 6px;
                background-color: #3498DB;
                color: white;
                border-radius: 3px;
            }
        """
    
    def get_button_style(self, button_type="primary"):
        """أنماط الأزرار"""
        styles = {
            "primary": """
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 3px;
                    font-size: 11px;
                }
            """,
            "secondary": """
                QPushButton {
                    background-color: #95A5A6;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 3px;
                    font-size: 11px;
                }
            """,
            "info": """
                QPushButton {
                    background-color: #17A2B8;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 3px;
                    font-size: 11px;
                }
            """
        }
        return styles.get(button_type, styles["primary"])