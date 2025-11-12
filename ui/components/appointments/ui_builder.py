# ui/components/appointments/ui_builder.py
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
                             QMessageBox, QHeaderView, QLabel, QToolBar,
                             QDateEdit, QGroupBox, QFrame, QProgressBar,
                             QTextEdit, QTabWidget, QSplitter, QScrollArea)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QColor, QIcon, QPalette
import logging
from datetime import datetime

class AppointmentsUIBuilder:
    """منشئ واجهة إدارة المواعيد - الإصدار المتكامل الكامل"""
    
    def __init__(self, main_app):
        self.main = main_app
        self.setup_completed = False
        self.status_update_timer = QTimer()
        
    def setup_ui(self):
        """إعداد الواجهة الرئيسية - بدون تكرار"""
        try:
            self.main.setMinimumSize(1400, 800)
            self.main.setWindowTitle("🏥 نظام إدارة المواعيد المتقدم + 🤖 الإرسال التلقائي الذكي")
            
            # تطبيق سمة ألوان متكاملة
            self.apply_global_theme()
            
            main_layout = QVBoxLayout()
            main_layout.setSpacing(12)
            main_layout.setContentsMargins(15, 15, 15, 15)
            
            # العنوان الرئيسي المحسن
            title_layout = self.create_enhanced_title_layout()
            main_layout.addLayout(title_layout)
            
            # تبويبات رئيسية بمظهر حديث
            self.main.tabs = QTabWidget()
            self.setup_modern_tabs()
            
            # إعداد التبويبات الرئيسية فقط
            self.setup_appointments_tab()
            self.setup_auto_sender_tab()
            
            # تبويبات إضافية (يتم استدعاؤها من TabManager)
            if hasattr(self.main, 'tab_manager'):
                try:
                    self.main.tab_manager.setup_bulk_messaging_tab(self.main)
                    self.main.tab_manager.setup_reports_tab(self.main) 
                    self.main.tab_manager.setup_settings_tab(self.main)
                except Exception as e:
                    logging.warning(f"⚠️ بعض التبويبات الإضافية غير متوفرة: {e}")
            
            main_layout.addWidget(self.main.tabs)
            
            # ⭐⭐ شريط حالة واحد فقط في الأسفل ⭐⭐
            status_bar = self.create_single_status_bar()
            main_layout.addWidget(status_bar)
            
            self.main.setLayout(main_layout)
            
            # تعيين جميع العناصر
            self.assign_all_widgets()
            
            # بدء التحديث التلقائي للحالة
            self.start_status_updates()
            
            self.setup_completed = True
            logging.info("✅ تم إعداد واجهة المواعيد بنجاح - بدون تكرار")
            
        except Exception as e:
            logging.error(f"❌ خطأ في إعداد الواجهة: {e}")

    def apply_global_theme(self):
        """تطبيق سمة ألوان عالمية"""
        self.main.setStyleSheet("""
            QMainWindow, QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F8F9FA, stop:1 #E9ECEF);
                font-family: 'Segoe UI', 'Tahoma', 'Arial';
            }
            
            QWidget {
                font-size: 14px;
            }
        """)

    def create_enhanced_title_layout(self):
        """إنشاء تخطيط العنوان"""
        title_layout = QHBoxLayout()
        
        # العنوان الرئيسي
        title_label = QLabel("🏥 نظام إدارة المواعيد المتقدم")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(20)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                padding: 20px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498DB, stop:0.5 #2C3E50, stop:1 #3498DB);
                color: white;
                border-radius: 12px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(title_label)
        
        # الإحصائيات السريعة
        quick_stats_layout = self.create_quick_stats()
        title_layout.addLayout(quick_stats_layout)
        
        return title_layout

    def create_quick_stats(self):
        """إنشاء الإحصائيات السريعة"""
        quick_stats_layout = QHBoxLayout()
        quick_stats_layout.setSpacing(10)
        
        today_appointments = len([a for a in self.main.all_appointments 
                                if a.get('appointment_date') == self.main.get_today_date()])
        
        auto_sender_status = "🟢 نشط" if self.main.auto_sender and hasattr(self.main.auto_sender, 'is_running') and self.main.auto_sender.is_running else "🔴 متوقف"
        
        quick_stats = [
            f"📊 اليوم: {today_appointments} موعد",
            f"🕒 {self.main.get_current_time()}",
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
        return quick_stats_layout

    def setup_modern_tabs(self):
        """إعداد تبويبات"""
        self.main.tabs.setStyleSheet("""
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

    def setup_appointments_tab(self):
        """إعداد تبويب المواعيد الرئيسي"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # شريط الأدوات
        toolbar = self.create_enhanced_toolbar()
        layout.addWidget(toolbar)
        
        # منطقة الإحصائيات
        stats_layout = self.create_enhanced_stats()
        layout.addLayout(stats_layout)
        
        # عوامل التصفية
        filter_group = self.create_advanced_filters()
        layout.addWidget(filter_group)
        
        # جدول المواعيد واللوحة الجانبية
        table_layout = QHBoxLayout()
        
        # الجدول
        self.appointments_table = self.create_enhanced_table()
        table_layout.addWidget(self.appointments_table)
        
        # اللوحة الجانبية
        sidebar = self.create_quick_sidebar()
        table_layout.addWidget(sidebar)
        
        layout.addLayout(table_layout)
        
        # ⭐⭐ لا نضيف شريط حالة هنا - فقط في الأسفل ⭐⭐
        
        self.main.tabs.addTab(tab, "📋 المواعيد")

    def create_enhanced_toolbar(self):
        """إنشاء شريط أدوات"""
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
            ("➕ حجز جديد", self.main.add_appointment, "#28A745", "add"),
            ("✏️ تعديل", self.main.edit_appointment, "#007BFF", "edit"),
            ("🗑️ إلغاء", self.main.cancel_appointment, "#DC3545", "cancel"),
            ("✅ تأكيد", self.main.confirm_appointment, "#17A2B8", "confirm"),
            ("📝 حضور", self.main.mark_as_completed, "#9B59B6", "complete")
        ]
        
        for text, slot, color, action_type in appointments_actions:
            btn = self.create_toolbar_button(text, slot, color, action_type)
            toolbar.addWidget(btn)
        
        toolbar.addSeparator()
        
        # زر الجدولة الذكية المضافة
        smart_schedule_btn = QPushButton("🎯 جدولة ذكية")
        smart_schedule_btn.clicked.connect(self.main.open_smart_scheduling)
        smart_schedule_btn.setStyleSheet("""
            QPushButton {
                background-color: #9B59B6;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 120px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
        """)
        toolbar.addWidget(smart_schedule_btn)
        
        toolbar.addSeparator()
        
        # البحث المتقدم
        toolbar.addWidget(QLabel("بحث متقدم:"))
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
        self.search_input.textChanged.connect(self.main.quick_search)
        toolbar.addWidget(self.search_input)
        
        # زر البحث المتقدم
        advanced_search_btn = QPushButton("🎯 متقدم")
        advanced_search_btn.clicked.connect(self.main.show_advanced_search)
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
        """)
        
        return btn

    def create_enhanced_stats(self):
        """إنشاء إحصائيات"""
        layout = QHBoxLayout()
        
        self.main.stats_widgets = {
            'مجدول': self.create_stat_card("المجدولة", "0", "#3498DB"),
            '✅ مؤكد': self.create_stat_card("المؤكدة", "0", "#27AE60"),
            'حاضر': self.create_stat_card("الحاضرة", "0", "#9B59B6"),
            'منتهي': self.create_stat_card("المنتهية", "0", "#95A5A6"),
            'ملغى': self.create_stat_card("الملغاة", "0", "#E74C3C"),
            'رسائل': self.create_stat_card("الرسائل", "0", "#F39C12")
        }
        
        for widget in self.main.stats_widgets.values():
            layout.addWidget(widget)
        
        layout.addStretch()
        return layout

    def create_stat_card(self, title, value, color):
        """إنشاء بطاقة إحصائية"""
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
        self.date_filter.currentTextChanged.connect(self.main.on_date_filter_changed)
        date_filter_layout.addWidget(self.date_filter)
        
        self.custom_date_start = QDateEdit()
        self.custom_date_start.setDate(self.main.get_current_date())
        self.custom_date_start.setDisplayFormat("yyyy-MM-dd")
        self.custom_date_start.setEnabled(False)
        date_filter_layout.addWidget(self.custom_date_start)
        
        self.custom_date_end = QDateEdit()
        self.custom_date_end.setDate(self.main.get_current_date())
        self.custom_date_end.setDisplayFormat("yyyy-MM-dd")
        self.custom_date_end.setEnabled(False)
        date_filter_layout.addWidget(self.custom_date_end)
        
        date_layout.addLayout(date_filter_layout)
        
        # فلتر الحالة
        status_layout = QVBoxLayout()
        status_layout.addWidget(QLabel("📊 الحالة:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["جميع الحالات", "🗓️ مجدول", "✅ مؤكد", "🕓 منتهي", "❌ ملغى", "🙋‍♂️ حاضر"])
        self.status_filter.currentTextChanged.connect(self.main.load_appointments)
        status_layout.addWidget(self.status_filter)
        
        # فلتر الطبيب
        doctor_layout = QVBoxLayout()
        doctor_layout.addWidget(QLabel("👨‍⚕️ الطبيب:"))
        self.doctor_filter = QComboBox()
        self.doctor_filter.addItems(["جميع الأطباء"])
        if hasattr(self.main, 'load_doctors'):
            self.main.load_doctors()
        self.doctor_filter.currentTextChanged.connect(self.main.load_appointments)
        doctor_layout.addWidget(self.doctor_filter)
        
        layout.addLayout(date_layout)
        layout.addLayout(status_layout)
        layout.addLayout(doctor_layout)
        layout.addStretch()
        
        # زر تطبيق الفلاتر
        apply_filters_btn = QPushButton("🔍 تطبيق الفلاتر")
        apply_filters_btn.clicked.connect(self.main.apply_advanced_filters)
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
        """إنشاء جدول مواعيد"""
        table = QTableWidget()
        table.setColumnCount(10)
        table.setHorizontalHeaderLabels([
            "🔘", "🆔", "👤 المريض", "📞 الهاتف", "👨‍⚕️ الطبيب", 
            "📅 التاريخ", "🕒 الوقت", "📊 الحالة", "📱 واتساب", "📝 ملاحظات"
        ])
        
        # ضبط إعدادات الجدول
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.Stretch)
        
        table.setColumnWidth(0, 40)
        table.setColumnWidth(1, 60)
        table.setColumnWidth(3, 120)
        table.setColumnWidth(5, 100)
        table.setColumnWidth(6, 80)
        table.setColumnWidth(7, 100)
        table.setColumnWidth(8, 80)
        
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        table.doubleClicked.connect(self.main.edit_appointment)
        
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
        table.customContextMenuRequested.connect(self.main.show_enhanced_context_menu)
        
        return table

    def create_quick_sidebar(self):
        """إنشاء اللوحة الجانبية"""
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
            ("📞 اتصال سريع", self.main.quick_call),
            ("📱 إرسال رسالة", self.main.quick_message),
            ("📧 إرسال بريد", self.main.quick_email),
            ("🗓️ إعادة جدولة", self.main.quick_reschedule)
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

    def setup_auto_sender_tab(self):
        """إعداد تبويب الإرسال التلقائي - الإصدار المتكامل"""
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
        
        # 🔥 أزرار التحكم - مرتبطة مباشرة بالدوال
        control_group = QGroupBox("🎮 تحكم فوري")
        control_layout = QHBoxLayout(control_group)
        
        # زر البدء
        self.start_auto_btn = QPushButton("🚀 بدء الإرسال التلقائي")
        self.start_auto_btn.clicked.connect(self.start_auto_sender_direct)
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
            QPushButton:disabled {
                background-color: #95A5A6;
            }
        """)
        
        # زر الإيقاف
        self.stop_auto_btn = QPushButton("⏹️ إيقاف الإرسال التلقائي")
        self.stop_auto_btn.clicked.connect(self.stop_auto_sender_direct)
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
            QPushButton:disabled {
                background-color: #95A5A6;
            }
        """)
        self.stop_auto_btn.setEnabled(False)
        
        # زر الاختبار
        self.test_auto_btn = QPushButton("🧪 اختبار النظام التلقائي")
        self.test_auto_btn.clicked.connect(self.test_auto_sender_direct)
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
            QPushButton:disabled {
                background-color: #95A5A6;
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
        
        # زر مسح السجل
        clear_log_btn = QPushButton("🗑️ مسح السجل")
        clear_log_btn.clicked.connect(lambda: self.auto_sender_log.clear())
        clear_log_btn.setStyleSheet("""
            QPushButton {
                background-color: #95A5A6;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #7F8C8D;
            }
        """)
        log_layout.addWidget(clear_log_btn)
        
        layout.addWidget(log_group)
        
        self.main.tabs.addTab(tab, "🤖 التلقائي")

    def create_single_status_bar(self):
        """إنشاء شريط حالة واحد فقط في الأسفل"""
        status_bar = QFrame()
        status_bar.setFixedHeight(80)
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
        self.system_status.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        layout.addWidget(self.system_status)
        
        # عدد النتائج
        self.results_count = QLabel("0 موعد")
        self.results_count.setStyleSheet("color: #3498DB; font-weight: bold; font-size: 12px;")
        layout.addWidget(self.results_count)
        
        # آخر تحديث
        self.last_update = QLabel("آخر تحديث: --")
        self.last_update.setStyleSheet("color: #BDC3C7; font-size: 11px;")
        layout.addWidget(self.last_update)
        
        layout.addStretch()
        
        # حالة الواتساب فقط - بدون حالة التلقائي المكررة
        self.whatsapp_status = QLabel("📱 واتساب: غير متصل")
        self.whatsapp_status.setStyleSheet("color: #E74C3C; font-weight: bold; font-size: 12px;")
        layout.addWidget(self.whatsapp_status)
        
        return status_bar

    def start_status_updates(self):
        """بدء التحديث التلقائي للحالة"""
        try:
            self.status_update_timer.timeout.connect(self.update_live_status)
            self.status_update_timer.start(5000)  # كل 5 ثوان
        except Exception as e:
            logging.error(f"❌ خطأ في بدء التحديث التلقائي: {e}")

    def update_live_status(self):
        """تحديث الحالة الحية للنظام"""
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            self.last_update.setText(f"آخر تحديث: {current_time}")
            
            # تحديث حالة الواتساب
            whatsapp_connected = (self.main.whatsapp_manager and 
                               getattr(self.main.whatsapp_manager, 'is_connected', False))
            whatsapp_text = "📱 واتساب: متصل" if whatsapp_connected else "📱 واتساب: غير متصل"
            self.whatsapp_status.setText(whatsapp_text)
            self.whatsapp_status.setStyleSheet(f"""
                QLabel {{
                    color: {'#27AE60' if whatsapp_connected else '#E74C3C'};
                    font-weight: bold;
                    font-size: 12px;
                }}
            """)
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث الحالة: {e}")

    def assign_all_widgets(self):
        """تعيين جميع عناصر الواجهة بشكل كامل"""
        try:
            # عناصر الجدول والبحث
            self.main.appointments_table = self.appointments_table
            self.main.search_input = self.search_input
            
            # عناصر الفلاتر
            self.main.date_filter = self.date_filter
            self.main.status_filter = self.status_filter
            self.main.doctor_filter = self.doctor_filter
            self.main.custom_date_start = self.custom_date_start
            self.main.custom_date_end = self.custom_date_end
            
            # عناصر الشريط الجانبي
            self.main.selected_appointment_info = self.selected_appointment_info
            self.main.whatsapp_stats_info = self.whatsapp_stats_info
            
            # عناصر AutoSender
            self.main.auto_sender_info = self.auto_sender_info
            self.main.auto_sender_stats = self.auto_sender_stats
            self.main.auto_sender_log = self.auto_sender_log
            self.main.start_auto_btn = self.start_auto_btn
            self.main.stop_auto_btn = self.stop_auto_btn
            self.main.test_auto_btn = self.test_auto_btn
            
            # عناصر شريط الحالة
            self.main.system_status = self.system_status
            self.main.results_count = self.results_count
            self.main.last_update = self.last_update
            self.main.whatsapp_status = self.whatsapp_status
            
            logging.info("✅ تم تعيين جميع عناصر الواجهة بنجاح")
            
        except Exception as e:
            logging.error(f"❌ فشل تعيين عناصر الواجهة: {e}")

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

    # 🔥 دوال التحكم المباشرة في AutoSender
    def start_auto_sender_direct(self):
        """بدء الإرسال التلقائي - مباشر من الواجهة"""
        try:
            if hasattr(self.main, 'auto_sender') and self.main.auto_sender:
                success = self.main.auto_sender.start_auto_sender()
                if success:
                    self.start_auto_btn.setEnabled(False)
                    self.stop_auto_btn.setEnabled(True)
                    self.test_auto_btn.setEnabled(False)
                    self.update_auto_sender_display()
                    logging.info("🚀 تم بدء الإرسال التلقائي بنجاح")
                else:
                    logging.error("❌ فشل بدء الإرسال التلقائي")
            else:
                logging.error("❌ نظام الإرسال التلقائي غير متوفر")
        except Exception as e:
            logging.error(f"❌ خطأ في بدء التلقائي: {e}")

    def stop_auto_sender_direct(self):
        """إيقاف الإرسال التلقائي - مباشر من الواجهة"""
        try:
            if hasattr(self.main, 'auto_sender') and self.main.auto_sender:
                success = self.main.auto_sender.stop_auto_sender()
                if success:
                    self.start_auto_btn.setEnabled(True)
                    self.stop_auto_btn.setEnabled(False)
                    self.test_auto_btn.setEnabled(True)
                    self.update_auto_sender_display()
                    logging.info("⏹️ تم إيقاف الإرسال التلقائي بنجاح")
                else:
                    logging.error("❌ فشل إيقاف الإرسال التلقائي")
            else:
                logging.error("❌ نظام الإرسال التلقائي غير متوفر")
        except Exception as e:
            logging.error(f"❌ خطأ في إيقاف التلقائي: {e}")

    def test_auto_sender_direct(self):
        """اختبار الإرسال التلقائي - مباشر من الواجهة"""
        try:
            if hasattr(self.main, 'auto_sender') and self.main.auto_sender:
                success = self.main.auto_sender.start_quick_test()
                if success:
                    self.start_auto_btn.setEnabled(False)
                    self.stop_auto_btn.setEnabled(True)
                    self.test_auto_btn.setEnabled(False)
                    self.update_auto_sender_display()
                    logging.info("🧪 تم بدء اختبار النظام التلقائي بنجاح")
                else:
                    logging.error("❌ فشل بدء اختبار النظام التلقائي")
            else:
                logging.error("❌ نظام الإرسال التلقائي غير متوفر")
        except Exception as e:
            logging.error(f"❌ خطأ في اختبار التلقائي: {e}")

    def update_auto_sender_display(self):
        """تحديث عرض الإرسال التلقائي"""
        try:
            if hasattr(self.main, 'auto_sender') and self.main.auto_sender:
                self.main.auto_sender.update_ui_info(self.main)
                logging.info("🔄 تم تحديث عرض النظام التلقائي")
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث العرض: {e}")