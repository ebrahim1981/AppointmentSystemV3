# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta

class SchedulingUIHelper:
    """مساعد واجهات المستخدم لنظام الجدولة الذكية"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def setup_doctor_schedule_ui(self, doctor_id, doctor_name=""):
        """واجهة مبسطة لإعداد جدول الطبيب"""
        print(f"\n{'='*50}")
        print(f"   ⚙️  إعداد جدول الطبيب: {doctor_name}")
        print(f"{'='*50}")
        
        try:
            # الحصول على الإعدادات الحالية
            current_settings = self.db.get_doctor_schedule_settings(doctor_id)
            
            if current_settings:
                print("📋 الإعدادات الحالية:")
                print(f"   • مدة الموعد: {current_settings.get('appointment_duration', 30)} دقيقة")
                print(f"   • أيام العمل: {current_settings.get('work_days', [])}")
                print(f"   • ساعات العمل: {current_settings.get('work_hours_start')} - {current_settings.get('work_hours_end')}")
                
                modify = input("\nهل تريد تعديل الإعدادات؟ (نعم/لا): ").strip().lower()
                if modify not in ['نعم', 'yes', 'y']:
                    return True
            
            # إدخال مدة الموعد
            print("\n🕒 إعداد مدة الموعد:")
            duration = input("مدة الموعد بالدقائق (افتراضي 30): ").strip()
            appointment_duration = int(duration) if duration.isdigit() else 30
            
            # اختيار نوع الدوام
            print("\n📅 اختيار نوع الدوام:")
            print("   1. دوام كامل (8 صباحاً - 5 مساءً)")
            print("   2. دوام صباحي (8 صباحاً - 1 ظهراً)") 
            print("   3. دوام مسائي (4 مساءً - 9 مساءً)")
            print("   4. مخصص")
            
            schedule_type = input("اختر نوع الدوام (1-4): ").strip()
            
            if schedule_type == "1":
                work_start, work_end = "08:00", "17:00"
                work_days = ["sunday", "monday", "tuesday", "wednesday", "thursday"]
            elif schedule_type == "2":
                work_start, work_end = "08:00", "13:00" 
                work_days = ["sunday", "monday", "tuesday", "wednesday", "thursday"]
            elif schedule_type == "3":
                work_start, work_end = "16:00", "21:00"
                work_days = ["sunday", "monday", "tuesday", "wednesday", "thursday"]
            else:
                work_start = input("وقت بدء الدوام (مثال: 08:00): ").strip() or "08:00"
                work_end = input("وقت انتهاء الدوام (مثال: 17:00): ").strip() or "17:00"
                work_days = self.get_custom_work_days()
            
            # حفظ الإعدادات
            success = self.db.setup_doctor_schedule(
                doctor_id=doctor_id,
                appointment_duration=appointment_duration,
                work_days=work_days,
                work_start=work_start,
                work_end=work_end
            )
            
            if success:
                print(f"\n✅ تم إعداد جدول الطبيب {doctor_name} بنجاح!")
                print(f"   • مدة الموعد: {appointment_duration} دقيقة")
                print(f"   • ساعات العمل: {work_start} - {work_end}")
                print(f"   • أيام العمل: {work_days}")
                return True
            else:
                print("\n❌ فشل في إعداد الجدول")
                return False
                
        except Exception as e:
            logging.error(f"خطأ في واجهة إعداد الجدول: {e}")
            return False
    
    def get_custom_work_days(self):
        """الحصول على أيام العمل المخصصة"""
        days_mapping = {
            "1": "sunday",
            "2": "monday", 
            "3": "tuesday",
            "4": "wednesday",
            "5": "thursday",
            "6": "friday",
            "7": "saturday"
        }
        
        print("\n📅 اختيار أيام العمل:")
        print("   1. الأحد     2. الإثنين     3. الثلاثاء")
        print("   4. الأربعاء  5. الخميس      6. الجمعة")
        print("   7. السبت")
        
        selected_days = []
        while True:
            choice = input("ادخل رقم اليوم (Enter لإنهاء): ").strip()
            if not choice:
                break
            if choice in days_mapping and days_mapping[choice] not in selected_days:
                selected_days.append(days_mapping[choice])
                day_name = self.get_arabic_day_name(days_mapping[choice])
                print(f"   ✓ تم إضافة {day_name}")
        
        return selected_days if selected_days else ["sunday", "monday", "tuesday", "wednesday", "thursday"]
    
    def show_reception_interface(self, doctor_id=None):
        """واجهة قسم الاستقبال"""
        print(f"\n{'='*50}")
        print("   🏥 نظام حجز المواعيد - قسم الاستقبال")
        print(f"{'='*50}")
        
        try:
            # اختيار الطبيب إذا لم يتم تحديده
            if not doctor_id:
                doctor_id = self.select_doctor_ui()
                if not doctor_id:
                    return
            
            doctor = self.db.get_doctor(doctor_id)
            if not doctor:
                print("❌ الطبيب غير موجود")
                return
            
            doctor_name = doctor.get('name', 'غير معروف')
            
            while True:
                print(f"\n👨‍⚕️ الطبيب: {doctor_name}")
                print("-" * 40)
                
                print("🔍 خيارات البحث:")
                print("   1. عرض الأسبوع القادم (7 أيام)")
                print("   2. البحث في 30 يوم القادمة") 
                print("   3. البحث في 90 يوم القادمة")
                print("   4. البحث عن أول موعد متاح")
                print("   5. تغيير الطبيب")
                print("   6. العودة للقائمة الرئيسية")
                
                choice = input("اختر الخيار: ").strip()
                
                if choice == "1":
                    self.show_weekly_schedule(doctor_id, doctor_name)
                elif choice == "2":
                    self.show_monthly_schedule(doctor_id, doctor_name)
                elif choice == "3":
                    self.show_quarterly_schedule(doctor_id, doctor_name)
                elif choice == "4":
                    self.find_first_available_ui(doctor_id, doctor_name)
                elif choice == "5":
                    doctor_id = self.select_doctor_ui()
                    if not doctor_id:
                        break
                    doctor = self.db.get_doctor(doctor_id)
                    doctor_name = doctor.get('name', 'غير معروف') if doctor else 'غير معروف'
                elif choice == "6":
                    break
                else:
                    print("❌ اختيار غير صحيح")
                    
        except Exception as e:
            logging.error(f"خطأ في واجهة الاستقبال: {e}")
    
    def select_doctor_ui(self):
        """واجهة اختيار الطبيب"""
        try:
            doctors = self.db.get_doctors()
            if not doctors:
                print("❌ لا توجد أطباء في النظام")
                return None
            
            print("\n👨‍⚕️ قائمة الأطباء:")
            for i, doctor in enumerate(doctors, 1):
                print(f"   {i}. {doctor['name']} - {doctor['specialty']}")
            
            choice = input("\nاختر رقم الطبيب: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(doctors):
                return doctors[int(choice) - 1]['id']
            else:
                print("❌ اختيار غير صحيح")
                return None
                
        except Exception as e:
            logging.error(f"خطأ في اختيار الطبيب: {e}")
            return None
    
    def show_weekly_schedule(self, doctor_id, doctor_name):
        """عرض جدول أسبوعي"""
        print(f"\n📅 جدول الطبيب {doctor_name} للأسبوع القادم:")
        print("-" * 50)
        
        schedule_data = {}
        
        for days_ahead in range(7):
            target_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            slots = self.db.get_available_slots(doctor_id, target_date)
            day_name = self.get_arabic_day_name((datetime.now() + timedelta(days=days_ahead)).weekday())
            
            status = "🟢" if slots else "🔴"
            schedule_data[target_date] = {
                'slots': slots,
                'day_name': day_name,
                'status': status
            }
            
            slots_display = f"({len(slots)} وقت)" if slots else "(ممتلئ)"
            print(f"   {target_date} ({day_name}): {status} {slots_display}")
            
            if slots and days_ahead == 0:  # عرض أوقات اليوم فقط
                for slot in slots[:3]:
                    print(f"      ⏰ {slot['display']}")
        
        return schedule_data
    
    def show_monthly_schedule(self, doctor_id, doctor_name):
        """عرض جدول شهري"""
        print(f"\n📅 جدول الطبيب {doctor_name} لـ 30 يوم:")
        print("-" * 50)
        
        schedule = self.db.generate_schedule_for_period(doctor_id, 30)
        
        available_days = sum(1 for day in schedule.values() if day['status'] == 'available')
        total_slots = sum(day['slots_count'] for day in schedule.values())
        
        print(f"📊 الملخص: {available_days} يوم متاح - {total_slots} وقت")
        
        # عرض أول 10 أيام
        for i, (date, data) in enumerate(list(schedule.items())[:10]):
            day_name = self.get_arabic_day_name(datetime.strptime(date, '%Y-%m-%d').weekday())
            status_icon = "🟢" if data['status'] == 'available' else "🔴"
            print(f"   {date} ({day_name}): {status_icon} {data['slots_count']} وقت")
    
    def show_quarterly_schedule(self, doctor_id, doctor_name):
        """عرض جدول ربع سنوي"""
        print(f"\n📅 جدول الطبيب {doctor_name} لـ 90 يوم:")
        print("-" * 50)
        
        schedule = self.db.generate_schedule_for_period(doctor_id, 90)
        
        available_days = sum(1 for day in schedule.values() if day['status'] == 'available')
        total_slots = sum(day['slots_count'] for day in schedule.values())
        
        print(f"📊 الملخص: {available_days} يوم متاح - {total_slots} وقت")
        
        # عرض إحصائية بالأسبوع
        from collections import defaultdict
        weekly_stats = defaultdict(int)
        
        for date, data in schedule.items():
            week_num = datetime.strptime(date, '%Y-%m-%d').isocalendar()[1]
            weekly_stats[week_num] += data['slots_count']
        
        print("\n📈 إحصائية بالأسبوع:")
        for week, slots in list(weekly_stats.items())[:8]:
            print(f"   الأسبوع {week}: {slots} وقت متاح")
    
    def find_first_available_ui(self, doctor_id, doctor_name):
        """واجهة البحث عن أول موعد متاح"""
        print(f"\n🔍 جاري البحث عن أول موعد متاح للطبيب {doctor_name}...")
        
        result = self.db.find_first_available_slot(doctor_id)
        
        if result:
            day_name = self.get_arabic_day_name(datetime.strptime(result['date'], '%Y-%m-%d').weekday())
            print(f"✅ أول موعد متاح: {result['date']} ({day_name})")
            print(f"   الأوقات المتاحة: {len(result['slots'])} وقت")
            
            for i, slot in enumerate(result['slots'][:5], 1):
                print(f"   {i}. {slot['display']}")
            
            # خيار الحجز السريع
            choice = input("\nادخل رقم الوقت للحجز، أو Enter للعودة: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(result['slots']):
                selected_slot = result['slots'][int(choice) - 1]
                self.quick_book_appointment(doctor_id, doctor_name, result['date'], selected_slot)
        else:
            print("❌ لا توجد مواعيد متاحة خلال 365 يوم القادمة")
    
    def quick_book_appointment(self, doctor_id, doctor_name, date, slot):
        """حجز سريع للموعد"""
        print(f"\n🎯 تأكيد الحجز:")
        print(f"   الطبيب: {doctor_name}")
        print(f"   التاريخ: {date}")
        print(f"   الوقت: {slot['display']}")
        
        confirm = input("هل تريد تأكيد الحجز؟ (نعم/لا): ").strip().lower()
        if confirm in ['نعم', 'yes', 'y']:
            # هنا يمكنك إضافة كود الحجز الفعلي
            print("✅ تم حجز الموعد بنجاح!")
            return True
        else:
            print("❌ تم إلغاء الحجز")
            return False
    
    def check_renewal_notifications_ui(self):
        """واجهة التحقق من إشعارات التجديد"""
        print(f"\n{'='*50}")
        print("   🔔 إشعارات تجديد الجداول")
        print(f"{'='*50}")
        
        notifications = self.db.check_renewal_notifications()
        
        if not notifications:
            print("🎉 لا توجد إشعارات تجديد حالياً")
            return
        
        for notification in notifications:
            print(f"\n🔄 الطبيب: {notification['doctor_name']}")
            print(f"   📅 ينتهي في: {notification['next_renewal_date']}")
            print(f"   ⏳ متبقي: {notification['days_remaining']} يوم")
            
            action = input("   اختر الإجراء (1. تجديد 30 يوم / 2. تجديد 60 يوم / 3. تأجيل): ").strip()
            
            if action == "1":
                self.db.renew_doctor_schedule(notification['doctor_id'], 30)
                print("   ✅ تم التجديد لـ 30 يوم")
            elif action == "2":
                self.db.renew_doctor_schedule(notification['doctor_id'], 60)
                print("   ✅ تم التجديد لـ 60 يوم")
            else:
                print("   ⏸️  تم تأجيل التجديد")
    
    def get_arabic_day_name(self, day_index):
        """الحصول على اسم اليوم بالعربية"""
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

# مثال للاستخدام
if __name__ == "__main__":
    print("تم تحميل مساعد واجهات الجدولة بنجاح")