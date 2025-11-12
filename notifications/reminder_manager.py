# notifications/reminder_manager.py
import logging
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal

class ReminderManager(QObject):
    """مدير التذكيرات - واجهة مبسطة للتكامل"""
    
    reminder_sent = pyqtSignal(dict)
    system_ready = pyqtSignal()
    
    def __init__(self, db_manager, clinic_id=1):
        super().__init__()
        self.db_manager = db_manager
        self.clinic_id = clinic_id
        self.reminder_system = None
        self.whatsapp_manager = None
        
        self.logger = logging.getLogger('ReminderManager')
    
    def initialize(self, whatsapp_manager):
        """تهيئة المدير مع WhatsAppManager"""
        try:
            from .reminder_system import ClinicReminderSystem
            
            self.whatsapp_manager = whatsapp_manager
            
            self.reminder_system = ClinicReminderSystem(
                db_manager=self.db_manager,
                whatsapp_manager=whatsapp_manager,
                clinic_id=self.clinic_id
            )
            
            # ربط الإشارات
            self.reminder_system.reminder_sent.connect(self.reminder_sent)
            self.reminder_system.system_status_changed.connect(self.on_system_status_changed)
            
            # بدء النظام
            success = self.reminder_system.start()
            
            if success:
                self.logger.info("✅ تم تهيئة مدير التذكيرات بنجاح")
                self.system_ready.emit()
                return True
            else:
                self.logger.error("❌ فشل تهيئة مدير التذكيرات")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ خطأ في تهيئة المدير: {e}")
            return False
    
    def on_system_status_changed(self, status):
        """عند تغيير حالة النظام"""
        self.logger.info(f"🔄 حالة النظام: {status}")
    
    def send_appointment_confirmation(self, appointment_id):
        """إرسال تأكيد موعد فوري"""
        try:
            if not self.reminder_system:
                self.logger.error("❌ نظام التذكيرات غير مهيء")
                return False
            
            return self.reminder_system.send_instant_confirmation(appointment_id)
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في إرسال التأكيد: {e}")
            return False
    
    def schedule_reminders(self, appointment_id):
        """جدولة تذكيرات الموعد"""
        try:
            if not self.reminder_system:
                self.logger.error("❌ نظام التذكيرات غير مهيء")
                return False
            
            return self.reminder_system.schedule_appointment_reminders(appointment_id)
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في جدولة التذكيرات: {e}")
            return False
    
    def get_status(self):
        """الحصول على حالة المدير"""
        if not self.reminder_system:
            return {'status': 'غير مهيء'}
        
        return self.reminder_system.get_system_status()
    
    def stop(self):
        """إيقاف المدير"""
        try:
            if self.reminder_system:
                self.reminder_system.stop()
                self.logger.info("⏹️ تم إيقاف مدير التذكيرات")
        except Exception as e:
            self.logger.error(f"❌ خطأ في إيقاف المدير: {e}")