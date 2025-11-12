# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta

class SchedulingMixin:
    """ميكسین إدارة الجدولة الذكية والأوقات المتاحة"""
    
    def create_scheduling_tables(self):
        """إنشاء جداول الجدولة الذكية"""
        try:
            cursor = self.conn.cursor()
            
            # جدول إعدادات الأطباء
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS doctor_schedule_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doctor_id INTEGER NOT NULL,
                    work_days TEXT NOT NULL, -- JSON: ["saturday", "sunday", ...]
                    work_hours_start TIME NOT NULL,
                    work_hours_end TIME NOT NULL,
                    appointment_duration INTEGER DEFAULT 30, -- بالدقائق
                    break_times TEXT, -- JSON: [{"start": "13:00", "end": "14:00", "reason": "غداء"}]
                    max_patients_per_day INTEGER DEFAULT 20,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (doctor_id) REFERENCES doctors (id)
                )
            ''')
            
            # جدول أنواع الخدمات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS service_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    default_duration INTEGER NOT NULL, -- بالدقائق
                    required_equipment TEXT,
                    color_code TEXT DEFAULT '#3498db',
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول إشغال الغرف
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS room_allocations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_id INTEGER NOT NULL,
                    room_name TEXT NOT NULL,
                    doctor_id INTEGER,
                    appointment_id INTEGER,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME NOT NULL,
                    status TEXT DEFAULT 'مشغول', -- مشغول/متاح/صيانة
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول الاستثناءات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schedule_exceptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doctor_id INTEGER NOT NULL,
                    exception_date DATE NOT NULL,
                    exception_type TEXT NOT NULL, -- إجازة/مرض/اجتماع/تدريب
                    start_time TIME,
                    end_time TIME,
                    reason TEXT,
                    is_all_day BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (doctor_id) REFERENCES doctors (id)
                )
            ''')
            
            self.conn.commit()
            logging.info("✅ تم إنشاء جداول الجدولة الذكية بنجاح")
            
        except Exception as e:
            logging.error(f"❌ خطأ في إنشاء جداول الجدولة: {e}")
            self.conn.rollback()

    def get_available_slots(self, doctor_id, date, service_type=None, duration=None):
        """الحصول على الأوقات المتاحة للطبيب - الخوارزمية الرئيسية"""
        try:
            # 1. الحصول على إعدادات الطبيب
            doctor_settings = self.get_doctor_schedule_settings(doctor_id)
            if not doctor_settings:
                return []
            
            # 2. الحصول على المواعيد الحالية
            existing_appointments = self.get_doctor_appointments(doctor_id, date)
            
            # 3. الحصول على الاستثناءات
            exceptions = self.get_schedule_exceptions(doctor_id, date)
            
            # 4. حساب مدة الموعد
            appointment_duration = duration or doctor_settings.get('appointment_duration', 30)
            
            # 5. توليد الأوقات المتاحة
            available_slots = self.generate_available_slots(
                doctor_settings, 
                existing_appointments, 
                exceptions, 
                appointment_duration,
                date
            )
            
            return available_slots
            
        except Exception as e:
            logging.error(f"❌ خطأ في الحصول على الأوقات المتاحة: {e}")
            return []

    def get_doctor_schedule_settings(self, doctor_id):
        """الحصول على إعدادات جدول الطبيب"""
        try:
            query = "SELECT * FROM doctor_schedule_settings WHERE doctor_id = ?"
            cursor = self.conn.cursor()
            cursor.execute(query, (doctor_id,))
            row = cursor.fetchone()
            
            if row:
                settings = dict(row)
                # تحويل JSON strings إلى Python objects
                if settings.get('work_days'):
                    import json
                    settings['work_days'] = json.loads(settings['work_days'])
                if settings.get('break_times'):
                    import json
                    settings['break_times'] = json.loads(settings['break_times'])
                return settings
            return None
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب إعدادات الطبيب: {e}")
            return None

    def get_doctor_appointments(self, doctor_id, date):
        """الحصول على مواعيد الطبيب في تاريخ معين"""
        try:
            query = '''
                SELECT appointment_time, type, status 
                FROM appointments 
                WHERE doctor_id = ? AND appointment_date = ? AND status NOT IN ('ملغي', 'منتهي')
                ORDER BY appointment_time
            '''
            cursor = self.conn.cursor()
            cursor.execute(query, (doctor_id, date))
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب مواعيد الطبيب: {e}")
            return []

    def get_schedule_exceptions(self, doctor_id, date):
        """الحصول على استثناءات الجدول"""
        try:
            query = '''
                SELECT * FROM schedule_exceptions 
                WHERE doctor_id = ? AND exception_date = ?
            '''
            cursor = self.conn.cursor()
            cursor.execute(query, (doctor_id, date))
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب الاستثناءات: {e}")
            return []

    def generate_available_slots(self, settings, appointments, exceptions, duration, date):
        """توليد الأوقات المتاحة - قلب الخوارزمية"""
        try:
            available_slots = []
            
            # أوقات العمل
            start_time = datetime.strptime(settings['work_hours_start'], '%H:%M').time()
            end_time = datetime.strptime(settings['work_hours_end'], '%H:%M').time()
            
            # المواعيد الحالية كمشغولة
            booked_slots = []
            for appointment in appointments:
                appointment_time = datetime.strptime(appointment['appointment_time'], '%H:%M').time()
                booked_slots.append(appointment_time)
            
            # الاستثناءات كمشغولة
            for exception in exceptions:
                if exception.get('is_all_day'):
                    # إذا كان الاستثناء طوال اليوم، لا توجد أوقات متاحة
                    return []
                elif exception.get('start_time') and exception.get('end_time'):
                    start_exception = datetime.strptime(exception['start_time'], '%H:%M').time()
                    end_exception = datetime.strptime(exception['end_time'], '%H:%M').time()
                    # إضافة الاستثناء كفترة مشغولة
                    booked_slots.extend(self.get_time_range_slots(start_exception, end_exception, duration))
            
            # فترات الراحة كمشغولة
            if settings.get('break_times'):
                for break_time in settings['break_times']:
                    break_start = datetime.strptime(break_time['start'], '%H:%M').time()
                    break_end = datetime.strptime(break_time['end'], '%H:%M').time()
                    booked_slots.extend(self.get_time_range_slots(break_start, break_end, duration))
            
            # توليد جميع الأوقات الممكنة
            current_time = start_time
            while current_time < end_time:
                slot_end = self.add_minutes_to_time(current_time, duration)
                
                # التحقق إذا كان الوقت ضمن نهاية الدوام
                if slot_end > end_time:
                    break
                
                # التحقق إذا كان الوقت متاح (غير مشغول)
                if current_time not in booked_slots:
                    available_slots.append({
                        'time': current_time.strftime('%H:%M'),
                        'end_time': slot_end.strftime('%H:%M'),
                        'duration': duration,
                        'status': 'available',
                        'display': f"{current_time.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}"
                    })
                
                # الانتقال للوقت التالي (كل 15 دقيقة)
                current_time = self.add_minutes_to_time(current_time, 15)
            
            return available_slots
            
        except Exception as e:
            logging.error(f"❌ خطأ في توليد الأوقات المتاحة: {e}")
            return []

    def get_time_range_slots(self, start_time, end_time, duration):
        """الحصول على جميع الأوقات في نطاق معين"""
        slots = []
        current = start_time
        while current < end_time:
            slots.append(current)
            current = self.add_minutes_to_time(current, duration)
        return slots

    def add_minutes_to_time(self, time_obj, minutes):
        """إضافة دقائق إلى وقت"""
        time_delta = timedelta(minutes=minutes)
        full_datetime = datetime.combine(datetime.today(), time_obj)
        new_datetime = full_datetime + time_delta
        return new_datetime.time()

    def check_schedule_conflict(self, doctor_id, date, start_time, duration=30):
        """التحقق من تضارب المواعيد"""
        try:
            # الحصول على المواعيد الحالية
            appointments = self.get_doctor_appointments(doctor_id, date)
            
            # وقت البدء والانتهاء للموعد الجديد
            new_start = datetime.strptime(start_time, '%H:%M').time()
            new_end = self.add_minutes_to_time(new_start, duration)
            
            for appointment in appointments:
                existing_start = datetime.strptime(appointment['appointment_time'], '%H:%M').time()
                existing_end = self.add_minutes_to_time(existing_start, duration)
                
                # التحقق من التداخل
                if (new_start < existing_end and new_end > existing_start):
                    return {
                        'has_conflict': True,
                        'conflicting_appointment': appointment,
                        'message': f"التوقيت يتعارض مع موعد موجود: {existing_start.strftime('%H:%M')}"
                    }
            
            return {'has_conflict': False, 'message': 'لا يوجد تعارض'}
            
        except Exception as e:
            logging.error(f"❌ خطأ في التحقق من التعارض: {e}")
            return {'has_conflict': True, 'message': f'خطأ في التحقق: {e}'}

    def initialize_default_schedules(self):
        """تهيئة الجداول الافتراضية"""
        try:
            # إضافة أنواع الخدمات الافتراضية
            default_services = [
                ('كشف عام', 30, '#3498db'),
                ('كشف أطفال', 45, '#e74c3c'),
                ('كشف نساء', 60, '#9b59b6'),
                ('طوارئ', 15, '#e67e22'),
                ('متابعة', 20, '#2ecc71'),
                ('تحاليل', 30, '#f1c40f'),
                ('أشعة', 45, '#1abc9c')
            ]
            
            cursor = self.conn.cursor()
            for service in default_services:
                cursor.execute('''
                    INSERT OR IGNORE INTO service_types (name, default_duration, color_code)
                    VALUES (?, ?, ?)
                ''', service)
            
            self.conn.commit()
            logging.info("✅ تم تهيئة أنواع الخدمات الافتراضية")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تهيئة الجداول الافتراضية: {e}")
            self.conn.rollback()

# اختبار الملف
if __name__ == "__main__":
    print("✅ تم تحميل database_scheduling.py بنجاح")