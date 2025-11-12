# -*- coding: utf-8 -*-
import logging

class DoctorsMixin:
    """ميكسین إدارة الأطباء"""
    
    def get_doctors(self, department_id=None, clinic_id=None):
        """الحصول على قائمة الأطباء"""
        try:
            query = '''
                SELECT d.*, dept.name as department_name, c.name as clinic_name 
                FROM doctors d 
                LEFT JOIN departments dept ON d.department_id = dept.id 
                LEFT JOIN clinics c ON d.clinic_id = c.id 
                WHERE 1=1
            '''
            params = []
            
            if department_id:
                query += ' AND d.department_id = ?'
                params.append(department_id)
            if clinic_id:
                query += ' AND d.clinic_id = ?'
                params.append(clinic_id)
            
            query += ' ORDER BY d.name'
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            doctors = [dict(row) for row in rows]
            return doctors
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب الأطباء: {e}")
            return []
    
    def get_doctor_by_id(self, doctor_id):
        """الحصول على بيانات طبيب بواسطة ID"""
        try:
            query = '''
                SELECT d.*, dept.name as department_name, c.name as clinic_name 
                FROM doctors d 
                LEFT JOIN departments dept ON d.department_id = dept.id 
                LEFT JOIN clinics c ON d.clinic_id = c.id 
                WHERE d.id = ?
            '''
            cursor = self.conn.cursor()
            cursor.execute(query, (doctor_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب بيانات الطبيب: {e}")
            return None
    
    def add_doctor(self, doctor_data):
        """إضافة طبيب جديد"""
        try:
            query = '''
                INSERT INTO doctors (name, specialty, department_id, clinic_id, phone, email)
                VALUES (?, ?, ?, ?, ?, ?)
            '''
            params = (
                doctor_data['name'],
                doctor_data['specialty'],
                doctor_data['department_id'],
                doctor_data['clinic_id'],
                doctor_data.get('phone', ''),
                doctor_data.get('email', '')
            )
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            
            doctor_id = cursor.lastrowid
            return doctor_id
            
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة الطبيب: {e}")
            self.conn.rollback()
            return None
    
    def update_doctor(self, doctor_id, doctor_data):
        """تحديث بيانات الطبيب"""
        try:
            query = '''
                UPDATE doctors 
                SET name=?, specialty=?, department_id=?, clinic_id=?, phone=?, email=?
                WHERE id=?
            '''
            params = (
                doctor_data['name'],
                doctor_data['specialty'],
                doctor_data['department_id'],
                doctor_data['clinic_id'],
                doctor_data.get('phone', ''),
                doctor_data.get('email', ''),
                doctor_id
            )
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            
            logging.info(f"✅ تم تحديث الطبيب: {doctor_data['name']} - ID: {doctor_id}")
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث الطبيب: {e}")
            self.conn.rollback()
            return False
    
    def toggle_doctor_status(self, doctor_id, is_active):
        """تفعيل/إيقاف الطبيب"""
        try:
            query = 'UPDATE doctors SET is_active = ? WHERE id = ?'
            cursor = self.conn.cursor()
            cursor.execute(query, (is_active, doctor_id))
            self.conn.commit()
            
            status_text = "تفعيل" if is_active else "إيقاف"
            logging.info(f"✅ تم {status_text} الطبيب برقم: {doctor_id}")
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في تغيير حالة الطبيب: {e}")
            self.conn.rollback()
            return False