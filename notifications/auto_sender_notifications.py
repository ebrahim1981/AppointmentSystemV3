# notifications/auto_sender.py
# -*- coding: utf-8 -*-
import logging
import sqlite3
from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

class AutoSender(QObject):
    """نظام الإرسال التلقائي الحقيقي - الإصدار العملي المتكامل"""

    # 🔥 إضافة إشارات جديدة للتكامل
    reminder_sent = pyqtSignal(dict)
    reminder_failed = pyqtSignal(dict)
    quick_test_started = pyqtSignal()
    quick_test_completed = pyqtSignal()
    status_changed = pyqtSignal(str)

    def __init__(self, db_manager, main_window=None):
        super().__init__()
        self.db_manager = db_manager
        self.main_window = main_window
        self.whatsapp_sender = None
        self.test_mode = False
        self.quick_test_mode = False
        self.is_running = False
        
        # 🔥 استخدام النسخة العالمية من WhatsAppManager
        try:
            from whatsapp.whatsapp_manager import WhatsAppManager
            self.whatsapp_sender = WhatsAppManager.get_global_instance()
            
            if self.whatsapp_sender is None:
                logging.warning("⚠️ لا توجد نسخة عالمية - جاري إنشاء واحدة...")
                self.whatsapp_sender = WhatsAppManager(db_manager, 1)  # clinic_id افتراضي
            else:
                logging.info("✅ AutoSender يستخدم النسخة العالمية من WhatsAppManager")
                
        except Exception as e:
            logging.error(f"❌ فشل تهيئة WhatsAppManager في AutoSender: {e}")
            self.whatsapp_sender = None
        
        self.setup_timers()
        
        logging.info("✅ تم تهيئة نظام الإرسال التلقائي الحقيقي المتكامل")

    def setup_senders(self):
        """إعداد مرسلي القنوات - الإصدار المحسن"""
        # تم دمج هذه الوظيفة في __init__ لاستخدام النسخة العالمية
        pass

    def setup_timers(self):
        """إعداد المؤقتات الدورية"""
        # فحص التذكيرات كل دقيقة
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self.check_all_reminders)
        self.reminder_timer.start(60000)  # كل دقيقة
        
        # مؤقت لتحديث الحالة
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(30000)  # كل 30 ثانية
        
        logging.info("✅ تم تفعيل المؤقتات الدورية للإرسال التلقائي")

    def update_status(self):
        """تحديث حالة النظام"""
        try:
            status_info = self.get_status()
            status_text = "نشط" if status_info.get('is_running', False) else "متوقف"
            self.status_changed.emit(status_text)
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث الحالة: {e}")

    def set_quick_test_mode(self, enabled=True):
        """تفعيل وضع الاختبار السريع (دقائق بدلاً من ساعات)"""
        self.quick_test_mode = enabled
        status = "مفعل" if enabled else "معطل"
        logging.info(f"🔧 وضع الاختبار السريع: {status}")
        
        if enabled:
            self.quick_test_started.emit()

    def check_all_reminders(self):
        """فحص جميع التذكيرات - الإصدار الحقيقي"""
        try:
            if not self.is_running:
                return
                
            if self.quick_test_mode:
                self.check_quick_reminders()
            else:
                self.check_24h_reminders()
                self.check_2h_reminders()
                
        except Exception as e:
            logging.error(f"❌ خطأ في فحص التذكيرات: {e}")

    # 🔥🔥🔥 الحل الجذري: إضافة الدوال المفقودة للتوافق
    def send_24h_reminders(self):
        """واجهة توافقية - تستدعي check_24h_reminders"""
        try:
            logging.info("🔄 استدعاء واجهة التوافق: send_24h_reminders -> check_24h_reminders")
            self.check_24h_reminders()
        except Exception as e:
            logging.error(f"❌ خطأ في send_24h_reminders: {e}")

    def send_2h_reminders(self):
        """واجهة توافقية - تستدعي check_2h_reminders"""
        try:
            logging.info("🔄 استدعاء واجهة التوافق: send_2h_reminders -> check_2h_reminders")
            self.check_2h_reminders()
        except Exception as e:
            logging.error(f"❌ خطأ في send_2h_reminders: {e}")

    def check_quick_reminders(self):
        """فحص التذكيرات السريعة (للاستخدام في الاختبار)"""
        try:
            logging.info("⚡ فحص التذكيرات السريعة...")
            
            # تذكير بعد 5 دقائق (بدلاً من 24 ساعة)
            self.send_quick_reminders(minutes=5, reminder_type="quick_5min")
            
            # تذكير بعد 1 دقيقة (بدلاً من ساعتين)
            self.send_quick_reminders(minutes=1, reminder_type="quick_1min")
            
        except Exception as e:
            logging.error(f"❌ خطأ في التذكيرات السريعة: {e}")

    def send_quick_reminders(self, minutes=5, reminder_type="quick_5min"):
        """إرسال تذكيرات سريعة للاختبار"""
        try:
            if not self.whatsapp_sender:
                logging.warning("⚠️ نظام الواتساب غير متوفر")
                return False

            # حساب الوقت المستهدف
            target_time = datetime.now() + timedelta(minutes=minutes)
            target_date = target_time.strftime('%Y-%m-%d')
            target_hour = target_time.strftime('%H:%M')

            # الحصول على المواعيد القريبة
            appointments = self.get_appointments_for_reminder(target_date, target_hour, reminder_type)
            
            sent_count = 0
            for appointment in appointments:
                try:
                    patient_name = appointment.get('patient_name', 'مريض')
                    patient_phone = appointment.get('patient_phone', '')
                    appointment_time = appointment.get('appointment_time', '')
                    
                    if not patient_phone:
                        continue

                    # إنشاء رسالة التذكير
                    message = self.create_quick_reminder_message(
                        patient_name, 
                        appointment_time, 
                        minutes,
                        reminder_type
                    )
                    
                    # إرسال الرسالة الحقيقية عبر واتساب
                    result = self.whatsapp_sender.send_message(
                        patient_phone, 
                        message, 
                        f"reminder_{reminder_type}",
                        appointment_id=appointment['id'],
                        patient_id=appointment.get('patient_id')
                    )
                    
                    if result.get('success'):
                        sent_count += 1
                        # تحديث حالة الإرسال في قاعدة البيانات
                        self.update_reminder_status(appointment['id'], reminder_type)
                        
                        # إرسال إشارة النجاح
                        self.reminder_sent.emit({
                            'patient_name': patient_name,
                            'reminder_type': reminder_type,
                            'appointment_id': appointment['id']
                        })
                        
                        logging.info(f"✅ تم إرسال تذكير {reminder_type} لـ {patient_name}")
                        
                    else:
                        # إرسال إشارة الفشل
                        self.reminder_failed.emit({
                            'patient_name': patient_name,
                            'reminder_type': reminder_type,
                            'error': result.get('message', 'فشل غير معروف')
                        })
                        logging.error(f"❌ فشل إرسال تذكير لـ {patient_name}: {result.get('message')}")
                        
                except Exception as e:
                    logging.error(f"❌ خطأ في إرسال تذكير: {e}")
                    self.reminder_failed.emit({
                        'patient_name': appointment.get('patient_name', 'مريض'),
                        'reminder_type': reminder_type,
                        'error': str(e)
                    })
            
            if sent_count > 0:
                logging.info(f"📤 تم إرسال {sent_count} تذكير {reminder_type}")
            
            return sent_count > 0
            
        except Exception as e:
            logging.error(f"❌ فشل في إرسال التذكيرات السريعة: {e}")
            return False

    def create_quick_reminder_message(self, patient_name, appointment_time, minutes, reminder_type):
        """إنشاء رسالة تذكير سريعة"""
        if reminder_type == "quick_5min":
            return f"""
⏰ تذكير بالموعد - اختبار نظام

عزيزي/عزيزتي {patient_name},

هذا اختبار حقيقي لنظام التذكير التلقائي.
سيتم إرسال تذكير آخر قبل موعدك بدقيقة.

موعدك: {appointment_time}

شكراً لتفهمك 🤝
            """.strip()
        else:  # quick_1min
            return f"""
🔔 تذكير فوري - اختبار نظام

عزيزي/عزيزتي {patient_name},

موعدك بعد دقيقة واحدة!
هذا اختبار حقيقي لنظام التذكير التلقائي.

الوقت: {appointment_time}

نترقب زيارتكم 👨‍⚕️
            """.strip()

    def get_appointments_for_reminder(self, target_date, target_hour, reminder_type):
        """الحصول على المواعيد التي تحتاج لتذكير"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # تحديد حقل التذكير بناءً على النوع
            reminder_field = ""
            if reminder_type == "quick_5min":
                reminder_field = "reminder_24h_sent"
            elif reminder_type == "quick_1min":
                reminder_field = "reminder_2h_sent"
            else:
                reminder_field = "reminder_24h_sent"
            
            query = f'''
                SELECT a.*, p.name as patient_name, p.phone as patient_phone
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                WHERE a.appointment_date = ? 
                AND a.appointment_time = ?
                AND a.status = "مجدول"
                AND a.{reminder_field} = 0
            '''
            
            cursor.execute(query, (target_date, target_hour))
            appointments = cursor.fetchall()
            
            # تحويل إلى قاموس
            result = []
            for row in appointments:
                result.append(dict(row))
            
            return result
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب المواعيد للتذكير: {e}")
            return []

    def update_reminder_status(self, appointment_id, reminder_type):
        """تحديث حالة التذكير في قاعدة البيانات"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            if reminder_type == "quick_5min":
                cursor.execute('''
                    UPDATE appointments 
                    SET reminder_24h_sent = 1, reminder_24h_sent_at = datetime('now')
                    WHERE id = ?
                ''', (appointment_id,))
            elif reminder_type == "quick_1min":
                cursor.execute('''
                    UPDATE appointments 
                    SET reminder_2h_sent = 1, reminder_2h_sent_at = datetime('now')
                    WHERE id = ?
                ''', (appointment_id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث حالة التذكير: {e}")
            return False

    def check_24h_reminders(self):
        """فحص تذكيرات 24 ساعة - الإصدار الحقيقي"""
        try:
            if not self.whatsapp_sender:
                logging.warning("⚠️ نظام الواتساب غير متوفر لتذكيرات 24 ساعة")
                return False

            # حساب الوقت بعد 24 ساعة
            target_date = (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d')
            
            # الحصول على المواعيد بعد 24 ساعة
            appointments = self.db_manager.get_appointments(date=target_date)
            
            sent_count = 0
            for appointment in appointments:
                try:
                    if not appointment.get('reminder_24h_sent'):
                        result = self.whatsapp_sender.send_appointment_reminder(
                            appointment['id'], 
                            "24h"
                        )
                        
                        if result:
                            sent_count += 1
                            
                            # إرسال إشارة النجاح
                            self.reminder_sent.emit({
                                'patient_name': appointment.get('patient_name', 'مريض'),
                                'reminder_type': '24h',
                                'appointment_id': appointment['id']
                            })
                            
                            logging.info(f"✅ تم إرسال تذكير 24 ساعة للموعد {appointment['id']}")
                except Exception as e:
                    logging.error(f"❌ خطأ في إرسال تذكير 24 ساعة: {e}")
                    self.reminder_failed.emit({
                        'patient_name': appointment.get('patient_name', 'مريض'),
                        'reminder_type': '24h',
                        'error': str(e)
                    })
            
            if sent_count > 0:
                logging.info(f"📤 تم إرسال {sent_count} تذكير 24 ساعة")
            
        except Exception as e:
            logging.error(f"❌ فشل في فحص تذكيرات 24 ساعة: {e}")

    def check_2h_reminders(self):
        """فحص تذكيرات ساعتين - الإصدار الحقيقي"""
        try:
            if not self.whatsapp_sender:
                logging.warning("⚠️ نظام الواتساب غير متوفر لتذكيرات ساعتين")
                return False

            # حساب الوقت بعد ساعتين
            target_time = datetime.now() + timedelta(hours=2)
            target_date = target_time.strftime('%Y-%m-%d')
            target_hour = target_time.strftime('%H:%M')
            
            # الحصول على المواعيد بعد ساعتين
            appointments = self.db_manager.get_appointments(date=target_date)
            
            sent_count = 0
            for appointment in appointments:
                try:
                    if (appointment.get('appointment_time') == target_hour and 
                        not appointment.get('reminder_2h_sent')):
                        
                        result = self.whatsapp_sender.send_appointment_reminder(
                            appointment['id'], 
                            "2h"
                        )
                        
                        if result:
                            sent_count += 1
                            
                            # إرسال إشارة النجاح
                            self.reminder_sent.emit({
                                'patient_name': appointment.get('patient_name', 'مريض'),
                                'reminder_type': '2h',
                                'appointment_id': appointment['id']
                            })
                            
                            logging.info(f"✅ تم إرسال تذكير ساعتين للموعد {appointment['id']}")
                except Exception as e:
                    logging.error(f"❌ خطأ في إرسال تذكير ساعتين: {e}")
                    self.reminder_failed.emit({
                        'patient_name': appointment.get('patient_name', 'مريض'),
                        'reminder_type': '2h',
                        'error': str(e)
                    })
            
            if sent_count > 0:
                logging.info(f"📤 تم إرسال {sent_count} تذكير ساعتين")
            
        except Exception as e:
            logging.error(f"❌ فشل في فحص تذكيرات ساعتين: {e}")

    def create_test_appointment(self, minutes_later=10):
        """إنشاء موعد تجريبي للاختبار - الإصدار الحقيقي"""
        try:
            # حساب وقت الموعد
            appointment_time = (datetime.now() + timedelta(minutes=minutes_later)).strftime('%H:%M')
            appointment_date = datetime.now().strftime('%Y-%m-%d')
            
            # إنشاء مريض تجريبي
            patient_id = self.create_test_patient()
            if not patient_id:
                return None
            
            # إنشاء الموعد
            appointment_id = self.db_manager.add_appointment({
                'patient_id': patient_id,
                'doctor_id': self.get_first_doctor(),
                'department_id': self.get_first_department(),
                'clinic_id': 1,
                'appointment_date': appointment_date,
                'appointment_time': appointment_time,
                'type': 'كشف',
                'status': 'مجدول',
                'notes': 'موعد اختبار حقيقي لنظام التذكير التلقائي'
            })
            
            if appointment_id:
                logging.info(f"✅ تم إنشاء موعد اختبار حقيقي: {appointment_time} (بعد {minutes_later} دقائق)")
                return appointment_id
            else:
                logging.error("❌ فشل إنشاء موعد اختبار")
                return None
                
        except Exception as e:
            logging.error(f"❌ خطأ في إنشاء موعد اختبار: {e}")
            return None

    def create_test_patient(self):
        """إنشاء مريض تجريبي"""
        try:
            # البحث عن مريض اختبار موجود
            patients = self.db_manager.get_patients()
            for patient in patients:
                if 'اختبار' in patient.get('name', '') or 'test' in patient.get('name', '').lower():
                    return patient['id']
            
            # إنشاء مريض جديد
            patient_id = self.db_manager.add_patient({
                'name': 'مريض اختبار التذكير التلقائي',
                'phone': '0555555555',
                'country_code': '+966',
                'email': 'test@reminder.com',
                'gender': 'ذكر',
                'address': 'عنوان اختبار النظام التلقائي'
            })
            
            return patient_id
        except Exception as e:
            logging.error(f"❌ فشل إنشاء مريض تجريبي: {e}")
            return None

    def get_first_doctor(self):
        """الحصول على أول طبيب متوفر"""
        try:
            doctors = self.db_manager.get_doctors()
            if doctors:
                return doctors[0]['id']
            return 1
        except:
            return 1

    def get_first_department(self):
        """الحصول على أول قسم متوفر"""
        try:
            departments = self.db_manager.get_departments()
            if departments:
                return departments[0]['id']
            return 1
        except:
            return 1

    def start_quick_test(self):
        """بدء اختبار سريع حقيقي"""
        try:
            logging.info("🚀 بدء الاختبار السريع الحقيقي...")
            
            # إرسال إشارة بدء الاختبار
            self.quick_test_started.emit()
            
            # تفعيل وضع الاختبار السريع
            self.set_quick_test_mode(True)
            
            # إنشاء موعد اختبار بعد 6 دقائق
            appointment_id = self.create_test_appointment(minutes_later=6)
            
            if appointment_id:
                logging.info("✅ تم إعداد الاختبار السريع بنجاح")
                logging.info("📱 ستصلك رسالتين عبر واتساب:")
                logging.info("   - الأولى بعد 5 دقائق (تذكير مبكر)")
                logging.info("   - الثانية بعد 1 دقيقة (تذكير فوري)")
                
                # إرسال إشارة اكتمال الإعداد
                self.quick_test_completed.emit()
                return True
            else:
                logging.error("❌ فشل إعداد الاختبار السريع")
                return False
                
        except Exception as e:
            logging.error(f"❌ خطأ في الاختبار السريع: {e}")
            return False

    def start_auto_sender(self):
        """بدء نظام الإرسال التلقائي"""
        try:
            self.is_running = True
            logging.info("🚀 بدء نظام الإرسال التلقائي")
            self.status_changed.emit("نشط")
            return True
        except Exception as e:
            logging.error(f"❌ خطأ في بدء النظام التلقائي: {e}")
            return False

    def stop_auto_sender(self):
        """إيقاف نظام الإرسال التلقائي"""
        try:
            self.is_running = False
            logging.info("⏹️ إيقاف نظام الإرسال التلقائي")
            self.status_changed.emit("متوقف")
            return True
        except Exception as e:
            logging.error(f"❌ خطأ في إيقاف النظام التلقائي: {e}")
            return False

    def get_status(self):
        """الحصول على حالة النظام"""
        return {
            'is_running': self.is_running,
            'check_interval': 5,
            'last_check_time': datetime.now().strftime('%H:%M:%S'),
            'sent_count': 0,
            'whatsapp_connected': self.whatsapp_sender is not None and 
                                getattr(self.whatsapp_sender, 'is_connected', False)
        }