# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
                             QMessageBox, QHeaderView, QLabel, QToolBar, QAction,
                             QDialog, QMenu, QTabWidget, QTextEdit, QDateEdit, 
                             QGroupBox, QFormLayout, QListWidget, QSplitter, 
                             QFrame, QScrollArea, QToolButton, QDialogButtonBox,
                             QApplication, QInputDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QDate, QTimer, QSize
from PyQt5.QtGui import QIcon, QFont, QColor, QBrush, QPalette
import logging
import traceback
from datetime import datetime

class PatientsManager(QWidget):
    data_updated = pyqtSignal()
    
    def __init__(self, db_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.current_patient_id = None
        self._loading = False
        
        # تهيئة العناصر أولاً
        self.initialize_ui_elements()
        
        try:
            self.setup_ui()
            QTimer.singleShot(100, self.load_patients)
        except Exception as e:
            logging.error(f"خطأ في تهيئة PatientsManager: {e}")
            self.show_error(f"خطأ في التهيئة: {str(e)}")

    def initialize_ui_elements(self):
        """تهيئة عناصر الواجهة بشكل آمن"""
        try:
            # تهيئة الأزرار
            self.edit_button = None
            self.delete_button = None
            self.manage_tags_button = None
            self.add_button = None
            self.refresh_button = None
            
            # تهيئة تسميات التفاصيل
            self.detail_labels = {}
            
            # تهيئة عناصر الواجهة الأخرى
            self.patients_table = None
            self.search_input = None
            self.tag_filter = None
            self.gender_filter = None
            self.details_tabs = None
            self.appointments_list = None
            self.medical_history_list = None
            self.upcoming_appointments_list = None
            self.stats_labels = {}
            
            logging.info("✅ تم تهيئة عناصر الواجهة بنجاح")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تهيئة عناصر الواجهة: {e}")

    def setup_ui(self):
        """إعداد واجهة المستخدم مع التنسيق الجمالي"""
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', 'Tahoma', 'Arial';
                font-size: 9pt;
            }
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: #f8f9fa;
            }
            QTabBar::tab {
                background-color: #e9ecef;
                border: 1px solid #c0c0c0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #007bff;
                color: white;
                border-bottom: 2px solid #0056b3;
            }
            QTabBar::tab:hover {
                background-color: #dee2e6;
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # شريط الأدوات
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)
        
        # شريط البحث
        search_layout = self.create_search_bar()
        main_layout.addLayout(search_layout)
        
        # تقسيم الشاشة
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dee2e6;
                width: 4px;
                border-radius: 2px;
            }
            QSplitter::handle:hover {
                background-color: #adb5bd;
            }
        """)
        
        # اللوحة اليسرى: قائمة المرضى
        left_panel = self.create_patients_list_panel()
        splitter.addWidget(left_panel)
        
        # اللوحة اليمنى: تفاصيل المريض
        right_panel = self.create_patient_details_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([400, 600])
        main_layout.addWidget(splitter)
        
        self.setLayout(main_layout)

    def create_toolbar(self):
        """إنشاء شريط أدوات مخصص"""
        toolbar = QToolBar()
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 5px;
                spacing: 5px;
            }
            QToolButton {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 6px 12px;
                color: #495057;
            }
            QToolButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QToolButton:pressed {
                background-color: #dee2e6;
            }
            QToolButton:disabled {
                background-color: #f8f9fa;
                color: #6c757d;
                border-color: #dee2e6;
            }
        """)
        
        # إنشاء الأزرار مع أيقونات
        self.add_button = QAction("➕ إضافة مريض", self)
        self.add_button.triggered.connect(self.add_patient)
        
        self.edit_button = QAction("✏️ تعديل", self)
        self.edit_button.triggered.connect(self.safe_edit_patient)
        self.edit_button.setEnabled(False)
        
        self.delete_button = QAction("🗑️ حذف", self)
        self.delete_button.triggered.connect(self.safe_delete_patient)
        self.delete_button.setEnabled(False)
        
        self.manage_tags_button = QAction("🏷️ إدارة العلامات", self)
        self.manage_tags_button.triggered.connect(self.manage_patient_tags)
        self.manage_tags_button.setEnabled(False)
        
        self.refresh_button = QAction("🔄 تحديث", self)
        self.refresh_button.triggered.connect(self.safe_load_patients)
        
        # إضافة الأزرار إلى الشريط
        toolbar.addAction(self.add_button)
        toolbar.addAction(self.edit_button)
        toolbar.addAction(self.delete_button)
        toolbar.addAction(self.manage_tags_button)
        toolbar.addAction(self.refresh_button)
        
        return toolbar

    def create_search_bar(self):
        """إنشاء شريط البحث بتنسيق جميل"""
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        
        # حقل البحث
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 ابحث بالاسم أو الهاتف...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #ced4da;
                border-radius: 6px;
                background-color: white;
                font-size: 9pt;
            }
            QLineEdit:focus {
                border-color: #007bff;
                box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
            }
            QLineEdit:hover {
                border-color: #adb5bd;
            }
        """)
        self.search_input.textChanged.connect(self.debounced_search)
        
        # فلتر العلامات
        self.tag_filter = QComboBox()
        self.tag_filter.addItem("🏷️ جميع العلامات")
        self.tag_filter.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #ced4da;
                border-radius: 6px;
                background-color: white;
                min-width: 120px;
            }
            QComboBox:hover {
                border-color: #adb5bd;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #495057;
                width: 0px;
                height: 0px;
            }
        """)
        self.tag_filter.currentTextChanged.connect(self.safe_filter_by_tag)
        
        # فلتر الجنس
        self.gender_filter = QComboBox()
        self.gender_filter.addItems(["👥 جميع الجنس", "👦 ذكر", "👧 أنثى"])
        self.gender_filter.setStyleSheet(self.tag_filter.styleSheet())
        self.gender_filter.currentTextChanged.connect(self.safe_filter_patients)
        
        search_layout.addWidget(QLabel("بحث:"))
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(QLabel("العلامة:"))
        search_layout.addWidget(self.tag_filter)
        search_layout.addWidget(QLabel("الجنس:"))
        search_layout.addWidget(self.gender_filter)
        
        return search_layout

    def debounced_search(self):
        """بحث مع تأخير لتجنب التكرار"""
        if hasattr(self, '_search_timer'):
            self._search_timer.stop()
        
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self.safe_search_patients)
        self._search_timer.start(300)

    def safe_search_patients(self):
        """بحث آمن مع معالجة الأخطاء"""
        try:
            if self._loading:
                return
                
            search_term = self.search_input.text().strip()
            self.load_patients(search_term if search_term else None)
        except Exception as e:
            self.show_error(f"خطأ في البحث: {str(e)}")

    def safe_filter_by_tag(self, tag):
        """تصفية آمنة بالعلامات"""
        try:
            if self._loading:
                return
                
            if tag == "🏷️ جميع العلامات":
                self.load_patients()
            else:
                # إزالة الإيموجي من النص للبحث
                clean_tag = tag.replace("🏷️ ", "")
                patients = self.db_manager.get_patients_by_tag(clean_tag)
                self.display_patients(patients)
        except Exception as e:
            self.show_error(f"خطأ في التصفية بالعلامات: {str(e)}")

    def safe_filter_patients(self):
        """تصفية آمنة بالجنس"""
        try:
            if self._loading:
                return
                
            gender = self.gender_filter.currentText()
            if gender == "👥 جميع الجنس":
                self.load_patients()
            else:
                # إزالة الإيموجي من النص للبحث
                clean_gender = gender.replace("👦 ", "").replace("👧 ", "")
                patients = self.db_manager.get_patients()
                filtered_patients = [p for p in patients if p.get('gender') == clean_gender]
                self.display_patients(filtered_patients)
        except Exception as e:
            self.show_error(f"خطأ في التصفية بالجنس: {str(e)}")

    def create_patients_list_panel(self):
        """إنشاء لوحة قائمة المرضى بتنسيق جميل"""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        
        title = QLabel("👥 قائمة المرضى")
        title.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                padding: 10px;
                background-color: #e9ecef;
                border-radius: 6px;
                margin-bottom: 5px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        self.patients_table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.patients_table)
        
        return panel

    def setup_table(self):
        """إعداد جدول المرضى بتنسيق جميل"""
        self.patients_table.setColumnCount(6)
        self.patients_table.setHorizontalHeaderLabels([
            "#", "👤 الاسم", "📞 الهاتف", "📧 البريد", "⚧ الجنس", "🏷️ العلامات"
        ])
        
        # تنسيق رأس الجدول
        self.patients_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                gridline-color: #dee2e6;
                font-size: 9pt;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f3f4;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 10px 8px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
                color: #495057;
            }
            QTableWidget QScrollBar:vertical {
                background-color: #f1f3f4;
                width: 12px;
                border-radius: 6px;
            }
            QTableWidget QScrollBar::handle:vertical {
                background-color: #c1c1c1;
                border-radius: 6px;
                min-height: 20px;
            }
            QTableWidget QScrollBar::handle:vertical:hover {
                background-color: #a8a8a8;
            }
        """)
        
        header = self.patients_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # توسيع عمود الاسم
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # عمود ID
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # عمود الهاتف
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # عمود البريد
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # عمود الجنس
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # عمود العلامات
        
        self.patients_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.patients_table.setAlternatingRowColors(True)
        self.patients_table.setSortingEnabled(True)
        self.patients_table.doubleClicked.connect(self.safe_edit_patient)
        
        # إضافة متابعة اختيار الصفوف
        self.patients_table.itemSelectionChanged.connect(self.on_patient_selection_changed)
        
        self.patients_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.patients_table.customContextMenuRequested.connect(self.safe_show_context_menu)

    def create_patient_details_panel(self):
        """إنشاء لوحة تفاصيل المريض بتنسيق جميل"""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        
        title = QLabel("📋 تفاصيل المريض")
        title.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                padding: 10px;
                background-color: #e9ecef;
                border-radius: 6px;
                margin-bottom: 5px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        self.details_tabs = QTabWidget()
        self.details_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: #ffffff;
                border-radius: 6px;
            }
            QTabBar::tab {
                background-color: #e9ecef;
                border: 1px solid #c0c0c0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #007bff;
                color: white;
                border-bottom: 2px solid #0056b3;
            }
            QTabBar::tab:hover {
                background-color: #dee2e6;
            }
        """)
        
        basic_info_tab = self.create_basic_info_tab()
        self.details_tabs.addTab(basic_info_tab, "📄 المعلومات الأساسية")
        
        history_tab = self.create_history_tab()
        self.details_tabs.addTab(history_tab, "📊 السجل")
        
        stats_tab = self.create_stats_tab()
        self.details_tabs.addTab(stats_tab, "📈 الإحصائيات")
        
        layout.addWidget(self.details_tabs)
        
        return panel

    def create_basic_info_tab(self):
        """إنشاء تبويب المعلومات الأساسية بتنسيق جميل"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 6px;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # مجموعة المعلومات الشخصية
        personal_group = QGroupBox("👤 المعلومات الشخصية")
        personal_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #f8f9fa;
            }
        """)
        personal_layout = QFormLayout(personal_group)
        personal_layout.setSpacing(12)
        personal_layout.setContentsMargins(15, 20, 15, 15)
        
        fields = [
            ('name', '👤 الاسم الكامل:'),
            ('phone', '📞 رقم الهاتف:'),
            ('email', '📧 البريد الإلكتروني:'),
            ('birth_date', '📅 تاريخ الميلاد:'),
            ('gender', '⚧ الجنس:'),
            ('address', '🏠 العنوان:'),
            ('emergency_contact', '🚨 جهة اتصال الطوارئ:'),
            ('insurance', '🏥 معلومات التأمين:'),
            ('medical_history', '📝 التاريخ المرضي:'),
            ('whatsapp_consent', '💬 موافقة واتساب:'),
            ('tags', '🏷️ العلامات:')
        ]
        
        for field, label in fields:
            self.detail_labels[field] = QLabel("غير محدد")
            self.detail_labels[field].setStyleSheet("""
                QLabel {
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 4px;
                    padding: 8px 12px;
                    color: #495057;
                    min-height: 15px;
                }
            """)
            self.detail_labels[field].setTextInteractionFlags(Qt.TextSelectableByMouse)
            personal_layout.addRow(QLabel(label), self.detail_labels[field])
        
        layout.addWidget(personal_group)
        layout.addStretch()
        
        return widget

    def create_history_tab(self):
        """إنشاء تبويب السجل التاريخي مع بيانات حقيقية"""
        widget = QScrollArea()
        widget.setStyleSheet("""
            QScrollArea {
                background-color: white;
                border-radius: 6px;
            }
        """)
        content = QWidget()
        content.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # المواعيد القادمة
        upcoming_appointments_group = QGroupBox("📅 المواعيد القادمة")
        upcoming_appointments_group.setStyleSheet(self.get_group_box_style())
        upcoming_layout = QVBoxLayout(upcoming_appointments_group)
        self.upcoming_appointments_list = QListWidget()
        self.upcoming_appointments_list.setStyleSheet(self.get_list_style())
        upcoming_layout.addWidget(self.upcoming_appointments_list)
        layout.addWidget(upcoming_appointments_group)
        
        # المواعيد السابقة
        appointments_group = QGroupBox("📋 المواعيد السابقة")
        appointments_group.setStyleSheet(self.get_group_box_style())
        appointments_layout = QVBoxLayout(appointments_group)
        self.appointments_list = QListWidget()
        self.appointments_list.setStyleSheet(self.get_list_style())
        appointments_layout.addWidget(self.appointments_list)
        layout.addWidget(appointments_group)
        
        # السجل الطبي
        medical_group = QGroupBox("🏥 السجل الطبي")
        medical_group.setStyleSheet(self.get_group_box_style())
        medical_layout = QVBoxLayout(medical_group)
        self.medical_history_list = QListWidget()
        self.medical_history_list.setStyleSheet(self.get_list_style())
        medical_layout.addWidget(self.medical_history_list)
        layout.addWidget(medical_group)
        
        # إضافة رسالة عندما لا توجد بيانات
        self.setup_empty_lists()
        
        widget.setWidget(content)
        widget.setWidgetResizable(True)
        
        return widget

    def get_group_box_style(self):
        """تنسيق مجموعة العناصر"""
        return """
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #f8f9fa;
            }
        """

    def get_list_style(self):
        """تنسيق القوائم"""
        return """
            QListWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 5px;
                font-size: 9pt;
            }
            QListWidget::item {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 8px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                border: 1px solid #2196f3;
            }
            QListWidget::item:hover {
                background-color: #f1f3f4;
            }
        """

    def setup_empty_lists(self):
        """إعداد القوائم الفارغة برسائل مناسبة"""
        empty_message = "📭 لا توجد بيانات لعرضها"
        
        # المواعيد القادمة
        if self.upcoming_appointments_list:
            self.upcoming_appointments_list.clear()
            self.upcoming_appointments_list.addItem(empty_message)
        
        # المواعيد السابقة
        if self.appointments_list:
            self.appointments_list.clear()
            self.appointments_list.addItem(empty_message)
        
        # السجل الطبي
        if self.medical_history_list:
            self.medical_history_list.clear()
            self.medical_history_list.addItem(empty_message)

    def create_stats_tab(self):
        """إنشاء تبويب الإحصائيات بتنسيق جميل"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 6px;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        stats_group = QGroupBox("📈 إحصائيات المريض")
        stats_group.setStyleSheet(self.get_group_box_style())
        stats_layout = QFormLayout(stats_group)
        stats_layout.setSpacing(15)
        stats_layout.setContentsMargins(20, 25, 20, 20)
        
        stats_fields = [
            ('total_appointments', '📊 إجمالي المواعيد:'),
            ('completed_appointments', '✅ المواعيد المنتهية:'),
            ('first_appointment', '📅 أول موعد:'),
            ('last_appointment', '📆 آخر موعد:'),
            ('medical_records', '🏥 السجلات الطبية:')
        ]
        
        for field, label in stats_fields:
            self.stats_labels[field] = QLabel("0")
            self.stats_labels[field].setStyleSheet("""
                QLabel {
                    background-color: #e3f2fd;
                    border: 2px solid #2196f3;
                    border-radius: 6px;
                    padding: 10px 15px;
                    font-weight: bold;
                    font-size: 11pt;
                    color: #1976d2;
                    min-width: 80px;
                    text-align: center;
                }
            """)
            stats_layout.addRow(QLabel(label), self.stats_labels[field])
        
        layout.addWidget(stats_group)
        layout.addStretch()
        
        return widget

    def safe_load_patients(self, search_term=None):
        """تحميل آمن للمرضى"""
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self._loading = True
            self.load_patients(search_term)
        except Exception as e:
            self.show_error(f"خطأ في تحميل المرضى: {str(e)}")
        finally:
            self._loading = False
            QApplication.restoreOverrideCursor()

    def load_patients(self, search_term=None):
        """تحميل قائمة المرضى"""
        try:
            if not self.db_manager:
                logging.error("مدير قاعدة البيانات غير متوفر")
                return
                
            patients = self.db_manager.get_patients(search_term)
            self.display_patients(patients)
            self.update_tag_filter()
            
        except Exception as e:
            logging.error(f"خطأ في تحميل المرضى: {e}")
            self.show_error(f"فشل في تحميل قائمة المرضى: {str(e)}")

    def display_patients(self, patients):
        """عرض المرضى في الجدول"""
        try:
            if not self.patients_table:
                logging.error("جدول المرضى غير مهيأ")
                return
                
            self.patients_table.setRowCount(len(patients))
            
            for row, patient in enumerate(patients):
                # الحصول على العلامات للمريض
                tags = []
                if self.db_manager:
                    tags = self.db_manager.get_patient_tags(patient['id'])
                tags_text = " ".join([f"🏷️{tag}" for tag in tags]) if tags else "لا توجد علامات"
                
                # تنسيق الجنس
                gender_icon = "👦" if patient.get('gender') == 'ذكر' else "👧" if patient.get('gender') == 'أنثى' else "❓"
                gender_text = f"{gender_icon} {patient.get('gender', '')}"
                
                items = [
                    QTableWidgetItem(str(patient.get('id', ''))),
                    QTableWidgetItem(patient.get('name', '')),
                    QTableWidgetItem(patient.get('phone', '')),
                    QTableWidgetItem(patient.get('email', '')),
                    QTableWidgetItem(gender_text),
                    QTableWidgetItem(tags_text)
                ]
                
                for col, item in enumerate(items):
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    # تنسيق العناصر
                    if col == 0:  # عمود ID
                        item.setTextAlignment(Qt.AlignCenter)
                    self.patients_table.setItem(row, col, item)
            
        except Exception as e:
            logging.error(f"خطأ في عرض المرضى: {e}")

    def update_tag_filter(self):
        """تحديث قائمة العلامات"""
        try:
            if not self.tag_filter:
                logging.error("فلتر العلامات غير مهيأ")
                return
                
            current_text = self.tag_filter.currentText()
            self.tag_filter.blockSignals(True)
            self.tag_filter.clear()
            self.tag_filter.addItem("🏷️ جميع العلامات")
            
            # استخدام الدالة الصحيحة من DatabaseManager
            tags = []
            if self.db_manager:
                tags = self.db_manager.get_all_patient_tags()
            for tag in tags:
                self.tag_filter.addItem(f"🏷️ {tag}")
            
            # استعادة التحديد السابق
            index = self.tag_filter.findText(current_text)
            if index >= 0:
                self.tag_filter.setCurrentIndex(index)
            self.tag_filter.blockSignals(False)
            
        except Exception as e:
            logging.error(f"خطأ في تحديث العلامات: {e}")
            if self.tag_filter:
                self.tag_filter.blockSignals(False)

    def on_patient_selection_changed(self):
        """عند تغيير اختيار المريض"""
        try:
            # استخدام Timer لتأخير التحديث وتجنب المشاكل
            QTimer.singleShot(100, self.safe_update_ui_elements)
            
            # عرض التفاصيل إذا كان هناك مريض محدد
            patient_id = self.get_selected_patient_id()
            if patient_id:
                QTimer.singleShot(150, self.safe_show_patient_details)
                
        except Exception as e:
            logging.error(f"خطأ في اختيار المريض: {e}")

    def safe_update_ui_elements(self):
        """تحديث عناصر الواجهة بشكل آمن"""
        try:
            patient_id = self.get_selected_patient_id()
            has_selection = patient_id is not None
            
            # تحديث الأزرار بشكل آمن
            if self.edit_button:
                self.edit_button.setEnabled(has_selection)
            if self.delete_button:
                self.delete_button.setEnabled(has_selection)
            if self.manage_tags_button:
                self.manage_tags_button.setEnabled(has_selection)
                
        except Exception as e:
            logging.error(f"خطأ في تحديث عناصر الواجهة: {e}")

    def safe_show_context_menu(self, position):
        """عرض قائمة السياق الآمنة"""
        try:
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: white;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    padding: 5px;
                }
                QMenu::item {
                    padding: 8px 20px 8px 10px;
                    border-radius: 4px;
                }
                QMenu::item:selected {
                    background-color: #e3f2fd;
                    color: #1976d2;
                }
            """)
            
            patient_data = self.get_selected_patient_data()
            if not patient_data:
                return
            
            menu.addAction("👁️ عرض التفاصيل", self.safe_show_patient_details)
            menu.addAction("✏️ تعديل البيانات", self.safe_edit_patient)
            menu.addAction("🏷️ إدارة العلامات", self.manage_patient_tags)
            menu.addSeparator()
            menu.addAction("🗑️ حذف المريض", self.safe_delete_patient)
            
            menu.exec_(self.patients_table.viewport().mapToGlobal(position))
        except Exception as e:
            self.show_error(f"خطأ في القائمة: {str(e)}")

    def get_selected_patient_data(self):
        """الحصول على بيانات المريض المحدد"""
        try:
            patient_id = self.get_selected_patient_id()
            if patient_id is None:
                return None
            
            patient = None
            if self.db_manager:
                patient = self.db_manager.get_patient_by_id(patient_id)
            if patient:
                # إضافة العلامات لبيانات المريض
                tags = []
                if self.db_manager:
                    tags = self.db_manager.get_patient_tags(patient_id)
                patient['patient_tags'] = tags
                return patient
            return None
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على بيانات المريض: {e}")
            return None

    def get_selected_patient_id(self):
        """الحصول على رقم المريض المحدد"""
        try:
            if not self.patients_table:
                return None
                
            selected_items = self.patients_table.selectedItems()
            if not selected_items:
                return None
            
            item = self.patients_table.item(selected_items[0].row(), 0)
            if item and item.text().strip():
                return int(item.text())
            return None
        except (ValueError, TypeError) as e:
            logging.error(f"خطأ في تحويل ID المريض: {e}")
            return None

    def safe_show_patient_details(self):
        """عرض تفاصيل المريض بشكل آمن"""
        try:
            patient = self.get_selected_patient_data()
            if not patient:
                QMessageBox.warning(self, "تحذير", "يرجى اختيار مريض لعرض التفاصيل")
                return
            
            # التحقق من تهيئة عناصر الواجهة قبل الاستخدام
            if not hasattr(self, 'detail_labels') or not self.detail_labels:
                logging.error("عناصر الواجهة غير مهيأة")
                return
                
            self.show_patient_details(patient)
        except Exception as e:
            logging.error(f"خطأ في عرض التفاصيل: {str(e)}")
            self.show_error(f"خطأ في عرض التفاصيل: {str(e)}")

    def show_patient_details(self, patient):
        """عرض تفاصيل المريض"""
        try:
            # التحقق من وجود المريض وبياناته
            if not patient:
                logging.warning("بيانات المريض غير متوفرة")
                return
                
            # التحقق من وجود تسميات التفاصيل
            if not hasattr(self, 'detail_labels') or not self.detail_labels:
                logging.error("تسميات التفاصيل غير مهيأة")
                return
            
            # قائمة الحقول المطلوبة
            fields_mapping = {
                'name': ('name', 'غير محدد'),
                'phone': ('phone', 'غير محدد'),
                'email': ('email', 'غير محدد'),
                'birth_date': ('date_of_birth', 'غير محدد'),
                'gender': ('gender', 'غير محدد'),
                'address': ('address', 'غير محدد'),
                'emergency_contact': ('emergency_contact', 'غير محدد'),
                'insurance': ('insurance_info', 'غير محدد'),
                'medical_history': ('medical_history', 'لا توجد معلومات'),
                'whatsapp_consent': ('whatsapp_consent', 0),
                'tags': ('patient_tags', [])
            }
            
            # تعيين القيم بشكل آمن
            for field, (data_key, default_value) in fields_mapping.items():
                if field in self.detail_labels and self.detail_labels[field] is not None:
                    try:
                        value = patient.get(data_key, default_value)
                        
                        if field == 'whatsapp_consent':
                            display_value = '✅ نعم' if value else '❌ لا'
                            self.detail_labels[field].setText(display_value)
                        elif field == 'tags':
                            display_value = " ".join([f"🏷️{tag}" for tag in value]) if value and isinstance(value, list) else "لا توجد علامات"
                            self.detail_labels[field].setText(display_value)
                        elif field == 'gender':
                            gender_icon = "👦" if value == 'ذكر' else "👧" if value == 'أنثى' else "❓"
                            display_value = f"{gender_icon} {value}" if value != 'غير محدد' else value
                            self.detail_labels[field].setText(display_value)
                        else:
                            self.detail_labels[field].setText(str(value))
                            
                    except Exception as field_error:
                        logging.error(f"خطأ في تعيين الحقل {field}: {field_error}")
                        self.detail_labels[field].setText("خطأ في العرض")
            
            # تحديث السجل التاريخي والإحصائيات إذا كان patient_id متوفراً
            if 'id' in patient and patient['id']:
                try:
                    self.update_patient_history(patient['id'])
                    self.update_patient_statistics(patient['id'])
                except Exception as update_error:
                    logging.error(f"خطأ في تحديث السجل والإحصائيات: {update_error}")
            
            # تحديث حالة الأزرار
            self.safe_update_ui_elements()
            
        except Exception as e:
            logging.error(f"خطأ في عرض تفاصيل المريض: {e}")

    def update_patient_history(self, patient_id):
        """تحديث السجل التاريخي - الإصدار المحسن"""
        try:
            # المواعيد القادمة
            upcoming_appointments = []
            if self.db_manager:
                upcoming_appointments = self.db_manager.get_patient_appointments(patient_id)
                
            if self.upcoming_appointments_list:
                self.upcoming_appointments_list.clear()
                
                if upcoming_appointments:
                    for appointment in upcoming_appointments:
                        if appointment.get('status') == 'مجدول':
                            item_text = f"📅 {appointment.get('appointment_date', '')} - 🕒 {appointment.get('appointment_time', '')}"
                            if appointment.get('doctor_name'):
                                item_text += f" - 👨‍⚕️ د. {appointment['doctor_name']}"
                            if appointment.get('department_name'):
                                item_text += f" - 🏥 {appointment['department_name']}"
                            self.upcoming_appointments_list.addItem(item_text)
                
                if self.upcoming_appointments_list.count() == 0:
                    self.upcoming_appointments_list.addItem("📭 لا توجد مواعيد قادمة")
            
            # المواعيد السابقة
            appointments = []
            if self.db_manager:
                appointments = self.db_manager.get_patient_appointments(patient_id)
                
            if self.appointments_list:
                self.appointments_list.clear()
                
                if appointments:
                    for appointment in appointments:
                        if appointment.get('status') == 'منتهي':
                            item_text = f"✅ {appointment.get('appointment_date', '')} - {appointment.get('appointment_time', '')}"
                            if appointment.get('doctor_name'):
                                item_text += f" - د. {appointment['doctor_name']}"
                            self.appointments_list.addItem(item_text)
                
                if self.appointments_list.count() == 0:
                    self.appointments_list.addItem("📭 لا توجد مواعيد سابقة")
            
            # السجل الطبي - إصلاح: استخدام البيانات الحقيقية
            medical_history = []
            if self.db_manager:
                medical_history = self.db_manager.get_patient_medical_history(patient_id)
                
            if self.medical_history_list:
                self.medical_history_list.clear()
                
                if medical_history:
                    for record in medical_history:
                        item_text = f"📋 {record.get('visit_date', '')}"
                        if record.get('doctor_name'):
                            item_text += f" - 👨‍⚕️ د. {record['doctor_name']}"
                        if record.get('diagnosis'):
                            item_text += f" - 📝 {record['diagnosis']}"
                        if record.get('treatment'):
                            item_text += f" - 💊 {record['treatment']}"
                        self.medical_history_list.addItem(item_text)
                
                if self.medical_history_list.count() == 0:
                    # إذا لم توجد سجلات طبية، نعرض التاريخ المرضي من بيانات المريض
                    patient_data = None
                    if self.db_manager:
                        patient_data = self.db_manager.get_patient_by_id(patient_id)
                    if patient_data and patient_data.get('medical_history'):
                        self.medical_history_list.addItem(f"📝 {patient_data.get('medical_history')}")
                    else:
                        self.medical_history_list.addItem("📭 لا توجد سجلات طبية")
                    
        except Exception as e:
            logging.error(f"خطأ في تحديث السجل: {e}")

    def update_patient_statistics(self, patient_id):
        """تحديث إحصائيات المريض"""
        try:
            stats = {}
            if self.db_manager:
                stats = self.db_manager.get_patient_statistics(patient_id)
            
            if 'total_appointments' in self.stats_labels:
                self.stats_labels['total_appointments'].setText(str(stats.get('total_appointments', 0)))
            if 'completed_appointments' in self.stats_labels:
                self.stats_labels['completed_appointments'].setText(str(stats.get('completed_appointments', 0)))
            if 'first_appointment' in self.stats_labels:
                self.stats_labels['first_appointment'].setText(stats.get('first_appointment', 'لا يوجد'))
            if 'last_appointment' in self.stats_labels:
                self.stats_labels['last_appointment'].setText(stats.get('last_appointment', 'لا يوجد'))
            if 'medical_records' in self.stats_labels:
                self.stats_labels['medical_records'].setText(str(stats.get('medical_records_count', 0)))
            
        except Exception as e:
            logging.error(f"خطأ في تحديث الإحصائيات: {e}")

    def manage_patient_tags(self):
        """فتح نافذة إدارة العلامات"""
        try:
            patient_id = self.get_selected_patient_id()
            if not patient_id:
                QMessageBox.warning(self, "تحذير", "يرجى اختيار مريض أولاً")
                return
            
            # استيراد آمن
            try:
                from ui.dialogs.patient_tags_manager import PatientTagsManager
                dialog = PatientTagsManager(self.db_manager, patient_id, self)
                if dialog.exec_() == QDialog.Accepted:
                    # تحديث البيانات بعد التعديل
                    self.safe_load_patients()
                    patient = self.get_selected_patient_data()
                    if patient:
                        self.show_patient_details(patient)
                        
            except ImportError:
                # إذا لم يكن الـ dialog موجوداً، استخدام نموذج بسيط
                self.show_basic_tags_manager(patient_id)
                
        except Exception as e:
            logging.error(f"خطأ في إدارة العلامات: {e}")
            QMessageBox.critical(self, "خطأ", f"حدث خطأ: {str(e)}")

    def show_basic_tags_manager(self, patient_id):
        """عرض مدير علامات بسيط بديل"""
        try:
            tags = []
            if self.db_manager:
                tags = self.db_manager.get_patient_tags(patient_id)
            current_tags = "، ".join(tags) if tags else "لا توجد علامات"
            
            new_tag, ok = QInputDialog.getText(
                self, 
                "🏷️ إدارة العلامات", 
                f"العلامات الحالية: {current_tags}\n\nأدخل علامة جديدة:"
            )
            
            if ok and new_tag.strip():
                success = False
                if self.db_manager:
                    success = self.db_manager.add_patient_tag(patient_id, new_tag.strip())
                if success:
                    QMessageBox.information(self, "✅ نجاح", "تم إضافة العلامة بنجاح")
                    self.safe_load_patients()
                else:
                    QMessageBox.critical(self, "❌ خطأ", "فشل في إضافة العلامة")
                    
        except Exception as e:
            logging.error(f"خطأ في المدير البديل: {e}")
            QMessageBox.critical(self, "❌ خطأ", "لا يمكن فتح مدير العلامات")

    def add_patient(self):
        """إضافة مريض جديد"""
        try:
            from ui.dialogs.patient_dialog import PatientDialog
            dialog = PatientDialog(self.db_manager, self)
            if dialog.exec_() == QDialog.Accepted:
                self.safe_load_patients()
                self.data_updated.emit()
                QMessageBox.information(self, "نجاح", "تم إضافة المريض بنجاح")
        except ImportError:
            # إذا لم يكن الـ dialog موجوداً، استخدام نموذج بسيط
            self.show_basic_patient_dialog()
        except Exception as e:
            self.show_error(f"خطأ في إضافة المريض: {str(e)}")

    def show_basic_patient_dialog(self):
        """عرض نموذج بسيط لإضافة مريض"""
        dialog = QDialog(self)
        dialog.setWindowTitle("إضافة مريض جديد")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
        name_input = QLineEdit()
        phone_input = QLineEdit()
        gender_combo = QComboBox()
        gender_combo.addItems(["ذكر", "أنثى"])
        
        form_layout.addRow("الاسم:", name_input)
        form_layout.addRow("الهاتف:", phone_input)
        form_layout.addRow("الجنس:", gender_combo)
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            patient_data = {
                'name': name_input.text().strip(),
                'phone': phone_input.text().strip(),
                'gender': gender_combo.currentText(),
                'country_code': '+966'
            }
            
            if not patient_data['name'] or not patient_data['phone']:
                QMessageBox.warning(self, "تحذير", "الاسم والهاتف حقلان مطلوبان")
                return
            
            patient_id = None
            if self.db_manager:
                patient_id = self.db_manager.add_patient(patient_data)
            if patient_id:
                self.safe_load_patients()
                self.data_updated.emit()
                QMessageBox.information(self, "نجاح", "تم إضافة المريض بنجاح")
            else:
                QMessageBox.critical(self, "خطأ", "فشل في إضافة المريض")

    def safe_edit_patient(self):
        """تعديل آمن للمريض"""
        try:
            self.edit_patient()
        except Exception as e:
            self.show_error(f"خطأ في التعديل: {str(e)}")

    def edit_patient(self):
        """تعديل بيانات المريض"""
        patient_data = self.get_selected_patient_data()
        if not patient_data:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار مريض للتعديل")
            return
        
        try:
            from ui.dialogs.patient_dialog import PatientDialog
            dialog = PatientDialog(self.db_manager, self, patient_data)
            if dialog.exec_() == QDialog.Accepted:
                self.safe_load_patients()
                self.data_updated.emit()
                QMessageBox.information(self, "نجاح", "تم تحديث بيانات المريض بنجاح")
        except ImportError:
            self.show_basic_edit_dialog(patient_data)
        except Exception as e:
            self.show_error(f"خطأ في تعديل المريض: {str(e)}")

    def show_basic_edit_dialog(self, patient_data):
        """عرض نموذج بسيط للتعديل"""
        dialog = QDialog(self)
        dialog.setWindowTitle("تعديل بيانات المريض")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
        name_input = QLineEdit(patient_data.get('name', ''))
        phone_input = QLineEdit(patient_data.get('phone', ''))
        gender_combo = QComboBox()
        gender_combo.addItems(["ذكر", "أنثى"])
        gender_combo.setCurrentText(patient_data.get('gender', 'ذكر'))
        
        form_layout.addRow("الاسم:", name_input)
        form_layout.addRow("الهاتف:", phone_input)
        form_layout.addRow("الجنس:", gender_combo)
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            patient_data['name'] = name_input.text().strip()
            patient_data['phone'] = phone_input.text().strip()
            patient_data['gender'] = gender_combo.currentText()
            
            if not patient_data['name'] or not patient_data['phone']:
                QMessageBox.warning(self, "تحذير", "الاسم والهاتف حقلان مطلوبان")
                return
            
            success = False
            if self.db_manager:
                success = self.db_manager.update_patient(patient_data['id'], patient_data)
            if success:
                self.safe_load_patients()
                self.data_updated.emit()
                QMessageBox.information(self, "نجاح", "تم تحديث بيانات المريض بنجاح")
            else:
                QMessageBox.critical(self, "خطأ", "فشل في تحديث المريض")

    def safe_delete_patient(self):
        """حذف آمن للمريض"""
        try:
            self.delete_patient()
        except Exception as e:
            self.show_error(f"خطأ في الحذف: {str(e)}")

    def delete_patient(self):
        """حذف المريض المحدد"""
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار مريض للحذف")
            return
        
        patient_data = self.get_selected_patient_data()
        if not patient_data:
            return
        
        reply = QMessageBox.question(
            self, 
            "تأكيد الحذف", 
            f"هل أنت متأكد من حذف المريض:\n{patient_data['name']}؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success = False
                if self.db_manager:
                    success = self.db_manager.delete_patient(patient_id)
                if success:
                    QMessageBox.information(self, "نجاح", "تم حذف المريض بنجاح")
                    self.safe_load_patients()
                    self.data_updated.emit()
                else:
                    QMessageBox.critical(self, "خطأ", "فشل في حذف المريض")
            except Exception as e:
                self.show_error(f"خطأ في حذف المريض: {str(e)}")

    def show_error(self, message):
        """عرض رسالة خطأ"""
        QMessageBox.critical(self, "❌ خطأ", message)
        logging.error(message)

# إذا كان الملف يُشغل مباشرةً
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    
    # اختبار بسيط
    from database_manager import DatabaseManager
    db = DatabaseManager(":memory:")  # قاعدة بيانات في الذاكرة للاختبار
    
    window = PatientsManager(db)
    window.show()
    
    sys.exit(app.exec_())