# -*- coding: utf-8 -*-
import logging
from datetime import date

class AppointmentsMixin:
    """ميكسین إدارة المواعيد والتذكيرات - الإصدار المصحح"""
    
    def get_appointments(self, target_date=None, status=None, doctor_id=None, clinic_id=None, department_id=None, patient_id=None):
        """الحصول على قائمة المواعيد - الإصدار المصحح"""
        try:
            query = '''
                SELECT 
                    a.*,
                    p.name as patient_name,
                    p.phone as patient_phone,
                    p.country_code as patient_country_code,
                    d.name as doctor_name,
                    dept.name as department_name,
                    c.name as clinic_name
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                JOIN departments dept ON a.department_id = dept.id
                JOIN clinics c ON a.clinic_id = c.id
                WHERE 1=1
            '''
            params = []
            
            if target_date:
                query += ' AND a.appointment_date = ?'
                params.append(target_date)
            if status and status != "جميع الحالات":
                query += ' AND a.status = ?'
                params.append(status)
            if doctor_id:
                query += ' AND a.doctor_id = ?'
                params.append(doctor_id)
            if clinic_id:
                query += ' AND a.clinic_id = ?'
                params.append(clinic_id)
            if department_id:
                query += ' AND a.department_id = ?'
                params.append(department_id)
            if patient_id:
                query += ' AND a.patient_id = ?'
                params.append(patient_id)
            
            query += ' ORDER BY a.appointment_date, a.appointment_time'
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            appointments = []
            for row in rows:
                row_dict = dict(row)  # تحويل sqlite3.Row إلى dict
                
                appointment_data = {
                    'id': row_dict.get('id', 0),
                    'patient_name': row_dict.get('patient_name', 'غير معروف'),
                    'patient_phone': row_dict.get('patient_phone', ''),
                    'patient_country_code': row_dict.get('patient_country_code', '+966'),
                    'doctor_name': row_dict.get('doctor_name', 'غير معروف'),
                    'department_name': row_dict.get('department_name', 'غير معروف'),
                    'clinic_name': row_dict.get('clinic_name', 'غير معروف'),
                    'appointment_date': row_dict.get('appointment_date', ''),
                    'appointment_time': row_dict.get('appointment_time', ''),
                    'status': row_dict.get('status', 'مجدول'),
                    'type': row_dict.get('type', 'كشف'),
                    'notes': row_dict.get('notes', ''),
                    'whatsapp_sent': bool(row_dict.get('whatsapp_sent', 0)),
                    'whatsapp_sent_at': row_dict.get('whatsapp_sent_at'),
                    'reminder_24h_sent': bool(row_dict.get('reminder_24h_sent', 0)),
                    'reminder_24h_sent_at': row_dict.get('reminder_24h_sent_at'),
                    'reminder_2h_sent': bool(row_dict.get('reminder_2h_sent', 0)),
                    'reminder_2h_sent_at': row_dict.get('reminder_2h_sent_at')
                }
                appointments.append(appointment_data)
            
            return appointments
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب المواعيد: {e}")
            return []
    
    def get_today_appointments(self):
        """الحصول على مواعيد اليوم"""
        try:
            today = date.today().strftime('%Y-%m-%d')
            return self.get_appointments(target_date=today)
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب مواعيد اليوم: {e}")
            return []
    
    def add_appointment(self, appointment_data):
        """إضافة موعد جديد"""
        try:
            query = '''
                INSERT INTO appointments (
                    patient_id, doctor_id, department_id, clinic_id, 
                    appointment_date, appointment_time, type, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                appointment_data['patient_id'],
                appointment_data['doctor_id'],
                appointment_data['department_id'],
                appointment_data['clinic_id'],
                appointment_data['appointment_date'],
                appointment_data['appointment_time'],
                appointment_data.get('type', 'كشف'),
                appointment_data.get('status', 'مجدول'),
                appointment_data.get('notes', '')
            )
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            
            appointment_id = cursor.lastrowid
            logging.info(f"✅ تم إضافة الموعد الجديد برقم: {appointment_id}")
            return appointment_id
            
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة الموعد: {e}")
            self.conn.rollback()
            return None

    def update_appointment_status(self, appointment_id, new_status):
        """تحديث حالة الموعد"""
        try:
            query = 'UPDATE appointments SET status = ? WHERE id = ?'
            cursor = self.conn.cursor()
            cursor.execute(query, (new_status, appointment_id))
            self.conn.commit()
            
            logging.info(f"✅ تم تحديث حالة الموعد {appointment_id} إلى: {new_status}")
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث حالة الموعد: {e}")
            self.conn.rollback()
            return False

    def update_appointment(self, appointment_id, appointment_data):
        """تحديث بيانات الموعد"""
        try:
            query = '''
                UPDATE appointments 
                SET patient_id=?, doctor_id=?, department_id=?, clinic_id=?,
                    appointment_date=?, appointment_time=?, type=?, status=?, notes=?
                WHERE id=?
            '''
            params = (
                appointment_data['patient_id'],
                appointment_data['doctor_id'],
                appointment_data['department_id'],
                appointment_data['clinic_id'],
                appointment_data['appointment_date'],
                appointment_data['appointment_time'],
                appointment_data.get('type', 'كشف'),
                appointment_data.get('status', 'مجدول'),
                appointment_data.get('notes', ''),
                appointment_id
            )
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث الموعد: {e}")
            self.conn.rollback()
            return False

    def get_appointment_by_id(self, appointment_id):
        """الحصول على بيانات موعد بواسطة ID"""
        try:
            query = '''
                SELECT 
                    a.*,
                    p.name as patient_name,
                    p.phone as patient_phone,
                    p.country_code as patient_country_code,
                    d.name as doctor_name,
                    dept.name as department_name,
                    c.name as clinic_name
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                JOIN departments dept ON a.department_id = dept.id
                JOIN clinics c ON a.clinic_id = c.id
                WHERE a.id = ?
            '''
            cursor = self.conn.cursor()
            cursor.execute(query, (appointment_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)  # تحويل إلى dict
            return None
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب بيانات الموعد: {e}")
            return None

    def update_appointment_whatsapp_status(self, appointment_id, sent_status=True):
        """تحديث حالة إرسال الواتساب للموعد - الإصدار المصحح والمتكامل"""
        try:
            cursor = self.conn.cursor()
            
            if sent_status:
                # إذا تم الإرسال بنجاح، نقوم بتحديث الحالة والوقت
                cursor.execute(
                    "UPDATE appointments SET whatsapp_sent = ?, whatsapp_sent_at = datetime('now') WHERE id = ?",
                    (1, appointment_id)
                )
            else:
                # إذا فشل الإرسال، نقوم بإعادة تعيين الحالة فقط
                cursor.execute(
                    "UPDATE appointments SET whatsapp_sent = ? WHERE id = ?",
                    (0, appointment_id)
                )
            
            self.conn.commit()
            logging.info(f"✅ تم تحديث حالة واتساب الموعد {appointment_id} إلى {sent_status}")
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث حالة واتساب الموعد: {e}")
            self.conn.rollback()
            return False

    def update_appointment_reminder_status(self, appointment_id, reminder_type, sent=True):
        """تحديث حالة التذكير للموعد - الإصدار المصحح"""
        try:
            cursor = self.conn.cursor()
            
            if reminder_type == '24h':
                cursor.execute('''
                    UPDATE appointments 
                    SET reminder_24h_sent = ?, reminder_24h_sent_at = datetime('now')
                    WHERE id = ?
                ''', (1 if sent else 0, appointment_id))
            elif reminder_type == '2h':
                cursor.execute('''
                    UPDATE appointments 
                    SET reminder_2h_sent = ?, reminder_2h_sent_at = datetime('now')
                    WHERE id = ?
                ''', (1 if sent else 0, appointment_id))
            
            self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث حالة التذكير: {e}")
            self.conn.rollback()
            return False