# -*- coding: utf-8 -*-
import sys
import os
import logging
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                             QTabWidget, QMessageBox, QAction, QToolBar, 
                             QStatusBar, QLabel, QDialog, QPushButton)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont, QKeySequence
import logging
import os
import sys

# إعداد المسارات بشكل آمن
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

class MainWindow(QMainWindow):
    """النافذة الرئيسية للتطبيق - الإصدار المُصحح بالكامل"""

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.clinic_id = 1  # العيادة الافتراضية
        
        # إدارة الإعدادات والمكونات
        self.settings_manager = None
        self.notification_system = None
        
        # المكونات الرئيسية
        self.dashboard = None
        self.appointments_manager = None
        self.patients_manager = None
        self.doctors_manager = None
        self.departments_manager = None
        self.whatsapp_manager = None
        
        self.setup_ui()
        self.load_components()
        self.setup_timers()
        
        logging.info("✅ تم تحميل النافذة الرئيسية بنجاح")

    def setup_ui(self):
        """إعداد واجهة النافذة الرئيسية"""
        self.setWindowTitle("نظام إدارة العيادات الطبية - النسخة المتكاملة")
        self.setMinimumSize(1400, 800)
        
        # مركزية النافذة على الشاشة
        screen = self.screen()
        screen_geometry = screen.availableGeometry()
        width = int(screen_geometry.width() * 0.8)
        height = int(screen_geometry.height() * 0.8)
        self.resize(width, height)
        self.move(
            (screen_geometry.width() - width) // 2,
            (screen_geometry.height() - height) // 2
        )
        
        # إعداد الشريط العلوي
        self.setup_menu_bar()
        self.setup_toolbar()
        
        # المنطقة المركزية
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # التبويبات الرئيسية
        self.setup_main_tabs(central_widget)
        
        # شريط الحالة
        self.setup_status_bar()
        
        # تطبيق التنسيق
        self.apply_styling()

    def setup_menu_bar(self):
        """إعداد شريط القوائم"""
        menubar = self.menuBar()
        
        # قائمة ملف
        file_menu = menubar.addMenu('📁 ملف')
        
        new_appointment_action = QAction('➕ موعد جديد', self)
        new_appointment_action.setShortcut(QKeySequence.New)
        new_appointment_action.triggered.connect(self.new_appointment)
        file_menu.addAction(new_appointment_action)
        
        file_menu.addSeparator()
        
        settings_action = QAction('⚙️ الإعدادات', self)
        settings_action.setShortcut('Ctrl+,')
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('🚪 خروج', self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close_application)
        file_menu.addAction(exit_action)
        
        # قائمة عرض
        view_menu = menubar.addMenu('👁️ عرض')
        
        refresh_action = QAction('🔄 تحديث', self)
        refresh_action.setShortcut(QKeySequence.Refresh)
        refresh_action.triggered.connect(self.refresh_all)
        view_menu.addAction(refresh_action)
        
        # قائمة تقارير
        reports_menu = menubar.addMenu('📊 تقارير')
        
        daily_report_action = QAction('📅 تقرير يومي', self)
        daily_report_action.triggered.connect(self.show_daily_report)
        reports_menu.addAction(daily_report_action)
        
        monthly_report_action = QAction('📈 تقرير شهري', self)
        monthly_report_action.triggered.connect(self.show_monthly_report)
        reports_menu.addAction(monthly_report_action)
        
        # قائمة مساعدة
        help_menu = menubar.addMenu('❓ مساعدة')
        
        about_action = QAction('ℹ️ عن البرنامج', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_toolbar(self):
        """إعداد شريط الأدوات"""
        toolbar = QToolBar("شريط الأدوات الرئيسي")
        toolbar.setIconSize(QIcon().actualSize(toolbar.iconSize()))
        self.addToolBar(toolbar)
        
        # أزرار التنقل السريع
        actions = [
            ("🏠 اللوحة الرئيسية", self.show_dashboard, "#3498DB"),
            ("📅 إدارة المواعيد", self.show_appointments, "#2ECC71"),
            ("👥 إدارة المرضى", self.show_patients, "#E74C3C"),
            ("👨‍⚕️ إدارة الأطباء", self.show_doctors, "#9B59B6"),
            ("🏥 إدارة الأقسام", self.show_departments, "#F39C12"),
            ("📱 إعدادات الواتساب", self.show_whatsapp_settings, "#27AE60")
        ]
        
        for text, slot, color in actions:
            btn = self.create_toolbar_button(text, slot, color)
            toolbar.addWidget(btn)
        
        toolbar.addSeparator()
        
        # إشعارات سريعة
        notification_btn = self.create_toolbar_button("🔔 اختبار الإشعارات", self.test_notifications, "#FF6B6B")
        toolbar.addWidget(notification_btn)

    def create_toolbar_button(self, text, slot, color):
        """إنشاء زر في شريط الأدوات"""
        btn = QPushButton(text)
        btn.clicked.connect(slot)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
                margin: 2px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
        """)
        return btn

    def setup_main_tabs(self, central_widget):
        """إعداد التبويبات الرئيسية"""
        layout = QVBoxLayout(central_widget)
        
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(False)
        
        layout.addWidget(self.tabs)

    def setup_status_bar(self):
        """إعداد شريط الحالة"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # معلومات النظام
        self.status_label = QLabel("🟢 النظام جاهز للعمل")
        status_bar.addWidget(self.status_label)
        
        # عدد المواعيد اليوم
        self.today_appointments_label = QLabel("📅 اليوم: 0 موعد")
        status_bar.addWidget(self.today_appointments_label)
        
        # حالة الواتساب
        self.whatsapp_status_label = QLabel("📱 واتساب: جاري التحميل...")
        status_bar.addWidget(self.whatsapp_status_label)
        
        # مساحة مرنة
        status_bar.addPermanentWidget(QLabel(""), 1)
        
        # الوقت والتاريخ
        self.time_label = QLabel()
        self.update_time()
        status_bar.addPermanentWidget(self.time_label)

    def load_components(self):
        """تحميل جميع المكونات الرئيسية"""
        try:
            # تحميل جميع التبويبات
            self.load_all_tabs()
            
            # تحميل مدير الإعدادات
            self.load_settings_manager()
            
            # تحميل نظام الإشعارات
            self.setup_notification_system()
            
            # تحديث البيانات الأولية
            self.refresh_all()
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل المكونات: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل المكونات: {e}")

    def load_all_tabs(self):
        """تحميل جميع التبويبات الرئيسية"""
        try:
            # قائمة المكونات الرئيسية مع دوال التحميل الخاصة بكل منها
            components = [
                ('dashboard', '🏠 اللوحة الرئيسية', self.create_dashboard_tab),
                ('appointments_manager', '📅 إدارة المواعيد', self.create_appointments_tab),
                ('patients_manager', '👥 إدارة المرضى', self.create_patients_tab),
                ('doctors_manager', '👨‍⚕️ إدارة الأطباء', self.create_doctors_tab),
                ('departments_manager', '🏥 إدارة الأقسام', self.create_departments_tab),
                ('whatsapp_manager', '📱 إعدادات الواتساب', self.create_whatsapp_tab)
            ]
            
            for attr_name, tab_name, create_method in components:
                try:
                    component = create_method()
                    if component:
                        setattr(self, attr_name, component)
                        
                        # ربط إشارات البيانات المُحدثة
                        if hasattr(component, 'data_updated'):
                            component.data_updated.connect(self.on_data_updated)
                        
                        # إضافة للتبويبات
                        self.tabs.addTab(component, tab_name)
                        logging.info(f"✅ تم تحميل {tab_name} بنجاح")
                    else:
                        # إنشاء تبويب بديل في حالة الفشل
                        fallback_widget = self.create_fallback_tab(tab_name, f"❌ المكون غير متوفر")
                        self.tabs.addTab(fallback_widget, tab_name)
                        logging.warning(f"⚠️ فشل تحميل {tab_name}")
                        
                except Exception as e:
                    logging.error(f"❌ فشل في تحميل {tab_name}: {e}")
                    fallback_widget = self.create_fallback_tab(tab_name, f"خطأ في التحميل: {str(e)}")
                    self.tabs.addTab(fallback_widget, tab_name)
                    
        except Exception as e:
            logging.error(f"❌ خطأ عام في تحميل التبويبات: {e}")

    def create_dashboard_tab(self):
        """إنشاء تبويب لوحة التحكم"""
        try:
            # محاولة الاستيراد من المسارات المختلفة
            for module_path in ['ui.components.dashboard', 'components.dashboard']:
                try:
                    module = __import__(module_path, fromlist=['Dashboard'])
                    component_class = getattr(module, 'Dashboard')
                    return component_class(self.db_manager)
                except ImportError:
                    continue
            logging.warning("⚠️ لم يتم العثور على مكون Dashboard في أي مسار")
            return None
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل Dashboard: {e}")
            return None

    def create_appointments_tab(self):
        """إنشاء تبويب إدارة المواعيد"""
        try:
            for module_path in ['ui.components.appointments_manager', 'components.appointments_manager']:
                try:
                    module = __import__(module_path, fromlist=['AppointmentsManager'])
                    component_class = getattr(module, 'AppointmentsManager')
                    return component_class(self.db_manager)
                except ImportError:
                    continue
            logging.warning("⚠️ لم يتم العثور على مكون AppointmentsManager في أي مسار")
            return None
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل AppointmentsManager: {e}")
            return None

    def create_patients_tab(self):
        """إنشاء تبويب إدارة المرضى"""
        try:
            for module_path in ['ui.components.patients_manager', 'components.patients_manager']:
                try:
                    module = __import__(module_path, fromlist=['PatientsManager'])
                    component_class = getattr(module, 'PatientsManager')
                    return component_class(self.db_manager)
                except ImportError:
                    continue
            logging.warning("⚠️ لم يتم العثور على مكون PatientsManager في أي مسار")
            return None
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل PatientsManager: {e}")
            return None

    def create_doctors_tab(self):
        """إنشاء تبويب إدارة الأطباء"""
        try:
            for module_path in ['ui.components.doctors_manager', 'components.doctors_manager']:
                try:
                    module = __import__(module_path, fromlist=['DoctorsManager'])
                    component_class = getattr(module, 'DoctorsManager')
                    return component_class(self.db_manager)
                except ImportError:
                    continue
            logging.warning("⚠️ لم يتم العثور على مكون DoctorsManager في أي مسار")
            return None
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل DoctorsManager: {e}")
            return None

    def create_departments_tab(self):
        """إنشاء تبويب إدارة الأقسام"""
        try:
            for module_path in ['ui.components.departments_manager', 'components.departments_manager']:
                try:
                    module = __import__(module_path, fromlist=['DepartmentsManager'])
                    component_class = getattr(module, 'DepartmentsManager')
                    return component_class(self.db_manager)
                except ImportError:
                    continue
            logging.warning("⚠️ لم يتم العثور على مكون DepartmentsManager في أي مسار")
            return None
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل DepartmentsManager: {e}")
            return None

    def create_whatsapp_tab(self):
        """إنشاء تبويب إعدادات الواتساب"""
        try:
            # محاولة المسارات المختلفة للواتساب
            for module_path in ['whatsapp.whatsapp_settings', 'ui.components.whatsapp_settings', 'components.whatsapp_settings']:
                try:
                    module = __import__(module_path, fromlist=['WhatsAppSettingsManager'])
                    component_class = getattr(module, 'WhatsAppSettingsManager')
                    return component_class(self.db_manager)
                except ImportError:
                    continue
            logging.warning("⚠️ لم يتم العثور على مكون WhatsAppSettingsManager في أي مسار")
            return None
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل WhatsAppSettingsManager: {e}")
            return None

    def create_fallback_tab(self, title, message):
        """إنشاء تبويب بديل عند فشل تحميل المكون"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel(f"{title}\n\n{message}")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 14px; color: #6C757D; padding: 40px;")
        layout.addWidget(label)
        
        retry_btn = QPushButton("🔄 إعادة المحاولة")
        retry_btn.clicked.connect(self.refresh_all)
        retry_btn.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #0056B3;
            }
        """)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(retry_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        return widget

    def load_settings_manager(self):
        """تحميل مدير الإعدادات"""
        try:
            for module_path in ['ui.components.settings_manager', 'components.settings_manager']:
                try:
                    module = __import__(module_path, fromlist=['SettingsManager'])
                    component_class = getattr(module, 'SettingsManager')
                    self.settings_manager = component_class(self.db_manager, self.clinic_id)
                    logging.info("✅ تم تحميل مدير الإعدادات بنجاح")
                    return
                except ImportError:
                    continue
            logging.error("❌ لم يتم العثور على مدير الإعدادات في أي مسار")
            
        except Exception as e:
            logging.error(f"❌ فشل في تحميل مدير الإعدادات: {e}")
            self.show_error_message("مدير الإعدادات", e)

    def setup_notification_system(self):
        """إعداد نظام الإشعارات الموحد"""
        try:
            if self.settings_manager is None:
                logging.warning("⚠️ نظام الإشعارات غير متوفر - الإعدادات غير محملة")
                return
            
            # محاولة تحميل نظام الإشعارات من المسارات المختلفة
            for module_path in ['ui.components.notification_manager', 'components.notification_manager', 'notifications.desktop_notifier']:
                try:
                    if 'desktop_notifier' in module_path:
                        # تحميل مباشر من ملف desktop_notifier
                        module = __import__(module_path, fromlist=['create_notification_system'])
                        create_func = getattr(module, 'create_notification_system')
                    else:
                        module = __import__(module_path, fromlist=['create_notification_system'])
                        create_func = getattr(module, 'create_notification_system')
                    
                    self.notification_system = create_func(
                        self.db_manager,
                        self.settings_manager, 
                        self
                    )
                    
                    if self.notification_system:
                        logging.info("✅ تم تفعيل نظام الإشعارات الموحد بنجاح")
                        
                        # اختبار النظام
                        self.test_notification_system()
                    return
                    
                except ImportError as e:
                    continue
                except Exception as e:
                    logging.error(f"❌ خطأ في تحميل نظام الإشعارات من {module_path}: {e}")
                    continue
            
            logging.warning("⚠️ نظام الإشعارات غير متوفر في أي مسار")
                
        except Exception as e:
            logging.error(f"❌ فشل في إعداد نظام الإشعارات: {e}")

    def test_notification_system(self):
        """اختبار نظام الإشعارات بعد التحميل"""
        try:
            if self.notification_system:
                # اختبار بسيط للإشعارات
                if hasattr(self.notification_system, 'notify_system_ready'):
                    self.notification_system.notify_system_ready()
                elif hasattr(self.notification_system, 'internal_notification'):
                    self.notification_system.internal_notification.emit("✅ النظام جاهز", "تم تحميل نظام الإشعارات بنجاح")
                
                logging.info("✅ تم اختبار نظام الإشعارات بنجاح")
        except Exception as e:
            logging.error(f"❌ خطأ في اختبار نظام الإشعارات: {e}")

    def setup_timers(self):
        """إعداد المؤقتات الدورية"""
        # تحديث الوقت كل ثانية
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
        
        # تحديث البيانات كل دقيقتين
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.refresh_data)
        self.data_timer.start(120000)
        
        # تحديث حالة النظام كل 30 ثانية
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_system_status)
        self.status_timer.start(30000)

    def update_time(self):
        """تحديث الوقت في شريط الحالة"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(f"🕒 {current_time}")

    def update_system_status(self):
        """تحديث حالة النظام"""
        try:
            # تحديث عدد مواعيد اليوم
            today_appointments = self.db_manager.get_today_appointments()
            self.today_appointments_label.setText(f"📅 اليوم: {len(today_appointments)} موعد")
            
            # تحديث حالة الواتساب
            whatsapp_status = "🔴 غير متصل"
            if self.whatsapp_manager:
                if hasattr(self.whatsapp_manager, 'is_connected'):
                    whatsapp_status = "🟢 متصل" if self.whatsapp_manager.is_connected() else "🔴 غير متصل"
                elif hasattr(self.whatsapp_manager, 'get_connection_status'):
                    status = self.whatsapp_manager.get_connection_status()
                    whatsapp_status = f"🟢 {status}" if "متصل" in status else f"🔴 {status}"
            
            self.whatsapp_status_label.setText(f"📱 واتساب: {whatsapp_status}")
            
            # تحديث حالة النظام العامة
            try:
                total_patients = len(self.db_manager.get_patients())
                total_appointments = len(self.db_manager.get_appointments())
                status_text = f"🟢 النظام نشط | 👥 {total_patients} مريض | 📅 {total_appointments} موعد"
                self.status_label.setText(status_text)
            except:
                self.status_label.setText("🟢 النظام يعمل")
                
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث حالة النظام: {e}")

    def apply_styling(self):
        """تطبيق التنسيق على الواجهة"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F8F9FA, stop:1 #E9ECEF);
            }
            QTabWidget::pane {
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                background-color: white;
                margin-top: 5px;
            }
            QTabBar::tab {
                background-color: #E9ECEF;
                color: #495057;
                padding: 12px 20px;
                margin-right: 3px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                font-size: 13px;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background-color: #007BFF;
                color: white;
                border-bottom: 3px solid #0056B3;
            }
            QTabBar::tab:hover {
                background-color: #0056B3;
                color: white;
            }
            QStatusBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2C3E50, stop:1 #34495E);
                color: white;
                padding: 5px;
                font-weight: bold;
            }
            QToolBar {
                background-color: white;
                border: none;
                border-bottom: 2px solid #DEE2E6;
                spacing: 8px;
                padding: 8px;
            }
            QMenuBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2C3E50, stop:1 #34495E);
                color: white;
                padding: 5px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 8px 12px;
                border-radius: 4px;
                margin: 2px;
            }
            QMenuBar::item:selected {
                background-color: #3498DB;
            }
        """)

    def darken_color(self, color):
        """تغميق اللون للتأثيرات"""
        try:
            from PyQt5.QtGui import QColor
            qcolor = QColor(color)
            return qcolor.darker(120).name()
        except:
            return color

    # ██████████████████████████████████████████████████████████████████████████
    # دوال التنقل بين التبويبات
    # ██████████████████████████████████████████████████████████████████████████

    def show_dashboard(self):
        """إظهار لوحة التحكم"""
        self.tabs.setCurrentIndex(0)
        if self.dashboard and hasattr(self.dashboard, 'refresh_data'):
            self.dashboard.refresh_data()

    def show_appointments(self):
        """إظهار إدارة المواعيد"""
        self.tabs.setCurrentIndex(1)
        if self.appointments_manager and hasattr(self.appointments_manager, 'load_appointments'):
            self.appointments_manager.load_appointments()

    def show_patients(self):
        """إظهار إدارة المرضى"""
        self.tabs.setCurrentIndex(2)
        if self.patients_manager and hasattr(self.patients_manager, 'load_patients'):
            self.patients_manager.load_patients()

    def show_doctors(self):
        """إظهار إدارة الأطباء"""
        self.tabs.setCurrentIndex(3)
        if self.doctors_manager and hasattr(self.doctors_manager, 'load_doctors'):
            self.doctors_manager.load_doctors()

    def show_departments(self):
        """إظهار إدارة الأقسام"""
        self.tabs.setCurrentIndex(4)
        if self.departments_manager and hasattr(self.departments_manager, 'load_departments'):
            self.departments_manager.load_departments()

    def show_whatsapp_settings(self):
        """إظهار إعدادات الواتساب"""
        self.tabs.setCurrentIndex(5)
        if self.whatsapp_manager and hasattr(self.whatsapp_manager, 'refresh_settings'):
            self.whatsapp_manager.refresh_settings()

    # ██████████████████████████████████████████████████████████████████████████
    # دوال القوائم الرئيسية
    # ██████████████████████████████████████████████████████████████████████████

    def new_appointment(self):
        """إضافة موعد جديد"""
        try:
            for module_path in ['ui.dialogs.appointment_dialog', 'dialogs.appointment_dialog']:
                try:
                    module = __import__(module_path, fromlist=['AppointmentDialog'])
                    dialog_class = getattr(module, 'AppointmentDialog')
                    dialog = dialog_class(self.db_manager, self)
                    if dialog.exec_() == QDialog.Accepted:
                        self.refresh_all()
                        if self.notification_system:
                            self.notification_system.notify_new_appointment("مريض جديد", "الآن")
                    return
                except ImportError:
                    continue
            
            QMessageBox.warning(self, "تحذير", "نافذة إضافة الموعد غير متوفرة حالياً")
                    
        except Exception as e:
            self.show_error_message("إضافة موعد", e)

    def open_settings(self):
        """فتح الإعدادات"""
        try:
            if self.settings_manager is None:
                QMessageBox.warning(self, "تحذير", "مدير الإعدادات غير متوفر")
                return
            
            settings_dialog = QDialog(self)
            settings_dialog.setWindowTitle("⚙️ الإعدادات العامة للنظام")
            settings_dialog.setMinimumSize(1000, 700)
            settings_dialog.setModal(True)
            
            layout = QVBoxLayout(settings_dialog)
            layout.addWidget(self.settings_manager)
            
            buttons_layout = QHBoxLayout()
            save_btn = self.create_toolbar_button("💾 حفظ الإعدادات", 
                                                self.settings_manager.save_all_settings, "#28A745")
            close_btn = self.create_toolbar_button("إغلاق", settings_dialog.close, "#6C757D")
            
            buttons_layout.addWidget(save_btn)
            buttons_layout.addWidget(close_btn)
            buttons_layout.addStretch()
            
            layout.addLayout(buttons_layout)
            settings_dialog.exec_()
            
        except Exception as e:
            self.show_error_message("فتح الإعدادات", e)

    def refresh_all(self):
        """تحديث جميع البيانات"""
        try:
            # تحديث جميع المكونات
            components = [
                self.dashboard,
                self.appointments_manager, 
                self.patients_manager,
                self.doctors_manager,
                self.departments_manager,
                self.whatsapp_manager
            ]
            
            for component in components:
                if component:
                    if hasattr(component, 'refresh_data'):
                        component.refresh_data()
                    elif hasattr(component, 'load_appointments'):
                        component.load_appointments()
                    elif hasattr(component, 'load_patients'):
                        component.load_patients()
                    elif hasattr(component, 'load_doctors'):
                        component.load_doctors()
                    elif hasattr(component, 'load_departments'):
                        component.load_departments()
                    elif hasattr(component, 'refresh_settings'):
                        component.refresh_settings()
            
            # تحديث شريط الحالة
            self.update_system_status()
            
            logging.info("✅ تم تحديث جميع البيانات بنجاح")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث البيانات: {e}")

    def refresh_data(self):
        """تحديث البيانات (للاستخدام من المؤقتات)"""
        self.refresh_all()

    def on_data_updated(self):
        """عند تحديث البيانات من أي مكون"""
        self.refresh_all()

    def show_daily_report(self):
        """عرض التقرير اليومي"""
        try:
            if self.dashboard and hasattr(self.dashboard, 'show_full_report'):
                self.dashboard.show_full_report()
            else:
                QMessageBox.information(self, "التقرير اليومي", 
                                      "📊 جاري إعداد التقرير اليومي...")
        except Exception as e:
            self.show_error_message("التقرير اليومي", e)

    def show_monthly_report(self):
        """عرض التقرير الشهري"""
        QMessageBox.information(self, "التقرير الشهري", 
                              "📈 جاري إعداد التقرير الشهري...\n\nهذه الميزة قيد التطوير")

    def test_notifications(self):
        """اختبار نظام الإشعارات"""
        try:
            if self.notification_system:
                if hasattr(self.notification_system, 'test_notification'):
                    self.notification_system.test_notification()
                elif hasattr(self.notification_system, 'internal_notification'):
                    self.notification_system.internal_notification.emit("🧪 اختبار", "هذا إشعار اختبار من النظام")
                
                QMessageBox.information(self, "اختبار الإشعارات", 
                                      "🔔 تم إرسال إشعار اختبار بنجاح!")
            else:
                QMessageBox.warning(self, "تحذير", 
                                  "نظام الإشعارات غير مفعل حالياً")
        except Exception as e:
            self.show_error_message("اختبار الإشعارات", e)

    def show_about(self):
        """عرض معلومات عن البرنامج"""
        about_text = """
        🏥 نظام إدارة العيادات الطبية - النسخة المتكاملة
        
        📋 وصف النظام:
        نظام متكامل لإدارة العيادات والمستشفيات يتضمن:
        • إدارة المواعيد والمرضى
        • إدارة الأطباء والأقسام  
        • نظام إشعارات متكامل
        • تقارير وإحصائيات متقدمة
        • تكامل مع واتساب والبريد الإلكتروني
        
        🚀 المميزات:
        ✅ لوحة تحكم شاملة
        ✅ إرسال تلقائي للتذكيرات
        ✅ إشعارات داخلية وخارجية
        ✅ نسخ احتياطي تلقائي
        ✅ واجهة مستخدم متطورة
        
        ⚙️ الإصدار: 2.0 المتكامل
        📅 آخر تحديث: 2024
        """
        
        QMessageBox.about(self, "عن البرنامج", about_text)

    def show_error_message(self, context, error):
        """عرض رسالة خطأ موحدة"""
        error_msg = f"❌ فشل في {context}:\n\n{str(error)}"
        logging.error(error_msg)
        QMessageBox.critical(self, "خطأ", error_msg)

    def close_application(self):
        """إغلاق التطبيق"""
        reply = QMessageBox.question(
            self, 
            "تأكيد الخروج",
            "هل أنت متأكد من رغبتك في إغلاق التطبيق؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # إيقاف جميع المؤقتات
            timers = ['time_timer', 'data_timer', 'status_timer']
            for timer_name in timers:
                timer = getattr(self, timer_name, None)
                if timer and timer.isActive():
                    timer.stop()
            
            # إغلاق نظام الإشعارات
            if self.notification_system and hasattr(self.notification_system, 'quit_application'):
                self.notification_system.quit_application()
            
            logging.info("✅ تم إغلاق التطبيق بنجاح")
            self.close()

    def closeEvent(self, event):
        """معالجة حدث إغلاق النافذة"""
        self.close_application()
        event.accept()

# تشغيل التطبيق
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    
    # نموذج تجريبي لمدير قاعدة البيانات
    class MockDBManager:
        def get_today_appointments(self):
            return []
        def get_patients(self):
            return []
        def get_appointments(self):
            return []
        def get_clinics(self):
            return [{'id': 1, 'name': 'عيادة النور'}]
        def get_doctors(self):
            return []
        def get_departments(self):
            return []

    # إعداد التطبيق
    app = QApplication(sys.argv)
    app.setApplicationName("نظام إدارة العيادات")
    app.setApplicationVersion("2.0 المتكامل")
    
    # إنشاء النافذة الرئيسية
    try:
        db_manager = MockDBManager()
        window = MainWindow(db_manager)
        window.show()
        
        sys.exit(app.exec_())
    except Exception as e:
        logging.critical(f"❌ فشل تشغيل النظام: {e}")
        QMessageBox.critical(None, "خطأ فادح", f"فشل تشغيل النظام:\n\n{str(e)}")
        sys.exit(1)