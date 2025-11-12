# -*- coding: utf-8 -*-
import sqlite3
import logging
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QGroupBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QComboBox, QDateEdit, 
                             QTextEdit, QProgressBar, QHeaderView)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
from PyQt5.QtChart import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PyQt5.QtGui import QPainter

class ReportsManager(QWidget):
    """مدير التقارير والإحصائيات"""

    def __init__(self, db_path, clinic_id):
        super().__init__()
        self.db_path = db_path
        self.clinic_id = clinic_id
        self.setup_ui()
        self.load_reports()

    def setup_ui(self):
        """إعداد واجهة التقارير"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # عنوان اللوحة
        title = QLabel("📊 التقارير والإحصائيات")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # فلترة التقارير
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("الفترة:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["اليوم", "أسبوع", "شهر", "3 أشهر", "سنة", "مخصص"])
        self.period_combo.currentTextChanged.connect(self.on_period_changed)
        filter_layout.addWidget(self.period_combo)

        filter_layout.addWidget(QLabel("من:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        filter_layout.addWidget(self.date_from)

        filter_layout.addWidget(QLabel("إلى:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        filter_layout.addWidget(self.date_to)

        self.generate_btn = QPushButton("🔄 توليد التقرير")
        self.generate_btn.clicked.connect(self.generate_report)
        filter_layout.addWidget(self.generate_btn)

        self.export_btn = QPushButton("📥 تصدير التقرير")
        self.export_btn.clicked.connect(self.export_report)
        filter_layout.addWidget(self.export_btn)

        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # شبكة التقارير
        grid_layout = QGridLayout()

        # الإحصائيات الرئيسية
        self.setup_main_stats(grid_layout)

        # تقرير المواعيد
        self.setup_appointments_report(grid_layout)

        # تقرير الإيرادات
        self.setup_revenue_report(grid_layout)

        main_layout.addLayout(grid_layout)

    def setup_main_stats(self, layout):
        """إعداد الإحصائيات الرئيسية"""
        stats_group = QGroupBox("الإحصائيات الرئيسية")
        stats_layout = QGridLayout(stats_group)

        self.main_stats = {}
        stats_data = [
            ("إجمالي المواعيد", "total_appointments", 0, 0),
            ("مواعيد تمت", "completed_appointments", 0, 1),
            ("مواعيد ملغاة", "cancelled_appointments", 0, 2),
            ("نسبة الحضور", "attendance_rate", 1, 0),
            ("إجمالي المرضى", "total_patients", 1, 1),
            ("مرضى جدد", "new_patients", 1, 2),
            ("إجمالي الأطباء", "total_doctors", 2, 0),
            ("الإيرادات", "revenue", 2, 1),
            ("متوسط التقييم", "avg_rating", 2, 2)
        ]

        for title, key, row, col in stats_data:
            group = QGroupBox(title)
            group_layout = QVBoxLayout(group)

            value_label = QLabel("0")
            value_label.setFont(QFont("Arial", 18, QFont.Bold))
            value_label.setAlignment(Qt.AlignCenter)
            value_label.setStyleSheet("color: #2c3e50; padding: 10px;")

            group_layout.addWidget(value_label)
            stats_layout.addWidget(group, row, col)
            self.main_stats[key] = value_label

        layout.addWidget(stats_group, 0, 0, 2, 1)

    def setup_appointments_report(self, layout):
        """إعداد تقرير المواعيد"""
        appointments_group = QGroupBox("تقرير المواعيد")
        appointments_layout = QVBoxLayout(appointments_group)

        # جدول المواعيد
        self.appointments_table = QTableWidget()
        self.appointments_table.setColumnCount(6)
        self.appointments_table.setHorizontalHeaderLabels([
            "التاريخ", "المريض", "الطبيب", "النوع", "الحالة", "المبلغ"
        ])
        self.appointments_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        appointments_layout.addWidget(self.appointments_table)

        layout.addWidget(appointments_group, 0, 1, 1, 1)

    def setup_revenue_report(self, layout):
        """إعداد تقرير الإيرادات"""
        revenue_group = QGroupBox("تقرير الإيرادات")
        revenue_layout = QVBoxLayout(revenue_group)

        # مخطط الإيرادات (سيتم تنفيذه لاحقاً)
        revenue_label = QLabel("مخطط الإيرادات سيظهر هنا")
        revenue_label.setAlignment(Qt.AlignCenter)
        revenue_label.setStyleSheet("background-color: #34495E; color: white; padding: 50px;")
        revenue_layout.addWidget(revenue_label)

        # ملخص الإيرادات
        self.revenue_summary = QTextEdit()
        self.revenue_summary.setMaximumHeight(100)
        self.revenue_summary.setReadOnly(True)
        revenue_layout.addWidget(self.revenue_summary)

        layout.addWidget(revenue_group, 1, 1, 1, 1)

    def on_period_changed(self, period):
        """عند تغيير الفترة"""
        today = QDate.currentDate()
        
        if period == "اليوم":
            self.date_from.setDate(today)
            self.date_to.setDate(today)
        elif period == "أسبوع":
            self.date_from.setDate(today.addDays(-7))
            self.date_to.setDate(today)
        elif period == "شهر":
            self.date_from.setDate(today.addDays(-30))
            self.date_to.setDate(today)
        elif period == "3 أشهر":
            self.date_from.setDate(today.addDays(-90))
            self.date_to.setDate(today)
        elif period == "سنة":
            self.date_from.setDate(today.addDays(-365))
            self.date_to.setDate(today)

    def generate_report(self):
        """توليد التقرير"""
        try:
            date_from = self.date_from.date().toString("yyyy-MM-dd")
            date_to = self.date_to.date().toString("yyyy-MM-dd")

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # الإحصائيات الرئيسية
            self.load_main_stats(cursor, date_from, date_to)

            # تقرير المواعيد
            self.load_appointments_report(cursor, date_from, date_to)

            # تقرير الإيرادات
            self.load_revenue_report(cursor, date_from, date_to)

            conn.close()

        except Exception as e:
            logging.error(f"خطأ في توليد التقرير: {e}")

    def load_main_stats(self, cursor, date_from, date_to):
        """تحميل الإحصائيات الرئيسية"""
        # إجمالي المواعيد
        cursor.execute('''
            SELECT COUNT(*) FROM appointments 
            WHERE clinic_id = ? AND appointment_date BETWEEN ? AND ?
        ''', (self.clinic_id, date_from, date_to))
        total_appointments = cursor.fetchone()[0]

        # المواعيد المكتملة
        cursor.execute('''
            SELECT COUNT(*) FROM appointments 
            WHERE clinic_id = ? AND appointment_date BETWEEN ? AND ? AND status = 'تم الحضور'
        ''', (self.clinic_id, date_from, date_to))
        completed_appointments = cursor.fetchone()[0]

        # المواعيد الملغاة
        cursor.execute('''
            SELECT COUNT(*) FROM appointments 
            WHERE clinic_id = ? AND appointment_date BETWEEN ? AND ? AND status = 'ملغي'
        ''', (self.clinic_id, date_from, date_to))
        cancelled_appointments = cursor.fetchone()[0]

        # نسبة الحضور
        attendance_rate = (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0

        # إجمالي المرضى
        cursor.execute('SELECT COUNT(*) FROM patients WHERE clinic_id = ?', (self.clinic_id,))
        total_patients = cursor.fetchone()[0]

        # مرضى جدد في الفترة
        cursor.execute('''
            SELECT COUNT(*) FROM patients 
            WHERE clinic_id = ? AND created_at BETWEEN ? AND ?
        ''', (self.clinic_id, date_from, date_to))
        new_patients = cursor.fetchone()[0]

        # إجمالي الأطباء
        cursor.execute('SELECT COUNT(*) FROM doctors WHERE clinic_id = ? AND is_active = 1', (self.clinic_id,))
        total_doctors = cursor.fetchone()[0]

        # الإيرادات
        cursor.execute('''
            SELECT SUM(d.consultation_fee) 
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.clinic_id = ? AND a.appointment_date BETWEEN ? AND ? AND a.status = 'تم الحضور'
        ''', (self.clinic_id, date_from, date_to))
        revenue = cursor.fetchone()[0] or 0

        # تحديث القيم
        self.main_stats['total_appointments'].setText(str(total_appointments))
        self.main_stats['completed_appointments'].setText(str(completed_appointments))
        self.main_stats['cancelled_appointments'].setText(str(cancelled_appointments))
        self.main_stats['attendance_rate'].setText(f"{attendance_rate:.1f}%")
        self.main_stats['total_patients'].setText(str(total_patients))
        self.main_stats['new_patients'].setText(str(new_patients))
        self.main_stats['total_doctors'].setText(str(total_doctors))
        self.main_stats['revenue'].setText(f"{revenue:,.0f} ريال")

    def load_appointments_report(self, cursor, date_from, date_to):
        """تحميل تقرير المواعيد"""
        cursor.execute('''
            SELECT a.appointment_date, p.name, d.name, a.type, a.status, d.consultation_fee
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.clinic_id = ? AND a.appointment_date BETWEEN ? AND ?
            ORDER BY a.appointment_date DESC
        ''', (self.clinic_id, date_from, date_to))

        appointments = cursor.fetchall()

        self.appointments_table.setRowCount(len(appointments))
        for row, appointment in enumerate(appointments):
            for col, value in enumerate(appointment):
                item = QTableWidgetItem(str(value))
                
                # تلوين حسب الحالة
                if col == 4:  # عمود الحالة
                    if value == 'تم الحضور':
                        item.setBackground(Qt.green)
                    elif value == 'ملغي':
                        item.setBackground(Qt.red)
                    elif value == 'مجدول':
                        item.setBackground(Qt.yellow)
                
                self.appointments_table.setItem(row, col, item)

    def load_revenue_report(self, cursor, date_from, date_to):
        """تحميل تقرير الإيرادات"""
        cursor.execute('''
            SELECT d.name, COUNT(*) as appointment_count, SUM(d.consultation_fee) as revenue
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.clinic_id = ? AND a.appointment_date BETWEEN ? AND ? AND a.status = 'تم الحضور'
            GROUP BY d.name
            ORDER BY revenue DESC
        ''', (self.clinic_id, date_from, date_to))

        revenue_data = cursor.fetchall()

        summary = "ملخص الإيرادات حسب الأطباء:\n\n"
        total_revenue = 0
        
        for doctor_name, count, revenue in revenue_data:
            summary += f"د. {doctor_name}: {count} موعد - {revenue:,.0f} ريال\n"
            total_revenue += revenue
        
        summary += f"\nالإجمالي: {total_revenue:,.0f} ريال"
        self.revenue_summary.setPlainText(summary)

    def export_report(self):
        """تصدير التقرير"""
        # TODO: تنفيذ تصدير التقرير إلى PDF أو Excel
        logging.info("جاري تصدير التقرير...")