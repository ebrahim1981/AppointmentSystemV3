# -*- coding: utf-8 -*-
import logging
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QMessageBox

class SchedulingIntegration(QObject):
    """نظام تكامل الجدولة الذكية مع النظام الحالي"""
    
    # إشارات النظام
    scheduling_initialized = pyqtSignal(bool)
    available_slots_updated = pyqtSignal(list)
    schedule_conflict_detected = pyqtSignal(dict)
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.is_initialized = False
        self.scheduling_tables_created = False
        
        # تهيئة النظام
        self.initialize_scheduling_system()
        
    def initialize_scheduling_system(self):
        """تهيئة نظام الجدولة الذكية"""
        try:
            logging.info("🔧 جاري تهيئة نظام الجدولة الذكية...")
            
            # 1. إنشاء الجداول إذا لم تكن موجودة
            self.create_scheduling_tables()
            
            # 2. تهيئة البيانات الافتراضية
            self.initialize_default_data()
            
            # 3. التحقق من التكامل مع النظام الحالي
            integration_status = self.check_system_integration()
            
            if integration_status['success']:
                self.is_initialized = True
                self.scheduling_initialized.emit(True)
                logging.info("✅ تم تهيئة نظام الجدولة الذكية بنجاح")
            else:
                logging.warning(f"⚠️ تهيئة النظام مع تحذيرات: {integration_status['warnings']}")
                self.is_initialized = True
                self.scheduling_initialized.emit(True)
                
        except Exception as e:
            logging.error(f"❌ فشل في تهيئة نظام الجدولة: {e}")
            self.scheduling_initialized.emit(False)
            
    def create_scheduling_tables(self):
        """إنشاء جداول الجدولة إذا لم تكن موجودة"""
        try:
            if hasattr(self.db_manager, 'create_scheduling_tables'):
                self.db_manager.create_scheduling_tables()
                self.scheduling_tables_created = True
                logging.info("✅ تم إنشاء جداول الجدولة")
            else:
                logging.warning("⚠️ دالة create_scheduling_tables غير متاحة")
                
        except Exception as e:
            logging.error(f"❌ خطأ في إنشاء جداول الجدولة: {e}")
            
    def initialize_default_data(self):
        """تهيئة البيانات الافتراضية للجدولة"""
        try:
            if hasattr(self.db_manager, 'initialize_default_schedules'):
                self.db_manager.initialize_default_schedules()
                logging.info("✅ تم تهيئة البيانات الافتراضية")
            else:
                logging.warning("⚠️ دالة initialize_default_schedules غير متاحة")
                
        except Exception as e:
            logging.error(f"❌ خطأ في تهيئة البيانات الافتراضية: {e}")
            
    def check_system_integration(self):
        """التحقق من تكامل النظام مع المكونات الحالية"""
        integration_report = {
            'success': True,
            'warnings': [],
            'errors': []
        }
        
        try:
            # التحقق من وجود الدوال الأساسية
            required_functions = [
                'get_available_slots',
                'check_schedule_conflict',
                'get_doctor_schedule_settings'
            ]
            
            for func_name in required_functions:
                if not hasattr(self.db_manager, func_name):
                    integration_report['warnings'].append(f"الدالة {func_name} غير متاحة")
                    integration_report['success'] = False
                    
            # التحقق من الجداول الأساسية
            required_tables = [
                'doctor_schedule_settings',
                'service_types', 
                'schedule_exceptions'
            ]
            
            cursor = self.db_manager.conn.cursor()
            for table in required_tables:
                try:
                    cursor.execute(f"SELECT 1 FROM {table} LIMIT 1")
                except:
                    integration_report['warnings'].append(f"الجدول {table} غير موجود")
                    
            # التحقق من تكامل البيانات مع الأطباء الحاليين
            doctors = self.db_manager.get_doctors()
            if doctors:
                logging.info(f"✅ تم العثور على {len(doctors)} طبيب للتكامل")
            else:
                integration_report['warnings'].append("لا توجد بيانات أطباء للتكامل")
                
            return integration_report
            
        except Exception as e:
            logging.error(f"❌ خطأ في فحص التكامل: {e}")
            integration_report['success'] = False
            integration_report['errors'].append(str(e))
            return integration_report
            
    def integrate_with_appointment_dialog(self, appointment_dialog):
        """تكامل نظام الجدولة مع نافذة المواعيد الحالية"""
        try:
            if not self.is_initialized:
                logging.warning("⚠️ لم يتم تهيئة النظام بعد - تأجيل التكامل")
                return False
                
            # ربط الأحداث والإشارات
            self.connect_appointment_dialog_signals(appointment_dialog)
            
            # إضافة أقسام الجدولة الذكية
            self.add_smart_scheduling_sections(appointment_dialog)
            
            logging.info("✅ تم تكامل نظام الجدولة مع نافذة المواعيد")
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في تكامل نافذة المواعيد: {e}")
            return False
            
    def connect_appointment_dialog_signals(self, dialog):
        """ربط إشارات نافذة المواعيد"""
        try:
            # ربط تغيير الطبيب لتحميل الأوقات المتاحة
            if hasattr(dialog, 'doctor_combo'):
                dialog.doctor_combo.currentIndexChanged.connect(
                    lambda: self.on_doctor_changed_in_dialog(dialog)
                )
                
            # ربط تغيير التاريخ لتحميل الأوقات المتاحة  
            if hasattr(dialog, 'appointment_date'):
                dialog.appointment_date.dateChanged.connect(
                    lambda: self.on_date_changed_in_dialog(dialog)
                )
                
            # ربط التحقق من التعارض قبل الحفظ
            if hasattr(dialog, 'save_appointment'):
                original_save = dialog.save_appointment
                dialog.save_appointment = lambda: self.safe_save_appointment(dialog, original_save)
                
            logging.info("✅ تم ربط إشارات نافذة المواعيد")
            
        except Exception as e:
            logging.error(f"❌ خطأ في ربط الإشارات: {e}")
            
    def add_smart_scheduling_sections(self, dialog):
        """إضافة أقسام الجدولة الذكية للواجهة الحالية"""
        try:
            # هذه الدالة ستضاف لاحقاً بعد تعديل appointment_dialog.py
            if hasattr(dialog, 'setup_smart_scheduling_section'):
                dialog.setup_smart_scheduling_section()
                logging.info("✅ تم إضافة أقسام الجدولة الذكية")
            else:
                logging.warning("⚠️ دالة setup_smart_scheduling_section غير متاحة")
                
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة أقسام الجدولة: {e}")
            
    def on_doctor_changed_in_dialog(self, dialog):
        """عند تغيير الطبيب في نافذة المواعيد"""
        try:
            doctor_id = dialog.doctor_combo.currentData() if hasattr(dialog, 'doctor_combo') else None
            selected_date = dialog.appointment_date.date().toString("yyyy-MM-dd") if hasattr(dialog, 'appointment_date') else None
            
            if doctor_id and selected_date:
                # تحميل الأوقات المتاحة
                available_slots = self.get_available_slots(doctor_id, selected_date)
                
                # تحديث الواجهة إذا كانت الدالة متاحة
                if hasattr(dialog, 'update_available_slots_display'):
                    dialog.update_available_slots_display(available_slots)
                    
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة تغيير الطبيب: {e}")
            
    def on_date_changed_in_dialog(self, dialog):
        """عند تغيير التاريخ في نافذة المواعيد"""
        try:
            doctor_id = dialog.doctor_combo.currentData() if hasattr(dialog, 'doctor_combo') else None
            selected_date = dialog.appointment_date.date().toString("yyyy-MM-dd")
            
            if doctor_id:
                # تحميل الأوقات المتاحة
                available_slots = self.get_available_slots(doctor_id, selected_date)
                
                # تحديث الواجهة إذا كانت الدالة متاحة
                if hasattr(dialog, 'update_available_slots_display'):
                    dialog.update_available_slots_display(available_slots)
                    
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة تغيير التاريخ: {e}")
            
    def safe_save_appointment(self, dialog, original_save_function):
        """حفظ آمن للموعد مع التحقق من التعارض"""
        try:
            # التحقق من التعارض أولاً
            conflict_check = self.check_appointment_conflict(dialog)
            
            if conflict_check['has_conflict']:
                # عرض تحذير التعارض
                response = self.show_conflict_warning(conflict_check)
                
                if response == QMessageBox.Yes:
                    # المتابعة رغم التعارض
                    original_save_function()
                else:
                    # إلغاء الحفظ
                    return
            else:
                # لا يوجد تعارض - المتابعة بالحفظ العادي
                original_save_function()
                
        except Exception as e:
            logging.error(f"❌ خطأ في الحفظ الآمن: {e}")
            # العودة للحفظ العادي في حالة الخطأ
            original_save_function()
            
    def check_appointment_conflict(self, dialog):
        """التحقق من تعارض الموعد"""
        try:
            if not hasattr(dialog, 'get_appointment_data'):
                return {'has_conflict': False, 'message': 'لا يمكن التحقق'}
                
            appointment_data = dialog.get_appointment_data()
            doctor_id = appointment_data.get('doctor_id')
            date = appointment_data.get('appointment_date')
            time = appointment_data.get('appointment_time')
            
            if not all([doctor_id, date, time]):
                return {'has_conflict': False, 'message': 'بيانات ناقصة'}
                
            # استخدام نظام الجدولة للتحقق من التعارض
            if hasattr(self.db_manager, 'check_schedule_conflict'):
                return self.db_manager.check_schedule_conflict(doctor_id, date, time)
            else:
                return {'has_conflict': False, 'message': 'نظام التحقق غير متاح'}
                
        except Exception as e:
            logging.error(f"❌ خطأ في التحقق من التعارض: {e}")
            return {'has_conflict': False, 'message': f'خطأ في التحقق: {e}'}
            
    def show_conflict_warning(self, conflict_info):
        """عرض تحذير التعارض"""
        message = f"""
        ⚠️ تنبيه: تعارض في الموعد!
        
        {conflict_info.get('message', 'هناك تعارض في الموعد المحدد')}
        
        هل تريد المتابعة رغم التعارض؟
        """
        
        return QMessageBox.question(
            None,
            "تعارض في الموعد",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
    def get_available_slots(self, doctor_id, date, service_type=None):
        """الحصول على الأوقات المتاحة - واجهة موحدة"""
        try:
            if hasattr(self.db_manager, 'get_available_slots'):
                return self.db_manager.get_available_slots(doctor_id, date, service_type)
            else:
                logging.warning("⚠️ نظام الأوقات المتاحة غير متاح - استخدام الطريقة التقليدية")
                return self.get_available_slots_fallback(doctor_id, date)
                
        except Exception as e:
            logging.error(f"❌ خطأ في الحصول على الأوقات المتاحة: {e}")
            return []
            
    def get_available_slots_fallback(self, doctor_id, date):
        """طريقة بديلة للحصول على الأوقات المتاحة"""
        try:
            # استخدام البيانات الحالية من جدول المواعيد
            appointments = self.db_manager.get_appointments(doctor_id=doctor_id, date=date)
            
            # أوقات العمل الافتراضية
            work_start = "08:00"
            work_end = "17:00"
            slot_duration = 30
            
            # تحويل الأوقات المشغولة
            booked_slots = []
            for appointment in appointments:
                if appointment.get('appointment_time') and appointment.get('status') not in ['ملغي', 'منتهي']:
                    booked_slots.append(appointment['appointment_time'])
                    
            # توليد الأوقات المتاحة
            from datetime import datetime, timedelta
            available_slots = []
            
            start_time = datetime.strptime(work_start, '%H:%M')
            end_time = datetime.strptime(work_end, '%H:%M')
            
            current_time = start_time
            while current_time < end_time:
                time_str = current_time.strftime('%H:%M')
                
                if time_str not in booked_slots:
                    slot_end = (current_time + timedelta(minutes=slot_duration)).strftime('%H:%M')
                    
                    available_slots.append({
                        'time': time_str,
                        'end_time': slot_end,
                        'duration': slot_duration,
                        'status': 'available',
                        'display': f"{time_str} - {slot_end}"
                    })
                    
                current_time += timedelta(minutes=15)  # كل 15 دقيقة
                
            return available_slots
            
        except Exception as e:
            logging.error(f"❌ خطأ في الطريقة البديلة: {e}")
            return []
            
    def open_smart_scheduling_dialog(self, parent=None):
        """فتح نافذة الجدولة الذكية"""
        try:
            from ui.dialogs.smart_scheduling_dialog import SmartSchedulingDialog
            
            dialog = SmartSchedulingDialog(self.db_manager, parent)
            
            # ربط إشارة اختيار الموعد
            dialog.appointment_selected.connect(self.on_smart_appointment_selected)
            
            return dialog
            
        except ImportError as e:
            logging.error(f"❌ خطأ في فتح نافذة الجدولة الذكية: {e}")
            QMessageBox.warning(parent, "تحذير", "نافذة الجدولة الذكية غير متاحة حالياً")
            return None
            
    def on_smart_appointment_selected(self, appointment_data):
        """عند اختيار موعد من النظام الذكي"""
        try:
            logging.info(f"✅ تم اختيار موعد ذكي: {appointment_data}")
            # يمكن استخدام هذه البيانات لملء نافذة الموعد العادية
            self.available_slots_updated.emit([appointment_data])
            
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة الموعد الذكي: {e}")
            
    def update_doctor_schedule_settings(self, doctor_id, settings):
        """تحديث إعدادات جدول الطبيب"""
        try:
            if hasattr(self.db_manager, 'update_doctor_schedule_settings'):
                return self.db_manager.update_doctor_schedule_settings(doctor_id, settings)
            else:
                logging.warning("⚠️ دالة update_doctor_schedule_settings غير متاحة")
                return False
                
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث إعدادات الطبيب: {e}")
            return False
            
    def get_doctor_schedule_settings(self, doctor_id):
        """الحصول على إعدادات جدول الطبيب"""
        try:
            if hasattr(self.db_manager, 'get_doctor_schedule_settings'):
                return self.db_manager.get_doctor_schedule_settings(doctor_id)
            else:
                logging.warning("⚠️ دالة get_doctor_schedule_settings غير متاحة")
                return None
                
        except Exception as e:
            logging.error(f"❌ خطأ في جلب إعدادات الطبيب: {e}")
            return None
            
    def add_schedule_exception(self, exception_data):
        """إضافة استثناء للجدول"""
        try:
            if hasattr(self.db_manager, 'add_schedule_exception'):
                return self.db_manager.add_schedule_exception(exception_data)
            else:
                logging.warning("⚠️ دالة add_schedule_exception غير متاحة")
                return False
                
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة الاستثناء: {e}")
            return False

# اختبار الملف
if __name__ == "__main__":
    print("✅ تم تحميل scheduling_integration.py بنجاح")