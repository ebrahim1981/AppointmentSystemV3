# notifications/auto_sender.py - الإصدار النهائي المصحح والمتكامل
# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from PyQt5.QtWidgets import QMessageBox

class AutoSender(QObject):
    """نظام الإرسال التلقائي الموحد - الإصدار النهائي المصحح والمتكامل"""

    # إشارات النظام
    reminder_sent = pyqtSignal(dict)
    reminder_failed = pyqtSignal(dict)
    quick_test_started = pyqtSignal()
    quick_test_completed = pyqtSignal()
    status_changed = pyqtSignal(str)
    log_updated = pyqtSignal(str)

    def __init__(self, db_manager, main_window=None):
        super().__init__()
        self.db_manager = db_manager
        self.main_window = main_window
        self.whatsapp_sender = None
        self.is_running = False
        self.sent_count = 0
        self.quick_test_mode = False
        
        # ⭐⭐ تهيئة متقدمة مع WhatsAppManager ⭐⭐
        self.setup_whatsapp_integration()
        self.setup_timers()
        self.connect_signals()
        
        self.add_log("🚀 AutoSender المتكامل النهائي جاهز للتشغيل")

    def setup_whatsapp_integration(self):
        """تهيئة تكامل الواتساب بشكل متقدم"""
        try:
            from whatsapp.whatsapp_manager import WhatsAppManager
            
            # ⭐⭐ استخدام النسخة العالمية مع التعامل الآمن ⭐⭐
            self.whatsapp_sender = WhatsAppManager.get_global_instance()
            
            if self.whatsapp_sender is None:
                self.add_log("🔄 لا توجد نسخة عالمية - جاري إنشاء مدير واتساب جديد...")
                self.whatsapp_sender = WhatsAppManager(self.db_manager, None, 1)
                WhatsAppManager.set_global_instance(self.whatsapp_sender)
                self.add_log("✅ تم إنشاء وتثبيت نسخة عالمية جديدة")
            else:
                self.add_log("✅ AutoSender يستخدم النسخة العالمية من WhatsAppManager")
            
            # ⭐⭐ التحقق من اتصال الواتساب فوراً ⭐⭐
            connection_result = self.whatsapp_sender.check_connection()
            if connection_result.get('success'):
                self.add_log("📱 اتصال الواتساب نشط وجاهز")
            else:
                self.add_log(f"⚠️ تحذير اتصال الواتساب: {connection_result.get('message')}")
                
        except ImportError as e:
            self.add_log(f"❌ خطأ استيراد: WhatsAppManager غير موجود - {e}")
        except Exception as e:
            self.add_log(f"❌ فشل تكامل الواتساب: {e}")

    def setup_timers(self):
        """إعداد المؤقتات المتقدمة"""
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self.check_all_reminders)
        self.reminder_timer.start(60000)  # كل دقيقة
        
        # مؤقت مراقبة الاتصال
        self.connection_monitor = QTimer()
        self.connection_monitor.timeout.connect(self.monitor_connection)
        self.connection_monitor.start(30000)  # كل 30 ثانية
        
        self.add_log("⏰ تم تفعيل المؤقتات - فحص كل دقيقة، مراقبة اتصال كل 30 ثانية")

    def connect_signals(self):
        """ربط إشارات النظام بشكل متقدم"""
        try:
            if self.whatsapp_sender:
                # ⭐⭐ ربط إشارات WhatsAppManager بشكل آمن ⭐⭐
                self.whatsapp_sender.connection_status_changed.connect(self.on_connection_status_changed)
                self.whatsapp_sender.message_sent.connect(self.on_message_sent)
                self.whatsapp_sender.message_failed.connect(self.on_message_failed)
                self.add_log("✅ تم ربط إشارات WhatsAppManager بنجاح")
        except Exception as e:
            self.add_log(f"⚠️ فشل ربط بعض الإشارات: {e}")

    def add_log(self, message):
        """إضافة رسالة للسجل وإرسال إشارة"""
        log_entry = f"{datetime.now().strftime('%H:%M:%S')} - {message}"
        logging.info(log_entry)
        self.log_updated.emit(log_entry)

    # 🔥 دوال التوافق المطلوبة لحل الأخطاء
    def send_24h_reminders(self):
        """دالة توافقية للكود القديم - تستدعي check_24h_reminders"""
        try:
            self.add_log("🔄 استدعاء واجهة التوافق: send_24h_reminders -> check_24h_reminders")
            return self.check_24h_reminders()
        except Exception as e:
            self.add_log(f"❌ خطأ في send_24h_reminders: {e}")
            return False

    def send_2h_reminders(self):
        """دالة توافقية للكود القديم - تستدعي check_2h_reminders"""
        try:
            self.add_log("🔄 استدعاء واجهة التوافق: send_2h_reminders -> check_2h_reminders")
            return self.check_2h_reminders()
        except Exception as e:
            self.add_log(f"❌ خطأ في send_2h_reminders: {e}")
            return False

    def setup_senders(self):
        """دالة التوافق - لا تفعل شيء"""
        self.add_log("🔄 استدعاء واجهة التوافق: setup_senders")
        pass

    def process_scheduled_notifications(self):
        """معالجة الإشعارات المجدولة - دالة توافقية"""
        self.add_log("🔄 استدعاء واجهة التوافق: process_scheduled_notifications")
        return self.check_all_reminders()

    def send_scheduled_notifications(self):
        """إرسال الإشعارات المجدولة - دالة توافقية"""
        self.add_log("🔄 استدعاء واجهة التوافق: send_scheduled_notifications")
        return self.process_scheduled_notifications()

    # 🔄 دوال التحكم الرئيسية المتقدمة
    def start_auto_sender(self):
        """بدء النظام التلقائي - النسخة المتقدمة"""
        try:
            if self.is_running:
                self.add_log("⚠️ النظام يعمل بالفعل")
                return False

            # ⭐⭐ التحقق المتقدم من اتصال الواتساب أولاً ⭐⭐
            if not self.whatsapp_sender:
                self.add_log("❌ لا يمكن بدء النظام - WhatsAppManager غير متوفر")
                return False

            connection_check = self.whatsapp_sender.check_connection()
            if not connection_check.get('success'):
                self.add_log(f"❌ لا يمكن بدء النظام - الواتساب غير متصل: {connection_check.get('message')}")
                return False

            self.is_running = True
            self.quick_test_mode = False
            self.add_log("🚀 بدء نظام الإرسال التلقائي المتكامل")
            self.status_changed.emit("نشط")
            
            # فحص فوري شامل عند البدء
            self.check_all_reminders()
            
            return True
        except Exception as e:
            self.add_log(f"❌ خطأ في بدء النظام التلقائي: {e}")
            return False

    def stop_auto_sender(self):
        """إيقاف النظام التلقائي"""
        try:
            if not self.is_running:
                self.add_log("⚠️ النظام متوقف بالفعل")
                return False

            self.is_running = False
            self.quick_test_mode = False
            self.add_log("⏹️ إيقاف نظام الإرسال التلقائي")
            self.status_changed.emit("متوقف")
            return True
        except Exception as e:
            self.add_log(f"❌ خطأ في إيقاف النظام التلقائي: {e}")
            return False

    def start_quick_test(self):
        """بدء اختبار سريع متقدم"""
        try:
            self.add_log("🧪 بدء الاختبار السريع المتقدم...")
            self.quick_test_started.emit()
            
            # التحقق من اتصال الواتساب أولاً
            if not self.whatsapp_sender:
                self.add_log("❌ فشل الاختبار - WhatsAppManager غير متوفر")
                return False

            connection_check = self.whatsapp_sender.check_connection()
            if not connection_check.get('success'):
                self.add_log(f"❌ فشل الاختبار - الواتساب غير متصل: {connection_check.get('message')}")
                return False

            # تفعيل وضع الاختبار السريع
            self.quick_test_mode = True
            self.is_running = True
            
            self.add_log("🔧 تفعيل وضع الاختبار السريع المتقدم (دقائق بدلاً من ساعات)")
            self.status_changed.emit("اختبار")
            
            # إنشاء موعد اختبار بعد 6 دقائق
            test_appointment_id = self.create_test_appointment()
            if test_appointment_id:
                self.add_log(f"✅ تم إنشاء موعد اختبار #{test_appointment_id}")
                self.add_log("📱 ستصلك رسالتين خلال 6 دقائق:")
                self.add_log("   - الأولى بعد 5 دقائق (محاكاة تذكير 24 ساعة)")
                self.add_log("   - الثانية بعد 1 دقيقة (محاكاة تذكير ساعتين)")
                
                # بدء الفحص الفوري
                self.check_quick_reminders()
            else:
                self.add_log("❌ فشل إنشاء موعد اختبار")
            
            self.quick_test_completed.emit()
            return True
            
        except Exception as e:
            self.add_log(f"❌ خطأ في الاختبار السريع: {e}")
            return False

    def create_test_appointment(self):
        """إنشاء موعد تجريبي للاختبار - النسخة المتقدمة"""
        try:
            # حساب وقت الموعد بعد 6 دقائق
            appointment_time = (datetime.now() + timedelta(minutes=6)).strftime('%H:%M')
            appointment_date = datetime.now().strftime('%Y-%m-%d')
            
            # إنشاء مريض تجريبي
            patient_id = self.create_test_patient()
            if not patient_id:
                return None
            
            # إنشاء الموعد
            appointment_data = {
                'patient_id': patient_id,
                'doctor_id': self.get_first_doctor(),
                'department_id': self.get_first_department(),
                'clinic_id': 1,
                'appointment_date': appointment_date,
                'appointment_time': appointment_time,
                'type': 'كشف',
                'status': 'مجدول',
                'notes': 'موعد اختبار حقيقي لنظام التذكير التلقائي - AutoSender المتكامل'
            }
            
            if hasattr(self.db_manager, 'add_appointment'):
                appointment_id = self.db_manager.add_appointment(appointment_data)
                self.add_log(f"✅ تم إنشاء موعد اختبار #{appointment_id} للوقت {appointment_time}")
                return appointment_id
            return None
                
        except Exception as e:
            self.add_log(f"❌ خطأ في إنشاء موعد اختبار: {e}")
            return None

    def create_test_patient(self):
        """إنشاء مريض تجريبي - النسخة المحسنة"""
        try:
            # البحث عن مريض اختبار موجود أولاً
            if hasattr(self.db_manager, 'get_patients'):
                patients = self.db_manager.get_patients()
                for patient in patients:
                    if any(keyword in patient.get('name', '') for keyword in ['اختبار', 'تجريبي', 'test']):
                        self.add_log(f"✅ استخدام مريض اختبار موجود: {patient.get('name')}")
                        return patient['id']
            
            # إنشاء مريض جديد
            if hasattr(self.db_manager, 'add_patient'):
                patient_data = {
                    'name': 'مريض اختبار التذكير التلقائي - AutoSender',
                    'phone': '0555555555',
                    'country_code': '+966',
                    'email': 'test@autosender.com',
                    'gender': 'ذكر',
                    'address': 'عنوان اختبار نظام AutoSender المتكامل'
                }
                patient_id = self.db_manager.add_patient(patient_data)
                self.add_log(f"✅ تم إنشاء مريض اختبار جديد #{patient_id}")
                return patient_id
            return None
        except Exception as e:
            self.add_log(f"❌ فشل إنشاء مريض تجريبي: {e}")
            return None

    def get_first_doctor(self):
        """الحصول على أول طبيب متوفر"""
        try:
            if hasattr(self.db_manager, 'get_doctors'):
                doctors = self.db_manager.get_doctors()
                if doctors:
                    return doctors[0]['id']
            return 1
        except Exception as e:
            self.add_log(f"⚠️ استخدام الطبيب الافتراضي بسبب: {e}")
            return 1

    def get_first_department(self):
        """الحصول على أول قسم متوفر"""
        try:
            if hasattr(self.db_manager, 'get_departments'):
                departments = self.db_manager.get_departments()
                if departments:
                    return departments[0]['id']
            return 1
        except Exception as e:
            self.add_log(f"⚠️ استخدام القسم الافتراضي بسبب: {e}")
            return 1

    # 🔥 دوال التذكيرات الحقيقية المتكاملة
    def check_all_reminders(self):
        """فحص جميع التذكيرات - الإصدار المتكامل"""
        try:
            if not self.is_running:
                return
                
            # ⭐⭐ التحقق المتقدم من اتصال الواتساب ⭐⭐
            if not self.whatsapp_sender:
                self.add_log("⚠️ تخطي الفحص - WhatsAppManager غير متوفر")
                return

            connection_check = self.whatsapp_sender.check_connection()
            if not connection_check.get('success'):
                self.add_log(f"⚠️ تخطي الفحص - الواتساب غير متصل: {connection_check.get('message')}")
                return

            self.add_log("🔄 فحص التذكيرات التلقائية المتكاملة...")
            self.status_changed.emit("يعمل")
            
            if self.quick_test_mode:
                self.check_quick_reminders()
            else:
                # ⭐⭐ الفحص المتوازي لكلا النوعين ⭐⭐
                self.check_24h_reminders()
                self.check_2h_reminders()
                
            self.add_log("✅ اكتمل فحص التذكيرات المتكاملة")
                
        except Exception as e:
            self.add_log(f"❌ خطأ في فحص التذكيرات: {e}")
            self.status_changed.emit("خطأ")

    def check_quick_reminders(self):
        """فحص التذكيرات السريعة للاختبار - النسخة المتكاملة"""
        try:
            # تذكير بعد 5 دقائق (بدلاً من 24 ساعة)
            quick_5min_result = self.send_quick_reminders(minutes=5, reminder_type="quick_5min")
            
            # تذكير بعد 1 دقيقة (بدلاً من ساعتين)
            quick_1min_result = self.send_quick_reminders(minutes=1, reminder_type="quick_1min")
            
            if quick_5min_result or quick_1min_result:
                self.add_log("🎉 اكتمل إرسال تذكيرات الاختبار السريع")
            else:
                self.add_log("ℹ️ لم يتم إرسال أي تذكيرات اختبار سريع")
            
        except Exception as e:
            self.add_log(f"❌ خطأ في التذكيرات السريعة: {e}")

    def send_quick_reminders(self, minutes=5, reminder_type="quick_5min"):
        """إرسال تذكيرات سريعة للاختبار - النسخة المتكاملة"""
        try:
            if not self.whatsapp_sender:
                self.add_log("⚠️ نظام الواتساب غير متوفر للتذكيرات السريعة")
                return False

            # حساب الوقت المستهدف
            target_time = datetime.now() + timedelta(minutes=minutes)
            target_date = target_time.strftime('%Y-%m-%d')
            target_hour = target_time.strftime('%H:%M')

            # البحث عن مواعيد الاختبار
            appointments = self.get_test_appointments(target_date, target_hour)
            
            if not appointments:
                self.add_log(f"ℹ️ لا توجد مواعيد اختبار للوقت {target_hour}")
                return False

            sent_count = 0
            for appointment in appointments:
                try:
                    patient_name = appointment.get('patient_name', 'مريض اختبار')
                    patient_phone = appointment.get('patient_phone', '')
                    
                    if not patient_phone:
                        self.add_log(f"⚠️ تخطي الموعد {appointment['id']} - لا يوجد رقم هاتف")
                        continue

                    # إنشاء رسالة التذكير
                    message = self.create_quick_reminder_message(
                        patient_name, 
                        appointment.get('appointment_time', ''),
                        minutes,
                        reminder_type
                    )
                    
                    # إرسال الرسالة الحقيقية عبر WhatsAppManager
                    result = self.whatsapp_sender.send_message(
                        patient_phone, 
                        message, 
                        f"reminder_{reminder_type}",
                        appointment_id=appointment['id'],
                        patient_id=appointment.get('patient_id')
                    )
                    
                    if result.get('success'):
                        sent_count += 1
                        self.add_log(f"✅ تم إرسال تذكير {reminder_type} لـ {patient_name}")
                        
                        self.reminder_sent.emit({
                            'patient_name': patient_name,
                            'reminder_type': reminder_type,
                            'appointment_id': appointment['id'],
                            'phone': patient_phone
                        })
                    else:
                        error_msg = result.get('message', 'فشل غير معروف')
                        self.add_log(f"❌ فشل إرسال تذكير لـ {patient_name}: {error_msg}")
                        self.reminder_failed.emit({
                            'patient_name': patient_name,
                            'reminder_type': reminder_type,
                            'error': error_msg,
                            'phone': patient_phone
                        })
                        
                except Exception as e:
                    self.add_log(f"❌ خطأ في إرسال تذكير: {e}")
                    self.reminder_failed.emit({
                        'patient_name': appointment.get('patient_name', 'مريض'),
                        'reminder_type': reminder_type,
                        'error': str(e)
                    })
            
            if sent_count > 0:
                self.add_log(f"📤 تم إرسال {sent_count} تذكير {reminder_type}")
                return True
            else:
                self.add_log(f"⚠️ لم يتم إرسال أي تذكير {reminder_type}")
                return False
            
        except Exception as e:
            self.add_log(f"❌ فشل في إرسال التذكيرات السريعة: {e}")
            return False

    def get_test_appointments(self, target_date, target_hour):
        """الحصول على مواعيد الاختبار - النسخة المحسنة"""
        try:
            appointments = []
            if hasattr(self.db_manager, 'get_appointments'):
                all_appointments = self.db_manager.get_appointments(date=target_date)
                for appointment in all_appointments:
                    if (appointment.get('appointment_time') == target_hour and 
                        any(keyword in appointment.get('patient_name', '') for keyword in ['اختبار', 'تجريبي', 'test'])):
                        appointments.append(appointment)
            
            self.add_log(f"🔍 تم العثور على {len(appointments)} موعد اختبار للوقت {target_hour}")
            return appointments
        except Exception as e:
            self.add_log(f"❌ خطأ في جلب مواعيد الاختبار: {e}")
            return []

    def create_quick_reminder_message(self, patient_name, appointment_time, minutes, reminder_type):
        """إنشاء رسالة تذكير سريعة - النسخة المحسنة"""
        if reminder_type == "quick_5min":
            return f"""
⏰ تذكير بالموعد - اختبار نظام AutoSender المتكامل

عزيزي/عزيزتي {patient_name},

هذا اختبار حقيقي لنظام التذكير التلقائي المتكامل.
سيتم إرسال تذكير آخر قبل موعدك بدقيقة واحدة.

موعدك: {appointment_time}
الوقت المتبقي: 5 دقائق

شكراً لتفهمك 🤝
            """.strip()
        else:  # quick_1min
            return f"""
🔔 تذكير فوري - اختبار نظام AutoSender المتكامل

عزيزي/عزيزتي {patient_name},

موعدك بعد دقيقة واحدة!
هذا اختبار حقيقي لنظام التذكير التلقائي المتكامل.

الوقت: {appointment_time}
الحالة: جاهز للاستقبال

نترقب زيارتكم 👨‍⚕️
            """.strip()

    def check_24h_reminders(self):
        """فحص تذكيرات 24 ساعة - الإصدار المتكامل"""
        try:
            if not self.whatsapp_sender:
                self.add_log("⚠️ نظام الواتساب غير متوفر لتذكيرات 24 ساعة")
                return False

            # حساب الوقت بعد 24 ساعة
            target_date = (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d')
            
            self.add_log(f"🔍 البحث عن مواعيد بعد 24 ساعة لتاريخ {target_date}")
            
            # الحصول على المواعيد بعد 24 ساعة
            if hasattr(self.db_manager, 'get_appointments'):
                appointments = self.db_manager.get_appointments(date=target_date)
            else:
                self.add_log("❌ db_manager لا يدعم get_appointments")
                return False
            
            sent_count = 0
            total_appointments = len(appointments)
            
            for appointment in appointments:
                try:
                    if not appointment.get('reminder_24h_sent'):
                        patient_name = appointment.get('patient_name', 'مريض')
                        self.add_log(f"🔄 معالجة تذكير 24 ساعة للموعد {appointment['id']} - {patient_name}")
                        
                        result = self.whatsapp_sender.send_appointment_reminder(
                            appointment['id'], 
                            "24h"
                        )
                        
                        if result:
                            sent_count += 1
                            self.add_log(f"✅ تم إرسال تذكير 24 ساعة للموعد {appointment['id']}")
                            
                            self.reminder_sent.emit({
                                'patient_name': patient_name,
                                'reminder_type': '24h',
                                'appointment_id': appointment['id']
                            })
                        else:
                            self.add_log(f"❌ فشل إرسال تذكير 24 ساعة للموعد {appointment['id']}")
                            self.reminder_failed.emit({
                                'patient_name': patient_name,
                                'reminder_type': '24h',
                                'error': 'فشل الإرسال',
                                'appointment_id': appointment['id']
                            })
                    else:
                        self.add_log(f"ℹ️ تخطي الموعد {appointment['id']} - تم إرسال التذكير مسبقاً")
                except Exception as e:
                    self.add_log(f"❌ خطأ في إرسال تذكير 24 ساعة: {e}")
                    self.reminder_failed.emit({
                        'patient_name': appointment.get('patient_name', 'مريض'),
                        'reminder_type': '24h',
                        'error': str(e),
                        'appointment_id': appointment.get('id')
                    })
            
            if sent_count > 0:
                self.add_log(f"📤 تم إرسال {sent_count} من أصل {total_appointments} تذكير 24 ساعة")
            else:
                self.add_log(f"ℹ️ لم يتم إرسال أي تذكيرات 24 ساعة من أصل {total_appointments} موعد")
            
            return sent_count > 0
            
        except Exception as e:
            self.add_log(f"❌ فشل في فحص تذكيرات 24 ساعة: {e}")
            return False

    def check_2h_reminders(self):
        """فحص تذكيرات ساعتين - الإصدار المتكامل"""
        try:
            if not self.whatsapp_sender:
                self.add_log("⚠️ نظام الواتساب غير متوفر لتذكيرات ساعتين")
                return False

            # حساب الوقت بعد ساعتين
            target_time = datetime.now() + timedelta(hours=2)
            target_date = target_time.strftime('%Y-%m-%d')
            target_hour = target_time.strftime('%H:%M')
            
            self.add_log(f"🔍 البحث عن مواعيد بعد ساعتين للوقت {target_hour}")
            
            # الحصول على المواعيد بعد ساعتين
            if hasattr(self.db_manager, 'get_appointments'):
                appointments = self.db_manager.get_appointments(date=target_date)
            else:
                self.add_log("❌ db_manager لا يدعم get_appointments")
                return False
            
            sent_count = 0
            matching_appointments = 0
            
            for appointment in appointments:
                try:
                    if (appointment.get('appointment_time') == target_hour and 
                        not appointment.get('reminder_2h_sent')):
                        
                        matching_appointments += 1
                        patient_name = appointment.get('patient_name', 'مريض')
                        self.add_log(f"🔄 معالجة تذكير ساعتين للموعد {appointment['id']} - {patient_name}")
                        
                        result = self.whatsapp_sender.send_appointment_reminder(
                            appointment['id'], 
                            "2h"
                        )
                        
                        if result:
                            sent_count += 1
                            self.add_log(f"✅ تم إرسال تذكير ساعتين للموعد {appointment['id']}")
                            
                            self.reminder_sent.emit({
                                'patient_name': patient_name,
                                'reminder_type': '2h',
                                'appointment_id': appointment['id']
                            })
                        else:
                            self.add_log(f"❌ فشل إرسال تذكير ساعتين للموعد {appointment['id']}")
                            self.reminder_failed.emit({
                                'patient_name': patient_name,
                                'reminder_type': '2h',
                                'error': 'فشل الإرسال',
                                'appointment_id': appointment['id']
                            })
                    else:
                        if appointment.get('appointment_time') == target_hour:
                            self.add_log(f"ℹ️ تخطي الموعد {appointment['id']} - تم إرسال التذكير مسبقاً")
                except Exception as e:
                    self.add_log(f"❌ خطأ في إرسال تذكير ساعتين: {e}")
                    self.reminder_failed.emit({
                        'patient_name': appointment.get('patient_name', 'مريض'),
                        'reminder_type': '2h',
                        'error': str(e),
                        'appointment_id': appointment.get('id')
                    })
            
            if sent_count > 0:
                self.add_log(f"📤 تم إرسال {sent_count} من أصل {matching_appointments} تذكير ساعتين")
            else:
                self.add_log(f"ℹ️ لم يتم إرسال أي تذكيرات ساعتين من أصل {matching_appointments} موعد متطابق")
            
            return sent_count > 0
            
        except Exception as e:
            self.add_log(f"❌ فشل في فحص تذكيرات ساعتين: {e}")
            return False

    # 🔄 معالجات الإشارات المتقدمة
    def on_connection_status_changed(self, status):
        """معالجة تغيير حالة الاتصال - النسخة المتقدمة"""
        status_text = "🟢 متصل" if status == "connected" else "🔴 غير متصل"
        self.add_log(f"📡 حالة الاتصال: {status_text}")
        self.status_changed.emit(status)

    def on_message_sent(self, data):
        """معالجة إرسال الرسالة بنجاح - النسخة المتقدمة"""
        try:
            phone = data.get('phone', '')
            message_type = data.get('type', 'reminder')
            self.sent_count += 1
            
            self.add_log(f"✅ تم إرسال رسالة {message_type} إلى {phone}")
            
            if data.get('appointment_id'):
                self.reminder_sent.emit({
                    'patient_name': f"مريض {phone}",
                    'reminder_type': message_type,
                    'appointment_id': data.get('appointment_id'),
                    'phone': phone,
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                })
        except Exception as e:
            self.add_log(f"❌ خطأ في معالجة الإرسال الناجح: {e}")

    def on_message_failed(self, data):
        """معالجة فشل إرسال الرسالة - النسخة المتقدمة"""
        try:
            phone = data.get('phone', '')
            error = data.get('error', '')
            message_type = data.get('type', 'reminder')
            
            self.add_log(f"❌ فشل إرسال رسالة {message_type} إلى {phone}: {error}")
            
            if data.get('appointment_id'):
                self.reminder_failed.emit({
                    'patient_name': f"مريض {phone}",
                    'reminder_type': message_type,
                    'error': error,
                    'phone': phone,
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                })
        except Exception as e:
            self.add_log(f"❌ خطأ في معالجة الفشل: {e}")

    def monitor_connection(self):
        """مراقبة اتصال النظام"""
        try:
            if self.is_running and self.whatsapp_sender:
                connection_status = self.whatsapp_sender.is_connected
                if not connection_status:
                    self.add_log("⚠️ مراقبة الاتصال: فقدان الاتصال بالواتساب")
                    # يمكن إضافة محاولة إعادة الاتصال تلقائياً هنا
        except Exception as e:
            self.add_log(f"⚠️ خطأ في مراقبة الاتصال: {e}")

    def get_status(self):
        """الحصول على حالة النظام - النسخة المتقدمة"""
        try:
            whatsapp_connected = self.whatsapp_sender is not None and getattr(self.whatsapp_sender, 'is_connected', False)
            whatsapp_status = "🟢 متصل" if whatsapp_connected else "🔴 غير متصل"
            
            return {
                'is_running': self.is_running,
                'check_interval': 1,
                'last_check_time': datetime.now().strftime('%H:%M:%S'),
                'sent_count': self.sent_count,
                'whatsapp_connected': whatsapp_connected,
                'whatsapp_status': whatsapp_status,
                'quick_test_mode': self.quick_test_mode,
                'system_status': 'نشط' if self.is_running else 'متوقف',
                'db_connected': self.db_manager is not None
            }
        except Exception as e:
            self.add_log(f"❌ خطأ في الحصول على الحالة: {e}")
            return {
                'is_running': False,
                'check_interval': 0,
                'last_check_time': 'خطأ',
                'sent_count': 0,
                'whatsapp_connected': False,
                'whatsapp_status': 'غير معروف',
                'quick_test_mode': False,
                'system_status': 'خطأ',
                'db_connected': False
            }

    def update_ui_info(self, main_app):
        """تحديث معلومات الواجهة - النسخة المتكاملة"""
        try:
            status = self.get_status()
            
            info_text = f"""
🤖 نظام الإرسال التلقائي المتكامل - AutoSender

📊 الحالة: {'🟢 نشط' if status['is_running'] else '🔴 متوقف'}
🎯 الوضع: {'🧪 اختبار سريع' if status['quick_test_mode'] else '⚡ تشغيل عادي'}
⏰ فترة الفحص: كل {status['check_interval']} دقيقة
🔄 آخر فحص: {status['last_check_time']}
📤 عدد الرسائل المرسلة: {status['sent_count']}
📱 حالة الواتساب: {status['whatsapp_status']}
💾 قاعدة البيانات: {'🟢 متصل' if status['db_connected'] else '🔴 غير متصل'}

💡 الميزات المتوفرة:
• ✅ تذكيرات المواعيد التلقائية (24 ساعة)
• ⏰ تذكيرات المواعيد التلقائية (ساعتين)  
• 🔄 فحص دوري كل دقيقة
• 🧪 نظام اختبار سريع متكامل
• 📱 تكامل كامل مع WhatsAppManager
• 🔍 مراقبة اتصال مستمرة
"""
            
            if hasattr(main_app, 'auto_sender_info'):
                main_app.auto_sender_info.setText(info_text)
            
            # تحديث الإحصائيات الحية
            stats_text = f"""
📈 إحصائيات حية - النظام المتكامل:

• 🏥 عدد المواعيد اليوم: {len(main_app.get_today_appointments()) if hasattr(main_app, 'get_today_appointments') else 'غير متوفر'}
• 📱 حالة الواتساب: {status['whatsapp_status']}
• 🤖 حالة التلقائي: {'🟢 نشط' if status['is_running'] else '🔴 متوقف'}
• 📤 رسائل مرسلة: {status['sent_count']}
• ⏰ وقت التشغيل: {datetime.now().strftime('%H:%M:%S')}
• 🎯 وضع التشغيل: {'اختبار سريع' if status['quick_test_mode'] else 'عادي'}
• 💾 قاعدة البيانات: {'🟢 متصل' if status['db_connected'] else '🔴 غير متصل'}
• 🔄 آخر فحص: {status['last_check_time']}
"""
            
            if hasattr(main_app, 'auto_sender_stats'):
                main_app.auto_sender_stats.setText(stats_text)
            
        except Exception as e:
            self.add_log(f"❌ خطأ في تحديث الواجهة: {e}")

    def get_detailed_status(self):
        """الحصول على حالة مفصلة للنظام"""
        status = self.get_status()
        
        detailed_status = {
            'system': {
                'name': 'AutoSender المتكامل',
                'version': '2.0.0',
                'status': status['system_status'],
                'running': status['is_running'],
                'quick_test': status['quick_test_mode']
            },
            'whatsapp': {
                'connected': status['whatsapp_connected'],
                'status': status['whatsapp_status'],
                'manager_available': self.whatsapp_sender is not None
            },
            'database': {
                'connected': status['db_connected'],
                'manager_available': self.db_manager is not None
            },
            'performance': {
                'check_interval': status['check_interval'],
                'last_check': status['last_check_time'],
                'messages_sent': status['sent_count'],
                'uptime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'timers': {
                'reminder_timer': self.reminder_timer.isActive() if hasattr(self, 'reminder_timer') else False,
                'connection_monitor': self.connection_monitor.isActive() if hasattr(self, 'connection_monitor') else False
            }
        }
        
        return detailed_status

# نموذج استخدام سريع للاختبار
if __name__ == "__main__":
    print("🧪 اختبار AutoSender المتكامل...")
    
    class MockDBManager:
        def get_appointments(self, date=None):
            return []
        
        def get_patients(self):
            return []
        
        def add_patient(self, data):
            return 1
            
        def add_appointment(self, data):
            return 1
            
        def get_doctors(self):
            return [{'id': 1, 'name': 'طبيب اختبار'}]
            
        def get_departments(self):
            return [{'id': 1, 'name': 'قسم اختبار'}]
    
    # اختبار بسيط
    db_mock = MockDBManager()
    auto_sender = AutoSender(db_mock)
    
    print("✅ AutoSender المتكامل جاهز للاستخدام!")
    print("🎯 الميزات المتوفرة:")
    print("   - تذكيرات 24 ساعة تلقائية")
    print("   - تذكيرات ساعتين تلقائية") 
    print("   - نظام اختبار سريع متكامل")
    print("   - تكامل كامل مع WhatsAppManager")
    print("   - مراقبة اتصال مستمرة")