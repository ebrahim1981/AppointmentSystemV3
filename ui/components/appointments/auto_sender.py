# ui/components/appointments/auto_sender.py
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QMessageBox
import logging
from datetime import datetime

class AutoSenderHandler:
    """معالج الإرسال التلقائي - الإصدار الموحد"""

    def __init__(self, main_app):
        self.main = main_app
        self.auto_sender = None
    
    def setup_integration(self):
        """التكامل مع AutoSender من المسار الصحيح الوحيد"""
        try:
            logging.info("🤖 بدء تكامل AutoSender من المسار الحقيقي...")
            
            # ⭐⭐ المسار الوحيد والصحيح ⭐⭐
            from notifications.auto_sender import AutoSender
            
            self.auto_sender = AutoSender(self.main.db_manager, self.main)
            self.main.auto_sender = self.auto_sender
            
            # ⭐⭐ إعداد مبسط بدون خطوات معقدة ⭐⭐
            self.auto_sender.setup_timers()
            
            # ربط الإشارات الأساسية فقط
            self.setup_auto_sender_signals()
            
            logging.info("✅ تكامل AutoSender مكتمل")
            return True
                
        except Exception as e:
            logging.error(f"❌ فشل تكامل AutoSender: {e}")
            return False

    def setup_auto_sender_signals(self):
        """ربط الإشارات الأساسية فقط"""
        try:
            if not self.auto_sender:
                return False
                
            # الإشارات الأساسية فقط
            self.auto_sender.reminder_sent.connect(self.main.on_auto_reminder_sent)
            self.auto_sender.reminder_failed.connect(self.main.on_auto_reminder_failed)
            self.auto_sender.status_changed.connect(self.on_auto_sender_status_changed)
            
            logging.info("✅ تم ربط إشارات AutoSender")
            return True
            
        except Exception as e:
            logging.error(f"❌ فشل ربط إشارات AutoSender: {e}")
            return False

    def on_auto_sender_status_changed(self, status):
        """معالجة تغيير حالة AutoSender"""
        logging.info(f"🔄 حالة AutoSender: {status}")

    def start(self):
        """بدء نظام الإرسال التلقائي"""
        try:
            if not self.auto_sender:
                logging.error("❌ AutoSender غير متوفر")
                return False
            
            if hasattr(self.auto_sender, 'start_auto_sender'):
                self.auto_sender.start_auto_sender()
                logging.info("🚀 تم بدء نظام الإرسال التلقائي")
                return True
            else:
                logging.error("❌ AutoSender لا يدعم بدء التشغيل")
                return False
                
        except Exception as e:
            logging.error(f"❌ خطأ في بدء AutoSender: {e}")
            return False
    
    def stop(self):
        """إيقاف نظام الإرسال التلقائي"""
        try:
            if not self.auto_sender:
                return False
            
            if hasattr(self.auto_sender, 'stop_auto_sender'):
                self.auto_sender.stop_auto_sender()
                logging.info("⏹️ تم إيقاف نظام الإرسال التلقائي")
                return True
            else:
                logging.error("❌ AutoSender لا يدعم إيقاف التشغيل")
                return False
                
        except Exception as e:
            logging.error(f"❌ خطأ في إيقاف AutoSender: {e}")
            return False
    
    def test(self):
        """اختبار نظام الإرسال التلقائي"""
        try:
            if not self.auto_sender:
                QMessageBox.warning(self.main, "تحذير", "❌ نظام الإرسال التلقائي غير متوفر")
                return False
            
            if hasattr(self.auto_sender, 'start_quick_test'):
                success = self.auto_sender.start_quick_test()
                if success:
                    QMessageBox.information(self.main, "نجاح", "🧪 تم بدء اختبار النظام التلقائي")
                    return True
                else:
                    QMessageBox.warning(self.main, "تحذير", "❌ فشل في بدء اختبار النظام التلقائي")
                    return False
            else:
                QMessageBox.warning(self.main, "تحذير", "❌ النظام لا يدعم الاختبار السريع")
                return False
                
        except Exception as e:
            logging.error(f"❌ خطأ في اختبار AutoSender: {e}")
            QMessageBox.critical(self.main, "خطأ", f"فشل الاختبار: {e}")
            return False
    
    def get_status(self):
        """الحصول على حالة نظام الإرسال التلقائي"""
        try:
            if not self.auto_sender:
                return {
                    'is_running': False,
                    'status': 'غير متوفر',
                    'check_interval': 0,
                    'last_check': None
                }
            
            if hasattr(self.auto_sender, 'get_status'):
                status = self.auto_sender.get_status()
                status['status'] = 'نشط' if status.get('is_running', False) else 'متوقف'
                return status
            else:
                return {
                    'is_running': False,
                    'status': 'غير معروف',
                    'check_interval': 0,
                    'last_check': None
                }
                
        except Exception as e:
            logging.error(f"❌ خطأ في جلب حالة AutoSender: {e}")
            return {
                'is_running': False,
                'status': f'خطأ: {e}',
                'check_interval': 0,
                'last_check': None
            }
    
    def update_info(self):
        """تحديث معلومات النظام التلقائي"""
        try:
            status = self.get_status()
            
            info_text = f"""
            🤖 نظام الإرسال التلقائي المتكامل
            
            📊 الحالة: {status.get('status', 'غير معروف')}
            ⏰ فترة الفحص: كل {status.get('check_interval', 0)} دقيقة
            🔄 آخر فحص: {status.get('last_check_time', 'لم يتم بعد')}
            📤 عدد الرسائل المرسلة: {status.get('sent_count', 0)}
            
            💡 الميزات المتوفرة:
            • ✅ إرسال تلقائي للفواتير الجديدة
            • ⏰ تذكيرات المواعيد التلقائية
            • 🔄 فحص دوري كل 5 دقائق
            • 📱 تكامل كامل مع واتساب
            """
            
            self.main.auto_sender_info.setText(info_text)
            
            # تحديث الإحصائيات
            stats_text = f"""
            📈 إحصائيات حية:
            
            • 🏥 عدد المواعيد اليوم: {len(self.main.get_today_appointments())}
            • 📱 حالة الواتساب: {'🟢 متصل' if self.main.whatsapp_manager and getattr(self.main.whatsapp_manager, 'is_connected', False) else '🔴 غير متصل'}
            • 🤖 حالة التلقائي: {'🟢 نشط' if status.get('is_running', False) else '🔴 متوقف'}
            • ⏰ وقت التشغيل: {datetime.now().strftime('%H:%M:%S')}
            """
            
            self.main.auto_sender_stats.setText(stats_text)
            
        except Exception as e:
            self.main.auto_sender_info.setText(f"❌ خطأ في تحديث المعلومات: {e}")