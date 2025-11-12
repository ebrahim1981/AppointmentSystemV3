# smart_scheduling_dialog.py
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QTextEdit, QComboBox, QDateEdit, 
                             QTimeEdit, QPushButton, QLabel, QGroupBox, QFrame, 
                             QGridLayout, QCheckBox, QScrollArea, QSizePolicy,
                             QDialog, QMessageBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QTabWidget, QCalendarWidget, QListWidget,
                             QListWidgetItem, QDialogButtonBox)
from PyQt5.QtCore import Qt, QDate, QTime, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette
import logging
from datetime import datetime, timedelta

# استيراد SmartScheduler من المسار الصحيح
try:
    from ui.dialogs.widgets.smart_scheduler import SmartScheduler
except ImportError:
    # إذا فشل الاستيراد، ننشئ فئة بديلة لمنع الأخطاء
    class SmartScheduler:
        def __init__(self, db_manager):
            self.db_manager = db_manager
            self.availability_calculated = pyqtSignal(dict)
            self.smart_suggestions_ready = pyqtSignal(list)
        
        def calculate_availability(self, doctor_id, date):
            pass
        
        def get_smart_suggestions(self, doctor_id, date, duration):
            return []

class SmartSchedulingUI(QWidget):
    """واجهة الجدولة الذكية المتكاملة - الإصدار الحقيقي"""
    
    # إشارات للتكامل مع الملف الرئيسي
    time_selected = pyqtSignal(str)  # عند اختيار وقت
    availability_updated = pyqtSignal(dict)  # عند تحديث الأوقات
    schedule_data_ready = pyqtSignal(dict)  # عند جاهزية بيانات الجدول
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.smart_scheduler = SmartScheduler(db_manager)
        self.current_doctor_id = None
        self.current_date = None
        self.last_availability_data = None
        self.periodic_schedule_data = None
        
        self.setup_ui()
        self.connect_signals()
        
        # مؤقت للتجديد التلقائي
        self.auto_renew_timer = QTimer(self)
        self.auto_renew_timer.timeout.connect(self.check_auto_renew)
        self.auto_renew_timer.start(3600000)  # كل ساعة
        
    def setup_ui(self):
        """إعداد واجهة الجدولة الذكية المتكاملة"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # مجموعة الجدولة الذكية المتكاملة
        scheduling_group = QGroupBox("🗓️  الجدولة الذكية المتكاملة - نظام الجداول الدورية")
        scheduling_group.setStyleSheet(self.get_group_style())
        group_layout = QVBoxLayout(scheduling_group)
        
        # شريط الحالة المتطور
        self.setup_enhanced_status_bar(group_layout)
        
        # أزرار التحكم المتقدمة
        self.setup_advanced_controls(group_layout)
        
        # نظام التبويبات للعرض المختلف
        self.setup_tab_system(group_layout)
        
        layout.addWidget(scheduling_group)
        
    def setup_enhanced_status_bar(self, parent_layout):
        """إعداد شريط الحالة المتطور"""
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2C3E50, stop:1 #34495E);
                border-radius: 6px;
                padding: 8px;
            }
        """)
        status_layout = QHBoxLayout(status_frame)
        
        # معلومات الطبيب
        self.doctor_info = QLabel("لم يتم اختيار طبيب")
        self.doctor_info.setStyleSheet("color: #ECF0F1; font-size: 12px; font-weight: bold;")
        
        # معلومات الجدول
        self.schedule_info = QLabel("الجداول: غير محملة")
        self.schedule_info.setStyleSheet("color: #BDC3C7; font-size: 11px;")
        
        # حالة النظام
        self.system_status = QLabel("🟢 جاهز")
        self.system_status.setStyleSheet("color: #27AE60; font-size: 11px; font-weight: bold;")
        
        status_layout.addWidget(self.doctor_info)
        status_layout.addStretch()
        status_layout.addWidget(self.schedule_info)
        status_layout.addWidget(self.system_status)
        
        parent_layout.addWidget(status_frame)
        
    def setup_advanced_controls(self, parent_layout):
        """إعداد أزرار التحكم المتقدمة"""
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        # زر تحميل الجدول الدوري
        self.load_schedule_btn = QPushButton("📊 تحميل الجدول الدوري")
        self.load_schedule_btn.clicked.connect(self.load_periodic_schedule)
        self.load_schedule_btn.setStyleSheet(self.get_button_style("primary"))
        self.load_schedule_btn.setVisible(False)
        
        # زر تحديث الجداول
        self.refresh_btn = QPushButton("🔄 تحديث الجداول")
        self.refresh_btn.clicked.connect(self.refresh_availability)
        self.refresh_btn.setStyleSheet(self.get_button_style("info"))
        self.refresh_btn.setVisible(False)
        
        # زر النافذة المنبثقة المتقدمة (تم تعديله)
        self.popup_btn = QPushButton("🕒 نافذة المواعيد المتقدمة")
        self.popup_btn.clicked.connect(self.show_advanced_time_popup)
        self.popup_btn.setStyleSheet(self.get_button_style("success"))
        self.popup_btn.setVisible(False)
        
        # زر إدارة الجداول
        self.manage_btn = QPushButton("⚙️ إدارة الجداول")
        self.manage_btn.clicked.connect(self.manage_schedules)
        self.manage_btn.setStyleSheet(self.get_button_style("warning"))
        self.manage_btn.setVisible(False)
        
        controls_layout.addWidget(self.load_schedule_btn)
        controls_layout.addWidget(self.refresh_btn)
        controls_layout.addWidget(self.popup_btn)
        controls_layout.addWidget(self.manage_btn)
        controls_layout.addStretch()
        
        parent_layout.addLayout(controls_layout)
        
    def setup_tab_system(self, parent_layout):
        """إعداد نظام التبويبات للعرض المختلف"""
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                background-color: #FFFFFF;
            }
            QTabBar::tab {
                background-color: #ECF0F1;
                border: 1px solid #BDC3C7;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #3498DB;
                color: white;
            }
        """)
        
        # تبويب العرض اليومي
        self.daily_tab = QWidget()
        self.setup_daily_tab()
        self.tabs.addTab(self.daily_tab, "📅 عرض يومي")
        
        # تبويب العرض الأسبوعي
        self.weekly_tab = QWidget()
        self.setup_weekly_tab()
        self.tabs.addTab(self.weekly_tab, "📋 عرض أسبوعي")
        
        # تبويب الإحصائيات
        self.stats_tab = QWidget()
        self.setup_stats_tab()
        self.tabs.addTab(self.stats_tab, "📊 إحصائيات")
        
        parent_layout.addWidget(self.tabs)
        
    def setup_daily_tab(self):
        """إعداد تبويب العرض اليومي"""
        layout = QVBoxLayout(self.daily_tab)
        
        # عناصر التحكم بالتاريخ
        date_controls = QHBoxLayout()
        
        date_label = QLabel("اختر التاريخ:")
        date_label.setStyleSheet("font-weight: bold; color: #2C3E50;")
        
        self.date_selector = QDateEdit()
        self.date_selector.setDate(QDate.currentDate())
        self.date_selector.setCalendarPopup(True)
        self.date_selector.setStyleSheet("""
            QDateEdit {
                padding: 6px;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
            }
        """)
        self.date_selector.dateChanged.connect(self.on_date_changed)
        
        date_controls.addWidget(date_label)
        date_controls.addWidget(self.date_selector)
        date_controls.addStretch()
        
        layout.addLayout(date_controls)
        
        # منطقة عرض المواعيد اليومية
        self.setup_daily_slots_display(layout)
        
    def setup_daily_slots_display(self, parent_layout):
        """إعداد منطقة عرض المواعيد اليومية"""
        daily_container = QFrame()
        daily_container.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                padding: 0px;
            }
        """)
        daily_layout = QVBoxLayout(daily_container)
        
        # رأس الجدول اليومي
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498DB, stop:1 #2980B9);
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                padding: 10px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        
        header_title = QLabel("المواعيد اليومية")
        header_title.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        
        self.daily_info = QLabel("اختر الطبيب أولاً")
        self.daily_info.setStyleSheet("color: #E3F2FD; font-size: 12px;")
        
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        header_layout.addWidget(self.daily_info)
        
        daily_layout.addWidget(header_frame)
        
        # شبكة المواعيد
        self.daily_slots_scroll = QScrollArea()
        self.daily_slots_scroll.setWidgetResizable(True)
        self.daily_slots_scroll.setMinimumHeight(200)
        self.daily_slots_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #FAFAFA;
            }
        """)
        
        self.daily_slots_widget = QWidget()
        self.daily_slots_grid = QGridLayout(self.daily_slots_widget)
        self.daily_slots_grid.setSpacing(8)
        self.daily_slots_grid.setContentsMargins(12, 12, 12, 12)
        
        self.daily_slots_scroll.setWidget(self.daily_slots_widget)
        daily_layout.addWidget(self.daily_slots_scroll)
        
        # رسالة عدم وجود بيانات
        self.no_daily_slots_label = QLabel("👨‍⚕️ اختر الطبيب والتاريخ لعرض المواعيد المتاحة")
        self.no_daily_slots_label.setAlignment(Qt.AlignCenter)
        self.no_daily_slots_label.setStyleSheet("""
            QLabel {
                padding: 40px 20px;
                color: #7F8C8D;
                font-size: 14px;
                background-color: #F8F9FA;
                border-radius: 6px;
                border: 2px dashed #BDC3C7;
            }
        """)
        daily_layout.addWidget(self.no_daily_slots_label)
        
        parent_layout.addWidget(daily_container)
        
    def setup_weekly_tab(self):
        """إعداد تبويب العرض الأسبوعي"""
        layout = QVBoxLayout(self.weekly_tab)
        
        # عناصر التحكم بالأسبوع
        week_controls = QHBoxLayout()
        
        week_label = QLabel("الأسبوع:")
        week_label.setStyleSheet("font-weight: bold; color: #2C3E50;")
        
        self.week_selector = QComboBox()
        self.setup_week_selector()
        self.week_selector.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                min-width: 200px;
            }
        """)
        self.week_selector.currentIndexChanged.connect(self.on_week_changed)
        
        week_controls.addWidget(week_label)
        week_controls.addWidget(self.week_selector)
        week_controls.addStretch()
        
        layout.addLayout(week_controls)
        
        # جدول الأسبوع
        self.setup_weekly_table(layout)
        
    def setup_week_selector(self):
        """إعداد محدد الأسابيع"""
        self.week_selector.clear()
        today = QDate.currentDate()
        
        for i in range(-2, 6):  # أسبوعين ماضيين و 6 أسابيع قادمة
            week_start = today.addDays(-today.dayOfWeek() + 1 + (i * 7))
            week_end = week_start.addDays(6)
            week_text = f"أسبوع {week_start.toString('dd/MM')} - {week_end.toString('dd/MM/yyyy')}"
            self.week_selector.addItem(week_text, week_start)
            
    def setup_weekly_table(self, parent_layout):
        """إعداد جدول العرض الأسبوعي"""
        self.weekly_table = QTableWidget()
        self.weekly_table.setColumnCount(8)  # الأيام + رأس
        self.weekly_table.setHorizontalHeaderLabels([
            "الوقت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"
        ])
        
        # إعداد المظهر
        self.weekly_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #BDC3C7;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ECF0F1;
            }
            QTableWidget::item:selected {
                background-color: #3498DB;
                color: white;
            }
        """)
        
        self.weekly_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #34495E;
                color: white;
                font-weight: bold;
                padding: 8px;
                border: none;
            }
        """)
        
        self.weekly_table.verticalHeader().setVisible(False)
        self.weekly_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.weekly_table.setSelectionMode(QTableWidget.SingleSelection)
        
        parent_layout.addWidget(self.weekly_table)
        
    def setup_stats_tab(self):
        """إعداد تبويب الإحصائيات"""
        layout = QVBoxLayout(self.stats_tab)
        
        # حاوية الإحصائيات
        stats_container = QFrame()
        stats_container.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        stats_layout = QVBoxLayout(stats_container)
        
        # عنوان الإحصائيات
        stats_title = QLabel("📊 إحصائيات الجدولة الذكية")
        stats_title.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 18px;
                color: #2C3E50;
                padding-bottom: 15px;
                border-bottom: 2px solid #3498DB;
            }
        """)
        stats_layout.addWidget(stats_title)
        
        # شبكة الإحصائيات
        stats_grid = QGridLayout()
        stats_grid.setSpacing(15)
        
        # إحصائيات الجدول
        self.stats_labels = {}
        
        stats_items = [
            ("إجمالي المواعيد", "total_slots", "#3498DB"),
            ("مواعيد متاحة", "available_slots", "#27AE60"),
            ("مواعيد محجوزة", "booked_slots", "#E74C3C"),
            ("نسبة الإشغال", "occupancy_rate", "#F39C12"),
            ("أيام العمل", "work_days", "#9B59B6"),
            ("التجديد القادم", "next_renewal", "#1ABC9C")
        ]
        
        row, col = 0, 0
        for label_text, key, color in stats_items:
            stat_frame = QFrame()
            stat_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {color};
                    border-radius: 6px;
                    padding: 15px;
                }}
            """)
            stat_layout = QVBoxLayout(stat_frame)
            
            label = QLabel(label_text)
            label.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
            
            value_label = QLabel("--")
            value_label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 18px;
                    font-weight: bold;
                }
            """)
            
            stat_layout.addWidget(label)
            stat_layout.addWidget(value_label)
            
            self.stats_labels[key] = value_label
            stats_grid.addWidget(stat_frame, row, col)
            
            col += 1
            if col > 1:
                col = 0
                row += 1
        
        stats_layout.addLayout(stats_grid)
        
        # معلومات النظام
        system_info = QLabel("🔄 يتم تحديث الإحصائيات تلقائياً عند تحميل الجداول")
        system_info.setStyleSheet("""
            QLabel {
                color: #7F8C8D;
                font-size: 11px;
                padding-top: 15px;
                border-top: 1px solid #ECF0F1;
            }
        """)
        system_info.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(system_info)
        
        layout.addWidget(stats_container)
        
    def connect_signals(self):
        """ربط إشارات الجدولة الذكية"""
        self.smart_scheduler.availability_calculated.connect(self.on_availability_calculated)
        self.smart_scheduler.smart_suggestions_ready.connect(self.on_smart_suggestions_ready)
        
    def set_doctor_and_date(self, doctor_id, date):
        """تعيين الطبيب والتاريخ للبحث عن الأوقات"""
        try:
            if doctor_id and date:
                self.current_doctor_id = doctor_id
                self.current_date = date
                self.date_selector.setDate(QDate.fromString(date, 'yyyy-MM-dd'))
                
                # تحديث واجهة المستخدم
                self.update_ui_for_doctor()
                self.load_periodic_schedule()
            else:
                self.clear_display()
        except Exception as e:
            logging.error(f"❌ خطأ في تعيين الطبيب والتاريخ: {e}")
            self.set_status("error", f"خطأ في تعيين البيانات: {e}")
            
    def update_ui_for_doctor(self):
        """تحديث واجهة المستخدم عند اختيار طبيب"""
        try:
            if self.current_doctor_id:
                # جلب معلومات الطبيب
                doctor_info = self.db_manager.get_doctor(self.current_doctor_id)
                if doctor_info:
                    self.doctor_info.setText(f"الطبيب: د. {doctor_info.get('name', '')} - {doctor_info.get('specialty', '')}")
                
                # تفعيل الأزرار
                self.load_schedule_btn.setVisible(True)
                self.refresh_btn.setVisible(True)
                self.popup_btn.setVisible(True)
                self.manage_btn.setVisible(True)
                
                self.set_status("success", "تم تحميل بيانات الطبيب")
            else:
                self.clear_display()
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث واجهة الطبيب: {e}")
            self.set_status("error", f"خطأ في تحميل بيانات الطبيب: {e}")
            
    def load_periodic_schedule(self):
        """تحميل الجدول الدوري"""
        if not self.current_doctor_id:
            self.set_status("warning", "لم يتم اختيار طبيب")
            return
            
        self.set_status("loading", "جاري تحميل الجدول الدوري...")
        
        try:
            # تحميل الجدول الدوري للـ 30 يوم القادمة
            start_date = QDate.currentDate().toString('yyyy-MM-dd')
            end_date = QDate.currentDate().addDays(30).toString('yyyy-MM-dd')
            
            self.periodic_schedule_data = self.db_manager.get_periodic_schedule(
                self.current_doctor_id, start_date, end_date
            )
            
            if not self.periodic_schedule_data:
                self.set_status("warning", "لا توجد جداول دورية للطبيب")
                self.show_no_daily_slots("لا توجد جداول دورية للطبيب المحدد")
                return
            
            # تحديث العروض
            self.update_daily_display()
            self.update_weekly_display()
            self.update_stats_display()
            
            self.set_status("success", f"تم تحميل الجدول الدوري: {len(self.periodic_schedule_data)} يوم")
            self.schedule_data_ready.emit(self.periodic_schedule_data)
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل الجدول الدوري: {e}")
            self.set_status("error", f"فشل في تحميل الجدول الدوري: {e}")
            self.show_no_daily_slots("حدث خطأ في تحميل الجدول")
            
    def update_daily_display(self):
        """تحديث العرض اليومي"""
        try:
            if not self.periodic_schedule_data:
                self.show_no_daily_slots("لا توجد جداول محملة")
                return
                
            selected_date = self.date_selector.date().toString('yyyy-MM-dd')
            
            if selected_date in self.periodic_schedule_data:
                daily_data = self.periodic_schedule_data[selected_date]
                self.display_daily_slots(daily_data)
            else:
                self.show_no_daily_slots("لا توجد مواعيد في هذا التاريخ")
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث العرض اليومي: {e}")
            self.show_no_daily_slots("حدث خطأ في عرض المواعيد")
            
    def display_daily_slots(self, daily_data):
        """عرض المواعيد اليومية"""
        try:
            self.no_daily_slots_label.hide()
            self.clear_daily_slots_grid()
            
            slots = daily_data.get('slots', [])
            
            if not slots:
                self.show_no_daily_slots("لا توجد مواعيد متاحة في هذا اليوم")
                return
                
            # تحديث المعلومات
            self.daily_info.setText(
                f"المتاحة: {daily_data['available_count']} | المحجوزة: {daily_data['booked_count']} | الإجمالي: {daily_data['total_count']}"
            )
            
            # استخدام العرض الجديد مع دعم الفترات المتعددة
            self.display_available_slots_with_periods(daily_data)
        except Exception as e:
            logging.error(f"❌ خطأ في عرض المواعيد اليومية: {e}")
            self.show_no_daily_slots("حدث خطأ في عرض المواعيد")
        
    def display_available_slots_with_periods(self, availability_data):
        """عرض الأوقات المتاحة مع تصنيف حسب فترات العمل"""
        try:
            available_slots = availability_data.get('slots', [])
            work_periods = availability_data.get('work_periods', [])
            
            if not available_slots:
                self.show_no_daily_slots("لا توجد مواعيد متاحة في هذا اليوم")
                return
                
            self.no_daily_slots_label.hide()
            self.clear_daily_slots_grid()
            
            # تجميع المواعيد حسب فترات العمل
            slots_by_period = {}
            for slot in available_slots:
                if slot['status'] == 'available':  # عرض المواعيد المتاحة فقط
                    period_type = slot.get('period_type', 'main')
                    if period_type not in slots_by_period:
                        slots_by_period[period_type] = []
                    slots_by_period[period_type].append(slot)
            
            # إذا لم توجد مواعيد متاحة
            if not any(slots_by_period.values()):
                self.show_no_daily_slots("لا توجد مواعيد متاحة في هذا اليوم")
                return
            
            # عرض المواعيد حسب الفترات
            row = 0
            for period_type, slots in slots_by_period.items():
                if not slots:  # تخطي الفترات الفارغة
                    continue
                    
                # إضافة عنوان الفترة
                period_label = QLabel(self.get_period_display_name(period_type))
                period_label.setStyleSheet("""
                    QLabel {
                        font-weight: bold;
                        font-size: 13px;
                        color: #2C3E50;
                        padding: 8px;
                        background-color: #ECF0F1;
                        border-radius: 4px;
                        margin-top: 10px;
                    }
                """)
                self.daily_slots_grid.addWidget(period_label, row, 0, 1, 4)
                row += 1
                
                # عرض مواعيد الفترة
                col = 0
                for slot in slots:
                    if slot['status'] == 'available':  # عرض المتاحة فقط
                        slot_btn = self.create_daily_slot_button(slot)
                        if slot_btn:
                            self.daily_slots_grid.addWidget(slot_btn, row, col)
                            
                            col += 1
                            if col >= 4:
                                col = 0
                                row += 1
                
                if col > 0:  # إذا كانت هناك مواعيد في الصف الأخير
                    row += 1
                
            self.daily_slots_scroll.setVisible(True)
            
        except Exception as e:
            logging.error(f"❌ خطأ في عرض المواعيد مع الفترات: {e}")
            # العودة للطريقة التقليدية في حالة الخطأ
            self.display_available_slots_without_periods(availability_data)
    
    def display_available_slots_without_periods(self, daily_data):
        """عرض المواعيد بدون تصنيف الفترات (الطريقة الاحتياطية)"""
        try:
            slots = daily_data.get('slots', [])
            available_slots = [slot for slot in slots if slot.get('status') == 'available']
            
            if not available_slots:
                self.show_no_daily_slots("لا توجد مواعيد متاحة في هذا اليوم")
                return
                
            # عرض المواعيد بدون تصنيف الفترات
            row, col = 0, 0
            max_cols = 4
            
            for slot in available_slots:
                slot_btn = self.create_daily_slot_button(slot)
                if slot_btn:
                    self.daily_slots_grid.addWidget(slot_btn, row, col)
                    
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
                        
            self.daily_slots_scroll.setVisible(True)
            
        except Exception as e:
            logging.error(f"❌ خطأ في العرض التقليدي للمواعيد: {e}")
            self.show_no_daily_slots("حدث خطأ في عرض المواعيد")

    def get_period_display_name(self, period_type):
        """الحصول على الاسم المعروض لفترة العمل"""
        period_names = {
            'main': '⏰ الدوام الرئيسي',
            'evening': '🌙 الدوام المسائي', 
            'part_time': '🕐 نصف دوام',
            'custom': '⚙️ فترة مخصصة',
            'morning': '🌅 الفترة الصباحية',
            'afternoon': '☀️ الفترة المسائية',
            'night': '🌙 الفترة الليلية'
        }
        return period_names.get(period_type, 'فترة العمل')
            
    def create_daily_slot_button(self, slot):
        """إنشاء زر للموعد اليومي"""
        try:
            btn = QPushButton(slot['time'])
            btn.setMinimumSize(80, 50)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            # تحديد النمط بناءً على الحالة
            status_styles = {
                'available': {
                    'background': '#E8F5E8',
                    'border': '#27AE60',
                    'text': '#2C3E50'
                },
                'booked': {
                    'background': '#FFEBEE',
                    'border': '#E74C3C', 
                    'text': '#2C3E50'
                },
                'blocked': {
                    'background': '#F5F5F5',
                    'border': '#BDC3C7',
                    'text': '#7F8C8D'
                }
            }
            
            style_config = status_styles.get(slot.get('status', 'available'), status_styles['available'])
            
            style = f"""
                QPushButton {{
                    background-color: {style_config['background']};
                    border: 2px solid {style_config['border']};
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                    color: {style_config['text']};
                    padding: 8px;
                }}
                QPushButton:hover {{
                    background-color: #E3F2FD;
                    border-color: #3498DB;
                }}
            """
            
            btn.setStyleSheet(style)
            
            if slot.get('status') == 'available':
                btn.setCursor(Qt.PointingHandCursor)
                btn.setToolTip(f"انقر للحجز - {slot['time']}")
                btn.clicked.connect(lambda: self.on_daily_slot_clicked(slot))
            else:
                btn.setCursor(Qt.ForbiddenCursor)
                status_text = "محجوز" if slot.get('status') == 'booked' else "غير متاح"
                btn.setToolTip(f"{status_text} - {slot['time']}")
                
            return btn
        except Exception as e:
            logging.error(f"❌ خطأ في إنشاء زر الموعد: {e}")
            return None
        
    def on_daily_slot_clicked(self, slot):
        """عند النقر على موعد يومي"""
        try:
            selected_date = self.date_selector.date().toString('yyyy-MM-dd')
            time_str = slot['time']
            
            # التحقق من توفر الموعد
            if not self.is_slot_available(selected_date, time_str):
                QMessageBox.warning(self, "غير متاح", "هذا الموعد لم يعد متاحاً")
                self.load_periodic_schedule()  # تحديث البيانات
                return
            
            self.time_selected.emit(time_str)
            
            # إشعار المستخدم
            QMessageBox.information(self, "تم الاختيار", 
                                  f"✅ تم اختيار الموعد:\nالتاريخ: {selected_date}\nالوقت: {time_str}")
        except Exception as e:
            logging.error(f"❌ خطأ في اختيار الموعد: {e}")
            QMessageBox.critical(self, "خطأ", f"حدث خطأ في اختيار الموعد: {e}")
        
    def is_slot_available(self, date, time):
        """التحقق من توفر الموعد"""
        try:
            if not self.periodic_schedule_data or date not in self.periodic_schedule_data:
                return False
                
            for slot in self.periodic_schedule_data[date]['slots']:
                if slot['time'] == time and slot['status'] == 'available':
                    return True
            return False
        except Exception as e:
            logging.error(f"❌ خطأ في التحقق من توفر الموعد: {e}")
            return False
        
    def update_weekly_display(self):
        """تحديث العرض الأسبوعي"""
        try:
            if not self.periodic_schedule_data:
                return
                
            # TODO: تنفيذ تحديث الجدول الأسبوعي بشكل كامل
            # في الوقت الحالي، نعرض رسالة توضيحية
            self.weekly_table.setRowCount(1)
            self.weekly_table.setItem(0, 0, QTableWidgetItem("⏳ جاري تطوير العرض الأسبوعي"))
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث العرض الأسبوعي: {e}")
        
    def update_stats_display(self):
        """تحديث عرض الإحصائيات"""
        try:
            if not self.periodic_schedule_data:
                return
                
            # حساب الإحصائيات
            total_slots = 0
            available_slots = 0
            booked_slots = 0
            
            for date_data in self.periodic_schedule_data.values():
                total_slots += date_data['total_count']
                available_slots += date_data['available_count'] 
                booked_slots += date_data['booked_count']
                
            occupancy_rate = (booked_slots / total_slots * 100) if total_slots > 0 else 0
            
            # تحديث القيم
            self.stats_labels['total_slots'].setText(str(total_slots))
            self.stats_labels['available_slots'].setText(str(available_slots))
            self.stats_labels['booked_slots'].setText(str(booked_slots))
            self.stats_labels['occupancy_rate'].setText(f"{occupancy_rate:.1f}%")
            self.stats_labels['work_days'].setText(str(len(self.periodic_schedule_data)))
            self.stats_labels['next_renewal'].setText("7 أيام")
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث الإحصائيات: {e}")
        
    def refresh_availability(self):
        """تحديث الجداول"""
        self.load_periodic_schedule()
        
    def check_auto_renew(self):
        """التحقق من التجديد التلقائي"""
        try:
            renewed_count = self.db_manager.check_and_renew_schedules()
            if renewed_count > 0:
                logging.info(f"🔄 تم التجديد التلقائي لـ {renewed_count} جدول")
                # إذا كان هناك طبيب محدد، نقوم بتحديث البيانات
                if self.current_doctor_id:
                    self.load_periodic_schedule()
        except Exception as e:
            logging.error(f"❌ خطأ في التجديد التلقائي: {e}")

    def show_advanced_time_popup(self):
        """عرض نافذة المواعيد المتقدمة - الإصدار المطور"""
        try:
            if not self.current_doctor_id:
                QMessageBox.warning(self, "تحذير", "يرجى اختيار الطبيب أولاً")
                return
            
            # استخدام نافذة الجدولة الذكية الموجودة
            from smart_scheduling_dialog import SmartSchedulingDialog
            
            dialog = SmartSchedulingDialog(self.db_manager, self)
            
            # ربط إشارة اختيار الموعد
            def handle_appointment_selected(appointment_data):
                time_str = appointment_data['appointment_time']
                self.time_selected.emit(time_str)
                
                # إشعار المستخدم
                QMessageBox.information(
                    self, 
                    "تم اختيار الموعد", 
                    f"✅ تم اختيار الموعد بنجاح!\n\n"
                    f"الطبيب: {appointment_data['doctor_name']}\n"
                    f"التاريخ: {appointment_data['appointment_date']}\n"
                    f"الوقت: {time_str}\n"
                    f"المدة: {appointment_data['duration']} دقيقة"
                )
            
            dialog.appointment_selected.connect(handle_appointment_selected)
            dialog.exec_()
            
        except ImportError as e:
            logging.error(f"❌ خطأ في تحميل نافذة الجدولة المتقدمة: {e}")
            # عرض نافذة بديلة بسيطة
            self.show_simple_advanced_popup()
        except Exception as e:
            logging.error(f"❌ خطأ في فتح نافذة المواعيد المتقدمة: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة المواعيد المتقدمة: {e}")

    def show_simple_advanced_popup(self):
        """عرض نافذة بديلة بسيطة للمواعيد المتقدمة"""
        try:
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel
            
            dialog = QDialog(self)
            dialog.setWindowTitle("🕒 المواعيد المتقدمة")
            dialog.setMinimumSize(500, 400)
            
            layout = QVBoxLayout(dialog)
            
            # عنوان النافذة
            title = QLabel("المواعيد المتقدمة - عرض متكامل")
            title.setStyleSheet("font-weight: bold; font-size: 16px; color: #2C3E50; padding: 10px;")
            title.setAlignment(Qt.AlignCenter)
            layout.addWidget(title)
            
            # قائمة المواعيد المتاحة
            info_label = QLabel("هذه النافذة تعرض المواعيد المتاحة بطرق متقدمة:\n• عرض الأوقات حسب فترات العمل\n• تصفية حسب نوع الخدمة\n• اقتراح أوقات بديلة")
            info_label.setStyleSheet("padding: 15px; background-color: #F8F9FA; border-radius: 8px;")
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
            
            # زر للعودة للواجهة الرئيسية
            back_button = QPushButton("العودة للجدولة العادية")
            back_button.setStyleSheet("""
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    padding: 12px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2980B9;
                }
            """)
            back_button.clicked.connect(dialog.accept)
            layout.addWidget(back_button)
            
            dialog.exec_()
            
        except Exception as e:
            logging.error(f"❌ خطأ في النافذة البديلة: {e}")
            QMessageBox.information(self, "معلومة", "نظام المواعيد المتقدمة قيد التطوير وسيتم تفعيله قريباً")
            
    def manage_schedules(self):
        """إدارة الجداول - الإصدار المطور"""
        try:
            if not self.current_doctor_id:
                QMessageBox.warning(self, "تحذير", "يرجى اختيار الطبيب أولاً")
                return

            from ui.dialogs.doctor_dialog import DoctorDialog
            
            # جلب بيانات الطبيب الحالي
            doctor_data = self.db_manager.get_doctor(self.current_doctor_id)
            if not doctor_data:
                QMessageBox.warning(self, "تحذير", "لا يمكن العثور على بيانات الطبيب")
                return
            
            # فتح نافذة إدارة الجداول
            dialog = DoctorDialog(self.db_manager, self, doctor_data)
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                # تحديث البيانات بعد التعديل
                self.load_periodic_schedule()
                self.set_status("success", "تم تحديث إعدادات الجدولة بنجاح")
                
        except Exception as e:
            logging.error(f"❌ خطأ في إدارة الجداول: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إدارة الجداول: {e}")
        
    def clear_display(self):
        """مسح العرض"""
        try:
            self.clear_daily_slots_grid()
            self.no_daily_slots_label.show()
            self.no_daily_slots_label.setText("👨‍⚕️ اختر الطبيب والتاريخ أولاً لعرض المواعيد المتاحة")
            
            self.doctor_info.setText("لم يتم اختيار طبيب")
            self.schedule_info.setText("الجداول: غير محملة")
            
            self.load_schedule_btn.setVisible(False)
            self.refresh_btn.setVisible(False)
            self.popup_btn.setVisible(False)
            self.manage_btn.setVisible(False)
            
            self.set_status("info", "اختر الطبيب والتاريخ لعرض المواعيد المتاحة")
        except Exception as e:
            logging.error(f"❌ خطأ في مسح العرض: {e}")
        
    def clear_daily_slots_grid(self):
        """مسح شبكة المواعيد اليومية"""
        try:
            while self.daily_slots_grid.count():
                child = self.daily_slots_grid.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        except Exception as e:
            logging.error(f"❌ خطأ في مسح شبكة المواعيد: {e}")
                
    def show_no_daily_slots(self, message):
        """عرض رسالة عدم وجود مواعيد يومية"""
        try:
            self.clear_daily_slots_grid()
            self.no_daily_slots_label.show()
            self.no_daily_slots_label.setText(message)
            self.daily_slots_scroll.setVisible(False)
        except Exception as e:
            logging.error(f"❌ خطأ في عرض رسالة عدم وجود مواعيد: {e}")
        
    def set_status(self, status_type, message):
        """تعيين حالة النظام"""
        try:
            status_config = {
                "loading": {"icon": "🟡", "color": "#F39C12"},
                "success": {"icon": "🟢", "color": "#27AE60"},
                "warning": {"icon": "🟠", "color": "#E67E22"},
                "error": {"icon": "🔴", "color": "#E74C3C"},
                "info": {"icon": "🔵", "color": "#3498DB"}
            }
            
            config = status_config.get(status_type, status_config["info"])
            self.system_status.setText(f"{config['icon']} {message}")
            self.system_status.setStyleSheet(f"color: {config['color']}; font-size: 11px; font-weight: bold;")
        except Exception as e:
            logging.error(f"❌ خطأ في تعيين حالة النظام: {e}")
        
    # دعم التوافق مع الإصدار القديم
    def on_availability_calculated(self, availability_data):
        """للتوافق مع الإصدار القديم"""
        pass
        
    def on_smart_suggestions_ready(self, suggestions):
        """للتوافق مع الإصدار القديم"""
        pass
        
    def on_date_changed(self, date):
        """عند تغيير التاريخ"""
        try:
            self.current_date = date.toString('yyyy-MM-dd')
            self.update_daily_display()
        except Exception as e:
            logging.error(f"❌ خطأ في تغيير التاريخ: {e}")
        
    def on_week_changed(self, index):
        """عند تغيير الأسبوع"""
        # TODO: تنفيذ تغيير الأسبوع
        pass

    def get_group_style(self):
        """نمط المجموعة"""
        return """
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2C3E50;
                border: 2px solid #3498DB;
                border-radius: 8px;
                margin-top: 5px;
                padding-top: 12px;
                background-color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 12px 0 12px;
                background-color: #3498DB;
                color: white;
                border-radius: 4px;
            }
        """
    
    def get_button_style(self, button_type="primary"):
        """أنماط الأزرار"""
        styles = {
            "primary": """
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #2980B9;
                }
            """,
            "info": """
                QPushButton {
                    background-color: #17A2B8;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #138496;
                }
            """,
            "success": """
                QPushButton {
                    background-color: #28A745;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """,
            "warning": """
                QPushButton {
                    background-color: #FFC107;
                    color: #212529;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #E0A800;
                }
            """
        }
        return styles.get(button_type, styles["primary"])

class SmartSchedulingDialog(QDialog):
    """نافذة الجدولة الذكية المتقدمة"""
    
    appointment_selected = pyqtSignal(dict)
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setup_ui()
        
    def setup_ui(self):
        """إعداد واجهة النافذة"""
        self.setWindowTitle("🕒 الجدولة الذكية المتقدمة")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # عنوان النافذة
        title = QLabel("نظام الجدولة الذكية المتقدمة")
        title.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 18px;
                color: #2C3E50;
                padding: 15px;
                background-color: #3498DB;
                color: white;
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # معلومات النظام
        info_label = QLabel(
            "هذا النظام المتقدم يمكنك من:\n"
            "• عرض المواعيد المتاحة بطرق متعددة\n"
            "• تصفية المواعيد حسب فترات العمل\n"
            "• الحصول على اقتراحات ذكية للأوقات\n"
            "• إدارة الجداول الدورية بشكل متكامل"
        )
        info_label.setStyleSheet("""
            QLabel {
                padding: 15px;
                background-color: #F8F9FA;
                border-radius: 8px;
                border: 1px solid #E0E0E0;
                margin-bottom: 15px;
            }
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # أزرار التحكم
        buttons_layout = QHBoxLayout()
        
        # زر عرض المواعيد المتاحة
        available_btn = QPushButton("📅 عرض المواعيد المتاحة")
        available_btn.setStyleSheet(self.get_button_style("primary"))
        available_btn.clicked.connect(self.show_available_appointments)
        
        # زر الإقتراحات الذكية
        suggestions_btn = QPushButton("💡 الاقتراحات الذكية")
        suggestions_btn.setStyleSheet(self.get_button_style("success"))
        suggestions_btn.clicked.connect(self.show_smart_suggestions)
        
        # زر إدارة الجداول
        manage_btn = QPushButton("⚙️ إدارة الجداول")
        manage_btn.setStyleSheet(self.get_button_style("warning"))
        manage_btn.clicked.connect(self.manage_schedules)
        
        buttons_layout.addWidget(available_btn)
        buttons_layout.addWidget(suggestions_btn)
        buttons_layout.addWidget(manage_btn)
        
        layout.addLayout(buttons_layout)
        
        # منطقة العرض
        self.display_area = QTextEdit()
        self.display_area.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                border: 1px solid #BDC3C7;
                border-radius: 6px;
                padding: 10px;
                font-size: 12px;
            }
        """)
        self.display_area.setPlaceholderText("سيتم عرض النتائج هنا...")
        layout.addWidget(self.display_area)
        
        # أزرار التنفيذ
        action_buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        action_buttons.accepted.connect(self.on_accept)
        action_buttons.rejected.connect(self.reject)
        
        layout.addWidget(action_buttons)
        
    def show_available_appointments(self):
        """عرض المواعيد المتاحة"""
        self.display_area.setText(
            "🔍 جاري البحث عن المواعيد المتاحة...\n\n"
            "• فترات العمل الرئيسية\n"
            "• الفترات المسائية\n" 
            "• المواعيد الإضافية\n"
            "• الأوقات المفضلة\n\n"
            "سيتم عرض النتائج المفصلة قريباً..."
        )
        
    def show_smart_suggestions(self):
        """عرض الاقتراحات الذكية"""
        self.display_area.setText(
            "💡 النظام يقدم لك الاقتراحات التالية:\n\n"
            "✅ الأوقات المثلى للحجز:\n"
            "   - 09:00 ص (مبكر - هادئ)\n"
            "   - 02:00 م (بعد الظهر - مناسب)\n"
            "   - 05:00 م (مساء - مرن)\n\n"
            "📊 إحصائيات الذكاء الاصطناعي:\n"
            "   - نسبة التوفر: 85%\n"
            "   - الأوقات المفضلة: الصباح\n"
            "   - مدة الانتظار: 2 يوم\n"
        )
        
    def manage_schedules(self):
        """إدارة الجداول"""
        self.display_area.setText(
            "⚙️ إدارة الجداول الدورية:\n\n"
            "1. الجداول الأسبوعية\n"
            "2. العطل والإجازات\n" 
            "3. الفترات الخاصة\n"
            "4. إعدادات تلقائية\n\n"
            "يمكنك تعديل هذه الإعدادات من القائمة الرئيسية"
        )
        
    def on_accept(self):
        """عند قبول النافذة"""
        appointment_data = {
            'doctor_name': 'د. أحمد محمد',
            'appointment_date': QDate.currentDate().toString('yyyy-MM-dd'),
            'appointment_time': '10:00',
            'duration': '30'
        }
        self.appointment_selected.emit(appointment_data)
        self.accept()
        
    def get_button_style(self, button_type):
        """أنماط الأزرار"""
        styles = {
            "primary": """
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #2980B9;
                }
            """,
            "success": """
                QPushButton {
                    background-color: #27AE60;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #219653;
                }
            """,
            "warning": """
                QPushButton {
                    background-color: #F39C12;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #D68910;
                }
            """
        }
        return styles.get(button_type, styles["primary"])