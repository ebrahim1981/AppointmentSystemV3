# -*- coding: utf-8 -*-
import sqlite3
import logging
from datetime import datetime
from database_core import DatabaseCore

class DataMigrator:
    """أداة ترحيل البيانات من النظام القديم إلى الجديد"""
    
    def __init__(self, old_db_path: str, new_db_path: str):
        self.old_db_path = old_db_path
        self.new_db = DatabaseCore(new_db_path)
    
    def migrate_all_data(self):
        """ترحيل جميع البيانات"""
        try:
            logging.info("🔄 بدء ترحيل البيانات...")
            
            # الاتصال بقاعدة البيانات القديمة
            old_conn = sqlite3.connect(self.old_db_path)
            old_conn.row_factory = sqlite3.Row
            
            # ترحيل العيادات
            self._migrate_clinics(old_conn)
            
            # ترحيل الأقسام
            self._migrate_departments(old_conn)
            
            # ترحيل الأطباء
            self._migrate_doctors(old_conn)
            
            # ترحيل المرضى
            self._migrate_patients(old_conn)
            
            # ترحيل المواعيد
            self._migrate_appointments(old_conn)
            
            old_conn.close()
            logging.info("✅ تم ترحيل جميع البيانات بنجاح")
            
        except Exception as e:
            logging.error(f"❌ خطأ في ترحيل البيانات: {e}")
            raise
    
    def _migrate_clinics(self, old_conn):
        """ترحيل العيادات"""
        cursor = old_conn.cursor()
        cursor.execute("SELECT * FROM clinics")
        
        for old_clinic in cursor.fetchall():
            old_dict = dict(old_clinic)
            
            clinic_data = {
                'code': f"CLN-{old_dict['id']:03d}",
                'name_ar': old_dict.get('name', 'عيادة بدون اسم'),
                'type': old_dict.get('type', 'clinic'),
                'address_ar': old_dict.get('address', ''),
                'phone': old_dict.get('phone', ''),
                'country_code': old_dict.get('country_code', '+966'),
                'status': 'active' if old_dict.get('is_active', 1) else 'inactive'
            }
            
            self.new_db.add_clinic(clinic_data)
        
        logging.info("✅ تم ترحيل العيادات")
    
    def _migrate_doctors(self, old_conn):
        """ترحيل الأطباء"""
        cursor = old_conn.cursor()
        cursor.execute("SELECT * FROM doctors")
        
        for old_doctor in cursor.fetchall():
            old_dict = dict(old_doctor)
            
            doctor_data = {
                'license_number': f"DOC-{old_dict['id']:03d}",
                'first_name_ar': old_dict.get('name', 'طبيب').split()[0] if ' ' in old_dict.get('name', '') else old_dict.get('name', 'طبيب'),
                'last_name_ar': old_dict.get('name', 'بدون اسم').split()[-1] if ' ' in old_dict.get('name', '') else ' ',
                'specialty_ar': old_dict.get('specialty', 'عام'),
                'phone': old_dict.get('phone', ''),
                'country_code': old_dict.get('country_code', '+966'),
                'status': 'active' if old_dict.get('is_active', 1) else 'inactive'
            }
            
            self.new_db.add_doctor(doctor_data)
        
        logging.info("✅ تم ترحيل الأطباء")

# استخدام الأداة
if __name__ == "__main__":
    migrator = DataMigrator("data/old_clinics.db", "data/clinics_professional.db")
    migrator.migrate_all_data()