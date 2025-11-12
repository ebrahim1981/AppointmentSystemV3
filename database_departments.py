# -*- coding: utf-8 -*-
import logging

class DepartmentsMixin:
    """ميكسین إدارة الأقسام"""
    
    def get_departments(self, clinic_id=None):
        """الحصول على قائمة الأقسام"""
        try:
            if clinic_id:
                query = '''
                    SELECT d.*, c.name as clinic_name 
                    FROM departments d 
                    JOIN clinics c ON d.clinic_id = c.id 
                    WHERE d.clinic_id = ?
                    ORDER BY d.name
                '''
                params = (clinic_id,)
            else:
                query = '''
                    SELECT d.*, c.name as clinic_name 
                    FROM departments d 
                    JOIN clinics c ON d.clinic_id = c.id 
                    ORDER BY c.name, d.name
                '''
                params = ()
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            departments = []
            for row in rows:
                departments.append(dict(row))
            
            return departments
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب الأقسام: {e}")
            return []
    
    def get_department_by_id(self, department_id):
        """الحصول على بيانات قسم بواسطة ID"""
        try:
            query = '''
                SELECT d.*, c.name as clinic_name 
                FROM departments d 
                JOIN clinics c ON d.clinic_id = c.id 
                WHERE d.id = ?
            '''
            cursor = self.conn.cursor()
            cursor.execute(query, (department_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب بيانات القسم: {e}")
            return None
    
    def add_department(self, department_data):
        """إضافة قسم جديد"""
        try:
            query = '''
                INSERT INTO departments (name, clinic_id, description)
                VALUES (?, ?, ?)
            '''
            params = (
                department_data['name'],
                department_data['clinic_id'],
                department_data.get('description', '')
            )
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            
            department_id = cursor.lastrowid
            return department_id
            
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة القسم: {e}")
            self.conn.rollback()
            return None
    
    def update_department(self, department_id, department_data):
        """تحديث بيانات القسم"""
        try:
            query = '''
                UPDATE departments 
                SET name=?, clinic_id=?, description=?
                WHERE id=?
            '''
            params = (
                department_data['name'],
                department_data['clinic_id'],
                department_data.get('description', ''),
                department_id
            )
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            
            logging.info(f"✅ تم تحديث القسم: {department_data['name']} - ID: {department_id}")
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث القسم: {e}")
            self.conn.rollback()
            return False
    
    def toggle_department_status(self, department_id, is_active):
        """تفعيل/إيقاف القسم"""
        try:
            query = 'UPDATE departments SET is_active = ? WHERE id = ?'
            cursor = self.conn.cursor()
            cursor.execute(query, (is_active, department_id))
            self.conn.commit()
            
            status_text = "تفعيل" if is_active else "إيقاف"
            logging.info(f"✅ تم {status_text} القسم برقم: {department_id}")
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في تغيير حالة القسم: {e}")
            self.conn.rollback()
            return False