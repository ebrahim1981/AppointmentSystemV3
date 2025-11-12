# -*- coding: utf-8 -*-
"""
دليل التكامل الشامل لنظام الجدولة الذكية
==========================================

هذا الدليل يشرح كيفية دمج نظام الجدولة الذكية مع نظامك الحالي
"""

class SchedulingIntegrationGuide:
    """دليل تكامل نظام الجدولة الذكية"""
    
    def __init__(self):
        self.guide_steps = {
            'التهيئة': self.initialization_guide,
            'التكامل_مع_واجهات_الأطباء': self.doctors_integration_guide,
            'التكامل_مع_واجهات_الاستقبال': self.reception_integration_guide,
            'نظام_الإشعارات': self.notifications_guide,
            'استكشاف_الأخطاء': self.troubleshooting_guide
        }
    
    def show_guide(self):
        """عرض الدليل الكامل"""
        print("\n" + "="*60)
        print("   📚 دليل تكامل نظام الجدولة الذكية")
        print("="*60)
        
        while True:
            print("\n📖 اختر قسم الدليل:")
            print("   1. التهيئة والإعداد الأولي")
            print("   2. التكامل مع واجهات الأطباء")
            print("   3. التكامل مع واجهات الاستقبال") 
            print("   4. نظام الإشعارات والتجديد")
            print("   5. استكشاف الأخطاء وإصلاحها")
            print("   6. خروج")
            
            choice = input("\nاختر القسم (1-6): ").strip()
            
            if choice == "1":
                self.initialization_guide()
            elif choice == "2":
                self.doctors_integration_guide()
            elif choice == "3":
                self.reception_integration_guide()
            elif choice == "4":
                self.notifications_guide()
            elif choice == "5":
                self.troubleshooting_guide()
            elif choice == "6":
                break
            else:
                print("❌ اختيار غير صحيح")
    
    def initialization_guide(self):
        """دليل التهيئة الأولية"""
        print(f"\n{'='*50}")
        print("   🔧 دليل التهيئة الأولية")
        print(f"{'='*50}")
        
        print("""
الخطوة 1: استيراد النظام
-------------------------
from database_manager import DatabaseManager
from scheduling_ui_helper import SchedulingUIHelper

الخطوة 2: تهيئة النظام
-----------------------
db = DatabaseManager()  # سيعمل تلقائياً على إنشاء الجداول

الخطوة 3: التحقق من التكامل
---------------------------
overview = db.get_scheduling_overview()
print(f"حالة النظام: {overview}")

الخطوة 4: إعداد الأطباء
-----------------------
# الطريقة الآلية (لجميع الأطباء):
db.initialize_default_schedules()

# الطريقة اليدوية (لطبيب محدد):
db.setup_doctor_schedule(doctor_id=1, appointment_duration=30)

الملاحظات:
• النظام سينشئ تلقائياً جداول الجدولة
• سيضيف بيانات افتراضية لأنواع الخدمات
• يمكن تعديل الإعدادات لاحقاً
        """)
    
    def doctors_integration_guide(self):
        """دليل التكامل مع واجهات الأطباء"""
        print(f"\n{'='*50}")
        print("   👨‍⚕️ دليل التكامل مع واجهات الأطباء")
        print(f"{'='*50}")
        
        print("""
إضافة زر إعداد الجدول في بطاقة الطبيب:
--------------------------------------

# في كود بطاقة الطبيب، أضف:

def setup_doctor_schedule(doctor_id, doctor_name):
    \"\"\"فتح نافذة إعداد جدول الطبيب\"\"\"
    try:
        from scheduling_ui_helper import SchedulingUIHelper
        from database_manager import DatabaseManager
        
        db = DatabaseManager()
        ui_helper = SchedulingUIHelper(db)
        
        success = ui_helper.setup_doctor_schedule_ui(doctor_id, doctor_name)
        
        if success:
            show_success_message("تم إعداد الجدول بنجاح")
        else:
            show_error_message("فشل في إعداد الجدول")
            
    except Exception as e:
        show_error_message(f"خطأ: {e}")

نماذج الاستخدام:
----------------

# 1. عند إنشاء طبيب جديد:
def create_new_doctor(doctor_data):
    # كود إنشاء الطبيب الحالي...
    doctor_id = save_doctor_to_database(doctor_data)
    
    # إضافة الجدول تلقائياً
    db.setup_doctor_schedule(doctor_id, appointment_duration=30)
    
    return doctor_id

# 2. في قائمة الأطباء:
def show_doctors_list():
    doctors = db.get_doctors()
    for doctor in doctors:
        print(f"الطبيب: {doctor['name']}")
        
        # زر إعداد الجدول
        if has_schedule(doctor['id']):
            print("[📅 تعديل الجدول]")
        else:
            print("[⚙️ إعداد الجدول]")

نصائح مهمة:
-----------
• اسأل الطبيب عن مدة الموعد المناسبة قبل الإعداد
• يمكن تعديل الإعدادات في أي وقت
• التغييرات تنعكس فوراً على الجداول
        """)
    
    def reception_integration_guide(self):
        """دليل التكامل مع واجهات الاستقبال"""
        print(f"\n{'='*50}")
        print("   🏥 دليل التكامل مع واجهات الاستقبال")
        print(f"{'='*50}")
        
        print("""
واجهة حجز المواعيد المحسنة:
----------------------------

def enhanced_booking_interface():
    \"\"\"واجهة حجز مواعيد محسنة\"\"\"
    from scheduling_ui_helper import SchedulingUIHelper
    from database_manager import DatabaseManager
    
    db = DatabaseManager()
    ui_helper = SchedulingUIHelper(db)
    
    # عرض واجهة الاستقبال
    ui_helper.show_reception_interface()

نماذج الاستخدام السريعة:
------------------------

# 1. البحث عن موعد لطبيب محدد:
def find_doctor_appointment(doctor_id):
    slots = db.get_available_slots(doctor_id, "2025-11-15")
    return slots

# 2. البحث عن أول موعد متاح:
def find_first_available(doctor_id):
    result = db.find_first_available_slot(doctor_id)
    return result

# 3. عرض جدول أسبوعي:
def show_weekly_schedule(doctor_id):
    schedule = db.generate_schedule_for_period(doctor_id, 7)
    return schedule

# 4. التحقق من التعارض:
def check_appointment_conflict(doctor_id, date, time):
    result = db.check_schedule_conflict(doctor_id, date, time)
    return result

واجهة مبسطة للكول سنتر:
-----------------------

def call_center_interface():
    \"\"\"واجهة مبسطة للكول سنتر\"\"\"
    print("مرحباً بك في خدمة حجز المواعيد")
    
    # اختيار الطبيب
    doctor_id = select_doctor()
    
    # البحث عن أول موعد متاح
    result = db.find_first_available_slot(doctor_id)
    
    if result:
        print(f"أول موعد متاح: {result['date']}")
        for slot in result['slots'][:3]:
            print(f"• {slot['display']}")
        
        # تأكيد الحجز
        if confirm_booking():
            return book_appointment(doctor_id, result['date'], result['slots'][0])
    else:
        print("نأسف، لا توجد مواعيد متاحة")

مميزات واجهة الاستقبال:
-----------------------
• عرض سريع لـ 7 أيام قادمة
• بحث ذكي عن أول موعد متاح
• منع التعارض التلقائي
• تجديد الجداول التلقائي
        """)
    
    def notifications_guide(self):
        """دليل نظام الإشعارات"""
        print(f"\n{'='*50}")
        print("   🔔 دليل نظام الإشعارات والتجديد")
        print(f"{'='*50}")
        
        print("""
نظام الإشعارات التلقائي:
------------------------

def check_daily_notifications():
    \"\"\"التحقق اليومي من الإشعارات\"\"\"
    from database_manager import DatabaseManager
    
    db = DatabaseManager()
    notifications = db.check_renewal_notifications()
    
    for notification in notifications:
        show_notification(
            title="تجديد الجدول",
            message=notification['message'],
            actions=[
                {"text": "تجديد 30 يوم", "action": lambda: db.renew_doctor_schedule(notification['doctor_id'], 30)},
                {"text": "تجديد 60 يوم", "action": lambda: db.renew_doctor_schedule(notification['doctor_id'], 60)},
                {"text": "تأجيل", "action": None}
            ]
        )

طريقة الدمج مع النظام الرئيسي:
-----------------------------

# في البرنامج الرئيسي، أضف:

def main_application():
    # تهيئة التطبيق...
    
    # التحقق من الإشعارات
    check_daily_notifications()
    
    # استمرار التطبيق العادي...

نماذج الإشعارات:
----------------

# 1. إشعار قبل يومين:
"🔄 تجديد الجدول - الطبيب: د. أحمد محمد
ينتهي خلال: 2 يوم
[تجديد 30 يوم] [تجديد 60 يوم] [تأجيل]"

# 2. إشعار عند الانتهاء:
"⚠️ انتهى الجدول - الطبيب: د. أحمد محمد
لا يمكن حجز مواعيد جديدة
[تجديد عاجل]"

إعدادات التخصيص:
----------------

# يمكن تخصيص فترات التجديد:
db.renew_doctor_schedule(doctor_id, 30)   # 30 يوم
db.renew_doctor_schedule(doctor_id, 60)   # 60 يوم  
db.renew_doctor_schedule(doctor_id, 90)   # 90 يوم
db.renew_doctor_schedule(doctor_id, 180)  # 6 أشهر

نصائح للإشعارات:
----------------
• تحقق من الإشعارات عند فتح التطبيق
• أضف صوت تنبيه للإشعارات العاجلة
• احفظ سجل للإشعارات السابقة
• اسمح بإيقاف الإشعارات للعيادات المغلوقة
        """)
    
    def troubleshooting_guide(self):
        """دليل استكشاف الأخطاء"""
        print(f"\n{'='*50}")
        print("   🔧 دليل استكشاف الأخطاء وإصلاحها")
        print(f"{'='*50}")
        
        print("""
المشكلة 1: لا تظهر أي أوقات متاحة
----------------------------------
السبب المحتمل: لم يتم إعداد جدول للطبيب
الحل: 
db.setup_doctor_schedule(doctor_id, appointment_duration=30)

المشكلة 2: خطأ في إنشاء الجداول
--------------------------------
السبب المحتمل: مشكلة في اتصال قاعدة البيانات
الحل:
1. تحقق من وجود مجلد data/
2. تحقق من صلاحيات الكتابة
3. جرب إعادة إنشاء قاعدة البيانات

المشكلة 3: التعارض لا يتم اكتشافه
----------------------------------
السبب المحتمل: المواعيد مخزنة بتنسيق مختلف
الحل:
تحقق من تنسيق الوقت في قاعدة البيانات (يجب أن يكون HH:MM)

المشكلة 4: الإشعارات لا تظهر
-----------------------------
السبب المحتمل: لم يتم تجديد الجدول مسبقاً
الحل:
db.renew_doctor_schedule(doctor_id, 30)

المشكلة 5: أداء بطيء
--------------------
السبب المحتمل: جداول كبيرة جداً
الحل:
• استخدم فترات أقصر (7 أيام بدل 30)
• حذف الجداول القديمة
• تحسين استعلامات قاعدة البيانات

أكواد فحص النظام:
------------------

def system_health_check():
    \"\"\"فحص صحة النظام\"\"\"
    from database_manager import DatabaseManager
    
    db = DatabaseManager()
    
    # 1. فحص الأطباء
    doctors = db.get_doctors()
    print(f"عدد الأطباء: {len(doctors)}")
    
    # 2. فحص الجداول
    for doctor in doctors:
        settings = db.get_doctor_schedule_settings(doctor['id'])
        print(f"الطبيب {doctor['name']}: {'لديه جدول' if settings else 'لا يوجد جدول'}")
    
    # 3. فحص الإشعارات
    notifications = db.check_renewal_notifications()
    print(f"عدد الإشعارات: {len(notifications)}")
    
    return len(doctors) > 0

نصائح الصيانة:
---------------
• اجري فحصاً أسبوعياً للنظام
• احفظ نسخ احتياطية للجداول
• سجل الأخطاء في ملف log
• حافظ على تحديث النظام
        """)

# تشغيل الدليل
if __name__ == "__main__":
    guide = SchedulingIntegrationGuide()
    guide.show_guide()