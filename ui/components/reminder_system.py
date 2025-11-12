# -*- coding: utf-8 -*-
import sqlite3
import logging
from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, pyqtSignal

class ReminderSystem(QObject):
    """نظام التذكيرات التلقائي"""

    # إشارات لتحديث الواجهة
    reminder_sent = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, db_path, clinic_id):
        super().__init__()
        self.db_path = db_path
        self.clinic_id = clinic_id
        self.logger = logging.getLogger(__name__)

    def check_and_send_reminders(self):
        """فحص وإرسال التذكيرات"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # المواعيد القادمة في الـ24 ساعة القادمة
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT a.id, a.appointment_date, a.appointment_time, 
                       p.name as patient_name, p.phone,
                       d.name as doctor_name,
                       a.reminder_24h_sent, a.reminder_2h_sent
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                WHERE a.clinic_id = ? 
                AND a.appointment_date = ?
                AND a.status IN ('مجدول', 'تم التأكيد')
            ''', (self.clinic_id, tomorrow))

            appointments_24h = cursor.fetchall()

            # المواعيد القادمة في الساعتين القادمتين
            now_plus_2h = datetime.now() + timedelta(hours=2)
            cursor.execute('''
                SELECT a.id, a.appointment_date, a.appointment_time, 
                       p.name as patient_name, p.phone,
                       d.name as doctor_name,
                       a.reminder_24h_sent, a.reminder_2h_sent
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                WHERE a.clinic_id = ? 
                AND a.appointment_date = ?
                AND a.appointment_time BETWEEN TIME('now') AND TIME('now', '+2 hours')
                AND a.status IN ('مجدول', 'تم التأكيد')
            ''', (self.clinic_id, datetime.now().strftime('%Y-%m-%d')))

            appointments_2h = cursor.fetchall()

            # معالجة تذكيرات 24 ساعة
            for apt in appointments_24h:
                if not apt[6]:  # إذا لم يتم إرسال تذكير 24 ساعة
                    self.send_24h_reminder(apt)
                    cursor.execute('UPDATE appointments SET reminder_24h_sent = 1 WHERE id = ?', (apt[0],))

            # معالجة تذكيرات ساعتين
            for apt in appointments_2h:
                if not apt[7]:  # إذا لم يتم إرسال تذكير ساعتين
                    self.send_2h_reminder(apt)
                    cursor.execute('UPDATE appointments SET reminder_2h_sent = 1 WHERE id = ?', (apt[0],))

            conn.commit()
            conn.close()

            self.logger.info("تم فحص التذكيرات بنجاح")

        except Exception as e:
            self.logger.error(f"خطأ في فحص التذكيرات: {e}")
            self.error_occurred.emit(str(e))

    def send_24h_reminder(self, appointment):
        """إرسال تذكير قبل 24 ساعة"""
        try:
            appointment_id, date, time, patient_name, phone, doctor_name, _, _ = appointment
            
            # تحويل التاريخ إلى تنسيق عربي
            arabic_date = self.convert_to_arabic_date(date)
            
            message = f"""
تذكير: موعدك غداً {arabic_date} الساعة {time}
مع د. {doctor_name}
الرجاء التأكد من الحضور قبل الموعد بـ 15 دقيقة
            """.strip()

            # حفظ الرسالة في قاعدة البيانات
            self.save_message(patient_name, phone, message, "تذكير 24ساعة", appointment_id)
            
            # في الواقع، هنا سيتم إرسال الرسالة عبر واتساب
            # self.send_whatsapp_message(phone, message)
            
            self.reminder_sent.emit({
                'type': '24h',
                'patient': patient_name,
                'phone': phone,
                'message': message,
                'appointment_id': appointment_id
            })
            
            self.logger.info(f"تم إرسال تذكير 24 ساعة لـ {patient_name}")

        except Exception as e:
            self.logger.error(f"خطأ في إرسال تذكير 24 ساعة: {e}")

    def send_2h_reminder(self, appointment):
        """إرسال تذكير قبل ساعتين"""
        try:
            appointment_id, date, time, patient_name, phone, doctor_name, _, _ = appointment
            
            message = f"""
تذكير: موعدك بعد ساعتين الساعة {time}
مع د. {doctor_name}
نرجو عدم التأخر
            """.strip()

            # حفظ الرسالة في قاعدة البيانات
            self.save_message(patient_name, phone, message, "تذكير 2ساعة", appointment_id)
            
            # في الواقع، هنا سيتم إرسال الرسالة عبر واتساب
            # self.send_whatsapp_message(phone, message)
            
            self.reminder_sent.emit({
                'type': '2h',
                'patient': patient_name,
                'phone': phone,
                'message': message,
                'appointment_id': appointment_id
            })
            
            self.logger.info(f"تم إرسال تذكير ساعتين لـ {patient_name}")

        except Exception as e:
            self.logger.error(f"خطأ في إرسال تذكير ساعتين: {e}")

    def convert_to_arabic_date(self, date_str):
        """تحويل التاريخ إلى تنسيق عربي"""
        try:
            months = {
                '01': 'يناير', '02': 'فبراير', '03': 'مارس',
                '04': 'أبريل', '05': 'مايو', '06': 'يونيو',
                '07': 'يوليو', '08': 'أغسطس', '09': 'سبتمبر',
                '10': 'أكتوبر', '11': 'نوفمبر', '12': 'ديسمبر'
            }
            
            year, month, day = date_str.split('-')
            return f"{day} {months[month]} {year}"
        except:
            return date_str

    def save_message(self, patient_name, phone, message, message_type, appointment_id):
        """حفظ الرسالة في قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # الحصول على patient_id من appointment_id
            cursor.execute('SELECT patient_id FROM appointments WHERE id = ?', (appointment_id,))
            patient_id = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT INTO messages 
                (clinic_id, patient_id, phone_number, message_type, message_text, status, sent_date)
                VALUES (?, ?, ?, ?, ?, 'مرسل', CURRENT_TIMESTAMP)
            ''', (self.clinic_id, patient_id, phone, message_type, message))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"خطأ في حفظ الرسالة: {e}")

    def send_whatsapp_message(self, phone, message):
        """إرسال رسالة واتساب (سيتم تنفيذها لاحقاً)"""
        # TODO: تنفيذ الإرسال الفعلي عبر واتساب
        print(f"إرسال واتساب إلى {phone}: {message}")
        return True