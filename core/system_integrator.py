# system_integrator.py
# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
from PyQt5.QtCore import QTimer, pyqtSignal, QObject

class SystemIntegrator(QObject):
    """مكامل النظام - يدير التكامل بين جميع المكونات"""
    
    # إشارات النظام
    system_initialized = pyqtSignal(bool)
    schedules_renewed = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.auto_renew_timer = None
        self.health_check_timer = None
        
    def initialize_system(self):
        """تهيئة النظام بالكامل"""
        try:
            logging.info("🚀 بدء تهيئة النظام المتكامل...")
            
            # 1. إنشاء الجداول إذا لم تكن موجودة
            self.db_manager.create_scheduling_tables()
            
            # 2. تهيئة الإعدادات الافتراضية
            self.db_manager.initialize_default_periodic_settings()
            
            # 3. التحقق من الجداول الحالية وتجديدها إذا لزم الأمر
            renewed_count = self.db_manager.check_and_renew_schedules()
            
            # 4. بدء المراقبة التلقائية
            self.start_auto_monitoring()
            
            logging.info(f"✅ تم تهيئة النظام المتكامل بنجاح - تم تجديد {renewed_count} جدول")
            self.system_initialized.emit(True)
            
            return True
            
        except Exception as e:
            logging.error(f"❌ فشل في تهيئة النظام: {e}")
            self.system_initialized.emit(False)
            return False
    
    def start_auto_monitoring(self):
        """بدء المراقبة التلقائية للنظام"""
        try:
            # مؤقت التجديد التلقائي (كل 6 ساعات)
            self.auto_renew_timer = QTimer()
            self.auto_renew_timer.timeout.connect(self.auto_renew_schedules)
            self.auto_renew_timer.start(6 * 60 * 60 * 1000)  # 6 ساعات
            
            # مؤقت فحص صحة النظام (كل ساعة)
            self.health_check_timer = QTimer()
            self.health_check_timer.timeout.connect(self.health_check)
            self.health_check_timer.start(60 * 60 * 1000)  # ساعة
            
            logging.info("✅ بدء المراقبة التلقائية للنظام")
            
        except Exception as e:
            logging.error(f"❌ خطأ في بدء المراقبة التلقائية: {e}")
    
    def auto_renew_schedules(self):
        """التجديد التلقائي للجداول"""
        try:
            renewed_count = self.db_manager.check_and_renew_schedules()
            if renewed_count > 0:
                logging.info(f"✅ تم التجديد التلقائي لـ {renewed_count} جدول")
                self.schedules_renewed.emit(renewed_count)
                
        except Exception as e:
            logging.error(f"❌ خطأ في التجديد التلقائي: {e}")
            self.error_occurred.emit(f"خطأ في التجديد التلقائي: {str(e)}")
    
    def health_check(self):
        """فحص صحة النظام"""
        try:
            status = self.get_system_status()
            
            # التحقق من الأطباء بدون جداول
            doctors_without_schedules = status.get('doctors_without_schedules', 0)
            if doctors_without_schedules > 0:
                logging.warning(f"⚠️  يوجد {doctors_without_schedules} طبيب بدون جداول دورية")
                
            # التحقق من الجداول المنتهية
            expired_schedules = status.get('expired_schedules', 0)
            if expired_schedules > 0:
                logging.warning(f"⚠️  يوجد {expired_schedules} جدول منتهي يحتاج تجديد")
                
            logging.info("✅ فحص صحة النظام مكتمل")
            
        except Exception as e:
            logging.error(f"❌ خطأ في فحص صحة النظام: {e}")
    
    def get_system_status(self):
        """الحصول على حالة النظام الشاملة"""
        try:
            cursor = self.db_manager.conn.cursor()
            
            # عدد الأطباء
            cursor.execute('SELECT COUNT(*) as count FROM doctors')
            total_doctors = cursor.fetchone()['count']
            
            # عدد الأطباء النشطين
            cursor.execute('SELECT COUNT(*) as count FROM doctors WHERE is_active = 1')
            active_doctors = cursor.fetchone()['count']
            
            # عدد الجداول النشطة
            cursor.execute('SELECT COUNT(DISTINCT doctor_id) as count FROM doctor_periodic_schedules')
            active_schedules = cursor.fetchone()['count']
            
            # الأطباء بدون جداول
            cursor.execute('''
                SELECT COUNT(*) as count FROM doctors d
                LEFT JOIN periodic_schedule_settings p ON d.id = p.doctor_id
                WHERE p.doctor_id IS NULL AND d.is_active = 1
            ''')
            doctors_without_schedules = cursor.fetchone()['count']
            
            # الجداول المنتهية
            cursor.execute('''
                SELECT COUNT(*) as count FROM periodic_schedule_settings 
                WHERE next_renewal_date <= DATE('now')
            ''')
            expired_schedules = cursor.fetchone()['count']
            
            # إجمالي المواعيد
            cursor.execute('SELECT COUNT(*) as count FROM doctor_periodic_schedules')
            total_slots = cursor.fetchone()['count']
            
            # المواعيد المتاحة
            cursor.execute('SELECT COUNT(*) as count FROM doctor_periodic_schedules WHERE status = "available"')
            available_slots = cursor.fetchone()['count']
            
            # المواعيد المحجوزة
            cursor.execute('SELECT COUNT(*) as count FROM doctor_periodic_schedules WHERE status = "booked"')
            booked_slots = cursor.fetchone()['count']
            
            return {
                'total_doctors': total_doctors,
                'active_doctors': active_doctors,
                'active_schedules': active_schedules,
                'doctors_without_schedules': doctors_without_schedules,
                'expired_schedules': expired_schedules,
                'total_slots': total_slots,
                'available_slots': available_slots,
                'booked_slots': booked_slots,
                'occupancy_rate': (booked_slots / total_slots * 100) if total_slots > 0 else 0,
                'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logging.error(f"❌ خطأ في الحصول على حالة النظام: {e}")
            return {}
    
    def setup_doctor_complete_system(self, doctor_id):
        """إعداد نظام كامل للطبيب (جدولة + دورية)"""
        try:
            # 1. إعداد الجدولة الأساسية
            basic_success = self.db_manager.setup_doctor_schedule(doctor_id)
            
            # 2. إعداد الجدولة الدورية
            periodic_success = self.db_manager.setup_doctor_periodic_schedule(doctor_id, 30)
            
            # 3. إعداد الإعدادات الدورية
            cursor = self.db_manager.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO periodic_schedule_settings 
                (doctor_id, schedule_period_days, auto_renew_enabled, renewal_advance_days)
                VALUES (?, 30, 1, 7)
            ''', (doctor_id,))
            
            self.db_manager.conn.commit()
            
            if basic_success and periodic_success:
                logging.info(f"✅ تم إعداد النظام الكامل للطبيب {doctor_id}")
                return True
            else:
                logging.error(f"❌ فشل في إعداد النظام الكامل للطبيب {doctor_id}")
                return False
                
        except Exception as e:
            logging.error(f"❌ خطأ في إعداد النظام الكامل: {e}")
            return False
    
    def stop_system(self):
        """إيقاف النظام"""
        try:
            if self.auto_renew_timer:
                self.auto_renew_timer.stop()
            if self.health_check_timer:
                self.health_check_timer.stop()
                
            logging.info("✅ تم إيقاف نظام المراقبة التلقائية")
            
        except Exception as e:
            logging.error(f"❌ خطأ في إيقاف النظام: {e}")