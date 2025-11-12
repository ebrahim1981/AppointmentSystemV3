# -*- coding: utf-8 -*-
import logging
import json
from datetime import datetime, timedelta, time, date
from typing import List, Dict, Optional, Union

class SchedulingMixin:
    """ميكسین إدارة الجدولة الذكية المتكاملة - الإصدار النهائي المتكامل والمصحح"""

    def create_scheduling_tables(self):
        """إنشاء جداول الجدولة الذكية المتكاملة - الإصدار المحسن والمصحح"""
        try:
            cursor = self.conn.cursor()
            
            # ⭐⭐ الجداول الأساسية المعدلة للتكامل ⭐⭐
            
            # جدول إعدادات الأطباء الأساسية - معدل للتكامل
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS doctor_schedule_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doctor_id INTEGER NOT NULL UNIQUE,
                    work_days TEXT NOT NULL DEFAULT '["sunday", "monday", "tuesday", "wednesday", "thursday"]',
                    work_hours_start TIME NOT NULL DEFAULT '08:00',
                    work_hours_end TIME NOT NULL DEFAULT '17:00',
                    appointment_duration INTEGER DEFAULT 30,
                    break_times TEXT DEFAULT '[{"start": "12:00", "end": "13:00", "reason": "استراحة غداء"}]',
                    max_patients_per_day INTEGER DEFAULT 20,
                    allow_overbooking BOOLEAN DEFAULT 0,
                    buffer_time INTEGER DEFAULT 5,
                    work_periods TEXT DEFAULT '[{"start": "08:00", "end": "17:00", "type": "main", "is_active": true}]',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE CASCADE
                )
            ''')
            
            # ⭐⭐ الجدول الجديد: فترات العمل المتعددة ⭐⭐
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS doctor_work_periods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doctor_id INTEGER NOT NULL,
                    period_type TEXT NOT NULL, -- main, evening, part_time, custom
                    start_time TIME NOT NULL,
                    end_time TIME NOT NULL,
                    days_of_week TEXT NOT NULL, -- JSON array
                    is_active BOOLEAN DEFAULT 1,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE CASCADE
                )
            ''')
            
            # ⭐⭐ الجدول الجديد: الجداول الدورية للطبيب ⭐⭐
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS doctor_periodic_schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doctor_id INTEGER NOT NULL,
                    schedule_date DATE NOT NULL,
                    time_slot TIME NOT NULL,
                    slot_duration INTEGER DEFAULT 30,
                    status TEXT NOT NULL DEFAULT 'available', -- available, booked, blocked, break
                    appointment_id INTEGER NULL,
                    slot_type TEXT DEFAULT 'regular', -- regular, emergency, followup
                    period_type TEXT DEFAULT 'main', -- نوع الفترة
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(doctor_id, schedule_date, time_slot),
                    FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE CASCADE,
                    FOREIGN KEY (appointment_id) REFERENCES appointments (id) ON DELETE SET NULL
                )
            ''')
            
            # ⭐⭐ الجدول الجديد: إعدادات الجدولة الدورية ⭐⭐
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS periodic_schedule_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doctor_id INTEGER NOT NULL UNIQUE,
                    schedule_period_days INTEGER DEFAULT 30,
                    auto_renew_enabled BOOLEAN DEFAULT 1,
                    renewal_advance_days INTEGER DEFAULT 7,
                    last_renewal_date DATE,
                    next_renewal_date DATE,
                    max_daily_appointments INTEGER DEFAULT 15,
                    slot_interval INTEGER DEFAULT 30,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE CASCADE
                )
            ''')
            
            # جدول أنواع الخدمات
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
            
            # جدول الاستثناءات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schedule_exceptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doctor_id INTEGER NOT NULL,
                    exception_date DATE NOT NULL,
                    exception_type TEXT NOT NULL,
                    start_time TIME,
                    end_time TIME,
                    reason TEXT,
                    is_all_day BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE CASCADE
                )
            ''')
            
            self.conn.commit()
            logging.info("✅ تم إنشاء جداول الجدولة الذكية المحسنة بنجاح")
            
            # ⭐⭐ إضافة الأعمدة المفقودة للتكامل ⭐⭐
            self.add_missing_columns()
            
            # إنشاء البيانات الافتراضية
            self.create_default_service_types()
            self.initialize_default_periodic_settings()
            
        except Exception as e:
            logging.error(f"❌ خطأ في إنشاء جداول الجدولة: {e}")
            self.conn.rollback()

    def add_missing_columns(self):
        """إضافة الأعمدة المفقودة للتكامل مع النظام الحالي - الإصدار المصحح"""
        try:
            cursor = self.conn.cursor()
            
            # التحقق من وجود الأعمدة في doctor_schedule_settings
            cursor.execute("PRAGMA table_info(doctor_schedule_settings)")
            existing_columns = [column[1] for column in cursor.fetchall()]
            
            columns_to_add = [
                ('work_hours_start', 'TIME NOT NULL DEFAULT "08:00"'),
                ('work_hours_end', 'TIME NOT NULL DEFAULT "17:00"'),
                ('buffer_time', 'INTEGER DEFAULT 5'),
                ('allow_overbooking', 'BOOLEAN DEFAULT 0'),
                ('work_periods', 'TEXT DEFAULT \'[{"start": "08:00", "end": "17:00", "type": "main", "is_active": true}]\'')
            ]
            
            for column_name, column_def in columns_to_add:
                if column_name not in existing_columns:
                    try:
                        cursor.execute(f'ALTER TABLE doctor_schedule_settings ADD COLUMN {column_name} {column_def}')
                        logging.info(f"✅ تم إضافة عمود {column_name}")
                    except Exception as e:
                        logging.warning(f"⚠️ تعذر إضافة العمود {column_name}: {e}")
            
            # التحقق من وجود الأعمدة في doctor_periodic_schedules
            cursor.execute("PRAGMA table_info(doctor_periodic_schedules)")
            existing_columns = [column[1] for column in cursor.fetchall()]
            
            periodic_columns_to_add = [
                ('period_type', 'TEXT DEFAULT "main"')
            ]
            
            for column_name, column_def in periodic_columns_to_add:
                if column_name not in existing_columns:
                    try:
                        cursor.execute(f'ALTER TABLE doctor_periodic_schedules ADD COLUMN {column_name} {column_def}')
                        logging.info(f"✅ تم إضافة عمود {column_name} لجدول الجداول الدورية")
                    except Exception as e:
                        logging.warning(f"⚠️ تعذر إضافة العمود {column_name}: {e}")
            
            self.conn.commit()
            
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة الأعمدة المفقودة: {e}")
            self.conn.rollback()

    def safe_json_loads(self, json_str: Union[str, list, dict]) -> Union[list, dict]:
        """تحميل JSON بشكل آمن مع معالجة الأخطاء - الإصدار المحسن"""
        try:
            if isinstance(json_str, (list, dict)):
                return json_str
            elif isinstance(json_str, str) and json_str.strip():
                return json.loads(json_str)
            else:
                return []
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logging.warning(f"⚠️ خطأ في تحليل JSON، استخدام القيمة الافتراضية: {e}")
            return []

    def create_default_service_types(self):
        """إنشاء أنواع الخدمات الافتراضية"""
        try:
            cursor = self.conn.cursor()
            
            default_services = [
                ('كشف عام', 30, '#3498db'),
                ('كشف أطفال', 45, '#e74c3c'),
                ('كشف نساء', 60, '#9b59b6'),
                ('طوارئ', 15, '#e67e22'),
                ('متابعة', 20, '#2ecc71'),
                ('تحاليل', 30, '#f1c40f'),
                ('أشعة', 45, '#1abc9c')
            ]
            
            for service in default_services:
                cursor.execute('''
                    INSERT OR IGNORE INTO service_types (name, default_duration, color_code)
                    VALUES (?, ?, ?)
                ''', service)
            
            self.conn.commit()
            logging.info("✅ تم إنشاء أنواع الخدمات الافتراضية")
            
        except Exception as e:
            logging.error(f"❌ خطأ في إنشاء أنواع الخدمات: {e}")

    def initialize_default_periodic_settings(self):
        """تهيئة الإعدادات الدورية الافتراضية لجميع الأطباء"""
        try:
            cursor = self.conn.cursor()
            
            # الحصول على جميع الأطباء
            cursor.execute("SELECT id FROM doctors")
            doctors = cursor.fetchall()
            
            for doctor in doctors:
                doctor_id = doctor['id']
                
                # إدخال الإعدادات الدورية إذا لم تكن موجودة
                cursor.execute('''
                    INSERT OR IGNORE INTO periodic_schedule_settings 
                    (doctor_id, schedule_period_days, auto_renew_enabled, renewal_advance_days)
                    VALUES (?, 30, 1, 7)
                ''', (doctor_id,))
            
            self.conn.commit()
            logging.info(f"✅ تم تهيئة الإعدادات الدورية لـ {len(doctors)} طبيب")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تهيئة الإعدادات الدورية: {e}")

    # ⭐⭐ الوظائف الأساسية للجدولة المتكاملة ⭐⭐

    def setup_doctor_schedule(self, doctor_id: int, appointment_duration: int = 30, 
                            work_days: List[str] = None, work_start: str = "08:00", 
                            work_end: str = "17:00", breaks: List[Dict] = None, 
                            buffer_time: int = 5, work_periods: List[Dict] = None, **kwargs) -> bool:
        """إعداد جدول الطبيب - معدل للتكامل مع النظام الحالي - الإصدار المصحح"""
        try:
            if work_days is None:
                work_days = ["sunday", "monday", "tuesday", "wednesday", "thursday"]
            
            if breaks is None:
                breaks = [{"start": "12:00", "end": "13:00", "reason": "استراحة غداء"}]
            
            if work_periods is None:
                # إنشاء فترات العمل المتعددة من الإعدادات التقليدية
                work_periods = [{
                    "start": work_start,
                    "end": work_end, 
                    "type": "main",
                    "is_active": True
                }]
            
            # أولاً نتأكد من وجود جميع الأعمدة
            self.add_missing_columns()
            
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO doctor_schedule_settings 
                (doctor_id, work_days, work_hours_start, work_hours_end, 
                 work_periods, break_times, appointment_duration, buffer_time, max_patients_per_day)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                doctor_id,
                json.dumps(work_days),
                work_start,
                work_end,
                json.dumps(work_periods),
                json.dumps(breaks),
                appointment_duration,
                buffer_time,
                20  # القيمة الافتراضية لـ max_patients_per_day
            ))
            
            # إنشاء الجدول الدوري بعد إعداد الإعدادات
            success = self.setup_doctor_periodic_schedule(doctor_id, 30)
            
            self.conn.commit()
            logging.info(f"✅ تم إعداد جدول الطبيب {doctor_id} بنجاح")
            return success
            
        except Exception as e:
            logging.error(f"❌ خطأ في إعداد جدول الطبيب: {e}")
            self.conn.rollback()
            return False

    def setup_doctor_periodic_schedule(self, doctor_id: int, period_days: int = 30) -> bool:
        """إنشاء جدول دوري للطبيب لمدة محددة - الإصدار المتكامل والمصحح"""
        try:
            cursor = self.conn.cursor()
            
            # الحصول على إعدادات الطبيب
            settings = self.get_doctor_schedule_settings(doctor_id)
            if not settings:
                logging.warning(f"⚠️ لا توجد إعدادات للطبيب {doctor_id}، سيتم استخدام الإعدادات الافتراضية")
                # استخدام إعدادات افتراضية
                settings = {
                    'work_hours_start': '08:00',
                    'work_hours_end': '17:00',
                    'appointment_duration': 30,
                    'buffer_time': 5,
                    'work_days': ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday'],
                    'break_times': [{'start': '12:00', 'end': '13:00', 'reason': 'استراحة غداء'}],
                    'work_periods': [{'start': '08:00', 'end': '17:00', 'type': 'main', 'is_active': True}]
                }
            
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=period_days)
            
            slots_created = 0
            current_date = start_date
            
            while current_date <= end_date:
                if self.is_work_day(settings, current_date):
                    daily_slots = self.generate_daily_slots(settings, current_date)
                    
                    for slot in daily_slots:
                        cursor.execute('''
                            INSERT OR REPLACE INTO doctor_periodic_schedules 
                            (doctor_id, schedule_date, time_slot, slot_duration, status, slot_type, period_type)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            doctor_id,
                            current_date.strftime('%Y-%m-%d'),
                            slot['time'],
                            settings.get('appointment_duration', 30),
                            'available',
                            'regular',
                            slot.get('period_type', 'main')
                        ))
                        slots_created += 1
                
                current_date += timedelta(days=1)
            
            # تحديث إعدادات الجدولة الدورية
            next_renewal = end_date - timedelta(days=7)  # التجديد قبل 7 أيام من النهاية
            cursor.execute('''
                INSERT OR REPLACE INTO periodic_schedule_settings 
                (doctor_id, schedule_period_days, auto_renew_enabled, renewal_advance_days, 
                 last_renewal_date, next_renewal_date)
                VALUES (?, ?, 1, 7, DATE('now'), ?)
            ''', (doctor_id, period_days, next_renewal.strftime('%Y-%m-%d')))
            
            self.conn.commit()
            logging.info(f"✅ تم إنشاء جدول دوري للطبيب {doctor_id}: {slots_created} موعد خلال {period_days} يوم")
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في إنشاء الجدول الدوري: {e}")
            self.conn.rollback()
            return False

    def get_doctor_schedule_settings(self, doctor_id: int) -> Optional[Dict]:
        """الحصول على إعدادات جدول الطبيب - الإصدار المتكامل"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM doctor_schedule_settings 
                WHERE doctor_id = ?
            ''', (doctor_id,))
            
            row = cursor.fetchone()
            if row:
                settings = dict(row)
                # استخدام الدالة الآمنة لتحميل JSON
                settings['work_days'] = self.safe_json_loads(settings.get('work_days', '[]'))
                settings['work_periods'] = self.safe_json_loads(settings.get('work_periods', '[]'))
                settings['break_times'] = self.safe_json_loads(settings.get('break_times', '[]'))
                return settings
            return None
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب إعدادات الطبيب: {e}")
            return None

    def generate_daily_slots(self, settings: Dict, target_date: date) -> List[Dict]:
        """توليد المواعيد اليومية بناءً على فترات العمل المتعددة - الإصدار المتكامل"""
        try:
            slots = []
            
            # استخدام فترات العمل المتعددة إذا كانت متاحة
            work_periods = settings.get('work_periods', [])
            if work_periods:
                # استخدام فترات العمل المتعددة
                duration = settings.get('appointment_duration', 30)
                buffer_time = settings.get('buffer_time', 5)
                
                for period in work_periods:
                    if not period.get('is_active', True):
                        continue
                        
                    work_start = datetime.strptime(period['start'], '%H:%M').time()
                    work_end = datetime.strptime(period['end'], '%H:%M').time()
                    
                    current_time = work_start
                    while current_time < work_end:
                        slot_end = self.add_minutes_to_time(current_time, duration)
                        
                        # إضافة وقت缓冲 بين المواعيد
                        slot_end_with_buffer = self.add_minutes_to_time(slot_end, buffer_time)
                        
                        if slot_end_with_buffer > work_end:
                            break
                        
                        # التحقق من فترات الراحة
                        if not self.is_break_time(settings, current_time, slot_end):
                            slots.append({
                                'time': current_time.strftime('%H:%M'),
                                'end': slot_end.strftime('%H:%M'),
                                'duration': duration,
                                'period_type': period.get('type', 'main'),
                                'with_buffer': buffer_time
                            })
                        
                        current_time = self.add_minutes_to_time(current_time, duration + buffer_time)
            else:
                # استخدام الطريقة التقليدية
                work_start = datetime.strptime(settings['work_hours_start'], '%H:%M').time()
                work_end = datetime.strptime(settings['work_hours_end'], '%H:%M').time()
                duration = settings.get('appointment_duration', 30)
                buffer_time = settings.get('buffer_time', 5)
                
                current_time = work_start
                while current_time < work_end:
                    slot_end = self.add_minutes_to_time(current_time, duration)
                    
                    if slot_end > work_end:
                        break
                    
                    # التحقق من فترات الراحة
                    if not self.is_break_time(settings, current_time, slot_end):
                        slots.append({
                            'time': current_time.strftime('%H:%M'),
                            'end': slot_end.strftime('%H:%M'),
                            'duration': duration,
                            'period_type': 'main'
                        })
                    
                    current_time = self.add_minutes_to_time(current_time, duration + buffer_time)
            
            return slots
            
        except Exception as e:
            logging.error(f"❌ خطأ في توليد المواعيد اليومية: {e}")
            return []

    def is_break_time(self, settings: Dict, start_time: time, end_time: time) -> bool:
        """التحقق إذا كانت الفترة تقع في وقت راحة - الإصدار المحسن"""
        try:
            break_times = settings.get('break_times', [])
            
            # استخدام الدالة الآمنة لتحميل JSON
            break_times = self.safe_json_loads(break_times)
            
            if not isinstance(break_times, list):
                return False

            for break_period in break_times:
                if not isinstance(break_period, dict):
                    continue
                    
                break_start_str = break_period.get('start')
                break_end_str = break_period.get('end')
                
                if not break_start_str or not break_end_str:
                    continue

                try:
                    break_start = datetime.strptime(break_start_str, '%H:%M').time()
                    break_end = datetime.strptime(break_end_str, '%H:%M').time()
                    
                    if self.is_time_overlap(start_time, end_time, break_start, break_end):
                        return True
                except ValueError as e:
                    logging.warning(f"⚠️ تنسيق وقت راحة غير صالح: {break_start_str}-{break_end_str}")
                    continue

            return False
            
        except Exception as e:
            logging.error(f"❌ خطأ في التحقق من أوقات الراحة: {e}")
            return False

    # ⭐⭐ وظائف إدارة فترات العمل المتعددة ⭐⭐

    def add_work_period(self, doctor_id: int, period_data: Dict) -> bool:
        """إضافة فترة عمل جديدة للطبيب"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO doctor_work_periods 
                (doctor_id, period_type, start_time, end_time, days_of_week, is_active, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                doctor_id,
                period_data.get('type', 'custom'),
                period_data.get('start_time'),
                period_data.get('end_time'),
                json.dumps(period_data.get('days_of_week', [])),
                period_data.get('is_active', True),
                period_data.get('notes', '')
            ))
            
            self.conn.commit()
            logging.info(f"✅ تم إضافة فترة عمل للطبيب {doctor_id}")
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة فترة عمل: {e}")
            self.conn.rollback()
            return False

    def get_doctor_work_periods(self, doctor_id: int) -> List[Dict]:
        """الحصول على فترات العمل للطبيب"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM doctor_work_periods 
                WHERE doctor_id = ? AND is_active = 1
                ORDER BY start_time
            ''', (doctor_id,))
            
            periods = []
            for row in cursor.fetchall():
                period = dict(row)
                period['days_of_week'] = self.safe_json_loads(period['days_of_week'])
                periods.append(period)
                
            return periods
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب فترات العمل: {e}")
            return []

    def update_work_period(self, period_id: int, period_data: Dict) -> bool:
        """تحديث فترة عمل"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE doctor_work_periods 
                SET period_type = ?, start_time = ?, end_time = ?, 
                    days_of_week = ?, is_active = ?, notes = ?
                WHERE id = ?
            ''', (
                period_data.get('type'),
                period_data.get('start_time'),
                period_data.get('end_time'),
                json.dumps(period_data.get('days_of_week', [])),
                period_data.get('is_active', True),
                period_data.get('notes', ''),
                period_id
            ))
            
            self.conn.commit()
            logging.info(f"✅ تم تحديث فترة العمل {period_id}")
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث فترة العمل: {e}")
            self.conn.rollback()
            return False

    # ⭐⭐ وظائف الجدولة الدورية المتقدمة ⭐⭐

    def get_periodic_schedule(self, doctor_id: int, start_date: str = None, end_date: str = None) -> Dict:
        """الحصول على الجدول الدوري للطبيب لفترة محددة"""
        try:
            if not start_date:
                start_date = datetime.now().strftime('%Y-%m-%d')
            if not end_date:
                end_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT schedule_date, time_slot, status, appointment_id, slot_type, period_type
                FROM doctor_periodic_schedules 
                WHERE doctor_id = ? 
                AND schedule_date BETWEEN ? AND ?
                ORDER BY schedule_date, time_slot
            ''', (doctor_id, start_date, end_date))
            
            schedule_data = {}
            for row in cursor.fetchall():
                date_str = row['schedule_date']
                time_str = row['time_slot']
                
                if date_str not in schedule_data:
                    schedule_data[date_str] = {
                        'date': date_str,
                        'slots': [],
                        'available_count': 0,
                        'booked_count': 0,
                        'total_count': 0
                    }
                
                slot_info = {
                    'time': time_str,
                    'status': row['status'],
                    'appointment_id': row['appointment_id'],
                    'type': row['slot_type'],
                    'period_type': row.get('period_type', 'main')
                }
                
                schedule_data[date_str]['slots'].append(slot_info)
                schedule_data[date_str]['total_count'] += 1
                
                if row['status'] == 'available':
                    schedule_data[date_str]['available_count'] += 1
                elif row['status'] == 'booked':
                    schedule_data[date_str]['booked_count'] += 1
            
            return schedule_data
            
        except Exception as e:
            logging.error(f"❌ خطأ في الحصول على الجدول الدوري: {e}")
            return {}

    def book_appointment_slot(self, doctor_id: int, appointment_date: str, 
                            appointment_time: str, appointment_id: int) -> bool:
        """حجز موعد في الجدول الدوري"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
                UPDATE doctor_periodic_schedules 
                SET status = 'booked', appointment_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE doctor_id = ? 
                AND schedule_date = ? 
                AND time_slot = ?
                AND status = 'available'
            ''', (appointment_id, doctor_id, appointment_date, appointment_time))
            
            if cursor.rowcount > 0:
                self.conn.commit()
                logging.info(f"✅ تم حجز الموعد: {appointment_date} {appointment_time}")
                return True
            else:
                logging.warning(f"⚠️ الموعد غير متاح: {appointment_date} {appointment_time}")
                return False
                
        except Exception as e:
            logging.error(f"❌ خطأ في حجز الموعد: {e}")
            self.conn.rollback()
            return False

    def check_and_renew_schedules(self):
        """التحقق من الحاجة لتجديد الجداول والتجديد التلقائي"""
        try:
            cursor = self.conn.cursor()
            
            # الحصول على الأطباء الذين يحتاجون تجديد
            cursor.execute('''
                SELECT ps.doctor_id, d.name, ps.next_renewal_date
                FROM periodic_schedule_settings ps
                JOIN doctors d ON ps.doctor_id = d.id
                WHERE ps.auto_renew_enabled = 1 
                AND ps.next_renewal_date <= DATE('now')
            ''')
            
            doctors_to_renew = cursor.fetchall()
            renewed_count = 0
            
            for doctor in doctors_to_renew:
                doctor_id = doctor['doctor_id']
                doctor_name = doctor['name']
                
                if self.renew_doctor_schedule(doctor_id):
                    renewed_count += 1
                    logging.info(f"✅ تم تجديد جدول الطبيب: {doctor_name}")
                else:
                    logging.error(f"❌ فشل في تجديد جدول الطبيب: {doctor_name}")
            
            logging.info(f"📊 تم تجديد {renewed_count} جدول من أصل {len(doctors_to_renew)}")
            return renewed_count
            
        except Exception as e:
            logging.error(f"❌ خطأ في تجديد الجداول: {e}")
            return 0

    def renew_doctor_schedule(self, doctor_id: int) -> bool:
        """تجديد الجدول الدوري للطبيب"""
        try:
            cursor = self.conn.cursor()
            
            # الحصول على إعدادات الطبيب
            cursor.execute('''
                SELECT schedule_period_days, renewal_advance_days 
                FROM periodic_schedule_settings 
                WHERE doctor_id = ?
            ''', (doctor_id,))
            
            settings = cursor.fetchone()
            if not settings:
                return False
            
            period_days = settings['schedule_period_days']
            advance_days = settings['renewal_advance_days']
            
            # الحصول على آخر تاريخ في الجدول الحالي
            cursor.execute('''
                SELECT MAX(schedule_date) as last_date 
                FROM doctor_periodic_schedules 
                WHERE doctor_id = ?
            ''', (doctor_id,))
            
            result = cursor.fetchone()
            if not result or not result['last_date']:
                return self.setup_doctor_periodic_schedule(doctor_id, period_days)
            
            last_date = datetime.strptime(result['last_date'], '%Y-%m-%d').date()
            today = datetime.now().date()
            
            # إذا كان التاريخ الأخير ضمن أيام التنبيه، نقوم بالتجديد
            if (last_date - today).days <= advance_days:
                # إضافة فترة جديدة بعد آخر تاريخ
                new_start_date = last_date + timedelta(days=1)
                new_end_date = new_start_date + timedelta(days=period_days - 1)
                
                # إنشاء الجدول للفترة الجديدة
                settings_data = self.get_doctor_schedule_settings(doctor_id)
                current_date = new_start_date
                
                while current_date <= new_end_date:
                    if self.is_work_day(settings_data, current_date):
                        daily_slots = self.generate_daily_slots(settings_data, current_date)
                        
                        for slot in daily_slots:
                            cursor.execute('''
                                INSERT OR REPLACE INTO doctor_periodic_schedules 
                                (doctor_id, schedule_date, time_slot, slot_duration, status, slot_type, period_type)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                doctor_id,
                                current_date.strftime('%Y-%m-%d'),
                                slot['time'],
                                settings_data.get('appointment_duration', 30),
                                'available',
                                'regular',
                                slot.get('period_type', 'main')
                            ))
                    
                    current_date += timedelta(days=1)
                
                # تحديث تاريخ التجديد القادم
                next_renewal = new_end_date - timedelta(days=advance_days)
                cursor.execute('''
                    UPDATE periodic_schedule_settings 
                    SET last_renewal_date = DATE('now'), next_renewal_date = ?
                    WHERE doctor_id = ?
                ''', (next_renewal.strftime('%Y-%m-%d'), doctor_id))
                
                self.conn.commit()
                logging.info(f"✅ تم تجديد جدول الطبيب {doctor_id} حتى {new_end_date}")
                return True
            
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في تجديد جدول الطبيب: {e}")
            self.conn.rollback()
            return False

    # ⭐⭐ وظائف التحقق والتحليل ⭐⭐

    def verify_schedule_creation(self, doctor_id: int) -> Dict:
        """التحقق من إنشاء الجدول الدوري للطبيب"""
        try:
            cursor = self.conn.cursor()
            
            # التحقق من عدد المواعيد المنشأة
            cursor.execute('''
                SELECT COUNT(*) as slot_count 
                FROM doctor_periodic_schedules 
                WHERE doctor_id = ? AND schedule_date >= DATE('now')
            ''', (doctor_id,))
            
            result = cursor.fetchone()
            slot_count = result['slot_count'] if result else 0
            
            # التحقق من عدد الأيام
            cursor.execute('''
                SELECT COUNT(DISTINCT schedule_date) as date_count 
                FROM doctor_periodic_schedules 
                WHERE doctor_id = ? AND schedule_date >= DATE('now')
            ''', (doctor_id,))
            
            result = cursor.fetchone()
            date_count = result['date_count'] if result else 0
            
            # التحقق من إعدادات الجدولة الدورية
            cursor.execute('SELECT * FROM periodic_schedule_settings WHERE doctor_id = ?', (doctor_id,))
            schedule_settings = cursor.fetchone()
            
            return {
                'success': slot_count > 0,
                'slot_count': slot_count,
                'date_count': date_count,
                'has_schedule_settings': schedule_settings is not None,
                'message': f'تم إنشاء {slot_count} موعد في {date_count} يوم' if slot_count > 0 else 'لم يتم إنشاء أي مواعيد',
                'next_renewal': schedule_settings['next_renewal_date'] if schedule_settings else None
            }
            
        except Exception as e:
            logging.error(f"❌ خطأ في التحقق من إنشاء الجدول: {e}")
            return {'success': False, 'message': f'خطأ في التحقق: {e}'}

    def get_doctor_schedule_summary(self, doctor_id: int, start_date: str = None, end_date: str = None) -> Dict:
        """الحصول على ملخص جدول الطبيب"""
        try:
            if not start_date:
                start_date = datetime.now().strftime('%Y-%m-%d')
            if not end_date:
                end_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            
            schedule = self.get_periodic_schedule(doctor_id, start_date, end_date)
            
            total_slots = 0
            available_slots = 0
            booked_slots = 0
            
            for date_data in schedule.values():
                total_slots += date_data['total_count']
                available_slots += date_data['available_count']
                booked_slots += date_data['booked_count']
            
            return {
                'total_slots': total_slots,
                'available_slots': available_slots,
                'booked_slots': booked_slots,
                'utilization_rate': round((booked_slots / total_slots * 100) if total_slots > 0 else 0, 2),
                'period': f'{start_date} إلى {end_date}'
            }
            
        except Exception as e:
            logging.error(f"❌ خطأ في الحصول على ملخص الجدول: {e}")
            return {}

    # ⭐⭐ الوظائف المساعدة ⭐⭐

    def is_work_day(self, settings: Dict, target_date: date) -> bool:
        """التحقق إذا كان التاريخ يوم عمل"""
        try:
            day_names = {
                0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday",
                4: "friday", 5: "saturday", 6: "sunday"
            }
            
            day_of_week = day_names[target_date.weekday()]
            work_days = settings.get('work_days', [])
            
            return day_of_week in work_days
            
        except Exception as e:
            logging.error(f"❌ خطأ في التحقق من يوم العمل: {e}")
            return False

    def add_minutes_to_time(self, time_obj: time, minutes: int) -> time:
        """إضافة دقائق إلى وقت"""
        full_datetime = datetime.combine(datetime.today(), time_obj)
        new_datetime = full_datetime + timedelta(minutes=minutes)
        return new_datetime.time()

    def is_time_overlap(self, start1: time, end1: time, start2: time, end2: time) -> bool:
        """التحقق من تداخل فترتين زمنيتين"""
        return not (end1 <= start2 or start1 >= end2)

    # ⭐⭐ وظائف التوافق مع النظام القديم ⭐⭐

    def get_available_slots(self, doctor_id: int, target_date: str) -> List[str]:
        """الحصول على الأوقات المتاحة (للتوافق مع النظام القديم)"""
        try:
            schedule = self.get_periodic_schedule(doctor_id, target_date, target_date)
            
            if target_date in schedule:
                available_slots = []
                for slot in schedule[target_date]['slots']:
                    if slot['status'] == 'available':
                        available_slots.append(slot['time'])
                
                return available_slots
            
            return []
            
        except Exception as e:
            logging.error(f"❌ خطأ في الحصول على الأوقات المتاحة: {e}")
            return []

    def get_work_periods_for_day(self, settings: Dict, target_date: date) -> List[Dict]:
        """الحصول على فترات العمل ليوم محدد - تدعم فترات متعددة"""
        try:
            work_periods = settings.get('work_periods', [])
            
            # إذا لم توجد فترات محددة، نستخدم الفترة التقليدية
            if not work_periods:
                work_start = settings.get('work_hours_start', '08:00')
                work_end = settings.get('work_hours_end', '17:00')
                return [{'start': work_start, 'end': work_end, 'type': 'main', 'is_active': True}]
            
            # التحقق من أيام العمل
            work_days = settings.get('work_days', [])
            
            day_names = {
                0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday",
                4: "friday", 5: "saturday", 6: "sunday"
            }
            
            day_of_week = day_names[target_date.weekday()]
            
            if day_of_week not in work_days:
                return []
            
            return work_periods
            
        except Exception as e:
            logging.error(f"❌ خطأ في الحصول على فترات العمل: {e}")
            return []

# اختبار الملف
if __name__ == "__main__":
    print("✅ تم تحميل database_scheduling.py بنجاح - الإصدار النهائي المتكامل والمصحح")