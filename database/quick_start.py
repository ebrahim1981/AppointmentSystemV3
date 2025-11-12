# -*- coding: utf-8 -*-
from database_core import DatabaseCore

def quick_start():
    """بدء سريع للنظام"""
    print("🚀 بدء تشغيل نظام إدارة العيادات...")
    
    # إنشاء قاعدة البيانات
    db = DatabaseCore("data/clinics_professional.db")
    
    # اختبار النظام
    stats = db.get_dashboard_stats()
    print(f"📊 إحصائيات النظام:")
    print(f"   👥 المرضى: {stats.get('total_patients', 0)}")
    print(f"   👨‍⚕️ الأطباء: {stats.get('total_doctors', 0)}")
    print(f"   📅 مواعيد اليوم: {stats.get('today_appointments', 0)}")
    
    # عرض العيادات المتاحة
    clinics = db.get_clinics()
    print(f"🏥 العيادات المتاحة: {len(clinics)}")
    
    for clinic in clinics[:3]:  # عرض أول 3 عيادات فقط
        print(f"   - {clinic['name_ar']} ({clinic['code']})")
    
    print("✅ النظام جاهز للاستخدام!")
    return db

if __name__ == "__main__":
    db = quick_start()