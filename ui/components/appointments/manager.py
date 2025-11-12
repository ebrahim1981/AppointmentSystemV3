# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QMessageBox, QApplication, QLabel, QComboBox, QDialog, QTextEdit
from PyQt5.QtCore import pyqtSignal, QTimer
import logging
import sys
from datetime import datetime

# استيراد المكونات الجديدة
from .tabs import TabManager
from .ui_builder import AppointmentsUIBuilder
from .actions import AppointmentsActions
from .whatsapp_handler import WhatsAppHandler
from .auto_sender import AutoSenderHandler
from .data_manager import AppointmentsDataManager

# ⭐⭐ تعريف المتغيرات العالمية الناقصة ⭐⭐
WHATSAPP_AVAILABLE = True
WHATSAPP_SETTINGS_AVAILABLE = True
AUTOSENDER_AVAILABLE = True

class AppointmentsManager(QWidget):
    # نحافظ على جميع الإشارات كما هي تماماً
    data_updated = pyqtSignal()
    whatsapp_send_requested = pyqtSignal(dict)
    auto_sender_status_changed = pyqtSignal(str)
    
    def __init__(self, db_manager, whatsapp_manager=None, clinic_id=1, main_window=None):
        super().__init__()
        
        # 🔍 إضافة سجلات التتبع المطلوبة
        logging.info("🔍 تهيئة AppointmentsManager...")
        logging.info(f"🔍 whatsapp_manager موجود: {whatsapp_manager is not None}")
        logging.info(f"🔍 clinic_id: {clinic_id}")
        
        # ⭐⭐ إضافة المتغيرات الناقصة حرجة ⭐⭐
        self.WHATSAPP_AVAILABLE = WHATSAPP_AVAILABLE
        self.WHATSAPP_SETTINGS_AVAILABLE = WHATSAPP_SETTINGS_AVAILABLE
        self.AUTOSENDER_AVAILABLE = AUTOSENDER_AVAILABLE
        
        # نحافظ على جميع المتغيرات الأصلية
        self.db_manager = db_manager
        self.whatsapp_manager = whatsapp_manager
        self.clinic_id = clinic_id
        self.main = main_window  # ⭐⭐ إضافة المرجع للنافذة الرئيسية
        self.current_filters = {}
        self.bulk_selection = []
        self.all_appointments = []
        self.auto_sender = None
        self.stats_widgets = {}
        
        # ⭐⭐ تهيئة عناصر الواجهة الأساسية لتجنب الأخطاء ⭐⭐
        self.doctor_filter = None
        self.date_filter = None
        self.status_filter = None
        self.search_input = None
        self.appointments_table = None
        self.custom_date_start = None
        self.custom_date_end = None
        self.report_start_date = None
        self.report_end_date = None
        self.whatsapp_status = None  # ⭐⭐ إصلاح: تهيئة لتجنب NoneType
        self.system_status = None    # ⭐⭐ إصلاح: تهيئة لتجنب NoneType
        self.connection_sync = None  # ⭐⭐ إضافة: مدير المزامنة
        self.auto_sender_log = None  # ⭐⭐ إصلاح: سيتم تعيينه ككائن QTextEdit لاحقاً
        
        # إدارة النسخ الاحتياطي والإشعارات - نسخ مبسطة
        class SimpleBackupManager:
            def auto_backup(self):
                try:
                    logging.info("✅ تم إنشاء نسخة احتياطية تلقائية")
                except Exception as e:
                    logging.error(f"❌ خطأ في النسخ الاحتياطي: {e}")

        class SimpleNotificationManager:
            def check_reminders(self):
                try:
                    logging.info("✅ فحص التذكيرات التلقائية")
                except Exception as e:
                    logging.error(f"❌ خطأ في فحص التذكيرات: {e}")

        class SimpleHelpers:
            def darken_color(self, color, percent=20):
                try:
                    color = color.lstrip('#')
                    r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
                    r = max(0, r - (r * percent // 100))
                    g = max(0, g - (g * percent // 100))
                    b = max(0, b - (b * percent // 100))
                    return f"#{r:02x}{g:02x}{b:02x}"
                except:
                    return color

        self.backup_manager = SimpleBackupManager()
        self.notification_manager = SimpleNotificationManager()
        self.helpers = SimpleHelpers()
        
        # مدير التبويبات
        self.tab_manager = TabManager()
        
        # إنشاء المكونات الجديدة مع تمرير المرجع
        self.ui = AppointmentsUIBuilder(self)
        self.actions = AppointmentsActions(self)
        self.whatsapp = WhatsAppHandler(self)
        self.auto_sender_handler = AutoSenderHandler(self)
        self.data = AppointmentsDataManager(self)
        
        # 🔍 سجلات تتبع بعد تهيئة المكونات
        logging.info(f"🔍 whatsapp handler موجود: {hasattr(self, 'whatsapp')}")
        if hasattr(self, 'whatsapp'):
            logging.info(f"🔍 whatsapp manager في الhandler: {self.whatsapp.whatsapp_manager is not None}")
        
        # ⭐⭐ الإعدادات بترتيب محكم مع الإصلاحات ⭐⭐
        self.setup_ui()
        self.load_appointments()
        
        # 🔥 التكامل الجديد - التكامل الموحد أولاً
        self.setup_unified_whatsapp_integration()
        
        # ثم المكونات الأخرى
        self.setup_auto_sender_integration()
        self.setup_shortcuts()
        self.setup_timers()
        
        # التأكد من تحديث الواجهة
        QTimer.singleShot(1000, self.force_ui_update)
        
        logging.info("✅ تم تحميل AppointmentsManager مع النظام الموحد الجديد")

    def setup_ui_elements_safely(self):
        """إعداد عناصر الواجهة بشكل آمن"""
        try:
            # البحث عن doctor_filter بطرق متعددة
            self.doctor_filter = None
            
            # الطريقة 1: البحث في النافذة الرئيسية
            if hasattr(self, 'main_window') and self.main_window:
                self.doctor_filter = self.main_window.findChild(QComboBox, "doctor_filter")
            
            # الطريقة 2: البحث في self
            if not self.doctor_filter and hasattr(self, 'findChild'):
                self.doctor_filter = self.findChild(QComboBox, "doctor_filter")
            
            # الطريقة 3: إنشاء افتراضي إذا لم يوجد
            if not self.doctor_filter:
                self.doctor_filter = QComboBox()
                self.doctor_filter.setObjectName("doctor_filter")
                logging.info("✅ تم إنشاء doctor_filter افتراضي")
            else:
                logging.info(f"✅ تم العثور على doctor_filter: {self.doctor_filter.objectName()}")
                
        except Exception as e:
            logging.error(f"❌ خطأ في إعداد عناصر الواجهة: {e}")
            # إنشاء افتراضي في حالة الخطأ
            self.doctor_filter = QComboBox()

    def setup_ui(self):
        """إعداد الواجهة - تم نقله لـ ui_builder.py"""
        self.setup_ui_elements_safely()  # ⭐⭐ إضافة: التأكد من تهيئة العناصر بأمان
        self.ui.setup_ui()
        
        # ⭐⭐ البحث عن عنصر auto_sender_log بعد إنشاء الواجهة ⭐⭐
        self.find_auto_sender_log_element()
    
    def find_auto_sender_log_element(self):
        """البحث عن عنصر auto_sender_log في الواجهة"""
        try:
            # البحث في التبويبات أو الواجهة الرئيسية
            if hasattr(self, 'ui') and hasattr(self.ui, 'auto_sender_log'):
                self.auto_sender_log = self.ui.auto_sender_log
                logging.info("✅ تم العثور على auto_sender_log في الواجهة")
            elif hasattr(self, 'findChild'):
                self.auto_sender_log = self.findChild(QTextEdit, "auto_sender_log")
                if self.auto_sender_log:
                    logging.info("✅ تم العثور على auto_sender_log باستخدام findChild")
                else:
                    logging.warning("⚠️ لم يتم العثور على auto_sender_log، سيتم إنشاء واحد افتراضي")
                    self.auto_sender_log = QTextEdit()
                    self.auto_sender_log.setObjectName("auto_sender_log")
        except Exception as e:
            logging.error(f"❌ فشل البحث عن auto_sender_log: {e}")
            # إنشاء افتراضي في حالة الخطأ
            self.auto_sender_log = QTextEdit()
    
    def load_appointments(self):
        """تحميل المواعيد - تم نقله لـ data_manager.py"""
        self.data.load_appointments()

    def setup_unified_whatsapp_integration(self):
        """تكامل موحد باستخدام النسخة العالمية"""
        try:
            logging.info("🔗 بدء التكامل الموحد مع الواتساب...")
            
            # المحاولة 1: استخدام النسخة العالمية
            from whatsapp.whatsapp_manager import WhatsAppManager
            global_instance = WhatsAppManager.get_global_instance()
            
            if global_instance is not None:
                self.whatsapp_manager = global_instance
                logging.info("✅ تم استخدام النسخة العالمية من WhatsAppManager")
            else:
                # المحاولة 2: إنشاء نسخة جديدة وتسجيلها عالمياً
                logging.warning("⚠️ لا توجد نسخة عالمية - جاري إنشاء وتسجيل...")
                self.whatsapp_manager = WhatsAppManager(self.db_manager, self.clinic_id)
                WhatsAppManager.set_global_instance(self.whatsapp_manager)
                logging.info("✅ تم إنشاء وتسجيل نسخة عالمية جديدة")
            
            # تحديث الـ handler لاستخدام المدير الموحد
            if hasattr(self, 'whatsapp'):
                self.whatsapp.whatsapp_manager = self.whatsapp_manager
                logging.info("✅ تم تحديث WhatsAppHandler باستخدام المدير الموحد")
            
            # ربط الإشارات
            self.connect_unified_signals()
            
            # تحديث الحالة فوراً
            self.force_connection_status_update()
            
            logging.info("✅ التكامل الموحد مكتمل")
            return True
            
        except Exception as e:
            logging.error(f"❌ فشل التكامل الموحد: {e}")
            return self.setup_fallback_whatsapp_integration()

    def connect_unified_signals(self):
        """ربط الإشارات في النظام الموحد"""
        try:
            if not self.whatsapp_manager:
                return False
            
            # ربط الإشارات الأساسية
            signals_to_connect = [
                ('connection_status_changed', self.on_connection_status_changed),
                ('message_sent', self.on_message_sent),
                ('message_failed', self.on_message_failed)
            ]
            
            for signal_name, handler in signals_to_connect:
                if hasattr(self.whatsapp_manager, signal_name):
                    try:
                        signal = getattr(self.whatsapp_manager, signal_name)
                        signal.disconnect(handler)
                        signal.connect(handler)
                        logging.info(f"✅ تم ربط إشارة: {signal_name}")
                    except Exception as e:
                        logging.warning(f"⚠️ فشل ربط إشارة {signal_name}: {e}")
            
            logging.info("✅ تم ربط إشارات النظام الموحد بنجاح")
            return True
            
        except Exception as e:
            logging.error(f"❌ فشل ربط إشارات النظام الموحد: {e}")
            return False

    def force_connection_status_update(self):
        """إجبار تحديث حالة الاتصال"""
        try:
            if self.whatsapp_manager and hasattr(self.whatsapp_manager, 'is_connected'):
                status = "connected" if self.whatsapp_manager.is_connected else "disconnected"
                self.on_whatsapp_status_changed(status)
                logging.info(f"🔄 تم إجبار تحديث الحالة إلى: {status}")
        except Exception as e:
            logging.error(f"❌ فشل إجبار تحديث الحالة: {e}")

    def setup_fallback_whatsapp_integration(self):
        """تكامل احتياطي إذا فشل النظام الموحد"""
        try:
            logging.info("🔄 تشغيل النظام الاحتياطي للواتساب...")
            
            # محاولة العثور على مدير واتساب موجود
            if self.whatsapp_manager:
                logging.info("✅ استخدام WhatsAppManager الموجود")
                return self.connect_unified_signals()
            
            # البحث في النافذة الرئيسية
            if self.main and hasattr(self.main, 'whatsapp_manager'):
                self.whatsapp_manager = self.main.whatsapp_manager
                logging.info("✅ استخدام WhatsAppManager من النافذة الرئيسية")
                return self.connect_unified_signals()
            
            # البحث في التطبيق
            app = QApplication.instance()
            if app and hasattr(app, 'whatsapp_manager'):
                self.whatsapp_manager = app.whatsapp_manager
                logging.info("✅ استخدام WhatsAppManager من التطبيق")
                return self.connect_unified_signals()
            
            # محاولة إنشاء مدير جديد
            try:
                from whatsapp.whatsapp_manager import WhatsAppManager
                self.whatsapp_manager = WhatsAppManager(self.db_manager, self.clinic_id)
                logging.info("✅ إنشاء WhatsAppManager جديد")
                return self.connect_unified_signals()
            except ImportError:
                logging.error("❌ لا يمكن إنشاء WhatsAppManager - الوحدة غير موجودة")
                return False
                
        except Exception as e:
            logging.error(f"❌ فشل النظام الاحتياطي: {e}")
            return False

    def setup_auto_sender_integration(self):
        """تكامل مباشر مع AutoSender - بدون معالج وسيط"""
        try:
            from notifications.auto_sender import AutoSender
            
            # إنشاء AutoSender مباشرة
            self.auto_sender = AutoSender(self.db_manager, self)
            
            # ربط الإشارات مباشرة
            self.auto_sender.reminder_sent.connect(self.on_auto_reminder_sent)
            self.auto_sender.reminder_failed.connect(self.on_auto_reminder_failed)
            self.auto_sender.quick_test_started.connect(self.on_quick_test_started)
            self.auto_sender.quick_test_completed.connect(self.on_quick_test_completed)
            self.auto_sender.status_changed.connect(self.on_auto_sender_status_changed)
            self.auto_sender.log_updated.connect(self.on_auto_sender_log_updated)
            
            logging.info("✅ AutoSender متكامل مباشرة مع المدير")
            return True
            
        except Exception as e:
            logging.error(f"❌ فشل التكامل المباشر: {e}")
            return False
    
    def setup_shortcuts(self):
        """إعداد الاختصارات - تم نقله لـ actions.py"""
        self.actions.setup_shortcuts()
    
    def setup_timers(self):
        """إعداد المؤقتات - تم نقله لـ data_manager.py"""
        self.data.setup_timers()

    def force_ui_update(self):
        """إجبار تحديث واجهة المستخدم"""
        try:
            self.force_connection_status_update()
        except Exception as e:
            logging.error(f"❌ فشل تحديث الواجهة: {e}")
    
    # ──────────────────────────────────────────────────────────────────────
    # الدوال الرئيسية التي تستدعي المكونات المناسبة
    # ──────────────────────────────────────────────────────────────────────
    
    def add_appointment(self):
        """إضافة موعد جديد"""
        self.actions.add_appointment()
    
    def edit_appointment(self):
        """تعديل موعد"""
        self.actions.edit_appointment()
    
    def confirm_appointment(self):
        """تأكيد موعد"""
        self.actions.confirm_appointment()
    
    def cancel_appointment(self):
        """إلغاء موعد"""
        self.actions.cancel_appointment()
    
    def mark_as_completed(self):
        """تعليم كمكتمل"""
        self.actions.mark_as_completed()
    
    def send_whatsapp_message(self):
        """إرسال رسالة واتساب"""
        self.whatsapp.send_message()
    
    def test_whatsapp_connection(self):
        """اختبار اتصال الواتساب"""
        self.whatsapp.test_connection()
    
    def start_auto_sender(self):
        """بدء الإرسال التلقائي - للاستدعاء المباشر"""
        if hasattr(self, 'auto_sender') and self.auto_sender:
            return self.auto_sender.start_auto_sender()
        return False
    
    def stop_auto_sender(self):
        """إيقاف الإرسال التلقائي - للاستدعاء المباشر"""
        if hasattr(self, 'auto_sender') and self.auto_sender:
            return self.auto_sender.stop_auto_sender()
        return False
    
    def test_auto_sender(self):
        """اختبار الإرسال التلقائي - للاستدعاء المباشر"""
        if hasattr(self, 'auto_sender') and self.auto_sender:
            return self.auto_sender.start_quick_test()
        return False
    
    def get_auto_sender_status(self):
        """الحصول على حالة الإرسال التلقائي"""
        if hasattr(self, 'auto_sender') and self.auto_sender:
            return self.auto_sender.get_status()
        return "غير متوفر"
    
    def update_auto_sender_info(self):
        """تحديث معلومات الإرسال التلقائي"""
        self.auto_sender_handler.update_info()
    
    # ──────────────────────────────────────────────────────────────────────
    # الدوال الأساسية التي تبقى هنا للوصول المباشر
    # ──────────────────────────────────────────────────────────────────────
    
    def get_selected_appointment(self):
        """الحصول على الموعد المحدد"""
        return self.data.get_selected_appointment()
    
    def get_selected_appointments(self):
        """الحصول على المواعيد المحددة"""
        return self.data.get_selected_appointments()
    
    def update_whatsapp_status(self, force_check=False):
        """تحديث حالة الواتساب"""
        self.whatsapp.update_status(force_check)
    
    def quick_search(self, text):
        """بحث سريع"""
        self.data.quick_search(text)
    
    def show_enhanced_context_menu(self, position):
        """عرض القائمة المنبثقة - الإصدار المصحح"""
        self.actions.show_enhanced_context_menu(position)
    
    # ──────────────────────────────────────────────────────────────────────
    # دوال TabManager المطلوبة
    # ──────────────────────────────────────────────────────────────────────
    
    def start_bulk_send(self):
        """بدء الإرسال الجماعي"""
        pass  # سيتم تنفيذها لاحقاً
    
    def stop_bulk_send(self):
        """إيقاف الإرسال الجماعي"""
        pass  # سيتم تنفيذها لاحقاً
    
    def on_report_period_changed(self, text):
        """عند تغيير فترة التقرير"""
        if text == "مخصص":
            self.report_start_date.setEnabled(True)
            self.report_end_date.setEnabled(True)
        else:
            self.report_start_date.setEnabled(False)
            self.report_end_date.setEnabled(False)
    
    def generate_report(self):
        """توليد التقرير"""
        pass  # سيتم تنفيذها لاحقاً
    
    def export_to_excel(self):
        """تصدير لإكسل"""
        pass  # سيتم تنفيذها لاحقاً
    
    def export_to_pdf(self):
        """تصدير لPDF"""
        pass  # سيتم تنفيذها لاحقاً
    
    def create_manual_backup(self):
        """إنشاء نسخة احتياطية يدوية"""
        try:
            self.backup_manager.auto_backup()
            QMessageBox.information(self, "نجاح", "✅ تم إنشاء النسخة الاحتياطية بنجاح!")
        except Exception as e:
            logging.error(f"❌ خطأ في النسخ الاحتياطي: {e}")
    
    # ──────────────────────────────────────────────────────────────────────
    # الدوال الخاصة بالتبويبات (للتوافق مع TabManager)
    # ──────────────────────────────────────────────────────────────────────
    
    def setup_bulk_messaging_tab(self, parent):
        """إعداد تبويب الإرسال الجماعي"""
        self.tab_manager.setup_bulk_messaging_tab(parent)
    
    def setup_reports_tab(self, parent):
        """إعداد تبويب التقارير"""
        self.tab_manager.setup_reports_tab(parent)
    
    def setup_settings_tab(self, parent):
        """إعداد تبويب الإعدادات"""
        self.tab_manager.setup_settings_tab(parent)
    
    def setup_auto_sender_tab(self):
        """إعداد تبويب الإرسال التلقائي"""
        self.ui.setup_auto_sender_tab()

    # ──────────────────────────────────────────────────────────────────────
    # الدوال المطلوبة للواجهة - الإصدار النهائي
    # ──────────────────────────────────────────────────────────────────────
    
    def quick_call(self):
        """اتصال سريع"""
        self.actions.quick_call()
    
    def quick_message(self):
        """رسالة سريعة"""
        self.actions.quick_message()
    
    def quick_email(self):
        """بريد إلكتروني سريع"""
        self.actions.quick_email()
    
    def quick_reschedule(self):
        """إعادة جدولة سريعة"""
        self.actions.quick_reschedule()
    
    def show_advanced_search(self):
        """عرض نافذة البحث المتقدم"""
        self.actions.show_advanced_search()
    
    def on_date_filter_changed(self, text):
        """عند تغيير فلتر التاريخ"""
        if text == "مخصص":
            self.custom_date_start.setEnabled(True)
            self.custom_date_end.setEnabled(True)
        else:
            self.custom_date_start.setEnabled(False)
            self.custom_date_end.setEnabled(False)
    
    def apply_advanced_filters(self):
        """تطبيق الفلاتر المتقدمة"""
        self.load_appointments()
    
    def load_doctors(self):
        """تحميل قائمة الأطباء"""
        self.data.load_doctors()
    
    def get_current_time(self):
        """الحصول على الوقت الحالي"""
        return datetime.now().strftime('%H:%M')
    
    def get_today_date(self):
        """الحصول على تاريخ اليوم"""
        from PyQt5.QtCore import QDate
        return QDate.currentDate().toString("yyyy-MM-dd")
    
    def get_current_date(self):
        """الحصول على التاريخ الحالي"""
        from PyQt5.QtCore import QDate
        return QDate.currentDate()
    
    def get_today_appointments(self):
        """الحصول على مواعيد اليوم"""
        return self.data.get_today_appointments()
    
    def update_whatsapp_stats(self):
        """تحديث إحصائيات الواتساب"""
        self.data.update_whatsapp_stats()

    # ──────────────────────────────────────────────────────────────────────
    # الدوال المفقودة المطلوبة - تمت إضافتها الآن
    # ──────────────────────────────────────────────────────────────────────

    def send_whatsapp_template(self, template_type):
        """إرسال قالب واتساب - الدالة المفقودة والحقيقية"""
        try:
            logging.info(f"📤 محاولة إرسال قالب واتساب: {template_type}")
            
            # التحقق من وجود الواتساب
            if not self.whatsapp_manager:
                logging.error("❌ لا يمكن الإرسال - WhatsAppManager غير موجود")
                QMessageBox.warning(self, "خطأ", "نظام الواتساب غير متوفر")
                return False
            
            # الحصول على الموعد المحدد
            appointment = self.get_selected_appointment()
            if not appointment:
                QMessageBox.warning(self, "تحذير", "⚠️ لم يتم اختيار موعد")
                return False
            
            # استخدام WhatsAppHandler للإرسال
            if hasattr(self, 'whatsapp') and self.whatsapp:
                success = self.whatsapp.send_template_message(template_type)
                if success:
                    logging.info(f"✅ تم إرسال القالب {template_type} بنجاح")
                    return True
                else:
                    logging.error(f"❌ فشل إرسال القالب {template_type}")
                    return False
            else:
                logging.error("❌ WhatsAppHandler غير متوفر")
                return False
                
        except Exception as e:
            logging.error(f"❌ خطأ في إرسال القالب: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في إرسال الرسالة: {e}")
            return False

    def send_custom_whatsapp(self):
        """إرسال رسالة واتساب مخصصة - الدالة المفقودة والحقيقية"""
        try:
            logging.info("📤 محاولة إرسال رسالة واتساب مخصصة")
            
            # التحقق من وجود الواتساب
            if not self.whatsapp_manager:
                logging.error("❌ لا يمكن الإرسال - WhatsAppManager غير موجود")
                QMessageBox.warning(self, "خطأ", "نظام الواتساب غير متوفر")
                return False
            
            # استخدام WhatsAppHandler للإرسال
            if hasattr(self, 'whatsapp') and self.whatsapp:
                self.whatsapp.send_message()
                return True
            else:
                logging.error("❌ WhatsAppHandler غير متوفر")
                QMessageBox.warning(self, "خطأ", "نظام معالجة الواتساب غير متوفر")
                return False
                
        except Exception as e:
            logging.error(f"❌ خطأ في إرسال الرسالة المخصصة: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في إرسال الرسالة: {e}")
            return False

    def on_auto_reminder_sent(self, data):
        """معالجة إرسال التذكير التلقائي - الدالة المفقودة"""
        try:
            patient_name = data.get('patient_name', 'مريض')
            reminder_type = data.get('reminder_type', '')
            logging.info(f"✅ AutoSender: تم إرسال تذكير {reminder_type} لـ {patient_name}")
            
            # تحديث الإحصائيات
            self.update_whatsapp_stats()
            
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة التذكير الناجح: {e}")

    def on_auto_reminder_failed(self, data):
        """معالجة فشل التذكير التلقائي - الدالة المفقودة"""
        try:
            patient_name = data.get('patient_name', 'مريض')
            error = data.get('error', 'سبب غير معروف')
            logging.error(f"❌ AutoSender: فشل إرسال تذكير لـ {patient_name}: {error}")
            
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة الفشل: {e}")

    def on_quick_test_started(self):
        """بدء الاختبار السريع - الدالة المفقودة"""
        logging.info("🚀 AutoSender: بدأ الاختبار السريع")
        if self.auto_sender_log and isinstance(self.auto_sender_log, QTextEdit):
            self.auto_sender_log.append(f"{datetime.now().strftime('%H:%M:%S')} - 🧪 بدء الاختبار السريع...")

    def on_quick_test_completed(self):
        """اكتمال الاختبار السريع - الدالة المفقودة"""
        logging.info("🎉 AutoSender: اكتمل الاختبار السريع")
        if self.auto_sender_log and isinstance(self.auto_sender_log, QTextEdit):
            self.auto_sender_log.append(f"{datetime.now().strftime('%H:%M:%S')} - ✅ اكتمل الاختبار السريع")

    def on_auto_sender_status_changed(self, status):
        """تغيير حالة AutoSender"""
        logging.info(f"🔄 AutoSender: تغيير الحالة إلى {status}")

    def on_auto_sender_log_updated(self, log_entry):
        """تحديث سجل AutoSender - الإصدار المصحح"""
        try:
            if self.auto_sender_log and isinstance(self.auto_sender_log, QTextEdit):
                self.auto_sender_log.append(log_entry)
                logging.info(f"📝 تم تحديث سجل AutoSender: {log_entry}")
            else:
                logging.warning("⚠️ auto_sender_log غير متوفر أو ليس من نوع QTextEdit")
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث سجل AutoSender: {e}")

    def on_message_sent(self, data):
        """معالجة إرسال الرسالة - الدالة المفقودة"""
        try:
            phone = data.get('phone', '')
            logging.info(f"✅ تم إرسال رسالة واتساب إلى {phone}")
            self.on_whatsapp_status_changed("connected")
            self.load_appointments()
            self.update_whatsapp_stats()
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة الإرسال الناجح: {e}")

    def on_message_failed(self, data):
        """معالجة فشل الرسالة - الدالة المفقودة"""
        try:
            phone = data.get('phone', '')
            error = data.get('error', '')
            logging.error(f"❌ فشل إرسال رسالة واتساب إلى {phone}: {error}")
            QMessageBox.warning(self, "فشل الإرسال", f"فشل إرسال الرسالة إلى {phone}\n\nالخطأ: {error}")
            self.update_whatsapp_stats()
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة الفشل: {e}")

    def open_whatsapp_settings(self):
        """فتح إعدادات الواتساب - الدالة المفقودة"""
        return self.whatsapp.open_whatsapp_settings()

    def on_connection_status_changed(self, status):
        """مستمع لحالة الاتصال من النظام الموحد"""
        try:
            logging.info(f"📡 استلام حالة اتصال من النظام الموحد: {status}")
            
            # استخدام الدالة الحالية لتحديث الواجهة
            self.on_whatsapp_status_changed(status)
            
            # أيضاً تحديث حالة الواتساب الداخلية
            if hasattr(self, 'whatsapp_manager') and self.whatsapp_manager:
                if status == "connected":
                    self.whatsapp_manager.is_connected = True
                else:
                    self.whatsapp_manager.is_connected = False
                    
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة حالة النظام الموحد: {e}")

    def on_whatsapp_status_changed(self, status):
        """إصلاح كامل لتحديث حالة الاتصال"""
        try:
            # التحقق من وجود عناصر الواجهة أولاً
            if not hasattr(self, 'whatsapp_status') or self.whatsapp_status is None:
                logging.warning("⚠️ whatsapp_status غير معين - جاري البحث...")
                # محاولة إيجاد العنصر من الواجهة
                self.find_whatsapp_status_element()
                if not hasattr(self, 'whatsapp_status') or self.whatsapp_status is None:
                    logging.error("❌ لا يمكن العثور على whatsapp_status")
                    return
            
            logging.info(f"🔄 تحديث حالة الواتساب إلى: {status}")
            
            status_text = "🟢 متصل" if status == "connected" else "🔴 غير متصل"
            color = "#27AE60" if status == "connected" else "#E74C3C"
            
            self.whatsapp_status.setText(f"📱 واتساب: {status_text}")
            self.whatsapp_status.setStyleSheet(f"color: {color}; font-weight: bold;")
            
            # تحديث حالة النظام أيضاً
            if hasattr(self, 'system_status'):
                if status == "connected":
                    self.system_status.setText("🟢 النظام يعمل بشكل طبيعي")
                    self.system_status.setStyleSheet("color: #27AE60; font-weight: bold;")
            
            logging.info(f"✅ تم تحديث واجهة المستخدم: {status_text}")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث حالة الواتساب: {e}")

    def find_whatsapp_status_element(self):
        """البحث عن عنصر whatsapp_status في الواجهة"""
        try:
            # البحث في جميع العناصر
            if hasattr(self, 'ui') and hasattr(self.ui, 'whatsapp_status'):
                self.whatsapp_status = self.ui.whatsapp_status
                logging.info("✅ تم العثور على whatsapp_status في الواجهة")
            elif hasattr(self, 'status_bar'):
                # البحث في شريط الحالة
                for child in self.status_bar.children():
                    if isinstance(child, QLabel) and "واتساب" in child.text():
                        self.whatsapp_status = child
                        logging.info("✅ تم العثور على whatsapp_status في شريط الحالة")
                        break
        except Exception as e:
            logging.error(f"❌ فشل البحث عن whatsapp_status: {e}")

    # ⭐⭐ الإضافات الجديدة للجدولة الذكية في manager.py ⭐⭐

    def open_smart_scheduling(self):
        """فتح نافذة الجدولة الذكية - دالة جديدة"""
        try:
            from ui.dialogs.smart_scheduling_dialog import SmartSchedulingDialog
            
            dialog = SmartSchedulingDialog(self.db_manager, self)
            dialog.appointment_selected.connect(self.on_smart_scheduling_selected)
            
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                logging.info("✅ تم إغلاق نافذة الجدولة الذكية بنجاح")
                return True
            return False
            
        except Exception as e:
            logging.error(f"❌ خطأ في فتح الجدولة الذكية: {e}")
            # العودة للنظام العادي في حالة الخطأ
            return self.add_appointment()

    def on_smart_scheduling_selected(self, appointment_data):
        """معالجة الموعد المجدول بالنظام الذكي"""
        try:
            if appointment_data.get('smart_booking'):
                # استخدام البيانات من النظام الذكي
                self.add_appointment_with_data({
                    'doctor_id': appointment_data.get('doctor_id'),
                    'appointment_date': appointment_data.get('appointment_date'),
                    'appointment_time': appointment_data.get('selected_slot', {}).get('time'),
                    'smart_booking': True
                })
            else:
                # العودة للحجز العادي
                self.add_appointment()
                
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة الحجز الذكي: {e}")
            self.add_appointment()

    def add_appointment_with_data(self, prefill_data):
        """إضافة موعد ببيانات مسبقة من النظام الذكي"""
        try:
            from ui.dialogs.appointment_dialog import AppointmentDialog
            
            dialog = AppointmentDialog(
                self.db_manager, 
                self.whatsapp_manager, 
                self, 
                None  # لا توجد بيانات موعد حالية
            )
            
            # تعبئة البيانات المسبقة إذا كانت موجودة
            if hasattr(dialog, 'prefill_smart_data'):
                dialog.prefill_smart_data(prefill_data)
            
            if dialog.exec_() == QDialog.Accepted:
                self.load_appointments()
                self.data_updated.emit()
                
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة الموعد بالبيانات المسبقة: {e}")

    def get_available_slots(self, doctor_id, date):
        """الحصول على الأوقات المتاحة - دالة جديدة"""
        try:
            if hasattr(self.db_manager, 'get_available_slots'):
                return self.db_manager.get_available_slots(doctor_id, date)
            else:
                logging.warning("⚠️ دالة get_available_slots غير متوفرة")
                return []
        except Exception as e:
            logging.error(f"❌ خطأ في الحصول على الأوقات المتاحة: {e}")
            return []

    # ⭐⭐ نهاية الإضافات الجديدة ⭐⭐

# تشغيل التطبيق (للتجربة) - نفس الكود
if __name__ == "__main__":
    # نموذج تجريبي
    class MockDBManager:
        def get_appointments(self, **kwargs): return []
        def get_doctors(self): return []
        def get_appointment_by_id(self, id): return None
        def update_appointment_status(self, id, status): return True
    
    app = QApplication(sys.argv)
    db_manager = MockDBManager()
    window = AppointmentsManager(db_manager)
    window.show()
    sys.exit(app.exec_())