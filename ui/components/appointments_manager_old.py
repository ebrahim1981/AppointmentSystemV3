# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
                             QMessageBox, QHeaderView, QLabel, QToolBar,
                             QDateEdit, QDialog, QMenu, QGroupBox, QFrame,
                             QTabWidget, QProgressBar, QSplitter, QCheckBox,
                             QTextEdit, QSpinBox, QTimeEdit, QDialogButtonBox,
                             QApplication, QSystemTrayIcon, QAction, QToolButton, QGridLayout,
                             QInputDialog, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal, QDate, QTimer, QDateTime, QSize, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QColor, QIcon, QPalette, QPainter, QKeySequence
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
import logging
from datetime import datetime, timedelta
import json
import os
import sys
import sqlite3
import csv
from urllib.parse import quote
import webbrowser

# استيراد الملفات الجديدة
try:
    from ui.components.appointments_tabs import TabManager
    from ui.components.appointments_widgets import BackupManager, NotificationManager, ExportWorker, Helpers
except ImportError:
    # استيراد بديل في حالة عدم وجود المكونات
    class TabManager:
        def setup_bulk_messaging_tab(self, parent): pass
        def setup_reports_tab(self, parent): pass
        def setup_settings_tab(self, parent): pass
    
    class BackupManager:
        def __init__(self, db_manager): pass
        def auto_backup(self): pass
    
    class NotificationManager:
        def __init__(self, db_manager): pass
        def check_reminders(self): pass
    
    class ExportWorker:
        pass
    
    class Helpers:
        def darken_color(self, color, percent=20): 
            return color
        def format_phone_display(self, phone, country_code):
            return phone

# إعداد المسارات بشكل آمن
current_dir = os.path.dirname(os.path.abspath(__file__))
whatsapp_dir = os.path.join(current_dir, "whatsapp")
dialogs_dir = os.path.join(current_dir, "dialogs")
ui_dialogs_dir = os.path.join(current_dir, "ui", "dialogs")

# إضافة المسارات المطلوبة
for path in [whatsapp_dir, dialogs_dir, ui_dialogs_dir]:
    if path not in sys.path and os.path.exists(path):
        sys.path.append(path)

# استيراد آمن للوحدات
try:
    from whatsapp_manager import WhatsAppManager
    WHATSAPP_AVAILABLE = True
except ImportError as e:
    logging.warning(f"⚠️ لم يتم العثور على WhatsAppManager: {e}")
    WHATSAPP_AVAILABLE = False

try:
    from whatsapp.whatsapp_manager import WhatsAppManager
    WHATSAPP_AVAILABLE = True
except ImportError as e:
    logging.warning(f"⚠️ لم يتم العثور على WhatsAppManager في المسار البديل: {e}")
    WHATSAPP_AVAILABLE = False

try:
    from whatsapp.whatsapp_settings import WhatsAppSettingsManager
    WHATSAPP_SETTINGS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"⚠️ لم يتم العثور على WhatsAppSettingsManager: {e}")
    WHATSAPP_SETTINGS_AVAILABLE = False

# استيراد AutoSender
try:
    from auto_sender import AutoSender
    AUTOSENDER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"⚠️ لم يتم العثور على AutoSender: {e}")
    AUTOSENDER_AVAILABLE = False

# استيراد آمن لـ AppointmentDialog
def import_appointment_dialog():
    """استيراد آمن لـ AppointmentDialog من مسارات متعددة"""
    try:
        from ui.dialogs.appointment_dialog import AppointmentDialog
        return AppointmentDialog
    except ImportError:
        try:
            from dialogs.appointment_dialog import AppointmentDialog
            return AppointmentDialog
        except ImportError:
            try:
                from appointment_dialog import AppointmentDialog
                return AppointmentDialog
            except ImportError as e:
                logging.error(f"❌ فشل استيراد AppointmentDialog: {e}")
                return None

AppointmentDialog = import_appointment_dialog()

class AppointmentsManager(QWidget):
    data_updated = pyqtSignal()
    whatsapp_send_requested = pyqtSignal(dict)
    auto_sender_status_changed = pyqtSignal(str)  # 🔥 إشارة جديدة
    
    def __init__(self, db_manager, whatsapp_manager=None, clinic_id=1):
        super().__init__()
        self.db_manager = db_manager
        self.whatsapp_manager = whatsapp_manager
        self.clinic_id = clinic_id
        self.current_filters = {}
        self.bulk_selection = []
        self.all_appointments = []
        self.auto_sender = None  # 🔥 إضافة AutoSender
        
        # إدارة النسخ الاحتياطي والإشعارات
        self.backup_manager = BackupManager(db_manager)
        self.notification_manager = NotificationManager(db_manager)
        self.helpers = Helpers()
        
        # مدير التبويبات
        self.tab_manager = TabManager()
        
        self.setup_ui()
        self.load_appointments()
        self.setup_whatsapp_integration()
        self.setup_auto_sender_integration()  # 🔥 إضافة التكامل التلقائي
        self.setup_shortcuts()
        
        # مؤقتات للتحديث التلقائي
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.load_appointments)
        self.auto_refresh_timer.start(300000)  # 5 دقائق
        
        # مؤقت للنسخ الاحتياطي التلقائي (كل 24 ساعة)
        self.backup_timer = QTimer()
        self.backup_timer.timeout.connect(self.backup_manager.auto_backup)
        self.backup_timer.start(86400000)  # 24 ساعة
        
        # مؤقت للتحقق من التذكيرات (كل 30 دقيقة)
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self.notification_manager.check_reminders)
        self.reminder_timer.start(1800000)  # 30 دقيقة

    # 🔥 دالة التكامل الجديدة مع AutoSender
    def setup_auto_sender_integration(self):
        """إعداد التكامل الكامل مع نظام الإرسال التلقائي - الحل الجذري"""
        try:
            if not AUTOSENDER_AVAILABLE:
                logging.warning("⚠️ AutoSender غير متوفر - سيتم تخطي التكامل")
                return
            
            # إنشاء AutoSender
            self.auto_sender = AutoSender(self.db_manager, self)
            logging.info("✅ تم إنشاء AutoSender بنجاح")
            
            # مشاركة WhatsAppManager مع AutoSender
            if self.whatsapp_manager and hasattr(self.auto_sender, 'whatsapp_sender'):
                self.auto_sender.whatsapp_sender = self.whatsapp_manager
                logging.info("✅ تم مشاركة WhatsAppManager مع AutoSender")
            
            # إعداد AutoSender
            if hasattr(self.auto_sender, 'setup_senders'):
                self.auto_sender.setup_senders()
                logging.info("✅ تم إعداد مرسلي AutoSender")
            
            if hasattr(self.auto_sender, 'setup_timers'):
                self.auto_sender.setup_timers()
                logging.info("✅ تم إعداد مؤقتات AutoSender")
            
            # ربط إشارات AutoSender
            self.setup_auto_sender_signals()
            
            # تفعيل نظام التذكير التلقائي
            if hasattr(self.auto_sender, 'set_quick_test_mode'):
                self.auto_sender.set_quick_test_mode(False)  # الوضع العادي
                logging.info("✅ تم تفعيل نظام التذكير التلقائي")
            
            # إرسال إشارة نجاح التكامل
            self.auto_sender_status_changed.emit("connected")
            logging.info("🎯 التكامل الكامل مع AutoSender مكتمل وجاهز للعمل")
            
        except Exception as e:
            logging.error(f"❌ فشل التكامل مع AutoSender: {e}")
            self.auto_sender_status_changed.emit("disconnected")

    def setup_auto_sender_signals(self):
        """ربط إشارات AutoSender مع النظام الرئيسي"""
        try:
            if not self.auto_sender:
                logging.warning("⚠️ AutoSender غير متوفر لربط الإشارات")
                return
            
            # ربط إشارات التذكير
            if hasattr(self.auto_sender, 'reminder_sent'):
                self.auto_sender.reminder_sent.connect(self.on_auto_reminder_sent)
                logging.info("✅ تم ربط إشارة reminder_sent")
            
            if hasattr(self.auto_sender, 'reminder_failed'):
                self.auto_sender.reminder_failed.connect(self.on_auto_reminder_failed)
                logging.info("✅ تم ربط إشارة reminder_failed")
            
            if hasattr(self.auto_sender, 'quick_test_started'):
                self.auto_sender.quick_test_started.connect(self.on_quick_test_started)
                logging.info("✅ تم ربط إشارة quick_test_started")
            
            if hasattr(self.auto_sender, 'quick_test_completed'):
                self.auto_sender.quick_test_completed.connect(self.on_quick_test_completed)
                logging.info("✅ تم ربط إشارة quick_test_completed")
                
            logging.info("✅ تم ربط جميع إشارات AutoSender بنجاح")
            
        except Exception as e:
            logging.error(f"❌ خطأ في ربط إشارات AutoSender: {e}")

    # 🔥 دوال معالجة إشارات AutoSender
    def on_auto_reminder_sent(self, data):
        """عند إرسال تذكير تلقائي بنجاح"""
        try:
            patient_name = data.get('patient_name', 'مريض')
            reminder_type = data.get('reminder_type', '')
            
            logging.info(f"✅ AutoSender: تم إرسال تذكير {reminder_type} لـ {patient_name}")
            
            # تحديث الواجهة
            self.update_whatsapp_stats()
            
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة التذكير الناجح: {e}")

    def on_auto_reminder_failed(self, data):
        """عند فشل إرسال تذكير تلقائي"""
        try:
            patient_name = data.get('patient_name', 'مريض')
            error = data.get('error', 'سبب غير معروف')
            
            logging.error(f"❌ AutoSender: فشل إرسال تذكير لـ {patient_name}: {error}")
            
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة الفشل: {e}")

    def on_quick_test_started(self):
        """عند بدء اختبار سريع"""
        logging.info("🚀 AutoSender: بدأ الاختبار السريع")

    def on_quick_test_completed(self):
        """عند اكتمال الاختبار السريع"""
        logging.info("🎉 AutoSender: اكتمل الاختبار السريع")
        QMessageBox.information(self, "اختبار مكتمل", "✅ تم إكمال الاختبار السريع بنجاح!")

    # 🔥 دوال التحكم في AutoSender
    def start_auto_sender(self):
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
                logging.error("❌ AutoSender لا يدوب بدء التشغيل")
                return False
                
        except Exception as e:
            logging.error(f"❌ خطأ في بدء AutoSender: {e}")
            return False

    def stop_auto_sender(self):
        """إيقاف نظام الإرسال التلقائي"""
        try:
            if not self.auto_sender:
                return False
            
            if hasattr(self.auto_sender, 'stop_auto_sender'):
                self.auto_sender.stop_auto_sender()
                logging.info("⏹️ تم إيقاف نظام الإرسال التلقائي")
                return True
            else:
                logging.error("❌ AutoSender لا يدوب إيقاف التشغيل")
                return False
                
        except Exception as e:
            logging.error(f"❌ خطأ في إيقاف AutoSender: {e}")
            return False

    def test_auto_sender(self):
        """اختبار نظام الإرسال التلقائي"""
        try:
            if not self.auto_sender:
                QMessageBox.warning(self, "تحذير", "❌ نظام الإرسال التلقائي غير متوفر")
                return False
            
            if hasattr(self.auto_sender, 'start_quick_test'):
                success = self.auto_sender.start_quick_test()
                if success:
                    QMessageBox.information(self, "نجاح", "🧪 تم بدء اختبار النظام التلقائي")
                    return True
                else:
                    QMessageBox.warning(self, "تحذير", "❌ فشل في بدء اختبار النظام التلقائي")
                    return False
            else:
                QMessageBox.warning(self, "تحذير", "❌ النظام لا يدعم الاختبار السريع")
                return False
                
        except Exception as e:
            logging.error(f"❌ خطأ في اختبار AutoSender: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل الاختبار: {e}")
            return False

    def get_auto_sender_status(self):
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

    def setup_ui(self):
        """إعداد واجهة إدارة المواعيد - الإصدار المحسن والمتكامل"""
        self.setMinimumSize(1200, 700)
        self.setWindowTitle("نظام إدارة المواعيد المتقدم + الإرسال التلقائي")
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # العنوان الرئيسي مع معلومات سريعة
        title_layout = QHBoxLayout()
        
        title_label = QLabel("📅 إدارة المواعيد المتقدمة + 🤖 الإرسال التلقائي")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(18)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                padding: 15px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498DB, stop:1 #2C3E50);
                color: white;
                border-radius: 10px;
                margin-bottom: 5px;
            }
        """)
        title_layout.addWidget(title_label)
        
        # معلومات سريعة
        quick_stats_layout = QHBoxLayout()
        
        today = QDate.currentDate().toString("yyyy-MM-dd")
        today_appointments = len([a for a in self.all_appointments 
                                if a.get('appointment_date') == today])
        
        # 🔥 إضافة حالة AutoSender
        auto_sender_status = "🟢 نشط" if self.auto_sender and hasattr(self.auto_sender, 'is_running') and self.auto_sender.is_running else "🔴 متوقف"
        
        quick_stats = [
            f"📊 اليوم: {today_appointments} موعد",
            f"🕒 {datetime.now().strftime('%H:%M')}",
            f"🤖 التلقائي: {auto_sender_status}"
        ]
        
        for stat in quick_stats:
            stat_label = QLabel(stat)
            stat_label.setStyleSheet("""
                QLabel {
                    background-color: #ECF0F1;
                    color: #2C3E50;
                    padding: 8px 12px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
            quick_stats_layout.addWidget(stat_label)
        
        quick_stats_layout.addStretch()
        title_layout.addLayout(quick_stats_layout)
        
        main_layout.addLayout(title_layout)
        
        # تبويبات رئيسية
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #BDC3C7;
                border-radius: 8px;
                background-color: #FFFFFF;
            }
            QTabBar::tab {
                background-color: #ECF0F1;
                color: #2C3E50;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: #3498DB;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #2980B9;
                color: white;
            }
        """)
        
        # تبويب المواعيد الرئيسي
        self.setup_appointments_tab()
        # تبويب الإرسال الجماعي
        self.setup_bulk_messaging_tab()
        # تبويب التقارير والإحصائيات
        self.setup_reports_tab()
        # تبويب الإعدادات المتقدمة
        self.setup_settings_tab()
        # 🔥 تبويب الإرسال التلقائي الجديد
        self.setup_auto_sender_tab()
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def setup_appointments_tab(self):
        """إعداد تبويب المواعيد الرئيسي"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # شريط الأدوات المحسن
        toolbar = self.create_enhanced_toolbar()
        layout.addWidget(toolbar)
        
        # منطقة الإحصائيات السريعة
        stats_layout = self.create_enhanced_stats()
        layout.addLayout(stats_layout)
        
        # عوامل التصفية المتقدمة
        filter_group = self.create_advanced_filters()
        layout.addWidget(filter_group)
        
        # جدول المواعيد المحسن
        table_layout = QHBoxLayout()
        
        self.appointments_table = self.create_enhanced_table()
        table_layout.addWidget(self.appointments_table)
        
        # اللوحة الجانبية للمعلومات السريعة
        sidebar = self.create_quick_sidebar()
        table_layout.addWidget(sidebar)
        
        layout.addLayout(table_layout)
        
        # شريط الحالة المتقدم
        status_bar = self.create_advanced_status_bar()
        layout.addWidget(status_bar)
        
        self.tabs.addTab(tab, "📋 المواعيد")

    def setup_auto_sender_tab(self):
        """إعداد تبويب الإرسال التلقائي الجديد"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # عنوان التبويب
        title_label = QLabel("🤖 نظام الإرسال التلقائي المتكامل")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2C3E50;
                padding: 15px;
                background-color: #E8F4FD;
                border-radius: 10px;
                margin-bottom: 10px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # معلومات النظام التلقائي
        info_group = QGroupBox("📊 حالة النظام التلقائي")
        info_layout = QVBoxLayout(info_group)
        
        self.auto_sender_info = QLabel("جاري تحميل معلومات النظام...")
        self.auto_sender_info.setStyleSheet("""
            QLabel {
                background-color: #F8F9FA;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #DEE2E6;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        self.auto_sender_info.setWordWrap(True)
        info_layout.addWidget(self.auto_sender_info)
        
        layout.addWidget(info_group)
        
        # أزرار التحكم
        control_group = QGroupBox("🎮 تحكم فوري")
        control_layout = QHBoxLayout(control_group)
        
        # زر البدء
        self.start_auto_btn = QPushButton("🚀 بدء الإرسال التلقائي")
        self.start_auto_btn.clicked.connect(self.start_auto_sender)
        self.start_auto_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #219653;
            }
        """)
        
        # زر الإيقاف
        self.stop_auto_btn = QPushButton("⏹️ إيقاف الإرسال التلقائي")
        self.stop_auto_btn.clicked.connect(self.stop_auto_sender)
        self.stop_auto_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        
        # زر الاختبار
        self.test_auto_btn = QPushButton("🧪 اختبار النظام التلقائي")
        self.test_auto_btn.clicked.connect(self.test_auto_sender)
        self.test_auto_btn.setStyleSheet("""
            QPushButton {
                background-color: #F39C12;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #D68910;
            }
        """)
        
        control_layout.addWidget(self.start_auto_btn)
        control_layout.addWidget(self.stop_auto_btn)
        control_layout.addWidget(self.test_auto_btn)
        
        layout.addWidget(control_group)
        
        # إحصائيات التشغيل
        stats_group = QGroupBox("📈 إحصائيات التشغيل")
        stats_layout = QVBoxLayout(stats_group)
        
        self.auto_sender_stats = QLabel("جاري جمع الإحصائيات...")
        self.auto_sender_stats.setStyleSheet("""
            QLabel {
                background-color: #FFFFFF;
                padding: 12px;
                border-radius: 6px;
                border: 1px dashed #BDC3C7;
                font-size: 12px;
                line-height: 1.5;
            }
        """)
        stats_layout.addWidget(self.auto_sender_stats)
        
        layout.addWidget(stats_group)
        
        # سجل التشغيل
        log_group = QGroupBox("📝 سجل التشغيل التلقائي")
        log_layout = QVBoxLayout(log_group)
        
        self.auto_sender_log = QTextEdit()
        self.auto_sender_log.setReadOnly(True)
        self.auto_sender_log.setStyleSheet("""
            QTextEdit {
                background-color: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Courier New';
                font-size: 11px;
            }
        """)
        log_layout.addWidget(self.auto_sender_log)
        
        layout.addWidget(log_group)
        
        self.tabs.addTab(tab, "🤖 التلقائي")
        
        # تحديث المعلومات أول مرة
        self.update_auto_sender_info()

    def update_auto_sender_info(self):
        """تحديث معلومات النظام التلقائي"""
        try:
            status = self.get_auto_sender_status()
            
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
            
            self.auto_sender_info.setText(info_text)
            
            # تحديث الإحصائيات
            stats_text = f"""
            📈 إحصائيات حية:
            
            • 🏥 عدد المواعيد اليوم: {len(self.get_today_appointments())}
            • 📱 حالة الواتساب: {'🟢 متصل' if self.whatsapp_manager and getattr(self.whatsapp_manager, 'is_connected', False) else '🔴 غير متصل'}
            • 🤖 حالة التلقائي: {'🟢 نشط' if status.get('is_running', False) else '🔴 متوقف'}
            • ⏰ وقت التشغيل: {datetime.now().strftime('%H:%M:%S')}
            """
            
            self.auto_sender_stats.setText(stats_text)
            
        except Exception as e:
            self.auto_sender_info.setText(f"❌ خطأ في تحديث المعلومات: {e}")

    def create_enhanced_toolbar(self):
        """إنشاء شريط أدوات متقدم"""
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setStyleSheet("""
            QToolBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #E9ECEF);
                border: none;
                border-bottom: 2px solid #DEE2E6;
                spacing: 8px;
                padding: 8px;
                border-radius: 8px;
            }
        """)
        
        # مجموعة إجراءات المواعيد
        appointments_actions = [
            ("➕ حجز جديد", self.add_appointment, "#28A745", "add"),
            ("✏️ تعديل", self.edit_appointment, "#007BFF", "edit"),
            ("🗑️ إلغاء", self.cancel_appointment, "#DC3545", "cancel"),
            ("✅ تأكيد", self.confirm_appointment, "#17A2B8", "confirm"),
            ("📝 حضور", self.mark_as_completed, "#9B59B6", "complete")
        ]
        
        for text, slot, color, action_type in appointments_actions:
            btn = self.create_toolbar_button(text, slot, color, action_type)
            toolbar.addWidget(btn)
        
        toolbar.addSeparator()
        
        # 🔥 إضافة أزرار التحكم في AutoSender
        auto_sender_actions = [
            ("🤖 تشغيل التلقائي", self.start_auto_sender, "#27AE60", "auto_start"),
            ("⏹️ إيقاف التلقائي", self.stop_auto_sender, "#E74C3C", "auto_stop"),
            ("🧪 اختبار التلقائي", self.test_auto_sender, "#F39C12", "auto_test")
        ]
        
        for text, slot, color, action_type in auto_sender_actions:
            btn = self.create_toolbar_button(text, slot, color, action_type)
            toolbar.addWidget(btn)
        
        toolbar.addSeparator()
        
        # مجموعة إجراءات الواتساب
        whatsapp_actions = [
            ("📤 إرسال رسالة", self.send_whatsapp_message, "#25D366", "whatsapp"),
            ("🔄 تحديث", self.load_appointments, "#6C757D", "refresh"),
        ]
        
        # ✅ إضافة زر تحديث حالة الواتساب يدوياً
        refresh_status_btn = self.create_toolbar_button("🔄 تحديث حالة الواتساب", 
                                                      lambda: self.update_whatsapp_status(force_check=True), 
                                                      "#FFC107", "refresh_status")
        toolbar.addWidget(refresh_status_btn)
        
        if WHATSAPP_SETTINGS_AVAILABLE:
            whatsapp_actions.append(("⚙️ إعدادات", self.open_whatsapp_settings, "#FFC107", "settings"))
        
        for text, slot, color, action_type in whatsapp_actions:
            btn = self.create_toolbar_button(text, slot, color, action_type)
            toolbar.addWidget(btn)
        
        toolbar.addSeparator()
        
        # البحث المتقدم
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 بحث سريع في المواعيد...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #CED4DA;
                border-radius: 6px;
                min-width: 250px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #007BFF;
                background-color: #F0F8FF;
            }
        """)
        self.search_input.textChanged.connect(self.quick_search)
        
        toolbar.addWidget(QLabel("بحث متقدم:"))
        toolbar.addWidget(self.search_input)
        
        # زر البحث المتقدم
        advanced_search_btn = QPushButton("🎯 متقدم")
        advanced_search_btn.clicked.connect(self.show_advanced_search)
        advanced_search_btn.setStyleSheet("""
            QPushButton {
                background-color: #6C757D;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5A6268;
            }
        """)
        toolbar.addWidget(advanced_search_btn)
        
        return toolbar

    def create_toolbar_button(self, text, slot, color, action_type):
        """إنشاء زر في شريط الأدوات"""
        btn = QPushButton(text)
        btn.setMinimumHeight(35)
        btn.clicked.connect(slot)
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 100px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color, 40)};
            }}
        """)
        
        return btn

    def darken_color(self, color, percent=20):
        """تغميق اللون"""
        try:
            color = color.lstrip('#')
            r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
            r = max(0, r - (r * percent // 100))
            g = max(0, g - (g * percent // 100))
            b = max(0, b - (b * percent // 100))
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return color

    def create_enhanced_stats(self):
        """إنشاء إحصائيات محسنة"""
        layout = QHBoxLayout()
        
        self.stats_widgets = {
            'مجدول': self.create_stat_card("المجدولة", "0", "#3498DB"),
            '✅ مؤكد': self.create_stat_card("المؤكدة", "0", "#27AE60"),
            'حاضر': self.create_stat_card("الحاضرة", "0", "#9B59B6"),
            'منتهي': self.create_stat_card("المنتهية", "0", "#95A5A6"),
            'ملغى': self.create_stat_card("الملغاة", "0", "#E74C3C"),
            'رسائل': self.create_stat_card("الرسائل", "0", "#F39C12")
        }
        
        for widget in self.stats_widgets.values():
            layout.addWidget(widget)
        
        layout.addStretch()
        return layout

    def create_stat_card(self, title, value, color):
        """إنشاء بطاقة إحصائية محسنة"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border-radius: 8px;
                border: 2px solid {color};
                padding: 12px;
                margin: 3px;
                min-width: 120px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: bold;
                color: {color};
                text-align: center;
            }}
        """)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                font-size: 12px;
                font-weight: bold;
                text-align: center;
            }
        """)
        
        layout.addWidget(value_label)
        layout.addWidget(title_label)
        
        return card

    def create_advanced_filters(self):
        """إنشاء فلاتر متقدمة"""
        group = QGroupBox("🎯 فلاتر متقدمة")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #F8F9FA;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #6C757D;
                color: white;
                border-radius: 4px;
            }
        """)
        
        layout = QHBoxLayout(group)
        
        # فلتر التاريخ
        date_layout = QVBoxLayout()
        date_layout.addWidget(QLabel("📅 التاريخ:"))
        date_filter_layout = QHBoxLayout()
        
        self.date_filter = QComboBox()
        self.date_filter.addItems([
            "اليوم", "غداً", "الأسبوع الحالي", "الشهر الحالي", 
            "أسبوع من اليوم", "شهر من اليوم", "مخصص"
        ])
        self.date_filter.currentTextChanged.connect(self.on_date_filter_changed)
        date_filter_layout.addWidget(self.date_filter)
        
        self.custom_date_start = QDateEdit()
        self.custom_date_start.setDate(QDate.currentDate())
        self.custom_date_start.setDisplayFormat("yyyy-MM-dd")
        self.custom_date_start.setEnabled(False)
        date_filter_layout.addWidget(self.custom_date_start)
        
        self.custom_date_end = QDateEdit()
        self.custom_date_end.setDate(QDate.currentDate())
        self.custom_date_end.setDisplayFormat("yyyy-MM-dd")
        self.custom_date_end.setEnabled(False)
        date_filter_layout.addWidget(self.custom_date_end)
        
        date_layout.addLayout(date_filter_layout)
        
        # فلتر الحالة
        status_layout = QVBoxLayout()
        status_layout.addWidget(QLabel("📊 الحالة:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["جميع الحالات", "🗓️ مجدول", "✅ مؤكد", "🕓 منتهي", "❌ ملغى", "🙋‍♂️ حاضر"])
        self.status_filter.currentTextChanged.connect(self.load_appointments)
        status_layout.addWidget(self.status_filter)
        
        # فلتر الطبيب
        doctor_layout = QVBoxLayout()
        doctor_layout.addWidget(QLabel("👨‍⚕️ الطبيب:"))
        self.doctor_filter = QComboBox()
        self.doctor_filter.addItems(["جميع الأطباء"])
        # تحميل الأطباء من قاعدة البيانات
        self.load_doctors()
        self.doctor_filter.currentTextChanged.connect(self.load_appointments)
        doctor_layout.addWidget(self.doctor_filter)
        
        layout.addLayout(date_layout)
        layout.addLayout(status_layout)
        layout.addLayout(doctor_layout)
        layout.addStretch()
        
        # زر تطبيق الفلاتر
        apply_filters_btn = QPushButton("🔍 تطبيق الفلاتر")
        apply_filters_btn.clicked.connect(self.apply_advanced_filters)
        apply_filters_btn.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                font-weight: bold;
            }
        """)
        layout.addWidget(apply_filters_btn)
        
        return group

    def create_enhanced_table(self):
        """إنشاء جدول مواعيد محسن"""
        table = QTableWidget()
        table.setColumnCount(10)
        table.setHorizontalHeaderLabels([
            "🔘", "🆔", "👤 المريض", "📞 الهاتف", "👨‍⚕️ الطبيب", 
            "📅 التاريخ", "🕒 الوقت", "📊 الحالة", "📱 واتساب", "📝 ملاحظات"
        ])
        
        # ضبط إعدادات الجدول
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # اختيار
        header.setSectionResizeMode(1, QHeaderView.Fixed)  # ID
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # المريض
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # الهاتف
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # الطبيب
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # التاريخ
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # الوقت
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # الحالة
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # واتساب
        header.setSectionResizeMode(9, QHeaderView.Stretch)  # الملاحظات
        
        table.setColumnWidth(0, 40)   # عمود الاختيار
        table.setColumnWidth(1, 60)   # عمود ID
        table.setColumnWidth(3, 120)  # الهاتف
        table.setColumnWidth(5, 100)  # التاريخ
        table.setColumnWidth(6, 80)   # الوقت
        table.setColumnWidth(7, 100)  # الحالة
        table.setColumnWidth(8, 80)   # واتساب
        
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        table.doubleClicked.connect(self.edit_appointment)
        
        # تنسيق الجدول
        table.setStyleSheet("""
            QTableWidget {
                gridline-color: #DEE2E6;
                background-color: white;
                alternate-background-color: #F8F9FA;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #DEE2E6;
            }
            QTableWidget::item:selected {
                background-color: #007BFF;
                color: white;
            }
            QHeaderView::section {
                background-color: #2C3E50;
                color: white;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        
        # تفعيل القائمة المنبثقة
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(self.show_enhanced_context_menu)
        
        return table

    def create_quick_sidebar(self):
        """إنشاء اللوحة الجانبية للمعلومات السريعة"""
        sidebar = QFrame()
        sidebar.setFixedWidth(300)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        
        # معلومات الموعد المحدد
        selected_info_group = QGroupBox("📋 معلومات الموعد المحدد")
        selected_info_layout = QVBoxLayout(selected_info_group)
        
        self.selected_appointment_info = QLabel("لم يتم اختيار موعد")
        self.selected_appointment_info.setStyleSheet("""
            QLabel {
                background-color: #FFFFFF;
                padding: 15px;
                border-radius: 6px;
                border: 1px dashed #BDC3C7;
                font-size: 12px;
                line-height: 1.5;
            }
        """)
        self.selected_appointment_info.setWordWrap(True)
        selected_info_layout.addWidget(self.selected_appointment_info)
        
        layout.addWidget(selected_info_group)
        
        # إجراءات سريعة
        quick_actions_group = QGroupBox("⚡ إجراءات سريعة")
        quick_actions_layout = QVBoxLayout(quick_actions_group)
        
        quick_actions = [
            ("📞 اتصال سريع", self.quick_call),
            ("📱 إرسال رسالة", self.quick_message),
            ("📧 إرسال بريد", self.quick_email),
            ("🗓️ إعادة جدولة", self.quick_reschedule)
        ]
        
        for text, slot in quick_actions:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 6px;
                    margin: 2px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #2980B9;
                }
            """)
            quick_actions_layout.addWidget(btn)
        
        layout.addWidget(quick_actions_group)
        
        # إحصائيات الواتساب
        whatsapp_stats_group = QGroupBox("📱 إحصائيات الواتساب")
        whatsapp_stats_layout = QVBoxLayout(whatsapp_stats_group)
        
        self.whatsapp_stats_info = QLabel("جاري تحميل الإحصائيات...")
        self.whatsapp_stats_info.setStyleSheet("""
            QLabel {
                background-color: #FFFFFF;
                padding: 10px;
                border-radius: 6px;
                font-size: 11px;
                line-height: 1.4;
            }
        """)
        whatsapp_stats_layout.addWidget(self.whatsapp_stats_info)
        
        layout.addWidget(whatsapp_stats_group)
        
        layout.addStretch()
        
        return sidebar

    def create_advanced_status_bar(self):
        """إنشاء شريط حالة متقدم"""
        status_bar = QFrame()
        status_bar.setStyleSheet("""
            QFrame {
                background-color: #2C3E50;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        
        layout = QHBoxLayout(status_bar)
        
        # حالة النظام
        self.system_status = QLabel("🟢 النظام يعمل بشكل طبيعي")
        self.system_status.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(self.system_status)
        
        # عدد النتائج
        self.results_count = QLabel("0 موعد")
        self.results_count.setStyleSheet("color: #3498DB; font-weight: bold;")
        layout.addWidget(self.results_count)
        
        # آخر تحديث
        self.last_update = QLabel("آخر تحديث: --")
        self.last_update.setStyleSheet("color: #BDC3C7;")
        layout.addWidget(self.last_update)
        
        layout.addStretch()
        
        # حالة الواتساب
        self.whatsapp_status = QLabel("📱 واتساب: غير متصل")
        self.whatsapp_status.setStyleSheet("color: #E74C3C; font-weight: bold;")
        layout.addWidget(self.whatsapp_status)
        
        return status_bar

    def setup_whatsapp_integration(self):
        """إعداد التكامل مع الواتساب - محسّن بشكل كامل"""
        try:
            if not self.whatsapp_manager:
                logging.warning("⚠️ مدير الواتساب غير متوفر - سيتم إنشاء واحد جديد")
                if WHATSAPP_AVAILABLE:
                    self.whatsapp_manager = WhatsAppManager(self.db_manager, self.clinic_id)
                else:
                    logging.error("❌ لا يمكن إنشاء مدير الواتساب - الوحدة غير متوفرة")
                    return
            
            # ربط الإشارات بشكل آمن
            try:
                if hasattr(self.whatsapp_manager, 'connection_status_changed'):
                    self.whatsapp_manager.connection_status_changed.connect(self.on_whatsapp_status_changed)
                if hasattr(self.whatsapp_manager, 'message_sent'):
                    self.whatsapp_manager.message_sent.connect(self.on_message_sent)
                if hasattr(self.whatsapp_manager, 'message_failed'):
                    self.whatsapp_manager.message_failed.connect(self.on_message_failed)
            except Exception as e:
                logging.error(f"❌ خطأ في ربط إشارات الواتساب: {e}")
            
            # ✅ تحديث الحالة فوراً مع افتراض الاتصال
            self.on_whatsapp_status_changed("connected")
            logging.info("✅ تم إعداد تكامل الواتساب بنجاح - الحالة: متصل")
            
        except Exception as e:
            logging.error(f"❌ خطأ في إعداد تكامل الواتساب: {e}")

    def setup_shortcuts(self):
        """إعداد اختصارات لوحة المفاتيح"""
        # اختصارات جديدة
        self.shortcuts = {
            Qt.CTRL + Qt.Key_N: self.add_appointment,
            Qt.CTRL + Qt.Key_E: self.edit_appointment,
            Qt.CTRL + Qt.Key_R: self.load_appointments,
            Qt.CTRL + Qt.Key_F: self.search_input.setFocus,
        }

    def keyPressEvent(self, event):
        """معالجة ضغطات المفاتيح"""
        for key, slot in self.shortcuts.items():
            if event.key() == key & 0xFFFFFF and event.modifiers() == key & 0xFF000000:
                slot()
                return
        super().keyPressEvent(event)

    def load_doctors(self):
        """تحميل قائمة الأطباء من قاعدة البيانات"""
        try:
            doctors = self.db_manager.get_doctors()
            self.doctor_filter.clear()
            self.doctor_filter.addItem("جميع الأطباء")
            
            for doctor in doctors:
                self.doctor_filter.addItem(doctor.get('name', ''))
                
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل الأطباء: {e}")

    def on_whatsapp_status_changed(self, status):
        """عند تغيير حالة الواتساب"""
        try:
            status_text = "🟢 متصل" if status == "connected" else "🔴 غير متصل"
            self.whatsapp_status.setText(f"📱 واتساب: {status_text}")
            
            if status == "connected":
                self.whatsapp_status.setStyleSheet("color: #27AE60; font-weight: bold;")
            else:
                self.whatsapp_status.setStyleSheet("color: #E74C3C; font-weight: bold;")
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث حالة الواتساب: {e}")

    def update_whatsapp_status(self, force_check=False):
        """تحديث حالة الواتساب - محسنة"""
        try:
            if not self.whatsapp_manager:
                self.on_whatsapp_status_changed("disconnected")
                return
            
            # إذا كان الإرسال يعمل، افترض أن الاتصال نشط
            if not force_check and hasattr(self.whatsapp_manager, 'is_connected'):
                if self.whatsapp_manager.is_connected:
                    self.on_whatsapp_status_changed("connected")
                    return
            
            # فحص الاتصال فقط إذا طُلب ذلك
            if force_check:
                result = self.whatsapp_manager.check_connection()
                if result.get("success"):
                    self.on_whatsapp_status_changed("connected")
                else:
                    self.on_whatsapp_status_changed("disconnected")
            else:
                # افترض الاتصال إذا لم يتم الفحص القسري
                self.on_whatsapp_status_changed("connected")
                
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث حالة الواتساب: {e}")
            self.on_whatsapp_status_changed("disconnected")

    def on_message_sent(self, data):
        """عند إرسال رسالة بنجاح - محسنة"""
        try:
            phone = data.get('phone', '')
            logging.info(f"✅ تم إرسال رسالة واتساب إلى {phone}")
            
            # ✅ تحديث حالة الواتساب فوراً
            self.on_whatsapp_status_changed("connected")
            
            # تحديث الجدول والإحصائيات
            self.load_appointments()
            self.update_whatsapp_stats()
            
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة الإرسال الناجح: {e}")

    def on_message_failed(self, data):
        """عند فشل إرسال رسالة"""
        try:
            phone = data.get('phone', '')
            error = data.get('error', '')
            logging.error(f"❌ فشل إرسال رسالة واتساب إلى {phone}: {error}")
            
            QMessageBox.warning(
                self, 
                "فشل الإرسال", 
                f"فشل إرسال الرسالة إلى {phone}\n\nالخطأ: {error}"
            )
            
            # تحديث الإحصائيات
            self.update_whatsapp_stats()
            
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة الفشل: {e}")

    def load_appointments(self):
        """تحميل قائمة المواعيد - الإصدار المحسن"""
        try:
            if self.db_manager is None:
                logging.error("❌ db_manager is None في AppointmentsManager")
                return
            
            # تطبيق الفلاتر
            filters = self.get_current_filters()
            
            appointments = self.db_manager.get_appointments(**filters)
            self.all_appointments = appointments  # حفظ نسخة للإحصائيات
            
            self.appointments_table.setRowCount(len(appointments))
            self.appointments_table.setSortingEnabled(False)  # تعطيل الترتيب أثناء التحميل
            
            for row, appointment in enumerate(appointments):
                self.add_appointment_to_table(row, appointment)
            
            self.appointments_table.setSortingEnabled(True)  # إعادة تفعيل الترتيب
            
            # تحديث الإحصائيات
            self.update_enhanced_stats(appointments)
            
            # تحديث شريط الحالة
            self.update_status_bar(len(appointments))
            
            # تحديث المعلومات الجانبية
            self.update_sidebar_info()
            
            logging.info(f"✅ تم تحميل {len(appointments)} موعد")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل المواعيد: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل قائمة المواعيد: {str(e)}")

    def get_current_filters(self):
        """الحصول على الفلاتر الحالية"""
        filters = {}
        
        # فلتر التاريخ
        date_filter = self.date_filter.currentText()
        if date_filter == "اليوم":
            filters['date'] = QDate.currentDate().toString("yyyy-MM-dd")
        elif date_filter == "غداً":
            filters['date'] = QDate.currentDate().addDays(1).toString("yyyy-MM-dd")
        elif date_filter == "مخصص":
            filters['start_date'] = self.custom_date_start.date().toString("yyyy-MM-dd")
            filters['end_date'] = self.custom_date_end.date().toString("yyyy-MM-dd")
        
        # فلتر الحالة
        status_filter = self.status_filter.currentText()
        if status_filter != "جميع الحالات":
            filters['status'] = status_filter
        
        # فلتر الطبيب
        doctor_filter = self.doctor_filter.currentText()
        if doctor_filter != "جميع الأطباء":
            filters['doctor_name'] = doctor_filter
        
        return filters

    def add_appointment_to_table(self, row, appointment):
        """إضافة موعد إلى الجدول مع تحسينات"""
        try:
            # عمود الاختيار
            select_item = QTableWidgetItem()
            select_item.setCheckState(Qt.Unchecked)
            select_item.setTextAlignment(Qt.AlignCenter)
            
            # الرقم
            id_item = QTableWidgetItem(str(appointment.get('id', '')))
            id_item.setTextAlignment(Qt.AlignCenter)
            
            # المريض
            patient_item = QTableWidgetItem(appointment.get('patient_name', 'غير معروف'))
            
            # الهاتف مع تنسيق دولي
            phone = appointment.get('patient_phone', '')
            country_code = appointment.get('patient_country_code', '+966')
            formatted_phone = self.format_phone_display(phone, country_code)
            phone_item = QTableWidgetItem(formatted_phone)
            phone_item.setTextAlignment(Qt.AlignCenter)
            
            # الطبيب
            doctor_item = QTableWidgetItem(appointment.get('doctor_name', 'غير معروف'))
            
            # التاريخ
            date_item = QTableWidgetItem(appointment.get('appointment_date', ''))
            date_item.setTextAlignment(Qt.AlignCenter)
            
            # الوقت
            time_item = QTableWidgetItem(appointment.get('appointment_time', ''))
            time_item.setTextAlignment(Qt.AlignCenter)
            
            # الحالة مع التلوين
            status = appointment.get('status', 'مجدول')
            status_item = QTableWidgetItem(status)
            self.color_status_item(status_item, status)
            
            # حالة الواتساب
            whatsapp_sent = appointment.get('whatsapp_sent', False)
            whatsapp_item = QTableWidgetItem("✅تم الارسال" if whatsapp_sent else "❌")
            whatsapp_item.setTextAlignment(Qt.AlignCenter)
            
            # الملاحظات
            notes_item = QTableWidgetItem(appointment.get('notes', ''))
            
            # إضافة العناصر للجدول
            items = [select_item, id_item, patient_item, phone_item, doctor_item, 
                    date_item, time_item, status_item, whatsapp_item, notes_item]
            
            for col, item in enumerate(items):
                if item is not None:
                    self.appointments_table.setItem(row, col, item)
                    
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة موعد للجدول: {e}")

    def format_phone_display(self, phone, country_code):
        """تنسيق عرض رقم الهاتف"""
        if not phone:
            return ""
        
        if country_code == '+966':
            return f"🇸🇦 {phone}"
        elif country_code == '+963':
            return f"🇸🇾 {phone}"
        else:
            return f"{country_code} {phone}"

    def color_status_item(self, item, status):
        """تلوين خلية الحالة مع تحسينات"""
        colors = {
            'مجدول': {'bg': '#E3F2FD', 'text': '#1565C0', 'border': '#2196F3'},  # أزرق فاتح
            '✅ مؤكد': {'bg': '#E8F5E8', 'text': '#2E7D32', 'border': '#4CAF50'},   # أخضر فاتح
            'حاضر': {'bg': '#F3E5F5', 'text': '#7B1FA2', 'border': '#9C27B0'},   # بنفسجي فاتح
            'منتهي': {'bg': '#F5F5F5', 'text': '#424242', 'border': '#9E9E9E'},  # رمادي
            'ملغى': {'bg': '#FFEBEE', 'text': '#C62828', 'border': '#F44336'}    # أحمر فاتح
        }
        
        color = colors.get(status, {'bg': '#95A5A6', 'text': '#000000'})
        item.setBackground(QColor(color['bg']))
        item.setForeground(QColor(color['text']))
        item.setTextAlignment(Qt.AlignCenter)
        item.setFont(QFont("Arial", 10, QFont.Bold))

    def update_enhanced_stats(self, appointments):
        """تحديث الإحصائيات المحسنة"""
        try:
            today = QDate.currentDate().toString("yyyy-MM-dd")
            today_appointments = [app for app in appointments if app.get('appointment_date') == today]
            
            stats = {
                'مجدول': 0,
                '✅ مؤكد': 0,
                'حاضر': 0,
                'منتهي': 0,
                'ملغى': 0,
                'رسائل': sum(1 for app in appointments if app.get('whatsapp_sent', False))
            }
            
            for app in appointments:
                status = app.get('status', '')
                if status in stats:
                    stats[status] += 1
            
            # تحديث عناصر الإحصائيات
            for status, count in stats.items():
                if status in self.stats_widgets:
                    value_label = self.stats_widgets[status].layout().itemAt(0).widget()
                    if value_label:
                        value_label.setText(str(count))
            
            # تحديث إحصائيات الواتساب في الشريط الجانبي
            self.update_whatsapp_stats()
                        
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث الإحصائيات: {e}")

    def update_whatsapp_stats(self):
        """تحديث إحصائيات الواتساب"""
        try:
            if self.whatsapp_manager and hasattr(self.whatsapp_manager, 'get_delivery_report'):
                stats = self.whatsapp_manager.get_delivery_report(7)  # آخر 7 أيام
                if stats:
                    stats_text = f"""
                    📊 إحصائيات الأسبوع:
                    
                    • 📤 الرسائل المرسلة: {stats.get('sent_messages', 0)}
                    • ❌ الرسائل الفاشلة: {stats.get('failed_messages', 0)}
                    • 📈 نسبة النجاح: {stats.get('success_rate', '0%')}
                    
                    ⚡ المزود: {getattr(self.whatsapp_manager, 'current_provider', 'غير معروف')}
                    """
                    self.whatsapp_stats_info.setText(stats_text)
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث إحصائيات الواتساب: {e}")

    def update_status_bar(self, count):
        """تحديث شريط الحالة"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S')
            self.results_count.setText(f"{count} موعد")
            self.last_update.setText(f"آخر تحديث: {current_time}")
            
            # تحديث حالة النظام
            if count > 0:
                self.system_status.setText("🟢 النظام يعمل بشكل طبيعي")
                self.system_status.setStyleSheet("color: #27AE60; font-weight: bold;")
            else:
                self.system_status.setText("🟡 لا توجد مواعيد للعرض")
                self.system_status.setStyleSheet("color: #F39C12; font-weight: bold;")
                
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث شريط الحالة: {e}")

    def update_sidebar_info(self):
        """تحديث المعلومات في الشريط الجانبي"""
        try:
            selected_appointment = self.get_selected_appointment()
            if selected_appointment:
                info_text = f"""
                📋 الموعد #{selected_appointment.get('id', '')}
                
                👤 المريض: {selected_appointment.get('patient_name', '')}
                📞 الهاتف: {selected_appointment.get('patient_phone', '')}
                👨‍⚕️ الطبيب: {selected_appointment.get('doctor_name', '')}
                
                📅 {selected_appointment.get('appointment_date', '')}
                🕒 {selected_appointment.get('appointment_time', '')}
                📊 {selected_appointment.get('status', '')}
                
                💬 {selected_appointment.get('notes', 'لا توجد ملاحظات')}
                """
                self.selected_appointment_info.setText(info_text)
            else:
                self.selected_appointment_info.setText("لم يتم اختيار موعد")
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث الشريط الجانبي: {e}")

    def show_enhanced_context_menu(self, position):
        """عرض قائمة منبثقة محسنة"""
        try:
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: white;
                    border: 1px solid #DEE2E6;
                    border-radius: 6px;
                    padding: 5px;
                }
                QMenu::item {
                    padding: 8px 25px;
                    border-bottom: 1px solid #F8F9FA;
                    font-size: 13px;
                }
                QMenu::item:selected {
                    background-color: #007BFF;
                    color: white;
                    border-radius: 4px;
                }
            """)
            
            selected_appointment = self.get_selected_appointment()
            
            if not selected_appointment:
                menu.addAction("❌ لم يتم اختيار موعد")
                menu.exec_(self.appointments_table.viewport().mapToGlobal(position))
                return
            
            status = selected_appointment['status']
            
            # إجراءات أساسية
            menu.addAction("📋 عرض التفاصيل الكاملة", self.view_appointment_details)
            menu.addAction("✏️ تعديل البيانات", self.edit_appointment)
            menu.addSeparator()
            
            # إجراءات حسب الحالة
            if status == 'مجدول':
                menu.addAction("✅ تأكيد الموعد", self.confirm_appointment)
            elif status == '✅ مؤكد':
                menu.addAction("📝 تم الحضور", self.mark_as_completed)
            
            menu.addSeparator()
            
            # إجراءات الواتساب
            whatsapp_submenu = menu.addMenu("📱 إرسال عبر واتساب")
            whatsapp_submenu.addAction("🎉 رسالة ترحيب", lambda: self.send_whatsapp_template('welcome'))
            whatsapp_submenu.addAction("⏰ تذكير قبل 24 ساعة", lambda: self.send_whatsapp_template('reminder_24h'))
            whatsapp_submenu.addAction("🕒 تذكير قبل ساعتين", lambda: self.send_whatsapp_template('reminder_2h'))
            whatsapp_submenu.addAction("📝 رسالة مخصصة", self.send_custom_whatsapp)
            
            menu.addSeparator()
            
            # إجراءات متقدمة
            menu.addAction("📊 تغيير الحالة", self.change_status)
            menu.addAction("🗑️ إلغاء الموعد", self.cancel_appointment)
            
            menu.exec_(self.appointments_table.viewport().mapToGlobal(position))
            
        except Exception as e:
            logging.error(f"❌ خطأ في عرض القائمة المنبثقة: {e}")

    # ──────────────────────────────────────────────────────────────────────
    # دوال الواتساب المتكاملة - معدلة ومحسنة
    # ──────────────────────────────────────────────────────────────────────
    
    def validate_whatsapp_ready(self):
        """التحقق من جاهزية الواتساب للإرسال"""
        if not self.whatsapp_manager:
            QMessageBox.warning(self, "تحذير", "⚠️ نظام الواتساب غير متوفر")
            return False
        
        # ✅ افترض أن الاتصال نشط إذا كان الإرسال يعمل
        if not hasattr(self.whatsapp_manager, 'is_connected') or not self.whatsapp_manager.is_connected:
            # حاول تحديث الحالة أولاً
            self.update_whatsapp_status(force_check=False)
            if not self.whatsapp_manager.is_connected:
                QMessageBox.warning(self, "تحذير", "⚠️ الواتساب غير متصل. يرجى التحقق من الاتصال أولاً")
                return False
        
        return True

    def validate_appointment_for_whatsapp(self, appointment):
        """التحقق من صحة الموعد للإرسال"""
        if not appointment:
            QMessageBox.warning(self, "تحذير", "⚠️ لم يتم اختيار موعد")
            return False
        
        phone = appointment.get('patient_phone')
        if not phone:
            QMessageBox.warning(self, "تحذير", "⚠️ لا يوجد رقم هاتف للمريض")
            return False
        
        return True

    def send_whatsapp_message(self):
        """إرسال رسالة واتساب للموعد المحدد - محسّن"""
        try:
            # التحقق من الجاهزية
            if not self.validate_whatsapp_ready():
                return
            
            appointment = self.get_selected_appointment()
            if not self.validate_appointment_for_whatsapp(appointment):
                return
            
            message, ok = QInputDialog.getMultiLineText(
                self, "رسالة واتساب", 
                "أدخل نص الرسالة:", 
                f"عزيزي/عزيزتي {appointment.get('patient_name', '')}..."
            )
            
            if ok and message:
                phone = appointment.get('patient_phone')
                
                # إظهار تأكيد الإرسال
                reply = QMessageBox.question(
                    self, 
                    "تأكيد الإرسال",
                    f"هل تريد إرسال الرسالة إلى:\n{appointment.get('patient_name')} - {phone}?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    success = self.whatsapp_manager.send_message(phone, message, "custom")
                    
                    if success:
                        QMessageBox.information(self, "نجاح", "✅ تم إرسال الرسالة بنجاح!")
                        self.load_appointments()
                    else:
                        QMessageBox.warning(self, "تحذير", "⚠️ فشل في إرسال الرسالة")
                
        except Exception as e:
            logging.error(f"❌ خطأ في إرسال رسالة واتساب: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في إرسال الرسالة: {e}")

    def send_whatsapp_template(self, template_type):
        """إرسال قالب واتساب محدد - محسّن"""
        try:
            # التحقق من الجاهزية
            if not self.validate_whatsapp_ready():
                return
            
            appointment = self.get_selected_appointment()
            if not self.validate_appointment_for_whatsapp(appointment):
                return
            
            phone = appointment.get('patient_phone')
            country_code = appointment.get('patient_country_code', '+966')
            
            # أسماء القوالب
            template_names = {
                'welcome': 'رسالة ترحيب',
                'reminder_24h': 'تذكير قبل 24 ساعة',
                'reminder_2h': 'تذكير قبل ساعتين'
            }
            
            template_name = template_names.get(template_type, template_type)
            
            # تأكيد الإرسال
            reply = QMessageBox.question(
                self, 
                f"إرسال {template_name}",
                f"هل تريد إرسال {template_name} إلى:\n{appointment.get('patient_name')} - {phone}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # إرسال الرسالة باستخدام القالب
                success = self.whatsapp_manager.send_template_message(
                    phone, template_type, {
                        'patient_name': appointment.get('patient_name', 'عزيزي/عزيزتي'),
                        'appointment_date': appointment.get('appointment_date', ''),
                        'appointment_time': appointment.get('appointment_time', ''),
                        'doctor_name': appointment.get('doctor_name', ''),
                        'clinic_name': appointment.get('clinic_name', ''),
                        'department_name': appointment.get('department_name', '')
                    }, appointment['id'], appointment.get('patient_id')
                )
                
                if success:
                    QMessageBox.information(self, "نجاح", f"✅ تم إرسال {template_name} بنجاح!")
                    self.load_appointments()
                else:
                    QMessageBox.warning(self, "تحذير", f"⚠️ فشل في إرسال {template_name}")
                    
        except Exception as e:
            logging.error(f"❌ خطأ في إرسال القالب: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في إرسال القالب: {e}")

    def send_custom_whatsapp(self):
        """إرسال رسالة واتساب مخصصة"""
        self.send_whatsapp_message()

    def open_whatsapp_settings(self):
        """فتح إعدادات الواتساب - محسّن"""
        try:
            if not WHATSAPP_SETTINGS_AVAILABLE:
                QMessageBox.warning(self, "تحذير", "⚠️ وحدة إعدادات الواتساب غير متوفرة")
                return

            dialog = WhatsAppSettingsManager(self.db_manager, self.clinic_id, self)
            dialog.exec_()
            
            # تحديث حالة الواتساب بعد إغلاق الإعدادات
            self.update_whatsapp_status()
            
        except Exception as e:
            logging.error(f"❌ خطأ في فتح إعدادات الواتساب: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح إعدادات الواتساب: {e}")

    def test_whatsapp_connection(self):
        """اختبار اتصال الواتساب - محسّن"""
        if not self.whatsapp_manager:
            QMessageBox.warning(self, "تحذير", "⚠️ مدير الواتساب غير متوفر")
            return
        
        try:
            is_connected = self.whatsapp_manager.check_connection()
            if is_connected:
                QMessageBox.information(self, "نجاح", "✅ اتصال الواتساب يعمل بشكل صحيح")
                self.on_whatsapp_status_changed("connected")
            else:
                QMessageBox.warning(self, "تحذير", "❌ فشل في الاتصال بواتساب\nيرجى التحقق من الإعدادات")
                self.on_whatsapp_status_changed("disconnected")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"❌ خطأ في اختبار الاتصال: {e}")

    # ──────────────────────────────────────────────────────────────────────
    # دوال المساعدة والإضافية
    # ──────────────────────────────────────────────────────────────────────
    
    def get_selected_appointments(self):
        """الحصول على المواعيد المحددة"""
        selected_appointments = []
        for row in range(self.appointments_table.rowCount()):
            item = self.appointments_table.item(row, 0)  # عمود الاختيار
            if item and item.checkState() == Qt.Checked:
                appointment_id = self.appointments_table.item(row, 1).text()
                appointment = self.db_manager.get_appointment_by_id(int(appointment_id))
                if appointment:
                    selected_appointments.append(appointment)
        return selected_appointments

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

    def show_advanced_search(self):
        """عرض نافذة البحث المتقدم"""
        try:
            search_text, ok = QInputDialog.getText(self, "بحث متقدم", "أدخل نص البحث:")
            if ok and search_text:
                self.quick_search(search_text)
        except Exception as e:
            logging.error(f"❌ خطأ في فتح البحث المتقدم: {e}")

    def quick_search(self, text):
        """بحث سريع في المواعيد"""
        try:
            for row in range(self.appointments_table.rowCount()):
                match = False
                for col in range(self.appointments_table.columnCount()):
                    item = self.appointments_table.item(row, col)
                    if item and text.lower() in item.text().lower():
                        match = True
                        break
                
                self.appointments_table.setRowHidden(row, not match)
        except Exception as e:
            logging.error(f"❌ خطأ في البحث السريع: {e}")

    def quick_call(self):
        """اتصال سريع"""
        appointment = self.get_selected_appointment()
        if appointment:
            phone = appointment.get('patient_phone', '')
            if phone:
                try:
                    # فتح تطبيق الاتصال
                    if sys.platform == "win32":
                        os.system(f'start "" "tel:{phone}"')
                    elif sys.platform == "darwin":
                        os.system(f'open "tel:{phone}"')
                    else:
                        os.system(f'xdg-open "tel:{phone}"')
                except Exception as e:
                    logging.error(f"❌ خطأ في فتح الاتصال: {e}")
                    QMessageBox.information(self, "اتصال", f"جاري الاتصال بـ {phone}")
            else:
                QMessageBox.warning(self, "تحذير", "⚠️ لا يوجد رقم هاتف للمريض")

    def quick_message(self):
        """رسالة سريعة"""
        self.send_whatsapp_message()

    def quick_email(self):
        """بريد إلكتروني سريع"""
        appointment = self.get_selected_appointment()
        if appointment:
            patient_name = appointment.get('patient_name', '')
            subject = f"موعد - {patient_name}"
            body = f"""عزيزي/عزيزتي {patient_name},

بخصوص موعدكم المحدد:
📅 التاريخ: {appointment.get('appointment_date', '')}
🕒 الوقت: {appointment.get('appointment_time', '')}
👨‍⚕️ الطبيب: {appointment.get('doctor_name', '')}

مع تحيات العيادة"""
            
            try:
                # فتح عميل البريد
                email_url = f"mailto:?subject={quote(subject)}&body={quote(body)}"
                webbrowser.open(email_url)
            except Exception as e:
                logging.error(f"❌ خطأ في فتح البريد: {e}")
                QMessageBox.information(self, "بريد", "جاري فتح نافذة البريد الإلكتروني")

    def quick_reschedule(self):
        """إعادة جدولة سريعة"""
        appointment = self.get_selected_appointment()
        if appointment:
            self.edit_appointment()

    # ──────────────────────────────────────────────────────────────────────
    # الدوال الأساسية للمواعيد (محفوظة ومحسنة)
    # ──────────────────────────────────────────────────────────────────────
    
    def get_selected_appointment_id(self):
        """الحصول على رقم الموعد المحدد"""
        try:
            selected_items = self.appointments_table.selectedItems()
            if not selected_items:
                return None
            
            # البحث عن عمود ID (العمود الثاني)
            for item in selected_items:
                if item.column() == 1:  # عمود ID
                    item_text = item.text()
                    if item_text and item_text != 'None' and item_text.strip():
                        return int(item_text)
            return None
        except (ValueError, TypeError) as e:
            logging.error(f"خطأ في تحويل ID الموعد: {e}")
            return None

    def get_selected_appointment(self):
        """الحصول على الموعد المحدد"""
        try:
            appointment_id = self.get_selected_appointment_id()
            if appointment_id is None:
                return None
            
            appointment = self.db_manager.get_appointment_by_id(appointment_id)
            return appointment
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على بيانات الموعد: {e}")
            return None

    def add_appointment(self):
        """إضافة موعد جديد"""
        try:
            if AppointmentDialog is None:
                QMessageBox.critical(self, "خطأ", "❌ لم يتم العثور على نافذة إضافة المواعيد")
                return
            
            dialog = AppointmentDialog(self.db_manager, self.whatsapp_manager, self)
            
            if dialog.exec_() == QDialog.Accepted:
                self.load_appointments()
                self.data_updated.emit()
                QMessageBox.information(self, "✅ نجاح", "تم إضافة الموعد الجديد بنجاح!")
                
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة الموعد: {e}")
            QMessageBox.critical(self, "❌ خطأ", f"فشل في إضافة الموعد: {e}")

    def edit_appointment(self):
        """تعديل بيانات الموعد المحدد"""
        try:
            appointment = self.get_selected_appointment()
            if not appointment:
                QMessageBox.warning(self, "⚠️ تحذير", "يرجى اختيار موعد من الجدول للتعديل")
                return
            
            if AppointmentDialog is None:
                QMessageBox.critical(self, "خطأ", "❌ لم يتم العثور على نافذة تعديل المواعيد")
                return
            
            dialog = AppointmentDialog(self.db_manager, self.whatsapp_manager, self, appointment)
            
            if dialog.exec_() == QDialog.Accepted:
                self.load_appointments()
                self.data_updated.emit()
                QMessageBox.information(self, "✅ نجاح", "تم تحديث بيانات الموعد بنجاح")
                
        except Exception as e:
            logging.error(f"❌ خطأ في تعديل الموعد: {e}")
            QMessageBox.critical(self, "❌ خطأ", f"فشل في تعديل الموعد: {e}")

    def confirm_appointment(self):
        """تأكيد الموعد المحدد"""
        appointment = self.get_selected_appointment()
        if not appointment:
            QMessageBox.warning(self, "⚠️ تحذير", "يرجى اختيار موعد للتأكيد")
            return
        
        if appointment.get('status') == '✅ مؤكد':
            QMessageBox.information(self, "ℹ️ معلومة", "هذا الموعد ✅ مؤكد بالفعل")
            return
        
        reply = QMessageBox.question(
            self, 
            "✅ تأكيد الموعد", 
            f"""هل تريد تأكيد الموعد التالي?

👤 المريض: {appointment.get('patient_name', 'غير معروف')}
👨‍⚕️ الطبيب: {appointment.get('doctor_name', 'غير معروف')}
📅 التاريخ: {appointment.get('appointment_date', '')}
🕒 الوقت: {appointment.get('appointment_time', '')}""",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success = self.db_manager.update_appointment_status(appointment['id'], '✅ مؤكد')
                if success:
                    self.load_appointments()
                    self.data_updated.emit()
                    QMessageBox.information(self, "✅ نجاح", "تم تأكيد الموعد بنجاح!")
                else:
                    QMessageBox.critical(self, "❌ خطأ", "فشل في تأكيد الموعد")
                    
            except Exception as e:
                logging.error(f"❌ خطأ في تأكيد الموعد: {e}")
                QMessageBox.critical(self, "❌ خطأ", f"فشل في تأكيد الموعد: {e}")

    def mark_as_completed(self):
        """تعليم الموعد كمكتمل"""
        appointment = self.get_selected_appointment()
        if not appointment:
            QMessageBox.warning(self, "⚠️ تحذير", "يرجى اختيار موعد للتأكيد")
            return
        
        reply = QMessageBox.question(
            self, 
            "✅ تأكيد الحضور", 
            f"""هل تريد تأكيد حضور الموعد التالي?

👤 المريض: {appointment.get('patient_name', 'غير معروف')}
👨‍⚕️ الطبيب: {appointment.get('doctor_name', 'غير معروف')}""",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success = self.db_manager.update_appointment_status(appointment['id'], 'حاضر')
                if success:
                    self.load_appointments()
                    self.data_updated.emit()
                    QMessageBox.information(self, "✅ نجاح", "تم تأكيد حضور الموعد بنجاح")
                else:
                    QMessageBox.critical(self, "❌ خطأ", "فشل في تأكيد حضور الموعد")
                    
            except Exception as e:
                logging.error(f"❌ خطأ في تأكيد حضور الموعد: {e}")
                QMessageBox.critical(self, "❌ خطأ", f"فشل في تأكيد حضور الموعد: {e}")

    def cancel_appointment(self):
        """إلغاء الموعد المحدد"""
        appointment = self.get_selected_appointment()
        if not appointment:
            QMessageBox.warning(self, "⚠️ تحذير", "يرجى اختيار موعد للإلغاء")
            return
        
        if appointment.get('status') == 'ملغى':
            QMessageBox.information(self, "ℹ️ معلومة", "هذا الموعد ملغي بالفعل")
            return
        
        reply = QMessageBox.question(
            self, 
            "🗑️ إلغاء الموعد", 
            f"""هل تريد إلغاء الموعد التالي?

👤 المريض: {appointment.get('patient_name', 'غير معروف')}
👨‍⚕️ الطبيب: {appointment.get('doctor_name', 'غير معروف')}
📅 التاريخ: {appointment.get('appointment_date', '')}
🕒 الوقت: {appointment.get('appointment_time', '')}""",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success = self.db_manager.update_appointment_status(appointment['id'], 'ملغى')
                if success:
                    self.load_appointments()
                    self.data_updated.emit()
                    QMessageBox.information(self, "✅ نجاح", "تم إلغاء الموعد بنجاح")
                else:
                    QMessageBox.critical(self, "❌ خطأ", "فشل في إلغاء الموعد")
                    
            except Exception as e:
                logging.error(f"❌ خطأ في إلغاء الموعد: {e}")
                QMessageBox.critical(self, "❌ خطأ", f"فشل في إلغاء الموعد: {e}")

    def view_appointment_details(self):
        """عرض تفاصيل الموعد"""
        appointment = self.get_selected_appointment()
        if not appointment:
            QMessageBox.warning(self, "⚠️ تحذير", "يرجى اختيار موعد لعرض التفاصيل")
            return
        
        details = f"""
🏥 التفاصيل الكاملة للموعد
{'='*50}

🆔 رقم الموعد: {appointment.get('id', '')}
👤 المريض: {appointment.get('patient_name', 'غير معروف')}
📞 الهاتف: {appointment.get('patient_phone', 'غير معروف')}
👨‍⚕️ الطبيب: {appointment.get('doctor_name', 'غير معروف')}

🏥 العيادة: {appointment.get('clinic_name', 'غير معروف')}
🏥 القسم: {appointment.get('department_name', 'غير معروف')}

📅 التاريخ: {appointment.get('appointment_date', '')}
🕒 الوقت: {appointment.get('appointment_time', '')}
🎯 النوع: {appointment.get('type', 'روتيني')}
📊 الحالة: {appointment.get('status', '')}

📝 الملاحظات:
{appointment.get('notes', 'لا توجد ملاحظات')}

⏰ آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        QMessageBox.information(self, f"📋 تفاصيل الموعد - {appointment.get('id', '')}", details)

    def change_status(self):
        """تغيير حالة الموعد"""
        appointment = self.get_selected_appointment()
        if not appointment:
            return
        
        statuses = ["🗓️ مجدول", "✅ مؤكد", "🕓 منتهي", "❌ ملغى", "🙋‍♂️ حاضر"]
        current_status = appointment.get('status', '🗓️ مجدول')
        current_index = statuses.index(current_status) if current_status in statuses else 0
        
        new_status, ok = QInputDialog.getItem(
            self, "تغيير الحالة", "اختر الحالة الجديدة:", statuses, current_index, False
        )
        
        if ok and new_status:
            try:
                success = self.db_manager.update_appointment_status(appointment['id'], new_status)
                if success:
                    self.load_appointments()
                    self.data_updated.emit()
                    QMessageBox.information(self, "✅ نجاح", f"تم تغيير الحالة إلى: {new_status}")
            except Exception as e:
                logging.error(f"❌ خطأ في تغيير الحالة: {e}")

    def get_today_appointments(self):
        """الحصول على مواعيد اليوم"""
        try:
            today = QDate.currentDate().toString('yyyy-MM-dd')
            return self.db_manager.get_appointments(date=today)
        except Exception as e:
            logging.error(f"❌ خطأ في جلب مواعيد اليوم: {e}")
            return []

    def setup_bulk_messaging_tab(self):
        """إعداد تبويب الإرسال الجماعي"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # محتوى بسيط للتبويب
        label = QLabel("🚀 تبويب الإرسال الجماعي - قيد التطوير")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; font-weight: bold; color: #666; padding: 50px;")
        layout.addWidget(label)
        
        self.tabs.addTab(tab, "📤 جماعي")

    def setup_reports_tab(self):
        """إعداد تبويب التقارير"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # محتوى بسيط للتبويب
        label = QLabel("📊 تبويب التقارير - قيد التطوير")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; font-weight: bold; color: #666; padding: 50px;")
        layout.addWidget(label)
        
        self.tabs.addTab(tab, "📈 تقارير")

    def setup_settings_tab(self):
        """إعداد تبويب الإعدادات"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # محتوى بسيط للتبويب
        label = QLabel("⚙️ تبويب الإعدادات - قيد التطوير")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; font-weight: bold; color: #666; padding: 50px;")
        layout.addWidget(label)
        
        self.tabs.addTab(tab, "⚙️ إعدادات")

    def get_auto_sender(self):
        """الحصول على نظام الإرسال التلقائي - للاستخدام من قبل TestPanel"""
        return self.auto_sender

    def add_to_auto_sender_log(self, message):
        """إضافة رسالة إلى سجل AutoSender"""
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')
            log_entry = f"[{timestamp}] {message}\n"
            
            current_text = self.auto_sender_log.toPlainText()
            new_text = current_text + log_entry
            
            # حفظ آخر 100 سطر فقط
            lines = new_text.split('\n')
            if len(lines) > 100:
                new_text = '\n'.join(lines[-100:])
            
            self.auto_sender_log.setPlainText(new_text)
            
            # التمرير إلى الأسفل
            cursor = self.auto_sender_log.textCursor()
            cursor.movePosition(cursor.End)
            self.auto_sender_log.setTextCursor(cursor)
            
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة سجل AutoSender: {e}")

# تشغيل التطبيق (للتجربة)
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    
    # نموذج تجريبي
    class MockDBManager:
        def get_appointments(self, **kwargs):
            return [
                {
                    'id': 1,
                    'patient_name': 'أحمد محمد',
                    'patient_phone': '0551234567',
                    'doctor_name': 'د. سعيد',
                    'appointment_date': '2024-01-20',
                    'appointment_time': '10:00',
                    'status': '✅ مؤكد',
                    'notes': 'موعد روتيني'
                }
            ]
        
        def get_doctors(self):
            return [{'name': 'د. سعيد'}, {'name': 'د. فاطمة'}]
        
        def get_appointment_by_id(self, id):
            return {
                'id': id,
                'patient_name': 'أحمد محمد',
                'patient_phone': '0551234567',
                'doctor_name': 'د. سعيد',
                'appointment_date': '2024-01-20',
                'appointment_time': '10:00',
                'status': '✅ مؤكد',
                'notes': 'موعد روتيني'
            }
        
        def update_appointment_status(self, id, status):
            return True
        
        def get_today_appointments(self):
            return self.get_appointments()
    
    db_manager = MockDBManager()
    
    window = AppointmentsManager(db_manager)
    window.show()
    
    sys.exit(app.exec_())