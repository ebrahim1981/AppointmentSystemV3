# -*- coding: utf-8 -*-
import sqlite3
import logging
import os
from datetime import datetime, timedelta

# استيراد الميكسينات
from database_init import DatabaseInitMixin
from database_whatsapp import WhatsAppMixin
from database_clinics import ClinicsMixin
from database_departments import DepartmentsMixin
from database_doctors import DoctorsMixin
from database_patients import PatientsMixin
from database_appointments import AppointmentsMixin
from database_utils import DatabaseUtilsMixin
from database_scheduling import SchedulingMixin  # نظام الجدولة الذكية

class DatabaseManager(
    DatabaseInitMixin,
    WhatsAppMixin,
    ClinicsMixin,
    DepartmentsMixin,
    DoctorsMixin,
    PatientsMixin,
    AppointmentsMixin,
    DatabaseUtilsMixin,
    SchedulingMixin  # إضافة نظام الجدولة
):
    """مدير قاعدة البيانات - الجسر الخفيف المتكامل"""
    
    def __init__(self, db_path="data/clinics.db"):
        self.db_path = db_path
        self.conn = None
        self.init_database()

    def init_database(self):
        """تهيئة قاعدة البيانات - الإصدار الخفيف"""
        try:
            # إنشاء المجلد
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # الاتصال بقاعدة البيانات
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")
            
            logging.info(f"تم الاتصال بقاعدة البيانات: {self.db_path}")
            
            # إنشاء الجداول الأساسية
            self.create_tables()
            
            # تهيئة البيانات الافتراضية
            self.init_default_data()
            
            # تهيئة نظام الجدولة الذكية
            self.initialize_scheduling_system()
            
            logging.info("✅ تم تهيئة قاعدة البيانات بنجاح")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تهيئة قاعدة البيانات: {e}")
            raise

    def create_tables(self):
        """إنشاء الجداول الأساسية"""
        try:
            cursor = self.conn.cursor()
            
            # الجداول الأساسية الحالية (بدون تعديل)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clinics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    address TEXT,
                    phone TEXT,
                    country_code TEXT DEFAULT '+966',
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS departments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clinic_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (clinic_id) REFERENCES clinics (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS doctors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    specialty TEXT NOT NULL,
                    department_id INTEGER NOT NULL,
                    clinic_id INTEGER NOT NULL,
                    phone TEXT,
                    email TEXT,
                    national_id TEXT,
                    license_number TEXT,
                    consultation_fee REAL DEFAULT 100.0,
                    working_hours TEXT,
                    notes TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (department_id) REFERENCES departments (id),
                    FOREIGN KEY (clinic_id) REFERENCES clinics (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    country_code TEXT DEFAULT '+966',
                    email TEXT,
                    date_of_birth DATE,
                    gender TEXT,
                    address TEXT,
                    medical_history TEXT,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    doctor_id INTEGER NOT NULL,
                    department_id INTEGER NOT NULL,
                    clinic_id INTEGER NOT NULL,
                    appointment_date DATE NOT NULL,
                    appointment_time TIME NOT NULL,
                    type TEXT DEFAULT 'كشف',
                    status TEXT DEFAULT 'مجدول',
                    notes TEXT,
                    whatsapp_sent BOOLEAN DEFAULT 0,
                    whatsapp_sent_at DATETIME,
                    reminder_24h_sent BOOLEAN DEFAULT 0,
                    reminder_24h_sent_at DATETIME,
                    reminder_2h_sent BOOLEAN DEFAULT 0,
                    reminder_2h_sent_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id),
                    FOREIGN KEY (doctor_id) REFERENCES doctors (id),
                    FOREIGN KEY (department_id) REFERENCES departments (id),
                    FOREIGN KEY (clinic_id) REFERENCES clinics (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS medical_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    doctor_id INTEGER,
                    visit_date DATE NOT NULL,
                    diagnosis TEXT,
                    treatment TEXT,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id),
                    FOREIGN KEY (doctor_id) REFERENCES doctors (id)
                )
            ''')
            
            # إنشاء جداول الجدولة الذكية (من scheduling.py)
            self.create_scheduling_tables()
            
            self.conn.commit()
            logging.info("✅ تم إنشاء جميع الجداول بنجاح")
            
        except Exception as e:
            logging.error(f"❌ خطأ في إنشاء الجداول: {e}")
            self.conn.rollback()
            raise

    def init_default_data(self):
        """تهيئة البيانات الافتراضية"""
        try:
            cursor = self.conn.cursor()
            
            # البيانات الافتراضية الحالية
            cursor.execute('''
                INSERT OR IGNORE INTO clinics (id, name, type, address, phone) 
                VALUES (1, 'عيادة النور', 'خاصة', 'الرياض - حي الملز', '0112345678')
            ''')
            
            cursor.execute('''
                INSERT OR IGNORE INTO departments (id, clinic_id, name, description) 
                VALUES 
                (1, 1, 'الباطنية', 'قسم الباطنية والجهاز الهضمي'),
                (2, 1, 'الجلدية', 'قسم الأمراض الجلدية والتناسلية'),
                (3, 1, 'العظام', 'قسم العظام والمفاصل')
            ''')
            
            cursor.execute('''
                INSERT OR IGNORE INTO doctors (id, name, specialty, department_id, clinic_id, phone) 
                VALUES 
                (1, 'د. أحمد محمد', 'باطنية', 1, 1, '0551111111'),
                (2, 'د. فاطمة خالد', 'جلدية', 2, 1, '0552222222'),
                (3, 'د. عمر عبدالله', 'عظام', 3, 1, '0553333333')
            ''')
            
            self.conn.commit()
            logging.info("✅ تم تهيئة البيانات الافتراضية بنجاح")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تهيئة البيانات الافتراضية: {e}")
            self.conn.rollback()

    def initialize_scheduling_system(self):
        """تهيئة نظام الجدولة الذكية - استدعاء من scheduling.py"""
        try:
            logging.info("🔄 جاري تهيئة نظام الجدولة الذكية...")
            
            # إنشاء جدول أنواع الخدمات
            self.create_service_types_table()
            
            # تهيئة الجداول الافتراضية للجدولة
            self.initialize_default_schedules()
            
            # التحقق من التكامل
            integration_status = self.check_scheduling_integration()
            
            if integration_status['success']:
                logging.info("✅ تم تهيئة نظام الجدولة الذكية بنجاح")
            else:
                logging.warning(f"⚠️ تم تهيئة النظام مع بعض التحذيرات: {integration_status.get('issues', [])}")
            
            return integration_status
            
        except Exception as e:
            logging.error(f"❌ خطأ في تهيئة نظام الجدولة: {e}")
            return {'success': False, 'error': str(e)}

    def check_scheduling_integration(self):
        """فحص تكامل نظام الجدولة - استدعاء من scheduling.py"""
        try:
            status = {
                'success': True,
                'doctors_count': 0,
                'doctors_with_schedules': 0,
                'service_types_count': 0,
                'issues': []
            }
            
            # فحص الأطباء
            doctors = self.get_doctors()
            status['doctors_count'] = len(doctors) if doctors else 0
            
            for doctor in doctors:
                schedule = self.get_doctor_schedule_settings(doctor['id'])
                if schedule:
                    status['doctors_with_schedules'] += 1
            
            # فحص أنواع الخدمات
            service_types = self.get_service_types()
            status['service_types_count'] = len(service_types) if service_types else 0
            
            # تسجيل المشاكل
            if status['doctors_count'] == 0:
                status['issues'].append("لا توجد أطباء في النظام")
                status['success'] = False
            
            if status['doctors_with_schedules'] == 0:
                status['issues'].append("لا توجد جداول زمنية للأطباء")
            
            if status['service_types_count'] == 0:
                status['issues'].append("لا توجد أنواع خدمات")
            
            logging.info(f"📊 حالة التكامل: {status['doctors_with_schedules']}/{status['doctors_count']} طبيب لديهم جداول")
            
            return status
            
        except Exception as e:
            logging.error(f"❌ خطأ في فحص التكامل: {e}")
            return {'success': False, 'error': str(e)}

    def get_scheduling_overview(self):
        """نظرة عامة على نظام الجدولة - استدعاء من scheduling.py"""
        try:
            overview = {
                'total_doctors': 0,
                'doctors_with_schedules': 0,
                'total_service_types': 0,
                'next_available_slots': []
            }
            
            # إحصائيات الأطباء
            doctors = self.get_doctors()
            overview['total_doctors'] = len(doctors) if doctors else 0
            
            for doctor in doctors:
                if self.get_doctor_schedule_settings(doctor['id']):
                    overview['doctors_with_schedules'] += 1
            
            # إحصائيات الخدمات
            service_types = self.get_service_types()
            overview['total_service_types'] = len(service_types) if service_types else 0
            
            # أوقات متاحة قريبة
            if doctors and len(doctors) > 0:
                doctor_id = doctors[0]['id']
                tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                slots = self.get_available_slots(doctor_id, tomorrow)
                overview['next_available_slots'] = slots[:3] if slots else []
            
            return overview
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب نظرة الجدولة: {e}")
            return {}

    def get_doctor(self, doctor_id):
        """الحصول على بيانات طبيب محدد"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT d.*, dept.name as department_name, c.name as clinic_name 
                FROM doctors d 
                LEFT JOIN departments dept ON d.department_id = dept.id 
                LEFT JOIN clinics c ON d.clinic_id = c.id 
                WHERE d.id = ?
            ''', (doctor_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logging.error(f"❌ خطأ في جلب بيانات الطبيب: {e}")
            return None

    def get_patient_appointment_stats(self, patient_phone=None):
        """الحصول على إحصائيات مواعيد المريض - الإصدار المصحح"""
        try:
            cursor = self.conn.cursor()
            
            if patient_phone:
                # البحث عن patient_id أولاً باستخدام الهاتف
                cursor.execute('SELECT id FROM patients WHERE phone = ?', (patient_phone,))
                patient_result = cursor.fetchone()
                
                if patient_result:
                    patient_id = patient_result['id']
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total_appointments,
                            SUM(CASE WHEN status = 'مكتمل' THEN 1 ELSE 0 END) as completed,
                            SUM(CASE WHEN status = 'ملغي' THEN 1 ELSE 0 END) as cancelled,
                            SUM(CASE WHEN appointment_date >= DATE('now') THEN 1 ELSE 0 END) as upcoming
                        FROM appointments 
                        WHERE patient_id = ?
                    ''', (patient_id,))
                else:
                    # إذا لم يتم العثور على المريض، إرجاع إحصائيات صفرية
                    return {
                        'total_appointments': 0,
                        'completed': 0,
                        'cancelled': 0,
                        'upcoming': 0
                    }
            else:
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_appointments,
                        SUM(CASE WHEN status = 'مكتمل' THEN 1 ELSE 0 END) as completed,
                        SUM(CASE WHEN status = 'ملغي' THEN 1 ELSE 0 END) as cancelled,
                        SUM(CASE WHEN appointment_date >= DATE('now') THEN 1 ELSE 0 END) as upcoming
                    FROM appointments
                ''')
            
            result = cursor.fetchone()
            return dict(result) if result else {
                'total_appointments': 0,
                'completed': 0,
                'cancelled': 0,
                'upcoming': 0
            }
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب إحصائيات المواعيد: {e}")
            return {
                'total_appointments': 0,
                'completed': 0,
                'cancelled': 0,
                'upcoming': 0
            }

    def verify_doctor_schedule(self, doctor_id):
        """التحقق من جدول الطبيب وعرض النتائج"""
        try:
            result = self.verify_schedule_creation(doctor_id)
            
            doctor_info = self.get_doctor(doctor_id)
            doctor_name = doctor_info['name'] if doctor_info else f"الطبيب {doctor_id}"
            
            if result['success']:
                logging.info(f"✅ تم التحقق من جدول الطبيب {doctor_name}: {result['message']}")
            else:
                logging.warning(f"⚠️ مشكلة في جدول الطبيب {doctor_name}: {result['message']}")
                
            return result
            
        except Exception as e:
            logging.error(f"❌ خطأ في التحقق من جدول الطبيب: {e}")
            return {'success': False, 'message': f'خطأ في التحقق: {e}'}

    def get_service_types(self):
        """الحصول على أنواع الخدمات - دالة مساعدة للتكامل"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM service_types WHERE is_active = 1')
            rows = cursor.fetchall()
            return [dict(row) for row in rows] if rows else []
        except Exception as e:
            logging.error(f"❌ خطأ في جلب أنواع الخدمات: {e}")
            return []

    def create_service_types_table(self):
        """إنشاء جدول أنواع الخدمات إذا لم يكن موجوداً"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS service_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    default_duration INTEGER NOT NULL,
                    color_code TEXT DEFAULT '#3498db',
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # إضافة البيانات الافتراضية
            default_services = [
                ('كشف عام', 30, '#3498db'),
                ('كشف أطفال', 45, '#e74c3c'),
                ('كشف نساء', 60, '#9b59b6'),
                ('طوارئ', 15, '#e67e22'),
                ('متابعة', 20, '#2ecc71')
            ]
            
            for service in default_services:
                cursor.execute('''
                    INSERT OR IGNORE INTO service_types (name, default_duration, color_code)
                    VALUES (?, ?, ?)
                ''', service)
            
            self.conn.commit()
            logging.info("✅ تم إنشاء/تأكيد جدول أنواع الخدمات")
            
        except Exception as e:
            logging.error(f"❌ خطأ في إنشاء جدول أنواع الخدمات: {e}")
            self.conn.rollback()

    def initialize_default_schedules(self):
        """تهيئة الجداول الافتراضية للجدولة"""
        try:
            # الحصول على جميع الأطباء
            doctors = self.get_doctors()
            
            for doctor in doctors:
                # التحقق إذا كان الطبيب لديه إعدادات جدولة
                schedule_settings = self.get_doctor_schedule_settings(doctor['id'])
                
                if not schedule_settings:
                    # إنشاء إعدادات افتراضية للطبيب
                    self.setup_doctor_schedule(
                        doctor_id=doctor['id'],
                        appointment_duration=30,
                        work_days=['sunday', 'monday', 'tuesday', 'wednesday', 'thursday'],
                        work_start="08:00",
                        work_end="17:00"
                    )
                    logging.info(f"✅ تم إنشاء إعدادات جدولة افتراضية للطبيب: {doctor['name']}")
            
            logging.info("✅ تم تهيئة الجداول الافتراضية للجدولة")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تهيئة الجداول الافتراضية: {e}")

    def close(self):
        """إغلاق connection قاعدة البيانات"""
        if self.conn:
            self.conn.close()
            logging.info("تم إغلاق connection قاعدة البيانات")

# اختبار التشغيل
if __name__ == "__main__":
    try:
        db = DatabaseManager()
        
        # اختبار شامل
        overview = db.get_scheduling_overview()
        print(f"نظرة عامة على الجدولة: {overview}")
        
        # اختبار الدوال المضافة
        doctor = db.get_doctor(1)
        print(f"بيانات الطبيب: {doctor}")
        
        stats = db.get_patient_appointment_stats()
        print(f"إحصائيات المواعيد: {stats}")
        
        verification = db.verify_doctor_schedule(1)
        print(f"نتيجة التحقق: {verification}")
        
        db.close()
        print("✅ تم اختبار النظام بنجاح!")
        
    except Exception as e:
        print(f"❌ خطأ في اختبار النظام: {e}")