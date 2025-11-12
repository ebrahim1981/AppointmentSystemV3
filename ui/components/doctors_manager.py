# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
                             QMessageBox, QHeaderView, QLabel, QToolBar, QAction,
                             QDialog, QMenu, QProgressBar, QFrame, QStatusBar, 
                             QApplication, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor
import logging
import csv
import datetime

class DoctorsManager(QWidget):
    data_updated = pyqtSignal()
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.setup_ui()
        self.load_doctors()
        
        # مؤقت للتحديث التلقائي
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.load_doctors)
        self.auto_refresh_timer.start(30000)  # تحديث كل 30 ثانية
        
        # مؤقت للبحث
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.load_doctors)
    
    def setup_ui(self):
        """إعداد واجهة إدارة الأطباء"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # شريط العنوان
        title_layout = QHBoxLayout()
        
        title_label = QLabel("👨‍⚕️ إدارة الأطباء")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(18)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2C3E50; padding: 10px;")
        
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("""
            QLabel {
                background-color: #3498db;
                color: white;
                padding: 8px 15px;
                border-radius: 15px;
                font-weight: bold;
            }
        """)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.stats_label)
        
        main_layout.addLayout(title_layout)
        
        # شريط الأدوات الرئيسي
        action_buttons_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ إضافة طبيب")
        self.add_btn.clicked.connect(self.add_doctor)
        self.add_btn.setStyleSheet(self.get_button_style("primary"))
        
        self.edit_btn = QPushButton("✏️ تعديل")
        self.edit_btn.clicked.connect(self.edit_doctor)
        self.edit_btn.setStyleSheet(self.get_button_style("info"))
        
        self.toggle_btn = QPushButton("🔄 تفعيل/إيقاف")
        self.toggle_btn.clicked.connect(self.toggle_doctor_status)
        self.toggle_btn.setStyleSheet(self.get_button_style("warning"))
        
        # زر الحذف - جديد
        self.delete_btn = QPushButton("🗑️ حذف")
        self.delete_btn.clicked.connect(self.delete_doctor)
        self.delete_btn.setStyleSheet(self.get_button_style("danger"))
        
        # زر إرسال رسالة واتساب - جديد
        self.whatsapp_btn = QPushButton("📱 واتساب")
        self.whatsapp_btn.clicked.connect(self.send_whatsapp_message)
        self.whatsapp_btn.setStyleSheet(self.get_button_style("success"))
        
        self.export_btn = QPushButton("📊 تصدير")
        self.export_btn.clicked.connect(self.export_data)
        self.export_btn.setStyleSheet(self.get_button_style("primary"))
        
        self.refresh_btn = QPushButton("🔄 تحديث")
        self.refresh_btn.clicked.connect(self.load_doctors)
        self.refresh_btn.setStyleSheet(self.get_button_style("info"))
        
        # زر إدارة الجدولة - جديد
        self.schedule_btn = QPushButton("📅 إدارة الجدولة")
        self.schedule_btn.clicked.connect(self.manage_scheduling)
        self.schedule_btn.setStyleSheet(self.get_button_style("success"))
        
        for btn in [self.add_btn, self.edit_btn, self.toggle_btn, self.delete_btn, 
                   self.whatsapp_btn, self.export_btn, self.refresh_btn, self.schedule_btn]:
            btn.setStyleSheet(self.get_button_style("primary"))  # سيتم تعديل الأنماط لاحقاً
            action_buttons_layout.addWidget(btn)
        
        action_buttons_layout.addStretch()
        main_layout.addLayout(action_buttons_layout)
        
        # منطقة الفلاتر والبحث
        filter_group = QFrame()
        filter_group.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 15px;
            }
        """)
        filter_layout = QHBoxLayout(filter_group)
        
        # فلتر العيادة
        filter_layout.addWidget(QLabel("🏥 العيادة:"))
        self.clinic_filter = QComboBox()
        self.clinic_filter.addItem("جميع العيادات")
        self.clinic_filter.currentTextChanged.connect(self.load_doctors)
        self.clinic_filter.setStyleSheet(self.get_combo_style())
        filter_layout.addWidget(self.clinic_filter)
        
        # فلتر القسم
        filter_layout.addWidget(QLabel("📋 القسم:"))
        self.department_filter = QComboBox()
        self.department_filter.addItem("جميع الأقسام")
        self.department_filter.currentTextChanged.connect(self.load_doctors)
        self.department_filter.setStyleSheet(self.get_combo_style())
        filter_layout.addWidget(self.department_filter)
        
        # فلتر الحالة
        filter_layout.addWidget(QLabel("📊 الحالة:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("جميع الأطباء")
        self.status_filter.addItem("الأطباء النشطين فقط")
        self.status_filter.addItem("الأطباء غير النشطين فقط")
        self.status_filter.currentTextChanged.connect(self.load_doctors)
        self.status_filter.setStyleSheet(self.get_combo_style())
        filter_layout.addWidget(self.status_filter)
        
        filter_layout.addStretch()
        
        # البحث
        filter_layout.addWidget(QLabel("🔍 بحث:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث باسم الطبيب، التخصص، الرقم الوطني...")
        self.search_input.textChanged.connect(self.search_doctors)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #bdc3c7;
                border-radius: 20px;
                font-size: 13px;
                min-width: 250px;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
        """)
        filter_layout.addWidget(self.search_input)
        
        main_layout.addWidget(filter_group)
        
        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                text-align: center;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 3px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # جدول الأطباء
        self.doctors_table = QTableWidget()
        self.doctors_table.setColumnCount(10)  # تمت إضافة عمود الجدولة
        self.doctors_table.setHorizontalHeaderLabels([
            "الرقم", "الاسم", "التخصص", "القسم", "العيادة", "الهاتف", "رسوم الكشف", "الحالة", "الجداول", "آخر تحديث"
        ])
        
        # ضبط إعدادات الجدول
        header = self.doctors_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # الاسم
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # التخصص
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # الجداول
        
        self.doctors_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.doctors_table.setAlternatingRowColors(True)
        self.doctors_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #dee2e6;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #dee2e6;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #2C3E50;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        
        self.doctors_table.doubleClicked.connect(self.edit_doctor)
        self.doctors_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.doctors_table.customContextMenuRequested.connect(self.show_context_menu)
        self.doctors_table.selectionModel().selectionChanged.connect(self.update_ui)
        
        main_layout.addWidget(self.doctors_table)
        
        # شريط الحالة
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #ecf0f1;
                color: #2C3E50;
                border-top: 1px solid #bdc3c7;
                padding: 5px;
            }
        """)
        main_layout.addWidget(self.status_bar)
        
        self.setLayout(main_layout)
        
        # تحميل بيانات الفلاتر
        self.load_filter_data()
        
        # تحديث واجهة المستخدم
        QTimer.singleShot(100, self.update_ui)
    
    def get_button_style(self, button_type="primary"):
        """أنماط الأزرار"""
        styles = {
            "primary": """
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 5px;
                    font-weight: bold;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:disabled {
                    background-color: #bdc3c7;
                    color: #7f8c8d;
                }
            """,
            "success": """
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 5px;
                    font-weight: bold;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #219a52;
                }
            """,
            "warning": """
                QPushButton {
                    background-color: #f39c12;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 5px;
                    font-weight: bold;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #e67e22;
                }
            """,
            "danger": """
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 5px;
                    font-weight: bold;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """,
            "info": """
                QPushButton {
                    background-color: #17a2b8;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 5px;
                    font-weight: bold;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #138496;
                }
            """
        }
        return styles.get(button_type, styles["primary"])
    
    def get_combo_style(self):
        return """
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 13px;
                min-width: 150px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
            }
        """
    
    def update_ui(self):
        """تحديث واجهة المستخدم"""
        has_selection = len(self.doctors_table.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.toggle_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        self.whatsapp_btn.setEnabled(has_selection)
        self.schedule_btn.setEnabled(has_selection)
    
    def load_filter_data(self):
        """تحميل بيانات الفلاتر"""
        try:
            # تحميل العيادات
            clinics = self.db_manager.get_clinics()
            self.clinic_filter.clear()
            self.clinic_filter.addItem("جميع العيادات")
            for clinic in clinics:
                self.clinic_filter.addItem(clinic['name'], clinic['id'])
            
            # تحميل الأقسام
            departments = self.db_manager.get_departments()
            self.department_filter.clear()
            self.department_filter.addItem("جميع الأقسام")
            for dept in departments:
                self.department_filter.addItem(dept['name'], dept['id'])
                
        except Exception as e:
            logging.error(f"خطأ في تحميل بيانات الفلاتر: {e}")
            self.show_error_message("تحميل الفلاتر", f"فشل في تحميل بيانات الفلاتر: {str(e)}")
    
    def load_doctors(self):
        """تحميل قائمة الأطباء - الإصدار المحسن"""
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Progress bar in busy mode
            
            # الحصول على معايير التصفية
            clinic_id = self.clinic_filter.currentData()
            department_id = self.department_filter.currentData()
            search_term = self.search_input.text().strip()
            
            # تحديد حالة التصفية
            status_filter = None
            if self.status_filter.currentText() == "الأطباء النشطين فقط":
                status_filter = True
            elif self.status_filter.currentText() == "الأطباء غير النشطين فقط":
                status_filter = False
            
            # استدعاء الدالة الصحيحة من db_manager
            doctors = self.db_manager.get_doctors(
                clinic_id=clinic_id if clinic_id else None,
                department_id=department_id if department_id else None
            )
            
            # تطبيق تصفية الحالة يدوياً إذا لم تكن مدعومة في db_manager
            if status_filter is not None:
                doctors = [doc for doc in doctors if doc.get('is_active', True) == status_filter]
            
            # تطبيق البحث إذا كان موجوداً
            if search_term:
                doctors = [doc for doc in doctors if 
                          search_term.lower() in doc['name'].lower() or 
                          search_term.lower() in doc.get('specialty', '').lower() or
                          search_term.lower() in doc.get('national_id', '').lower() or
                          search_term.lower() in doc.get('license_number', '').lower()]
            
            self.doctors_table.setRowCount(len(doctors))
            
            for row, doctor in enumerate(doctors):
                # الرقم
                self.doctors_table.setItem(row, 0, QTableWidgetItem(str(doctor['id'])))
                
                # الاسم
                name_item = QTableWidgetItem(doctor['name'])
                if not doctor.get('is_active', True):
                    name_item.setBackground(QColor(255, 230, 230))
                self.doctors_table.setItem(row, 1, name_item)
                
                # التخصص
                specialty = doctor.get('specialty', '') or doctor.get('specialization', '')
                self.doctors_table.setItem(row, 2, QTableWidgetItem(specialty))
                
                # القسم والعيادة
                self.doctors_table.setItem(row, 3, QTableWidgetItem(doctor.get('department_name', '')))
                self.doctors_table.setItem(row, 4, QTableWidgetItem(doctor.get('clinic_name', '')))
                
                # الهاتف
                self.doctors_table.setItem(row, 5, QTableWidgetItem(doctor.get('phone', '')))
                
                # رسوم الكشف
                fee = doctor.get('consultation_fee', 0)
                fee_item = QTableWidgetItem(f"{float(fee): ,.0f} ريال")
                fee_item.setTextAlignment(Qt.AlignCenter)
                self.doctors_table.setItem(row, 6, fee_item)
                
                # حالة الطبيب
                is_active = doctor.get('is_active', True)
                status = "🟢 نشط" if is_active else "🔴 غير نشط"
                status_item = QTableWidgetItem(status)
                status_item.setTextAlignment(Qt.AlignCenter)
                if is_active:
                    status_item.setBackground(QColor(230, 255, 230))
                    status_item.setForeground(QColor(0, 100, 0))
                else:
                    status_item.setBackground(QColor(255, 230, 230))
                    status_item.setForeground(QColor(139, 0, 0))
                self.doctors_table.setItem(row, 7, status_item)
                
                # حالة الجدولة - جديد
                schedule_status = self.get_doctor_schedule_status(doctor['id'])
                schedule_item = QTableWidgetItem(schedule_status['text'])
                schedule_item.setTextAlignment(Qt.AlignCenter)
                schedule_item.setBackground(schedule_status['background'])
                schedule_item.setForeground(schedule_status['foreground'])
                self.doctors_table.setItem(row, 8, schedule_item)
                
                # آخر تحديث
                updated = doctor.get('updated_at', doctor.get('created_at', ''))
                date_item = QTableWidgetItem(str(updated)[:10] if updated else "")
                date_item.setTextAlignment(Qt.AlignCenter)
                self.doctors_table.setItem(row, 9, date_item)
            
            # تحديث الإحصائيات
            self.update_statistics(doctors)
            
            self.status_bar.showMessage(f"تم تحميل {len(doctors)} طبيب - آخر تحديث: {datetime.datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            logging.error(f"خطأ في تحميل الأطباء: {e}")
            self.show_error_message("تحميل الأطباء", f"فشل في تحميل قائمة الأطباء: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
            self.update_ui()
    
    def get_doctor_schedule_status(self, doctor_id):
        """الحصول على حالة جدولة الطبيب"""
        try:
            # التحقق من وجود إعدادات الجدولة
            schedule_settings = self.db_manager.get_doctor_schedule_settings(doctor_id)
            
            if not schedule_settings:
                return {
                    'text': '⚪ غير مُعد',
                    'background': QColor(255, 255, 255),
                    'foreground': QColor(128, 128, 128)
                }
            
            # التحقق من وجود الجدول الدوري
            schedule_data = self.db_manager.get_periodic_schedule(doctor_id)
            if not schedule_data:
                return {
                    'text': '🟡 بلا جدول',
                    'background': QColor(255, 255, 204),
                    'foreground': QColor(153, 153, 0)
                }
            
            # حساب إحصائيات الجدول
            total_slots = 0
            available_slots = 0
            booked_slots = 0
            
            for date_data in schedule_data.values():
                total_slots += date_data['total_count']
                available_slots += date_data['available_count']
                booked_slots += date_data['booked_count']
            
            if total_slots == 0:
                return {
                    'text': '🟡 بلا مواعيد',
                    'background': QColor(255, 255, 204),
                    'foreground': QColor(153, 153, 0)
                }
            
            occupancy_rate = (booked_slots / total_slots * 100) if total_slots > 0 else 0
            
            if occupancy_rate > 80:
                return {
                    'text': '🔵 مشغول',
                    'background': QColor(204, 229, 255),
                    'foreground': QColor(0, 76, 153)
                }
            elif occupancy_rate > 50:
                return {
                    'text': '🟢 نشط',
                    'background': QColor(204, 255, 204),
                    'foreground': QColor(0, 102, 0)
                }
            else:
                return {
                    'text': '🟢 متاح',
                    'background': QColor(204, 255, 204),
                    'foreground': QColor(0, 102, 0)
                }
                
        except Exception as e:
            logging.error(f"خطأ في الحصول على حالة الجدولة: {e}")
            return {
                'text': '⚪ غير معروف',
                'background': QColor(255, 255, 255),
                'foreground': QColor(128, 128, 128)
            }
    
    def update_statistics(self, doctors):
        """تحديث الإحصائيات مع تحسينات"""
        active_doctors = sum(1 for doc in doctors if doc.get('is_active', True))
        total_doctors = len(doctors)
        inactive_doctors = total_doctors - active_doctors
        
        # حساب الأطباء الذين لديهم جداول
        doctors_with_schedules = 0
        for doctor in doctors:
            schedule_settings = self.db_manager.get_doctor_schedule_settings(doctor['id'])
            if schedule_settings:
                doctors_with_schedules += 1
        
        stats_text = f"👥 الإجمالي: {total_doctors} | 🟢 النشطين: {active_doctors} | 🔴 غير النشطين: {inactive_doctors} | 📅 المجدولين: {doctors_with_schedules}"
        self.stats_label.setText(stats_text)
    
    def search_doctors(self):
        """بحث الأطباء مع تأخير لتحسين الأداء"""
        self.search_timer.start(500)  # تأخير 500 مللي ثانية
    
    def show_context_menu(self, position):
        """إظهار قائمة السياق مع إضافات جديدة"""
        menu = QMenu(self)
        
        # الإجراءات الأساسية
        edit_action = menu.addAction("✏️ تعديل البيانات")
        toggle_action = menu.addAction("🔄 تفعيل/إيقاف")
        delete_action = menu.addAction("🗑️ حذف")
        
        menu.addSeparator()
        
        # إجراءات جديدة للنسخ
        copy_name_action = menu.addAction("📋 نسخ الاسم")
        copy_phone_action = menu.addAction("📞 نسخ رقم الهاتف")
        
        menu.addSeparator()
        
        # إرسال رسالة واتساب - جديد
        whatsapp_action = menu.addAction("📱 إرسال رسالة واتساب")
        
        menu.addSeparator()
        
        # إجراءات الجدولة - جديد
        schedule_action = menu.addAction("📅 إدارة الجدولة")
        view_schedule_action = menu.addAction("👁️ عرض الجدول")
        create_schedule_action = menu.addAction("🔄 إنشاء جدول دوري")
        
        menu.addSeparator()
        
        view_details = menu.addAction("👁️ عرض التفاصيل")
        
        menu.addSeparator()
        
        export_action = menu.addAction("📊 تصدير البيانات")
        
        # ربط الإجراءات
        edit_action.triggered.connect(self.edit_doctor)
        toggle_action.triggered.connect(self.toggle_doctor_status)
        delete_action.triggered.connect(self.delete_doctor)
        copy_name_action.triggered.connect(self.copy_doctor_name)
        copy_phone_action.triggered.connect(self.copy_doctor_phone)
        whatsapp_action.triggered.connect(self.send_whatsapp_message)
        schedule_action.triggered.connect(self.manage_scheduling)
        view_schedule_action.triggered.connect(self.view_doctor_schedule)
        create_schedule_action.triggered.connect(self.create_doctor_schedule)
        view_details.triggered.connect(self.view_doctor_details)
        export_action.triggered.connect(self.export_data)
        
        menu.exec_(self.doctors_table.viewport().mapToGlobal(position))
    
    def copy_doctor_name(self):
        """نسخ اسم الطبيب إلى الحافظة"""
        doctor = self.get_selected_doctor()
        if doctor:
            clipboard = QApplication.clipboard()
            clipboard.setText(doctor['name'])
            self.status_bar.showMessage("تم نسخ الاسم إلى الحافظة", 2000)
    
    def copy_doctor_phone(self):
        """نسخ رقم هاتف الطبيب إلى الحافظة"""
        doctor = self.get_selected_doctor()
        if doctor and doctor.get('phone'):
            clipboard = QApplication.clipboard()
            clipboard.setText(doctor['phone'])
            self.status_bar.showMessage("تم نسخ رقم الهاتف إلى الحافظة", 2000)
        else:
            self.status_bar.showMessage("لا يوجد رقم هاتف للطبيب المحدد", 2000)
    
    def get_selected_doctor(self):
        """الحصول على الطبيب المحدد"""
        selected_items = self.doctors_table.selectedItems()
        if not selected_items:
            return None
        
        try:
            doctor_id = int(self.doctors_table.item(selected_items[0].row(), 0).text())
            
            # الحصول على جميع الأطباء والبحث عن الطبيب المحدد
            doctors = self.db_manager.get_doctors()
            for doctor in doctors:
                if doctor['id'] == doctor_id:
                    return doctor
        except Exception as e:
            logging.error(f"خطأ في الحصول على الطبيب المحدد: {e}")
            self.show_error_message("اختيار الطبيب", "فشل في الحصول على بيانات الطبيب المحدد")
        
        return None
    
    def add_doctor(self):
        """إضافة طبيب جديد"""
        try:
            # استيراد DoctorDialog من المسار الصحيح
            try:
                from ui.dialogs.doctor_dialog import DoctorDialog
            except ImportError:
                from doctor_dialog import DoctorDialog
            
            dialog = DoctorDialog(self.db_manager, self)
            if dialog.exec_() == QDialog.Accepted:
                self.load_doctors()
                self.data_updated.emit()
                QMessageBox.information(self, "نجاح", "✅ تم إضافة الطبيب بنجاح")
        except Exception as e:
            logging.error(f"خطأ في إضافة الطبيب: {e}")
            self.show_error_message("إضافة طبيب", f"فشل في إضافة الطبيب: {str(e)}")
    
    def edit_doctor(self):
        """تعديل بيانات الطبيب المحدد"""
        try:
            doctor = self.get_selected_doctor()
            if not doctor:
                QMessageBox.warning(self, "تحذير", "يرجى اختيار طبيب للتعديل")
                return
            
            # استيراد DoctorDialog من المسار الصحيح
            try:
                from ui.dialogs.doctor_dialog import DoctorDialog
            except ImportError:
                from doctor_dialog import DoctorDialog
            
            dialog = DoctorDialog(self.db_manager, self, doctor)
            if dialog.exec_() == QDialog.Accepted:
                self.load_doctors()
                self.data_updated.emit()
                QMessageBox.information(self, "نجاح", "✅ تم تحديث بيانات الطبيب بنجاح")
        except Exception as e:
            logging.error(f"خطأ في تعديل الطبيب: {e}")
            self.show_error_message("تعديل طبيب", f"فشل في تعديل الطبيب: {str(e)}")
    
    def toggle_doctor_status(self):
        """تفعيل/إيقاف الطبيب المحدد - الإصدار المصحح"""
        doctor = self.get_selected_doctor()
        if not doctor:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار طبيب")
            return
        
        current_status = doctor.get('is_active', True)
        new_status = not current_status
        
        action = "تفعيل" if new_status else "إيقاف"
        
        reply = QMessageBox.question(
            self, 
            f"تأكيد {action}", 
            f"هل أنت متأكد من {action} الطبيب التالي:\n\nالاسم: {doctor['name']}\nالتخصص: {doctor.get('specialty', '')}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # استخدام الدالة الجديدة في DatabaseManager
                success = self.db_manager.toggle_doctor_status(doctor['id'], new_status)
                if success:
                    self.load_doctors()
                    self.data_updated.emit()
                    status_text = "مفعل" if new_status else "موقوف"
                    QMessageBox.information(self, "نجاح", f"✅ تم {action} الطبيب بنجاح - الحالة: {status_text}")
                else:
                    QMessageBox.critical(self, "خطأ", f"❌ فشل في {action} الطبيب")
            except Exception as e:
                logging.error(f"خطأ في {action} الطبيب: {e}")
                self.show_error_message(f"{action} الطبيب", f"فشل في {action} الطبيب: {str(e)}")
    
    def send_whatsapp_message(self):
        """إرسال رسالة واتساب للطبيب المحدد - ميزة جديدة"""
        doctor = self.get_selected_doctor()
        if not doctor:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار طبيب")
            return
        
        if not doctor.get('phone'):
            QMessageBox.warning(self, "تحذير", "لا يوجد رقم هاتف مسجل للطبيب المحدد")
            return
        
        try:
            from PyQt5.QtWidgets import QInputDialog, QTextEdit, QDialogButtonBox
            
            # إنشاء نافذة لإدخال الرسالة
            dialog = QDialog(self)
            dialog.setWindowTitle(f"إرسال رسالة واتساب - د. {doctor['name']}")
            dialog.setMinimumWidth(500)
            
            layout = QVBoxLayout()
            
            # معلومات الطبيب
            info_label = QLabel(f"👨‍⚕️ الطبيب: {doctor['name']}\n📞 الرقم: {doctor.get('phone', 'غير متوفر')}")
            info_label.setStyleSheet("""
                QLabel {
                    background-color: #f8f9fa;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid #dee2e6;
                    font-weight: bold;
                }
            """)
            layout.addWidget(info_label)
            
            # حقل إدخال الرسالة
            layout.addWidget(QLabel("الرسالة:"))
            message_edit = QTextEdit()
            message_edit.setPlaceholderText("اكتب رسالتك هنا...")
            message_edit.setMinimumHeight(150)
            layout.addWidget(message_edit)
            
            # أزرار
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            dialog.setLayout(layout)
            
            if dialog.exec_() == QDialog.Accepted:
                message = message_edit.toPlainText().strip()
                if not message:
                    QMessageBox.warning(self, "تحذير", "يرجى كتابة رسالة")
                    return
                
                # تنظيف رقم الهاتف
                phone_number = self.db_manager.clean_phone_number(doctor['phone'])
                
                if phone_number:
                    # فتح رابط واتساب
                    import webbrowser
                    whatsapp_url = f"https://wa.me/{phone_number}?text={message}"
                    webbrowser.open(whatsapp_url)
                    
                    # تسجيل الإحصائية
                    self.db_manager.log_message_stat(
                        clinic_id=doctor.get('clinic_id', 1),
                        stat_data={
                            'patient_id': None,
                            'appointment_id': None,
                            'message_type': 'doctor_communication',
                            'phone_number': phone_number,
                            'country_code': '+966',
                            'status': 'opened',
                            'provider': 'whatsapp_web',
                            'error_message': ''
                        }
                    )
                    
                    QMessageBox.information(self, "نجاح", f"✅ تم فتح واتساب لإرسال الرسالة للدكتور {doctor['name']}")
                else:
                    QMessageBox.critical(self, "خطأ", "❌ رقم الهاتف غير صحيح")
                    
        except Exception as e:
            logging.error(f"خطأ في إرسال رسالة واتساب: {e}")
            self.show_error_message("إرسال واتساب", f"فشل في إرسال الرسالة: {str(e)}")
    
    def manage_scheduling(self):
        """إدارة جدولة الطبيب المحدد"""
        doctor = self.get_selected_doctor()
        if not doctor:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار طبيب")
            return
        
        try:
            # فتح نافذة إدارة الجدولة
            from ui.dialogs.doctor_dialog import DoctorDialog
            dialog = DoctorDialog(self.db_manager, self, doctor)
            # الانتقال مباشرة إلى تبويب الجدولة
            dialog.tabs.setCurrentIndex(2)  # تبويب الجداول الدورية
            dialog.exec_()
            
            # تحديث البيانات بعد الإغلاق
            self.load_doctors()
            
        except Exception as e:
            logging.error(f"خطأ في إدارة الجدولة: {e}")
            self.show_error_message("إدارة الجدولة", f"فشل في فتح إعدادات الجدولة: {str(e)}")
    
    def view_doctor_schedule(self):
        """عرض جدول الطبيب المحدد"""
        doctor = self.get_selected_doctor()
        if not doctor:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار طبيب")
            return
        
        try:
            # الحصول على جدول الطبيب
            schedule_data = self.db_manager.get_periodic_schedule(doctor['id'])
            
            if not schedule_data:
                QMessageBox.information(self, "معلومات", 
                                      f"📋 لا يوجد جدول دوري للطبيب {doctor['name']}\n\n"
                                      f"يرجى إنشاء جدول أولاً باستخدام خيار 'إدارة الجدولة'")
                return
            
            # حساب الإحصائيات
            total_slots = 0
            available_slots = 0
            booked_slots = 0
            total_days = len(schedule_data)
            
            for date_data in schedule_data.values():
                total_slots += date_data['total_count']
                available_slots += date_data['available_count']
                booked_slots += date_data['booked_count']
            
            occupancy_rate = (booked_slots / total_slots * 100) if total_slots > 0 else 0
            
            message = f"""
📊 جدول الطبيب: {doctor['name']}

• عدد الأيام في الجدول: {total_days} يوم
• إجمالي المواعيد: {total_slots} موعد
• المواعيد المتاحة: {available_slots} موعد
• المواعيد المحجوزة: {booked_slots} موعد
• نسبة الإشغال: {occupancy_rate:.1f}%

🗓️ الجدول يشمل الفترة من:
{min(schedule_data.keys())} إلى {max(schedule_data.keys())}

💡 يمكنك عرض التفاصيل الكاملة في واجهة الجدولة الذكية.
"""
            QMessageBox.information(self, f"جدول الطبيب {doctor['name']}", message.strip())
            
        except Exception as e:
            logging.error(f"خطأ في عرض جدول الطبيب: {e}")
            self.show_error_message("عرض الجدول", f"فشل في عرض جدول الطبيب: {str(e)}")
    
    def create_doctor_schedule(self):
        """إنشاء جدول دوري للطبيب المحدد"""
        doctor = self.get_selected_doctor()
        if not doctor:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار طبيب")
            return
        
        try:
            reply = QMessageBox.question(
                self,
                "إنشاء جدول دوري",
                f"هل تريد إنشاء جدول دوري للطبيب:\n\n{doctor['name']}\n\n"
                f"سيتم إنشاء جدول لمدة 30 يوم بالأوقات المتاحة وفقاً لإعدادات الجدولة.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                success = self.db_manager.setup_doctor_periodic_schedule(doctor['id'], 30)
                
                if success:
                    QMessageBox.information(self, "نجاح", 
                                          f"✅ تم إنشاء الجدول الدوري للطبيب {doctor['name']} بنجاح!\n\n"
                                          f"تم إنشاء جدول لمدة 30 يوم بالأوقات المتاحة.")
                    self.load_doctors()
                else:
                    QMessageBox.critical(self, "خطأ", 
                                       f"❌ فشل في إنشاء الجدول الدوري للطبيب {doctor['name']}\n\n"
                                       f"يرجى التحقق من إعدادات الجدولة للطبيب.")
                    
        except Exception as e:
            logging.error(f"خطأ في إنشاء جدول الطبيب: {e}")
            self.show_error_message("إنشاء الجدول", f"فشل في إنشاء الجدول: {str(e)}")
    
    def view_doctor_details(self):
        """عرض تفاصيل الطبيب المحدد"""
        doctor = self.get_selected_doctor()
        if not doctor:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار طبيب")
            return
        
        try:
            # الحصول على معلومات الجدولة
            schedule_settings = self.db_manager.get_doctor_schedule_settings(doctor['id'])
            schedule_data = self.db_manager.get_periodic_schedule(doctor['id'])
            
            # حساب إحصائيات الجدول
            total_slots = 0
            available_slots = 0
            booked_slots = 0
            total_days = len(schedule_data) if schedule_data else 0
            
            if schedule_data:
                for date_data in schedule_data.values():
                    total_slots += date_data['total_count']
                    available_slots += date_data['available_count']
                    booked_slots += date_data['booked_count']
            
            occupancy_rate = (booked_slots / total_slots * 100) if total_slots > 0 else 0
            
            details = f"""
👨‍⚕️ تفاصيل الطبيب:

الاسم: {doctor['name']}
التخصص: {doctor.get('specialty', '')}
العيادة: {doctor.get('clinic_name', '')}
القسم: {doctor.get('department_name', '')}

📞 معلومات الاتصال:
الهاتف: {doctor.get('phone', 'غير متوفر')}
البريد الإلكتروني: {doctor.get('email', 'غير متوفر')}

💼 المعلومات المهنية:
الرقم الوطني: {doctor.get('national_id', 'غير متوفر')}
رقم الترخيص: {doctor.get('license_number', 'غير متوفر')}
رسوم الكشف: {doctor.get('consultation_fee', 0): ,.0f} ريال

📊 معلومات الجدولة:
إعدادات الجدولة: {'✅ مكتملة' if schedule_settings else '❌ ناقصة'}
الجدول الدوري: {'✅ منشأ' if schedule_data else '❌ غير منشأ'}
عدد الأيام في الجدول: {total_days} يوم
إجمالي المواعيد: {total_slots} موعد
المواعيد المتاحة: {available_slots} موعد
المواعيد المحجوزة: {booked_slots} موعد
نسبة الإشغال: {occupancy_rate:.1f}%

📝 ملاحظات:
{doctor.get('notes', 'لا توجد ملاحظات')}

📊 الحالة: {'🟢 نشط' if doctor.get('is_active', True) else '🔴 غير نشط'}
"""
            QMessageBox.information(self, "تفاصيل الطبيب", details.strip())
            
        except Exception as e:
            logging.error(f"خطأ في عرض تفاصيل الطبيب: {e}")
            self.show_error_message("عرض التفاصيل", f"فشل في عرض تفاصيل الطبيب: {str(e)}")
    
    def export_data(self):
        """تصدير بيانات الأطباء"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "تصدير بيانات الأطباء",
                f"doctors_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if file_path:
                doctors = self.db_manager.get_doctors()
                
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    # كتابة العنوان
                    writer.writerow([
                        'الرقم', 'الاسم', 'التخصص', 'القسم', 'العيادة', 
                        'الهاتف', 'البريد الإلكتروني', 'الرقم الوطني', 
                        'رقم الترخيص', 'رسوم الكشف', 'ساعات العمل', 'الحالة', 'الجداول'
                    ])
                    
                    # كتابة البيانات
                    for doctor in doctors:
                        schedule_status = self.get_doctor_schedule_status(doctor['id'])
                        writer.writerow([
                            doctor['id'],
                            doctor['name'],
                            doctor.get('specialty', ''),
                            doctor.get('department_name', ''),
                            doctor.get('clinic_name', ''),
                            doctor.get('phone', ''),
                            doctor.get('email', ''),
                            doctor.get('national_id', ''),
                            doctor.get('license_number', ''),
                            doctor.get('consultation_fee', 0),
                            doctor.get('working_hours', ''),
                            'نشط' if doctor.get('is_active', True) else 'غير نشط',
                            schedule_status['text']
                        ])
                
                QMessageBox.information(self, "نجاح", f"✅ تم تصدير البيانات إلى: {file_path}")
                
        except Exception as e:
            logging.error(f"خطأ في تصدير البيانات: {e}")
            self.show_error_message("تصدير البيانات", f"فشل في تصدير البيانات: {str(e)}")
    
    def delete_doctor(self):
        """حذف الطبيب المحدد"""
        doctor = self.get_selected_doctor()
        if not doctor:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار طبيب للحذف")
            return
        
        reply = QMessageBox.question(
            self, 
            "تأكيد الحذف", 
            f"هل أنت متأكد من حذف الطبيب التالي:\n\nالاسم: {doctor['name']}\nالتخصص: {doctor.get('specialty', '')}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success = self.db_manager.delete_doctor(doctor['id'])
                if success:
                    self.load_doctors()
                    self.data_updated.emit()
                    QMessageBox.information(self, "نجاح", "✅ تم حذف الطبيب بنجاح")
                else:
                    QMessageBox.critical(self, "خطأ", "❌ فشل في حذف الطبيب")
            except Exception as e:
                logging.error(f"خطأ في حذف الطبيب: {e}")
                self.show_error_message("حذف طبيب", f"فشل في حذف الطبيب: {str(e)}")
    
    def show_error_message(self, operation, message):
        """عرض رسالة خطأ موحدة"""
        QMessageBox.critical(self, "خطأ", f"{operation}: {message}")