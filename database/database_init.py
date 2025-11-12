# -*- coding: utf-8 -*-
import sqlite3
import logging
import os
import json
from datetime import datetime, date

class DatabaseInitMixin:
    """ميكسین تهيئة قاعدة البيانات وإنشاء الجداول"""
    
    def init_database(self):
        """تهيئة قاعدة البيانات وإنشاء الجداول المحسنة"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            
            self.create_tables()
            self.update_tables()
            self.add_sample_data()
            
            logging.info("✅ تم تهيئة قاعدة البيانات بنجاح")
        except Exception as e:
            logging.error(f"❌ فشل في تهيئة قاعدة البيانات: {e}")
            raise

    def create_tables(self):
        """إنشاء الجداول مع الإضافات الجديدة"""
        cursor = self.conn.cursor()
        
        # جدول العيادات (محدث)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clinics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                address TEXT,
                phone TEXT,
                email TEXT,
                country_code TEXT DEFAULT '+966',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول إعدادات الواتساب (جديد)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS whatsapp_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clinic_id INTEGER NOT NULL,
                provider_type TEXT DEFAULT 'whatsapp_web',
                api_key TEXT,
                api_secret TEXT,
                phone_number TEXT,
                country_code TEXT DEFAULT '+966',
                smartwats_template_id TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (clinic_id) REFERENCES clinics (id)
            )
        ''')
        
        # جدول قوالب الرسائل المحسن (جديد)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clinic_id INTEGER NOT NULL,
                template_name TEXT NOT NULL,
                template_type TEXT NOT NULL,
                template_content TEXT NOT NULL,
                variables TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (clinic_id) REFERENCES clinics (id)
            )
        ''')
        
        # جدول إحصائيات الرسائل (محدث ومصحح)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clinic_id INTEGER NOT NULL,
                patient_id INTEGER,
                appointment_id INTEGER,
                message_type TEXT,
                phone_number TEXT,
                country_code TEXT,
                status TEXT,
                provider TEXT,
                error_message TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (clinic_id) REFERENCES clinics (id)
            )
        ''')
        
        # الجداول الأساسية (موجودة سابقاً - محفوظة)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                clinic_id INTEGER NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
                gender TEXT CHECK(gender IN ('ذكر', 'أنثى')),
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                whatsapp_sent_at TIMESTAMP,
                reminder_24h_sent BOOLEAN DEFAULT 0,
                reminder_24h_sent_at TIMESTAMP,
                reminder_2h_sent BOOLEAN DEFAULT 0,
                reminder_2h_sent_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id),
                FOREIGN KEY (doctor_id) REFERENCES doctors (id),
                FOREIGN KEY (department_id) REFERENCES departments (id),
                FOREIGN KEY (clinic_id) REFERENCES clinics (id)
            )
        ''')
        
        # جدول إعدادات النظام (موجود سابقاً)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clinic_id INTEGER NOT NULL,
                setting_key TEXT NOT NULL,
                setting_value TEXT,
                setting_type TEXT DEFAULT 'text',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ──────────────────────────────────────────────────────────────────────
        # الجداول الجديدة المضافة
        # ──────────────────────────────────────────────────────────────────────
        
        # جدول العلامات (جديد)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patient_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                tag_name TEXT NOT NULL,
                color TEXT DEFAULT '#3498db',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE,
                UNIQUE(patient_id, tag_name)
            )
        ''')
        
        # جدول السجلات الطبية (جديد)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medical_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                doctor_id INTEGER,
                visit_date DATE NOT NULL,
                diagnosis TEXT,
                treatment TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id),
                FOREIGN KEY (doctor_id) REFERENCES doctors (id)
            )
        ''')
        
        self.conn.commit()
        logging.info("✅ تم إنشاء جميع الجداول بنجاح")

    def update_tables(self):
        """تحديث الجداول بإضافة الأعمدة المفقودة وإصلاح message_stats"""
        try:
            cursor = self.conn.cursor()
            
            # إضافة أعمدة الدول
            tables_to_update = {
                'clinics': ['country_code'],
                'patients': ['country_code'],
                'whatsapp_settings': ['country_code', 'smartwats_template_id'],
                'appointments': ['reminder_24h_sent', 'reminder_24h_sent_at', 'reminder_2h_sent', 'reminder_2h_sent_at', 'whatsapp_sent_at']
            }
            
            for table, columns in tables_to_update.items():
                cursor.execute(f"PRAGMA table_info({table})")
                existing_columns = [col[1] for col in cursor.fetchall()]
                
                for column in columns:
                    if column not in existing_columns:
                        if column == 'country_code':
                            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} TEXT")
                            cursor.execute(f"UPDATE {table} SET {column} = '+966' WHERE {column} IS NULL")
                        elif column.endswith('_sent'):
                            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} BOOLEAN DEFAULT 0")
                        elif column.endswith('_sent_at'):
                            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} TIMESTAMP")
                        else:
                            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} TEXT")
                        logging.info(f"✅ تم إضافة عمود {column} لجدول {table}")
            
            # ──────────────────────────────────────────────────────────────────────
            # تحديث جدول patients بإضافة الحقول المفقودة
            # ──────────────────────────────────────────────────────────────────────
            
            cursor.execute("PRAGMA table_info(patients)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            
            missing_columns = [
                ('emergency_contact', 'TEXT'),
                ('insurance_info', 'TEXT'), 
                ('medical_history', 'TEXT'),
                ('whatsapp_consent', 'BOOLEAN DEFAULT 0')
            ]
            
            for column_name, column_type in missing_columns:
                if column_name not in existing_columns:
                    cursor.execute(f'ALTER TABLE patients ADD COLUMN {column_name} {column_type}')
                    logging.info(f"✅ تم إضافة عمود {column_name} لجدول patients")
            
            # إصلاح جدول message_stats - التأكد من وجود جميع الأعمدة المطلوبة
            cursor.execute("PRAGMA table_info(message_stats)")
            stats_columns = [column[1] for column in cursor.fetchall()]
            
            # الأعمدة المطلوبة لجدول message_stats
            required_stats_columns = {
                'sent_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'provider': 'TEXT',
                'message_type': 'TEXT'
            }
            
            for column, definition in required_stats_columns.items():
                if column not in stats_columns:
                    cursor.execute(f"ALTER TABLE message_stats ADD COLUMN {column} {definition}")
                    logging.info(f"✅ تم إضافة عمود {column} لجدول message_stats")
            
            # تحديث القيم الافتراضية للتواريخ إذا كانت NULL
            cursor.execute("UPDATE message_stats SET sent_at = datetime('now') WHERE sent_at IS NULL")
            cursor.execute("UPDATE message_stats SET created_at = datetime('now') WHERE created_at IS NULL")
            cursor.execute("UPDATE message_stats SET provider = 'unknown' WHERE provider IS NULL")
            cursor.execute("UPDATE message_stats SET message_type = 'custom' WHERE message_type IS NULL")
            
            # تحديث جدول message_templates
            cursor.execute("PRAGMA table_info(message_templates)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # إضافة الأعمدة المفقودة في message_templates
            missing_columns = {
                'template_content': 'TEXT',
                'variables': 'TEXT',
                'is_active': 'BOOLEAN'
            }
            
            for column, definition in missing_columns.items():
                if column not in columns:
                    cursor.execute(f"ALTER TABLE message_templates ADD COLUMN {column} {definition}")
                    logging.info(f"✅ تم إضافة عمود {column} لجدول message_templates")
            
            # تحديث القيم الافتراضية
            cursor.execute("UPDATE message_templates SET template_content = '' WHERE template_content IS NULL")
            cursor.execute("UPDATE message_templates SET is_active = 1 WHERE is_active IS NULL")
            
            # إذا كان هناك عمود template_text، نقوم بنقل البيانات وحذفه
            if 'template_text' in columns:
                logging.info("🔄 اكتشاف عمود template_text قديم - جاري الترحيل...")
                
                # إذا لم يكن هناك عمود template_content، ننشئه
                if 'template_content' not in columns:
                    cursor.execute("ALTER TABLE message_templates ADD COLUMN template_content TEXT")
                
                # نقل البيانات من template_text إلى template_content
                cursor.execute("UPDATE message_templates SET template_content = template_text WHERE template_content IS NULL OR template_content = ''")
                
                # إنشاء جدول جديد بدون template_text
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS message_templates_migrated (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        clinic_id INTEGER NOT NULL,
                        template_name TEXT NOT NULL,
                        template_type TEXT NOT NULL,
                        template_content TEXT NOT NULL,
                        variables TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP,
                        FOREIGN KEY (clinic_id) REFERENCES clinics (id)
                    )
                ''')
                
                # نسخ البيانات
                cursor.execute('''
                    INSERT INTO message_templates_migrated 
                    (id, clinic_id, template_name, template_type, template_content, variables, is_active, created_at)
                    SELECT id, clinic_id, template_name, template_type, template_content, variables, is_active, created_at
                    FROM message_templates
                ''')
                
                # إسقاط الجدول القديم وإعادة التسمية
                cursor.execute("DROP TABLE message_templates")
                cursor.execute("ALTER TABLE message_templates_migrated RENAME TO message_templates")
                
                logging.info("✅ تم ترحيل جدول message_templates بنجاح")
            
            # التأكد من أن الجدول يحتوي على البيانات الأساسية
            cursor.execute("SELECT COUNT(*) FROM message_templates")
            if cursor.fetchone()[0] == 0:
                basic_templates = [
                    (1, 'ترحيب', 'welcome', 
                     'مرحباً {patient_name} 👋\n\nشكراً لحجز موعد في {clinic_name}\n📅 الموعد: {appointment_date}\n⏰ الوقت: {appointment_time}\n👨‍⚕️ الدكتور: {doctor_name}\n📍 القسم: {department_name}\n\nنرجو الحضور قبل الموعد بـ 15 دقيقة.\nللاستفسار: {clinic_phone}', 
                     '["patient_name", "clinic_name", "appointment_date", "appointment_time", "doctor_name", "department_name", "clinic_phone"]', 1),
                    
                    (1, 'تذكير 24 ساعة', 'reminder_24h',
                     'تذكير موعد غداً 🗓️\n\nعزيزي/عزيزتي {patient_name}\nموعدك غداً الساعة {appointment_time} مع د. {doctor_name}\nفي عيادة {clinic_name}\n\nنرجو التأكيد على الحضور 🌹',
                     '["patient_name", "appointment_time", "doctor_name", "clinic_name"]', 1),
                    
                    (1, 'تذكير ساعتين', 'reminder_2h',
                     '⏰ تذكير بالموعد بعد ساعتين\n\nعزيزي/عزيزتي {patient_name}\nموعدك بعد ساعتين الساعة {appointment_time}\nمع د. {doctor_name} في {clinic_name}\n\nنترقب زيارتكم 👨‍⚕️',
                     '["patient_name", "appointment_time", "doctor_name", "clinic_name"]', 1)
                ]
                
                cursor.executemany('''
                    INSERT INTO message_templates (clinic_id, template_name, template_type, template_content, variables, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', basic_templates)
                
                logging.info("✅ تم إضافة القوالب الأساسية إلى message_templates")
            
            self.conn.commit()
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث الجداول: {e}")
            self.conn.rollback()

    def add_sample_data(self):
        """إضافة بيانات نموذجية محسنة"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM clinics")
            clinic_count = cursor.fetchone()[0]
            
            if clinic_count == 0:
                # إضافة عيادات من دول مختلفة
                sample_clinics = [
                    ('مستشفى النور', 'مستشفى', 'الرياض، السعودية', '0123456789', 'info@alnoor.com', '+966'),
                    ('مركز الشفاء', 'مركز', 'دمشق، سوريا', '0981706728', 'info@alshifa.com', '+963'),
                    ('عيادة الأمل', 'عيادة', 'عمان، الأردن', '0791234567', 'info@alamal.com', '+962')
                ]
                
                cursor.executemany('''
                    INSERT INTO clinics (name, type, address, phone, email, country_code)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', sample_clinics)
                
                clinic_ids = [cursor.lastrowid - 2, cursor.lastrowid - 1, cursor.lastrowid]
                
                # إضافة إعدادات واتساب نموذجية
                whatsapp_settings = []
                for clinic_id in clinic_ids:
                    whatsapp_settings.extend([
                        (clinic_id, 'whatsapp_web', '', '', '', '+966', '', 1),
                        (clinic_id, 'smartwats', 'sample_api_key', 'sample_secret', '', '+966', 'welcome_template', 0)
                    ])
                
                cursor.executemany('''
                    INSERT INTO whatsapp_settings (clinic_id, provider_type, api_key, api_secret, phone_number, country_code, smartwats_template_id, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', whatsapp_settings)
                
                # إضافة قوالب رسائل محسنة
                sample_templates = [
                    (clinic_ids[0], 'ترحيب', 'welcome', 'مرحباً {patient_name} 👋\n\nشكراً لحجز موعد في {clinic_name}\n📅 الموعد: {appointment_date}\n⏰ الوقت: {appointment_time}\n👨‍⚕️ الدكتور: {doctor_name}\n📍 القسم: {department_name}\n\nنرجو الحضور قبل الموعد بـ 15 دقيقة.\nللاستفسار: {clinic_phone}', '["patient_name", "clinic_name", "appointment_date", "appointment_time", "doctor_name", "department_name", "clinic_phone"]', 1),
                    (clinic_ids[0], 'تذكير 24 ساعة', 'reminder_24h', 'تذكير موعد غداً 🗓️\n\nعزيزي/عزيزتي {patient_name}\nموعدك غداً الساعة {appointment_time} مع د. {doctor_name}\nفي عيادة {clinic_name}\n\nنرجو التأكيد على الحضور 👇', '["patient_name", "appointment_time", "doctor_name", "clinic_name"]', 1),
                    (clinic_ids[0], 'تذكير ساعتين', 'reminder_2h', '⏰ تذكير بالموعد بعد ساعتين\n\nعزيزي/عزيزتي {patient_name}\nموعدك بعد ساعتين الساعة {appointment_time}\nمع د. {doctor_name} في {clinic_name}\n\nنترقب زيارتكم 🌹', '["patient_name", "appointment_time", "doctor_name", "clinic_name"]', 1)
                ]
                
                cursor.executemany('''
                    INSERT INTO message_templates (clinic_id, template_name, template_type, template_content, variables, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', sample_templates)
                
                # إضافة أقسام وأطباء ومرضى (البيانات الأساسية)
                for clinic_id in clinic_ids:
                    # أقسام
                    cursor.execute('''
                        INSERT INTO departments (name, clinic_id, description)
                        VALUES (?, ?, ?)
                    ''', ('قسم الباطنية', clinic_id, 'قسم الأمراض الباطنية'))
                    
                    dept_id = cursor.lastrowid
                    
                    # أطباء
                    cursor.execute('''
                        INSERT INTO doctors (name, specialty, department_id, clinic_id, phone, email)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', ('د. أحمد محمد', 'الباطنية', dept_id, clinic_id, '0123456789', 'doctor@clinic.com'))
                    
                    # مرضى
                    cursor.execute('''
                        INSERT INTO patients (name, phone, country_code, email, gender, address)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', ('محمد أحمد', '0563333333', '+966', 'patient@test.com', 'ذكر', 'العنوان'))
                
                self.conn.commit()
                logging.info("✅ تم إضافة البيانات النموذجية المحسنة")
                
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة البيانات النموذجية: {e}")
            self.conn.rollback()