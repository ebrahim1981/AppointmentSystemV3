# notifications/desktop_notifier.py
# -*- coding: utf-8 -*-
import sys
import os
import logging
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QTimer, QObject, pyqtSignal, Qt

class UnifiedNotificationSystem(QObject):
    """نظام الإشعارات الموحد - يدمج الإشعارات الداخلية والخارجية - الإصدار المصحح بالكامل"""
    
    # إشارات للإشعارات الداخلية
    internal_notification = pyqtSignal(str, str)
    system_status_changed = pyqtSignal(str, str)
    
    def __init__(self, db_manager, settings_manager, main_window=None):
        super().__init__()
        self.db_manager = db_manager
        self.settings_manager = settings_manager
        self.main_window = main_window
        
        # أنظمة الإرسال
        self.auto_sender = None
        self.email_sender = None
        self.whatsapp_manager = None
        
        # إعداد النظام
        self.setup_auto_sender()  # ⭐⭐ تهيئة AutoSender أولاً ⭐⭐
        self.setup_tray_icon()
        self.setup_timers()
        
        # ربط الإشارات
        self.internal_notification.connect(self.show_desktop_notification)
        
        logging.info("✅ تم تهيئة نظام الإشعارات الموحد بنجاح")
    
    def setup_auto_sender(self):
        """إعداد نظام الإرسال التلقائي - الإصدار المصحح بالكامل"""
        try:
            # ⭐⭐ استيراد AutoSender من نفس المجلد ⭐⭐
            from .auto_sender import AutoSender
            
            # التأكد من أن المديرين غير null
            if self.db_manager is None:
                logging.error("❌ db_manager هو None - لا يمكن تهيئة AutoSender")
                self.auto_sender = None
                return
                
            if self.settings_manager is None:
                logging.error("❌ settings_manager هو None - لا يمكن تهيئة AutoSender")
                self.auto_sender = None
                return
            
            # تهيئة AutoSender
            self.auto_sender = AutoSender(self.db_manager, self.settings_manager)
            
            # ⭐⭐ ربط WhatsApp Manager إذا كان متوفراً ⭐⭐
            if hasattr(self, 'whatsapp_manager') and self.whatsapp_manager:
                self.auto_sender.whatsapp_sender = self.whatsapp_manager
                logging.info("✅ تم ربط WhatsApp Manager مع AutoSender")
            
            logging.info("✅ تم تهيئة نظام الإرسال التلقائي بنجاح")
            
        except ImportError as e:
            logging.error(f"❌ لم يتم العثور على AutoSender: {e}")
            self.auto_sender = None
        except Exception as e:
            logging.error(f"❌ فشل في تهيئة نظام الإرسال التلقائي: {e}")
            self.auto_sender = None
    
    def set_whatsapp_manager(self, whatsapp_manager):
        """تعيين مدير الواتساب - للربط مع النظام"""
        try:
            self.whatsapp_manager = whatsapp_manager
            
            # ⭐⭐ إذا كان AutoSender موجوداً، نقوم بربطه فوراً ⭐⭐
            if self.auto_sender and hasattr(self.auto_sender, 'whatsapp_sender'):
                self.auto_sender.whatsapp_sender = whatsapp_manager
                logging.info("✅ تم ربط WhatsApp Manager مع AutoSender")
            
            logging.info("✅ تم تعيين WhatsApp Manager في نظام الإشعارات")
        except Exception as e:
            logging.error(f"❌ فشل في تعيين WhatsApp Manager: {e}")
    
    def setup_tray_icon(self):
        """إعداد أيقونة النظام"""
        try:
            if QSystemTrayIcon.isSystemTrayAvailable():
                self.tray_icon = QSystemTrayIcon()
                
                # إنشاء أيقونة بسيطة
                pixmap = QPixmap(32, 32)
                pixmap.fill(Qt.blue)
                icon = QIcon(pixmap)
                self.tray_icon.setIcon(icon)
                self.tray_icon.setToolTip("نظام إدارة العيادة - الإشعارات")
                
                # إنشاء قائمة السياق
                tray_menu = QMenu()
                
                show_action = QAction("إظهار النافذة", self)
                show_action.triggered.connect(self.show_main_window)
                tray_menu.addAction(show_action)
                
                # إضافة إجراءات الإشعارات
                notification_menu = tray_menu.addMenu("🔔 إدارة الإشعارات")
                
                test_notif_action = QAction("اختبار الإشعار", self)
                test_notif_action.triggered.connect(self.test_notification)
                notification_menu.addAction(test_notif_action)
                
                # ⭐⭐ إضافة اختبار الإرسال التلقائي ⭐⭐
                test_auto_send_action = QAction("اختبار الإرسال التلقائي", self)
                test_auto_send_action.triggered.connect(self.test_auto_send_system)
                notification_menu.addAction(test_auto_send_action)
                
                settings_action = QAction("الإعدادات", self)
                settings_action.triggered.connect(self.open_notification_settings)
                notification_menu.addAction(settings_action)
                
                tray_menu.addSeparator()
                
                exit_action = QAction("خروج", self)
                exit_action.triggered.connect(self.quit_application)
                tray_menu.addAction(exit_action)
                
                self.tray_icon.setContextMenu(tray_menu)
                self.tray_icon.activated.connect(self.on_tray_activated)
                self.tray_icon.show()
                
                logging.info("✅ تم تفعيل أيقونة النظام بنجاح")
                
        except Exception as e:
            logging.error(f"❌ فشل في إعداد أيقونة النظام: {e}")
    
    def setup_timers(self):
        """إعداد المؤقتات للفحص الدوري"""
        # فحص التذكيرات كل دقيقة
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(60000)  # كل دقيقة
        
        # فحص الإشعارات المجدولة كل 5 دقائق
        self.scheduled_timer = QTimer()
        self.scheduled_timer.timeout.connect(self.check_scheduled_notifications)
        self.scheduled_timer.start(300000)  # كل 5 دقائق
        
        # ⭐⭐ فحص الاتصال كل 30 ثانية ⭐⭐
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.check_system_connection)
        self.connection_timer.start(30000)
        
        logging.info("✅ تم تفعيل المؤقتات الدورية للإشعارات")
    
    def check_system_connection(self):
        """فحص حالة اتصال النظام"""
        try:
            # فحص AutoSender
            auto_sender_status = "غير متوفر"
            if self.auto_sender:
                auto_sender_status = "نشط"
            
            # فحص WhatsApp Manager
            whatsapp_status = "غير متوفر"
            if self.whatsapp_manager:
                if hasattr(self.whatsapp_manager, 'is_connected'):
                    whatsapp_status = "متصل" if self.whatsapp_manager.is_connected else "غير متصل"
            
            # إرسال إشارة بحالة النظام
            status_msg = f"AutoSender: {auto_sender_status} | WhatsApp: {whatsapp_status}"
            self.system_status_changed.emit("system_connection", status_msg)
            
        except Exception as e:
            logging.error(f"❌ خطأ في فحص اتصال النظام: {e}")
    
    def check_reminders(self):
        """فحص التذكيرات الدورية - الإصدار المصحح"""
        try:
            if not self.auto_sender:
                logging.warning("⚠️ AutoSender غير متوفر لفحص التذكيرات")
                return
            
            # الحصول على الإعدادات
            settings = self.settings_manager.get_system_settings()
            
            # فحص تذكيرات 24 ساعة إذا كانت مفعلة
            if settings.get('reminder_24h_enabled') == '1':
                try:
                    self.auto_sender.send_24h_reminders()
                    logging.info("✅ تم فحص تذكيرات 24 ساعة")
                except Exception as e:
                    logging.error(f"❌ خطأ في إرسال تذكيرات 24 ساعة: {e}")
            
            # فحص تذكيرات ساعتين إذا كانت مفعلة
            if settings.get('reminder_2h_enabled') == '1':
                try:
                    self.auto_sender.send_2h_reminders()
                    logging.info("✅ تم فحص تذكيرات ساعتين")
                except Exception as e:
                    logging.error(f"❌ خطأ في إرسال تذكيرات ساعتين: {e}")
            
            # ⭐⭐ فحص التذكيرات الفورية للاختبار ⭐⭐
            if hasattr(self.auto_sender, 'test_mode') and self.auto_sender.test_mode:
                try:
                    if hasattr(self.auto_sender, 'send_immediate_reminders_test'):
                        self.auto_sender.send_immediate_reminders_test()
                        logging.info("✅ تم فحص التذكيرات الفورية للاختبار")
                except Exception as e:
                    logging.error(f"❌ خطأ في التذكيرات الفورية: {e}")
                
        except Exception as e:
            logging.error(f"❌ خطأ في فحص التذكيرات: {e}")
    
    def check_scheduled_notifications(self):
        """فحص الإشعارات المجدولة"""
        try:
            if not self.auto_sender:
                logging.warning("⚠️ AutoSender غير متوفر لفحص الإشعارات المجدولة")
                return
            
            # فحص الإشعارات المجدولة
            self.auto_sender.process_scheduled_notifications()
            
        except Exception as e:
            logging.error(f"❌ خطأ في فحص الإشعارات المجدولة: {e}")
    
    def show_desktop_notification(self, title, message):
        """عرض إشعار سطح المكتب (داخلي)"""
        try:
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, 5000)
                logging.info(f"📢 إشعار داخلي: {title} - {message}")
        except Exception as e:
            logging.error(f"❌ فشل في عرض الإشعار الداخلي: {e}")
    
    def send_external_notification(self, patient_id, notification_type, channel='whatsapp'):
        """إرسال إشعار خارجي للمريض"""
        try:
            if not self.auto_sender:
                logging.warning("⚠️ نظام الإرسال التلقائي غير متوفر")
                return False
            
            return self.auto_sender.send_notification(patient_id, notification_type, channel)
            
        except Exception as e:
            logging.error(f"❌ فشل في إرسال الإشعار الخارجي: {e}")
            return False
    
    def schedule_notification(self, patient_id, notification_type, send_time, channel='whatsapp'):
        """جدولة إشعار للمستقبل"""
        try:
            if not self.auto_sender:
                logging.warning("⚠️ AutoSender غير متوفر للجدولة")
                return False
            
            return self.auto_sender.schedule_notification(patient_id, notification_type, send_time, channel)
            
        except Exception as e:
            logging.error(f"❌ فشل في جدولة الإشعار: {e}")
            return False
    
    def notify_new_appointment(self, patient_name, appointment_time):
        """إشعار بموعد جديد (داخلي)"""
        title = "📅 موعد جديد"
        message = f"تم حجز موعد للمريض {patient_name} الساعة {appointment_time}"
        self.internal_notification.emit(title, message)
    
    def notify_reminder_sent(self, patient_name, channel, reminder_type="تذكير"):
        """إشعار بإرسال تذكير (داخلي) - محدث"""
        title = "🔔 تم إرسال التذكير"
        message = f"تم إرسال {reminder_type} للمريض {patient_name} عبر {channel}"
        self.internal_notification.emit(title, message)
        
        # ⭐⭐ تسجيل في سجل النظام ⭐⭐
        logging.info(f"✅ {reminder_type} مرسل: {patient_name} عبر {channel}")
    
    def notify_auto_send_status(self, status, details):
        """إشعار بحالة الإرسال التلقائي - جديد"""
        title = "🔄 حالة الإرسال التلقائي"
        message = f"{status}: {details}"
        self.internal_notification.emit(title, message)
        logging.info(f"🔄 الإرسال التلقائي - {status}: {details}")
    
    def notify_new_patient(self, patient_name):
        """إشعار بمريض جديد (داخلي)"""
        title = "👤 مريض جديد"
        message = f"تم إضافة المريض {patient_name} إلى النظام"
        self.internal_notification.emit(title, message)
    
    def notify_settings_saved(self):
        """إشعار بحفظ الإعدادات (داخلي)"""
        title = "⚙️ تم حفظ الإعدادات"
        message = "تم حفظ جميع الإعدادات بنجاح"
        self.internal_notification.emit(title, message)
    
    def notify_error(self, error_message):
        """إشعار بخطأ (داخلي)"""
        title = "❌ خطأ في النظام"
        message = error_message
        self.internal_notification.emit(title, message)
    
    def notify_backup_created(self, backup_path):
        """إشعار بنسخة احتياطية (داخلي)"""
        title = "💾 نسخة احتياطية"
        message = f"تم إنشاء نسخة احتياطية في: {backup_path}"
        self.internal_notification.emit(title, message)
    
    def notify_whatsapp_connected(self):
        """إشعار باتصال الواتساب (داخلي)"""
        title = "📱 اتصال واتساب"
        message = "تم الاتصال بنجاح مع خدمة الواتساب"
        self.internal_notification.emit(title, message)
    
    def test_auto_send_system(self):
        """اختبار نظام الإرسال التلقائي - من خلال واجهة النظام"""
        try:
            if not self.auto_sender:
                self.internal_notification.emit("❌ اختبار فاشل", "نظام الإرسال التلقائي غير متوفر")
                logging.error("❌ AutoSender غير متوفر للاختبار")
                return False
            
            # تفعيل وضع الاختبار
            if hasattr(self.auto_sender, 'set_test_mode'):
                self.auto_sender.set_test_mode(True)
                self.internal_notification.emit("🔧 وضع الاختبار", "تم تفعيل وضع الاختبار")
                logging.info("🔧 تم تفعيل وضع الاختبار في AutoSender")
            
            # اختبار الإرسال الفوري
            if hasattr(self.auto_sender, 'send_immediate_reminders_test'):
                result = self.auto_sender.send_immediate_reminders_test()
                
                if result:
                    self.internal_notification.emit("✅ اختبار ناجح", "تم اختبار الإرسال التلقائي بنجاح")
                    logging.info("✅ اختبار الإرسال التلقائي نجح")
                    return True
                else:
                    self.internal_notification.emit("❌ اختبار فاشل", "فشل في اختبار الإرسال التلقائي")
                    logging.error("❌ اختبار الإرسال التلقائي فشل")
                    return False
            else:
                self.internal_notification.emit("⚠️ غير متوفر", "الإرسال الفوري غير مدعوم")
                logging.warning("⚠️ send_immediate_reminders_test غير متوفر")
                return False
                
        except Exception as e:
            error_msg = f"فشل اختبار النظام: {str(e)}"
            self.internal_notification.emit("❌ خطأ في الاختبار", error_msg)
            logging.error(f"❌ فشل في اختبار الإرسال التلقائي: {e}")
            return False
    
    def test_notification(self):
        """اختبار نظام الإشعارات"""
        try:
            self.internal_notification.emit("🧪 اختبار الإشعارات", "هذا إشعار اختبار لنظام الإشعارات الموحد")
            
            # اختبار الإرسال التلقائي إذا كان متوفراً
            if self.auto_sender:
                test_result = self.auto_sender.test_system()
                if test_result:
                    self.internal_notification.emit("✅ اختبار ناجح", "تم اختبار نظام الإرسال بنجاح")
                else:
                    self.internal_notification.emit("❌ اختبار فاشل", "فشل في اختبار نظام الإرسال")
                    
        except Exception as e:
            logging.error(f"❌ فشل في اختبار الإشعارات: {e}")
            self.internal_notification.emit("❌ خطأ في الاختبار", f"فشل اختبار النظام: {e}")
    
    def on_tray_activated(self, reason):
        """عند التفاعل مع أيقونة النظام"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_main_window()
    
    def show_main_window(self):
        """إظهار النافذة الرئيسية"""
        try:
            if self.main_window:
                self.main_window.show()
                self.main_window.activateWindow()
                self.main_window.raise_()
                logging.info("✅ تم إظهار النافذة الرئيسية")
        except Exception as e:
            logging.error(f"❌ فشل في إظهار النافذة: {e}")
    
    def quit_application(self):
        """إغلاق التطبيق"""
        try:
            # إيقاف جميع المؤقتات
            timers = ['reminder_timer', 'scheduled_timer', 'connection_timer']
            for timer_name in timers:
                timer = getattr(self, timer_name, None)
                if timer and timer.isActive():
                    timer.stop()
                    logging.info(f"⏹️ تم إيقاف مؤقت: {timer_name}")
            
            # إغلاق أنظمة الإرسال
            if self.auto_sender:
                logging.info("⏹️ تم إغلاق نظام الإرسال التلقائي")
            
            if self.main_window:
                self.main_window.close()
            else:
                QApplication.quit()
                
            logging.info("✅ تم إغلاق تطبيق الإشعارات بنجاح")
        except Exception as e:
            logging.error(f"❌ فشل في إغلاق التطبيق: {e}")
    
    def open_notification_settings(self):
        """فتح إعدادات الإشعارات"""
        try:
            if self.main_window:
                # افترض أن النافذة الرئيسية لديها طريقة لفتح الإعدادات
                if hasattr(self.main_window, 'open_settings'):
                    self.main_window.open_settings('notifications')
                else:
                    QMessageBox.information(None, "الإعدادات", "الرجاء فتح إعدادات النظام من القائمة الرئيسية")
        except Exception as e:
            logging.error(f"❌ فشل في فتح إعدادات الإشعارات: {e}")
    
    def get_system_status(self):
        """الحصول على حالة النظام - جديدة"""
        status = {
            'auto_sender': 'غير متوفر',
            'whatsapp_manager': 'غير متوفر',
            'connection': 'غير معروف'
        }
        
        if self.auto_sender:
            status['auto_sender'] = 'نشط'
        
        if self.whatsapp_manager:
            status['whatsapp_manager'] = 'نشط'
            if hasattr(self.whatsapp_manager, 'is_connected'):
                status['whatsapp_manager'] = 'متصل' if self.whatsapp_manager.is_connected else 'غير متصل'
        
        return status
    
    def notify_system_ready(self):
        """إشعار بجاهزية النظام - جديدة"""
        self.internal_notification.emit("✅ النظام جاهز", "تم تحميل نظام الإشعارات والإرسال التلقائي بنجاح")
        logging.info("🎉 نظام الإشعارات الموحد جاهز للعمل")

# دالة مساعدة لإنشاء النظام
def create_notification_system(db_manager, settings_manager, main_window=None):
    """دالة مساعدة لإنشاء نظام الإشعارات - الإصدار المصحح"""
    try:
        notification_system = UnifiedNotificationSystem(db_manager, settings_manager, main_window)
        
        # ⭐⭐ اختبار النظام بعد التهيئة ⭐⭐
        if notification_system.auto_sender:
            logging.info("✅ AutoSender محمل وجاهز في نظام الإشعارات")
        else:
            logging.warning("⚠️ AutoSender غير متوفر في نظام الإشعارات")
        
        return notification_system
    except Exception as e:
        logging.error(f"❌ فشل في إنشاء نظام الإشعارات: {e}")
        return None