# -*- coding: utf-8 -*-
import sqlite3
import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QGroupBox, QPushButton, QLineEdit, 
                             QComboBox, QCheckBox, QSpinBox, QMessageBox,
                             QTabWidget, QFormLayout, QTextEdit, QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class SettingsManager(QWidget):
    """مدير الإعدادات العامة للنظام - الإصدار المطور"""
    
    def __init__(self, db_manager, clinic_id=1):
        super().__init__()
        self.db_manager = db_manager
        self.clinic_id = clinic_id
        
        # إنشاء جدول الإعدادات إذا لم يكن موجوداً
        self.create_settings_table()
        
        # تهيئة جميع العناصر
        self.init_ui_elements()
        self.setup_ui()
        self.load_settings()
        
    def create_settings_table(self):
        """إنشاء جدول الإعدادات إذا لم يكن موجوداً"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clinic_id INTEGER NOT NULL,
                    setting_key TEXT NOT NULL,
                    setting_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(clinic_id, setting_key)
                )
            ''')
            
            conn.commit()
            conn.close()
            logging.info("✅ تم إنشاء/تحديث جداول الإعدادات بنجاح")
            
        except Exception as e:
            logging.error(f"❌ خطأ في إنشاء جدول الإعدادات: {e}")

    def init_ui_elements(self):
        """تهيئة جميع عناصر الواجهة مسبقاً"""
        # معلومات العيادة
        self.clinic_name = None
        self.clinic_type = None
        self.main_phone = None
        self.clinic_address = None
        self.clinic_email = None
        
        # أوقات العمل
        self.work_start = None
        self.work_end = None
        self.appointment_duration = None
        
        # التذكيرات الأساسية
        self.reminder_24h = None
        self.reminder_2h = None
        
        # النظام
        self.language = None
        self.timezone = None
        self.auto_backup = None
        self.backup_interval = None
        self.auto_logout = None
        self.logout_time = None
        
        # الإيميل
        self.smtp_server = None
        self.smtp_port = None
        self.smtp_username = None
        self.smtp_password = None
        self.smtp_from_name = None
        self.smtp_use_tls = None
        
        # أيام العمل
        self.days_checkboxes = {}
        
    def setup_ui(self):
        """إعداد واجهة الإعدادات العامة"""
        try:
            main_layout = QVBoxLayout(self)
            
            # عنوان الإعدادات
            title = QLabel("⚙️ الإعدادات العامة للنظام")
            title.setFont(QFont("Arial", 16, QFont.Bold))
            title.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(title)
            
            # تبويبات الإعدادات
            self.tabs = QTabWidget()
            
            # إعداد جميع التبويبات
            self.setup_basic_info_tab()
            self.setup_working_hours_tab()
            self.setup_reminders_tab()
            self.setup_email_tab()  # 🆕 تبويب الإيميل الجديد
            self.setup_system_tab()
            
            main_layout.addWidget(self.tabs)
            
            # أزرار الحفظ والإجراءات
            buttons_layout = QHBoxLayout()
            
            save_btn = QPushButton("💾 حفظ الإعدادات")
            save_btn.clicked.connect(self.save_all_settings)
            buttons_layout.addWidget(save_btn)
            
            reset_btn = QPushButton("🔄 استعادة الإفتراضيات")
            reset_btn.clicked.connect(self.reset_defaults)
            buttons_layout.addWidget(reset_btn)
            
            # زر فتح إعدادات الواتساب المتقدمة
            whatsapp_btn = QPushButton("📱 إعدادات الواتساب المتقدمة")
            whatsapp_btn.clicked.connect(self.open_whatsapp_settings)
            buttons_layout.addWidget(whatsapp_btn)
            
            buttons_layout.addStretch()
            main_layout.addLayout(buttons_layout)
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الواجهة", f"فشل في إعداد الواجهة: {e}")
        
    def setup_basic_info_tab(self):
        """إعداد تبويب المعلومات الأساسية"""
        try:
            tab = QWidget()
            layout = QFormLayout(tab)
            
            # معلومات العيادة
            info_group = QGroupBox("🏥 معلومات العيادة/المستشفى")
            info_layout = QFormLayout(info_group)
            
            self.clinic_name = QLineEdit()
            self.clinic_name.setPlaceholderText("اسم العيادة أو المستشفى")
            info_layout.addRow("اسم المؤسسة:", self.clinic_name)
            
            self.clinic_type = QComboBox()
            self.clinic_type.addItems(["عيادة", "مستشفى", "مركز طبي", "مستوصف"])
            info_layout.addRow("نوع المؤسسة:", self.clinic_type)
            
            self.main_phone = QLineEdit()
            self.main_phone.setPlaceholderText("+963900000000")
            info_layout.addRow("الهاتف الرئيسي:", self.main_phone)
            
            self.clinic_address = QTextEdit()
            self.clinic_address.setMaximumHeight(80)
            self.clinic_address.setPlaceholderText("عنوان المؤسسة بالتفصيل")
            info_layout.addRow("العنوان:", self.clinic_address)
            
            self.clinic_email = QLineEdit()
            self.clinic_email.setPlaceholderText("email@example.com")
            info_layout.addRow("البريد الإلكتروني:", self.clinic_email)
            
            layout.addWidget(info_group)
            
            self.tabs.addTab(tab, "🏥 المعلومات الأساسية")
            
        except Exception as e:
            logging.error(f"خطأ في تبويب المعلومات الأساسية: {e}")
            
    def setup_working_hours_tab(self):
        """إعداد تبويب أوقات العمل"""
        try:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            
            # أوقات العمل
            hours_group = QGroupBox("🕒 أوقات العمل")
            hours_layout = QGridLayout(hours_group)
            
            hours_layout.addWidget(QLabel("بداية العمل:"), 0, 0)
            self.work_start = QComboBox()
            self.work_start.addItems([f"{h:02d}:00" for h in range(6, 12)])
            hours_layout.addWidget(self.work_start, 0, 1)
            
            hours_layout.addWidget(QLabel("نهاية العمل:"), 1, 0)
            self.work_end = QComboBox()
            self.work_end.addItems([f"{h:02d}:00" for h in range(12, 24)])
            hours_layout.addWidget(self.work_end, 1, 1)
            
            hours_layout.addWidget(QLabel("مدة الموعد (دقائق):"), 2, 0)
            self.appointment_duration = QSpinBox()
            self.appointment_duration.setRange(15, 120)
            self.appointment_duration.setValue(30)
            self.appointment_duration.setSuffix(" دقيقة")
            hours_layout.addWidget(self.appointment_duration, 2, 1)
            
            layout.addWidget(hours_group)
            
            # أيام العمل
            days_group = QGroupBox("📅 أيام العمل")
            days_layout = QHBoxLayout(days_group)
            
            days = ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"]
            self.days_checkboxes = {}
            
            for day in days:
                cb = QCheckBox(day)
                cb.setChecked(True)
                days_layout.addWidget(cb)
                self.days_checkboxes[day] = cb
            
            layout.addWidget(days_group)
            
            self.tabs.addTab(tab, "🕒 أوقات العمل")
            
        except Exception as e:
            logging.error(f"خطأ في تبويب أوقات العمل: {e}")
    
    def setup_reminders_tab(self):
        """إعداد تبويب التذكيرات الأساسية"""
        try:
            tab = QWidget()
            layout = QFormLayout(tab)
            
            # التذكيرات التلقائية
            auto_group = QGroupBox("🔔 التذكيرات الأساسية")
            auto_layout = QFormLayout(auto_group)
            
            self.reminder_24h = QCheckBox("تفعيل التذكير قبل 24 ساعة")
            self.reminder_24h.setChecked(True)
            auto_layout.addRow(self.reminder_24h)
            
            self.reminder_2h = QCheckBox("تفعيل التذكير قبل ساعتين")
            self.reminder_2h.setChecked(True)
            auto_layout.addRow(self.reminder_2h)
            
            layout.addWidget(auto_group)
            
            # إعدادات متقدمة
            advanced_group = QGroupBox("⚙️ إعدادات إضافية")
            advanced_layout = QFormLayout(advanced_group)
            
            max_appointments_label = QLabel("الحد الأقصى للمواعيد اليومية:")
            self.max_daily_appointments = QSpinBox()
            self.max_daily_appointments.setRange(1, 100)
            self.max_daily_appointments.setValue(20)
            self.max_daily_appointments.setSuffix(" موعد")
            advanced_layout.addRow(max_appointments_label, self.max_daily_appointments)
            
            layout.addWidget(advanced_group)
            
            self.tabs.addTab(tab, "🔔 التذكيرات")
            
        except Exception as e:
            logging.error(f"خطأ في تبويب التذكيرات: {e}")
    
    def setup_email_tab(self):
        """🆕 إعداد تبويب إعدادات الإيميل"""
        try:
            tab = QWidget()
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            
            content_widget = QWidget()
            layout = QFormLayout(content_widget)
            
            # إعدادات خادم SMTP
            smtp_group = QGroupBox("📧 إعدادات خادم البريد الإلكتروني (SMTP)")
            smtp_layout = QFormLayout(smtp_group)
            
            self.smtp_server = QLineEdit()
            self.smtp_server.setPlaceholderText("smtp.gmail.com")
            smtp_layout.addRow("خادم SMTP:", self.smtp_server)
            
            self.smtp_port = QSpinBox()
            self.smtp_port.setRange(1, 65535)
            self.smtp_port.setValue(587)
            smtp_layout.addRow("منفذ SMTP:", self.smtp_port)
            
            self.smtp_username = QLineEdit()
            self.smtp_username.setPlaceholderText("your.email@gmail.com")
            smtp_layout.addRow("اسم المستخدم:", self.smtp_username)
            
            self.smtp_password = QLineEdit()
            self.smtp_password.setPlaceholderText("كلمة المرور")
            self.smtp_password.setEchoMode(QLineEdit.Password)
            smtp_layout.addRow("كلمة المرور:", self.smtp_password)
            
            self.smtp_from_name = QLineEdit()
            self.smtp_from_name.setPlaceholderText("عيادة النور")
            smtp_layout.addRow("اسم المرسل:", self.smtp_from_name)
            
            self.smtp_use_tls = QCheckBox("استخدام TLS (موصى به)")
            self.smtp_use_tls.setChecked(True)
            smtp_layout.addRow(self.smtp_use_tls)
            
            layout.addWidget(smtp_group)
            
            # اختبار الإيميل
            test_group = QGroupBox("🧪 اختبار إعدادات الإيميل")
            test_layout = QHBoxLayout(test_group)
            
            test_email_btn = QPushButton("اختبار الاتصال")
            test_email_btn.clicked.connect(self.test_email_connection)
            test_layout.addWidget(test_email_btn)
            
            test_layout.addStretch()
            layout.addWidget(test_group)
            
            # معلومات مساعدة
            help_group = QGroupBox("💡 معلومات مساعدة")
            help_layout = QVBoxLayout(help_group)
            
            help_text = QLabel(
                "لإعداد الإيميل مع Gmail:\n"
                "1. تأكد من تفعيل التحقق بخطوتين\n"
                "2. إنشاء كلمة مرور للتطبيقات\n"
                "3. استخدام كلمة المرور الخاصة بالتطبيقات\n\n"
                "لإعدادات أخرى، راجع إعدادات مزود البريد الإلكتروني"
            )
            help_text.setStyleSheet("color: #7F8C8D; font-size: 12px;")
            help_text.setWordWrap(True)
            help_layout.addWidget(help_text)
            
            layout.addWidget(help_group)
            
            scroll_area.setWidget(content_widget)
            
            tab_layout = QVBoxLayout(tab)
            tab_layout.addWidget(scroll_area)
            
            self.tabs.addTab(tab, "📧 الإيميل")
            
        except Exception as e:
            logging.error(f"خطأ في تبويب الإيميل: {e}")
    
    def setup_system_tab(self):
        """إعداد تبويب النظام"""
        try:
            tab = QWidget()
            layout = QFormLayout(tab)
            
            # إعدادات النظام
            system_group = QGroupBox("⚙️ إعدادات النظام العامة")
            system_layout = QFormLayout(system_group)
            
            self.language = QComboBox()
            self.language.addItems(["العربية", "English"])
            system_layout.addRow("لغة الواجهة:", self.language)
            
            self.timezone = QComboBox()
            self.timezone.addItems(["Asia/Damascus", "Asia/Riyadh", "Asia/Dubai", "Africa/Cairo"])
            system_layout.addRow("المنطقة الزمنية:", self.timezone)
            
            system_layout.addRow(QLabel(""))  # spacer
            
            self.auto_backup = QCheckBox("تفعيل النسخ الاحتياطي التلقائي")
            system_layout.addRow(self.auto_backup)
            
            self.backup_interval = QSpinBox()
            self.backup_interval.setRange(1, 30)
            self.backup_interval.setValue(7)
            self.backup_interval.setSuffix(" أيام")
            system_layout.addRow("فترة النسخ الاحتياطي:", self.backup_interval)
            
            backup_btn = QPushButton("💾 إنشاء نسخة احتياطية الآن")
            backup_btn.clicked.connect(self.create_backup)
            system_layout.addRow(backup_btn)
            
            layout.addWidget(system_group)
            
            # إعدادات الأمان
            security_group = QGroupBox("🔒 إعدادات الأمان")
            security_layout = QFormLayout(security_group)
            
            self.auto_logout = QCheckBox("تفعيل التسجيل الخروج التلقائي")
            security_layout.addRow(self.auto_logout)
            
            self.logout_time = QSpinBox()
            self.logout_time.setRange(5, 120)
            self.logout_time.setValue(30)
            self.logout_time.setSuffix(" دقيقة")
            security_layout.addRow("فترة الخروج التلقائي:", self.logout_time)
            
            layout.addWidget(security_group)
            
            self.tabs.addTab(tab, "⚙️ النظام")
            
        except Exception as e:
            logging.error(f"خطأ في تبويب النظام: {e}")

    def test_email_connection(self):
        """اختبار اتصال الإيميل"""
        try:
            from .email_sender import EmailSender
            
            email_sender = EmailSender(self.db_manager, self)
            success = email_sender.test_connection()
            
            if success:
                QMessageBox.information(self, "نجاح", "✅ تم الاتصال بخادم الإيميل بنجاح!")
            else:
                QMessageBox.warning(self, "تحذير", 
                                  "❌ فشل في الاتصال بخادم الإيميل\n\n"
                                  "الرجاء التحقق من:\n"
                                  "• إعدادات SMTP\n• اسم المستخدم وكلمة المرور\n• اتصال الإنترنت")
                
        except ImportError as e:
            QMessageBox.warning(self, "تحذير", 
                              "❌ وحدة الإيميل غير متوفرة\n\n"
                              "تأكد من وجود ملف:\n"
                              "ui/components/email_sender.py")
        except Exception as e:
            logging.error(f"❌ فشل في اختبار الإيميل: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في اختبار الإيميل: {e}")

    def open_whatsapp_settings(self):
        """فتح إعدادات الواتساب المتقدمة"""
        try:
            # استيراد وإظهار نافذة إعدادات الواتساب
            from .whatsapp_settings import WhatsAppSettingsManager
            
            # إنشاء نافذة منبثقة لإعدادات الواتساب
            self.whatsapp_dialog = WhatsAppSettingsManager(self.db_manager, self.clinic_id)
            self.whatsapp_dialog.setWindowTitle("📱 إعدادات الواتساب المتقدمة")
            self.whatsapp_dialog.setMinimumSize(800, 600)
            self.whatsapp_dialog.exec_()
            
        except ImportError as e:
            QMessageBox.warning(self, "تحذير", 
                               "❌ وحدة إعدادات الواتساب غير متوفرة\n\n"
                               "تأكد من وجود ملف:\n"
                               "ui/components/whatsapp_settings.py")
        except Exception as e:
            logging.error(f"❌ فشل في فتح إعدادات الواتساب: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح إعدادات الواتساب: {e}")

    def load_settings(self):
        """تحميل الإعدادات من قاعدة البيانات"""
        try:
            # تحميل إعدادات العيادة
            clinic_data = self.db_manager.get_clinic_by_id(self.clinic_id)
            
            if clinic_data:
                self.clinic_name.setText(clinic_data.get('name', ""))
                
                clinic_type = clinic_data.get('type', 'عيادة')
                index = self.clinic_type.findText(clinic_type)
                if index >= 0:
                    self.clinic_type.setCurrentIndex(index)
                    
                self.main_phone.setText(clinic_data.get('main_phone', ""))
                self.clinic_address.setPlainText(clinic_data.get('address', ""))
                self.clinic_email.setText(clinic_data.get('email', ""))
            
            # تحميل الإعدادات من system_settings
            settings = self.get_system_settings()
            self.apply_settings_from_dict(settings)
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل الإعدادات: {e}")
            QMessageBox.warning(self, "تحذير", f"فشل في تحميل الإعدادات: {e}")

    def get_system_settings(self):
        """الحصول على إعدادات النظام من قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT setting_key, setting_value FROM system_settings WHERE clinic_id = ?", (self.clinic_id,))
            settings = cursor.fetchall()
            
            conn.close()
            
            return {key: value for key, value in settings}
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب إعدادات النظام: {e}")
            return {}

    def apply_settings_from_dict(self, settings):
        """تطبيق الإعدادات من القاموس"""
        try:
            # أوقات العمل
            if 'working_hours_start' in settings:
                index = self.work_start.findText(settings['working_hours_start'])
                if index >= 0:
                    self.work_start.setCurrentIndex(index)
                    
            if 'working_hours_end' in settings:
                index = self.work_end.findText(settings['working_hours_end'])
                if index >= 0:
                    self.work_end.setCurrentIndex(index)
            
            if 'appointment_duration' in settings:
                try:
                    self.appointment_duration.setValue(int(settings['appointment_duration']))
                except:
                    pass
            
            # التذكيرات
            self.reminder_24h.setChecked(settings.get('reminder_24h_enabled') == '1')
            self.reminder_2h.setChecked(settings.get('reminder_2h_enabled') == '1')
            
            # النظام
            if 'language' in settings:
                self.language.setCurrentText("العربية" if settings['language'] == 'ar' else "English")
                
            if 'timezone' in settings:
                index = self.timezone.findText(settings['timezone'])
                if index >= 0:
                    self.timezone.setCurrentIndex(index)
            
            self.auto_backup.setChecked(settings.get('auto_backup_enabled') == '1')
            
            if 'backup_interval' in settings:
                try:
                    self.backup_interval.setValue(int(settings['backup_interval']))
                except:
                    pass
            
            self.auto_logout.setChecked(settings.get('auto_logout_enabled') == '1')
            
            if 'logout_time' in settings:
                try:
                    self.logout_time.setValue(int(settings['logout_time']))
                except:
                    pass
            
            if 'max_daily_appointments' in settings:
                try:
                    self.max_daily_appointments.setValue(int(settings['max_daily_appointments']))
                except:
                    pass
            
            # أيام العمل
            if 'working_days' in settings:
                try:
                    working_days = settings['working_days'].split(',')
                    for day, checkbox in self.days_checkboxes.items():
                        checkbox.setChecked(day in working_days)
                except:
                    pass
            
            # 🆕 إعدادات الإيميل
            if 'smtp_server' in settings:
                self.smtp_server.setText(settings['smtp_server'])
            
            if 'smtp_port' in settings:
                try:
                    self.smtp_port.setValue(int(settings['smtp_port']))
                except:
                    pass
            
            if 'smtp_username' in settings:
                self.smtp_username.setText(settings['smtp_username'])
            
            if 'smtp_password' in settings:
                self.smtp_password.setText(settings['smtp_password'])
            
            if 'smtp_from_name' in settings:
                self.smtp_from_name.setText(settings['smtp_from_name'])
            
            self.smtp_use_tls.setChecked(settings.get('smtp_use_tls', '1') == '1')
                    
        except Exception as e:
            logging.error(f"❌ خطأ في تطبيق الإعدادات: {e}")
    
    def save_all_settings(self):
        """حفظ جميع الإعدادات"""
        try:
            # تحديث معلومات العيادة
            clinic_data = {
                'name': self.clinic_name.text(),
                'type': self.clinic_type.currentText(),
                'main_phone': self.main_phone.text(),
                'address': self.clinic_address.toPlainText(),
                'email': self.clinic_email.text()
            }
            
            # استخدام دالة update_clinic من db_manager
            success = self.db_manager.update_clinic(self.clinic_id, clinic_data)
            
            if not success:
                QMessageBox.warning(self, "تحذير", "فشل في تحديث معلومات العيادة")
                return
            
            # حفظ الإعدادات في system_settings
            settings_to_save = [
                ('working_hours_start', self.work_start.currentText()),
                ('working_hours_end', self.work_end.currentText()),
                ('appointment_duration', str(self.appointment_duration.value())),
                ('reminder_24h_enabled', '1' if self.reminder_24h.isChecked() else '0'),
                ('reminder_2h_enabled', '1' if self.reminder_2h.isChecked() else '0'),
                ('language', 'ar' if self.language.currentText() == 'العربية' else 'en'),
                ('timezone', self.timezone.currentText()),
                ('auto_backup_enabled', '1' if self.auto_backup.isChecked() else '0'),
                ('backup_interval', str(self.backup_interval.value())),
                ('auto_logout_enabled', '1' if self.auto_logout.isChecked() else '0'),
                ('logout_time', str(self.logout_time.value())),
                ('max_daily_appointments', str(self.max_daily_appointments.value())),
                ('working_days', ','.join([day for day, cb in self.days_checkboxes.items() if cb.isChecked()])),
                # 🆕 إعدادات الإيميل
                ('smtp_server', self.smtp_server.text()),
                ('smtp_port', str(self.smtp_port.value())),
                ('smtp_username', self.smtp_username.text()),
                ('smtp_password', self.smtp_password.text()),
                ('smtp_from_name', self.smtp_from_name.text()),
                ('smtp_use_tls', '1' if self.smtp_use_tls.isChecked() else '0')
            ]
            
            self.save_system_settings(settings_to_save)
            
            QMessageBox.information(self, "نجاح", "✅ تم حفظ جميع الإعدادات العامة بنجاح")
            
        except Exception as e:
            logging.error(f"❌ خطأ في حفظ الإعدادات: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في حفظ الإعدادات: {e}")

    def save_system_settings(self, settings):
        """حفظ إعدادات النظام"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            
            for key, value in settings:
                cursor.execute('''
                    INSERT OR REPLACE INTO system_settings 
                    (clinic_id, setting_key, setting_value, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (self.clinic_id, key, value))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"❌ خطأ في حفظ إعدادات النظام: {e}")
            raise
    
    def reset_defaults(self):
        """استعادة الإعدادات الافتراضية"""
        reply = QMessageBox.question(
            self, 
            "تأكيد الاستعادة",
            "هل أنت متأكد من رغبتك في استعادة الإعدادات الافتراضية؟\nسيتم فقدان جميع التغييرات الحالية.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # إعادة تعيين الواجهة للإعدادات الافتراضية
                self.clinic_name.clear()
                self.clinic_type.setCurrentIndex(0)
                self.main_phone.clear()
                self.clinic_address.clear()
                self.clinic_email.clear()
                
                self.work_start.setCurrentText("08:00")
                self.work_end.setCurrentText("22:00")
                self.appointment_duration.setValue(30)
                
                self.reminder_24h.setChecked(True)
                self.reminder_2h.setChecked(True)
                
                self.language.setCurrentIndex(0)
                self.timezone.setCurrentText("Asia/Damascus")
                self.auto_backup.setChecked(False)
                self.backup_interval.setValue(7)
                self.auto_logout.setChecked(False)
                self.logout_time.setValue(30)
                self.max_daily_appointments.setValue(20)
                
                # 🆕 إعدادات الإيميل الافتراضية
                self.smtp_server.clear()
                self.smtp_port.setValue(587)
                self.smtp_username.clear()
                self.smtp_password.clear()
                self.smtp_from_name.clear()
                self.smtp_use_tls.setChecked(True)
                
                # تفعيل جميع أيام العمل
                for checkbox in self.days_checkboxes.values():
                    checkbox.setChecked(True)
                
                QMessageBox.information(self, "تم", "✅ تم استعادة الإعدادات الافتراضية بنجاح")
                
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل في استعادة الإعدادات: {e}")
    
    def create_backup(self):
        """إنشاء نسخة احتياطية"""
        try:
            import shutil
            import datetime
            import os
            
            backup_dir = "data/backups"
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{backup_dir}/backup_{timestamp}.db"
            
            shutil.copy2(self.db_manager.db_path, backup_file)
            
            QMessageBox.information(self, "نسخة احتياطية", 
                                  f"✅ تم إنشاء نسخة احتياطية في:\n{backup_file}")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في إنشاء النسخة الاحتياطية: {e}")
    
    def get_clinic_info(self):
        """الحصول على معلومات العيادة"""
        try:
            clinic_data = self.db_manager.get_clinic_by_id(self.clinic_id)
            settings = self.get_system_settings()
            
            return {
                'name': clinic_data.get('name', '') if clinic_data else '',
                'address': clinic_data.get('address', '') if clinic_data else '',
                'phone': clinic_data.get('main_phone', '') if clinic_data else '',
                'email': clinic_data.get('email', '') if clinic_data else '',
                'working_hours': f"{settings.get('working_hours_start', '08:00')} - {settings.get('working_hours_end', '22:00')}"
            }
        except Exception as e:
            logging.error(f"❌ فشل في الحصول على معلومات العيادة: {e}")
            return {}