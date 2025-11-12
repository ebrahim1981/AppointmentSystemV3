# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
                             QMessageBox, QHeaderView, QLabel, QToolBar, QAction,
                             QDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QColor, QBrush
import logging

class DepartmentsManager(QWidget):
    data_updated = pyqtSignal()
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.setup_ui()
        self.load_departments()
    
    def setup_ui(self):
        """إعداد واجهة إدارة الأقسام"""
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            QToolBar {
                background-color: #ffffff;
                padding: 8px;
                border-bottom: 1px solid #dee2e6;
                spacing: 10px;
            }
            QToolBar QToolButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QToolBar QToolButton:hover {
                background-color: #0056b3;
                transform: translateY(-1px);
            }
            QToolBar QToolButton:pressed {
                background-color: #004085;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                gridline-color: #e9ecef;
                selection-background-color: #e3f2fd;
                font-size: 14px;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #e9ecef;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #0066cc;
                font-weight: bold;
            }
            QTableWidget::item:hover {
                background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #343a40;
                color: white;
                padding: 12px 8px;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }
            QLineEdit, QComboBox {
                padding: 10px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                background-color: white;
                font-size: 14px;
                min-width: 200px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #007bff;
                background-color: #f8f9fa;
            }
            QLabel {
                color: #495057;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # شريط الأدوات
        toolbar = QToolBar()
        toolbar.setFixedHeight(50)
        
        add_action = QAction("➕ إضافة قسم", self)
        add_action.triggered.connect(self.add_department)
        toolbar.addAction(add_action)
        
        edit_action = QAction("✏️ تعديل", self)
        edit_action.triggered.connect(self.edit_department)
        toolbar.addAction(edit_action)
        
        delete_action = QAction("🗑️ حذف", self)
        delete_action.triggered.connect(self.delete_department)
        toolbar.addAction(delete_action)
        
        refresh_action = QAction("🔄 تحديث", self)
        refresh_action.triggered.connect(self.load_departments)
        toolbar.addAction(refresh_action)
        
        layout.addWidget(toolbar)
        
        # فلترة البيانات
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(15)
        
        self.clinic_filter = QComboBox()
        self.clinic_filter.addItem("جميع العيادات")
        self.clinic_filter.currentTextChanged.connect(self.load_departments)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 ابحث باسم القسم...")
        self.search_input.textChanged.connect(self.search_departments)
        
        filter_layout.addWidget(QLabel("العيادة:"))
        filter_layout.addWidget(self.clinic_filter)
        filter_layout.addWidget(QLabel("بحث:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # جدول الأقسام
        self.departments_table = QTableWidget()
        self.departments_table.setColumnCount(5)
        self.departments_table.setHorizontalHeaderLabels([
            "الرقم", "اسم القسم", "العيادة", "الوصف", "الحالة"
        ])
        
        # ضبط إعدادات الجدول
        header = self.departments_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.departments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.departments_table.setAlternatingRowColors(True)
        self.departments_table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #f8f9fa;
            }
            QTableWidget::item:hover {
                background-color: #e3f2fd;
            }
        """)
        self.departments_table.doubleClicked.connect(self.edit_department)
        
        layout.addWidget(self.departments_table)
        
        # إحصائيات
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("""
            QLabel {
                background-color: #e9ecef;
                color: #495057;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.stats_label)
        
        self.setLayout(layout)
        
        # تحميل بيانات الفلاتر
        self.load_filter_data()
    
    def load_filter_data(self):
        """تحميل بيانات الفلاتر"""
        try:
            # تحميل العيادات
            clinics = self.db_manager.get_clinics()
            self.clinic_filter.clear()
            self.clinic_filter.addItem("جميع العيادات")
            for clinic in clinics:
                self.clinic_filter.addItem(f"{clinic['name']} ({clinic['type']})", clinic['id'])
                
        except Exception as e:
            logging.error(f"خطأ في تحميل بيانات الفلاتر: {e}")
    
    def load_departments(self):
        """تحميل قائمة الأقسام"""
        try:
            # الحصول على معايير التصفية
            clinic_id = self.clinic_filter.currentData()
            search_term = self.search_input.text().strip()
            
            departments = self.db_manager.get_departments(
                clinic_id=clinic_id if clinic_id else None
            )
            
            # تطبيق البحث إذا كان موجوداً
            if search_term:
                departments = [dept for dept in departments if 
                              search_term.lower() in dept['name'].lower()]
            
            self.departments_table.setRowCount(len(departments))
            
            for row, department in enumerate(departments):
                self.departments_table.setItem(row, 0, QTableWidgetItem(str(department['id'])))
                self.departments_table.setItem(row, 1, QTableWidgetItem(department['name']))
                self.departments_table.setItem(row, 2, QTableWidgetItem(department.get('clinic_name', '')))
                self.departments_table.setItem(row, 3, QTableWidgetItem(department.get('description', '')))
                
                # حالة القسم
                status = "نشط" if department.get('is_active', 1) else "غير نشط"
                status_item = QTableWidgetItem(status)
                
                # تنسيق الحالة مع ألوان أفضل
                if status == "نشط":
                    status_item.setBackground(QColor("#28a745"))
                    status_item.setForeground(QBrush(Qt.white))
                    status_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
                else:
                    status_item.setBackground(QColor("#dc3545"))
                    status_item.setForeground(QBrush(Qt.white))
                    status_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
                
                # محاذاة النص في المنتصف
                status_item.setTextAlignment(Qt.AlignCenter)
                self.departments_table.setItem(row, 4, status_item)
                
                # تحسين محاذاة جميع الخلايا
                for col in range(self.departments_table.columnCount()):
                    item = self.departments_table.item(row, col)
                    if item:
                        if col == 0 or col == 4:  # الأعمدة الرقمية والحالة
                            item.setTextAlignment(Qt.AlignCenter)
                        else:
                            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # تحديث الإحصائيات
            active_count = sum(1 for dept in departments if dept.get('is_active', 1))
            inactive_count = len(departments) - active_count
            
            self.stats_label.setText(
                f"📊 الإحصائيات • عرض: {len(departments)} قسم • "
                f"نشط: {active_count} • غير نشط: {inactive_count} • "
                f"الإجمالي: {len(departments)} قسم"
            )
            
        except Exception as e:
            logging.error(f"خطأ في تحميل الأقسام: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل قائمة الأقسام: {str(e)}")
    
    def search_departments(self):
        """بحث الأقسام"""
        self.load_departments()
    
    def get_selected_department(self):
        """الحصول على القسم المحدد"""
        selected_items = self.departments_table.selectedItems()
        if not selected_items:
            return None
        
        department_id = int(self.departments_table.item(selected_items[0].row(), 0).text())
        departments = self.db_manager.get_departments()
        
        for department in departments:
            if department['id'] == department_id:
                return department
        
        return None
    
    def add_department(self):
        """إضافة قسم جديد"""
        try:
            from ui.dialogs.department_dialog import DepartmentDialog
            dialog = DepartmentDialog(self.db_manager, self)
            if dialog.exec_() == QDialog.Accepted:
                self.load_departments()
                self.data_updated.emit()
                QMessageBox.information(self, "نجاح", "✅ تم إضافة القسم بنجاح")
        except Exception as e:
            logging.error(f"خطأ في إضافة القسم: {e}")
            QMessageBox.critical(self, "خطأ", f"❌ فشل في إضافة القسم: {str(e)}")
    
    def edit_department(self):
        """تعديل بيانات القسم المحدد"""
        try:
            department = self.get_selected_department()
            if not department:
                QMessageBox.warning(self, "تحذير", "⚠️ يرجى اختيار قسم للتعديل")
                return
            
            from ui.dialogs.department_dialog import DepartmentDialog
            dialog = DepartmentDialog(self.db_manager, self, department)
            if dialog.exec_() == QDialog.Accepted:
                self.load_departments()
                self.data_updated.emit()
                QMessageBox.information(self, "نجاح", "✅ تم تحديث بيانات القسم بنجاح")
        except Exception as e:
            logging.error(f"خطأ في تعديل القسم: {e}")
            QMessageBox.critical(self, "خطأ", f"❌ فشل في تعديل القسم: {str(e)}")
    
    def delete_department(self):
        """حذف القسم المحدد - محدث"""
        department = self.get_selected_department()
        if not department:
            QMessageBox.warning(self, "تحذير", "⚠️ يرجى اختيار قسم للحذف")
            return
        
        reply = QMessageBox.question(
            self, 
            "تأكيد الحذف", 
            f"🗑️ هل أنت متأكد من حذف القسم التالي:\n\n"
            f"📝 اسم القسم: {department['name']}\n"
            f"🏥 العيادة: {department.get('clinic_name', '')}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success = self.db_manager.delete_department(department['id'])
                if success:
                    self.load_departments()
                    self.data_updated.emit()
                    QMessageBox.information(self, "نجاح", "✅ تم حذف القسم بنجاح")
                else:
                    QMessageBox.critical(self, "خطأ", "❌ فشل في حذف القسم")
            except Exception as e:
                logging.error(f"خطأ في حذف القسم: {e}")
                QMessageBox.critical(self, "خطأ", f"❌ فشل في حذف القسم: {str(e)}")
    
    def load_data(self):
        """تحميل البيانات - للتوافق مع النظام"""
        self.load_departments()