# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QWidget, QMessageBox, QLabel)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QTime
from PyQt5.QtGui import QFont
import logging
from datetime import datetime

# استيراد المكونات المنفصلة
from ui.dialogs.appointment_parts.basic_info_tab import BasicInfoTab
from ui.dialogs.appointment_parts.whatsapp_manager import WhatsAppManager
from ui.dialogs.appointment_parts.history_stats import HistoryStats
from ui.dialogs.appointment_parts.smart_scheduling_ui import SmartSchedulingUI
from ui.dialogs.appointment_parts.controls_status import ControlsStatus

class AppointmentDialog(QDialog):
    # إشارات للنافذة الرئيسية
    appointment_saved = pyqtSignal(dict)
    whatsapp_message_requested = pyqtSignal(dict)
    
    def __init__(self, db_manager, whatsapp_manager=None, parent=None, appointment_data=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.whatsapp_manager = whatsapp_manager
        self.appointment_data = appointment_data
        self.is_edit_mode = appointment_data is not None
        
        # المكونات المنفصلة
        self.basic_info_tab = None
        self.whatsapp_manager_tab = None
        self.history_stats_tab = None
        self.smart_scheduling_ui = None
        self.controls_status = None
        
        self.setup_ui()
        self.setWindowTitle("🔄 تعديل الموعد" if self.is_edit_mode else "➕ إضافة موعد جديد")
        self.setMinimumSize(800, 700)
        self.setModal(True)
        
    def setup_ui(self):
        """إعداد الواجهة الرئيسية باستخدام المكونات المنفصلة"""
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # العنوان الرئيسي
        title = QLabel("🔄 تعديل الموعد" if self.is_edit_mode else "➕ إضافة موعد جديد")
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
                    stop:0 #3498DB, stop:1 #2C3E50);
                color: white;
                border-radius: 8px;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(title)
        
        # تبويبات متعددة
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #BDC3C7;
                border-radius: 6px;
                background-color: #FFFFFF;
            }
            QTabBar::tab {
                background-color: #ECF0F1;
                color: #2C3E50;
                padding: 10px 15px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background-color: #3498DB;
                color: white;
            }
        """)
        
        # إنشاء التبويبات باستخدام المكونات المنفصلة
        self.setup_tabs()
        layout.addWidget(self.tabs)
        
        # إضافة الجدولة الذكية إلى التبويب الأساسي
        self.setup_smart_scheduling()
        
        # أزرار التحكم وشريط الحالة
        self.setup_controls_and_status(layout)
        
        self.setLayout(layout)
        
        # إذا كان في وضع التعديل، تعبئة البيانات
        if self.is_edit_mode:
            QTimer.singleShot(100, self.fill_appointment_data)
    
    def setup_tabs(self):
        """إعداد التبويبات باستخدام المكونات المنفصلة"""
        # تبويب المعلومات الأساسية
        self.basic_info_tab = BasicInfoTab(self.db_manager)
        self.tabs.addTab(self.basic_info_tab, "📋 المعلومات الأساسية")
        
        # تبويب الواتساب
        self.whatsapp_manager_tab = WhatsAppManager(self.db_manager, self.whatsapp_manager)
        self.tabs.addTab(self.whatsapp_manager_tab, "📱 رسائل الواتساب")
        
        # تبويب السجل والإحصائيات
        self.history_stats_tab = HistoryStats(self.db_manager)
        self.tabs.addTab(self.history_stats_tab, "📈 السجل والإحصائيات")
        
        # ربط الإشارات بين المكونات
        self.connect_tabs_signals()
    
    def setup_smart_scheduling(self):
        """إضافة الجدولة الذكية إلى التبويب الأساسي"""
        try:
            self.smart_scheduling_ui = SmartSchedulingUI(self.db_manager)
            
            # إضافة إلى التبويب الأساسي
            basic_info_layout = self.basic_info_tab.layout()
            basic_info_layout.insertWidget(2, self.smart_scheduling_ui)
            
            # ربط الإشارات - ⭐ التصحيح هنا
            self.smart_scheduling_ui.time_selected.connect(self.on_smart_time_selected)
            self.smart_scheduling_ui.availability_updated.connect(self.on_availability_updated)
            
            # ⭐ ربط إشارات الطبيب والتاريخ - التصحيح المهم
            self.basic_info_tab.doctor_changed.connect(self.on_doctor_or_date_changed)
            self.basic_info_tab.date_changed.connect(self.on_doctor_or_date_changed)
            self.basic_info_tab.clinic_changed.connect(self.on_doctor_or_date_changed)
            self.basic_info_tab.department_changed.connect(self.on_doctor_or_date_changed)
            
            logging.info("✅ تم إضافة الجدولة الذكية بنجاح")
            
        except Exception as e:
            logging.error(f"❌ خطأ في إعداد الجدولة الذكية: {e}")
    
    def setup_controls_and_status(self, parent_layout):
        """إعداد أزرار التحكم وشريط الحالة"""
        self.controls_status = ControlsStatus()
        parent_layout.addWidget(self.controls_status)
        
        # ربط إشارات التحكم
        self.controls_status.save_requested.connect(self.save_appointment)
        self.controls_status.save_and_send_requested.connect(lambda: self.save_appointment(send_message=True))
        self.controls_status.cancel_requested.connect(self.reject)
    
    def connect_tabs_signals(self):
        """ربط الإشارات بين المكونات المنفصلة"""
        # ربط اختيار المريض
        self.basic_info_tab.patient_selected.connect(self.on_patient_selected)
        
        # ربط إشارات الواتساب
        self.whatsapp_manager_tab.test_message_requested.connect(self.on_test_message_requested)
        self.whatsapp_manager_tab.template_changed.connect(self.on_template_changed)
    
    def on_patient_selected(self, patient_data):
        """عند اختيار مريض في التبويب الأساسي"""
        try:
            # تحديث الواتساب بالمريض المحدد
            appointment_data = self.get_appointment_form_data()
            self.whatsapp_manager_tab.set_patient_data(patient_data, appointment_data)
            
            # تحديث السجل والإحصائيات
            self.history_stats_tab.set_patient_id(patient_data.get('id'))
            
            # التحقق من صحة النموذج
            self.check_form_validity()
            
            logging.info(f"✅ تم تحديث البيانات للمريض: {patient_data.get('name')}")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث بيانات المريض: {e}")
    
    def on_doctor_or_date_changed(self):
        """عند تغيير الطبيب أو التاريخ - التحديث التلقائي للجدولة"""
        try:
            form_data = self.basic_info_tab.get_form_data()
            doctor_id = form_data.get('doctor_id')
            date = form_data.get('date')
            
            logging.info(f"🔄 تحديث الجدولة - الطبيب: {doctor_id}, التاريخ: {date}")
            
            if doctor_id and date:
                if self.smart_scheduling_ui:
                    self.smart_scheduling_ui.set_doctor_and_date(doctor_id, date)
            else:
                if self.smart_scheduling_ui:
                    self.smart_scheduling_ui.clear_display()
                    
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة تغيير الطبيب/التاريخ: {e}")
    
    def on_smart_time_selected(self, time_str):
        """عند اختيار وقت من الجدولة الذكية"""
        try:
            # تحويل النص إلى وقت وتعيينه في حقل الوقت في التبويب الأساسي
            time_obj = QTime.fromString(time_str, 'HH:mm')
            if time_obj.isValid():
                self.basic_info_tab.appointment_time.setTime(time_obj)
                logging.info(f"✅ تم تعيين الوقت من الجدولة الذكية: {time_str}")
        except Exception as e:
            logging.error(f"❌ خطأ في تعيين الوقت من الجدولة الذكية: {e}")
    
    def on_availability_updated(self, availability_data):
        """عند تحديث الأوقات المتاحة"""
        # يمكن استخدام هذه البيانات للإحصائيات أو التنبيهات
        if availability_data.get('success'):
            available_count = availability_data.get('available_count', 0)
            logging.info(f"📊 الأوقات المتاحة: {available_count}")
    
    def on_test_message_requested(self, phone, message):
        """عند طلب إرسال رسالة تجريبية"""
        try:
            if self.whatsapp_manager:
                success = self.whatsapp_manager.send_message(phone, message, "test")
                self.whatsapp_manager_tab.update_send_status(success, "تجريبي")
                
                if success:
                    QMessageBox.information(self, "نجاح", "✅ تم إرسال الرسالة التجريبية بنجاح!")
                else:
                    QMessageBox.warning(self, "تحذير", "⚠️ فشل في إرسال الرسالة التجريبية")
            else:
                QMessageBox.warning(self, "تحذير", "⚠️ مدير الواتساب غير متوفر")
                
        except Exception as e:
            logging.error(f"❌ خطأ في إرسال الرسالة التجريبية: {e}")
            QMessageBox.critical(self, "خطأ", f"❌ حدث خطأ أثناء الإرسال: {e}")
    
    def on_template_changed(self, template_data):
        """عند تغيير قالب الرسالة"""
        # يمكن إضافة معالجة إضافية هنا إذا لزم الأمر
        pass
    
    def check_form_validity(self):
        """التحقق من صحة النموذج"""
        try:
            form_data = self.basic_info_tab.get_form_data()
            
            is_valid = (
                form_data.get('patient') and 
                form_data.get('clinic_id') and
                form_data.get('department_id') and
                form_data.get('doctor_id')
            )
            
            self.controls_status.set_buttons_enabled(is_valid)
            
            if is_valid:
                self.controls_status.set_status("ready", "✅ النموذج صالح للحفظ")
            else:
                self.controls_status.set_status("warning", "⚠️ يرجى إكمال البيانات المطلوبة")
            
            return is_valid
            
        except Exception as e:
            logging.error(f"❌ خطأ في التحقق من صحة النموذج: {e}")
            return False
    
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
        
        return True
    
    def get_appointment_form_data(self):
        """الحصول على بيانات النموذج من جميع المكونات"""
        basic_data = self.basic_info_tab.get_form_data()
        whatsapp_data = self.whatsapp_manager_tab.get_whatsapp_data()
        
        appointment_data = {
            'patient_id': basic_data['patient']['id'] if basic_data['patient'] else None,
            'patient_name': basic_data['patient']['name'] if basic_data['patient'] else None,
            'patient_phone': basic_data['patient'].get('phone') if basic_data['patient'] else None,
            'patient_country_code': basic_data['patient'].get('country_code', '+966') if basic_data['patient'] else '+966',
            'doctor_id': basic_data['doctor_id'],
            'doctor_name': self.basic_info_tab.doctor_combo.currentText(),
            'department_id': basic_data['department_id'],
            'department_name': self.basic_info_tab.department_combo.currentText(),
            'clinic_id': basic_data['clinic_id'],
            'clinic_name': self.basic_info_tab.clinic_combo.currentText(),
            'appointment_date': basic_data['date'],
            'appointment_time': basic_data['time'],
            'type': basic_data['type'].split(' ', 1)[-1] if basic_data['type'] else '',  # إزالة الرمز
            'status': basic_data['status'].split(' ', 1)[-1] if basic_data['status'] else '',  # إزالة الرمز
            'notes': basic_data['notes'] or None,
            'whatsapp_data': whatsapp_data if self.whatsapp_manager else None
        }
        
        return appointment_data
    
    def fill_appointment_data(self):
        """تعبئة البيانات الحالية للموعد (في وضع التعديل)"""
        if not self.appointment_data:
            return
        
        try:
            # تعبئة البيانات في التبويب الأساسي
            self.basic_info_tab.set_form_data(self.appointment_data)
            
            # تحديث الواتساب والسجل بعد فترة قصيرة
            QTimer.singleShot(200, self.update_after_data_load)
            
            logging.info("✅ تم تحميل بيانات الموعد بنجاح")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تعبئة البيانات: {e}")
    
    def update_after_data_load(self):
        """تحديث المكونات بعد تحميل البيانات"""
        try:
            # تحديث الواتساب
            patient_data = self.basic_info_tab.selected_patient
            if patient_data:
                appointment_data = self.get_appointment_form_data()
                self.whatsapp_manager_tab.set_patient_data(patient_data, appointment_data)
            
            # تحديث السجل
            if patient_data and patient_data.get('id'):
                self.history_stats_tab.set_patient_id(patient_data['id'])
                
        except Exception as e:
            logging.error(f"❌ خطأ في التحديث بعد تحميل البيانات: {e}")
    
    def save_appointment(self, send_message=False):
        """حفظ الموعد"""
        try:
            if not self.validate_inputs():
                return
            
            self.controls_status.set_status("loading", "جاري حفظ الموعد...", "⏳")
            
            appointment_data = self.get_appointment_form_data()
            
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
                if send_message and self.whatsapp_manager:
                    self.send_whatsapp_message(appointment_data)
                
                # إرسال إشارة الحفظ
                self.appointment_saved.emit(appointment_data)
                
                # عرض رسالة النجاح
                self.show_success_message(appointment_data, action)
                
                self.accept()
                
            else:
                self.controls_status.set_status("error", "فشل في حفظ الموعد")
                QMessageBox.critical(self, "خطأ", f"❌ فشل في {action} الموعد")
                
        except Exception as e:
            logging.error(f"❌ خطأ في حفظ الموعد: {e}")
            self.controls_status.set_status("error", f"خطأ في الحفظ: {e}")
            QMessageBox.critical(self, "خطأ", f"❌ حدث خطأ غير متوقع: {e}")
    
    def send_whatsapp_message(self, appointment_data):
        """إرسال رسالة واتساب"""
        try:
            if not self.whatsapp_manager or not appointment_data.get('patient_phone'):
                return
            
            whatsapp_data = self.whatsapp_manager_tab.get_whatsapp_data()
            message_content = whatsapp_data.get('message_content', '')
            
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
                logging.info(f"✅ تم إرسال رسالة واتساب للموعد {appointment_data['id']}")
            else:
                logging.error(f"❌ فشل إرسال رسالة واتساب للموعد {appointment_data['id']}")
                
        except Exception as e:
            logging.error(f"❌ خطأ في إرسال رسالة واتساب: {e}")
    
    def show_success_message(self, appointment_data, action):
        """عرض رسالة النجاح"""
        success_msg = f"""
        ✅ تم {action} الموعد بنجاح!

        📋 معلومات الموعد:
        • المريض: {appointment_data['patient_name']}
        • الطبيب: {appointment_data['doctor_name']}
        • التاريخ: {appointment_data['appointment_date']}
        • الوقت: {appointment_data['appointment_time']}
        • الحالة: {appointment_data['status']}
        """
        
        whatsapp_data = self.whatsapp_manager_tab.get_whatsapp_data()
        if whatsapp_data.get('send_message') and self.whatsapp_manager:
            success_msg += "\n📱 تم إرسال رسالة الترحيب تلقائياً للمريض"
        
        QMessageBox.information(self, "نجاح", success_msg)