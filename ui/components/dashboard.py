# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QPushButton, QGroupBox, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QProgressBar, QFrame)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor, QPainter
import logging
from datetime import datetime, timedelta

class Dashboard(QWidget):
    """لوحة التحكم الرئيسية"""
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """إعداد واجهة لوحة التحكم"""
        layout = QVBoxLayout()
        
        # العنوان
        title = QLabel("لوحة التحكم - نظرة عامة")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(18)
        title.setFont(title_font)
        title.setStyleSheet("color: #2C3E50; padding: 15px;")
        layout.addWidget(title)
        
        # شبكة الإحصائيات السريعة
        stats_grid = QGridLayout()
        stats_grid.setSpacing(15)
        
        # إحصائيات العيادات
        self.clinics_stats = self.create_stat_card("🏥 العيادات", "0", "#3498DB", "إجمالي العيادات المسجلة")
        stats_grid.addWidget(self.clinics_stats, 0, 0)
        
        # إحصائيات الأقسام
        self.departments_stats = self.create_stat_card("🏥 الأقسام", "0", "#9B59B6", "إجمالي الأقسام الطبية")
        stats_grid.addWidget(self.departments_stats, 0, 1)
        
        # إحصائيات الأطباء
        self.doctors_stats = self.create_stat_card("👨‍⚕️ الأطباء", "0", "#2ECC71", "إجمالي الأطباء النشطين")
        stats_grid.addWidget(self.doctors_stats, 0, 2)
        
        # إحصائيات المرضى
        self.patients_stats = self.create_stat_card("👥 المرضى", "0", "#E74C3C", "إجمالي المرضى المسجلين")
        stats_grid.addWidget(self.patients_stats, 0, 3)
        
        # إحصائيات المواعيد
        self.appointments_stats = self.create_stat_card("📅 المواعيد", "0", "#F39C12", "مواعيد اليوم")
        stats_grid.addWidget(self.appointments_stats, 1, 0)
        
        # إحصائيات الإيرادات
        self.revenue_stats = self.create_stat_card("💰 الإيرادات", "0", "#27AE60", "إيرادات الشهر")
        stats_grid.addWidget(self.revenue_stats, 1, 1)
        
        # إحصائيات الحضور
        self.attendance_stats = self.create_stat_card("✅ الحضور", "0%", "#2980B9", "نسبة الحضور")
        stats_grid.addWidget(self.attendance_stats, 1, 2)
        
        # إحصائيات الإلغاء
        self.cancellation_stats = self.create_stat_card("❌ الإلغاء", "0%", "#C0392B", "نسبة الإلغاء")
        stats_grid.addWidget(self.cancellation_stats, 1, 3)
        
        layout.addLayout(stats_grid)
        
        # قسم المواعيد القادمة
        appointments_group = QGroupBox("📋 المواعيد القادمة - اليوم")
        appointments_layout = QVBoxLayout()
        
        # جدول المواعيد
        self.appointments_table = QTableWidget()
        self.appointments_table.setColumnCount(6)
        self.appointments_table.setHorizontalHeaderLabels([
            "المريض", "الطبيب", "القسم", "الوقت", "الحالة", "ملاحظات"
        ])
        
        # ضبط إعدادات الجدول
        header = self.appointments_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        
        self.appointments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.appointments_table.setAlternatingRowColors(True)
        self.appointments_table.setMaximumHeight(200)
        
        appointments_layout.addWidget(self.appointments_table)
        appointments_group.setLayout(appointments_layout)
        layout.addWidget(appointments_group)
        
        # قسم الإحصائيات التفصيلية
        stats_group = QGroupBox("📊 إحصائيات تفصيلية")
        stats_detail_layout = QHBoxLayout()
        
        # إحصائيات حسب العيادة
        clinic_stats = self.create_clinic_stats()
        stats_detail_layout.addWidget(clinic_stats)
        
        # إحصائيات حسب القسم
        department_stats = self.create_department_stats()
        stats_detail_layout.addWidget(department_stats)
        
        stats_group.setLayout(stats_detail_layout)
        layout.addWidget(stats_group)
        
        # أزرار التنقل السريع
        quick_actions_layout = QHBoxLayout()
        
        actions = [
            ("➕ إضافة موعد", self.add_appointment, "#007BFF"),
            ("👤 إضافة مريض", self.add_patient, "#28A745"),
            ("👨‍⚕️ إضافة طبيب", self.add_doctor, "#6C757D"),
            ("🏥 إدارة الأقسام", self.manage_departments, "#17A2B8"),
            ("📊 تقرير كامل", self.show_full_report, "#FFC107")
        ]
        
        for text, slot, color in actions:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 6px;
                    font-weight: bold;
                    min-width: 120px;
                }}
                QPushButton:hover {{
                    background-color: {self.darken_color(color)};
                }}
            """)
            btn.clicked.connect(slot)
            quick_actions_layout.addWidget(btn)
        
        layout.addLayout(quick_actions_layout)
        self.setLayout(layout)
    
    def create_stat_card(self, title, value, color, description):
        """إنشاء بطاقة إحصائية"""
        card = QGroupBox(title)
        card.setStyleSheet(f"""
            QGroupBox {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: {color};
                color: white;
                border-radius: 4px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        # القيمة
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setFont(QFont("Arial", 24, QFont.Bold))
        value_label.setStyleSheet(f"color: {color}; padding: 5px;")
        
        # الوصف
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #6C757D; font-size: 11px;")
        
        layout.addWidget(value_label)
        layout.addWidget(desc_label)
        card.setLayout(layout)
        
        return card
    
    def create_clinic_stats(self):
        """إنشاء إحصائيات حسب العيادة"""
        group = QGroupBox("🏥 الإحصائيات حسب العيادة")
        layout = QVBoxLayout()
        
        self.clinic_stats_label = QLabel("جاري تحميل الإحصائيات...")
        self.clinic_stats_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.clinic_stats_label)
        
        group.setLayout(layout)
        return group
    
    def create_department_stats(self):
        """إنشاء إحصائيات حسب القسم"""
        group = QGroupBox("📋 توزيع المواعيد حسب الأقسام")
        layout = QVBoxLayout()
        
        self.department_stats_label = QLabel("جاري تحميل التوزيع...")
        self.department_stats_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.department_stats_label)
        
        group.setLayout(layout)
        return group
    
    def darken_color(self, color):
        """تغميق اللون للتأثيرات"""
        colors = {
            "#007BFF": "#0056B3",
            "#28A745": "#1E7E34",
            "#6C757D": "#545B62",
            "#17A2B8": "#117A8B",
            "#FFC107": "#E0A800"
        }
        return colors.get(color, color)
    
    def load_data(self):
        """تحميل البيانات وعرض الإحصائيات"""
        try:
            if self.db_manager is None:
                logging.error("❌ db_manager is None في Dashboard")
                return
            
            # تحميل البيانات الأساسية
            clinics = self.db_manager.get_clinics()
            departments = self.db_manager.get_departments()
            doctors = self.db_manager.get_doctors()
            patients = self.db_manager.get_patients()
            today_appointments = self.db_manager.get_today_appointments()
            
            # تحديث البطاقات الإحصائية
            self.update_stat_cards(len(clinics), len(departments), len(doctors), len(patients), len(today_appointments))
            
            # تحديث جدول المواعيد
            self.update_appointments_table(today_appointments)
            
            # تحديث الإحصائيات التفصيلية
            self.update_detailed_stats(clinics, departments)
            
            logging.info(f"✅ تم تحميل بيانات اللوحة: {len(clinics)} عيادة، {len(departments)} قسم، {len(doctors)} طبيب، {len(patients)} مريض، {len(today_appointments)} موعد اليوم")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل بيانات اللوحة: {e}")
    
    def update_stat_cards(self, clinics_count, departments_count, doctors_count, patients_count, appointments_count):
        """تحديث البطاقات الإحصائية"""
        try:
            # تحديث قيم البطاقات
            self.clinics_stats.findChild(QLabel).setText(str(clinics_count))
            self.departments_stats.findChild(QLabel).setText(str(departments_count))
            self.doctors_stats.findChild(QLabel).setText(str(doctors_count))
            self.patients_stats.findChild(QLabel).setText(str(patients_count))
            self.appointments_stats.findChild(QLabel).setText(str(appointments_count))
            
            # حساب الإيرادات (نموذج بسيط)
            revenue = doctors_count * 1000  # مثال
            self.revenue_stats.findChild(QLabel).setText(f"{revenue: ,} ريال")
            
            # حساب نسب الحضور والإلغاء (نموذج)
            self.attendance_stats.findChild(QLabel).setText("85%")
            self.cancellation_stats.findChild(QLabel).setText("15%")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث البطاقات الإحصائية: {e}")
    
    def update_appointments_table(self, appointments):
        """تحديث جدول المواعيد"""
        try:
            self.appointments_table.setRowCount(len(appointments))
            
            for row, appointment in enumerate(appointments):
                self.appointments_table.setItem(row, 0, QTableWidgetItem(appointment.get('patient_name', 'غير معروف')))
                self.appointments_table.setItem(row, 1, QTableWidgetItem(appointment.get('doctor_name', 'غير معروف')))
                self.appointments_table.setItem(row, 2, QTableWidgetItem(appointment.get('department_name', 'غير معروف')))
                self.appointments_table.setItem(row, 3, QTableWidgetItem(appointment['appointment_time']))
                
                # تلوين الحالة
                status_item = QTableWidgetItem(appointment['status'])
                self.color_status_item(status_item, appointment['status'])
                self.appointments_table.setItem(row, 4, status_item)
                
                self.appointments_table.setItem(row, 5, QTableWidgetItem(appointment.get('notes', '')))
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث جدول المواعيد: {e}")
    
    def update_detailed_stats(self, clinics, departments):
        """تحديث الإحصائيات التفصيلية"""
        try:
            # إحصائيات العيادات
            clinic_text = ""
            for clinic in clinics:
                clinic_doctors = self.db_manager.get_doctors(clinic_id=clinic['id'])
                clinic_appointments = self.db_manager.get_appointments(clinic_id=clinic['id'])
                clinic_text += f"• {clinic['name']}: {len(clinic_doctors)} طبيب، {len(clinic_appointments)} موعد\n"
            
            self.clinic_stats_label.setText(clinic_text or "لا توجد بيانات")
            
            # إحصائيات الأقسام
            dept_text = ""
            for dept in departments:
                dept_doctors = self.db_manager.get_doctors(department_id=dept['id'])
                dept_appointments = self.db_manager.get_appointments(department_id=dept['id'])
                dept_text += f"• {dept['name']}: {len(dept_doctors)} طبيب، {len(dept_appointments)} موعد\n"
            
            self.department_stats_label.setText(dept_text or "لا توجد بيانات")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث الإحصائيات التفصيلية: {e}")
    
    def color_status_item(self, item, status):
        """تلوين خلية الحالة"""
        colors = {
            'مجدول': '#3498DB',      # أزرق
            'مؤكد': '#2ECC71',       # أخضر
            'منتهي': '#95A5A6',      # رمادي
            'ملغى': '#E74C3C'        # أحمر
        }
        
        color = colors.get(status, '#95A5A6')
        item.setBackground(QColor(color))
        item.setForeground(QColor('white'))
    
    def add_appointment(self):
        """إضافة موعد جديد"""
        try:
            from ui.dialogs.appointment_dialog import AppointmentDialog
            dialog = AppointmentDialog(self.db_manager, self)
            if dialog.exec_() == QDialog.Accepted:
                self.load_data()
                QMessageBox.information(self, "نجاح", "تم إضافة الموعد الجديد بنجاح")
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة الموعد: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في إضافة الموعد: {e}")
    
    def add_patient(self):
        """إضافة مريض جديد"""
        try:
            from ui.dialogs.patient_dialog import PatientDialog
            dialog = PatientDialog(self.db_manager, self)
            if dialog.exec_() == QDialog.Accepted:
                self.load_data()
                QMessageBox.information(self, "نجاح", "تم إضافة المريض الجديد بنجاح")
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة المريض: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في إضافة المريض: {e}")
    
    def add_doctor(self):
        """إضافة طبيب جديد"""
        try:
            from ui.dialogs.doctor_dialog import DoctorDialog
            dialog = DoctorDialog(self.db_manager, self)
            if dialog.exec_() == QDialog.Accepted:
                self.load_data()
                QMessageBox.information(self, "نجاح", "تم إضافة الطبيب الجديد بنجاح")
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة الطبيب: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في إضافة الطبيب: {e}")
    
    def manage_departments(self):
        """الانتقال إلى إدارة الأقسام"""
        main_window = self.window()
        if hasattr(main_window, 'show_departments'):
            main_window.show_departments()
    
    def show_full_report(self):
        """عرض تقرير كامل"""
        try:
            if self.db_manager is None:
                QMessageBox.warning(self, "تحذير", "لا يمكن إنشاء التقرير - قاعدة البيانات غير متاحة")
                return
            
            # جمع البيانات للتقرير
            clinics = self.db_manager.get_clinics()
            departments = self.db_manager.get_departments()
            doctors = self.db_manager.get_doctors()
            patients = self.db_manager.get_patients()
            appointments = self.db_manager.get_appointments()
            
            # إحصائيات المواعيد
            today = datetime.now().strftime('%Y-%m-%d')
            today_appointments = [app for app in appointments if app['appointment_date'] == today]
            upcoming_appointments = [app for app in appointments if app['appointment_date'] > today]
            
            # إنشاء التقرير
            report = f"""
📊 التقرير الشامل - نظام إدارة المواعيد الطبية
{'='*50}

🏥 العيادات: {len(clinics)} عيادة/مستشفى
🏥 الأقسام: {len(departments)} قسم طبي
👨‍⚕️ الأطباء: {len(doctors)} طبيب
👥 المرضى: {len(patients)} مريض
📅 إجمالي المواعيد: {len(appointments)} موعد

📋 مواعيد اليوم:
   • المجدولة: {len(today_appointments)} موعد
   • القادمة: {len(upcoming_appointments)} موعد

📈 الإحصائيات:
   • المواعيد المجدولة: {len([app for app in appointments if app['status'] == 'مجدول'])}
   • المواعيد المؤكدة: {len([app for app in appointments if app['status'] == 'مؤكد'])}
   • المواعيد المنتهية: {len([app for app in appointments if app['status'] == 'منتهي'])}
   • المواعيد الملغاة: {len([app for app in appointments if app['status'] == 'ملغى'])}

🕒 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            QMessageBox.information(self, "التقرير الشامل", report)
            
        except Exception as e:
            logging.error(f"❌ خطأ في إنشاء التقرير: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في إنشاء التقرير: {e}")
    
    def refresh_data(self):
        """تحديث البيانات (للاستخدام من النافذة الرئيسية)"""
        self.load_data()