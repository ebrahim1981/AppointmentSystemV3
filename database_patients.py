# -*- coding: utf-8 -*-
import logging

class PatientsMixin:
    """ميكسین إدارة المرضى والعلامات والسجلات الطبية"""
    
    def get_patients(self, search_term=None):
        """الحصول على قائمة المرضى مع رموز الدول"""
        try:
            if search_term:
                query = '''
                    SELECT *, 
                    CASE 
                        WHEN country_code = '+966' THEN '🇸🇦 ' || phone
                        WHEN country_code = '+963' THEN '🇸🇾 ' || phone
                        ELSE country_code || ' ' || phone
                    END as formatted_phone
                    FROM patients 
                    WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
                    ORDER BY name
                '''
                params = (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%')
            else:
                query = '''
                    SELECT *,
                    CASE 
                        WHEN country_code = '+966' THEN '🇸🇦 ' || phone
                        WHEN country_code = '+963' THEN '🇸🇾 ' || phone
                        ELSE country_code || ' ' || phone
                    END as formatted_phone
                    FROM patients ORDER BY name
                '''
                params = ()
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            patients = [dict(row) for row in rows]
            return patients
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب المرضى: {e}")
            return []
    
    def get_patient_by_id(self, patient_id):
        """الحصول على بيانات مريض بواسطة ID"""
        try:
            query = 'SELECT * FROM patients WHERE id = ?'
            cursor = self.conn.cursor()
            cursor.execute(query, (patient_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب بيانات المريض: {e}")
            return None
    
    def add_patient(self, patient_data):
        """إضافة مريض جديد"""
        try:
            query = '''
                INSERT INTO patients (name, phone, country_code, email, date_of_birth, gender, address, emergency_contact, insurance_info, medical_history, whatsapp_consent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                patient_data['name'],
                patient_data['phone'],
                patient_data.get('country_code', '+966'),
                patient_data.get('email', ''),
                patient_data.get('date_of_birth'),
                patient_data.get('gender', 'ذكر'),
                patient_data.get('address', ''),
                patient_data.get('emergency_contact', ''),
                patient_data.get('insurance_info', ''),
                patient_data.get('medical_history', ''),
                patient_data.get('whatsapp_consent', 0)
            )
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            
            patient_id = cursor.lastrowid
            return patient_id
            
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة المريض: {e}")
            self.conn.rollback()
            return None
    
    def update_patient(self, patient_id, patient_data):
        """تحديث بيانات المريض"""
        try:
            query = '''
                UPDATE patients 
                SET name=?, phone=?, country_code=?, email=?, date_of_birth=?, gender=?, address=?, emergency_contact=?, insurance_info=?, medical_history=?, whatsapp_consent=?
                WHERE id=?
            '''
            params = (
                patient_data['name'],
                patient_data['phone'],
                patient_data.get('country_code', '+966'),
                patient_data.get('email', ''),
                patient_data.get('date_of_birth'),
                patient_data.get('gender', 'ذكر'),
                patient_data.get('address', ''),
                patient_data.get('emergency_contact', ''),
                patient_data.get('insurance_info', ''),
                patient_data.get('medical_history', ''),
                patient_data.get('whatsapp_consent', 0),
                patient_id
            )
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث المريض: {e}")
            self.conn.rollback()
            return False

    def get_all_patient_tags(self):
        """الحصول على جميع العلامات الفريدة للمرضى"""
        try:
            query = "SELECT DISTINCT tag_name FROM patient_tags ORDER BY tag_name"
            cursor = self.conn.cursor()
            cursor.execute(query)
            tags = [row[0] for row in cursor.fetchall()]
            return tags
        except Exception as e:
            logging.error(f"❌ خطأ في جلب العلامات: {e}")
            return []

    def get_patients_by_tag(self, tag_name):
        """الحصول على المرضى حسب العلامة"""
        try:
            query = '''
                SELECT p.*, GROUP_CONCAT(pt.tag_name) as patient_tags
                FROM patients p
                LEFT JOIN patient_tags pt ON p.id = pt.patient_id
                WHERE pt.tag_name = ?
                GROUP BY p.id
            '''
            cursor = self.conn.cursor()
            cursor.execute(query, (tag_name,))
            rows = cursor.fetchall()
            
            patients = []
            for row in rows:
                patient = dict(row)
                # معالجة العلامات
                if patient.get('patient_tags'):
                    patient['patient_tags'] = patient['patient_tags'].split(',')
                else:
                    patient['patient_tags'] = []
                patients.append(patient)
            
            return patients
        except Exception as e:
            logging.error(f"❌ خطأ في جلب المرضى بالعلامة: {e}")
            return []

    def get_patient_tags(self, patient_id):
        """الحصول على علامات مريض معين"""
        try:
            query = "SELECT tag_name FROM patient_tags WHERE patient_id = ?"
            cursor = self.conn.cursor()
            cursor.execute(query, (patient_id,))
            tags = [row[0] for row in cursor.fetchall()]
            return tags
        except Exception as e:
            logging.error(f"❌ خطأ في جلب علامات المريض: {e}")
            return []

    def add_patient_tag(self, patient_id, tag_name, color='#3498db'):
        """إضافة علامة لمريض"""
        try:
            query = '''
                INSERT OR REPLACE INTO patient_tags (patient_id, tag_name, color)
                VALUES (?, ?, ?)
            '''
            cursor = self.conn.cursor()
            cursor.execute(query, (patient_id, tag_name, color))
            self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة علامة: {e}")
            self.conn.rollback()
            return False

    def remove_patient_tag(self, patient_id, tag_name):
        """إزالة علامة من مريض"""
        try:
            query = "DELETE FROM patient_tags WHERE patient_id = ? AND tag_name = ?"
            cursor = self.conn.cursor()
            cursor.execute(query, (patient_id, tag_name))
            self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"❌ خطأ في إزالة علامة: {e}")
            self.conn.rollback()
            return False

    def get_patients_stats(self):
        """الحصول على إحصائيات المرضى"""
        try:
            cursor = self.conn.cursor()
            
            # إجمالي المرضى
            cursor.execute("SELECT COUNT(*) FROM patients")
            total_patients = cursor.fetchone()[0]
            
            # المرضى الجدد هذا الشهر
            cursor.execute('''
                SELECT COUNT(*) FROM patients 
                WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
            ''')
            new_patients_this_month = cursor.fetchone()[0]
            
            return {
                'total_patients': total_patients,
                'new_patients_this_month': new_patients_this_month
            }
        except Exception as e:
            logging.error(f"❌ خطأ في جلب إحصائيات المرضى: {e}")
            return {'total_patients': 0, 'new_patients_this_month': 0}

    def get_patient_statistics(self, patient_id):
        """الحصول على إحصائيات مريض معين"""
        try:
            cursor = self.conn.cursor()
            
            # إجمالي المواعيد
            cursor.execute("SELECT COUNT(*) FROM appointments WHERE patient_id = ?", (patient_id,))
            total_appointments = cursor.fetchone()[0]
            
            # المواعيد المنتهية
            cursor.execute("SELECT COUNT(*) FROM appointments WHERE patient_id = ? AND status = 'منتهي'", (patient_id,))
            completed_appointments = cursor.fetchone()[0]
            
            # أول وآخر موعد
            cursor.execute('''
                SELECT MIN(appointment_date), MAX(appointment_date) 
                FROM appointments 
                WHERE patient_id = ?
            ''', (patient_id,))
            first_last = cursor.fetchone()
            first_appointment = first_last[0] if first_last[0] else 'لا يوجد'
            last_appointment = first_last[1] if first_last[1] else 'لا يوجد'
            
            # عدد السجلات الطبية
            cursor.execute("SELECT COUNT(*) FROM medical_records WHERE patient_id = ?", (patient_id,))
            medical_records_count = cursor.fetchone()[0]
            
            return {
                'total_appointments': total_appointments,
                'completed_appointments': completed_appointments,
                'first_appointment': first_appointment,
                'last_appointment': last_appointment,
                'medical_records_count': medical_records_count
            }
        except Exception as e:
            logging.error(f"❌ خطأ في جلب إحصائيات المريض: {e}")
            return {
                'total_appointments': 0,
                'completed_appointments': 0,
                'first_appointment': 'لا يوجد',
                'last_appointment': 'لا يوجد',
                'medical_records_count': 0
            }

    def get_patient_appointments(self, patient_id):
        """الحصول على مواعيد مريض معين"""
        try:
            query = '''
                SELECT a.*, d.name as doctor_name, dept.name as department_name
                FROM appointments a
                LEFT JOIN doctors d ON a.doctor_id = d.id
                LEFT JOIN departments dept ON a.department_id = dept.id
                WHERE a.patient_id = ?
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
            '''
            cursor = self.conn.cursor()
            cursor.execute(query, (patient_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logging.error(f"❌ خطأ في جلب مواعيد المريض: {e}")
            return []

    def get_patient_medical_history(self, patient_id):
        """الحصول على السجل الطبي للمريض"""
        try:
            query = '''
                SELECT mr.*, d.name as doctor_name
                FROM medical_records mr
                LEFT JOIN doctors d ON mr.doctor_id = d.id
                WHERE mr.patient_id = ?
                ORDER BY mr.visit_date DESC
            '''
            cursor = self.conn.cursor()
            cursor.execute(query, (patient_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logging.error(f"❌ خطأ في جلب السجل الطبي: {e}")
            return []

    def add_medical_record(self, record_data):
        """إضافة سجل طبي جديد"""
        try:
            query = '''
                INSERT INTO medical_records (patient_id, doctor_id, visit_date, diagnosis, treatment, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            '''
            params = (
                record_data['patient_id'],
                record_data.get('doctor_id'),
                record_data['visit_date'],
                record_data.get('diagnosis', ''),
                record_data.get('treatment', ''),
                record_data.get('notes', '')
            )
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة السجل الطبي: {e}")
            self.conn.rollback()
            return None

    def update_medical_record(self, record_id, record_data):
        """تحديث سجل طبي"""
        try:
            query = '''
                UPDATE medical_records 
                SET patient_id=?, doctor_id=?, visit_date=?, diagnosis=?, treatment=?, notes=?
                WHERE id=?
            '''
            params = (
                record_data['patient_id'],
                record_data.get('doctor_id'),
                record_data['visit_date'],
                record_data.get('diagnosis', ''),
                record_data.get('treatment', ''),
                record_data.get('notes', ''),
                record_id
            )
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث السجل الطبي: {e}")
            self.conn.rollback()
            return False

    def delete_medical_record(self, record_id):
        """حذف سجل طبي"""
        try:
            query = "DELETE FROM medical_records WHERE id = ?"
            cursor = self.conn.cursor()
            cursor.execute(query, (record_id,))
            self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"❌ خطأ في حذف السجل الطبي: {e}")
            self.conn.rollback()
            return False

    def get_medical_record_by_id(self, record_id):
        """الحصول على سجل طبي بواسطة ID"""
        try:
            query = '''
                SELECT mr.*, d.name as doctor_name, p.name as patient_name
                FROM medical_records mr
                LEFT JOIN doctors d ON mr.doctor_id = d.id
                LEFT JOIN patients p ON mr.patient_id = p.id
                WHERE mr.id = ?
            '''
            cursor = self.conn.cursor()
            cursor.execute(query, (record_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            logging.error(f"❌ خطأ في جلب السجل الطبي: {e}")
            return None