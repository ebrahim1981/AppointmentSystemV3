# -*- coding: utf-8 -*-
"""
أدوات تاريخ ووقت محسنة لنظام الجدولة الذكية
تدعم اللغة العربية والتقويم الهجري
"""

import logging
from datetime import datetime, timedelta, time, date
import json

class EnhancedDateUtils:
    """أدوات تاريخ ووقت محسنة للجدولة الذكية"""
    
    def __init__(self):
        self.hijri_months = {
            1: "محرم", 2: "صفر", 3: "ربيع الأول", 4: "ربيع الآخر",
            5: "جمادى الأولى", 6: "جمادى الآخرة", 7: "رجب", 
            8: "شعبان", 9: "رمضان", 10: "شوال",
            11: "ذو القعدة", 12: "ذو الحجة"
        }
        
        self.arabic_days = {
            "sunday": "الأحد",
            "monday": "الإثنين", 
            "tuesday": "الثلاثاء",
            "wednesday": "الأربعاء",
            "thursday": "الخميس",
            "friday": "الجمعة",
            "saturday": "السبت"
        }
        
        self.arabic_months = {
            1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل",
            5: "مايو", 6: "يونيو", 7: "يوليو", 8: "أغسطس",
            9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
        }
    
    def get_arabic_day_name(self, day_index):
        """الحصول على اسم اليوم بالعربية من رقم اليوم"""
        days = {
            0: "الإثنين",
            1: "الثلاثاء",
            2: "الأربعاء", 
            3: "الخميس",
            4: "الجمعة",
            5: "السبت",
            6: "الأحد"
        }
        return days.get(day_index, "غير معروف")
    
    def get_arabic_day_name_from_english(self, english_day_name):
        """تحويل اسم اليوم من الإنجليزية إلى العربية"""
        return self.arabic_days.get(english_day_name.lower(), english_day_name)
    
    def format_arabic_date(self, date_obj, include_day_name=True):
        """تنسيق التاريخ باللغة العربية"""
        try:
            day_name = self.get_arabic_day_name(date_obj.weekday()) if include_day_name else ""
            month_name = self.arabic_months.get(date_obj.month, "")
            
            if include_day_name:
                return f"{day_name}، {date_obj.day} {month_name} {date_obj.year}"
            else:
                return f"{date_obj.day} {month_name} {date_obj.year}"
                
        except Exception as e:
            logging.error(f"خطأ في تنسيق التاريخ العربي: {e}")
            return str(date_obj)
    
    def parse_flexible_date(self, date_input):
        """
        تحليل التاريخ من مدخلات مرنة
        يدعم: YYYY-MM-DD, DD/MM/YYYY, اليوم، غداً، بعد غد، etc.
        """
        try:
            date_input = str(date_input).strip().lower()
            
            # اليوم
            if date_input in ['today', 'اليوم', 'today']:
                return datetime.now().date()
            
            # غداً
            if date_input in ['tomorrow', 'غداً', 'غدا', 'tomorrow']:
                return (datetime.now() + timedelta(days=1)).date()
            
            # بعد غد
            if date_input in ['after tomorrow', 'بعد غد', 'after_tomorrow']:
                return (datetime.now() + timedelta(days=2)).date()
            
            # بعد أسبوع
            if date_input in ['next week', 'الأسبوع القادم', 'next_week']:
                return (datetime.now() + timedelta(days=7)).date()
            
            # تنسيق YYYY-MM-DD
            if len(date_input) == 10 and date_input[4] == '-' and date_input[7] == '-':
                return datetime.strptime(date_input, '%Y-%m-%d').date()
            
            # تنسيق DD/MM/YYYY
            if len(date_input) == 10 and date_input[2] == '/' and date_input[5] == '/':
                return datetime.strptime(date_input, '%d/%m/%Y').date()
            
            # إذا لم يتطابق مع أي تنسيق
            raise ValueError(f"تنسيق التاريخ غير معروف: {date_input}")
            
        except Exception as e:
            logging.error(f"خطأ في تحليل التاريخ: {e}")
            raise
    
    def generate_date_range(self, start_date, end_date):
        """إنشاء نطاق من التواريخ"""
        try:
            if isinstance(start_date, str):
                start_date = self.parse_flexible_date(start_date)
            if isinstance(end_date, str):
                end_date = self.parse_flexible_date(end_date)
            
            date_list = []
            current_date = start_date
            
            while current_date <= end_date:
                date_list.append(current_date)
                current_date += timedelta(days=1)
            
            return date_list
            
        except Exception as e:
            logging.error(f"خطأ في إنشاء نطاق التواريخ: {e}")
            return []
    
    def get_week_dates(self, target_date=None, week_start='sunday'):
        """الحصول على جميع تواريخ الأسبوع"""
        try:
            if target_date is None:
                target_date = datetime.now().date()
            elif isinstance(target_date, str):
                target_date = self.parse_flexible_date(target_date)
            
            # حساب بداية الأسبوع
            if week_start == 'sunday':
                start_offset = target_date.weekday() + 1 if target_date.weekday() != 6 else 0
            else:  # monday
                start_offset = target_date.weekday()
            
            week_start_date = target_date - timedelta(days=start_offset)
            
            # إنشاء قائمة بأيام الأسبوع
            week_dates = []
            for i in range(7):
                week_date = week_start_date + timedelta(days=i)
                week_dates.append({
                    'date': week_date,
                    'day_name': self.get_arabic_day_name(week_date.weekday()),
                    'is_today': week_date == datetime.now().date()
                })
            
            return week_dates
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على تواريخ الأسبوع: {e}")
            return []
    
    def calculate_age(self, birth_date):
        """حساب العمر من تاريخ الميلاد"""
        try:
            if isinstance(birth_date, str):
                birth_date = self.parse_flexible_date(birth_date)
            
            today = datetime.now().date()
            age = today.year - birth_date.year
            
            # تعديل إذا لم يكن قد مر عيد الميلاد بعد هذا السنة
            if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                age -= 1
            
            return age
            
        except Exception as e:
            logging.error(f"خطأ في حساب العمر: {e}")
            return None
    
    def is_weekend(self, date_obj):
        """التحقق إذا كان التاريخ عطلة نهاية أسبوع (الجمعة والسبت)"""
        try:
            if isinstance(date_obj, str):
                date_obj = self.parse_flexible_date(date_obj)
            
            # الجمعة = 4، السبت = 5 في Python (الإثنين = 0)
            return date_obj.weekday() in [4, 5]
            
        except Exception as e:
            logging.error(f"خطأ في التحقق من العطلة: {e}")
            return False
    
    def get_saudi_holidays(self, year=None):
        """الحصول على العطلات الرسمية في السعودية"""
        if year is None:
            year = datetime.now().year
        
        # العطلات الثابتة (تاريخ ميلادي)
        fixed_holidays = [
            f"{year}-09-23",  # اليوم الوطني
        ]
        
        # العطلات الإسلامية (تقريبية - تحتاج مكتبة دقيقة للحساب)
        # هذه مجرد أمثلة تقريبية
        eid_al_fitr = f"{year}-04-21"  # تقريبي
        eid_al_adha = f"{year}-06-28"  # تقريبي
        
        islamic_holidays = [eid_al_fitr, eid_al_adha]
        
        return fixed_holidays + islamic_holidays
    
    def is_saudi_holiday(self, date_obj):
        """التحقق إذا كان التاريخ عطلة رسمية في السعودية"""
        try:
            if isinstance(date_obj, str):
                date_obj = self.parse_flexible_date(date_obj)
            
            date_str = date_obj.strftime('%Y-%m-%d')
            holidays = self.get_saudi_holidays(date_obj.year)
            
            return date_str in holidays
            
        except Exception as e:
            logging.error(f"خطأ في التحقق من العطلة الرسمية: {e}")
            return False
    
    def add_minutes_to_time(self, time_obj, minutes):
        """إضافة دقائق إلى وقت"""
        try:
            if isinstance(time_obj, str):
                time_obj = datetime.strptime(time_obj, '%H:%M').time()
            
            full_datetime = datetime.combine(datetime.today(), time_obj)
            new_datetime = full_datetime + timedelta(minutes=minutes)
            return new_datetime.time()
            
        except Exception as e:
            logging.error(f"خطأ في إضافة الدقائق: {e}")
            return time_obj
    
    def generate_time_slots(self, start_time, end_time, slot_duration, interval=15):
        """توليد فترات زمنية بين وقتين"""
        try:
            if isinstance(start_time, str):
                start_time = datetime.strptime(start_time, '%H:%M').time()
            if isinstance(end_time, str):
                end_time = datetime.strptime(end_time, '%H:%M').time()
            
            slots = []
            current_time = start_time
            
            while current_time < end_time:
                slot_end = self.add_minutes_to_time(current_time, slot_duration)
                
                if slot_end > end_time:
                    break
                
                slots.append({
                    'start_time': current_time.strftime('%H:%M'),
                    'end_time': slot_end.strftime('%H:%M'),
                    'display': f"{current_time.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}"
                })
                
                current_time = self.add_minutes_to_time(current_time, interval)
            
            return slots
            
        except Exception as e:
            logging.error(f"خطأ في توليد الفترات الزمنية: {e}")
            return []
    
    def calculate_work_hours(self, start_time, end_time, breaks=None):
        """حساب ساعات العمل الفعلية مع استراحات"""
        try:
            if isinstance(start_time, str):
                start_time = datetime.strptime(start_time, '%H:%M').time()
            if isinstance(end_time, str):
                end_time = datetime.strptime(end_time, '%H:%M').time()
            
            # حساب الفرق الأساسي
            start_dt = datetime.combine(datetime.today(), start_time)
            end_dt = datetime.combine(datetime.today(), end_time)
            
            total_minutes = (end_dt - start_dt).total_seconds() / 60
            
            # طرح وقت الاستراحات
            if breaks:
                for break_time in breaks:
                    break_start = datetime.strptime(break_time['start'], '%H:%M').time()
                    break_end = datetime.strptime(break_time['end'], '%H:%M').time()
                    
                    break_start_dt = datetime.combine(datetime.today(), break_start)
                    break_end_dt = datetime.combine(datetime.today(), break_end)
                    
                    break_minutes = (break_end_dt - break_start_dt).total_seconds() / 60
                    total_minutes -= break_minutes
            
            hours = int(total_minutes // 60)
            minutes = int(total_minutes % 60)
            
            return f"{hours} ساعة و {minutes} دقيقة"
            
        except Exception as e:
            logging.error(f"خطأ في حساب ساعات العمل: {e}")
            return "غير محسوب"
    
    def get_next_available_date(self, work_days, start_date=None, max_days=365):
        """الحصول على next available date based on work days"""
        try:
            if start_date is None:
                start_date = datetime.now().date()
            elif isinstance(start_date, str):
                start_date = self.parse_flexible_date(start_date)
            
            for days_ahead in range(max_days):
                target_date = start_date + timedelta(days=days_ahead)
                day_name = self.get_english_day_name(target_date.weekday())
                
                if day_name in work_days and not self.is_saudi_holiday(target_date):
                    return target_date
            
            return None
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على next available date: {e}")
            return None
    
    def get_english_day_name(self, day_index):
        """الحصول على اسم اليوم بالإنجليزية"""
        days = {
            0: "monday",
            1: "tuesday",
            2: "wednesday",
            3: "thursday", 
            4: "friday",
            5: "saturday",
            6: "sunday"
        }
        return days.get(day_index, "unknown")

# استخدام مباشر للدوال
def create_date_utils():
    """إنشاء كائن أدوات التاريخ"""
    return EnhancedDateUtils()

# أمثلة للاستخدام
if __name__ == "__main__":
    utils = EnhancedDateUtils()
    
    print("أدوات التاريخ والوقت المحسنة")
    print("=" * 50)
    
    # مثال: تنسيق التاريخ
    today = datetime.now().date()
    print(f"اليوم: {utils.format_arabic_date(today)}")
    
    # مثال: تحليل التاريخ
    tomorrow = utils.parse_flexible_date("غداً")
    print(f"غداً: {utils.format_arabic_date(tomorrow)}")
    
    # مثال: توليد فترات زمنية
    slots = utils.generate_time_slots("08:00", "12:00", 30)
    print(f"الفترات المتاحة: {len(slots)} فترة")
    
    # مثال: العطلات
    print(f"هل اليوم عطلة؟ {utils.is_saudi_holiday(today)}")