# ui/components/appointments/auto_sender.py
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QMessageBox
import logging
from datetime import datetime

class AutoSenderHandler:
    """معالج الإرسال التلقائي"""
    
    def __init__(self, main_app):
        self.main = main_app
        self.auto_sender = None
    
    def setup_integration(self):
        """إعداد تكامل AutoSender الحقيقي من المسار الصحيح"""
        try:
            logging.info("🤖 بدء تكامل AutoSender من المسار الحقيقي...")
            
            # المسار الحقيقي: AppointmentSystem\notifications\auto_sender.py
            try:
                from notifications.auto_sender import AutoSender
                logging.info("✅ تم استيراد AutoSender من notifications.auto_sender")
                AUTOSENDER_AVAILABLE = True
            except ImportError as e:
                logging.error(f"❌ فشل استيراد AutoSender من notifications: {e}")
                
                # محاولة بديلة: قد يكون في notifications.core
                try:
                    from notifications.core.auto_sender import AutoSender
                    logging.info("✅ تم استيراد AutoSender من notifications.core.auto_sender")
                    AUTOSENDER_AVAILABLE = True
                except ImportError as e2:
                    logging.error(f"❌ فشل استيراد AutoSender من notifications.core: {e2}")
                    AUTOSENDER_AVAILABLE = False
                    return False
            
            if not AUTOSENDER_AVAILABLE:
                logging.error("❌ AutoSender غير متوفر بعد جميع المحاولات")
                return False
            
            # إنشاء AutoSender
            logging.info("🔧 جاري إنشاء كائن AutoSender...")
            self.auto_sender = AutoSender(self.main.db_manager, self.main)
            self.main.auto_sender = self.auto_sender
            logging.info("✅ تم إنشاء AutoSender بنجاح")
            
            # مشاركة WhatsAppManager إذا كان موجوداً
            if self.main.whatsapp_manager:
                if hasattr(self.auto_sender, 'whatsapp_sender'):
                    self.auto_sender.whatsapp_sender = self.main.whatsapp_manager
                    logging.info("✅ تم مشاركة WhatsAppManager مع AutoSender")
                else:
                    logging.warning("⚠️ AutoSender لا يحتوي على whatsapp_sender")
            
            # إعداد AutoSender خطوة بخطوة
            self.setup_auto_sender_step_by_step()
            
            # ربط الإشارات
            signal_success = self.setup_auto_sender_signals_real()
            
            if signal_success:
                logging.info("🎯 تكامل AutoSender مكتمل بنجاح")
                return True
            else:
                logging.error("❌ تكامل AutoSender به مشاكل في الإشارات")
                return False
                
        except Exception as e:
            logging.error(f"❌ فشل تكامل AutoSender: {e}")
            return False

    def setup_auto_sender_step_by_step(self):
        """إعداد AutoSender خطوة بخطوة"""
        try:
            setup_steps = [
                ('setup_senders', 'إعداد المرسلين', []),
                ('setup_timers', 'إعداد المؤقتات', []),
                ('set_quick_test_mode', 'تعيين وضع الاختبار', [False])
            ]
            
            for method_name, description, args in setup_steps:
                if hasattr(self.auto_sender, method_name):
                    try:
                        method = getattr(self.auto_sender, method_name)
                        method(*args)
                        logging.info(f"✅ {description}")
                    except Exception as e:
                        logging.error(f"❌ فشل {description}: {e}")
                else:
                    logging.warning(f"⚠️ الدالة {method_name} غير موجودة في AutoSender")
                    
        except Exception as e:
            logging.error(f"❌ فشل الإعداد الخطوة بخطوة: {e}")

    def setup_auto_sender_signals_real(self):
        """ربط إشارات AutoSender الحقيقية"""
        try:
            if not self.auto_sender:
                logging.error("❌ لا يمكن ربط الإشارات - AutoSender غير موجود")
                return False
                
            logging.info("🔌 بدء ربط إشارات AutoSender...")
            
            # قائمة الإشارات المطلوبة
            signals_to_connect = [
                ('reminder_sent', 'on_auto_reminder_sent'),
                ('reminder_failed', 'on_auto_reminder_failed'), 
                ('quick_test_started', 'on_quick_test_started'),
                ('quick_test_completed', 'on_quick_test_completed')
            ]
            
            connected_count = 0
            for signal_name, handler_name in signals_to_connect:
                # التحقق من وجود الإشارة في AutoSender
                if not hasattr(self.auto_sender, signal_name):
                    logging.warning(f"⚠️ الإشارة {signal_name} غير موجودة في AutoSender")
                    continue
                    
                # التحقق من وجود المعالج في main
                if not hasattr(self.main, handler_name):
                    logging.warning(f"⚠️ المعالج {handler_name} غير موجود في main")
                    continue
                
                try:
                    signal = getattr(self.auto_sender, signal_name)
                    handler = getattr(self.main, handler_name)
                    
                    # فصل أي روابط سابقة
                    try:
                        signal.disconnect()
                    except:
                        pass
                    
                    # الربط الجديد
                    signal.connect(handler)
                    connected_count += 1
                    logging.info(f"✅ تم ربط إشارة: {signal_name} -> {handler_name}")
                    
                except Exception as e:
                    logging.error(f"❌ فشل ربط {signal_name}: {e}")
            
            logging.info(f"📊 تم ربط {connected_count} من {len(signals_to_connect)} إشارات")
            return connected_count > 0
            
        except Exception as e:
            logging.error(f"❌ فشل ربط إشارات AutoSender: {e}")
            return False
    
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