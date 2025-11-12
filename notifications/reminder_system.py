# notifications/reminder_system.py
import logging
import sqlite3
from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

class ClinicReminderSystem(QObject):
    """نظام التذكيرات التلقائي المبسط والموثوق"""
    
    # إشارات للتحديثات
    reminder_sent = pyqtSignal(dict)
    reminder_failed = pyqtSignal(dict)
    system_status_changed = pyqtSignal(str)
    
    def __init__(self, db_manager, whatsapp_manager=None, clinic_id=1):
        super().__init__()
        self.db_manager = db_manager
        self.whatsapp_manager = whatsapp_manager
        self.clinic_id = clinic_id
        self.is_running = False
        
        self.setup_timers()
        self.setup_logging()
        
    def setup_logging(self):
        """إعداد نظام التسجيل"""
        self.logger = logging.getLogger('ReminderSystem')
        
    def setup_timers(self):
        """إعداد المؤقتات الدورية"""
        # فحص التذكيرات كل دقيقة
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self.check_reminders)
        
        # مؤقت حالة النظام كل 30 ثانية
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        
    def start(self):
        """بدء نظام التذكيرات"""
        try:
            self.reminder_timer.start(60000)  # كل دقيقة
            self.status_timer.start(30000)    # كل 30 ثانية
            self.is_running = True
            
            self.logger.info("✅ بدء نظام التذكيرات التلقائي")
            self.system_status_changed.emit("نشط")
            
            # فحص فوري للتذكيرات
            self.check_reminders()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ فشل بدء النظام: {e}")
            return False
    
    def stop(self):
        """إيقاف نظام التذكيرات"""
        self.reminder_timer.stop()
        self.status_timer.stop()
        self.is_running = False
        self.system_status_changed.emit("متوقف")
        self.logger.info("⏹️ إيقاف نظام التذكيرات")
    
    def check_reminders(self):
        """فحص التذكيرات المستحقة"""
        try:
            if not self.whatsapp_manager:
                self.logger.warning("⚠️ WhatsAppManager غير متوفر")
                return
            
            # فحص تذكيرات 24 ساعة
            self.check_24h_reminders()
            
            # فحص تذكيرات ساعتين
            self.check_2h_reminders()
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في فحص التذكيرات: {e}")
    
    def check_24h_reminders(self):
        """فحص تذكيرات 24 ساعة"""
        try:
            # حساب الوقت بعد 24 ساعة
            target_time = datetime.now() + timedelta(hours=24)
            target_date = target_time.strftime('%Y-%m-%d')
            target_hour = target_time.strftime('%H:%M')
            
            # جلب المواعيد التي تحتاج تذكير
            appointments = self.get_appointments_for_reminder(target_date, target_hour, '24h')
            
            for appointment in appointments:
                self.send_reminder(appointment, '24h')
                
        except Exception as e:
            self.logger.error(f"❌ خطأ في تذكيرات 24h: {e}")
    
    def check_2h_reminders(self):
        """فحص تذكيرات ساعتين"""
        try:
            # حساب الوقت بعد ساعتين
            target_time = datetime.now() + timedelta(hours=2)
            target_date = target_time.strftime('%Y-%m-%d')
            target_hour = target_time.strftime('%H:%M')
            
            # جلب المواعيد التي تحتاج تذكير
            appointments = self.get_appointments_for_reminder(target_date, target_hour, '2h')
            
            for appointment in appointments:
                self.send_reminder(appointment, '2h')
                
        except Exception as e:
            self.logger.error(f"❌ خطأ في تذكيرات 2h: {e}")
    
    def get_appointments_for_reminder(self, target_date, target_hour, reminder_type):
        """جلب المواعيد التي تحتاج تذكير"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # تحديد حقل التذكير بناءً على النوع
            reminder_field = "reminder_24h_sent" if reminder_type == '24h' else "reminder_2h_sent"
            
            query = f'''
                SELECT a.*, p.name as patient_name, p.phone as patient_phone,
                       d.name as doctor_name, dep.name as department_name
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                JOIN departments dep ON a.department_id = dep.id
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
            self.logger.error(f"❌ خطأ في جلب المواعيد: {e}")
            return []
    
    def send_reminder(self, appointment, reminder_type):
        """إرسال تذكير للموعد"""
        try:
            patient_phone = appointment.get('patient_phone')
            if not patient_phone:
                self.logger.warning(f"⚠️ رقم المريض غير موجود للموعد {appointment.get('id')}")
                return False
            
            # بناء رسالة التذكير
            message = self.build_reminder_message(appointment, reminder_type)
            
            # إرسال الرسالة عبر WhatsAppManager
            result = self.whatsapp_manager.send_message(
                patient_phone,
                message,
                f"reminder_{reminder_type}",
                appointment_id=appointment.get('id'),
                patient_id=appointment.get('patient_id')
            )
            
            if result.get('success'):
                # تحديث حالة التذكير في قاعدة البيانات
                self.update_reminder_status(appointment.get('id'), reminder_type)
                
                # إرسال إشارة النجاح
                self.reminder_sent.emit({
                    'patient_name': appointment.get('patient_name'),
                    'reminder_type': reminder_type,
                    'appointment_id': appointment.get('id'),
                    'phone': patient_phone
                })
                
                self.logger.info(f"✅ تم إرسال تذكير {reminder_type} لـ {appointment.get('patient_name')}")
                return True
            else:
                # إرسال إشارة الفشل
                self.reminder_failed.emit({
                    'patient_name': appointment.get('patient_name'),
                    'reminder_type': reminder_type,
                    'error': result.get('message', 'فشل غير معروف'),
                    'phone': patient_phone
                })
                
                self.logger.error(f"❌ فشل إرسال تذكير لـ {appointment.get('patient_name')}")
                return False
                
        except Exception as e:
            error_msg = f"خطأ في إرسال التذكير: {str(e)}"
            self.reminder_failed.emit({
                'patient_name': appointment.get('patient_name', 'مريض'),
                'reminder_type': reminder_type,
                'error': error_msg
            })
            self.logger.error(f"❌ {error_msg}")
            return False
    
    def build_reminder_message(self, appointment, reminder_type):
        """بناء رسالة التذكير"""
        patient_name = appointment.get('patient_name', 'عزيزي/عزيزتي')
        appointment_time = appointment.get('appointment_time', '')
        appointment_date = appointment.get('appointment_date', '')
        doctor_name = appointment.get('doctor_name', 'الطبيب')
        department_name = appointment.get('department_name', 'القسم')
        
        if reminder_type == '24h':
            return f"""
تذكير بالموعد 🗓️

عزيزي/عزيزتي {patient_name}

نذكرك بموعدك غداً:
📅 التاريخ: {appointment_date}
⏰ الوقت: {appointment_time}
👨‍⚕️ الدكتور: {doctor_name}
🏥 القسم: {department_name}

نرجو التأكيد على الحضور 🌹
            """.strip()
        
        else:  # 2h reminder
            return f"""
تذكير فوري بالموعد ⏰

عزيزي/عزيزتي {patient_name}

موعدك بعد ساعتين:
🕐 الوقت: {appointment_time}
👨‍⚕️ الدكتور: {doctor_name}

نترقب زيارتكم 👨‍⚕️
            """.strip()
    
    def update_reminder_status(self, appointment_id, reminder_type):
        """تحديث حالة التذكير في قاعدة البيانات"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            if reminder_type == '24h':
                cursor.execute('''
                    UPDATE appointments 
                    SET reminder_24h_sent = 1, reminder_24h_sent_at = datetime('now')
                    WHERE id = ?
                ''', (appointment_id,))
            else:  # 2h
                cursor.execute('''
                    UPDATE appointments 
                    SET reminder_2h_sent = 1, reminder_2h_sent_at = datetime('now')
                    WHERE id = ?
                ''', (appointment_id,))
            
            conn.commit()
            self.logger.info(f"✅ تم تحديث حالة تذكير {reminder_type} للموعد {appointment_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تحديث حالة التذكير: {e}")
            return False
    
    def schedule_appointment_reminders(self, appointment_id):
        """جدولة تذكيرات موعد جديد"""
        try:
            # هذا للمواعيد الجديدة - يمكن إضافة منطق إضافي هنا
            self.logger.info(f"📅 تم جدولة تذكيرات للموعد الجديد {appointment_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في جدولة التذكيرات: {e}")
            return False
    
    def send_instant_confirmation(self, appointment_id):
        """إرسال تأكيد فوري للموعد الجديد"""
        try:
            # جلب بيانات الموعد
            appointment = self.get_appointment_by_id(appointment_id)
            if not appointment:
                self.logger.error(f"❌ الموعد غير موجود: {appointment_id}")
                return False
            
            patient_phone = appointment.get('patient_phone')
            if not patient_phone:
                self.logger.warning(f"⚠️ رقم المريض غير موجود للموعد {appointment_id}")
                return False
            
            # بناء رسالة التأكيد
            message = self.build_confirmation_message(appointment)
            
            # إرسال الرسالة
            result = self.whatsapp_manager.send_message(
                patient_phone,
                message,
                "appointment_confirmation",
                appointment_id=appointment_id,
                patient_id=appointment.get('patient_id')
            )
            
            if result.get('success'):
                self.logger.info(f"✅ تم إرسال تأكيد الموعد لـ {appointment.get('patient_name')}")
                return True
            else:
                self.logger.error(f"❌ فشل إرسال تأكيد الموعد: {result.get('message')}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ خطأ في إرسال التأكيد: {e}")
            return False
    
    def build_confirmation_message(self, appointment):
        """بناء رسالة تأكيد الموعد"""
        patient_name = appointment.get('patient_name', 'عزيزي/عزيزتي')
        appointment_time = appointment.get('appointment_time', '')
        appointment_date = appointment.get('appointment_date', '')
        doctor_name = appointment.get('doctor_name', 'الطبيب')
        department_name = appointment.get('department_name', 'القسم')
        
        return f"""
تم حجز الموعد بنجاح ✅

عزيزي/عزيزتي {patient_name}

تم تأكيد حجز موعدك:
📅 التاريخ: {appointment_date}
⏰ الوقت: {appointment_time}
👨‍⚕️ الدكتور: {doctor_name}
🏥 القسم: {department_name}

سنرسل لك تذكير قبل 24 ساعة وساعتين من الموعد.

شكراً لثقتكم بنا 🤝
        """.strip()
    
    def get_appointment_by_id(self, appointment_id):
        """جلب بيانات موعد بواسطة الID"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            query = '''
                SELECT a.*, p.name as patient_name, p.phone as patient_phone,
                       d.name as doctor_name, dep.name as department_name
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                JOIN departments dep ON a.department_id = dep.id
                WHERE a.id = ?
            '''
            
            cursor.execute(query, (appointment_id,))
            result = cursor.fetchone()
            
            return dict(result) if result else None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في جلب بيانات الموعد: {e}")
            return None
    
    def update_status(self):
        """تحديث حالة النظام"""
        status = "نشط" if self.is_running else "متوقف"
        whatsapp_status = "متوفر" if self.whatsapp_manager else "غير متوفر"
        
        full_status = f"{status} - واتساب: {whatsapp_status}"
        self.system_status_changed.emit(full_status)
    
    def get_system_status(self):
        """الحصول على حالة النظام"""
        return {
            'is_running': self.is_running,
            'whatsapp_available': bool(self.whatsapp_manager),
            'last_check': datetime.now().strftime('%H:%M:%S')
        }