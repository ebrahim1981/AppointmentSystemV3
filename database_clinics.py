# -*- coding: utf-8 -*-
import logging

class ClinicsMixin:
    """ميكسین إدارة العيادات"""
    
    def get_clinics(self):
        """الحصول على قائمة العيادات"""
        try:
            query = 'SELECT * FROM clinics ORDER BY name'
            cursor = self.conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            
            clinics = [dict(row) for row in rows]
            return clinics
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب العيادات: {e}")
            return []
    
    def get_clinic_by_id(self, clinic_id):
        """الحصول على بيانات عيادة بواسطة ID"""
        try:
            query = 'SELECT * FROM clinics WHERE id = ?'
            cursor = self.conn.cursor()
            cursor.execute(query, (clinic_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب بيانات العيادة: {e}")
            return None
    
    def add_clinic(self, clinic_data):
        """إضافة عيادة جديدة"""
        try:
            query = '''
                INSERT INTO clinics (name, type, address, phone, email, country_code)
                VALUES (?, ?, ?, ?, ?, ?)
            '''
            params = (
                clinic_data['name'],
                clinic_data['type'],
                clinic_data.get('address', ''),
                clinic_data.get('phone', ''),
                clinic_data.get('email', ''),
                clinic_data.get('country_code', '+966')
            )
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            
            clinic_id = cursor.lastrowid
            return clinic_id
            
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة العيادة: {e}")
            self.conn.rollback()
            return None
    
    def update_clinic(self, clinic_id, clinic_data):
        """تحديث بيانات العيادة"""
        try:
            query = '''
                UPDATE clinics 
                SET name=?, type=?, address=?, phone=?, email=?, country_code=?
                WHERE id=?
            '''
            params = (
                clinic_data['name'],
                clinic_data['type'],
                clinic_data.get('address', ''),
                clinic_data.get('phone', ''),
                clinic_data.get('email', ''),
                clinic_data.get('country_code', '+966'),
                clinic_id
            )
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            
            logging.info(f"✅ تم تحديث العيادة: {clinic_data['name']} - ID: {clinic_id}")
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث العيادة: {e}")
            self.conn.rollback()
            return False
    
    def toggle_clinic_status(self, clinic_id, is_active):
        """تفعيل/إيقاف العيادة"""
        try:
            query = 'UPDATE clinics SET is_active = ? WHERE id = ?'
            cursor = self.conn.cursor()
            cursor.execute(query, (is_active, clinic_id))
            self.conn.commit()
            
            status_text = "تفعيل" if is_active else "إيقاف"
            logging.info(f"✅ تم {status_text} العيادة برقم: {clinic_id}")
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في تغيير حالة العيادة: {e}")
            self.conn.rollback()
            return False